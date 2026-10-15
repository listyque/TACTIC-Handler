import { documentEvent, policy } from '../admin.document.mjs';

export function initial() {
    return {
        query: '',
        confirmation: '',
        dropName: '',
        dropIdentity: ''
    };
}
export function permissions(model) {
    const allow = policy(model),
        clean =
            !!model.ready && !model.busy && !model.dirty && !model.uncertain;
    return Object.assign(allow, {
        navigate: !model.busy && !model.dirty && !model.uncertain,
        add: allow.editable && model.rows.length < 200,
        export: clean && allow.editable,
        drop: clean && allow.editable,
        previous: clean && allow.editable && model.metadata.offset > 0,
        next:
            clean &&
            allow.editable &&
            model.metadata.offset + 50 < model.metadata.total
    });
}
export function transition(ui, model, event) {
    const allow = permissions(model);
    if (event.type === 'confirm' && ui.confirmation === 'drop') {
        if (
            !allow.drop ||
            ui.dropIdentity !== model.identity ||
            ui.dropName !== model.metadata.label
        )
            return {
                ui,
                commands: []
            };
        return {
            ui: Object.assign({}, ui, {
                confirmation: ''
            }),
            commands: [
                {
                    type: 'drop',
                    name: ui.dropName
                }
            ]
        };
    }
    const document = documentEvent(ui, model, event);
    if (document) return document;
    const next = Object.assign({}, ui),
        commands = [];
    switch (event.type) {
        case 'query':
            if (allow.navigate && !ui.confirmation)
                next.query = String(event.value);
            break;
        case 'select':
            if (allow.navigate && !ui.confirmation)
                commands.push({
                    type: 'select',
                    identity: event.value
                });
            break;
        case 'add':
            if (allow.add && !ui.confirmation) {
                commands.push({
                    type: 'add'
                });
                if (model.columns.length)
                    commands.push({
                        type: 'focusGrid',
                        grid: 'rawTableViewport',
                        row: model.rows.length,
                        column: 0,
                        id:
                            'rawCell_' +
                            model.rows.length +
                            '_' +
                            model.columns[0].name
                    });
            }
            break;
        case 'deleteRow':
            if (
                allow.editable &&
                event.row >= 0 &&
                event.row < model.rows.length
            )
                commands.push({
                    type: 'deleteRow',
                    row: event.row
                });
            break;
        case 'cell':
            if (
                !model.busy &&
                event.row >= 0 &&
                event.row < model.rows.length &&
                !model.rows[event.row].deleted &&
                model.columns.some((column) => column.name === event.name)
            )
                commands.push({
                    type: 'cell',
                    row: event.row,
                    name: event.name
                });
            break;
        case 'navigateCell': {
            const row = event.row + event.dy,
                column = event.column + event.dx;
            if (
                !model.busy &&
                row >= 0 &&
                row < model.rows.length &&
                column >= 0 &&
                column < model.columns.length
            )
                commands.push({
                    type: 'focusGrid',
                    grid: 'rawTableViewport',
                    row,
                    column,
                    id: 'rawCell_' + row + '_' + model.columns[column].name
                });
            break;
        }
        case 'previous':
            if (allow.previous)
                commands.push({
                    type: 'page',
                    offset: Math.max(0, model.metadata.offset - 50)
                });
            break;
        case 'next':
            if (allow.next)
                commands.push({
                    type: 'page',
                    offset: model.metadata.offset + 50
                });
            break;
        case 'export':
            if (allow.export)
                commands.push({
                    type: 'export'
                });
            break;
        case 'drop':
            if (allow.drop) {
                next.confirmation = 'drop';
                next.dropName = '';
                next.dropIdentity = model.identity;
            }
            break;
        case 'dropName':
            if (!model.busy && ui.confirmation === 'drop')
                next.dropName = String(event.value);
            break;
        default:
            throw Error('Unsupported Raw database event: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}

export function cellInitial(cell) {
    return {
        mode: cell.mode || 'value',
        text: cell.text || '',
        session: cell.session
    };
}
export function cellTransition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [],
        editable = !model.readonly && !model.busy;
    switch (event.type) {
        case 'text':
            if (editable && ui.mode === 'value')
                next.text = String(event.value);
            break;
        case 'mode':
            if (
                editable &&
                (event.value === 'value' ||
                    event.value === 'null' ||
                    (event.value === 'default' && model.newRow))
            )
                next.mode = event.value;
            break;
        case 'apply':
            if (editable)
                commands.push({
                    type: 'apply',
                    mode: ui.mode,
                    text: ui.text
                });
            break;
        case 'cancel':
            commands.push({
                type: 'cancel'
            });
            break;
        default:
            throw Error('Unsupported Cell editor event: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}
