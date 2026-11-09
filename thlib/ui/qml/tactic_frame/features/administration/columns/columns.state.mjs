import { documentEvent, policy } from '../admin.document.mjs';
export const initial = () => ({
    query: '',
    searchType: '',
    mode: 'simple',
    viewMode: 'view',
    path: '',
    editing: false,
    showAllWidgets: false,
    catalogVisible: true,
    catalogWidth: 350,
    columnWidth: 250,
    columnHeight: 170,
    collapsedCategories: {},
    expandedLayers: {},
    colorsOpen: false,
    configsOpen: true,
    confirmation: '',
    text: {}
});
export const pending = (ui) => Object.keys(ui.text).length > 0;

export function elementFieldValue(element, field) {
    if (!element) return '';
    if (field === 'title')
        return element.rawTitle !== undefined
            ? String(element.rawTitle || '')
            : String(element.title || '');
    if (field === 'extraOptionAdd') return '';
    if (field.indexOf('option:') === 0)
        return String(
            (element.displayOptions &&
                element.displayOptions[field.slice(7)]) ||
                ''
        );
    if (field.indexOf('editOption:') === 0)
        return String(
            (element.editOptions && element.editOptions[field.slice(11)]) || ''
        );
    if (field.indexOf('actionOption:') === 0)
        return String(
            (element.actionOptions && element.actionOptions[field.slice(13)]) ||
                ''
        );
    return String(element[field] ?? '');
}

export function definitionSource(records, request, elements) {
    const views =
        request.view === 'edit_definition'
            ? ['edit_definition']
            : [request.view || 'table', 'definition'];
    const candidates = records.filter(
        (row) =>
            row.searchType === request.searchType &&
            views.indexOf(row.view) >= 0
    );
    candidates.sort(
        (left, right) =>
            views.indexOf(left.view) - views.indexOf(right.view) ||
            Number(right.code === request.code) -
                Number(left.code === request.code) ||
            Number(!!left.login) - Number(!!right.login)
    );
    if (!request.column) return candidates[0] || null;
    let reference = null;
    for (const row of candidates) {
        const column = elements(row).find(
            (item) => item.name === request.column
        );
        if (!column) continue;
        if (column.widget) return row;
        if (!reference) reference = row;
    }
    return reference;
}
export function selected(ui, elements, name) {
    const column = elements.find((row) => row.name === name) || elements[0];
    return Object.assign({}, ui, {
        text: {},
        path: column ? column.path : ''
    });
}
export function completed(ui, command, model) {
    const next = Object.assign({}, ui, {
        text: {}
    });
    if (['select', 'filter', 'reload', 'discard'].indexOf(command.type) >= 0)
        next.path = model.element.path || '';
    if (command.type === 'column') next.path = command.path;
    if (command.type === 'mode') next.mode = command.value;
    if (command.type === 'back') next.editing = false;
    if (command.type === 'change') {
        if (command.field === 'move')
            next.path = (
                model.elements.find((row) => row.name === command.name) ||
                model.element
            ).path;
        else if (command.field === 'addElement')
            next.path = (
                model.elements.find((row) => row.name === command.value) ||
                model.element
            ).path;
        else if (command.field === 'removeElement')
            next.path = model.elements[0] ? model.elements[0].path : '';
        else if (String(next.path || '').indexOf('def:') === 0) {
            const addedName = String(next.path).slice(4);
            const found = model.elements.find((row) => row.name === addedName);
            if (found) next.path = found.path;
        }
    }
    return next;
}
export function transition(ui, model, event) {
    const document = documentEvent(ui, model, event);
    if (document) return document;
    const next = Object.assign({}, ui),
        commands = [],
        allow = policy(model);
    if (event.type === 'applied') {
        next.text = {};
        return {
            ui: next,
            commands
        };
    }
    if (model.busy || ui.confirmation)
        return {
            ui: next,
            commands
        };
    switch (event.type) {
        case 'split':
            if (
                ['catalogWidth', 'columnWidth', 'columnHeight'].indexOf(
                    event.field
                ) >= 0
            )
                next[event.field] = event.value;
            break;
        case 'catalogVisible':
            next.catalogVisible = next.catalogVisible === false;
            break;
        case 'query':
        case 'searchType':
            if (!model.dirty && !model.uncertain) {
                next[event.type] = event.value;
                commands.push({
                    type: 'filter'
                });
            }
            break;
        case 'select':
            if (!model.dirty && !model.uncertain) {
                next.editing = true;
                commands.push({
                    type: 'select',
                    identity: event.identity
                });
            }
            break;
        case 'back':
            commands.push({
                type: 'back'
            });
            break;
        case 'mode':
            if (['xml', 'simple'].indexOf(event.value) >= 0)
                commands.push({
                    type: 'mode',
                    value: event.value
                });
            break;
        case 'viewMode':
            if (['view', 'edit'].indexOf(event.value) >= 0)
                next.viewMode = event.value;
            break;
        case 'toggleCategory':
            if (event.key)
                next.collapsedCategories = Object.assign(
                    {},
                    ui.collapsedCategories,
                    {
                        [event.key]: !ui.collapsedCategories[event.key]
                    }
                );
            break;
        case 'toggleLayer':
            if (event.key)
                next.expandedLayers = Object.assign({}, ui.expandedLayers, {
                    [event.key]: !ui.expandedLayers[event.key]
                });
            break;
        case 'toggleSection':
            if (event.section === 'colors') next.colorsOpen = !ui.colorsOpen;
            else if (event.section === 'configs')
                next.configsOpen = !ui.configsOpen;
            break;
        case 'column':
            if (
                model.elements.some((row) => row.path === event.path) ||
                (model.definitionElements || []).some(
                    (row) => row.path === event.path
                )
            )
                commands.push({
                    type: 'column',
                    path: event.path
                });
            break;
        case 'addElement':
            if (allow.editable && event.name)
                commands.push({
                    type: 'change',
                    field: 'addElement',
                    value: event.name
                });
            break;
        case 'removeElement':
            if (
                allow.editable &&
                model.elements.length > 1 &&
                model.element &&
                model.element.inView !== false
            )
                commands.push({
                    type: 'change',
                    field: 'removeElement',
                    value: model.element.name
                });
            break;
        case 'text':
            if (allow.editable) {
                next.text = Object.assign({}, ui.text);
                if (
                    String(event.value) ===
                    elementFieldValue(model.element, event.field)
                )
                    delete next.text[event.field];
                else next.text[event.field] = event.value;
            }
            break;
        case 'commit':
            if (allow.editable && pending(ui))
                commands.push({
                    type: 'apply'
                });
            break;
        case 'field':
            if (allow.editable)
                commands.push({
                    type: 'change',
                    field: event.field,
                    value: event.value
                });
            break;
        case 'move': {
            const index = model.elements.findIndex(
                (row) => row.path === model.element.path
            );
            if (
                allow.editable &&
                !pending(ui) &&
                index >= 0 &&
                (event.value === -1 || event.value === 1) &&
                model.elements[index + event.value]
            )
                commands.push({
                    type: 'change',
                    field: 'move',
                    value: event.value,
                    name: model.element.name
                });
            break;
        }
        case 'step':
            if (allow.editable)
                commands.push({
                    type: 'change',
                    field: 'width',
                    value: Math.max(
                        48,
                        Math.min(
                            640,
                            (Number(ui.text.width || model.element.width) ||
                                160) + event.value
                        )
                    )
                });
            break;
        case 'xml':
            if (allow.editable)
                commands.push({
                    type: 'xml',
                    value: event.value
                });
            break;
        case 'showAllWidgets':
            next.showAllWidgets = Boolean(event.value);
            break;
        default:
            throw Error('Unsupported Columns event: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}
