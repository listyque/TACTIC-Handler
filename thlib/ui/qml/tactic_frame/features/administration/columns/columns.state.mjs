import {documentEvent, policy} from "../admin.document.mjs";
export const initial = () => ({query: "", searchType: "", mode: "simple", path: "", editing: false, catalogWidth: 350, columnWidth: 250, columnHeight: 170, confirmation: "", text: {}});
export const pending = ui => Object.keys(ui.text).length > 0;
export function selected(ui, elements, name) {
  const column = elements.find(row => row.name === name) || elements[0];
  return Object.assign({}, ui, {text: {}, path: column ? column.path : ""});
}
export function completed(ui, command, model) {
  const next = Object.assign({}, ui, {text: {}});
  if (["select", "filter", "reload", "discard"].indexOf(command.type) >= 0) next.path = model.element.path || "";
  if (command.type === "column") next.path = command.path;
  if (command.type === "mode") next.mode = command.value;
  if (command.type === "back") next.editing = false;
  return next;
}
export function transition(ui, model, event) {
  const document = documentEvent(ui, model, event);
  if (document) return document;
  const next = Object.assign({}, ui), commands = [], allow = policy(model);
  if (event.type === "applied") {next.text = {}; return {ui: next, commands};}
  if (model.busy || ui.confirmation) return {ui: next, commands};
  switch (event.type) {
    case "split": if (["catalogWidth", "columnWidth", "columnHeight"].indexOf(event.field) >= 0) next[event.field] = event.value; break;
    case "query": case "searchType": if (!model.dirty && !model.uncertain) {next[event.type] = event.value; commands.push({type: "filter"});} break;
    case "select": if (!model.dirty && !model.uncertain) {next.editing = true; commands.push({type: "select", identity: event.identity});} break;
    case "back": commands.push({type: "back"}); break;
    case "mode": if (["xml", "simple"].indexOf(event.value) >= 0) commands.push({type: "mode", value: event.value}); break;
    case "column": if (model.elements.some(row => row.path === event.path)) commands.push({type: "column", path: event.path}); break;
    case "text": if (allow.editable) {next.text = Object.assign({}, ui.text); if (String(event.value) === String(model.element[event.field])) delete next.text[event.field]; else next.text[event.field] = event.value;} break;
    case "commit": if (allow.editable && pending(ui)) commands.push({type: "apply"}); break;
    case "field": if (allow.editable) commands.push({type: "change", field: event.field, value: event.value}); break;
    case "step": if (allow.editable) commands.push({type: "change", field: "width", value: Math.max(48, Math.min(640, (Number(ui.text.width || model.element.width) || 160) + event.value))}); break;
    case "xml": if (allow.editable) commands.push({type: "xml", value: event.value}); break;
    default: throw Error("Unsupported Columns event: " + event.type);
  }
  return {ui: next, commands};
}
