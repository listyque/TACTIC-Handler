// Tactic Frame's data contract. This module runs unchanged in Qt and Vue.
export const colors = {
  workspace: "--page", surfaceContainerLow: "--surface",
  surfaceContainerHigh: "--surface-high", primaryText: "--on-surface",
  secondaryText: "--muted", disabledText: "--disabled", action: "--primary",
  selected: "--selected", selectedText: "--on-selected",
  outline: "--outline", outlineVariant: "--outline-variant", error: "--error",
  contentSelection: "--content-selection"
};

export function node(kind, id, rect, properties) {
  const supported = ["Box", "Label", "Icon", "Button", "Action", "CheckBox", "Field", "Area", "Preview", "List", "Scroll", "Choice", "Grid", "IconChoice", "Splitter", "Switch", "Graph", "View", "ColorChoice", "Code"];
  if (supported.indexOf(kind) < 0) throw Error("Unsupported Tactic Frame control: " + kind);
  for (const key of ["x", "y", "width", "height"]) {
    if (typeof rect[key] !== "number" || !isFinite(rect[key])) throw Error("Invalid frame: " + id + ".." + key);
  }
  if (rect.width < 0 || rect.height < 0) throw Error("Negative frame: " + id);
  const options = Object.assign(kind === "List" ? {fields: []} : {}, properties || {});
  const button = kind === "Button";
  const color = options.enabled === false && ["Button", "Field", "Area", "Choice"].indexOf(kind) >= 0 ? "disabledText"
    : button && options.destructive && !options.highlighted ? "error"
    : button && (options.highlighted || options.radio && options.selected) ? "selectedText"
    : button && options.radio ? "secondaryText" : "primaryText";
  return Object.assign({kind, id, text: "", color, fontSize: 13,
    weight: button ? options.radio && !options.selected ? 500 : 600 : 400,
    enabled: true, opacity: 1, children: [], action: null}, rect, options);
}

export function virtualRange(count, rowHeight, viewport, scroll, overscan) {
  const first = Math.max(0, Math.floor(scroll / rowHeight) - overscan);
  const last = Math.min(count, Math.ceil((scroll + viewport) / rowHeight) + overscan);
  return {first, last, height: count * rowHeight};
}
