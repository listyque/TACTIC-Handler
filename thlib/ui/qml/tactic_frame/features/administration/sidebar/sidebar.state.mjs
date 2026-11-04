import { documentEvent, policy } from '../admin.document.mjs';
import { navigate } from '../../../controls/lists/tree.ui.mjs';

export const initial = () => ({
    page: 'item',
    mode: 'simple',
    editing: false,
    treeVisible: true,
    treeWidth: 350,
    confirmation: '',
    text: {},
    xml: null
});
export const pending = (ui) =>
    Object.keys(ui.text).length > 0 || ui.xml !== null;
export function completed(ui, command) {
    if (command.type === 'help') return Object.assign({}, ui);
    if (['reload', 'discard'].indexOf(command.type) >= 0)
        return Object.assign(initial(), {
            treeVisible: ui.treeVisible !== false,
            treeWidth: ui.treeWidth
        });
    const next = Object.assign({}, ui, {
        text: {},
        xml: null
    });
    if (command.type === 'mode') next.mode = command.value;
    if (command.type === 'back') next.editing = false;
    return next;
}
export function transition(ui, model, event) {
    if (event.type === 'treeKey') {
        const rows = model.entries.map((record) => ({
            id: String(record.index),
            depth: record.displayDepth || record.depth || 0,
            hasChildren: record.entryType === 'section',
            expanded: record.expanded
        }));
        const action = navigate(rows, String(event.index), event.key);
        if (!action) return { ui: Object.assign({}, ui), commands: [] };
        const result = transition(ui, model, {
            type: action.type === 'select' ? 'select' : 'toggle',
            index: Number(action.id)
        });
        result.ui.editing = ui.editing;
        return result;
    }
    const next = Object.assign({}, ui),
        commands = [],
        allow = policy(model);
    if (event.type === 'confirm' && ui.confirmation === 'delete') {
        next.confirmation = '';
        if (allow.editable && model.selected >= 0)
            commands.push({
                type: 'delete'
            });
        return {
            ui: next,
            commands
        };
    }
    const doc = documentEvent(ui, model, event);
    if (doc) return doc;
    if (event.type === 'applied') {
        next.text = {};
        next.xml = null;
        return {
            ui: next,
            commands
        };
    }
    if (event.type === 'reset')
        return {
            ui: Object.assign(initial(), {
                treeVisible: ui.treeVisible !== false,
                treeWidth: ui.treeWidth
            }),
            commands
        };
    if (model.busy || model.uncertain || next.confirmation)
        return {
            ui: next,
            commands
        };
    switch (event.type) {
        case 'split':
            next.treeWidth = Math.max(280, event.value);
            break;
        case 'treeVisible':
            next.treeVisible = next.treeVisible === false;
            break;
        case 'text':
            if (allow.editable) {
                next.text = Object.assign({}, ui.text);
                if (
                    String(event.value) ===
                    String(model.entry[event.field] || '')
                )
                    delete next.text[event.field];
                else next.text[event.field] = event.value;
            }
            break;
        case 'xml':
            if (allow.editable)
                next.xml = event.value === model.xml ? null : event.value;
            break;
        case 'page':
            if (['item', 'access', 'technical'].indexOf(event.value) >= 0) {
                next.page = event.value;
                commands.push({
                    type: 'apply'
                });
            }
            break;
        case 'mode':
            if (['simple', 'xml'].indexOf(event.value) >= 0)
                commands.push({
                    type: 'mode',
                    value: event.value
                });
            break;
        case 'select':
            if (model.entries.some((row) => row.index === event.index)) {
                next.editing = true;
                commands.push({
                    type: 'select',
                    index: event.index
                });
            }
            break;
        case 'back':
            commands.push({
                type: 'back'
            });
            break;
        case 'toggle':
            commands.push({
                type: 'toggle',
                index: event.index
            });
            break;
        case 'source':
            if (['handler', 'tactic'].indexOf(event.value) >= 0)
                commands.push({
                    type: 'source',
                    value: event.value
                });
            break;
        case 'preview':
            commands.push({
                type: 'preview',
                value: event.value
            });
            break;
        case 'add':
            if (
                allow.editable &&
                ['link', 'section', 'separator'].indexOf(event.value) >= 0
            ) {
                next.editing = true;
                commands.push({
                    type: 'add',
                    value: event.value
                });
            }
            break;
        case 'delete':
            if (allow.editable && model.selected >= 0)
                next.confirmation = 'delete';
            break;
        case 'field':
            if (allow.editable && model.selected >= 0)
                commands.push({
                    type: 'field',
                    field: event.field,
                    value: event.value
                });
            break;
        case 'group':
            if (allow.editable)
                commands.push({
                    type: 'group',
                    code: event.code,
                    value: event.value
                });
            break;
        case 'move':
            if (allow.editable)
                commands.push({
                    type: 'move',
                    value: event.value
                });
            break;
        case 'apply':
            if (allow.editable)
                commands.push({
                    type: 'apply'
                });
            break;
        case 'pageLayout':
        case 'groups':
        case 'search':
            if (allow.editable && !model.dirty)
                commands.push({
                    type: event.type
                });
            break;
        case 'help':
            commands.push({
                type: 'help'
            });
            break;
        default:
            throw Error('Unsupported Sidebar event: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}
