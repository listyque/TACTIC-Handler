import { node, rect, label, muted } from '../../core/frame.mjs';
import { sections } from '../../controls/forms/sections.ui.mjs';
import { translate } from '../../core/strings.mjs';
import { definitions } from './settings.fields.mjs';
import { controls, spacing } from '../../core/foundation.mjs';
import * as ServerControl from './server_control.ui.mjs';

export function fieldsFor(page, model) {
    const native = model.native === true;
    let fields = (definitions[page] || [])
        .filter((field) => !field.nativeOnly || native)
        .filter(
            (field) =>
                !native ||
                model.streamApi !== false ||
                !['serverUpdateMode', 'serverUpdateBatchDelay'].includes(
                    field.field
                )
        )
        .map((field) => Object.assign({}, field));
    if (page === 'server' && !native) {
        fields = definitions.server
            .filter(
                (field) =>
                    (field.kind === 'Heading' &&
                        field.title !== 'Application updates') ||
                    [
                        'serverUpdateMode',
                        'serverUpdateBatchDelay',
                        'serverUpdateInterval'
                    ].includes(field.field)
            )
            .map((field) => Object.assign({}, field));
        fields.splice(
            1,
            0,
            {
                kind: 'Field',
                field: 'serverUrl',
                title: 'Server address',
                description:
                    'The browser uses the server that hosts this application.',
                readOnly: true
            },
            {
                kind: 'Field',
                field: 'login',
                title: 'Current account',
                readOnly: true
            }
        );
    }
    if (page === 'global') {
        const position = fields.findIndex(
            (field) => field.title === 'Diagnostics'
        );
        const levels = [
            'LOG',
            'INFO',
            'WARNING',
            'MISSING',
            'EXCEPTION',
            'ERROR',
            'CRITICAL',
            'API'
        ];
        const diagnostics = levels.map((level) => ({
            kind: 'CheckBox',
            field: 'debug_' + level,
            title: level,
            description: {
                LOG: 'General application messages.',
                INFO: 'Informational application events.',
                WARNING: 'Recoverable issues and warnings.',
                MISSING: 'Missing files and resources.',
                EXCEPTION: 'Unhandled exceptions.',
                ERROR: 'Failed requests and application errors.',
                CRITICAL: 'Critical application failures.',
                API: 'Successful API calls, including arguments, results and duration.'
            }[level]
        }));
        fields.splice(position + 1, 0, ...diagnostics);
    }
    if (page === 'checkin' && native) {
        for (const [after, definition] of [
            [
                'descriptionLimitEnabled',
                {
                    field: 'descriptionLimit',
                    title: 'Description length',
                    min: 20,
                    max: 50000,
                    step: 5
                }
            ],
            [
                'sequencePaddingEnabled',
                {
                    field: 'sequencePadding',
                    title: 'Sequence padding',
                    min: 1,
                    max: 9,
                    step: 1
                }
            ]
        ]) {
            const index = fields.findIndex((field) => field.field === after);
            fields.splice(
                index + 1,
                0,
                Object.assign(
                    { kind: 'Number', enabled: !!model.values?.[after] },
                    definition
                )
            );
        }
    }
    if (page === 'appearance' && !native)
        fields.push(
            {
                kind: 'Heading',
                id: 'browserPreferences',
                title: 'Browser preferences',
                description:
                    'Additional browser features remain available alongside the Handler layout.'
            },
            {
                kind: 'Choice',
                field: 'mode',
                title: 'Color mode',
                description:
                    'Choose light or dark surfaces, or follow the system preference.'
            },
            {
                kind: 'Choice',
                field: 'discussionView',
                title: 'Object notes',
                description:
                    'Open object and process notes in the Task Inspector, or use a separate notes-only window.',
                options: [
                    { value: 'inspector', label: 'Task Inspector' },
                    { value: 'notes', label: 'Standalone notes' }
                ]
            }
        );
    if (page === 'server' && native)
        fields.push(
            {
                kind: 'Button',
                field: 'presets',
                title: 'Manage server presets',
                props: { icon: 'settings' },
                action: { type: 'presets' }
            },
            {
                kind: 'Button',
                field: 'test',
                title: model.serverTestBusy ? 'Testing…' : 'Test connection',
                enabled: !model.serverTestBusy,
                props: { icon: 'connection' },
                action: { type: 'test' }
            },
            {
                kind: 'Button',
                field: 'signIn',
                title: 'Generate ticket',
                enabled: !model.serverTestBusy,
                props: { icon: 'user' },
                action: { type: 'signIn' }
            }
        );
    for (const field of fields) {
        if (field.field === 'clearData') {
            field.title = model.cacheBusy ? 'Clearing…' : 'Clear cache';
            field.enabled = !model.cacheBusy;
            field.props = { icon: 'delete-sweep', destructive: true };
        }
        if (model.options?.[field.field])
            field.options = model.options[field.field];
        const selected = field.options?.find(
            (option) => option.value === model.values?.[field.field]
        );
        if (selected?.description) field.description = selected.description;
        if (
            ['previewsThroughHttp', 'checkinMethod', 'checkoutMethod'].includes(
                field.field
            )
        )
            field.description = model.values?.teamLocalRepository
                ? 'Locked by TACTIC TEAM Mode in the active server preset.'
                : {
                      previewsThroughHttp:
                          'Load preview files through the TACTIC HTTP endpoint instead of relying only on repository access.',
                      checkinMethod:
                          'Choose whether new files are preallocated, kept in place, copied, moved, or uploaded.',
                      checkoutMethod:
                          'Use direct local repository access or download files through the TACTIC HTTP endpoint.'
                  }[field.field];
        if (field.field === 'displayLimit' && !native) {
            field.min = 1;
            field.max = 500;
            field.step = 1;
        }
        if (field.field === 'serverUpdateInterval')
            field.when = model.values?.serverUpdateMode !== 'sse';
        if (field.field === 'serverUpdateBatchDelay')
            field.when = model.values?.serverUpdateMode === 'sse';
        if (
            field.field === 'previewsThroughHttp' &&
            model.values?.teamLocalRepository
        )
            field.enabled = false;
        if (
            ['checkinMethod', 'checkoutMethod'].includes(field.field) &&
            model.values?.teamLocalRepository
        )
            field.enabled = false;
        if (field.field === 'descriptionLimit')
            field.enabled = !!model.values?.descriptionLimitEnabled;
    }
    const result = [];
    let heading = null;
    for (const field of fields) {
        if (field.kind === 'Heading') heading = field;
        else {
            if (heading) result.push(heading);
            heading = null;
            result.push(field);
        }
    }
    return result;
}

export function dccFields(schema) {
    const fields = [];
    for (const [index, section] of (schema.sections || []).entries()) {
        fields.push({
            kind: 'Heading',
            id: 'dccSection' + index,
            title: section.title,
            description: section.description
        });
        for (const field of section.fields || [])
            fields.push({
                kind:
                    {
                        boolean: 'Switch',
                        choice: 'Choice',
                        integer: 'Number',
                        text: 'Field'
                    }[field.type] || 'Field',
                field: field.key,
                title: field.title || field.key,
                description: field.description,
                options: field.choices,
                min: field.minimum ?? 0,
                max: field.maximum ?? 999999,
                step: 1,
                readOnly: !!field.read_only,
                enabled: !field.read_only
            });
    }
    return fields;
}

export function change(values, action, fields) {
    const definition = fields.find((field) => field.field === action.field);
    if (!definition)
        throw Error('Unknown Configuration field: ' + action.field);
    let value = action.value;
    if (definition.kind === 'Number') {
        value =
            action.type === 'step'
                ? Number(values[action.field]) + Number(action.value)
                : Number(action.value);
        if (!Number.isFinite(value)) return values;
        if (action.type === 'step')
            value = Math.max(
                definition.min,
                Math.min(definition.max, Math.round(value))
            );
    }
    return Object.assign({}, values, { [action.field]: value });
}

export function field(definition, values, options, language, busy) {
    const result = Object.assign({}, definition);
    result.id = definition.id || 'setting_' + definition.field;
    if (result.kind === 'Heading') return result;
    const value = values[definition.field];
    result.value = value;
    const choices = definition.options || options?.[definition.field] || [];
    result.options = choices.map((option) => ({
        value: option.value,
        label: option.dataLabel
            ? option.label
            : translate(option.label, language)
    }));
    result.props = Object.assign({}, definition.props, {
        enabled: !busy && definition.enabled !== false,
        text: value === null || value === undefined ? '' : String(value),
        value,
        checked: !!value,
        readOnly: !!definition.readOnly,
        action: definition.action || { type: 'field', field: definition.field }
    });
    if (definition.kind === 'Button')
        result.props.text = translate(definition.title, language);
    if (['Switch', 'CheckBox'].includes(definition.kind))
        result.props.text = translate(definition.title, language);
    return result;
}

export function contentWidth(width) {
    return Math.max(
        1,
        width -
            Math.min(spacing.content, width / 12) * 2 -
            controls.scrollBar.extent
    );
}

export function describe(model, width, height, language) {
    const margin = Math.min(spacing.content, width / 12),
        viewportWidth = Math.max(1, width - margin * 2),
        inner = contentWidth(width);
    const fields = model.fields.map((definition) => {
        const result = field(
            definition,
            model.values || {},
            model.options,
            language,
            model.busy
        );
        if (['lightAccent', 'darkAccent'].includes(definition.field)) {
            result.controlWidth = Math.min(380, inner - 48);
            const columns = Math.max(
                1,
                Math.floor((result.controlWidth + 7) / 43)
            );
            const rows = Math.ceil((model.paletteCount || 19) / columns);
            result.height = rows * 36 + Math.max(0, rows - 1) * 7;
        }
        return result;
    });
    const form = sections(fields, inner, language, !model.busy, model.style);
    const nodes = [];
    let top = spacing.content;
    for (const [id, message, color] of [
        ['Error', model.error, 'error'],
        ['Notice', model.notice, 'secondaryText']
    ]) {
        if (!message) continue;
        const rows = Math.max(1, Math.ceil((message.length * 7) / inner));
        nodes.push(
            label(
                'configuration' + id,
                rect(0, top, inner, rows * 20),
                message,
                { color, wrap: true, role: id === 'Error' ? 'alert' : 'status' }
            )
        );
        top += rows * 20 + 12;
    }
    if (model.serverControls) {
        const height = ServerControl.describe({}, inner, language).height;
        nodes.push(
            node(
                'View',
                'configurationServerControl',
                rect(0, top, inner, height),
                { view: 'serverControl' }
            )
        );
        top += height + spacing.section;
    }
    for (const item of form.nodes)
        nodes.push(Object.assign({}, item, { y: item.y + top }));
    let bottom = top + form.height;
    for (const [index, column] of (model.columns || []).entries()) {
        const rowHeight = inner < 450 ? 86 : 48,
            compact = inner < 450;
        const row = [
            node(
                'CheckBox',
                'configurationColumn_' + column.key,
                rect(8, 5, compact ? inner - 16 : inner - 204, 36),
                {
                    text: translate(column.label, language),
                    checked: column.visible,
                    enabled:
                        !model.busy &&
                        !column.required &&
                        column.key !== 'object',
                    action: { type: 'columnVisible', key: column.key }
                }
            ),
            node(
                'Field',
                'configurationWidth_' + column.key,
                rect(inner - 190, compact ? 44 : 5, 100, 36),
                {
                    label: translate('Width', language),
                    text: String(column.width),
                    enabled: !model.busy,
                    action: { type: 'columnWidth', key: column.key }
                }
            ),
            node(
                'Button',
                'configurationUp_' + column.key,
                rect(inner - 82, compact ? 44 : 5, 34, 34),
                {
                    text: translate('Move column up', language),
                    icon: 'up',
                    iconOnly: true,
                    enabled: !model.busy && index > 0,
                    action: {
                        type: 'columnMove',
                        key: column.key,
                        direction: -1
                    }
                }
            ),
            node(
                'Button',
                'configurationDown_' + column.key,
                rect(inner - 42, compact ? 44 : 5, 34, 34),
                {
                    text: translate('Move column down', language),
                    icon: 'down',
                    iconOnly: true,
                    enabled: !model.busy && index < model.columns.length - 1,
                    action: {
                        type: 'columnMove',
                        key: column.key,
                        direction: 1
                    }
                }
            )
        ];
        nodes.push(
            node(
                'Box',
                'configurationColumnRow_' + column.key,
                rect(0, bottom, inner, rowHeight),
                { background: 'surfaceContainerLow', children: row }
            )
        );
        bottom += rowHeight + 4;
    }
    return {
        nodes: [
            node(
                'Scroll',
                'configurationSettings',
                rect(margin, 0, viewportWidth, height),
                {
                    contentHeight: bottom + spacing.content,
                    scrollbarId: 'configurationSettingsScrollBar',
                    children: nodes
                }
            )
        ]
    };
}

export function editColumn(columns, action) {
    const result = columns.map((column) => Object.assign({}, column));
    const index = result.findIndex((column) => column.key === action.key);
    if (index < 0) throw Error('Unknown task column: ' + action.key);
    if (action.type === 'columnMove') {
        const target = index + action.direction;
        if (target >= 0 && target < result.length)
            result.splice(target, 0, result.splice(index, 1)[0]);
    } else if (
        action.type === 'columnVisible' &&
        !result[index].required &&
        result[index].key !== 'object'
    )
        result[index].visible = action.value;
    else if (action.type === 'columnWidth')
        result[index].width = Number(action.value);
    return result;
}
