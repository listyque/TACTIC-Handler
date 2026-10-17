import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// Mirrors Handler search_contract.normalize_records and its editable first row.
export function normalizeRecords(records, columns = []) {
    const rows = (records || []).map((record, index) =>
        Object.assign({}, record, {
            rowEnabled: record.rowEnabled !== false,
            operator: index
                ? record.operator === 'or'
                    ? 'or'
                    : 'and'
                : 'begin',
            isDefault: index === 0
        })
    );
    if (!rows.length && columns.length) {
        const column =
            columns.find((option) => option.value === 'name') || columns[0];
        rows.push({
            column: column.value,
            relation: 'EQI',
            value: '',
            rowEnabled: true,
            operator: 'begin',
            isDefault: true
        });
    }
    return rows;
}

export function rowHeight(row, width) {
    return row.generatedFilterKind ? 94 : width < 560 ? 184 : 98;
}

export function suggestion(record, width) {
    const titleWidth = Math.min(150, Math.ceil(record.titleWidth || 150)),
        keywordWidth = record.keyword
            ? Math.min(100, Math.ceil(record.keywordWidth || 100))
            : 0,
        titleX = 29,
        descriptionX = titleX + titleWidth + 7,
        right = width - 8 - keywordWidth;
    return {
        nodes: [
            node('Icon', 'conditionSuggestionIcon', rect(8, 10, 14, 14), {
                icon: 'search',
                color: 'secondaryText'
            }),
            label(
                'conditionSuggestionTitle',
                rect(titleX, 0, titleWidth, 34),
                record.title,
                { weight: 600 }
            ),
            label(
                'conditionSuggestionDescription',
                rect(
                    descriptionX,
                    0,
                    right - descriptionX - (keywordWidth ? 7 : 0),
                    34
                ),
                record.description || '',
                { fontRole: 'secondary', color: 'secondaryText' }
            ),
            label(
                'conditionSuggestionKeyword',
                rect(right, 0, keywordWidth, 34),
                record.keyword ? '#' + record.keyword : '',
                {
                    fontRole: 'secondary',
                    weight: 600,
                    color: 'action',
                    visible: !!record.keyword
                }
            )
        ]
    };
}

export function row(record, index, width, language, options = {}) {
    const text = (key) => translate(key, language),
        compact = width < 560,
        generated = !!record.generatedFilterKind,
        enabled = !options.busy && record.rowEnabled !== false,
        prefix = 'searchCondition_' + index;
    const action = (field) => ({ type: 'condition', index, field });
    const children = [];
    if (!generated)
        children.push(
            node('CheckBox', prefix + 'Enabled', rect(10, 5, 32, 32), {
                text: '',
                label: text('Enable filter'),
                checked: record.rowEnabled !== false,
                enabled: !options.busy,
                action: action('rowEnabled')
            })
        );
    children.push(
        button(
            prefix + 'Operator',
            rect(generated ? 10 : 46, 8, 80, 28),
            record.isDefault || !index
                ? 'WHERE'
                : String(record.operator || 'and').toUpperCase(),
            '',
            { type: 'operator', index },
            !options.busy && !generated && !record.isDefault && index > 0,
            { tonal: true }
        )
    );
    const trailing = options.reorder && !generated ? 108 : generated ? 72 : 36;
    children.push(
        label(
            prefix + 'Title',
            rect(
                generated ? 98 : 134,
                8,
                width - trailing - (generated ? 108 : 144),
                28
            ),
            generated
                ? record.generatedTitle || text('Quick filter')
                : record.columnTitle || record.column || '',
            muted
        )
    );
    let right = width - 42;
    children.push(
        button(
            prefix + 'Remove',
            rect(right, 5, 32, 32),
            text(record.isDefault ? 'Add filter' : 'Remove filter'),
            record.isDefault ? 'add' : 'close',
            { type: record.isDefault ? 'add' : 'remove', index },
            !options.busy,
            { iconOnly: true }
        )
    );
    if (generated) {
        children.push(
            button(
                prefix + 'Detach',
                rect(right - 36, 5, 32, 32),
                text('Edit as custom filter'),
                'edit',
                { type: 'detach', index },
                !options.busy,
                { iconOnly: true }
            )
        );
        children.push(
            label(
                prefix + 'Managed',
                rect(14, 46, width - 28, 36),
                text('Managed by Quick Filters'),
                Object.assign({}, muted, { wrap: true })
            )
        );
    } else {
        if (options.reorder) {
            for (const [name, icon, delta] of [
                ['Up', 'arrow-up', -1],
                ['Down', 'arrow-down', 1]
            ]) {
                right -= 36;
                children.push(
                    button(
                        prefix + name,
                        rect(right, 5, 32, 32),
                        text(delta < 0 ? 'Move up' : 'Move down'),
                        icon,
                        { type: 'move', index, delta },
                        !options.busy &&
                            index + delta >= 0 &&
                            index + delta < options.count,
                        { iconOnly: true }
                    )
                );
            }
        }
        const inner = width - 20,
            columnWidth = compact ? inner : Math.floor((inner - 16) * 0.34),
            relationWidth = compact ? inner : Math.floor((inner - 16) * 0.24),
            valueWidth = compact
                ? inner
                : inner - columnWidth - relationWidth - 16;
        children.push(
            node('Choice', prefix + 'Column', rect(10, 46, columnWidth, 36), {
                label: text('Filter column'),
                value: record.column,
                options: options.columns || [],
                enabled,
                action: action('column')
            })
        );
        children.push(
            node(
                'Choice',
                prefix + 'Relation',
                rect(
                    compact ? 10 : 18 + columnWidth,
                    compact ? 89 : 46,
                    relationWidth,
                    36
                ),
                {
                    label: text('Filter relation'),
                    value: record.relation,
                    options: (record.relations || []).map((option) =>
                        Object.assign({}, option, { label: text(option.label) })
                    ),
                    enabled,
                    action: action('relation')
                }
            )
        );
        const valueBounds = rect(
            compact ? 10 : 26 + columnWidth + relationWidth,
            compact ? 132 : 46,
            valueWidth,
            36
        );
        const valueOptions = {
            label: text('Filter value'),
            text: record.value == null ? '' : String(record.value),
            placeholder: text(
                record.column === '_expression' ? 'TACTIC expression' : 'Value'
            ),
            enabled:
                enabled &&
                ![
                    'is empty',
                    'is not empty',
                    'is null',
                    'is not null'
                ].includes(record.relation),
            action: action('value')
        };
        children.push(
            node(
                options.valueView ? 'View' : 'Field',
                prefix + 'Value',
                valueBounds,
                options.valueView
                    ? Object.assign({ view: options.valueView }, valueOptions, {
                          index,
                          column: record.column
                      })
                    : valueOptions
            )
        );
    }
    return node('Box', prefix, rect(0, 0, width, rowHeight(record, width)), {
        background: 'surfaceContainerHigh',
        border: 'outlineVariant',
        children
    });
}

export function describe(model, width, language) {
    const text = (key) => translate(key, language),
        nodes = [],
        compact = width < 560;
    nodes.push(
        node('Box', 'searchFiltersHeader', rect(0, 0, width, 50), {
            background: 'surfaceContainerHigh'
        })
    );
    nodes.push(
        button(
            'searchFiltersExpand',
            rect(8, 7, 34, 36),
            text('Search Filters'),
            model.expanded === false ? 'chevron_right' : 'keyboard_arrow_down',
            { type: 'expand' },
            true,
            { iconOnly: true }
        )
    );
    nodes.push(
        label(
            'searchFiltersTitle',
            rect(48, 7, Math.max(0, width - (compact ? 182 : 320)), 36),
            text('Search Filters'),
            { weight: 600 }
        )
    );
    const applyWidth = compact ? 36 : 190;
    nodes.push(
        button(
            'searchFiltersApply',
            rect(width - applyWidth - 86, 7, applyWidth, 36),
            text(model.busy ? 'Searching...' : 'Apply filters'),
            'search',
            { type: 'apply' },
            !model.busy,
            { highlighted: true, iconOnly: compact }
        )
    );
    nodes.push(
        button(
            'searchFiltersAdd',
            rect(width - 78, 7, 34, 36),
            text('Add filter'),
            'add',
            { type: 'add' },
            !model.busy,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'searchFiltersReset',
            rect(width - 40, 7, 34, 36),
            text('Reset filters'),
            'delete',
            { type: 'reset' },
            !model.busy,
            { iconOnly: true }
        )
    );
    let top = 57;
    if (model.expanded !== false) {
        for (let index = 0; index < (model.rows || []).length; index++) {
            const condition = row(
                model.rows[index],
                index,
                width,
                language,
                Object.assign({}, model, { count: model.rows.length })
            );
            condition.y = top;
            nodes.push(condition);
            top += condition.height + 7;
        }
        if (!model.rows?.length) {
            nodes.push(
                label(
                    'searchFiltersEmpty',
                    rect(12, top, width - 24, 36),
                    text('No filters selected'),
                    muted
                )
            );
            top += 43;
        }
    }
    return { nodes, contentHeight: top };
}
