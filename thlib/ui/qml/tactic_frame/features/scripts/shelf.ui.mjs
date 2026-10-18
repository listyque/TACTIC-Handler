import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import { translate } from '../../core/strings.mjs';

export function layout(model, width, height) {
    const compact = width < 640,
        inset = compact ? 10 : 18,
        gap = 12;
    const inner = Math.max(0, width - inset * 2);
    const left = compact ? inner : Math.max(190, Math.min(280, inner * 0.25));
    const sideHeight = compact ? 182 : height - inset * 2;
    return {
        compact,
        presets: rect(inset, inset, left, sideHeight),
        editor: rect(
            compact ? inset : inset + left + gap,
            compact ? inset + sideHeight + gap : inset,
            compact ? inner : inner - left - gap,
            compact ? height - inset * 2 - sideHeight - gap : height - inset * 2
        )
    };
}

export function permissions(model) {
    const idle = !model.busy && !model.running && !model.contextChanged;
    return {
        select: idle && !model.dirty,
        edit: idle && model.canWrite && !model.uncertain,
        save:
            idle &&
            model.canWrite &&
            !model.uncertain &&
            model.ready &&
            (model.dirty || model.assignmentPending || !model.existing),
        remove: idle && model.canWrite && !model.uncertain && model.canRemove,
        assign:
            idle &&
            model.canWrite &&
            !model.dirty &&
            !model.uncertain &&
            model.assignmentPending
    };
}

export function rowHeight(width) {
    return width < 500 ? 136 : 88;
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        panes = layout(model, width, height),
        allow = permissions(model),
        p = panes.presets,
        e = panes.editor;
    const left = [],
        right = [],
        narrow = e.width < 500;
    left.push(
        node(
            'Segmented',
            'scriptShelfOwnerMode',
            rect(8, 8, p.width - 48, 34),
            {
                label: tr('Shelf owner'),
                value: model.owner,
                options: (model.canManage
                    ? ['personal', 'shared']
                    : ['personal']
                ).map((value) => ({
                    value,
                    label: tr(value === 'personal' ? 'Mine' : 'Shared'),
                    icon: value === 'personal' ? 'user' : 'users'
                })),
                enabled: allow.select,
                action: { type: 'owner' }
            }
        )
    );
    left.push(
        button(
            'scriptShelfHelpButton',
            rect(p.width - 34, 10, 26, 30),
            tr('Script shelf help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true }
        )
    );
    left.push(
        button(
            'scriptShelfGlobalPreset',
            rect(8, 50, p.width - 16, 40),
            tr(model.owner === 'shared' ? 'Shared shelf' : 'All tabs'),
            model.scope === 'global' ? 'check' : 'earth',
            { type: 'global' },
            allow.select,
            { highlighted: model.scope === 'global' }
        )
    );
    left.push(
        node('Box', 'scriptShelfGlobalDivider', rect(8, 96, p.width - 16, 1), {
            background: 'outlineVariant'
        })
    );
    left.push(
        label(
            'scriptShelfPresetsTitle',
            rect(8, 100, p.width - 52, 30),
            tr(model.owner === 'shared' ? 'Tab shelves' : 'Personal shelf'),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    if (model.owner === 'shared')
        left.push(
            button(
                'newScriptShelfButton',
                rect(p.width - 38, 100, 30, 30),
                tr('New shelf'),
                'add',
                { type: 'new' },
                allow.select && model.canWrite,
                { iconOnly: true, toolTip: tr('New shelf') }
            )
        );
    left.push(
        node(
            'List',
            'scriptShelfPresetList',
            rect(8, 136, p.width - 16, p.height - 144),
            {
                source: 'presets',
                keyField: 'value',
                fields: ['value', 'label', 'enabled', 'translate'],
                rowHeight: 42,
                rowGap: 4,
                scrollbarId: 'scriptShelfPresetScrollBar'
            }
        )
    );
    const headerHeight = model.canRename && narrow ? 84 : 40;
    right.push(
        node(
            'Field',
            'scriptShelfTitle',
            rect(
                0,
                0,
                model.canRename && !narrow
                    ? Math.max(0, e.width - 208)
                    : e.width,
                40
            ),
            {
                visible: !!model.canRename,
                label: tr('Shelf name'),
                placeholder: tr('Shelf name'),
                text: model.title || '',
                enabled: allow.edit,
                action: { type: 'title' }
            }
        )
    );
    right.push(
        label(
            'scriptShelfFixedTitle',
            rect(0, 0, e.width, 40),
            tr(model.owner === 'personal' ? 'My shelf' : 'Shared shelf'),
            { visible: !model.canRename, fontRole: 'title', weight: 600 }
        )
    );
    right.push(
        button(
            'applyScriptShelfButton',
            rect(
                narrow ? 0 : e.width - 200,
                narrow ? 44 : 0,
                narrow ? e.width : 200,
                38
            ),
            tr(
                model.assignmentPending
                    ? 'Apply to this tab'
                    : 'Used on this tab'
            ),
            '',
            { type: 'assign' },
            allow.assign,
            { visible: model.canRename && model.canAssign }
        )
    );
    right.push(
        label(
            'scriptShelfButtonsHeading',
            rect(0, headerHeight + 8, e.width - 142, 38),
            tr('Shelf buttons'),
            { weight: 600 }
        )
    );
    right.push(
        button(
            'addScriptShelfButton',
            rect(e.width - 134, headerHeight + 8, 134, 38),
            tr('Add button'),
            'add',
            { type: 'add' },
            allow.edit && model.ready && model.hasScripts
        )
    );
    const notice = model.notice || model.error || '',
        noticeHeight = notice
            ? captionHeight(notice, Math.max(1, e.width)) + 8
            : 0;
    const top = headerHeight + 54 + noticeHeight,
        footerHeight = model.ready ? 46 : 0;
    right.push(
        label(
            'scriptShelfError',
            rect(0, headerHeight + 50, e.width, noticeHeight),
            notice,
            {
                visible: !!notice,
                color: model.error ? 'error' : 'secondaryText',
                wrap: true
            }
        )
    );
    right.push(
        node(
            'Box',
            'scriptShelfButtonsSurface',
            rect(0, top, e.width, e.height - top - footerHeight),
            {
                background: 'panel',
                radius: 12,
                border: 'outlineVariant',
                borderWidth: 1,
                children: [
                    node(
                        'List',
                        'scriptShelfEditorList',
                        rect(
                            9,
                            9,
                            e.width - 18,
                            e.height - top - footerHeight - 18
                        ),
                        {
                            source: 'buttons',
                            keyField: 'buttonId',
                            fields: [
                                'buttonId',
                                'title',
                                'description',
                                'iconName',
                                'script',
                                'available'
                            ],
                            rowHeight: rowHeight(e.width - 34) + 7,
                            rowGap: 7,
                            scrollbarId: 'scriptShelfEditorScrollBar'
                        }
                    ),
                    label(
                        'scriptShelfEmptyHeading',
                        rect(12, 32, e.width - 24, 40),
                        tr(
                            model.ready
                                ? 'Add the first script button'
                                : 'No shelf selected'
                        ),
                        {
                            visible: !model.count,
                            weight: 600,
                            align: 'center',
                            wrap: true
                        }
                    ),
                    label(
                        'scriptShelfEmptyCaption',
                        rect(12, 80, e.width - 24, 54),
                        tr(
                            model.ready
                                ? 'Only saved executable scripts are listed.'
                                : 'Choose a shelf above or create a new one.'
                        ),
                        Object.assign({}, muted, {
                            visible: !model.count,
                            wrap: true,
                            align: 'center'
                        })
                    )
                ]
            }
        )
    );
    const removeLabel = translate(
        model.owner === 'personal' ? 'Remove “{name}”' : 'Delete “{name}”',
        language,
        { name: model.removeName || model.title || '' }
    );
    if (model.ready) {
        right.push(
            button(
                'deleteScriptShelfButton',
                rect(
                    0,
                    e.height - 38,
                    Math.max(0, Math.min(260, e.width - 244)),
                    38
                ),
                removeLabel,
                'delete',
                { type: 'remove' },
                allow.remove,
                {
                    visible: !!model.canRemove,
                    destructive: true,
                    toolTip: removeLabel
                }
            )
        );
        right.push(
            button(
                'discardScriptShelfButton',
                rect(e.width - 234, e.height - 38, 100, 38),
                tr('Discard'),
                'undo',
                { type: 'discard' },
                !model.busy,
                { visible: !!model.dirty }
            )
        );
        right.push(
            button(
                'saveScriptShelfButton',
                rect(e.width - 126, e.height - 38, 126, 38),
                tr('Save shelf'),
                'cloud-done',
                { type: 'save' },
                allow.save,
                { highlighted: true }
            )
        );
    }
    return {
        nodes: [
            node('Box', 'scriptShelfBackground', rect(0, 0, width, height), {
                background: 'workspace'
            }),
            node('Box', 'scriptShelfPresetPane', p, {
                background: 'panel',
                border: 'outlineVariant',
                borderWidth: 1,
                radius: 12,
                children: left
            }),
            node('Box', 'scriptShelfEditorPane', e, { children: right })
        ]
    };
}

export function scriptPicker(node, language) {
    return {
        nodes: [
            button(
                node.id + '_trigger',
                rect(0, 0, node.width, node.height),
                node.record.script || translate('Choose script', language),
                'account-tree',
                { type: 'pick' },
                node.enabled
            )
        ]
    };
}

export function row(list, record, index, model, language) {
    const tr = (text) => translate(text, language),
        width = Math.max(0, list.width - 16),
        allow = permissions(model);
    if (list.source === 'presets')
        return {
            nodes: [
                button(
                    'scriptShelfPreset_' +
                        record.value.replace(/[^a-zA-Z0-9_]/g, '_'),
                    rect(0, 0, width, 38),
                    record.translate === false
                        ? record.label
                        : tr(record.label),
                    record.value === model.selectedPreset
                        ? 'check'
                        : 'view-agenda',
                    { type: 'preset', value: record.value },
                    allow.select && record.enabled !== false,
                    {
                        highlighted: record.value === model.selectedPreset,
                        toolTip: record.label
                    }
                )
            ]
        };
    const compact = width < 500,
        titleWidth = compact
            ? Math.max(0, width - 150)
            : Math.max(120, width * 0.25),
        height = rowHeight(width);
    const event = (type, field) => ({ type, field, buttonId: record.buttonId });
    const children = [
        node(
            'IconChoice',
            'scriptShelfButtonIcon_' + index,
            rect(8, 8, 36, 36),
            {
                value: record.iconName,
                label: tr('Choose icon'),
                enabled: allow.edit,
                action: event('button', 'iconName')
            }
        ),
        node(
            'Field',
            'scriptShelfButtonTitle_' + index,
            rect(52, 8, titleWidth, 32),
            {
                text: record.title,
                label: tr('Button label'),
                placeholder: tr('Button label'),
                enabled: allow.edit,
                action: event('button', 'title')
            }
        )
    ];
    const pickerX = compact ? 52 : 58 + titleWidth,
        pickerY = compact ? 46 : 8;
    children.push(
        node(
            'View',
            'scriptShelfPicker_' + index,
            rect(
                pickerX,
                pickerY,
                compact ? width - 60 : Math.max(0, width - pickerX - 104),
                32
            ),
            {
                view: 'script',
                record,
                scopeKey: model.scopeKey,
                enabled: allow.edit
            }
        )
    );
    [
        ['up', 'Move up', 'arrow-up', index > 0],
        ['down', 'Move down', 'arrow-down', index < model.count - 1],
        ['removeButton', 'Remove button', 'delete', true]
    ].forEach((row, offset) =>
        children.push(
            button(
                'scriptShelfButton_' + row[0] + '_' + index,
                rect(width - 96 + offset * 28, 8, 26, 26),
                tr(row[1]),
                row[2],
                event(row[0]),
                allow.edit && row[3],
                { iconOnly: true, destructive: row[0] === 'removeButton' }
            )
        )
    );
    children.push(
        node(
            'Field',
            'scriptShelfButtonDescription_' + index,
            rect(52, compact ? 86 : 46, width - 60, 32),
            {
                text: record.description,
                label: tr('Description shown on hover'),
                placeholder: tr('Description shown on hover'),
                enabled: allow.edit,
                action: event('button', 'description')
            }
        )
    );
    return {
        nodes: [
            node(
                'Box',
                'scriptShelfButtonRow_' + index,
                rect(0, 0, width, height),
                {
                    background: 'row',
                    border: record.available ? 'outlineVariant' : 'error',
                    borderWidth: 1,
                    radius: 10,
                    children
                }
            )
        ]
    };
}
