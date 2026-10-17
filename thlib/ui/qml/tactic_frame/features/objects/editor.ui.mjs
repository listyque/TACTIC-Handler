import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

export function header(model, width, language) {
    const tr = (text) => translate(text, language),
        compact = width < 660,
        height = compact ? 90 : 98,
        margin = compact ? 16 : 22;
    const actions =
        model.mode === 'insert'
            ? Math.min(238, Math.max(80, width - margin * 2 - 142))
            : 0;
    const refreshX = width - margin - 28,
        modeX = refreshX - 8 - actions;
    const textWidth = Math.max(
        0,
        (model.mode === 'insert'
            ? modeX
            : refreshX - (model.mode === 'edit' ? 60 : 0)) -
            margin -
            57 -
            10
    );
    const nodes = [
        node('Box', 'sobjectEditorHeader', rect(0, 0, width, height), {
            background: 'surfaceContainerLow'
        }),
        node(
            'Box',
            'sobjectEditorIconSurface',
            rect(margin, (height - 44) / 2, 44, 44),
            {
                background: 'secondaryContainer',
                children: [
                    node('Icon', 'sobjectEditorIcon', rect(11, 11, 22, 22), {
                        icon: 'sobject',
                        color: 'action'
                    })
                ]
            }
        ),
        label(
            'sobjectEditorTitle',
            rect(margin + 57, model.parentTitle ? 14 : 22, textWidth, 24),
            model.title ||
                tr(model.mode === 'edit' ? 'Edit record' : 'Create record'),
            { fontRole: 'bodyLarge', weight: 600 }
        ),
        label(
            'sobjectEditorType',
            rect(
                margin + 57,
                model.parentTitle ? 40 : 48,
                Math.max(0, width - margin * 2 - 57),
                20
            ),
            model.searchType || '',
            { elideMiddle: true, color: 'secondaryText' }
        )
    ];
    if (model.parentTitle)
        nodes.push(
            label(
                'sobjectEditorParent',
                rect(margin + 57, 63, Math.max(0, width - margin * 2 - 57), 18),
                tr('Parent') + ': ' + model.parentTitle,
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    if (model.mode === 'insert')
        nodes.push(
            node(
                'Segmented',
                'sobjectCreateMode',
                rect(modeX, 18, actions, 36),
                {
                    label: tr('Create mode'),
                    options: [
                        { value: 'single', label: tr('One'), icon: 'sobject' },
                        {
                            value: 'batch',
                            label: tr('Multiple'),
                            icon: 'control-point-duplicate',
                            enabled: model.batchAllowed !== false
                        }
                    ],
                    value: model.batchEnabled ? 'batch' : 'single',
                    iconOnly: compact,
                    enabled: !model.busy,
                    action: { type: 'mode' }
                }
            )
        );
    if (model.mode === 'edit')
        nodes.push(
            node(
                'Box',
                'sobjectEditorModeBadge',
                rect(refreshX - 63, 24, 50, 25),
                {
                    background: 'secondaryContainer',
                    radius: 12.5,
                    children: [
                        label(
                            'sobjectEditorModeLabel',
                            rect(4, 3, 42, 19),
                            tr('Edit'),
                            {
                                align: 'center',
                                fontRole: 'caption',
                                color: 'action'
                            }
                        )
                    ]
                }
            )
        );
    nodes.push(
        button(
            'sobjectEditorRefresh',
            rect(refreshX, 22, 28, 28),
            tr('Reload schema'),
            'refresh',
            { type: 'refresh' },
            !model.busy && !model.dirty && !model.uncertain,
            { iconOnly: true, iconAction: true }
        )
    );
    return { height, nodes };
}

export function tools(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let y = 0;
    if (model.error || model.busy) {
        const text = tr(model.error || 'Loading data…'),
            height = Math.max(
                40,
                captionHeight(text, Math.max(1, width - 24)) + 20
            );
        nodes.push(
            label(
                'sobjectEditorMessage',
                rect(12, 10, Math.max(0, width - 24), height - 20),
                text,
                {
                    wrap: true,
                    color: model.error ? 'error' : 'secondaryText',
                    role: model.error ? 'alert' : 'status'
                }
            )
        );
        y += height + 10;
    }
    if (
        model.mode === 'insert' &&
        model.batchAllowed === false &&
        model.fieldCount
    ) {
        const text = tr(model.batchReason);
        const height = captionHeight(text, Math.max(1, width - 24)) + 12;
        nodes.push(
            label(
                'sobjectBatchCapability',
                rect(12, y, Math.max(0, width - 24), height),
                text,
                { wrap: true, fontRole: 'caption', color: 'secondaryText' }
            )
        );
        y += height + 10;
    }
    if (model.batchEnabled && !model.batchPreview) {
        const narrow = width < 660,
            caption =
                tr(
                    'Place the caret in a text field and insert a number format. Numbers are substituted during preview.'
                ) +
                (model.batchExample
                    ? '  ' + tr('Name preview') + ': ' + model.batchExample
                    : '');
        const captionY = narrow ? 96 : 56,
            height =
                captionY + captionHeight(caption, Math.max(1, width - 28)) + 18;
        const children = [
            label(
                'sobjectBatchCountLabel',
                rect(14, 14, narrow ? width - 154 : 150, 32),
                tr('Number of objects'),
                {}
            ),
            node(
                'View',
                'sobjectBatchCount',
                rect(narrow ? width - 126 : 174, 14, 112, 32),
                { view: 'batchCount' }
            )
        ];
        const start = narrow ? 14 : Math.max(300, width - 332),
            cell = narrow ? Math.max(0, (width - 52) / 4) : 70;
        ['{n}', '{n:02}', '{n:03}', '{n:04}'].forEach((token, index) =>
            children.push(
                button(
                    'sobjectBatchToken_' + index,
                    rect(
                        start + index * (cell + 8),
                        narrow ? 54 : 14,
                        cell,
                        32
                    ),
                    token,
                    '',
                    { type: 'token', value: token },
                    !model.busy,
                    { translate: false, retainFocus: true }
                )
            )
        );
        children.push(
            label(
                'sobjectBatchHint',
                rect(14, captionY, width - 28, height - captionY - 12),
                caption,
                { wrap: true, color: 'secondaryText', fontRole: 'caption' }
            )
        );
        nodes.push(
            node('Box', 'sobjectBatchSetup', rect(0, y, width, height), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
        y += height + 10;
    }
    if (model.batchPreview) {
        nodes.push(
            node('Box', 'sobjectBatchNavigator', rect(0, y, width, 58), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children: [
                    button(
                        'sobjectBatchPrevious',
                        rect(9, 13, 32, 32),
                        tr('Previous object'),
                        'chevron-left',
                        { type: 'item', value: model.batchIndex - 1 },
                        !model.busy && model.batchIndex > 0,
                        { iconOnly: true }
                    ),
                    label(
                        'sobjectBatchPosition',
                        rect(49, 8, Math.max(0, width - 98), 22),
                        translate('Object {index} of {total}', language, {
                            index: model.batchIndex + 1,
                            total: model.batchTotal
                        }),
                        { align: 'center', weight: 600 }
                    ),
                    label(
                        'sobjectBatchInstructions',
                        rect(49, 31, Math.max(0, width - 98), 18),
                        tr(
                            'Edit any fields for this object, then move to the next one.'
                        ),
                        {
                            align: 'center',
                            fontRole: 'caption',
                            color: 'secondaryText'
                        }
                    ),
                    button(
                        'sobjectBatchNext',
                        rect(width - 41, 13, 32, 32),
                        tr('Next object'),
                        'chevron-right',
                        { type: 'item', value: model.batchIndex + 1 },
                        !model.busy && model.batchIndex < model.batchTotal - 1,
                        { iconOnly: true }
                    )
                ]
            })
        );
        y += 68;
    } else {
        nodes.push(
            label(
                'sobjectEditorFieldsTitle',
                rect(0, y, Math.max(0, width - 48), 26),
                tr('Object fields'),
                { fontRole: 'bodyLarge', weight: 600 }
            ),
            label(
                'sobjectEditorFieldCount',
                rect(width - 44, y, 44, 26),
                String(model.fieldCount || 0),
                { align: 'right', color: 'secondaryText' }
            )
        );
        y += 36;
    }
    return { height: y, nodes };
}

export function footer(model, width, language) {
    const tr = (text) => translate(text, language),
        compact = width < 660,
        margin = compact ? 16 : 22;
    const submit =
        model.submitLabel ||
        (model.mode === 'edit'
            ? tr('Save changes')
            : model.batchPreview
              ? translate('Create {count} objects', language, {
                    count: model.batchTotal
                })
              : model.batchEnabled
                ? translate('Preview {count} objects', language, {
                      count: model.batchCount
                  })
                : tr('Create'));
    const submitWidth = Math.min(
            width * 0.52,
            Math.max(72, submit.length * 6 + 32)
        ),
        backWidth = model.batchPreview ? 86 : 0,
        closeWidth = 72,
        submitX = width - margin - submitWidth;
    const nodes = [
        node('Box', 'sobjectEditorFooter', rect(0, 0, width, 58), {
            background: 'surfaceContainer',
            radius: 0
        }),
        button(
            'sobjectEditorCancel',
            rect(
                Math.max(margin, submitX - closeWidth - backWidth - 8),
                14,
                closeWidth,
                36
            ),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        ),
        button(
            'sobjectEditorSubmit',
            rect(submitX, 14, submitWidth, 36),
            model.busy ? tr('Saving…') : submit,
            '',
            { type: 'submit' },
            !model.busy &&
                !model.uncertain &&
                model.valid !== false &&
                model.fieldCount > 0 &&
                model.canSave !== false,
            { highlighted: true }
        )
    ];
    if (model.batchPreview)
        nodes.push(
            button(
                'sobjectBatchBack',
                rect(submitX - backWidth - 4, 14, backWidth - 4, 36),
                tr('Back'),
                '',
                { type: 'back' },
                !model.busy
            )
        );
    nodes.push(
        node('Icon', 'sobjectEditorValidityIcon', rect(margin, 22, 16, 16), {
            icon: model.valid === false ? 'warning' : 'check-circle',
            color: model.valid === false ? 'error' : 'secondaryText'
        })
    );
    if (!compact)
        nodes.push(
            label(
                'sobjectEditorValidity',
                rect(
                    margin + 24,
                    16,
                    Math.max(0, submitX - closeWidth - backWidth - margin - 22),
                    32
                ),
                tr(
                    model.valid === false
                        ? 'Correct the highlighted fields'
                        : 'Ready to save'
                ),
                { color: model.valid === false ? 'error' : 'secondaryText' }
            )
        );
    return { height: 58, nodes };
}

export function batchDrafts(draft, fields, count) {
    if (!Number.isInteger(count) || count < 2 || count > 100)
        throw Error('Choose between 2 and 100 objects');
    return Array.from({ length: count }, (_, index) => {
        const result = JSON.parse(JSON.stringify(draft));
        for (const field of fields)
            if (
                !field.readOnly &&
                ['string', 'multiline'].includes(field.type) &&
                typeof result[field.name] === 'string'
            )
                result[field.name] = numberedValue(
                    result[field.name],
                    index + 1
                );
        return result;
    });
}

export function numberedValue(value, number) {
    return String(value).replace(/\{n(?::0([1-9]))?\}/g, (_, digits) =>
        String(number).padStart(Number(digits) || 0, '0')
    );
}
export function batchExample(value, count) {
    return /\{n(?::0([1-9]))?\}/.test(value)
        ? numberedValue(value, 1) + ' … ' + numberedValue(value, count)
        : '';
}
