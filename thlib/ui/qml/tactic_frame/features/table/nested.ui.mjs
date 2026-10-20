import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { metrics, paint } from './host.ui.mjs';

export const height = 320;
export const rowHeight = 68;

export function columns(model) {
    let left = metrics.selection;
    return (model.columns || []).map((column, index) => {
        const width = Math.max(48, Math.min(640, Number(column.width) || 160));
        const result = Object.assign({}, column, { index, x: left, width });
        left += width;
        return result;
    });
}

export function describe(model, width, extent, language) {
    const t = (value) => translate(value, language);
    const fields = columns(model);
    const contentWidth = Math.max(
        width - 16,
        metrics.selection +
            fields.reduce((sum, field) => sum + field.width, 0) +
            40
    );
    const nodes = [
        node(
            'Field',
            'nestedFilter',
            rect(0, 0, Math.max(0, width - 120), 36),
            {
                text: model.filter || '',
                placeholder: t('Filter'),
                action: { type: 'filter' }
            }
        ),
        button(
            'nestedReload',
            rect(Math.max(0, width - 112), 0, 32, 32),
            model.busy ? t('Loading data…') : t('Refresh'),
            model.busy ? 'loading' : 'refresh',
            { type: 'reload' },
            !model.busy,
            { iconOnly: true }
        ),
        button(
            'nestedCreate',
            rect(Math.max(0, width - 76), 0, 32, 32),
            t('Create'),
            'add',
            { type: 'create' },
            !model.busy && model.insert !== false,
            { iconOnly: true }
        ),
        button(
            'nestedClose',
            rect(Math.max(0, width - 40), 0, 32, 32),
            t('Close'),
            'close',
            { type: 'close' },
            true,
            { iconOnly: true }
        ),
        label(
            'nestedState',
            rect(0, extent - 32, Math.max(0, width - 120), 28),
            model.error ? t(model.error) : String((model.rows || []).length),
            { color: model.error ? 'error' : 'secondaryText' }
        ),
        button(
            'nestedClearSelection',
            rect(Math.max(0, width - 112), extent - 32, 32, 32),
            t('Clear selection'),
            'close',
            { type: 'clear-selection' },
            !!model.selected?.length,
            { iconOnly: true }
        ),
        button(
            'nestedPrevious',
            rect(Math.max(0, width - 76), extent - 32, 32, 32),
            t('Previous page'),
            'chevron-left',
            { type: 'page', value: -1 },
            !model.busy && model.offset > 0,
            { iconOnly: true }
        ),
        button(
            'nestedNext',
            rect(Math.max(0, width - 40), extent - 32, 32, 32),
            t('Next page'),
            'chevron-right',
            { type: 'page', value: 1 },
            !model.busy && !!model.hasNext,
            { iconOnly: true }
        )
    ];
    const children = [
        node(
            'Box',
            'nestedHeaderSurface',
            rect(0, 0, contentWidth, metrics.header),
            { background: paint.header }
        )
    ];
    for (const field of fields) {
        children.push(
            field.sortable
                ? button(
                      'nestedHeader_' + field.name,
                      rect(field.x, 0, field.width, metrics.header),
                      field.title || field.name,
                      '',
                      { type: 'sort', value: field.name },
                      !model.busy,
                      { iconAction: true }
                  )
                : label(
                      'nestedHeader_' + field.name,
                      rect(field.x + 10, 0, field.width - 20, metrics.header),
                      field.title || field.name,
                      { color: paint.headerText }
                  )
        );
    }
    children.push(
        node(
            'List',
            'nestedRows',
            rect(
                0,
                metrics.header + 3,
                contentWidth,
                Math.max(0, extent - metrics.header - 86)
            ),
            {
                source: 'rows',
                keyField: 'key',
                fields: ['key', 'nodeId', 'record', 'cells'],
                rowHeight,
                label: t('Table View'),
                role: 'list'
            }
        )
    );
    nodes.push(
        node(
            'Scroll',
            'nestedHorizontal',
            rect(0, 42, width, Math.max(0, extent - 80)),
            {
                contentWidth,
                contentHeight: Math.max(0, extent - 96),
                scrollbarId: 'nestedHorizontalBar',
                children
            }
        )
    );
    return { nodes };
}

export function row(model, record, language) {
    const fields = columns(model),
        nodes = [];
    const width =
        metrics.selection +
        fields.reduce((sum, field) => sum + field.width, 0) +
        40;
    const selected = (model.selected || []).includes(record.key);
    nodes.push(
        node('Box', 'nestedRowSurface', rect(0, 0, width, rowHeight - 1), {
            background: selected ? paint.selected : paint.row
        })
    );
    if (model.selection !== false)
        nodes.push(
            node('CheckBox', 'nestedSelect', rect(6, 14, 28, 28), {
                checked: selected,
                label: translate('Select row', language),
                action: { type: 'select', key: record.key }
            })
        );
    for (const field of fields)
        nodes.push(
            node(
                'View',
                'nestedCell_' + field.name,
                rect(field.x, 0, field.width, rowHeight - 1),
                {
                    view: 'tableCell',
                    weight: field.index === 0 ? 600 : 400,
                    column: field,
                    record: record.record,
                    cell: record.cells[field.name] || { text: '' },
                    key: record.key,
                    nodeId: record.nodeId,
                    selected
                }
            )
        );
    nodes.push(
        button(
            'nestedEdit',
            rect(width - 36, 16, 28, 28),
            translate('Edit', language),
            'edit',
            { type: 'edit', key: record.key },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    return { nodes };
}
