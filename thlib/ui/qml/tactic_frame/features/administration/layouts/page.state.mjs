import * as Document from './page.document.mjs';
import { documentEvent } from '../admin.document.mjs';
export function initial() {
    return {
        selected: '',
        panel: 'canvas',
        preview: false,
        text: {},
        confirmation: '',
        pendingPage: '',
        creating: false,
        newName: '',
        newTitle: '',
        error: ''
    };
}
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [];
    if (
        event.type === 'confirm' &&
        ['page', 'remove'].includes(ui.confirmation) &&
        (model.busy || model.uncertain || !model.canWrite)
    )
        return { ui: next, commands };
    function replace(document) {
        commands.push({ type: 'document', document });
        next.error = '';
    }
    if (event.type === 'keep') {
        next.pendingPage = '';
    }
    if (
        event.type === 'confirm' &&
        ui.confirmation === 'page' &&
        !model.busy &&
        !model.uncertain
    ) {
        next.confirmation = '';
        commands.push(
            { type: 'discard' },
            { type: 'load', name: ui.pendingPage }
        );
        next.pendingPage = '';
        return { ui: next, commands };
    }
    if (
        event.type === 'confirm' &&
        ui.confirmation === 'remove' &&
        model.canWrite &&
        !model.busy &&
        !model.uncertain
    ) {
        try {
            replace(Document.remove(model.document, ui.selected));
            next.selected = '';
        } catch (e) {
            next.error = e.message;
        }
        next.confirmation = '';
        return { ui: next, commands };
    }
    const document = documentEvent(next, model, event);
    if (document) return document;
    if (model.busy || ui.confirmation) return { ui: next, commands };
    if (
        (!model.canWrite || model.uncertain) &&
        !['select', 'panel', 'preview'].includes(event.type)
    )
        return { ui: next, commands };
    try {
        if (
            Object.keys(ui.text).length &&
            ['select', 'geometry', 'add', 'remove', 'change'].includes(
                event.type
            )
        )
            throw Error('Apply or discard the pending text before continuing');
        switch (event.type) {
            case 'preview':
                if (Object.keys(ui.text).length)
                    throw Error(
                        'Apply or discard the pending text before continuing'
                    );
                next.preview = !ui.preview;
                break;
            case 'panel':
                if (['layers', 'canvas', 'properties'].includes(event.value))
                    next.panel = event.value;
                break;
            case 'select':
                if (event.key) Document.block(model.document, event.key);
                next.selected = event.key;
                next.text = {};
                break;
            case 'load':
                if (model.dirty) {
                    next.confirmation = 'page';
                    next.pendingPage = event.value;
                } else {
                    commands.push({ type: 'load', name: event.value });
                    next.selected = '';
                    next.creating = false;
                }
                break;
            case 'new':
                if (model.dirty)
                    throw Error('Save or discard changes before continuing');
                next.creating = true;
                break;
            case 'cancelNew':
                next.creating = false;
                break;
            case 'newName':
            case 'newTitle':
                next[event.type] = event.value;
                break;
            case 'create':
                if (model.dirty)
                    throw Error('Save or discard changes before continuing');
                if (
                    !/^[a-z][a-z0-9_]{0,47}$/.test(ui.newName) ||
                    !ui.newTitle.trim()
                )
                    throw Error('Enter a page name and title');
                if (model.catalog.some((row) => row.identity === ui.newName))
                    throw Error('A view with this name already exists');
                commands.push({
                    type: 'create',
                    name: ui.newName,
                    title: ui.newTitle.trim()
                });
                next.creating = false;
                next.selected = '';
                break;
            case 'buffer':
                next.text = Object.assign({}, ui.text, {
                    [event.key]: event.value
                });
                break;
            case 'commit': {
                if (!Object.prototype.hasOwnProperty.call(ui.text, event.key))
                    break;
                replace(
                    Document.change(
                        model.document,
                        event.root ? '' : ui.selected,
                        event.field,
                        ui.text[event.key]
                    )
                );
                next.text = Object.assign({}, next.text);
                delete next.text[event.key];
                break;
            }
            case 'change':
                replace(
                    Document.change(
                        model.document,
                        event.root ? '' : ui.selected,
                        event.field,
                        event.value
                    )
                );
                break;
            case 'spacing': {
                if (!Object.prototype.hasOwnProperty.call(ui.text, event.key))
                    break;
                replace(
                    Document.spacing(
                        model.document,
                        ui.selected,
                        event.field,
                        event.side,
                        ui.text[event.key]
                    )
                );
                next.text = Object.assign({}, next.text);
                delete next.text[event.key];
                break;
            }
            case 'add': {
                if (!event.value) break;
                const value = Document.add(
                    model.document,
                    ui.selected,
                    event.value,
                    model.searchTypes?.[0]?.value
                );
                replace(value.document);
                next.selected = value.key;
                break;
            }
            case 'remove':
                if (ui.selected) next.confirmation = 'remove';
                break;
            case 'geometry': {
                const value = Document.geometry(
                    model.document,
                    event.value,
                    event.boxes
                );
                replace(value.document);
                next.selected = value.key;
                break;
            }
            case 'card': {
                const item = Document.block(model.document, ui.selected);
                if (item?.kind === 'items')
                    commands.push({
                        type: 'card',
                        searchType: item.search_type,
                        view: item.view
                    });
                break;
            }
            case 'open':
                if (!model.dirty) commands.push(event);
                break;
            case 'check':
                commands.push(event);
                break;
            default:
                throw Error('Unsupported page editor event: ' + event.type);
        }
    } catch (e) {
        next.error = String(e.message || e);
    }
    return { ui: next, commands };
}
