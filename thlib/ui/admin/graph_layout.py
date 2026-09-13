"""Deterministic local layouts for administration node graphs."""

from __future__ import annotations

from collections import deque
import math


NODE_WIDTH = 200
NODE_HEIGHT = 80
HORIZONTAL_STEP = 300
VERTICAL_STEP = 140
ORIGIN = 40
COMPONENT_GAP = 180


def _sort_key(node: dict) -> tuple[str, str]:
    identity = str(node.get('identity') or '')
    return str(node.get('label') or identity).casefold(), identity.casefold()


def _grid(nodes: list[dict], x: float, y: float) -> tuple[dict[str, tuple[float, float]], float]:
    """Lay out arbitrary counts in bounded alphabetical rows."""
    if not nodes:
        return {}, y
    ordered = sorted(nodes, key=_sort_key)
    columns = max(1, min(6, math.ceil(math.sqrt(len(ordered) * 1.5))))
    positions = {
        node['identity']: (
            x + index % columns * HORIZONTAL_STEP,
            y + index // columns * VERTICAL_STEP,
        )
        for index, node in enumerate(ordered)
    }
    rows = math.ceil(len(ordered) / columns)
    return positions, y + rows * VERTICAL_STEP


def _relationships(nodes: list[dict], edges: list[dict]):
    identities = {node['identity'] for node in nodes}
    adjacent = {identity: set() for identity in identities}
    outgoing = {identity: set() for identity in identities}
    incoming = {identity: set() for identity in identities}
    for edge in edges:
        source, target = edge.get('from'), edge.get('to')
        if source not in identities or target not in identities or source == target:
            continue
        adjacent[source].add(target)
        adjacent[target].add(source)
        outgoing[source].add(target)
        incoming[target].add(source)
    return adjacent, outgoing, incoming


def _components(nodes: list[dict], adjacent: dict[str, set[str]]) -> tuple[list[list[str]], list[str]]:
    by_identity = {node['identity']: node for node in nodes}
    linked = {identity for identity, neighbors in adjacent.items() if neighbors}
    components = []
    remaining = set(linked)
    while remaining:
        start = min(remaining, key=lambda identity: _sort_key(by_identity[identity]))
        queue, component = deque([start]), []
        remaining.remove(start)
        while queue:
            identity = queue.popleft()
            component.append(identity)
            for neighbor in sorted(
                    adjacent[identity], key=lambda value: _sort_key(by_identity[value])):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(component)
    components.sort(key=lambda component: _sort_key(by_identity[min(
        component, key=lambda identity: _sort_key(by_identity[identity]))]))
    isolated = sorted(
        (identity for identity in adjacent if not adjacent[identity]),
        key=lambda identity: _sort_key(by_identity[identity]),
    )
    return components, isolated


def _flow_component(component: list[str], by_identity: dict[str, dict],
                    outgoing: dict[str, set[str]], incoming: dict[str, set[str]]):
    members = set(component)
    roots = sorted(
        (identity for identity in component if not (incoming[identity] & members)),
        key=lambda identity: _sort_key(by_identity[identity]),
    )
    if not roots:
        roots = [min(component, key=lambda identity: _sort_key(by_identity[identity]))]
    levels: dict[str, int] = {}
    pending = deque((identity, 0) for identity in roots)
    while pending:
        identity, level = pending.popleft()
        if identity in levels:
            continue
        levels[identity] = level
        for target in sorted(
                outgoing[identity] & members,
                key=lambda value: _sort_key(by_identity[value])):
            if target not in levels:
                pending.append((target, level + 1))
    # Directional islands inside a weak component are possible with cycles and
    # converging arrows. Start each remainder deterministically without loops.
    for start in sorted(members - set(levels), key=lambda value: _sort_key(by_identity[value])):
        if start in levels:
            continue
        pending.append((start, 0))
        while pending:
            identity, level = pending.popleft()
            if identity in levels:
                continue
            levels[identity] = level
            for neighbor in sorted(
                    outgoing[identity] & members,
                    key=lambda value: _sort_key(by_identity[value])):
                if neighbor not in levels:
                    pending.append((neighbor, level + 1))
    columns: dict[int, list[str]] = {}
    for identity, level in levels.items():
        columns.setdefault(level, []).append(identity)
    for values in columns.values():
        values.sort(key=lambda identity: _sort_key(by_identity[identity]))
    maximum_rows = max(map(len, columns.values()))
    positions = {}
    for level in sorted(columns):
        values = columns[level]
        offset = (maximum_rows - len(values)) * VERTICAL_STEP / 2
        for row, identity in enumerate(values):
            positions[identity] = (level * HORIZONTAL_STEP, offset + row * VERTICAL_STEP)
    width = (max(columns) + 1) * HORIZONTAL_STEP
    height = max(NODE_HEIGHT, maximum_rows * VERTICAL_STEP)
    return positions, width, height


def _flow_layout(nodes: list[dict], edges: list[dict]) -> dict[str, tuple[float, float]]:
    by_identity = {node['identity']: node for node in nodes}
    adjacent, outgoing, incoming = _relationships(nodes, edges)
    components, isolated = _components(nodes, adjacent)
    result, cursor_y = {}, ORIGIN
    for component in components:
        local, _width, height = _flow_component(
            component, by_identity, outgoing, incoming)
        result.update({identity: (ORIGIN + point[0], cursor_y + point[1])
                       for identity, point in local.items()})
        cursor_y += height + COMPONENT_GAP
    isolated_nodes = [by_identity[identity] for identity in isolated]
    grid, _bottom = _grid(isolated_nodes, ORIGIN, cursor_y)
    result.update(grid)
    return result


def _network_component(component: list[str], by_identity: dict[str, dict],
                       adjacent: dict[str, set[str]]):
    center = min(
        component,
        key=lambda identity: (-len(adjacent[identity]), _sort_key(by_identity[identity])),
    )
    distances = {center: 0}
    queue = deque([center])
    while queue:
        identity = queue.popleft()
        for neighbor in sorted(
                adjacent[identity], key=lambda value: _sort_key(by_identity[value])):
            if neighbor not in distances:
                distances[neighbor] = distances[identity] + 1
                queue.append(neighbor)
    rings: dict[int, list[str]] = {}
    for identity, depth in distances.items():
        rings.setdefault(depth, []).append(identity)
    positions = {center: (0.0, 0.0)}
    golden_angle = math.pi * (3 - math.sqrt(5))
    for depth in sorted(rings):
        if depth == 0:
            continue
        values = sorted(rings[depth], key=lambda identity: _sort_key(by_identity[identity]))
        radius = 190 * depth
        for index, identity in enumerate(values):
            angle = depth * golden_angle + index * 2 * math.pi / len(values)
            positions[identity] = (math.cos(angle) * radius, math.sin(angle) * radius)
    minimum_x = min(point[0] for point in positions.values())
    minimum_y = min(point[1] for point in positions.values())
    maximum_x = max(point[0] for point in positions.values()) + NODE_WIDTH
    maximum_y = max(point[1] for point in positions.values()) + NODE_HEIGHT
    normalized = {identity: (point[0] - minimum_x, point[1] - minimum_y)
                  for identity, point in positions.items()}
    return normalized, maximum_x - minimum_x, maximum_y - minimum_y


def _network_layout(nodes: list[dict], edges: list[dict]) -> dict[str, tuple[float, float]]:
    by_identity = {node['identity']: node for node in nodes}
    adjacent, _outgoing, _incoming = _relationships(nodes, edges)
    components, isolated = _components(nodes, adjacent)
    result = {}
    cursor_x = cursor_y = ORIGIN
    row_height = 0.0
    shelf_width = 1300
    ordered_components = sorted(
        components,
        key=lambda component: (-len(component), _sort_key(by_identity[min(
            component, key=lambda identity: _sort_key(by_identity[identity]))])),
    )
    for component in ordered_components:
        local, width, height = _network_component(component, by_identity, adjacent)
        if cursor_x > ORIGIN and cursor_x + width > shelf_width:
            cursor_x = ORIGIN
            cursor_y += row_height + COMPONENT_GAP
            row_height = 0
        result.update({identity: (cursor_x + point[0], cursor_y + point[1])
                       for identity, point in local.items()})
        cursor_x += width + COMPONENT_GAP
        row_height = max(row_height, height)
    isolated_y = cursor_y + row_height + (COMPONENT_GAP if components else 0)
    isolated_nodes = [by_identity[identity] for identity in isolated]
    grid, _bottom = _grid(isolated_nodes, ORIGIN, isolated_y)
    result.update(grid)
    return result


def layout_graph(nodes: list[dict], edges: list[dict], style: str) -> list[dict]:
    """Return one atomic set of top-left positions for a supported layout."""
    movable = [node for node in nodes if node.get('identity') and not node.get('referenceOnly')]
    if style == 'grid':
        positions, _bottom = _grid(movable, ORIGIN, ORIGIN)
    elif style == 'flow':
        positions = _flow_layout(movable, edges)
    elif style == 'network':
        positions = _network_layout(movable, edges)
    else:
        raise ValueError('Unknown graph layout')
    return [{'identity': identity, 'nodeX': point[0], 'nodeY': point[1]}
            for identity, point in sorted(positions.items())]
