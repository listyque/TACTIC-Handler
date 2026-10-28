import * as Document from './page.document.mjs';
import * as Data from './page.data.mjs';
import * as Reports from './page.reports.mjs';
import * as Viewport from './page.viewport.mjs';
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
        recordQuery: '',
        pageFilter: 0,
        past: [],
        future: [],
        historyDocument: '',
        canvas: { width: 0, zoom: 'fit' },
        canvasWidthText: '',
        error: ''
    };
}
export function shortcut(key, control, shift, alt) {
    if (!control || alt) return null;
    key = key.toLowerCase();
    if (key === 'z') return { type: shift ? 'redo' : 'undo' };
    if (key === 'y' && !shift) return { type: 'redo' };
    if (key === 'd' && !shift) return { type: 'duplicate' };
    return null;
}
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [];
    const current = Document.fingerprint(model.document);
    if (ui.historyDocument && ui.historyDocument !== current) {
        next.past = [];
        next.future = [];
        next.historyDocument = '';
        next.selected = '';
    }
    if (
        event.type === 'confirm' &&
        ['page', 'remove'].includes(ui.confirmation) &&
        (model.busy || model.uncertain || !model.canWrite)
    )
        return { ui: next, commands };
    function replace(document) {
        if (Document.fingerprint(document) === current) return;
        next.past = next.past
            .concat([
                {
                    document: Document.copy(model.document),
                    selected: ui.selected
                }
            ])
            .slice(-20);
        next.future = [];
        next.historyDocument = Document.fingerprint(document);
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
    if (document) {
        if (
            document.commands.some((command) =>
                ['discard', 'reload'].includes(command.type)
            )
        )
            Object.assign(document.ui, {
                selected: '',
                text: {},
                past: [],
                future: [],
                historyDocument: ''
            });
        return document;
    }
    if (model.busy || ui.confirmation) return { ui: next, commands };
    if (
        (!model.canWrite || model.uncertain) &&
        ![
            'select',
            'panel',
            'preview',
            'source',
            'recordQuery',
            'canvasSize',
            'canvasWidthBuffer',
            'canvasWidthCommit',
            'canvasZoom'
        ].includes(event.type)
    )
        return { ui: next, commands };
    try {
        if (Reports.events.includes(event.type)) {
            if (
                event.key &&
                !Object.prototype.hasOwnProperty.call(ui.text, event.key)
            )
                return { ui: next, commands };
            if (
                Object.keys(ui.text).length &&
                ![
                    'pageConditionCommit',
                    'reportCommit',
                    'pageFilterChange'
                ].includes(event.type)
            )
                throw Error(
                    'Apply or discard the pending text before continuing'
                );
            const result = Reports.edit(model, next, event);
            Object.assign(next, result.ui);
            if (result.document) replace(result.document);
            return { ui: next, commands };
        }
        const pending = Object.keys(ui.text);
        if (
            pending.length &&
            ['data', 'filter'].includes(event.type) &&
            !(
                event.type === 'filter' &&
                event.action === 'remove' &&
                pending.every((key) => key === 'filter:' + event.index)
            )
        )
            throw Error('Apply or discard the pending text before continuing');
        if (
            Object.keys(ui.text).length &&
            [
                'select',
                'geometry',
                'add',
                'remove',
                'change',
                'undo',
                'redo',
                'duplicate',
                'reorder',
                'reparent'
            ].includes(event.type)
        )
            throw Error('Apply or discard the pending text before continuing');
        switch (event.type) {
            case 'canvasSize':
            case 'canvasWidthCommit': {
                const text =
                    event.type === 'canvasSize'
                        ? String(event.value === 'auto' ? '' : event.value)
                        : ui.canvasWidthText.trim();
                if (
                    text &&
                    (!/^\d+$/.test(text) ||
                        Number(text) < 320 ||
                        Number(text) > 3840)
                )
                    throw Error(
                        'Enter a preview width from 320 to 3840 pixels, or leave it empty for Auto.'
                    );
                next.canvas = Object.assign({}, ui.canvas, {
                    width: text ? Number(text) : 0
                });
                next.canvasWidthText = text;
                next.error = '';
                break;
            }
            case 'canvasWidthBuffer':
                next.canvasWidthText = String(event.value);
                break;
            case 'canvasZoom':
                if (
                    event.value !== 'fit' &&
                    !Viewport.zooms.includes(Number(event.value))
                )
                    throw Error('Choose an available canvas zoom');
                next.canvas = Object.assign({}, ui.canvas, {
                    zoom: String(event.value)
                });
                next.error = '';
                break;
            case 'undo':
            case 'redo': {
                if (ui.preview) break;
                const from = event.type === 'undo' ? 'past' : 'future';
                const to = event.type === 'undo' ? 'future' : 'past';
                if (!next[from].length) break;
                const snapshot = next[from][next[from].length - 1];
                next[from] = next[from].slice(0, -1);
                next[to] = next[to]
                    .concat([
                        {
                            document: Document.copy(model.document),
                            selected: ui.selected
                        }
                    ])
                    .slice(-20);
                next.selected = snapshot.selected;
                next.recordQuery = '';
                next.pageFilter = 0;
                next.historyDocument = Document.fingerprint(snapshot.document);
                next.error = '';
                commands.push({
                    type: 'document',
                    document: Document.copy(snapshot.document)
                });
                break;
            }
            case 'duplicate':
            case 'reorder':
            case 'reparent': {
                if (ui.preview || !ui.selected) break;
                const value =
                    event.type === 'duplicate'
                        ? Document.duplicate(model.document, ui.selected)
                        : event.type === 'reorder'
                          ? Document.reorder(
                                model.document,
                                ui.selected,
                                event.delta
                            )
                          : Document.reparent(
                                model.document,
                                ui.selected,
                                event.value
                            );
                replace(value.document);
                next.selected = value.key;
                break;
            }
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
                next.recordQuery = '';
                break;
            case 'recordQuery':
                next.recordQuery = event.value;
                break;
            case 'source': {
                const source = Reports.scope(model.document, ui);
                commands.push({
                    type: 'source',
                    searchType: source.searchType,
                    recordKey: source.recordKey,
                    query: event.query ? ui.recordQuery : null
                });
                break;
            }
            case 'data':
                replace(
                    Data.change(
                        model.document,
                        ui.selected,
                        event.field,
                        event.value
                    )
                );
                next.recordQuery = '';
                break;
            case 'filter':
            case 'filterCommit': {
                if (
                    event.type === 'filterCommit' &&
                    !Object.prototype.hasOwnProperty.call(ui.text, event.key)
                )
                    break;
                const edit =
                    event.type === 'filterCommit'
                        ? Object.assign({}, event, {
                              field: 'value',
                              value: ui.text[event.key]
                          })
                        : event;
                const source = Data.scope(model.document, ui.selected);
                replace(
                    Data.filter(
                        model.document,
                        ui.selected,
                        edit,
                        model.dataSource?.searchType === source.searchType
                            ? model.dataSource
                            : {}
                    )
                );
                next.text = Object.assign({}, next.text);
                delete next.text[event.key || 'filter:' + event.index];
                break;
            }
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
