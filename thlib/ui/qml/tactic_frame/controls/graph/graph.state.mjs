// Canvas coordinates and gestures are identical in Qt and the browser.
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
export function initial() {return {zoom: 1, x: -18, y: -18, world: {x: -18, y: -18, right: 818, bottom: 818}, pointer: null, pending: null, cursor: {x: 0, y: 0}, touch: null};}
export function size(node) {return {width: node.kind === "progress" ? 72 : 200, height: 72};}
export function position(ui, node) {
  const moved = ui.pointer && ui.pointer.positions && ui.pointer.positions.find(row => row.identity === node.identity);
  return moved || {identity: node.identity, nodeX: Number(node.nodeX) || 0, nodeY: Number(node.nodeY) || 0};
}
export function point(ui, x, y) {return {x: ui.x + x / ui.zoom, y: ui.y + y / ui.zoom};}
export function bounds(ui, node) {const p = position(ui, node); return Object.assign({x: p.nodeX, y: p.nodeY}, size(node));}
export function include(ui, model, viewport) {
  let world = Object.assign({}, ui.world);
  for (const row of model.nodes || []) {
    const box = bounds(ui, row);
    world.x = Math.min(world.x, box.x - 18); world.y = Math.min(world.y, box.y - 18);
    world.right = Math.max(world.right, box.x + box.width + 100); world.bottom = Math.max(world.bottom, box.y + box.height + 100);
  }
  world.right = Math.max(world.right, ui.x + viewport.width / ui.zoom + 18);
  world.bottom = Math.max(world.bottom, ui.y + viewport.height / ui.zoom + 18);
  return Object.assign({}, ui, {world});
}
function pan(ui, x, y, viewport, expand) {
  const world = Object.assign({}, ui.world);
  if (expand) {
    world.x = Math.min(world.x, x - 100); world.y = Math.min(world.y, y - 100);
    world.right = Math.max(world.right, x + viewport.width / ui.zoom + 100);
    world.bottom = Math.max(world.bottom, y + viewport.height / ui.zoom + 100);
  }
  return Object.assign({}, ui, {world, x: clamp(x, world.x, Math.max(world.x, world.right - viewport.width / ui.zoom)), y: clamp(y, world.y, Math.max(world.y, world.bottom - viewport.height / ui.zoom))});
}
function zoom(ui, value, x, y, viewport) {
  const anchor = point(ui, x, y), next = Object.assign({}, ui, {zoom: clamp(value, .4, 2)});
  return pan(next, anchor.x - x / next.zoom, anchor.y - y / next.zoom, viewport, true);
}
export function selection(model, identity, modifiers, dragging) {
  let names = (model.selectedNodes || []).slice(); const index = names.indexOf(identity);
  if (dragging && index >= 0) return names;
  if (modifiers.control) {if (index >= 0) names.splice(index, 1); else names.push(identity);}
  else if (modifiers.shift) {if (index < 0) names.push(identity);}
  else names = [identity];
  return names;
}
export function selectionRect(ui) {
  const drag = ui.pointer;
  if (!drag || drag.kind !== "selection" || !drag.active) return null;
  return {x: Math.min(drag.start.x, ui.cursor.x), y: Math.min(drag.start.y, ui.cursor.y), width: Math.abs(drag.start.x - ui.cursor.x), height: Math.abs(drag.start.y - ui.cursor.y)};
}
export function curves(ui, model) {
  const nodes = model.nodes || [], rows = [];
  for (let index = 0; index < (model.edges || []).length; index++) {
    const edge = model.edges[index], from = nodes.find(row => row.identity === edge.from), to = nodes.find(row => row.identity === edge.to);
    if (!from || !to) continue;
    const a = bounds(ui, from), b = bounds(ui, to), reverse = model.edges.some(row => row.from === edge.to && row.to === edge.from);
    const offset = reverse ? (String(edge.from) < String(edge.to) ? -24 : 24) : 0;
    rows.push(curve(a.x + a.width, a.y + a.height / 2 + offset, b.x, b.y + b.height / 2 + offset, Object.assign({index}, edge, {color: edge.color || from.color || "action"})));
  }
  if (ui.pending) {
    const node = nodes.find(row => row.identity === ui.pending.identity);
    if (node) {
      const box = bounds(ui, node), port = {x: box.x + (ui.pending.input ? 0 : box.width), y: box.y + box.height / 2};
      const a = ui.pending.input ? ui.cursor : port, b = ui.pending.input ? port : ui.cursor;
      rows.push(curve(a.x, a.y, b.x, b.y, {index: -1, pending: true, color: node.color || "action"}));
    }
  }
  return rows;
}
function curve(x1, y1, x2, y2, data) {return Object.assign({x1, y1, x2, y2, bend: Math.max(70, Math.abs(x2 - x1) / 2)}, data);}
export function curvePoint(edge, t) {
  const u = 1 - t;
  return {x: u*u*u*edge.x1 + 3*u*u*t*(edge.x1+edge.bend) + 3*u*t*t*(edge.x2-edge.bend) + t*t*t*edge.x2, y: u*u*u*edge.y1 + 3*u*u*t*edge.y1 + 3*u*t*t*edge.y2 + t*t*t*edge.y2};
}
function contains(rect, p) {return p.x >= rect.x && p.y >= rect.y && p.x <= rect.x + rect.width && p.y <= rect.y + rect.height;}
export function hit(ui, model, p) {
  for (const row of (model.nodes || []).slice().reverse()) {
    const box = bounds(ui, row), port = {y: box.y + box.height / 2 - 18, width: 36, height: 36};
    if (!model.readOnly && !row.referenceOnly) {
      if (contains(Object.assign({x: box.x - 18}, port), p)) return {kind: "port", identity: row.identity, input: true};
      if (contains(Object.assign({x: box.x + box.width - 18}, port), p)) return {kind: "port", identity: row.identity, input: false};
    }
    if (contains(box, p)) return {kind: "node", identity: row.identity};
  }
  for (const edge of curves(ui, model)) {
    if (edge.pending) continue;
    for (let t = 0; t <= 1; t += .025) {const q = curvePoint(edge, t); if (Math.hypot(q.x - p.x, q.y - p.y) <= 10 / ui.zoom) return {kind: "edge", index: edge.index};}
  }
  return {kind: "selection"};
}
function selectedCommand(names, primary) {return {type: "selectNodes", identities: names, primary: names.indexOf(primary) >= 0 ? primary : names[names.length - 1] || ""};}
function port(ui, target, commands) {
  if (ui.pending && ui.pending.input !== target.input && ui.pending.identity !== target.identity) {
    commands.push({type: "connect", from: target.input ? ui.pending.identity : target.identity, to: target.input ? target.identity : ui.pending.identity});
    return Object.assign({}, ui, {pending: null});
  }
  return Object.assign({}, ui, {pending: ui.pending && ui.pending.identity === target.identity && ui.pending.input === target.input ? null : target});
}
function click(ui, target, event, model, commands) {
  if (target.kind === "port" && !model.readOnly) return port(ui, target, commands);
  if (model.selectionEnabled === false) return ui;
  if (target.kind === "node") commands.push(selectedCommand(selection(model, target.identity, event, false), target.identity));
  else if (target.kind === "edge") commands.push({type: "selectEdge", index: target.index});
  else if (!event.control && !event.shift) commands.push({type: "clear"});
  return Object.assign({}, ui, {pending: null});
}
export function reduce(previous, event, model, viewport) {
  let ui = include(previous, model, viewport); const commands = [];
  const result = () => ({ui, commands});
  if (event.type === "cancel") {ui = Object.assign({}, ui, {pointer: null, pending: null, touch: null}); return result();}
  if (event.type === "scroll") {ui = pan(ui, ui.world.x + event.x / ui.zoom, ui.world.y + event.y / ui.zoom, viewport, false); return result();}
  if (event.type === "reset") {ui = include(initial(), model, viewport); return result();}
  if (event.type === "zoom") {if (!ui.pointer) ui = zoom(ui, event.value, event.x === undefined ? viewport.width / 2 : event.x, event.y === undefined ? viewport.height / 2 : event.y, viewport); return result();}
  if (event.type === "reveal") {
    const rows = (model.nodes || []).filter(row => (event.identities || model.selectedNodes || []).indexOf(row.identity) >= 0);
    if (rows.length) {
      const boxes = rows.map(row => bounds(ui, row)), left = Math.min.apply(null, boxes.map(row => row.x)), right = Math.max.apply(null, boxes.map(row => row.x + row.width)), top = Math.min.apply(null, boxes.map(row => row.y)), bottom = Math.max.apply(null, boxes.map(row => row.y + row.height));
      ui = pan(ui, (left + right) / 2 - viewport.width / ui.zoom / 2, (top + bottom) / 2 - viewport.height / ui.zoom / 2, viewport, true);
    }
    return result();
  }
  if (event.type === "key") {
    if (event.key === "Escape") {if (ui.pointer || ui.pending || ui.touch) ui = Object.assign({}, ui, {pointer: null, pending: null, touch: null}); else if (model.selectionEnabled !== false) commands.push({type: "clear"});}
    else if (event.control && event.key.toLowerCase() === "s" && !model.readOnly) {if (!event.repeat) commands.push({type: "save"});}
    else if (!event.control && !event.alt) {
      if (event.key === "+" || event.key === "=") return reduce(ui, {type: "zoom", value: ui.zoom + .1}, model, viewport);
      if (event.key === "-") return reduce(ui, {type: "zoom", value: ui.zoom - .1}, model, viewport);
      if (event.key === "Home") return reduce(ui, {type: "reset"}, model, viewport);
      if (event.key.toLowerCase() === "f") return reduce(ui, {type: "reveal"}, model, viewport);
      if (event.key === "Delete" && !model.readOnly && !event.repeat) commands.push({type: "remove"});
      const delta = {ArrowLeft: [-10, 0], ArrowRight: [10, 0], ArrowUp: [0, -10], ArrowDown: [0, 10]}[event.key];
      if (delta && !event.shift && !model.readOnly) commands.push({type: "moveNodes", positions: (model.nodes || []).filter(row => !row.referenceOnly && (model.selectedNodes || []).indexOf(row.identity) >= 0).map(row => ({identity: row.identity, nodeX: (Number(row.nodeX) || 0) + delta[0], nodeY: (Number(row.nodeY) || 0) + delta[1]}))});
    }
    return result();
  }
  if (event.type === "activate") {ui = click(ui, event.target, event, model, commands); return result();}
  if (event.type === "touch") {
    const points = event.points || [];
    if (points.length >= 2) {
      const middle = {x: (points[0].x + points[1].x) / 2, y: (points[0].y + points[1].y) / 2}, distance = Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
      if (ui.touch && ui.touch.pinch) {
        const scale = clamp(ui.touch.zoom * distance / Math.max(1, ui.touch.distance), .4, 2);
        ui = pan(Object.assign({}, ui, {zoom: scale}), ui.touch.anchor.x - middle.x / scale, ui.touch.anchor.y - middle.y / scale, viewport, true);
      } else ui = Object.assign({}, ui, {pointer: null, touch: {pinch: true, zoom: ui.zoom, distance, anchor: point(ui, middle.x, middle.y)}});
      return result();
    }
    if (ui.touch && ui.touch.pinch) {if (!points.length) ui = Object.assign({}, ui, {touch: null}); return result();}
    if (!points.length) {const p = ui.pointer; return reduce(ui, p ? {type: "up", x: p.lastX, y: p.lastY} : {type: "cancel"}, model, viewport);}
    const p = points[0]; return reduce(ui, {type: ui.pointer ? "move" : "down", x: p.x, y: p.y, touch: true}, model, viewport);
  }
  if (event.type === "down") {
    if (ui.pointer) return result();
    const start = point(ui, event.x, event.y), target = event.button === 1 ? {kind: "pan"} : hit(ui, model, start);
    ui = Object.assign({}, ui, {cursor: start, pointer: Object.assign({}, target, {start, x: event.x, y: event.y, lastX: event.x, lastY: event.y, originX: ui.x, originY: ui.y, control: !!event.control, shift: !!event.shift, touch: !!event.touch, active: false})});
    return result();
  }
  if (event.type === "tick" && ui.pointer && ui.pointer.active && ui.pointer.kind === "node") {
    const drag = ui.pointer, margin = 36, dt = Math.min(.05, event.seconds);
    const speed = (p, extent) => p < margin ? -Math.min(margin, margin - p) : p > extent - margin ? Math.min(margin, p - extent + margin) : 0;
    const dx = speed(drag.lastX, viewport.width), dy = speed(drag.lastY, viewport.height);
    if (!dx && !dy) return result();
    ui = pan(ui, ui.x + dx * dt * 10 / ui.zoom, ui.y + dy * dt * 10 / ui.zoom, viewport, true);
    return reduce(ui, {type: "move", x: drag.lastX, y: drag.lastY}, model, viewport);
  }
  if (event.type === "move") {
    ui = Object.assign({}, ui, {cursor: point(ui, event.x, event.y)});
    if (!ui.pointer) return result();
    let drag = Object.assign({}, ui.pointer, {lastX: event.x, lastY: event.y});
    if (!drag.active && Math.hypot(event.x - drag.x, event.y - drag.y) >= 8) {
      drag.active = true;
      const draggedNode = (model.nodes || []).find(row => row.identity === drag.identity);
      if (drag.kind === "node" && !model.readOnly && draggedNode && !draggedNode.referenceOnly) {
        const names = selection(model, drag.identity, drag, true);
        commands.push(selectedCommand(names, drag.identity));
        drag.original = model.nodes.filter(row => !row.referenceOnly && names.indexOf(row.identity) >= 0).map(row => Object.assign({}, position(ui, row)));
      } else if (drag.touch) drag.kind = "pan";
      if (drag.kind === "port") ui = Object.assign({}, ui, {pending: {identity: drag.identity, input: drag.input}});
    }
    if (drag.active && drag.kind === "pan") ui = pan(ui, drag.originX + (drag.x - event.x) / ui.zoom, drag.originY + (drag.y - event.y) / ui.zoom, viewport, true);
    else if (drag.active && drag.original) drag.positions = drag.original.map(row => ({identity: row.identity, nodeX: row.nodeX + ui.cursor.x - drag.start.x, nodeY: row.nodeY + ui.cursor.y - drag.start.y}));
    ui = include(Object.assign({}, ui, {pointer: drag}), model, viewport);
    return result();
  }
  if (event.type === "up") {
    const drag = ui.pointer; if (!drag) return result();
    if (drag.active) {
      if (drag.positions) commands.push({type: "moveNodes", positions: drag.positions});
      else if (drag.kind === "selection" && model.selectionEnabled !== false) {
        const rect = selectionRect(ui), names = (drag.control || drag.shift ? model.selectedNodes || [] : []).slice();
        for (const row of model.nodes || []) {const box = bounds(ui, row); if (rect && box.x + box.width >= rect.x && box.x <= rect.x + rect.width && box.y + box.height >= rect.y && box.y <= rect.y + rect.height && names.indexOf(row.identity) < 0) names.push(row.identity);}
        commands.push(selectedCommand(names, names[0]));
      } else if (drag.kind === "port" && !model.readOnly) {
        const target = hit(ui, model, point(ui, event.x, event.y));
        if (target.kind === "port" && target.input !== drag.input && target.identity !== drag.identity) {commands.push({type: "connect", from: target.input ? drag.identity : target.identity, to: target.input ? target.identity : drag.identity}); ui = Object.assign({}, ui, {pending: null});}
      }
    } else if (drag.kind !== "pan") ui = click(ui, drag, drag, model, commands);
    ui = Object.assign({}, ui, {pointer: null}); return result();
  }
  return result();
}
