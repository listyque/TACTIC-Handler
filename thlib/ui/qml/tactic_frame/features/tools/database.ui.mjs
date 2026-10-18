import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function changedFields(pending, name, original, value) {
    const changes = Object.assign({}, pending);
    if (String(value) === String(original)) delete changes[name];
    else changes[name] = String(value);
    return changes;
}

export function layout(model, width, height) {
    const multi = model.count > 1,
        left = multi ? Math.min(250, Math.max(0, width - 20) * 0.32) : 0;
    const bodyHeight = Math.max(0, height - 68 - (multi ? 70 : 0));
    return {
        left,
        objects: rect(10, 92, left, bodyHeight - 34),
        fields: rect(10 + left, 92, width - 20 - left, bodyHeight - 34),
        body: rect(10, 58, width - 20, bodyHeight),
        multi
    };
}

function bulk(model, width, y, language, batch) {
    const tr = (text) => translate(text, language),
        x = batch ? 12 : 10,
        available = Math.max(0, width - x * 2),
        fieldWidth = Math.min(batch ? 180 : 190, available * 0.3),
        applyWidth = batch ? 156 : 140;
    return node(
        'Box',
        'databaseBulkSurface',
        rect(x, y, available, batch ? 58 : 62),
        {
            background: 'surfaceContainerHigh',
            radius: batch ? 8 : 12,
            children: [
                node(
                    'Choice',
                    'databaseBulkColumn',
                    rect(8, 10, fieldWidth, 38),
                    {
                        label: tr('Choose field'),
                        value: model.column,
                        options: (model.columns || []).map((value) => ({
                            value,
                            label: value
                        })),
                        enabled: !model.busy && !!model.count,
                        action: { type: 'column' }
                    }
                ),
                node(
                    'Field',
                    'databaseBulkValue',
                    rect(
                        16 + fieldWidth,
                        10,
                        Math.max(0, available - fieldWidth - applyWidth - 32),
                        38
                    ),
                    {
                        text: model.bulkValue || '',
                        label: tr('Value for every selected item'),
                        placeholder: tr('Value for every selected item'),
                        enabled: !model.busy,
                        action: { type: 'bulkValue' },
                        keys: { Enter: { type: 'bulk' } }
                    }
                ),
                button(
                    'databaseBulkApply',
                    rect(available - applyWidth - 8, 10, applyWidth, 38),
                    batch
                        ? tr('Apply to selected')
                        : translate('Apply to {count}', language, {
                              count: model.count
                          }),
                    '',
                    { type: 'bulk' },
                    !!model.column && !!model.count && !model.busy
                )
            ]
        }
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        bounds = layout(model, width, height),
        dirty = Object.keys(model.pending || {}).length;
    const nodes = [
        node('Box', 'databaseBackground', rect(0, 0, width, height), {
            background: 'panelDeep'
        }),
        node('Icon', 'databaseHeadingIcon', rect(10, 20, 16, 16), {
            icon: 'table',
            color: 'action'
        }),
        label('databaseHeading', rect(34, 10, 180, 36), tr('Database Editor'), {
            fontRole: 'bodyLarge',
            weight: 600
        }),
        label(
            'databaseSelectionCount',
            rect(220, 10, Math.max(0, width - 460), 36),
            String(model.count) + tr(' selected'),
            muted
        ),
        label(
            'databaseDirtyCount',
            rect(width - 244, 10, 100, 36),
            dirty ? String(dirty) + tr(' unsaved') : '',
            { color: 'action' }
        ),
        button(
            'databaseSave',
            rect(width - 140, 13, 130, 30),
            tr('Save changes'),
            '',
            { type: 'save' },
            dirty > 0 && !model.busy,
            { highlighted: true }
        )
    ];
    if (!model.count) {
        nodes.push(
            label(
                'databaseEmpty',
                rect(20, 80, width - 40, height - 100),
                tr('Select one or more objects to edit database fields'),
                Object.assign({}, muted, { align: 'center', wrap: true })
            )
        );
        return { nodes };
    }
    nodes.push(
        node('Box', 'databaseBody', bounds.body, {
            background: 'panel',
            border: 'outlineVariant',
            borderWidth: 1,
            radius: 12
        })
    );
    if (bounds.multi) {
        nodes.push(
            node(
                'Box',
                'databaseObjectsHeadingSurface',
                rect(10, 58, bounds.left, 34),
                { background: 'surfaceContainerHigh' }
            )
        );
        nodes.push(
            label(
                'databaseObjectsHeading',
                rect(22, 58, bounds.left - 24, 34),
                tr('SELECTED OBJECTS'),
                Object.assign({}, muted, { fontRole: 'secondary' })
            )
        );
        nodes.push(
            node('List', 'databaseObjects', bounds.objects, {
                source: 'objects',
                keyField: 'nodeId',
                fields: ['nodeId', 'title', 'code', 'type', 'searchKey'],
                rowHeight: 48,
                rowGap: 0,
                scrollbarId: 'databaseObjectsScrollBar'
            })
        );
    }
    const fieldWidth = Math.min(210, bounds.fields.width * 0.34);
    nodes.push(
        node(
            'Box',
            'databaseFieldsHeadingSurface',
            rect(bounds.fields.x, 58, bounds.fields.width, 34),
            { background: 'surfaceContainerHigh' }
        )
    );
    nodes.push(
        label(
            'databaseFieldHeading',
            rect(bounds.fields.x + 12, 58, fieldWidth, 34),
            tr('FIELD'),
            muted
        )
    );
    nodes.push(
        label(
            'databaseValueHeading',
            rect(
                bounds.fields.x + fieldWidth + 24,
                58,
                bounds.fields.width - fieldWidth - 36,
                34
            ),
            model.active.title || tr('VALUE'),
            muted
        )
    );
    nodes.push(
        node('List', 'databaseFields', bounds.fields, {
            source: 'fields',
            keyField: 'fieldName',
            fields: ['fieldName', 'fieldLabel', 'fieldValue'],
            rowHeight: 41,
            rowGap: 1,
            scrollbarId: 'databaseFieldsScrollBar'
        })
    );
    if (bounds.multi)
        nodes.push(bulk(model, width, height - 72, language, false));
    return { nodes };
}

export function batch(model, width, height, language) {
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            node('Box', 'databaseBatchBackground', rect(0, 0, width, height), {
                background: 'panelDeep'
            }),
            node('Icon', 'databaseBatchIcon', rect(12, 18, 18, 18), {
                icon: 'edit',
                color: 'action'
            }),
            label(
                'databaseBatchHeading',
                rect(38, 12, width - 50, 30),
                model.count > 1
                    ? translate(
                          '{count} compatible objects selected',
                          language,
                          { count: model.count }
                      )
                    : tr('Selected object'),
                { weight: 600 }
            ),
            node(
                'Box',
                'databaseBatchHeadingSurface',
                rect(12, 50, width - 24, 32),
                { background: 'surfaceContainerHigh', radius: 4 }
            ),
            label(
                'databaseBatchObjectTitle',
                rect(24, 50, width - 300, 32),
                tr('Object'),
                muted
            ),
            label(
                'databaseBatchCodeTitle',
                rect(width - 266, 50, 130, 32),
                tr('Code'),
                muted
            ),
            label(
                'databaseBatchStatusTitle',
                rect(width - 126, 50, 100, 32),
                tr('Status'),
                muted
            ),
            node(
                'List',
                'databaseBatchObjects',
                rect(12, 90, width - 24, height - 172),
                {
                    source: 'objects',
                    keyField: 'nodeId',
                    fields: ['nodeId', 'title', 'code', 'status', 'searchKey'],
                    rowHeight: 43,
                    rowGap: 1,
                    scrollbarId: 'databaseBatchScrollBar'
                }
            ),
            bulk(model, width, height - 70, language, true)
        ]
    };
}

export function row(list, record, index, model) {
    const width = Math.max(0, list.width - 16),
        striped = index % 2 ? 'row' : 'panel';
    if (list.id === 'databaseBatchObjects')
        return {
            nodes: [
                node(
                    'Box',
                    'databaseBatchRow_' + record.nodeId,
                    rect(0, 0, width, 42),
                    {
                        background: striped,
                        children: [
                            label(
                                'databaseBatchObject',
                                rect(12, 0, width - 274, 42),
                                record.title || record.searchKey || ''
                            ),
                            label(
                                'databaseBatchCode',
                                rect(width - 252, 0, 130, 42),
                                record.code || '—',
                                muted
                            ),
                            label(
                                'databaseBatchStatus',
                                rect(width - 112, 0, 100, 42),
                                record.status || '—',
                                muted
                            )
                        ]
                    }
                )
            ]
        };
    if (list.source === 'objects')
        return {
            nodes: [
                node(
                    'Action',
                    'databaseObjectRow_' + record.nodeId,
                    rect(0, 0, width, 48),
                    {
                        surface: true,
                        selected: index === model.selected,
                        action: { type: 'select', value: index },
                        children: [
                            node(
                                'Preview',
                                'databaseObjectAvatar',
                                rect(10, 10, 28, 28),
                                {
                                    initials: String(record.title || '?')
                                        .slice(0, 2)
                                        .toUpperCase(),
                                    color: 'action'
                                }
                            ),
                            label(
                                'databaseObjectTitle',
                                rect(46, 5, width - 54, 22),
                                record.title || record.code || '',
                                { weight: 500 }
                            ),
                            label(
                                'databaseObjectCode',
                                rect(46, 27, width - 54, 17),
                                record.code || record.type || '',
                                Object.assign({}, muted, {
                                    fontRole: 'caption'
                                })
                            )
                        ]
                    }
                )
            ]
        };
    const field = record.fieldName,
        original =
            record.fieldValue === undefined ? '' : String(record.fieldValue),
        changed = model.pending[field] !== undefined,
        left = Math.min(210, width * 0.34);
    return {
        nodes: [
            node('Box', 'databaseFieldRow_' + field, rect(0, 0, width, 40), {
                background: changed ? 'secondaryContainer' : striped,
                children: [
                    label(
                        'databaseFieldName_' + field,
                        rect(12, 0, left, 40),
                        record.fieldLabel || field,
                        muted
                    ),
                    node(
                        'Field',
                        'databaseFieldValue_' + field,
                        rect(left + 24, 5, width - left - 56, 30),
                        {
                            text: changed ? model.pending[field] : original,
                            label: record.fieldLabel || field,
                            tableCell: true,
                            enabled: !model.busy,
                            action: { type: 'field', field, original }
                        }
                    ),
                    node(
                        'Icon',
                        'databaseFieldChanged_' + field,
                        rect(width - 22, 14, 13, 13),
                        { icon: 'edit', color: 'action', visible: changed }
                    )
                ]
            })
        ]
    };
}
