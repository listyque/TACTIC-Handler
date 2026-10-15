import {node} from "../../core/frame.mjs";
import {translate} from "./admin.strings.mjs";

export const rect = (x, y, width, height) => ({x, y, width: Math.max(0, width), height: Math.max(0, height)});
export const label = (id, bounds, text, extra) => node("Label", id, bounds, Object.assign({text}, extra || {}));
export const muted = {fontSize: 12, color: "secondaryText"};
export function policy(model) {
  const editable = !!model.ready && !!model.canWrite && !model.busy && !model.uncertain;
  return {editable, save: editable && !!model.dirty && !model.pendingText && model.saveAllowed !== false,
    discard: !model.busy && !!(model.dirty || model.uncertain || model.pendingText), reload: !model.busy && !!model.canLoad};
}
export function documentEvent(ui, model, event) {
  const next = Object.assign({}, ui), commands = [], allow = policy(model);
  switch (event.type) {
    case "save": if (allow.save) next.confirmation = "save"; break;
    case "reload":
      if (allow.reload) {
        if (model.dirty || model.uncertain || model.pendingText) next.confirmation = "reload";
        else commands.push({type: "reload", force: false});
      }
      break;
    case "discard": if (allow.discard) next.confirmation = "discard"; break;
    case "keep": next.confirmation = ""; break;
    case "confirm":
      if (!model.busy && next.confirmation) {
        const action = next.confirmation; next.confirmation = "";
        if (action === "save") {if (allow.save) commands.push({type: "save"});}
        else if (action === "reload" || model.uncertain) commands.push({type: "reload", force: true});
        else commands.push({type: "discard"});
      }
      break;
    default: return null;
  }
  return {ui: next, commands};
}
export function toolbar(model, ui, width, language) {
  const tr = text => translate(text, language), compact = width < 550, allow = policy(model);
  const saveWidth = compact ? 38 : language === "ru" ? 200 : 166, discardWidth = compact ? 38 : 118;
  return {nodes: [
    node("Button", "adminReloadDocument", rect(0, 0, 38, 38), {text: tr("Reload from server"), icon: "refresh", iconOnly: true, enabled: allow.reload, action: {type: "reload"}}),
    label("adminDocumentStatus", rect(48, 0, width - saveWidth - discardWidth - 72, 38), tr(model.busy ? "Working on the server…" : model.dirty ? "Unsaved changes" : !model.canWrite ? "Read-only" : ""), muted),
    node("Button", "adminDiscardDocument", rect(width - saveWidth - discardWidth - 8, 0, discardWidth, 38), {text: tr("Discard"), icon: "undo", iconOnly: compact, enabled: allow.discard, action: {type: "discard"}}),
    node("Button", "adminSaveDocument", rect(width - saveWidth, 0, saveWidth, 38), {text: tr("Save to server"), icon: "save", iconOnly: compact, enabled: allow.save, highlighted: true, action: {type: "save"}})
  ]};
}
export function notices(model, ui, width, language, discardText, confirmText) {
  const tr = text => translate(text, language), nodes = []; let top = 0;
  if (model.error || model.message) {
    nodes.push(node("Area", "adminDocumentError", rect(0, 0, width, 58), {text: tr(model.error || model.message), label: tr(model.error ? "Server error" : "Status"), notice: true, readOnly: true, role: model.error ? "alert" : "status", color: model.error ? "error" : "secondaryText"})); top += 66;
  }
  if (ui.confirmation) {
    const saving = ui.confirmation === "save", narrow = width < 520, details = saving && model.confirmationDetails, height = (narrow ? 136 : 90) + (details ? 140 : 0);
    nodes.push(node("Box", "adminDocumentConfirmation", rect(0, top, width, height), {background: "surfaceContainerHigh", children: [
      label("adminConfirmationText", rect(12, 6, width - 24, narrow ? 72 : 42), tr(model.confirmationText || (saving ? "These changes will be saved on the server and will affect other users of the project." : discardText || "Discard unsaved changes?")), {wrap: true}),
      node("Button", "adminCancelSave", rect(12, height - 44, narrow ? 128 : 164, 36), {text: tr(saving ? "Cancel" : "Keep editing"), enabled: !model.busy, action: {type: "keep"}}),
      node("Button", "adminConfirmSave", rect(narrow ? 150 : 188, height - 44, narrow ? width - 162 : 220, 36), {text: tr(saving ? "Save" : confirmText || "Discard changes"), enabled: !model.busy, highlighted: saving, destructive: !saving, action: {type: "confirm"}})].concat(details ? [node("Area", "adminConfirmationDetails", rect(12, narrow ? 82 : 48, width - 24, 126), {text: details, label: tr("Changes"), readOnly: true, notice: true, color: "error"})] : [])})); top += height + 8;
  }
  return {nodes, top};
}
export function tabs(id, options, current, bounds, enabled, actionType) {
  const width = bounds.width / options.length;
  const available = options.filter(option => !option.disabled);
  const keys = {Home: {type: actionType, value: available[0].value}, End: {type: actionType, value: available[available.length - 1].value}};
  const selected = Math.max(0, available.findIndex(option => option.value === current));
  keys.ArrowLeft = {type: actionType, value: available[(selected + available.length - 1) % available.length].value};
  keys.ArrowRight = {type: actionType, value: available[(selected + 1) % available.length].value};
  return node("Box", id, bounds, {background: "surfaceContainerHigh", border: "outlineVariant", radius: 9, role: "radiogroup", children: options.map((option, index) => node("Button", id + "_" + option.value, rect(index * width + 3, 3, width - 6, bounds.height - 6), {text: option.label, icon: option.icon || "", radio: true, selected: current === option.value, enabled: enabled && option.disabled !== true, keys, action: {type: actionType, value: option.value}}))});
}
export function sectionSelector(id, options, current, bounds, enabled, actionType, caption) {
  if (options.some(option => option.label.length * 6.8 + 32 > bounds.width / options.length))
    return node("Choice", id, bounds, {label: caption || (options.find(option => option.value === current) || options[0] || {}).label || "", options: options.map(option => ({value: option.value, label: option.label})), value: current, enabled, action: {type: actionType}});
  return tabs(id, options, current, bounds, enabled, actionType);
}
