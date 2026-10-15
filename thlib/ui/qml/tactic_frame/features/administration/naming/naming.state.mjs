import { documentEvent, policy } from '../admin.document.mjs';
export const fields = [
    'search_type',
    'dir_naming',
    'file_naming',
    'sandbox_dir_naming',
    'snapshot_type',
    'context',
    'latest_versionless',
    'current_versionless',
    'manual_version',
    'ingest_rule_code',
    'condition',
    'class_name',
    'script_path',
    'checkin_type',
    'base_dir_alias',
    'sandbox_dir_alias'
];
export const flags = [
    'latest_versionless',
    'current_versionless',
    'manual_version'
];
export function initial() {
    return {
        editing: true,
        catalogWidth: 270,
        page: 'rule',
        confirmation: '',
        pending: null,
        text: {},
        sampleVersion: null,
        error: ''
    };
}
export function pending(ui) {
    return Object.keys(ui.text).length > 0;
}
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [],
        edit = policy(model).editable;
    const document = documentEvent(ui, model, event);
    if (document && ['save', 'reload', 'discard'].indexOf(event.type) >= 0)
        return document;
    switch (event.type) {
        case 'keep':
            next.confirmation = '';
            next.pending = null;
            break;
        case 'confirm':
            if (model.busy || !next.confirmation) break;
            if (next.pending) {
                commands.push(
                    {
                        type: 'discard'
                    },
                    next.pending
                );
                next.pending = null;
                next.confirmation = '';
            } else if (next.confirmation === 'execute') {
                if (edit)
                    commands.push({
                        type: 'evaluate',
                        execute: true
                    });
                next.confirmation = '';
            } else return documentEvent(ui, model, event);
            break;
        case 'text':
            if (edit && !next.confirmation)
                next.text = Object.assign({}, next.text, {
                    [event.field]: event.value
                });
            break;
        case 'applied':
            next.text = {};
            break;
        case 'commit':
            if (edit && pending(next))
                commands.push({
                    type: 'apply'
                });
            break;
        case 'field':
            if (edit && !next.confirmation)
                commands.push({
                    type: 'field',
                    field: event.field,
                    value: event.value
                });
            break;
        case 'sample':
            if (edit && !next.confirmation)
                commands.push({
                    type: 'sample',
                    field: event.field,
                    value: event.value
                });
            break;
        case 'version':
            if (edit) next.sampleVersion = event.value;
            break;
        case 'commitVersion':
            if (next.sampleVersion !== null) {
                const version = Number(next.sampleVersion);
                if (
                    !/^\d+$/.test(next.sampleVersion) ||
                    version < 1 ||
                    version > 9999
                )
                    next.error = 'Version must be between 1 and 9999';
                else {
                    commands.push({
                        type: 'sample',
                        field: 'version',
                        value: version
                    });
                    next.sampleVersion = null;
                    next.error = '';
                }
            }
            break;
        case 'page':
            next.page = event.value;
            break;
        case 'split':
            next.catalogWidth = Math.max(
                180,
                Math.min(420, Number(event.value))
            );
            break;
        case 'back':
            if (model.identity) next.editing = false;
            break;
        case 'evaluate':
            if (edit && model.sample.key && !next.confirmation) {
                if (event.execute) next.confirmation = 'execute';
                else
                    commands.push({
                        type: 'evaluate',
                        execute: false
                    });
            }
            break;
        case 'items':
            if (!model.busy && !next.confirmation)
                commands.push({
                    type: 'items',
                    offset: event.offset
                });
            break;
        case 'select':
        case 'create':
        case 'duplicate':
            if (
                event.type === 'select' &&
                event.identity === model.identity &&
                !model.busy &&
                !next.confirmation
            ) {
                next.editing = true;
                break;
            }
            if (
                model.busy ||
                model.uncertain ||
                next.confirmation ||
                (!model.canWrite && event.type !== 'select')
            )
                break;
            if (model.dirty) {
                next.confirmation = 'navigate';
                next.pending = event;
            } else commands.push(event);
            break;
    }
    return {
        ui: next,
        commands
    };
}
export function completed(ui, command) {
    if (['select', 'create', 'duplicate'].indexOf(command.type) >= 0)
        return Object.assign({}, ui, {
            editing: true,
            text: {}
        });
    if (['reload', 'discard'].indexOf(command.type) >= 0)
        return Object.assign({}, ui, {
            text: {},
            confirmation: '',
            pending: null
        });
    return ui;
}
