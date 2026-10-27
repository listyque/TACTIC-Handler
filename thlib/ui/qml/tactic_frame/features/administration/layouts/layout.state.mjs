import * as Layout from './layout.document.mjs';
import * as Geometry from './item.geometry.mjs';
import { documentEvent, policy } from '../admin.document.mjs';
export function initial() {
    return {
        page: 'design',
        panel: 'elements',
        selected: '',
        context: '',
        catalogWidth: 220,
        propertiesWidth: 330,
        newName: '',
        template: 'blank',
        creating: false,
        pendingContext: null,
        text: {},
        confirmation: '',
        checking: false,
        error: ''
    };
}
export function pending(ui) {
    return Object.keys(ui.text).length > 0;
}
export function blankXml(model) {
    const blank = (model.templates || []).find((row) => row.name === 'blank');
    return model.ready && !model.xml && blank && blank.tree
        ? Layout.serialize(Layout.template(blank.tree, model.view), true)
        : '';
}
export function synchronize(ui, model) {
    if (!model.ready) return ui;
    const key = [
            model.project,
            model.searchType,
            model.view,
            model.source
        ].join(':'),
        next = Object.assign({}, ui);
    if (next.context !== key) {
        next.context = key;
        next.selected = (model.layout.elements[0] || {}).name || '';
        next.text = {};
        next.error = '';
        next.confirmation = '';
    } else if (
        !model.layoutError &&
        next.selected &&
        !model.layout.elements.some((row) => row.name === next.selected)
    )
        next.selected = (model.layout.elements[0] || {}).name || '';
    if (next.checking && !model.busy) {
        if (model.checked && model.checked === model.xml)
            next.page = 'resolved';
        next.checking = false;
    }
    return JSON.stringify(next) === JSON.stringify(ui) ? ui : next;
}
function change(next, model, event, commands) {
    try {
        const tree = Layout.edit(
                model.tree,
                model.view,
                event.name === undefined ? next.selected : event.name,
                event.field,
                event.value
            ),
            description = Layout.describe(tree, model.view);
        if (event.field === 'add')
            next.selected =
                (description.elements[description.elements.length - 1] || {})
                    .name || '';
        else if (event.field === 'remove')
            next.selected = (description.elements[0] || {}).name || '';
        commands.push({
            type: 'xml',
            value: Layout.serialize(tree, true)
        });
        next.error = '';
        return true;
    } catch (error) {
        next.error = String(error.message || error);
        return false;
    }
}
function numeric(field, value) {
    const number = Number(value),
        limits = {
            row: [1, 100],
            column: [1, 12],
            span: [1, 12],
            rows: [1, 100],
            columns: [1, 12],
            height: [1, 1200],
            card_width: [1, 1200],
            layer: [-100, 100]
        },
        range = limits[field];
    return (
        !range ||
        (/^-?\d+$/.test(String(value)) &&
            Number.isInteger(number) &&
            number >= range[0] &&
            number <= range[1])
    );
}
export function transition(ui, model, event) {
    if (event.invert)
        event = Object.assign({}, event, {
            value: !event.value
        });
    const next = Object.assign({}, ui),
        commands = [],
        edit = policy(model).editable;
    if (event.type === 'help')
        return {
            ui: next,
            commands: [event]
        };
    if (event.type === 'confirm' && ui.confirmation === 'remove') {
        if (edit)
            change(
                next,
                model,
                {
                    field: 'remove',
                    value: ''
                },
                commands
            );
        next.confirmation = '';
        return {
            ui: next,
            commands
        };
    }
    if (event.type === 'keep') next.pendingContext = null;
    if (event.type === 'confirm' && ui.confirmation === 'context') {
        if (!model.busy && !model.uncertain && ui.pendingContext) {
            commands.push({ type: 'discard' });
            if (ui.pendingContext.type === 'startView') next.creating = true;
            else commands.push(ui.pendingContext);
            next.confirmation = '';
            next.pendingContext = null;
            next.text = {};
        }
        return { ui: next, commands };
    }
    const document = documentEvent(next, model, event);
    if (document) return document;
    if (model.busy || ui.confirmation)
        return {
            ui: next,
            commands
        };
    switch (event.type) {
        case 'page':
            next.page = event.value;
            break;
        case 'panel':
            next.panel = event.value;
            break;
        case 'select':
            if (pending(ui))
                next.error =
                    'Apply or discard the pending text before continuing';
            else {
                next.selected = event.name;
                next.panel = 'settings';
                next.confirmation = '';
            }
            break;
        case 'catalogSplit':
            next.catalogWidth = Math.max(
                180,
                Math.min(420, Number(event.value))
            );
            break;
        case 'propertiesSplit':
            next.propertiesWidth = Math.max(
                240,
                Math.min(520, Number(event.value))
            );
            break;
        case 'newName':
        case 'template':
            next[event.type] = event.value;
            break;
        case 'buffer':
            if (edit)
                next.text = Object.assign({}, next.text, {
                    [event.key]: event.value
                });
            break;
        case 'text':
            if (
                edit &&
                !model.layoutError &&
                Object.keys(ui.text).every((key) => key === event.key)
            ) {
                next.text = Object.assign({}, next.text, {
                    [event.key]: event.value
                });
                change(next, model, event, commands);
            }
            break;
        case 'finishText':
            if (Object.prototype.hasOwnProperty.call(next.text, event.key)) {
                next.text = Object.assign({}, next.text);
                delete next.text[event.key];
            }
            break;
        case 'number': {
            if (
                !edit ||
                !Object.prototype.hasOwnProperty.call(next.text, event.key)
            )
                break;
            const text = next.text[event.key];
            if (!numeric(event.field, text)) {
                next.error = 'Enter a whole number within the allowed range';
                break;
            }
            if (
                change(
                    next,
                    model,
                    {
                        name: event.name,
                        field: event.field,
                        value: Number(text)
                    },
                    commands
                )
            ) {
                next.text = Object.assign({}, next.text);
                delete next.text[event.key];
            }
            break;
        }
        case 'change':
            if (edit && !model.layoutError && !pending(ui)) {
                if (!numeric(event.field, event.value)) {
                    next.error =
                        'Enter a whole number within the allowed range';
                    break;
                }
                if (event.field === 'parent') {
                    let parent = event.value,
                        seen = [next.selected];
                    while (parent) {
                        if (seen.indexOf(parent) >= 0) {
                            next.error = 'Invalid or cyclic layout container';
                            break;
                        }
                        seen.push(parent);
                        const item = model.layout.elements.find(
                            (row) => row.name === parent
                        );
                        if (!item || item.kind !== 'group') {
                            next.error = 'Invalid or cyclic layout container';
                            break;
                        }
                        parent = item.parent;
                    }
                    if (parent) break;
                }
                change(next, model, event, commands);
            }
            break;
        case 'add':
            if (edit && !model.layoutError && !pending(ui) && event.value)
                change(
                    next,
                    model,
                    {
                        name: '',
                        field: 'add',
                        value: event.value
                    },
                    commands
                );
            break;
        case 'remove':
            if (edit && next.selected && !pending(ui))
                next.confirmation = 'remove';
            break;
        case 'geometry':
            if (edit && !model.layoutError && !pending(ui)) {
                try {
                    commands.push({
                        type: 'xml',
                        value: Geometry.apply(model, event.value)
                    });
                    next.selected = event.value.key;
                    next.error = '';
                } catch (error) {
                    next.error = String(error.message || error);
                }
            }
            break;
        case 'spacing': {
            if (
                !edit ||
                model.layoutError ||
                !Object.prototype.hasOwnProperty.call(ui.text, event.key)
            )
                break;
            const value = ui.text[event.key];
            if (!/^\d+$/.test(String(value)) || Number(value) > 256) {
                next.error = 'Enter spacing from 0 to 256';
                break;
            }
            const item = model.layout.elements.find(
                (row) => row.name === next.selected
            );
            if (
                !item ||
                !['padding', 'margin'].includes(event.field) ||
                !Number.isInteger(event.side) ||
                event.side < 0 ||
                event.side > 3
            )
                break;
            const values = (item[event.field] || [0, 0, 0, 0]).slice();
            values[event.side] = Number(value);
            if (
                change(
                    next,
                    model,
                    { field: event.field, value: values.join(' ') },
                    commands
                )
            ) {
                next.text = Object.assign({}, next.text);
                delete next.text[event.key];
            }
            break;
        }
        case 'move':
        case 'drop':
            if (edit && !model.layoutError && !pending(ui)) {
                const name =
                        event.type === 'drop' ? event.value : next.selected,
                    item = model.layout.elements.find(
                        (row) => row.name === name
                    );
                if (!item) break;
                const parent = model.layout.elements.find(
                        (row) => row.name === item.parent
                    ),
                    columns = parent ? parent.columns : model.layout.columns;
                const row = Math.max(1, Math.min(100, event.row)),
                    column = Math.max(
                        1,
                        Math.min(columns - item.span + 1, event.column)
                    );
                try {
                    const tree = Layout.edit(
                        Layout.edit(model.tree, model.view, name, 'row', row),
                        model.view,
                        name,
                        'column',
                        column
                    );
                    next.selected = name;
                    commands.push({
                        type: 'xml',
                        value: Layout.serialize(tree, true)
                    });
                    next.error = '';
                } catch (error) {
                    next.error = String(error.message || error);
                }
                break;
            }
        case 'xml':
            if (edit)
                commands.push({
                    type: 'xml',
                    value: event.value
                });
            break;
        case 'formatXml':
            if (edit && !model.layoutError && !pending(ui))
                commands.push({
                    type: 'xml',
                    value: Layout.serialize(model.tree, true)
                });
            break;
        case 'context':
            if (
                !['view', 'searchType'].includes(event.field) ||
                model[event.field] === event.value
            )
                break;
            if (!model.uncertain) {
                if (model.dirty || pending(ui)) {
                    next.confirmation = 'context';
                    next.pendingContext = event;
                } else {
                    next.creating = false;
                    commands.push(event);
                }
            }
            break;
        case 'startView':
            if (edit && !model.uncertain) {
                if (model.dirty || pending(ui)) {
                    next.confirmation = 'context';
                    next.pendingContext = event;
                } else next.creating = true;
            }
            break;
        case 'cancelView':
            next.creating = false;
            break;
        case 'source':
            if (!model.dirty && !model.uncertain && !pending(ui))
                commands.push(event);
            break;
        case 'newView':
            if (edit && !model.dirty && !pending(ui)) {
                const name = next.newName.trim();
                if (!/^[A-Za-z_][\w.@-]{0,127}$/.test(name)) {
                    next.error = 'Invalid view name';
                    break;
                }
                if ((model.configuration.views || []).indexOf(name) >= 0) {
                    next.error = 'A view with this name already exists';
                    break;
                }
                const template = (model.templates || []).find(
                        (row) => row.name === next.template
                    ),
                    tree =
                        next.template === 'copy'
                            ? model.tree
                            : template && template.tree;
                try {
                    if (!tree) throw Error('Invalid layout template');
                    commands.push({
                        type: 'newView',
                        view: name,
                        xml: Layout.serialize(Layout.template(tree, name), true)
                    });
                    next.error = '';
                } catch (error) {
                    next.error = String(error.message || error);
                }
            }
            break;
        case 'check':
            if (edit && !pending(ui) && !model.layoutError) {
                next.checking = true;
                commands.push(event);
            }
            break;
        case 'openView':
            if (
                edit &&
                !model.dirty &&
                !pending(ui) &&
                model.configuration.resolved &&
                model.configuration.resolved.configured
            )
                commands.push(event);
            break;
        case 'help':
            commands.push(event);
            break;
    }
    return {
        ui: next,
        commands
    };
}
export function completed(ui, command) {
    if (command.type === 'newView')
        return Object.assign({}, ui, {
            creating: false,
            page: 'design',
            panel: 'elements'
        });
    return ['reload', 'discard', 'source'].indexOf(command.type) >= 0
        ? Object.assign({}, ui, {
              text: {},
              confirmation: '',
              checking: false,
              error: ''
          })
        : ui;
}
