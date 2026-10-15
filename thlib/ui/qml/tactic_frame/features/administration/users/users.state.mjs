// Server data stays in the existing Users controllers in each product.
export function initial() {return {page: "profile", query: "", showRetired: false, confirmation: ""};}
export function permissions(model) {
  const editable = !!model.ready && !!model.canWrite && !model.busy && !model.uncertain;
  return {editable, create: editable && !model.dirty, select: !!model.ready && !model.busy && !model.dirty && !model.uncertain,
    save: editable && !!model.draft && !!model.dirty, discard: !model.busy && !!(model.dirty || model.uncertain),
    reload: !model.busy && !!model.canLoad, search: !!model.ready && !model.busy};
}
export function transition(ui, model, event) {
  const next = Object.assign({}, ui), commands = [], allow = permissions(model);
  switch (event.type) {
    case "page":
      if (!model.busy && ["profile", "account", "groups"].indexOf(event.value) >= 0) {
        next.page = event.value;
        commands.push({type: "focus", id: "segmentedButtonSegment_" + next.page});
      }
      break;
    case "query":
      if (allow.search) {next.query = String(event.value); commands.push({type: "query", value: next.query});}
      break;
    case "showRetired":
      if (allow.search) {next.showRetired = !!event.value; commands.push({type: "showRetired", value: next.showRetired});}
      break;
    case "select":
      if (allow.select) {next.page = "profile"; next.confirmation = ""; commands.push({type: "select", login: event.login});}
      break;
    case "create":
      if (allow.create) {next.page = "profile"; next.confirmation = ""; commands.push({type: "create"}, {type: "focus", id: "adminUserLogin"});}
      break;
    case "field":
      if (allow.editable && model.draft && Object.prototype.hasOwnProperty.call(model.draft, event.field)
          && event.field !== "groups" && event.field !== "code" && !(event.field === "login" && model.identity))
        commands.push({type: "field", field: event.field, value: String(event.value)});
      break;
    case "retired":
      if (allow.editable && model.draft) commands.push({type: "field", field: "s_status", value: event.value ? "retired" : ""});
      break;
    case "member":
      if (allow.editable && model.draft) commands.push({type: "member", name: event.name, value: !!event.value});
      break;
    case "save":
      if (allow.save) {
        if (!String(model.draft.login || "").trim()) commands.push({type: "error", text: "A login is required"});
        else next.confirmation = "save";
      }
      break;
    case "reload":
      if (allow.reload) {
        if (model.dirty || model.uncertain) next.confirmation = "reload";
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
    default: throw Error("Unknown Users action: " + event.type);
  }
  return {ui: next, commands};
}
