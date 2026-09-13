"""Structural dock layout shared by the workspace model."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class DockStack:
    panel_ids: tuple[str, ...]
    active_panel_id: str = ""


@dataclass(frozen=True, slots=True)
class DockSplit:
    orientation: str
    ratio: float
    first: DockNode
    second: DockNode


DockNode = DockStack | DockSplit
DockRect = tuple[float, float, float, float]


def serialize_layout(node: DockNode | None) -> dict | None:
    if node is None:
        return None
    if isinstance(node, DockStack):
        return {
            "type": "stack",
            "panels": list(node.panel_ids),
            "active": node.active_panel_id,
        }
    return {
        "type": "split",
        "orientation": node.orientation,
        "ratio": node.ratio,
        "first": serialize_layout(node.first),
        "second": serialize_layout(node.second),
    }


def deserialize_layout(
        value, valid_panel_ids: set[str],
) -> DockNode | None:
    """Read an untrusted persisted tree and discard invalid references."""
    seen: set[str] = set()

    def read(current, depth: int) -> DockNode | None:
        if depth > 64 or not isinstance(current, dict):
            return None
        node_type = current.get("type")
        if node_type == "stack":
            values = []
            for panel_id in current.get("panels", ()):
                if (
                    isinstance(panel_id, str)
                    and panel_id in valid_panel_ids
                    and panel_id not in seen
                ):
                    seen.add(panel_id)
                    values.append(panel_id)
            if not values:
                return None
            active = current.get("active")
            if active not in values:
                active = values[0]
            return DockStack(tuple(values), active)
        if node_type != "split":
            return None
        orientation = current.get("orientation")
        if orientation not in {"horizontal", "vertical"}:
            return None
        first = read(current.get("first"), depth + 1)
        second = read(current.get("second"), depth + 1)
        if first is None:
            return second
        if second is None:
            return first
        try:
            ratio = float(current.get("ratio", 0.5))
        except (TypeError, ValueError):
            ratio = 0.5
        if ratio != ratio or ratio in {float("inf"), float("-inf")}:
            ratio = 0.5
        return DockSplit(
            orientation,
            max(0.02, min(0.98, ratio)),
            first,
            second,
        )

    return read(value, 0)


def stack(panel_id: str) -> DockStack:
    return DockStack((panel_id,), panel_id)


def default_layout() -> DockNode:
    work = DockSplit(
        "horizontal", 0.34, stack("results"), stack("tasks")
    )
    details = DockStack(
        (
            "notes", "task_calendar", "timesheet", "work_reports",
            "cost_reports", "snapshot", "description",
        ),
        "notes",
    )
    return DockSplit("horizontal", 0.66, work, details)


def layout_from_rectangles(rectangles: dict[str, DockRect]) -> DockNode | None:
    """Recover a slicing layout from normalized persisted rectangles."""
    if not rectangles:
        return None

    def build(values: dict[str, DockRect]) -> DockNode:
        if len(values) == 1:
            return stack(next(iter(values)))
        bounds = _rectangles_bounds(values.values())
        candidates: list[tuple[float, str, float, dict, dict]] = []
        for orientation in ("horizontal", "vertical"):
            axis = 0 if orientation == "horizontal" else 1
            extent_axis = 2 if orientation == "horizontal" else 3
            starts = [rect[axis] for rect in values.values()]
            ends = [rect[axis] + rect[extent_axis] for rect in values.values()]
            for boundary in sorted(set(starts + ends)):
                first = {
                    key: rect for key, rect in values.items()
                    if rect[axis] + rect[extent_axis] <= boundary + 0.002
                }
                second = {
                    key: rect for key, rect in values.items()
                    if rect[axis] >= boundary - 0.002
                }
                if not first or not second or len(first) + len(second) != len(values):
                    continue
                total_extent = bounds[extent_axis]
                if total_extent <= 0:
                    continue
                ratio = (boundary - bounds[axis]) / total_extent
                if not 0.02 < ratio < 0.98:
                    continue
                candidates.append((abs(ratio - 0.5), orientation, ratio, first, second))
        if candidates:
            _score, orientation, ratio, first, second = min(
                candidates, key=lambda value: value[0]
            )
            return DockSplit(
                orientation,
                ratio,
                build(first),
                build(second),
            )
        # Coincident rectangles are represented as a deterministic tab stack.
        ordered = tuple(sorted(values))
        return DockStack(ordered, ordered[0])

    return build(rectangles)


def panel_ids(node: DockNode | None) -> tuple[str, ...]:
    if node is None:
        return ()
    if isinstance(node, DockStack):
        return node.panel_ids
    return panel_ids(node.first) + panel_ids(node.second)


def stack_for_panel(
        node: DockNode | None, panel_id: str,
) -> DockStack | None:
    if node is None:
        return None
    if isinstance(node, DockStack):
        return node if panel_id in node.panel_ids else None
    return (
        stack_for_panel(node.first, panel_id)
        or stack_for_panel(node.second, panel_id)
    )


def set_active_panel(
        node: DockNode | None, panel_id: str,
) -> DockNode | None:
    if node is None:
        return None
    if isinstance(node, DockStack):
        if panel_id not in node.panel_ids:
            return node
        return replace(node, active_panel_id=panel_id)
    return replace(
        node,
        first=set_active_panel(node.first, panel_id),
        second=set_active_panel(node.second, panel_id),
    )


def reorder_stack_panel(
        node: DockNode | None, panel_id: str, target_index: int,
) -> DockNode | None:
    if node is None:
        return None
    if isinstance(node, DockStack):
        if panel_id not in node.panel_ids:
            return node
        values = list(node.panel_ids)
        values.remove(panel_id)
        target_index = max(0, min(len(values), target_index))
        values.insert(target_index, panel_id)
        return replace(node, panel_ids=tuple(values))
    return replace(
        node,
        first=reorder_stack_panel(node.first, panel_id, target_index),
        second=reorder_stack_panel(node.second, panel_id, target_index),
    )


def normalize_active_panels(
        node: DockNode | None, available: set[str],
) -> DockNode | None:
    if node is None:
        return None
    if isinstance(node, DockStack):
        visible = tuple(value for value in node.panel_ids if value in available)
        if not visible or node.active_panel_id in visible:
            return node
        return replace(node, active_panel_id=visible[0])
    return replace(
        node,
        first=normalize_active_panels(node.first, available),
        second=normalize_active_panels(node.second, available),
    )


def remove_panel(node: DockNode | None, panel_id: str) -> DockNode | None:
    if node is None:
        return None
    if isinstance(node, DockStack):
        remaining = tuple(value for value in node.panel_ids if value != panel_id)
        if not remaining:
            return None
        active = node.active_panel_id
        if active not in remaining:
            active = remaining[0]
        return DockStack(remaining, active)
    first = remove_panel(node.first, panel_id)
    second = remove_panel(node.second, panel_id)
    if first is None:
        return second
    if second is None:
        return first
    return replace(node, first=first, second=second)


def insert_at_root(
        node: DockNode | None, panel_id: str, side: str,
) -> DockNode:
    """Insert a panel at a workspace edge using the current drop-zone API."""
    node = remove_panel(node, panel_id)
    new_stack = stack(panel_id)
    if node is None:
        return new_stack
    if side == "left":
        return DockSplit("horizontal", 0.28, new_stack, node)
    if side == "right":
        return DockSplit("horizontal", 0.66, node, new_stack)
    if side == "top":
        return DockSplit("vertical", 0.28, new_stack, node)
    if side == "bottom":
        return DockSplit("vertical", 0.70, node, new_stack)
    # The current center guide has no target panel. Keep it deterministic until
    # target-relative tab/split zones are introduced by the next dock stage.
    return DockSplit("horizontal", 0.50, node, new_stack)


def insert_relative(
        node: DockNode | None,
        target_panel_id: str,
        panel_id: str,
        side: str,
) -> DockNode | None:
    """Split the target stack and insert a panel on the requested side."""
    if side not in {"left", "right", "top", "bottom"}:
        return node
    node = remove_panel(node, panel_id)
    if node is None:
        return stack(panel_id)
    inserted = False

    def visit(current: DockNode) -> DockNode:
        nonlocal inserted
        if isinstance(current, DockStack):
            if target_panel_id not in current.panel_ids:
                return current
            inserted = True
            new_stack = stack(panel_id)
            orientation = (
                "horizontal" if side in {"left", "right"} else "vertical"
            )
            if side in {"left", "top"}:
                return DockSplit(orientation, 0.50, new_stack, current)
            return DockSplit(orientation, 0.50, current, new_stack)
        return replace(
            current,
            first=visit(current.first),
            second=visit(current.second),
        )

    result = visit(node)
    if inserted:
        return result
    return insert_at_root(result, panel_id, side)


def swap_panels(
        node: DockNode | None, first_panel_id: str, second_panel_id: str,
) -> DockNode | None:
    """Exchange two panel positions without changing any split ratios."""
    if node is None or first_panel_id == second_panel_id:
        return node
    values = set(panel_ids(node))
    if first_panel_id not in values or second_panel_id not in values:
        return node

    def replace_id(value: str) -> str:
        if value == first_panel_id:
            return second_panel_id
        if value == second_panel_id:
            return first_panel_id
        return value

    def visit(current: DockNode) -> DockNode:
        if isinstance(current, DockStack):
            return DockStack(
                tuple(replace_id(value) for value in current.panel_ids),
                replace_id(current.active_panel_id),
            )
        return replace(
            current,
            first=visit(current.first),
            second=visit(current.second),
        )

    return visit(node)


def tabify(
        node: DockNode | None, target_panel_id: str, panel_id: str,
) -> DockNode | None:
    """Place a panel in the target stack without changing surrounding splits."""
    node = remove_panel(node, panel_id)
    if node is None:
        return stack(panel_id)

    def visit(current: DockNode) -> DockNode:
        if isinstance(current, DockStack):
            if target_panel_id not in current.panel_ids:
                return current
            values = current.panel_ids + (panel_id,)
            return DockStack(values, panel_id)
        return replace(
            current,
            first=visit(current.first),
            second=visit(current.second),
        )

    return visit(node)


def layout_rectangles(
        node: DockNode | None, available: set[str],
        rect: DockRect = (0.0, 0.0, 1.0, 1.0),
) -> dict[str, DockRect]:
    if node is None:
        return {}
    active = set(panel_ids(node)) & available
    if not active:
        return {}
    if isinstance(node, DockStack):
        return {panel_id: rect for panel_id in node.panel_ids if panel_id in active}

    first_active = set(panel_ids(node.first)) & active
    second_active = set(panel_ids(node.second)) & active
    if not first_active:
        return layout_rectangles(node.second, available, rect)
    if not second_active:
        return layout_rectangles(node.first, available, rect)

    x, y, width, height = rect
    ratio = max(0.05, min(0.95, node.ratio))
    if node.orientation == "horizontal":
        first_rect = (x, y, width * ratio, height)
        second_rect = (x + width * ratio, y, width * (1.0 - ratio), height)
    else:
        first_rect = (x, y, width, height * ratio)
        second_rect = (x, y + height * ratio, width, height * (1.0 - ratio))
    return {
        **layout_rectangles(node.first, available, first_rect),
        **layout_rectangles(node.second, available, second_rect),
    }


def has_resizable_edge(
        node: DockNode | None,
        panel_id: str,
        edge: str,
        available: set[str],
) -> bool:
    if node is None or panel_id not in available:
        return False

    def visit(current: DockNode) -> bool:
        if isinstance(current, DockStack):
            return False
        first_active = set(panel_ids(current.first)) & available
        second_active = set(panel_ids(current.second)) & available
        if not first_active:
            return visit(current.second)
        if not second_active:
            return visit(current.first)
        child = current.first if panel_id in first_active else current.second
        if visit(child):
            return True
        return (
            current.orientation == "horizontal"
            and (
                (edge == "right" and panel_id in first_active)
                or (edge == "left" and panel_id in second_active)
            )
        ) or (
            current.orientation == "vertical"
            and (
                (edge == "bottom" and panel_id in first_active)
                or (edge == "top" and panel_id in second_active)
            )
        )

    return visit(node)


def resize_split_for_edge(
        node: DockNode,
        panel_id: str,
        edge: str,
        boundary: float,
        available: set[str],
        minimum_sizes: dict[str, tuple[float, float]],
) -> tuple[DockNode, bool]:
    """Resize the deepest split that owns one visible edge of a panel."""

    def visit(current: DockNode, rect: DockRect) -> tuple[DockNode, bool]:
        if isinstance(current, DockStack):
            return current, False
        first_active = set(panel_ids(current.first)) & available
        second_active = set(panel_ids(current.second)) & available
        if not first_active:
            second, found = visit(current.second, rect)
            return replace(current, second=second), found
        if not second_active:
            first, found = visit(current.first, rect)
            return replace(current, first=first), found

        first_rect, second_rect = _child_rectangles(current, rect)
        if panel_id in first_active:
            first, found = visit(current.first, first_rect)
            if found:
                return replace(current, first=first), True
        else:
            second, found = visit(current.second, second_rect)
            if found:
                return replace(current, second=second), True

        matches = (
            current.orientation == "horizontal"
            and (
                (edge == "right" and panel_id in first_active)
                or (edge == "left" and panel_id in second_active)
            )
        ) or (
            current.orientation == "vertical"
            and (
                (edge == "bottom" and panel_id in first_active)
                or (edge == "top" and panel_id in second_active)
            )
        )
        if not matches:
            return current, False
        axis = 0 if current.orientation == "horizontal" else 1
        extent_axis = 2 if current.orientation == "horizontal" else 3
        extent = rect[extent_axis]
        if extent <= 0:
            return current, False
        desired_ratio = (boundary - rect[axis]) / extent
        ratio = _clamp_ratio(
            current,
            rect,
            available,
            minimum_sizes,
            desired_ratio,
        )
        return replace(current, ratio=ratio), True

    return visit(node, (0.0, 0.0, 1.0, 1.0))


def clamp_layout_ratios(
        node: DockNode,
        available: set[str],
        minimum_sizes: dict[str, tuple[float, float]],
) -> DockNode:
    """Clamp every visible split after the host window changes size."""

    def visit(current: DockNode, rect: DockRect) -> DockNode:
        if isinstance(current, DockStack):
            return current
        first_active = set(panel_ids(current.first)) & available
        second_active = set(panel_ids(current.second)) & available
        if not first_active:
            return replace(current, second=visit(current.second, rect))
        if not second_active:
            return replace(current, first=visit(current.first, rect))
        ratio = _clamp_ratio(
            current,
            rect,
            available,
            minimum_sizes,
            current.ratio,
        )
        updated = replace(current, ratio=ratio)
        first_rect, second_rect = _child_rectangles(updated, rect)
        return replace(
            updated,
            first=visit(updated.first, first_rect),
            second=visit(updated.second, second_rect),
        )

    return visit(node, (0.0, 0.0, 1.0, 1.0))


def subtree_minimum_size(
        node: DockNode,
        available: set[str],
        minimum_sizes: dict[str, tuple[float, float]],
) -> tuple[float, float]:
    if isinstance(node, DockStack):
        sizes = [
            minimum_sizes.get(panel_id, (0.0, 0.0))
            for panel_id in node.panel_ids if panel_id in available
        ]
        if not sizes:
            return 0.0, 0.0
        return max(value[0] for value in sizes), max(value[1] for value in sizes)
    first = subtree_minimum_size(node.first, available, minimum_sizes)
    second = subtree_minimum_size(node.second, available, minimum_sizes)
    if first == (0.0, 0.0):
        return second
    if second == (0.0, 0.0):
        return first
    if node.orientation == "horizontal":
        return first[0] + second[0], max(first[1], second[1])
    return max(first[0], second[0]), first[1] + second[1]


def _clamp_ratio(
        node: DockSplit,
        rect: DockRect,
        available: set[str],
        minimum_sizes: dict[str, tuple[float, float]],
        ratio: float,
) -> float:
    first_minimum = subtree_minimum_size(
        node.first, available, minimum_sizes
    )
    second_minimum = subtree_minimum_size(
        node.second, available, minimum_sizes
    )
    extent_axis = 2 if node.orientation == "horizontal" else 3
    minimum_axis = 0 if node.orientation == "horizontal" else 1
    extent = rect[extent_axis]
    if extent <= 0:
        return node.ratio
    first_extent = first_minimum[minimum_axis]
    second_extent = second_minimum[minimum_axis]
    lower = first_extent / extent
    upper = 1.0 - second_extent / extent
    if lower > upper:
        total = first_extent + second_extent
        return first_extent / total if total > 0 else 0.5
    return max(lower, min(upper, ratio))


def _child_rectangles(
        node: DockSplit, rect: DockRect,
) -> tuple[DockRect, DockRect]:
    x, y, width, height = rect
    ratio = max(0.0, min(1.0, node.ratio))
    if node.orientation == "horizontal":
        return (
            (x, y, width * ratio, height),
            (x + width * ratio, y, width * (1.0 - ratio), height),
        )
    return (
        (x, y, width, height * ratio),
        (x, y + height * ratio, width, height * (1.0 - ratio)),
    )


def _union(first: DockRect, second: DockRect) -> DockRect:
    left = min(first[0], second[0])
    top = min(first[1], second[1])
    right = max(first[0] + first[2], second[0] + second[2])
    bottom = max(first[1] + first[3], second[1] + second[3])
    return left, top, right - left, bottom - top


def _rectangles_bounds(rectangles) -> DockRect:
    iterator = iter(rectangles)
    result = next(iterator)
    for value in iterator:
        result = _union(result, value)
    return result
