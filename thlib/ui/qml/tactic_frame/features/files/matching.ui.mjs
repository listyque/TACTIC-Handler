import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import { controls } from '../../core/foundation.mjs';

export function testResult(text, language, matchedType) {
    return text.startsWith('Matched as ')
        ? translate('Matched as {type}', language, {
              type: matchedType || text.slice(11)
          })
        : translate(text, language);
}

export function actions(model) {
    const selected = model.selected >= 0;
    return [
        {
            title: 'Duplicate',
            icon: 'copy',
            command: 'duplicate',
            enabled: selected && !model.busy && model.canAdd !== false
        },
        {
            title: 'Move up',
            icon: 'arrow-up',
            command: 'move_up',
            enabled: selected && model.selected > 0 && !model.busy
        },
        {
            title: 'Move down',
            icon: 'arrow-down',
            command: 'move_down',
            enabled: selected && model.selected < model.count - 1 && !model.busy
        },
        {
            title: 'Delete',
            icon: 'delete',
            command: 'delete',
            enabled: selected && !model.record?.locked && !model.busy
        }
    ];
}

export function layout(model, width, height) {
    const compact = width < 620,
        inset = 12,
        gap = 10;
    const available = Math.max(0, width - inset * 2);
    const left = compact
        ? available
        : Math.max(
              200,
              Math.min(
                  model.paneWidth || Math.max(300, width * 0.48),
                  available - gap - 260
              )
          );
    return {
        compact,
        list: rect(inset, inset, left, height - inset * 2),
        editor: rect(
            compact ? inset : inset + left + gap,
            inset,
            compact ? available : available - left - gap,
            height - inset * 2
        ),
        showList: !compact || !model.editing,
        showEditor: !compact || model.editing,
        splitter: rect(inset + left, inset, gap, height - inset * 2)
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        bounds = layout(model, width, height),
        nodes = [];
    if (bounds.showList) {
        const w = bounds.list.width,
            compact = w < 400,
            children = [];
        const tools = actions(model),
            count = compact ? 2 : 5,
            extent = controls.iconButton.extent,
            stride = extent + 5,
            start = w - 9 - count * stride + 5;
        children.push(
            label(
                'matchingTemplatesHeading',
                rect(9, 9, Math.max(0, start - 14), extent),
                tr('Matching templates'),
                { fontRole: 'secondary', weight: 600 }
            )
        );
        children.push(
            button(
                'matchingTemplatesAdd',
                rect(start, 9, extent, extent),
                tr('Add'),
                'add',
                { type: 'create' },
                !model.busy && model.canAdd !== false,
                { iconOnly: true, iconAction: true }
            )
        );
        if (compact)
            children.push(
                button(
                    'matchingTemplatesOverflowButton',
                    rect(start + stride, 9, extent, extent),
                    tr('Template actions'),
                    'more',
                    { type: 'menu' },
                    !model.busy,
                    { iconOnly: true, iconAction: true }
                )
            );
        else
            tools.forEach((action, index) =>
                children.push(
                    button(
                        'matchingTemplate_' + action.command,
                        rect(start + (index + 1) * stride, 9, extent, extent),
                        tr(action.title),
                        action.icon,
                        { type: action.command },
                        action.enabled,
                        { iconOnly: true, iconAction: true }
                    )
                )
            );
        children.push(
            node(
                'List',
                'matchingTemplatesList',
                rect(9, 44, w - 18, bounds.list.height - 53),
                {
                    source: 'templates',
                    keyField: 'templateId',
                    rowHeight: 69,
                    rowGap: 5,
                    label: tr('Matching templates'),
                    fields: [
                        'templateId',
                        'templateEnabled',
                        'pattern',
                        'preview',
                        'matchingType',
                        'process',
                        'context',
                        'locked',
                        'selected',
                        'priority',
                        'validationError'
                    ]
                }
            )
        );
        nodes.push(
            node('Box', 'matchingTemplatesListPanel', bounds.list, {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 16,
                children
            })
        );
    }
    if (!bounds.compact)
        nodes.push(
            node('Splitter', 'matchingTemplatesSplitter', bounds.splitter, {
                label: tr('Templates pane width'),
                value: bounds.list.width,
                min: 200,
                max: Math.max(200, width - 294),
                action: { type: 'splitter' }
            })
        );
    if (bounds.showEditor) {
        const w = bounds.editor.width,
            h = bounds.editor.height,
            footerHeight = w < 330 ? 64 : 38,
            children = [];
        const form = properties(
            Object.assign({}, model, {
                editing: bounds.compact && model.editing
            }),
            Math.max(0, w - 44),
            language
        );
        children.push(
            node(
                'Scroll',
                'matchingTemplatesEditorScroll',
                rect(14, 14, w - 28, Math.max(0, h - footerHeight - 38)),
                { contentHeight: form.height, children: form.nodes }
            )
        );
        if (model.dirty)
            children.push(
                label(
                    'matchingTemplatesDirty',
                    rect(
                        14,
                        h - footerHeight - 14,
                        w < 330 ? w - 28 : w - 238,
                        20
                    ),
                    tr('Unsaved changes'),
                    { fontRole: 'secondary', color: 'yellow' }
                )
            );
        const footerY = h - 52;
        children.push(
            button(
                'matchingTemplatesCancel',
                rect(w - 254, footerY, 110, 38),
                tr('Cancel'),
                '',
                { type: 'close' },
                !model.busy
            )
        );
        children.push(
            button(
                'matchingTemplatesSave',
                rect(w - 134, footerY, 120, 38),
                tr('Save'),
                'save',
                { type: 'save' },
                !!model.dirty && !model.busy,
                { highlighted: true }
            )
        );
        nodes.push(
            node('Box', 'matchingTemplatesEditorPanel', bounds.editor, {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 16,
                children
            })
        );
    }
    return { nodes };
}

export function properties(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        record = model.record || {},
        enabled = model.selected >= 0 && !model.busy;
    const children = [],
        headingX = model.editing ? 36 : 0;
    if (model.editing)
        children.push(
            button(
                'matchingTemplatesBack',
                rect(0, 0, 28, 28),
                tr('Back'),
                'arrow-left',
                { type: 'back' },
                !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
    children.push(
        label(
            'matchingTemplatesProperties',
            rect(headingX, 0, width - headingX, 28),
            tr('Template properties'),
            { fontRole: 'bodyLarge', weight: 600, role: 'heading' }
        )
    );
    children.push(
        label('matchingPatternLabel', rect(0, 38, width, 18), tr('Pattern'), {
            fontRole: 'secondary',
            color: 'secondaryText'
        })
    );
    children.push(
        node('Field', 'matchingPattern', rect(0, 62, width, 36), {
            label: tr('Pattern'),
            text: record.pattern || '',
            enabled: enabled && !record.locked,
            action: { type: 'field', field: 'pattern' },
            commitAction: { type: 'validate' }
        })
    );
    const preview =
        record.validationError ||
        tr('Preview: {preview} · Type: {type}', {
            preview: record.preview || '—',
            type: record.matchingType || '—'
        });
    const previewHeight = Math.max(30, captionHeight(preview, width));
    children.push(
        label(
            'matchingPatternPreview',
            rect(0, 108, width, previewHeight),
            preview,
            {
                fontRole: 'secondary',
                wrap: true,
                color: record.validationError ? 'error' : 'secondaryText'
            }
        )
    );
    let y = 108 + previewHeight + 10;
    const stacked = width < 316;
    for (const [field, title, empty, options] of [
        ['process', 'Process mapping', 'All processes', model.processes || []],
        ['context', 'Context mapping', 'All contexts', model.contexts || []]
    ]) {
        children.push(
            label(
                'matching_' + field + 'Label',
                rect(0, y, stacked ? width : 122, stacked ? 18 : 36),
                tr(title),
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
        children.push(
            node(
                'Choice',
                'matching_' + field,
                rect(
                    stacked ? 0 : 132,
                    y + (stacked ? 24 : 0),
                    stacked ? width : width - 132,
                    36
                ),
                {
                    label: tr(title),
                    placeholder: tr(empty),
                    editable: true,
                    value: record[field] || '',
                    options: [
                        { value: '', label: tr(empty) },
                        ...options.map((option) =>
                            typeof option === 'string'
                                ? { value: option, label: option }
                                : option
                        )
                    ],
                    enabled: enabled && !record.locked,
                    action: { type: 'field', field }
                }
            )
        );
        y += stacked ? 70 : 46;
    }
    children.push(
        label(
            'matchingExampleLabel',
            rect(0, y, width, 18),
            tr('Test on filename'),
            { fontRole: 'secondary', color: 'secondaryText' }
        )
    );
    y += 24;
    const testBelow = width < 316;
    children.push(
        node(
            'Field',
            'matchingExample',
            rect(0, y, testBelow ? width : width - 94, 36),
            {
                label: tr('Test on filename'),
                placeholder: 'shot.001.exr',
                text: model.example || '',
                action: { type: 'example' },
                keys: { Enter: { type: 'test' } },
                enabled: !model.busy
            }
        )
    );
    children.push(
        button(
            'matchingTest',
            rect(
                testBelow ? Math.max(0, width - 84) : width - 84,
                y + (testBelow ? 44 : 0),
                84,
                36
            ),
            tr('Test'),
            'science',
            { type: 'test' },
            enabled
        )
    );
    y += testBelow ? 90 : 46;
    for (const [id, text, error] of [
        ['matchingTestResult', model.result, model.result === tr('No match')],
        ['matchingTemplateError', model.error, true]
    ]) {
        if (!text) continue;
        const height = Math.max(20, captionHeight(text, width));
        children.push(
            label(id, rect(0, y, width, height), text, {
                fontRole: 'secondary',
                wrap: true,
                color: error ? 'error' : 'secondaryText',
                role: error ? 'alert' : 'status'
            })
        );
        y += height + 10;
    }
    return { nodes: children, height: y };
}

export function row(model, record, width, language) {
    const tr = (text) => translate(text, language),
        titleWidth = Math.max(0, width - 98),
        index = record.priority;
    return {
        nodes: [
            node('Box', 'matchingTemplateDelegate', rect(0, 0, width, 64), {
                children: [
                    node(
                        'Action',
                        'matchingTemplateSelect_' + record.templateId,
                        rect(0, 0, width, 64),
                        {
                            text: record.pattern,
                            selected: !!record.selected,
                            normalColor: 'surfaceContainerHigh',
                            selectedColor: 'secondaryContainer',
                            radius: 12,
                            action: { type: 'select', index },
                            keys: {
                                ArrowUp: {
                                    type: 'select',
                                    index: Math.max(0, index - 1),
                                    focus: true
                                },
                                ArrowDown: {
                                    type: 'select',
                                    index: Math.min(model.count - 1, index + 1),
                                    focus: true
                                },
                                Home: { type: 'select', index: 0, focus: true },
                                End: {
                                    type: 'select',
                                    index: model.count - 1,
                                    focus: true
                                }
                            },
                            children: [
                                label(
                                    'matchingPriority_' + record.templateId,
                                    rect(55, 0, 12, 64),
                                    String(index + 1),
                                    {
                                        fontRole: 'secondary',
                                        color: 'disabledText',
                                        align: 'center'
                                    }
                                ),
                                label(
                                    'matchingPattern_' + record.templateId,
                                    rect(71, 6, titleWidth, 20),
                                    record.pattern,
                                    {
                                        weight: 600,
                                        elideMiddle: true,
                                        color: record.validationError
                                            ? 'error'
                                            : 'primaryText'
                                    }
                                ),
                                label(
                                    'matchingPreview_' + record.templateId,
                                    rect(71, 27, titleWidth, 15),
                                    record.validationError ||
                                        record.preview ||
                                        '',
                                    {
                                        fontRole: 'secondary',
                                        color: record.validationError
                                            ? 'error'
                                            : 'secondaryText'
                                    }
                                ),
                                label(
                                    'matchingType_' + record.templateId,
                                    rect(71, 44, titleWidth, 14),
                                    (record.matchingType || '') +
                                        (record.process
                                            ? ' • ' + record.process
                                            : '') +
                                        (record.context
                                            ? ' / ' + record.context
                                            : ''),
                                    {
                                        fontRole: 'caption',
                                        color: 'disabledText'
                                    }
                                ),
                                node(
                                    'Icon',
                                    'matchingLock_' + record.templateId,
                                    rect(width - 22, 24, 16, 16),
                                    {
                                        icon: record.locked
                                            ? 'lock'
                                            : 'drag-handle',
                                        color: 'secondaryText'
                                    }
                                )
                            ]
                        }
                    ),
                    node(
                        'CheckBox',
                        'matchingEnabled_' + record.templateId,
                        rect(8, 14, 36, 36),
                        {
                            label: tr('Enable template'),
                            indicatorX: 6,
                            checked: !!record.templateEnabled,
                            enabled: !record.locked && !model.busy,
                            action: { type: 'enabled', index }
                        }
                    )
                ]
            })
        ]
    };
}
