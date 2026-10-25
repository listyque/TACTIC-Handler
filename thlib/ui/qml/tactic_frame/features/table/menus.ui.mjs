import { metrics } from './host.ui.mjs';
import { translate } from '../../core/strings.mjs';

export function columnActions(model, language) {
    const column = model.column || {};
    if (!column.name) return [];
    const date =
        ['date', 'datetime', 'time', 'timestamp', 'timestamptz'].indexOf(
            column.dataType
        ) >= 0;
    const enabled = model.editable !== false && !model.busy;
    const actions = [
        {
            title:
                String(column.label || column.title || column.name) +
                ' · ' +
                translate('Column', language),
            header: true,
            translate: false
        }
    ];
    if (column.sortable) {
        actions.push({
            title: date ? 'Sort oldest first' : 'Sort A to Z',
            icon: 'sort-ascending',
            command: 'sort:ascending',
            checked: model.sorted && model.direction === 'asc',
            enabled: !model.busy
        });
        actions.push({
            title: date ? 'Sort newest first' : 'Sort Z to A',
            icon: 'sort-descending',
            command: 'sort:descending',
            checked: model.sorted && model.direction === 'desc',
            enabled: !model.busy
        });
        actions.push({ separator: true });
    }
    return actions.concat([
        {
            title: 'Group by this column',
            icon: 'group-items',
            command: 'group',
            checked: model.group === 'column:' + column.name,
            enabled: !model.busy
        },
        {
            title: 'Remove grouping',
            icon: 'ungroup-items',
            command: 'ungroup',
            enabled: !model.busy && model.group !== 'none'
        },
        { separator: true },
        {
            title: 'Edit Column Definition',
            icon: 'edit',
            command: 'edit_definition',
            status:
                column.widgetClass ||
                column.resolvedClass ||
                (column.display || {}).handler ||
                '',
            statusTranslate: false,
            enabled
        },
        {
            title: 'Column Manager',
            icon: 'view-column',
            command: 'columns',
            enabled
        },
        {
            title: 'Remove Column',
            icon: 'visibility-off',
            command: 'remove',
            enabled: enabled && model.count > 1,
            status:
                model.count > 1
                    ? ''
                    : translate(
                          'At least one column must remain visible',
                          language
                      )
        },
        {
            title: 'Move column left',
            icon: 'MDI_ARROW_LEFT',
            command: 'left',
            enabled: enabled && model.index > 0
        },
        {
            title: 'Move column right',
            icon: 'MDI_ARROW_RIGHT',
            command: 'right',
            enabled: enabled && model.index < model.count - 1
        },
        { separator: true },
        { title: 'Row height', header: true },
        {
            title: 'Fit to Preview',
            command: 'row_height:0',
            checked: !!model.automaticRowHeight
        },
        ...metrics.heights.map((height, index) => ({
            title: ['Compact rows', 'Comfortable rows', 'Large rows'][index],
            command: 'row_height:' + height,
            checked: !model.automaticRowHeight && model.rowHeight === height
        }))
    ]);
}

export function viewActions(views, enabled, language) {
    const actions = [{ title: 'Table views', header: true }];
    for (let index = 0; index < views.length; index++) {
        const view = views[index];
        actions.push({
            title:
                view.view === 'table'
                    ? translate('Default table', language)
                    : String(view.title || view.view || ''),
            icon: 'table-view',
            command: 'select:' + index,
            checked: !!view.current,
            translate: false
        });
    }
    return actions.concat([
        { separator: true },
        {
            title: 'Configure columns',
            icon: 'view-column',
            command: 'configure',
            enabled
        },
        {
            title: 'Save current as new view…',
            icon: 'add',
            command: 'save_as',
            enabled
        }
    ]);
}
