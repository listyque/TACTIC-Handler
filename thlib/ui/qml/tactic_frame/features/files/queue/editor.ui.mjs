import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';
import { fileName } from '../file_values.mjs';
import { describe as summary } from './summary.ui.mjs';

export function versionValue(text) {
    return /^\d*$/.test(text) && Number(text) <= 9999
        ? Number(text || 0)
        : null;
}

export function namingRows(record, language) {
    const tr = (text) => translate(text, language),
        rows = [];
    for (const [index, file] of (record.naming || []).entries()) {
        rows.push({
            key: 'heading_' + index,
            text: file.title || fileName(file.source),
            heading: true
        });
        for (const [type, paths, empty] of [
            ['Versioned', file.versioned || [], 'Waiting for naming preview'],
            ['Versionless', file.versionless || [], 'Not generated']
        ])
            (paths.length ? paths : [tr(empty)]).forEach((path, member) => {
                rows.push({
                    key: type + '_' + index + '_' + member,
                    text: tr(type) + '  ' + path,
                    heading: false
                });
            });
    }
    return rows;
}

export function namingRow(record, width) {
    return {
        nodes: [
            label(
                'commitQueueNaming_' + record.key,
                rect(6, 0, width - 12, 22),
                record.text,
                {
                    fontRole: record.heading ? 'secondary' : 'caption',
                    color: record.heading ? 'primaryText' : 'secondaryText',
                    weight: record.heading ? 600 : 400,
                    elideMiddle: true,
                    toolTip: record.text
                }
            )
        ]
    };
}

export function describe(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        record = model.record || {},
        nodes = [],
        editable = !model.busy && !!record.canEdit,
        inner = Math.max(0, width - 22);
    let y = 0;
    if (model.count > 1) {
        const h =
            Math.max(
                36,
                captionHeight(
                    tr('Apply every edit to checked items'),
                    width - 52
                )
            ) + 16;
        nodes.push(
            node('Box', 'commitQueueBatchEdit', rect(0, y, width, h), {
                background: model.applyChecked
                    ? 'secondaryContainer'
                    : 'surfaceContainerLow',
                radius: 12,
                children: [
                    node(
                        'CheckBox',
                        'commitQueueApplyToChecked',
                        rect(8, 8, width - 16, h - 16),
                        {
                            text: tr('Apply every edit to checked items'),
                            checked: !!model.applyChecked,
                            enabled: !model.busy,
                            description: tr(
                                'The current item and all checked operations will receive each edit.'
                            ),
                            action: { type: 'applyChecked' }
                        }
                    )
                ]
            })
        );
        y += h + 8;
    }
    const header = summary(model, width, language);
    nodes.push(
        node(
            'Box',
            'commitQueueSummarySlot',
            rect(0, y, width, header.height),
            { children: header.nodes }
        )
    );
    y += header.height + 8;
    const settings = [],
        top = y;
    let sy = 11;
    settings.push(
        label('commitQueueBasicHeading', rect(11, sy, inner, 20), tr('BASIC'), {
            fontRole: 'secondary',
            color: 'secondaryText',
            weight: 600,
            letterSpacing: 0.5
        })
    );
    sy += 26;
    settings.push(
        node('View', 'commitQueueDescription', rect(11, sy, inner, 72), {
            view: 'description'
        })
    );
    sy += 82;
    settings.push(
        button(
            'commitQueueAdvancedToggle',
            rect(11, sy, inner, 38),
            tr('Advanced options'),
            model.advanced ? 'expand-more' : 'chevron-right',
            { type: 'advanced' },
            true,
            { tonal: true }
        )
    );
    sy += 46;
    if (model.advanced) {
        const columns = inner >= 690 ? 2 : 1,
            cellWidth = (inner - (columns - 1) * 10) / columns,
            labelWidth = Math.min(110, cellWidth * 0.34);
        const fields = [
            {
                field: 'repository',
                title: 'Repository',
                kind: 'Choice',
                value: record.repository,
                options: model.repositories || [],
                active: record.canRepository !== false
            },
            {
                field: 'version',
                title: 'Version',
                kind: 'Field',
                text:
                    model.versionDraft == null
                        ? record.version > 0
                            ? String(record.version)
                            : ''
                        : model.versionDraft,
                placeholder: tr('Automatic version'),
                active: record.canVersion !== false && !record.onlyVersionless
            },
            {
                field: 'mode',
                title: 'Method',
                kind: 'Choice',
                value: record.mode || 'upload',
                options: [
                    ['preallocate', 'Preallocate'],
                    ['inplace', 'In-Place'],
                    ['copy', 'Copy'],
                    ['move', 'Move'],
                    ['upload', 'Upload']
                ].map(([value, title]) => ({
                    value,
                    label: tr(title),
                    disabled: !model.localMethods && value !== 'upload'
                }))
            }
        ];
        fields.forEach((field, index) => {
            const x = 11 + (index % columns) * (cellWidth + 10),
                yy = sy + Math.floor(index / columns) * 44,
                properties = {
                    label: tr(field.title),
                    enabled:
                        editable &&
                        !!record.canOptions &&
                        field.active !== false
                };
            settings.push(
                label(
                    'commitQueueLabel_' + field.field,
                    rect(x, yy, labelWidth, 36),
                    tr(field.title),
                    muted
                )
            );
            if (field.kind === 'Choice')
                Object.assign(properties, {
                    value: field.value,
                    options: field.options,
                    action: { type: 'field', field: field.field }
                });
            else
                Object.assign(properties, {
                    text: field.text,
                    placeholder: field.placeholder,
                    inputType: 'text',
                    inputMode: 'numeric',
                    min: 0,
                    max: 9999,
                    action: { type: 'versionDraft' },
                    commitAction: { type: 'versionCommit' },
                    keys: { Enter: { type: 'versionCommit' } },
                    error: !!model.versionError
                });
            settings.push(
                node(
                    field.kind,
                    'commitQueueField_' + field.field,
                    rect(
                        x + labelWidth + 8,
                        yy,
                        cellWidth - labelWidth - 8,
                        36
                    ),
                    properties
                )
            );
        });
        sy += Math.ceil(fields.length / columns) * 44;
        if (model.versionError) {
            settings.push(
                label(
                    'commitQueueVersionError',
                    rect(11, sy, inner, 30),
                    tr(model.versionError),
                    { color: 'error', wrap: true, role: 'alert' }
                )
            );
            sy += 38;
        }
        settings.push(
            label(
                'commitQueueFilenameLabel',
                rect(11, sy, labelWidth, 36),
                tr('Filename'),
                muted
            )
        );
        settings.push(
            node(
                'Field',
                'commitQueueField_explicitFilename',
                rect(19 + labelWidth, sy, inner - labelWidth - 8, 36),
                {
                    label: tr('Filename'),
                    placeholder: tr('Generated by naming rules'),
                    text:
                        model.filenameDraft == null
                            ? record.explicitFilename || ''
                            : model.filenameDraft,
                    enabled:
                        editable &&
                        !!record.canOptions &&
                        !record.contextAsFilename,
                    action: { type: 'filenameDraft' },
                    commitAction: { type: 'filenameCommit' },
                    keys: { Enter: { type: 'filenameCommit' } }
                }
            )
        );
        sy += 46;
        if (!model.localMethods) {
            const text = tr(
                    'Local transfer methods require a desktop connection. Browser check-in uses Upload.'
                ),
                h = captionHeight(text, inner);
            settings.push(
                label(
                    'commitQueueTransferCapability',
                    rect(11, sy, inner, h),
                    text,
                    Object.assign({}, muted, { wrap: true })
                )
            );
            sy += h + 10;
        }
        settings.push(
            label(
                'commitQueueOptionsHeading',
                rect(11, sy, inner, 20),
                tr('FILE OPTIONS'),
                {
                    fontRole: 'secondary',
                    color: 'secondaryText',
                    weight: 600,
                    letterSpacing: 0.5
                }
            )
        );
        sy += 26;
        const options = [
                [
                    'updateVersionless',
                    'Update versionless',
                    record.versionlessAllowed && !record.keepFileName
                ],
                [
                    'onlyVersionless',
                    'Commit versionless only',
                    record.versionlessAllowed
                ],
                ['keepFileName', 'Keep source filename', true],
                ['contextAsFilename', 'Use context as filename', true],
                ['generatePreviews', 'Generate previews', true]
            ],
            optionColumns = inner >= 560 ? 2 : 1,
            optionWidth = (inner - (optionColumns - 1) * 12) / optionColumns;
        for (let index = 0; index < options.length; index += optionColumns) {
            const row = options.slice(index, index + optionColumns),
                h = Math.max(
                    32,
                    ...row.map((option) =>
                        captionHeight(tr(option[1]), optionWidth - 40)
                    )
                );
            row.forEach(([field, title, active], column) =>
                settings.push(
                    node(
                        'CheckBox',
                        'commitQueueOption_' + field,
                        rect(
                            11 + column * (optionWidth + 12),
                            sy,
                            optionWidth,
                            h
                        ),
                        {
                            text: tr(title),
                            checked: !!record[field],
                            enabled:
                                editable && !!record.canOptions && !!active,
                            action: { type: 'field', field }
                        }
                    )
                )
            );
            sy += h + 4;
        }
    }
    sy += 8;
    nodes.push(
        node('Box', 'commitQueuePrimarySettings', rect(0, top, width, sy), {
            background: 'surfaceContainerLow',
            radius: 16,
            children: settings
        })
    );
    y += sy + 8;
    const naming = [
        button(
            'commitQueueNamingToggle',
            rect(11, 8, Math.max(0, width - 66), 38),
            tr('Naming preview'),
            model.namingExpanded ? 'expand-more' : 'chevron-right',
            { type: 'namingToggle' },
            true,
            { tonal: true }
        ),
        button(
            'commitQueueNamingEditor',
            rect(width - 44, 13, 28, 28),
            tr('Naming Editor'),
            'edit',
            { type: 'namingEditor' },
            !model.busy && !!record.canNaming,
            { iconOnly: true, iconAction: true }
        )
    ];
    let namingHeight = 54;
    if (model.namingExpanded) {
        const rows = namingRows(record, language),
            h = Math.min(360, Math.max(26, rows.length * 24));
        naming.push(
            node('List', 'commitQueueNamingDetails', rect(11, 54, inner, h), {
                source: 'naming',
                keyField: 'key',
                rowHeight: 24,
                rowGap: 2,
                label: tr('Naming preview'),
                fields: ['key', 'text', 'heading']
            })
        );
        namingHeight += h + 10;
    }
    nodes.push(
        node(
            'Box',
            'commitQueueNamingSection',
            rect(0, y, width, namingHeight),
            { background: 'surfaceContainerLow', radius: 16, children: naming }
        )
    );
    y += namingHeight + 8;
    for (const [id, text, error] of [
        ['commitQueueValidationError', record.validationError, true],
        ['commitQueueResultError', record.error, true],
        [
            'commitQueueStage',
            record.stage && record.stage !== 'prepared' ? record.stage : '',
            false
        ],
        [
            'commitQueueUnknownGuard',
            record.status === 'Result unknown'
                ? tr(
                      'Check the current snapshot before repeating this check-in; the server may already have saved it.'
                  )
                : '',
            false
        ]
    ]) {
        if (!text) continue;
        const h = Math.max(28, captionHeight(text, width - 24)) + 16;
        nodes.push(
            node('Box', id + 'Panel', rect(0, y, width, h), {
                background: error ? 'errorContainer' : 'surfaceContainerLow',
                radius: 12,
                children: [
                    label(id, rect(8, 8, width - 16, h - 16), text, {
                        fontRole: 'secondary',
                        color: error ? 'error' : 'secondaryText',
                        wrap: true,
                        role: error ? 'alert' : 'status'
                    })
                ]
            })
        );
        y += h + 8;
    }
    return { nodes, height: y };
}
