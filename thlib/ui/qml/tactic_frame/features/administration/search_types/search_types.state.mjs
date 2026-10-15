import { documentEvent, policy } from '../admin.document.mjs';
import { automaticFields, fieldTypes } from './search_types.fields.mjs';
export function initial() {
    return {
        query: '',
        projectOnly: true,
        hideConfig: true,
        page: 'summary',
        editing: false,
        catalogWidth: 280,
        fieldName: '',
        fieldType: 'varchar(256)',
        fieldQuery: '',
        confirmation: '',
        error: ''
    };
}
export function synchronize(ui, model) {
    if (
        model.ready &&
        !model.identity &&
        ['details', 'fields', 'ready'].indexOf(ui.page) < 0
    )
        return Object.assign({}, ui, {
            page: 'details',
            editing: true
        });
    if (model.identity && ui.page === 'ready')
        return Object.assign({}, ui, {
            page: 'details'
        });
    return ui;
}
export function detailsError(document) {
    if (!String(document.title || '').trim())
        return 'Enter a Search Type title';
    if (document.color && !/^#[0-9a-f]{6}$/i.test(document.color))
        return 'Use a color in #RRGGBB format or leave it empty';
    return '';
}
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [],
        edit = policy(model).editable && !next.confirmation;
    const doc = documentEvent(ui, model, event);
    if (doc) return doc;
    switch (event.type) {
        case 'query':
            if (!model.busy) next.query = event.value;
            break;
        case 'projectOnly':
        case 'hideConfig':
            if (!model.busy) next[event.type] = !!event.value;
            break;
        case 'split':
            next.catalogWidth = Math.max(
                200,
                Math.min(420, Number(event.value))
            );
            break;
        case 'back':
            if (!model.busy && model.identity) next.editing = false;
            break;
        case 'page':
            if (model.busy || next.confirmation) break;
            if (!model.identity && event.value !== 'details') {
                const error = detailsError(model.document);
                if (error) {
                    next.error = error;
                    break;
                }
            }
            commands.push({
                type: 'page',
                value: event.value
            });
            break;
        case 'field':
            if (edit)
                commands.push({
                    type: 'field',
                    field: event.field,
                    value: event.value
                });
            break;
        case 'preview':
            if (edit)
                commands.push({
                    type: 'preview'
                });
            break;
        case 'clearPreview':
            if (edit)
                commands.push({
                    type: 'clearPreview'
                });
            break;
        case 'queue':
            commands.push({
                type: 'queue'
            });
            break;
        case 'select':
            if (
                event.identity === model.identity &&
                !model.busy &&
                !next.confirmation
            ) {
                next.editing = true;
                break;
            }
            if (
                !model.busy &&
                !model.dirty &&
                !model.uncertain &&
                !model.namingLocked &&
                !next.confirmation
            )
                commands.push(event);
            break;
        case 'create':
            if (
                !model.busy &&
                !model.dirty &&
                !model.uncertain &&
                !model.namingLocked &&
                !next.confirmation &&
                (event.type !== 'create' || model.canWrite)
            )
                commands.push(event);
            break;
        case 'fieldName':
        case 'fieldType':
        case 'fieldQuery':
            next[event.type] = event.value;
            break;
        case 'addField':
            if (edit) {
                const name = ui.fieldName.trim(),
                    automatic = automaticFields.concat(
                        model.document.hasPipeline ? ['pipeline_code'] : []
                    );
                if (!/^[a-z][a-z0-9_]*$/.test(name))
                    next.error =
                        'Column names must be unique lowercase SQL identifiers';
                else if (!fieldTypes.some((row) => row.value === ui.fieldType))
                    next.error = 'Unsupported column type';
                else if (
                    name in (model.metadata.columns || {}) ||
                    (model.document.columns || []).some(
                        (row) => row.name === name
                    ) ||
                    (!model.identity && automatic.indexOf(name) >= 0)
                )
                    next.error = 'A column with this name already exists';
                else
                    commands.push({
                        type: 'addField',
                        name,
                        columnType: ui.fieldType
                    });
            }
            break;
        case 'removeDraft':
            if (edit) commands.push(event);
            break;
        case 'removeField':
            if (
                edit &&
                (!(model.metadata.columnRemovalBlocks || {})[event.name] ||
                    (model.document.removedColumns || []).indexOf(event.name) >=
                        0)
            )
                commands.push(event);
            break;
        case 'workflow':
            if (!model.busy && !model.uncertain && !model.namingLocked)
                commands.push(event);
            break;
    }
    return {
        ui: next,
        commands
    };
}
export function completed(ui, command, model) {
    if (command.type === 'page')
        return Object.assign({}, ui, {
            page: command.value,
            editing: true,
            error: ''
        });
    if (command.type === 'select')
        return Object.assign({}, ui, {
            editing: true,
            page: 'summary',
            error: ''
        });
    if (command.type === 'create')
        return Object.assign({}, ui, {
            editing: true,
            page: 'details',
            error: ''
        });
    if (command.type === 'addField')
        return Object.assign({}, ui, {
            fieldName: '',
            error: ''
        });
    if (command.type === 'reload' || command.type === 'discard')
        return Object.assign({}, ui, {
            error: '',
            page: model.identity ? 'summary' : 'details'
        });
    return ui;
}
