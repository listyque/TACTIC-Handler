import { translate } from '../../../core/strings.mjs';
import * as Document from './page.document.mjs';
import * as Data from './page.data.mjs';

const collections = ['items', 'table', 'metric', 'chart', 'summary'];
export function scope(document, ui) {
    if (ui.selected) return Data.scope(document, ui.selected);
    return {
        searchType: document?.filters?.[ui.pageFilter || 0]?.search_type || '',
        recordKey: ''
    };
}
function filterDocument(document, ui) {
    const item = document.filters[ui.pageFilter || 0];
    return {
        blocks: [
            {
                kind: 'metric',
                search_type: item.search_type,
                filters: [
                    {
                        column: item.column,
                        relation: item.relation,
                        value: item.value
                    }
                ]
            }
        ]
    };
}
export const events = [
    'pageFilterAdd',
    'pageFilterRemove',
    'pageFilterSelect',
    'pageFilterChange',
    'pageSource',
    'pageCondition',
    'pageConditionCommit',
    'report',
    'reportCommit'
];
export function edit(model, ui, event) {
    const document = Document.copy(model.document),
        next = Object.assign({}, ui);
    const filters = document.filters || (document.filters = []);
    const index = ui.pageFilter || 0;
    if (event.type === 'pageFilterSelect') {
        next.pageFilter = Number(event.value);
        return { ui: next };
    }
    if (event.type === 'pageFilterAdd') {
        if (filters.length >= 8)
            throw Error('A page supports at most eight shared filters');
        let number = 1;
        while (filters.some((item) => item.name === 'filter_' + number))
            number++;
        filters.push({
            name: 'filter_' + number,
            title: 'Filter ' + number,
            search_type: model.searchTypes?.[0]?.value || '',
            column: 'code',
            relation: '=',
            value: '',
            enabled: false
        });
        next.pageFilter = filters.length - 1;
    } else if (event.type === 'pageFilterRemove') {
        filters.splice(index, 1);
        next.pageFilter = Math.max(0, index - 1);
    } else if (
        [
            'pageSource',
            'pageCondition',
            'pageConditionCommit',
            'pageFilterChange'
        ].includes(event.type)
    ) {
        const item = filters[index];
        if (!item) throw Error('Choose a page filter');
        if (event.type === 'pageSource') item.search_type = event.value;
        else if (event.type === 'pageFilterChange') {
            if (!['title', 'enabled'].includes(event.field))
                throw Error('Unsupported page filter property');
            item[event.field] = event.key ? ui.text[event.key] : event.value;
        } else {
            if (
                event.type === 'pageConditionCommit' &&
                !Object.prototype.hasOwnProperty.call(ui.text, event.key)
            )
                return { ui: next };
            const result = Data.filter(
                filterDocument(document, ui),
                '0',
                event.type === 'pageConditionCommit'
                    ? Object.assign({}, event, {
                          field: 'value',
                          value: ui.text[event.key]
                      })
                    : event,
                model.dataSource
            );
            Object.assign(item, result.blocks[0].filters[0]);
        }
        if (event.key) {
            next.text = Object.assign({}, ui.text);
            delete next.text[event.key];
        }
    } else {
        const item = Document.block(document, ui.selected);
        if (!item || !collections.includes(item.kind))
            throw Error('Choose a data widget');
        const value = event.key ? ui.text[event.key] : event.value;
        if (event.field === 'mappingMode')
            item.page_filters = value === 'auto' ? null : {};
        else if (event.field === 'mapping') {
            item.page_filters = Object.assign({}, item.page_filters);
            if (value) item.page_filters[event.name] = value;
            else delete item.page_filters[event.name];
        } else if (
            ['group_limit', 'group_order', 'measure', 'chart_type'].includes(
                event.field
            )
        )
            item[event.field] = value;
        else {
            const field = event.section === 'group' ? 'group_by' : 'aggregates';
            const rows = item[field] || (item[field] = []);
            if (event.action === 'add') {
                if (rows.length >= (field === 'group_by' ? 3 : 8))
                    throw Error('Report dimension limit reached');
                if (field === 'group_by')
                    rows.push({
                        column:
                            model.dataSource?.fields?.find(
                                (f) => Data.type(f) !== 'complex'
                            )?.value || 'code',
                        period: 'value'
                    });
                else {
                    let number = 1;
                    while (rows.some((row) => row.name === 'measure_' + number))
                        number++;
                    rows.push({
                        name: 'measure_' + number,
                        title: 'Count',
                        function: 'count',
                        column: ''
                    });
                }
            } else if (event.action === 'remove') rows.splice(event.index, 1);
            else {
                const row = rows[event.index];
                if (
                    !row ||
                    !(
                        field === 'group_by'
                            ? ['column', 'period', 'title']
                            : ['column', 'function', 'title']
                    ).includes(event.field)
                )
                    throw Error('Choose a report field');
                if (event.field === 'function') {
                    const titles = {
                        count: 'Count',
                        sum: 'Sum',
                        avg: 'Average',
                        min: 'Minimum',
                        max: 'Maximum'
                    };
                    if (row.title === titles[row.function])
                        row.title = titles[value];
                }
                row[event.field] = value;
            }
        }
        if (event.key) {
            next.text = Object.assign({}, ui.text);
            delete next.text[event.key];
        }
    }
    return { document, ui: next };
}
function retag(value) {
    if (!value || typeof value !== 'object') return value;
    if (Array.isArray(value)) return value.map(retag);
    const result = {};
    for (const [key, item] of Object.entries(value)) result[key] = retag(item);
    if (result.type === 'data') result.type = 'pageSource';
    if (result.type === 'filter') result.type = 'pageCondition';
    if (result.type === 'filterCommit') result.type = 'pageConditionCommit';
    return result;
}
export function fields(model, ui, width, language, enabled) {
    const result = [],
        tr = (text) => translate(text, language),
        document = model.document;
    function heading(id, title, description = '') {
        result.push({ kind: 'Heading', id, title, description });
    }
    function choice(id, title, value, rows, action) {
        result.push({
            kind: 'Choice',
            id,
            title,
            options: Data.options(rows, value, language),
            props: { value, enabled, action }
        });
    }
    function button(id, title, action, icon = 'add') {
        result.push({
            kind: 'Button',
            id,
            title,
            props: { enabled, icon, action }
        });
    }
    function text(id, title, value, action) {
        const key = id;
        result.push({
            id,
            title,
            props: {
                enabled,
                text: Object.prototype.hasOwnProperty.call(ui.text, key)
                    ? ui.text[key]
                    : value,
                action: { type: 'buffer', key },
                commitAction: Object.assign({}, action, { key })
            }
        });
    }
    if (!ui.selected) {
        const filters = document.filters || [],
            index = ui.pageFilter || 0,
            item = filters[index];
        heading(
            'pageSharedHeading',
            'Shared page filters',
            'Apply the same condition to several widgets. Runtime values do not change the saved page.'
        );
        choice(
            'pageSharedSelect',
            'Page filter',
            String(index),
            filters.map((item, i) => ({ value: String(i), label: item.title })),
            { type: 'pageFilterSelect' }
        );
        button('pageSharedAdd', 'Add page filter', { type: 'pageFilterAdd' });
        if (!item) return result;
        text('pageSharedTitle', 'Filter label', item.title, {
            type: 'pageFilterChange',
            field: 'title'
        });
        result.push({
            kind: 'Switch',
            id: 'pageSharedEnabled',
            title: 'Enabled by default',
            props: {
                checked: item.enabled,
                enabled,
                action: { type: 'pageFilterChange', field: 'enabled' }
            }
        });
        const data = Data.fields(
            Object.assign({}, model, {
                document: filterDocument(document, ui)
            }),
            Object.assign({}, ui, { selected: '0' }),
            width,
            language,
            enabled
        ).filter(
            (field) => !['pageDataHeading', 'pageFilterAdd'].includes(field.id)
        );
        for (const field of data)
            if (field.id === 'pageFilter_0')
                field.props.children = field.props.children.filter(
                    (node) => !node.id.endsWith('_remove')
                );
        result.push(...data.map(retag));
        button(
            'pageSharedRemove',
            'Remove page filter',
            { type: 'pageFilterRemove' },
            'delete'
        );
        return result;
    }
    const item = Document.block(document, ui.selected);
    if (!collections.includes(item.kind)) return result;
    const metadata =
        model.dataSource?.searchType === item.search_type
            ? model.dataSource
            : {};
    const sourceFields = (metadata.fields || []).filter(
        (field) => Data.type(field) !== 'complex'
    );
    enabled = enabled && !model.dataBusy && !!metadata.searchType;
    if (document.filters?.length) {
        heading('pageMappingsHeading', 'Shared page filters');
        choice(
            'pageMappingMode',
            'Filter binding',
            item.page_filters == null ? 'auto' : 'custom',
            [
                { value: 'auto', label: tr('Match the same data source') },
                { value: 'custom', label: tr('Choose fields explicitly') }
            ],
            { type: 'report', field: 'mappingMode' }
        );
        if (item.page_filters != null)
            for (const filter of document.filters)
                choice(
                    'pageMapping_' + filter.name,
                    filter.title,
                    item.page_filters[filter.name] || '',
                    [{ value: '', label: tr('Not applied') }].concat(
                        sourceFields
                    ),
                    { type: 'report', field: 'mapping', name: filter.name }
                );
    }
    if (!['metric', 'chart', 'summary'].includes(item.kind)) return result;
    heading(
        'pageReportHeading',
        'Grouping and aggregates',
        'Totals use all matching records before the displayed group limit.'
    );
    if (item.kind !== 'metric') {
        (item.group_by || []).forEach((group, index) => {
            const action = { type: 'report', section: 'group', index };
            text(
                'pageGroup_' + index + '_title',
                'Group label (optional)',
                group.title || '',
                Object.assign({}, action, {
                    type: 'reportCommit',
                    field: 'title'
                })
            );
            choice(
                'pageGroup_' + index + '_column',
                'Group field',
                group.column,
                sourceFields,
                Object.assign({}, action, { field: 'column' })
            );
            choice(
                'pageGroup_' + index + '_period',
                'Group interval',
                group.period || 'value',
                (Data.type(
                    sourceFields.find((field) => field.value === group.column)
                ) === 'date'
                    ? ['value', 'year', 'month', 'day']
                    : ['value']
                ).map((value) => ({
                    value,
                    label: tr(
                        {
                            value: 'Field value',
                            year: 'Year (UTC)',
                            month: 'Month (UTC)',
                            day: 'Day (UTC)'
                        }[value]
                    )
                })),
                Object.assign({}, action, { field: 'period' })
            );
            button(
                'pageGroup_' + index + '_remove',
                'Remove group',
                Object.assign({}, action, { action: 'remove' }),
                'delete'
            );
        });
        button('pageGroupAdd', 'Add grouping', {
            type: 'report',
            section: 'group',
            action: 'add'
        });
    }
    const measures = item.aggregates || [];
    measures.forEach((measure, index) => {
        const action = { type: 'report', section: 'measure', index };
        text(
            'pageMeasure_' + index + '_title',
            'Measure label',
            measure.title,
            Object.assign({}, action, { type: 'reportCommit', field: 'title' })
        );
        choice(
            'pageMeasure_' + index + '_function',
            'Aggregate',
            measure.function,
            ['count', 'sum', 'avg', 'min', 'max'].map((value) => ({
                value,
                label: tr(
                    {
                        count: 'Count',
                        sum: 'Sum',
                        avg: 'Average',
                        min: 'Minimum',
                        max: 'Maximum'
                    }[value]
                )
            })),
            Object.assign({}, action, { field: 'function' })
        );
        choice(
            'pageMeasure_' + index + '_column',
            'Measure field',
            measure.column || '',
            [{ value: '', label: tr('All rows (count only)') }].concat(
                sourceFields.filter(
                    (field) =>
                        measure.function === 'count' ||
                        Data.type(field) === 'number'
                )
            ),
            Object.assign({}, action, { field: 'column' })
        );
        button(
            'pageMeasure_' + index + '_remove',
            'Remove measure',
            Object.assign({}, action, { action: 'remove' }),
            'delete'
        );
    });
    if (item.kind !== 'metric' || !measures.length)
        button('pageMeasureAdd', 'Add measure', {
            type: 'report',
            section: 'measure',
            action: 'add'
        });
    if (item.kind !== 'metric') {
        choice(
            'pageGroupOrder',
            'Group order',
            item.group_order || 'group',
            [
                { value: 'group', label: tr('By group') },
                {
                    value: 'value_desc',
                    label: tr('Largest first (first measure)')
                },
                {
                    value: 'value_asc',
                    label: tr('Smallest first (first measure)')
                }
            ],
            { type: 'report', field: 'group_order' }
        );
        choice(
            'pageGroupLimit',
            'Maximum groups',
            item.group_limit || 50,
            [10, 25, 50, 100].map((value) => ({ value, label: String(value) })),
            { type: 'report', field: 'group_limit' }
        );
    }
    if (item.kind === 'chart') {
        choice(
            'pageChartType',
            'Chart type',
            item.chart_type || 'bar',
            ['bar', 'line', 'donut'].map((value) => ({
                value,
                label: tr(
                    {
                        bar: 'Bar chart',
                        line: 'Line chart',
                        donut: 'Donut chart'
                    }[value]
                )
            })),
            { type: 'report', field: 'chart_type' }
        );
        choice(
            'pageChartMeasure',
            'Chart measure',
            item.measure || measures[0]?.name || 'count',
            measures.length
                ? measures.map((row) => ({ value: row.name, label: row.title }))
                : [{ value: 'count', label: tr('Count') }],
            { type: 'report', field: 'measure' }
        );
    }
    return result;
}
