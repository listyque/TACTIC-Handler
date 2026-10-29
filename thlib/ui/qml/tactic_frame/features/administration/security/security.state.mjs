import { documentEvent, policy } from '../admin.document.mjs';
export const matrixScopes = [
    'project',
    'link',
    'gear_menu',
    'search_type',
    'process',
    'tasks'
];
export function initial() {
    return {
        scope: 'project',
        page: 'group',
        query: '',
        groupQuery: '',
        targetQuery: '',
        editing: false,
        selectedCell: null,
        confirmation: '',
        text: '',
        baseline: '',
        textKey: ''
    };
}
export function pending(ui) {
    return ui.text !== ui.baseline;
}
export function inheritanceChoices(model) {
    const documents = model.groupDocuments || {},
        groups = model.groups || [],
        byName = new Map(groups.map((group) => [group.label, group.identity])),
        selected = (model.groupDocument.subGroups || '').split('|');
    function reaches(identity, visited) {
        if (identity === model.group) return true;
        if (visited.has(identity)) return false;
        visited.add(identity);
        return (documents[identity]?.subGroups || '')
            .split('|')
            .some((name) => {
                const child = byName.get(name);
                return child && reaches(child, visited);
            });
    }
    return groups
        .filter((group) => group.identity !== model.group)
        .map((group) =>
            Object.assign({}, group, {
                checked: selected.includes(group.label),
                cycle: reaches(group.identity, new Set())
            })
        );
}
export function source(model, ui) {
    return ui.page === 'inherited'
        ? model.inheritedSource || ''
        : ui.page === 'rule'
          ? model.jsonSource || '{}'
          : model.xmlSource || '';
}
export function synchronize(ui, model, force) {
    if (!force && pending(ui)) return ui;
    const text = source(model, ui);
    return Object.assign({}, ui, {
        text,
        baseline: text,
        textKey: model.group + ':' + ui.page + ':' + model.selected
    });
}
export function transition(ui, model, event) {
    const document = documentEvent(ui, model, event);
    if (document) return document;
    let next = Object.assign({}, ui);
    const commands = [],
        allow = policy(model);
    const canNavigate = !model.busy && !pending(ui);
    switch (event.type) {
        case 'scope':
            if (canNavigate) {
                next.scope = event.value;
                next.query = next.groupQuery = next.targetQuery = '';
                next.editing = false;
                next.selectedCell = null;
                commands.push(
                    {
                        type: 'filterMatrix'
                    },
                    {
                        type: 'focus',
                        id: 'adminSecurityTab_' + event.value,
                        fallback: 'adminSecurityScope'
                    }
                );
            }
            break;
        case 'page':
            if (
                canNavigate &&
                (event.value !== 'rule' || model.selected >= 0) &&
                ['group', 'xml', 'rule', 'inherited'].indexOf(event.value) >= 0
            ) {
                next.page = event.value;
                next = synchronize(next, model, true);
                commands.push({
                    type: 'focus',
                    id: 'adminSecurityTechnicalPages_' + event.value,
                    fallback: 'adminSecurityTechnicalPages'
                });
            }
            break;
        case 'query':
        case 'groupQuery':
        case 'targetQuery':
            if (!model.busy) {
                next[event.type] = String(event.value);
                next.selectedCell = null;
                if (event.type !== 'targetQuery')
                    commands.push({
                        type: 'filterMatrix'
                    });
            }
            break;
        case 'group':
            if (canNavigate) {
                commands.push({
                    type: 'group',
                    value: event.value
                });
                next.editing = false;
            }
            break;
        case 'matrix':
            next.selectedCell = {
                row: event.row,
                column: event.column
            };
            if (allow.editable && !pending(ui))
                commands.push({
                    type: 'matrix',
                    row: event.row,
                    column: event.column
                });
            break;
        case 'navigateCell': {
            const row = event.row + event.dy,
                column = event.column + event.dx;
            if (
                row >= 0 &&
                row < model.matrixRows.length &&
                column >= 0 &&
                column < model.matrixGroups.length
            ) {
                next.selectedCell = {
                    row,
                    column
                };
                commands.push({
                    type: 'focusGrid',
                    grid: 'adminSecurityMatrix',
                    row,
                    column,
                    id: 'adminSecurityCell_' + row + '_' + column
                });
            }
            break;
        }
        case 'inherit':
            if (allow.editable && ui.selectedCell && !pending(ui))
                commands.push(
                    Object.assign(
                        {
                            type: 'inherit'
                        },
                        ui.selectedCell
                    )
                );
            break;
        case 'selectRule':
            if (canNavigate) {
                next.editing = true;
                next.targetQuery = '';
                if (ui.scope === 'technical') next.page = 'rule';
                commands.push({
                    type: 'selectRule',
                    index: event.index
                });
            }
            break;
        case 'back':
            next.editing = false;
            break;
        case 'addRule':
            if (allow.editable && !pending(ui)) {
                next.editing = true;
                commands.push({
                    type: 'addRule',
                    scope: ui.scope
                });
            }
            break;
        case 'removeRule':
            if (allow.editable && model.selected >= 0 && !pending(ui)) {
                next.editing = false;
                commands.push({
                    type: 'removeRule'
                });
            }
            break;
        case 'attribute':
        case 'target':
        case 'groupField':
        case 'ruleAccess':
            if (allow.editable && !pending(ui))
                commands.push(Object.assign({}, event));
            break;
        case 'inheritGroup': {
            const choice = inheritanceChoices(model).find(
                (group) => group.identity === event.identity
            );
            if (
                allow.editable &&
                !pending(ui) &&
                choice &&
                (choice.checked || !choice.cycle)
            ) {
                const names = (model.groupDocument.subGroups || '')
                        .split('|')
                        .filter(Boolean),
                    value = choice.checked
                        ? names.filter((name) => name !== choice.label)
                        : [...names, choice.label];
                commands.push({
                    type: 'groupField',
                    field: 'subGroups',
                    value: value.join('|')
                });
            }
            break;
        }
        case 'text':
            if (allow.editable && ui.page !== 'inherited')
                next.text = String(event.value);
            break;
        case 'applyText':
            if (allow.editable && pending(ui))
                commands.push({
                    type: 'applyText',
                    page: ui.page,
                    text: ui.text
                });
            break;
        case 'discardText':
            next = synchronize(next, model, true);
            break;
        default:
            throw Error('Unsupported Access rules event: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}
