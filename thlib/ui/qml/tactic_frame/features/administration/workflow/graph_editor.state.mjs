import { documentEvent, policy } from '../admin.document.mjs';
export function initial() {
    return {
        page: 'canvas',
        panel: 'canvas',
        inspector: 'selection',
        processPage: 'parameters',
        catalogWidth: 230,
        propertiesWidth: 460,
        catalogVisible: true,
        propertiesVisible: true,
        query: '',
        typeQuery: '',
        subpipelineQuery: '',
        collapsed: [],
        nodeName: '',
        nodeKind: 'manual',
        typeToAdd: '',
        source: '',
        target: '',
        arrange: 'flow',
        text: {},
        confirmation: '',
        pending: null,
        error: ''
    };
}
export function pending(ui) {
    return Object.keys(ui.text).length > 0;
}
const selectionEvents = ['selectNodes', 'selectEdge', 'clear'];
export function transition(ui, model, event) {
    if (event.type === 'graph') event = event.value;
    const next = Object.assign({}, ui),
        commands = [],
        edit = policy(model).editable;
    const navigation = [
        'selectPipeline',
        'createWorkflow',
        'taskWorkflow',
        'dependencies',
        'createType',
        'deleteType'
    ];
    if (event.type === 'keep') {
        next.confirmation = '';
        next.pending = null;
        return {
            ui: next,
            commands
        };
    }
    if (event.type === 'confirm' && next.pending && !model.busy) {
        const command = next.pending;
        next.pending = null;
        next.confirmation = '';
        if (selectionEvents.indexOf(command.type) >= 0) {
            next.text = {};
            next.inspector = 'selection';
            next.propertiesVisible = true;
            next.processPage = 'parameters';
            commands.push(command);
        } else {
            next.text = {};
            commands.push(
                {
                    type: 'discard'
                },
                command
            );
        }
        return {
            ui: next,
            commands
        };
    }
    if (event.type === 'confirm' && next.confirmation === 'remove') {
        next.confirmation = '';
        if (edit)
            commands.push({
                type: 'remove'
            });
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
    if (selectionEvents.indexOf(event.type) >= 0) {
        if (pending(next)) {
            next.confirmation = 'selection';
            next.pending = event;
        } else {
            next.inspector = 'selection';
            next.processPage = 'parameters';
            next.propertiesVisible = true;
            next.text = {};
            commands.push(event);
        }
        return {
            ui: next,
            commands
        };
    }
    if (navigation.indexOf(event.type) >= 0) {
        if (model.uncertain)
            return {
                ui: next,
                commands
            };
        if (
            ['selectPipeline', 'createWorkflow'].indexOf(event.type) >= 0 &&
            model.dirty
        ) {
            next.confirmation = 'navigate';
            next.pending = event;
        } else if (pending(ui)) {
            next.error = 'Apply or discard the pending text before continuing';
        } else if (
            ['taskWorkflow', 'dependencies', 'deleteType'].indexOf(
                event.type
            ) >= 0 &&
            model.dirty
        ) {
            next.error =
                event.type === 'dependencies'
                    ? 'Save the workflow before editing process dependencies'
                    : 'Save or discard changes before continuing';
        } else if (
            event.type === 'selectPipeline' ||
            model.canWrite ||
            event.type === 'taskWorkflow' ||
            event.type === 'dependencies'
        )
            commands.push(event);
        return {
            ui: next,
            commands
        };
    }
    switch (event.type) {
        case 'page':
            next.page = event.value;
            break;
        case 'panel':
            next.panel = event.value;
            break;
        case 'inspector':
            next.inspector = event.value;
            next.propertiesVisible = true;
            next.panel = 'properties';
            break;
        case 'processPage':
            next.processPage = event.value;
            break;
        case 'catalogVisible':
            next.catalogVisible = !next.catalogVisible;
            break;
        case 'propertiesVisible':
            next.propertiesVisible = !next.propertiesVisible;
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
                Math.min(640, Number(event.value))
            );
            break;
        case 'collapse':
            next.collapsed =
                next.collapsed.indexOf(event.identity) >= 0
                    ? next.collapsed.filter((value) => value !== event.identity)
                    : next.collapsed.concat([event.identity]);
            break;
        case 'query':
        case 'typeQuery':
        case 'subpipelineQuery':
        case 'nodeName':
        case 'nodeKind':
        case 'typeToAdd':
        case 'source':
        case 'target':
        case 'arrange':
            next[event.type] = event.value;
            break;
        case 'buffer':
            if (edit)
                next.text = Object.assign({}, next.text, {
                    [event.key]: event.value
                });
            break;
        case 'commitInstance':
            if (edit && next.text.instance !== undefined) {
                const value = next.text.instance.trim();
                if (!/^[a-z][a-z0-9_]*$/.test(value)) {
                    next.error =
                        'Use a lowercase table name with letters, digits and underscores';
                    break;
                }
                commands.push({
                    type: 'renameInstance',
                    value
                });
            }
            break;
        case 'apply':
            if (edit) {
                const value =
                    next.text[event.key] === undefined
                        ? model[event.key]
                        : next.text[event.key];
                if (event.key === 'attributes' || event.key === 'settings') {
                    let parsed;
                    try {
                        parsed = JSON.parse(value);
                    } catch (error) {
                        next.error =
                            'Invalid JSON. Check quotes, commas and braces.';
                        break;
                    }
                    if (
                        !parsed ||
                        typeof parsed !== 'object' ||
                        Array.isArray(parsed)
                    ) {
                        next.error =
                            event.key === 'attributes'
                                ? 'Attributes must be a JSON object with string values'
                                : 'Process settings must be a JSON object';
                        break;
                    }
                    if (
                        event.key === 'attributes' &&
                        Object.keys(parsed).some(
                            (key) => typeof parsed[key] !== 'string'
                        )
                    ) {
                        next.error =
                            'Attributes must be a JSON object with string values';
                        break;
                    }
                }
                next.error = '';
                commands.push({
                    type: 'apply',
                    key: event.key,
                    value
                });
            }
            break;
        case 'integer': {
            const key = 'integer_' + event.section + '_' + event.key,
                text = next.text[key];
            if (text === undefined || !edit) break;
            const value = Number(text);
            if (
                text !== '' &&
                (!/^\d+$/.test(text) ||
                    !Number.isSafeInteger(value) ||
                    value < event.min ||
                    value > event.max)
            ) {
                next.error = 'Enter a whole number within the allowed range';
                break;
            }
            commands.push({
                type: 'setting',
                section: event.section,
                key: event.key,
                value: text === '' ? '' : value
            });
            next.text = Object.assign({}, next.text);
            delete next.text[key];
            next.error = '';
            break;
        }
        case 'position': {
            const text = next.text[event.key],
                value = Number(text);
            if (text === undefined || !edit) break;
            if (!String(text).trim() || !Number.isFinite(value)) {
                next.error = 'Node positions must be finite';
                break;
            }
            const node = (model.nodes || []).find(
                (row) => row.identity === model.selectedNode
            );
            if (node)
                commands.push({
                    type: 'moveNodes',
                    positions: [
                        {
                            identity: node.identity,
                            nodeX:
                                event.key === 'positionX' ? value : node.nodeX,
                            nodeY:
                                event.key === 'positionY' ? value : node.nodeY
                        }
                    ]
                });
            next.text = Object.assign({}, next.text);
            delete next.text[event.key];
            next.error = '';
            break;
        }
        case 'remove':
            if (edit && (model.selectedNode || model.selectedEdge >= 0))
                next.confirmation = 'remove';
            break;
        case 'addNode':
            if (edit) {
                const name =
                    model.mode === 'workflow'
                        ? next.nodeName.trim()
                        : next.typeToAdd;
                if (!name) {
                    next.error = 'Enter a unique node name';
                    break;
                }
                commands.push({
                    type: 'addNode',
                    identity: name,
                    kind:
                        model.document.searchType === 'sthpw/task'
                            ? 'status'
                            : next.nodeKind
                });
            }
            break;
        case 'connect':
            if (edit)
                commands.push({
                    type: 'connect',
                    from: event.from || next.source,
                    to: event.to || next.target
                });
            break;
        case 'field':
        case 'attribute':
        case 'setting':
        case 'description':
        case 'moveNodes':
        case 'column':
        case 'renameInstance':
        case 'relationship':
        case 'createColumns':
        case 'reverse':
        case 'restoreDirect':
            if (edit) commands.push(event);
            break;
        case 'layout':
            if (edit && model.nodes.length)
                commands.push({
                    type: 'layout',
                    style: next.arrange
                });
            break;
        case 'nodeWorkflows':
            if (model.selectedNode) commands.push(event);
            break;
        case 'refreshColumns':
            if (!model.columnsBusy) commands.push(event);
            break;
    }
    return {
        ui: next,
        commands
    };
}
export function applied(ui, key) {
    const text = Object.assign({}, ui.text);
    delete text[key];
    return Object.assign({}, ui, {
        text,
        error: ''
    });
}
export function completed(ui, command) {
    if (command.type === 'renameInstance') return applied(ui, 'instance');
    if (
        ['reload', 'discard', 'selectPipeline', 'createWorkflow'].indexOf(
            command.type
        ) >= 0
    )
        return Object.assign({}, ui, {
            text: {},
            confirmation: '',
            pending: null,
            error: '',
            processPage: 'parameters'
        });
    if (command.type === 'addNode')
        return Object.assign({}, ui, {
            nodeName: '',
            typeToAdd: '',
            inspector: 'selection',
            processPage: 'parameters',
            error: ''
        });
    return ui;
}
