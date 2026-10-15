import { node } from '../../../core/frame.mjs';
import { rect, label, muted, notices, toolbar } from '../admin.document.mjs';
import { translate } from '../../../core/strings.mjs';
import { permissions } from './raw.state.mjs';
export { toolbar, translate };

const button = (id, bounds, text, icon, action, enabled, extra) =>
    node(
        'Button',
        id,
        bounds,
        Object.assign(
            {
                text,
                icon,
                action,
                enabled
            },
            extra || {}
        )
    );
export function cellText(row, name) {
    const mode =
        (row.modes || {})[name] || (row.key == null ? 'default' : 'value');
    return mode === 'null'
        ? 'NULL'
        : mode === 'default'
          ? 'DEFAULT'
          : (row.texts || {})[name] || '';
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const scene = describeBody(model, ui, width, height, language);
    if (scene.minimumHeight <= height)
        return {
            nodes: scene.nodes
        };
    const inner = Math.max(1, width - 16),
        contentHeight = describeBody(
            model,
            ui,
            inner,
            0,
            language
        ).minimumHeight;
    return {
        nodes: [
            node('Scroll', 'rawPageScroll', rect(0, 0, width, height), {
                contentHeight,
                scrollbarId: 'rawPageScrollBar',
                children: describeBody(
                    model,
                    ui,
                    inner,
                    contentHeight,
                    language
                ).nodes
            })
        ]
    };
}
function describeBody(model, ui, width, height, language) {
    const tr = (text) => translate(text, language),
        allow = permissions(model),
        dropping = ui.confirmation === 'drop',
        locked = !!ui.confirmation;
    const notice = notices(
            model,
            dropping
                ? Object.assign({}, ui, {
                      confirmation: ''
                  })
                : ui,
            width,
            language,
            'Discard unsaved raw table changes?'
        ),
        nodes = notice.nodes;
    let y = notice.top;
    const warningHeight = width < 600 ? 68 : 46,
        helpHeight = width < 600 ? 60 : 36;
    nodes.push(
        node('Box', 'rawWarning', rect(0, y, width, warningHeight), {
            background: 'contentSelection',
            border: 'outlineVariant',
            children: [
                label(
                    'rawWarningText',
                    rect(12, 6, width - 24, warningHeight - 12),
                    tr(
                        'Raw SQL bypasses object validation, triggers and undo history. Changes can break the application.'
                    ),
                    {
                        wrap: true
                    }
                )
            ]
        })
    );
    y += warningHeight + 8;
    nodes.push(
        label(
            'rawCellHelp',
            rect(0, y, width, helpHeight),
            tr(
                'Open a cell to edit its value. Text needs no quotes. Choose NULL or Database default explicitly in the cell editor.'
            ),
            Object.assign(
                {
                    wrap: true
                },
                muted
            )
        )
    );
    y += helpHeight + 8;
    const compact = width < 470,
        addWidth = compact ? 38 : language === 'ru' ? 152 : 122,
        exportWidth = compact ? 38 : 142,
        dropWidth = compact ? 38 : 146;
    const actionsWidth = addWidth + exportWidth + dropWidth + 16;
    const stacked = width < 900,
        searchWidth = stacked
            ? (width - 8) / 2
            : Math.max(1, width - 236 - actionsWidth),
        selectWidth = stacked ? searchWidth : 220;
    nodes.push(
        node('Field', 'rawTableFilter', rect(0, y, searchWidth, 38), {
            text: ui.query,
            label: tr('Filter tables'),
            placeholder: tr('Filter tables'),
            enabled: allow.navigate && !locked,
            action: {
                type: 'query'
            }
        }),
        node(
            'Choice',
            'rawTableSelector',
            rect(searchWidth + 8, y, selectWidth, 38),
            {
                value: model.identity,
                options: model.catalog
                    .filter(
                        (row) =>
                            row.identity === model.identity ||
                            row.label
                                .toLowerCase()
                                .indexOf(ui.query.toLowerCase()) >= 0
                    )
                    .map((row) => ({
                        value: row.identity,
                        label: row.label
                    })),
                label: tr('Database table'),
                enabled: allow.navigate && !locked,
                action: {
                    type: 'select'
                }
            }
        )
    );
    const actionY = y + (stacked ? 46 : 0),
        actionX = stacked ? 0 : searchWidth + selectWidth + 16;
    nodes.push(
        node('Box', 'rawRowActions', rect(actionX, actionY, actionsWidth, 38), {
            children: [
                button(
                    'rawNewRow',
                    rect(0, 0, addWidth, 38),
                    tr('New row'),
                    'add',
                    {
                        type: 'add'
                    },
                    allow.add && !locked,
                    {
                        iconOnly: compact
                    }
                ),
                button(
                    'rawExportCsv',
                    rect(addWidth + 8, 0, exportWidth, 38),
                    tr('Export CSV'),
                    'download',
                    {
                        type: 'export'
                    },
                    allow.export && !locked,
                    {
                        iconOnly: compact
                    }
                ),
                button(
                    'rawDropTable',
                    rect(addWidth + exportWidth + 16, 0, dropWidth, 38),
                    tr('DROP TABLE'),
                    'delete',
                    {
                        type: 'drop'
                    },
                    allow.drop && !locked,
                    {
                        iconOnly: compact,
                        destructive: true
                    }
                )
            ]
        })
    );
    y += stacked ? 92 : 46;
    if (dropping) {
        const h = width < 600 ? 198 : 166;
        nodes.push(
            node('Box', 'rawConfirmation', rect(0, y, width, h), {
                background: 'surfaceContainerHigh',
                border: 'outlineVariant',
                children: [
                    label(
                        'rawDropWarning',
                        rect(12, 8, width - 24, width < 600 ? 66 : 34),
                        tr(
                            'Permanently delete this table and all its rows? Type its full name to confirm.'
                        ),
                        {
                            wrap: true
                        }
                    ),
                    label(
                        'rawDropTableName',
                        rect(12, h - 120, width - 24, 24),
                        model.metadata.label || '',
                        {
                            weight: 600
                        }
                    ),
                    node(
                        'Field',
                        'rawDropName',
                        rect(12, h - 90, width - 24, 38),
                        {
                            text: ui.dropName,
                            label: tr('Confirm table name'),
                            enabled: !model.busy,
                            action: {
                                type: 'dropName'
                            }
                        }
                    ),
                    button(
                        'rawKeepEditing',
                        rect(12, h - 44, Math.min(150, (width - 32) / 2), 36),
                        tr('Keep editing'),
                        '',
                        {
                            type: 'keep'
                        },
                        !model.busy
                    ),
                    button(
                        'rawConfirmChanges',
                        rect(
                            Math.min(150, (width - 32) / 2) + 20,
                            h - 44,
                            Math.min(170, (width - 32) / 2),
                            36
                        ),
                        tr('DROP TABLE'),
                        '',
                        {
                            type: 'confirm'
                        },
                        allow.drop &&
                            ui.dropName === model.metadata.label &&
                            ui.dropIdentity === model.identity,
                        {
                            destructive: true
                        }
                    )
                ]
            })
        );
        y += h + 8;
    }
    const gridHeight = Math.max(1, height - y - 46);
    const rowHeight = (model.controlHeight || 38) + 1;
    if (model.ready)
        nodes.push(
            node('Grid', 'rawTableViewport', rect(0, y, width, gridHeight), {
                source: 'rows',
                labelWidth: 84,
                headerHeight: 40,
                cellWidth: 230,
                rowHeight,
                caption: tr('Row'),
                rowHeaders: model.rows.map((record, index) => ({
                    children: [
                        label(
                            'rawRowNumber_' + index,
                            rect(6, 0, 32, rowHeight - 1),
                            String((model.metadata.offset || 0) + index + 1),
                            {
                                strike: record.deleted,
                                opacity: record.deleted ? 0.55 : 1
                            }
                        ),
                        button(
                            'rawDeleteRow_' + index,
                            rect(40, 0, rowHeight - 1, rowHeight - 1),
                            tr(record.deleted ? 'Restore row' : 'Delete row'),
                            record.deleted ? 'undo' : 'delete',
                            {
                                type: 'deleteRow',
                                row: index
                            },
                            allow.editable && !locked,
                            {
                                iconOnly: true,
                                destructive: !record.deleted,
                                opacity: record.deleted ? 0.55 : 1
                            }
                        )
                    ]
                })),
                columnHeaders: model.columns.map((column) => ({
                    label: column.name,
                    detail:
                        column.type +
                        (column.readonly ? ' · ' + tr('Read-only') : '')
                })),
                verticalBarId: 'rawTableVerticalBar',
                horizontalBarId: 'rawTableHorizontalBar',
                columnHeadersId: 'rawTableHeadings',
                rowHeadersId: 'rawTableRowHeaders'
            })
        );
    if (!model.rows.length && !model.busy)
        nodes.push(
            label(
                'rawTableEmpty',
                rect(12, y + (model.ready ? 48 : 12), width - 24, 38),
                tr('No rows'),
                muted
            )
        );
    const footer = height - 38,
        size = width < 600 ? 38 : 140;
    nodes.push(
        button(
            'rawPreviousPage',
            rect(0, footer, size, 38),
            tr('Previous'),
            'chevron-left',
            {
                type: 'previous'
            },
            allow.previous && !locked,
            {
                iconOnly: width < 600
            }
        ),
        label(
            'rawPageRange',
            rect(size + 8, footer, width - 2 * size - 16, 38),
            (model.metadata.total ? (model.metadata.offset || 0) + 1 : 0) +
                '–' +
                Math.min(
                    (model.metadata.offset || 0) + 50,
                    model.metadata.total || 0
                ) +
                ' / ' +
                (model.metadata.total || 0),
            {
                align: 'center'
            }
        ),
        button(
            'rawNextPage',
            rect(width - size, footer, size, 38),
            tr('Next'),
            'chevron-right',
            {
                type: 'next'
            },
            allow.next && !locked,
            {
                iconOnly: width < 600
            }
        )
    );
    return {
        nodes,
        minimumHeight: y + 206
    };
}

export function cell(grid, record, row, column, model, ui, language) {
    if (!model.columns[column])
        return {
            nodes: []
        };
    const name = model.columns[column].name,
        keys = {},
        action = {
            type: 'cell',
            row,
            name
        };
    [
        ['ArrowLeft', -1, 0],
        ['ArrowRight', 1, 0],
        ['ArrowUp', 0, -1],
        ['ArrowDown', 0, 1]
    ].forEach(([key, dx, dy]) => {
        keys[key] = {
            type: 'navigateCell',
            row,
            column,
            dx,
            dy
        };
    });
    keys.F2 = keys.Enter = action;
    return {
        nodes: [
            node(
                'Box',
                'rawCellBorder_' + row + '_' + name,
                rect(0, 0, grid.cellWidth, grid.rowHeight),
                {
                    border: 'outline',
                    radius: 0,
                    opacity: record.deleted ? 0.55 : 1
                }
            ),
            node(
                'Field',
                'rawCell_' + row + '_' + name,
                rect(0, 0, grid.cellWidth - 1, grid.rowHeight - 1),
                {
                    text: cellText(record, name),
                    label: name + ' · ' + (row + 1),
                    enabled: !model.busy && !record.deleted && !ui.confirmation,
                    activateAction: action,
                    keys,
                    tableCell: true,
                    readOnly: true,
                    strike: record.deleted,
                    opacity: record.deleted ? 0.55 : 1
                }
            )
        ]
    };
}

export function cellDescribe(model, ui, width, height, language) {
    if (!model.name)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        pad = 14,
        inner = Math.max(1, width - pad * 2),
        footer = height - 52,
        errorHeight = model.error ? 48 : 0,
        helpY = footer - 44;
    const narrow = width < 600;
    const header = [
        label(
            'rawCellTitle',
            rect(narrow ? 42 : 0, 0, inner - (narrow ? 42 : 100), 38),
            tr('Cell editor'),
            {
                fontSize: 17
            }
        ),
        button(
            narrow ? 'rawCellBack' : 'rawCellClose',
            rect(narrow ? 0 : inner - 38, 0, 38, 38),
            tr(narrow ? 'Back' : 'Close'),
            narrow ? 'chevron-left' : 'close',
            {
                type: 'cancel'
            },
            true,
            {
                iconOnly: true
            }
        )
    ];
    const nodes = [
        node('Box', 'rawCellHeader', rect(pad, pad, inner, 38), {
            titlebar: true,
            chromeRight: 46,
            children: header
        }),
        label(
            'rawCellDescription',
            rect(pad, 64, inner, 34),
            (model.name || '') +
                ' · ' +
                (model.type || '') +
                ' · ' +
                tr('Row') +
                ' ' +
                (model.rowNumber || ''),
            {
                wrap: true
            }
        ),
        node('Choice', 'rawCellMode', rect(pad, 110, inner, 38), {
            value: ui.mode,
            label: tr('Value mode'),
            enabled: !model.readonly && !model.busy,
            options: [
                ['value', 'Value'],
                ['null', 'NULL']
            ]
                .concat(model.newRow ? [['default', 'Database default']] : [])
                .map(([value, text]) => ({
                    value,
                    label: tr(text)
                })),
            action: {
                type: 'mode'
            }
        }),
        node(
            'Area',
            'rawCellValue',
            rect(pad, 160, inner, Math.max(1, helpY - errorHeight - 172)),
            {
                text: ui.text,
                label: tr('Cell value'),
                enabled: ui.mode === 'value' && !model.busy,
                readOnly: !!model.readonly,
                action: {
                    type: 'text'
                }
            }
        ),
        label(
            'rawCellApplyHelp',
            rect(pad, helpY, inner, 32),
            tr('Apply to draft, then save the table.'),
            Object.assign(
                {
                    wrap: true
                },
                muted
            )
        ),
        button(
            'rawCellCancel',
            rect(width - pad - (model.readonly ? 96 : 216), footer, 96, 38),
            tr(model.readonly ? 'Close' : 'Cancel'),
            '',
            {
                type: 'cancel'
            },
            true
        )
    ];
    if (model.error)
        nodes.push(
            label(
                'rawCellError',
                rect(pad, helpY - 48, inner, 40),
                tr(model.error),
                {
                    color: 'error',
                    wrap: true,
                    role: 'alert'
                }
            )
        );
    if (!model.readonly)
        nodes.push(
            button(
                'rawCellApply',
                rect(width - pad - 112, footer, 112, 38),
                tr('Apply'),
                '',
                {
                    type: 'apply'
                },
                !model.busy,
                {
                    highlighted: true
                }
            )
        );
    return {
        nodes
    };
}
