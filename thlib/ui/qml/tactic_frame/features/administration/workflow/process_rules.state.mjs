import { documentEvent, policy } from '../admin.document.mjs';
export function initial() {
    return {
        page: 'trigger',
        editing: false,
        catalogWidth: 250,
        confirmation: '',
        error: ''
    };
}
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [],
        edit = policy(model).editable && !model.rule.managed;
    if (event.type === 'confirm' && ui.confirmation === 'remove') {
        if (edit)
            commands.push({
                type: 'remove'
            });
        next.confirmation = '';
        return {
            ui: next,
            commands
        };
    }
    if (event.type === 'confirm' && ui.confirmation === 'close') {
        if (!model.busy)
            commands.push(
                {
                    type: 'discard'
                },
                {
                    type: 'close'
                }
            );
        next.confirmation = '';
        return {
            ui: next,
            commands
        };
    }
    const document = documentEvent(ui, model, event);
    if (document) return document;
    if (model.busy || ui.confirmation)
        return {
            ui: next,
            commands
        };
    switch (event.type) {
        case 'page':
            next.page = event.value;
            next.editing = false;
            commands.push({
                type: 'select',
                index: model.document.rules.findIndex(
                    (row) => row.kind === event.value
                )
            });
            break;
        case 'select':
            next.editing = true;
            commands.push(event);
            break;
        case 'back':
            next.editing = false;
            break;
        case 'split':
            next.catalogWidth = Math.max(
                180,
                Math.min(420, Number(event.value))
            );
            break;
        case 'add':
            if (
                model.canWrite &&
                !model.uncertain &&
                ['trigger', 'notification'].indexOf(next.page) >= 0
            ) {
                commands.push({
                    type: 'add',
                    kind: next.page
                });
                next.editing = true;
            }
            break;
        case 'field':
            if (edit && ownField(model.rule, event.field)) commands.push(event);
            break;
        case 'target':
            if (edit) commands.push(event);
            break;
        case 'output':
            if (edit) commands.push(event);
            break;
        case 'remove':
            if (edit && model.rule.kind) next.confirmation = 'remove';
            break;
        case 'items':
            if (!model.dirty) commands.push(event);
            break;
        case 'object':
            if (
                (model.metadata.items || []).some(
                    (row) => row.key === event.key
                )
            )
                commands.push(event);
            break;
        case 'close':
            if (model.dirty || model.uncertain) next.confirmation = 'close';
            else commands.push(event);
            break;
    }
    return {
        ui: next,
        commands
    };
}
function ownField(rule, key) {
    return (
        Object.prototype.hasOwnProperty.call(rule, key) &&
        ['key', 'kind', 'managed', 'targets', 'outputs'].indexOf(key) < 0
    );
}
