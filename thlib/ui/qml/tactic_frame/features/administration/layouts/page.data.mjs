import { node, rect } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import * as Document from './page.document.mjs';

export function inDetails(document, key) {
    const path = Document.path(key);
    return path
        .slice(0, -1)
        .some(
            (_, index) =>
                Document.block(document, path.slice(0, index + 1).join('.'))
                    .kind === 'details'
        );
}
export function mode(document, key) {
    const item = key ? Document.block(document, key) : null;
    if (
        !item ||
        ![
            'text',
            'heading',
            'markdown',
            'image',
            'field',
            'form',
            'action'
        ].includes(item.kind)
    )
        return '';
    if (item.binding && item.binding !== 'auto') return item.binding;
    if (['image', 'form', 'action', 'field'].includes(item.kind))
        return item.source_key
            ? 'record'
            : inDetails(document, key)
              ? 'selection'
              : 'project';
    return item.source_key
        ? 'record'
        : item.field
          ? inDetails(document, key)
              ? 'selection'
              : 'project'
          : 'static';
}
function selectedType(document, key) {
    const path = Document.path(key);
    for (let size = path.length; size > 0; size--) {
        const item = Document.block(document, path.slice(0, size).join('.'));
        if (item.search_type) return item.search_type;
    }
    const row = Document.layers(document).find(
        (layer) => layer.kind === 'items'
    );
    return row ? Document.block(document, row.key).search_type || '' : '';
}
export function scope(document, key) {
    if (
        !document?.blocks ||
        !key ||
        !Document.layers(document).some((row) => row.key === key)
    )
        return { searchType: '', recordKey: '' };
    const item = Document.block(document, key),
        binding = mode(document, key);
    const searchType =
        binding === 'project'
            ? 'sthpw/project'
            : binding === 'selection'
              ? selectedType(document, key)
              : binding === 'record'
                ? item.search_type || (item.source_key || '').split('?')[0]
                : [
                        'table',
                        'items',
                        'metric',
                        'chart',
                        'summary',
                        'row',
                        'column'
                    ].includes(item.kind)
                  ? item.search_type || ''
                  : '';
    const result = {
        searchType,
        recordKey: binding === 'record' ? item.source_key || '' : ''
    };
    if (item.kind === 'form') result.editView = item.edit_view || 'edit';
    return result;
}
export function change(document, key, field, value) {
    const result = Document.copy(document),
        item = Document.block(result, key);
    if (field === 'binding') {
        if (
            ![
                'text',
                'heading',
                'markdown',
                'image',
                'field',
                'form',
                'action'
            ].includes(item.kind) ||
            !['static', 'project', 'selection', 'record'].includes(value)
        )
            throw Error('Choose a supported field binding');
        if (value === 'selection' && !inDetails(result, key))
            throw Error('Place selection-bound widgets inside Details');
        const type = selectedType(result, key);
        if (item.kind === 'form') item.fields = [];
        Object.assign(item, {
            binding: value,
            field: '',
            source_key: '',
            search_type: value === 'selection' ? type : ''
        });
    } else if (field === 'search_type') {
        item.search_type = value;
        if (mode(result, key) === 'record') item.source_key = '';
    } else if (['field', 'source_key', 'view'].includes(field))
        item[field] = value;
    else throw Error('Unsupported data property');
    return result;
}
export function type(field) {
    const value = String(field?.dataType || '').toLowerCase();
    return /bool/.test(value)
        ? 'boolean'
        : /int|numeric|decimal|real|double|float/.test(value)
          ? 'number'
          : /date|time/.test(value)
            ? 'date'
            : /json|array|blob|bytea/.test(value)
              ? 'complex'
              : 'text';
}
const defaultValue = (field) =>
    type(field) === 'boolean' ? false : type(field) === 'number' ? 0 : '';
export function relation(condition) {
    // Qt exposes a Python None in QVariantMap as undefined.
    return condition.value == null && ['=', '!='].includes(condition.relation)
        ? condition.relation === '='
            ? 'empty'
            : 'notEmpty'
        : condition.relation;
}
export function value(field, raw) {
    if (type(field) === 'boolean') {
        if (![true, false, 'true', 'false'].includes(raw))
            throw Error('Choose Yes or No');
        return raw === true || raw === 'true';
    }
    if (type(field) === 'number') {
        if (String(raw).trim() === '' || !Number.isFinite(Number(raw)))
            throw Error('Enter a valid number');
        return Number(raw);
    }
    if (
        type(field) === 'date' &&
        raw &&
        !/^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?$/.test(
            String(raw)
        )
    )
        throw Error('Choose a valid date');
    return String(raw);
}
export function filter(document, key, event, metadata) {
    const result = Document.copy(document),
        item = Document.block(result, key);
    if (!['items', 'table', 'metric', 'chart', 'summary'].includes(item.kind))
        throw Error('Filters belong to a data collection');
    const fields = (metadata?.fields || []).filter(
        (row) => type(row) !== 'complex'
    );
    item.filters = item.filters || [];
    if (event.action === 'add') {
        if (item.filters.length >= 32)
            throw Error('Select at most 32 filter conditions');
        const field = fields.find((row) => row.value === 'code') || fields[0];
        if (!field) throw Error('Choose a data source first');
        item.filters.push({
            column: field.value,
            relation: '=',
            value: defaultValue(field)
        });
        return result;
    }
    if (
        !Number.isInteger(event.index) ||
        event.index < 0 ||
        event.index >= item.filters.length
    )
        throw Error('Choose a filter condition');
    if (event.action === 'remove') {
        item.filters.splice(event.index, 1);
        return result;
    }
    const row = item.filters[event.index],
        field = fields.find(
            (field) =>
                field.value ===
                (event.field === 'column' ? event.value : row.column)
        );
    if (!field) throw Error('Choose a field from the current data source');
    if (event.field === 'column')
        Object.assign(row, {
            column: event.value,
            relation: '=',
            value: defaultValue(field)
        });
    else if (event.field === 'relation') {
        const empty = ['empty', 'notEmpty'].includes(event.value);
        if (
            ![
                '=',
                '!=',
                '<',
                '<=',
                '>',
                '>=',
                'like',
                'empty',
                'notEmpty'
            ].includes(event.value)
        )
            throw Error('Choose a supported filter condition');
        row.relation = empty
            ? event.value === 'empty'
                ? '='
                : '!='
            : event.value;
        row.value = empty
            ? null
            : row.value == null
              ? defaultValue(field)
              : row.value;
    } else if (event.field === 'value') row.value = value(field, event.value);
    else throw Error('Unsupported filter property');
    return result;
}
export function options(rows, current, language) {
    const result = (rows || []).map((row) => ({
        value: row.value,
        label: row.label
    }));
    if (current && !result.some((row) => row.value === current))
        result.push({
            value: current,
            label: current + ' · ' + translate('Unavailable', language)
        });
    return result;
}
export function fields(model, ui, width, language, enabled) {
    if (!ui.selected) return [];
    const item = Document.block(model.document, ui.selected),
        binding = mode(model.document, ui.selected),
        requested = scope(model.document, ui.selected);
    const metadata =
            model.dataSource?.searchType === requested.searchType &&
            (!requested.editView ||
                model.dataSource?.editView === requested.editView)
                ? model.dataSource
                : {},
        tr = (text) => translate(text, language);
    const fields = [],
        collection = ['table', 'items', 'metric', 'chart', 'summary'].includes(
            item.kind
        ),
        condition =
            ['row', 'column', 'grid'].includes(item.kind) &&
            inDetails(model.document, ui.selected);
    if (!collection && !binding && !condition) return fields;
    const sourceReady = enabled && !model.dataBusy && !!metadata.searchType;
    fields.push({
        kind: 'Heading',
        id: 'pageDataHeading',
        title: 'Data',
        description: 'Data settings apply to this widget only.'
    });
    function choice(id, title, current, rows, field) {
        fields.push({
            kind: 'Choice',
            id,
            title,
            options: options(rows, current, language),
            props: {
                value: current,
                enabled: ['binding', 'search_type'].includes(field)
                    ? enabled
                    : sourceReady,
                action: { type: 'data', field }
            }
        });
    }
    if (binding)
        choice(
            'pageBinding',
            'Content source',
            binding,
            [
                ...(['image', 'form', 'action', 'field'].includes(item.kind)
                    ? []
                    : [['static', 'Static text']]),
                ['project', 'Current project'],
                ...(inDetails(model.document, ui.selected)
                    ? [['selection', 'Selected object']]
                    : []),
                ['record', 'Specific record']
            ].map(([value, label]) => ({ value, label: tr(label) })),
            'binding'
        );
    if (collection || condition || ['selection', 'record'].includes(binding)) {
        const sources = (model.searchTypes || []).filter(
            (row) => item.kind !== 'items' || row.projectOwned !== false
        );
        choice(
            'pageProperty_search_type',
            collection ? 'Data source' : 'Record type',
            item.search_type || '',
            [
                {
                    value: '',
                    label: tr(
                        condition ? 'Any record type' : 'Choose a data source'
                    )
                }
            ].concat(sources),
            'search_type'
        );
    }
    if (requested.searchType) {
        if (model.dataBusy || model.dataError || !metadata.searchType)
            fields.push({
                kind: 'Heading',
                id: 'pageDataStatus',
                title: model.dataError || 'Loading source fields…'
            });
        if (model.dataError)
            fields.push({
                kind: 'Button',
                id: 'pageDataRetry',
                title: 'Retry',
                props: { icon: 'refresh', action: { type: 'source' } }
            });
    }
    if (['items', 'table'].includes(item.kind)) {
        choice(
            'pageProperty_view',
            'Saved view',
            item.view || 'table',
            item.kind === 'items' ? metadata.itemViews : metadata.tableViews,
            'view'
        );
        fields[fields.length - 1].trailingAction = {
            title:
                item.kind === 'items'
                    ? 'Edit card layout'
                    : 'Edit table columns',
            icon: 'open-in-new',
            enabled: !model.busy && !!requested.searchType,
            action: { type: item.kind === 'items' ? 'card' : 'columns' }
        };
    }
    if (binding === 'record' && requested.searchType) {
        fields.push({
            id: 'pageRecordQuery',
            title: 'Find record',
            props: {
                text: ui.recordQuery || '',
                action: { type: 'recordQuery' }
            }
        });
        fields.push({
            kind: 'Button',
            id: 'pageRecordFind',
            title: 'Find records',
            props: {
                icon: 'search',
                enabled: !model.dataBusy,
                action: { type: 'source', query: true }
            }
        });
        choice(
            'pageRecord',
            'Source record',
            item.source_key || '',
            [{ value: '', label: tr('Choose a record') }].concat(
                metadata.records || []
            ),
            'source_key'
        );
        if (metadata.more)
            fields.push({
                kind: 'Heading',
                id: 'pageRecordMore',
                title: 'More matches. Refine your search.'
            });
    }
    if (item.kind === 'form') {
        fields.push({
            kind: 'Heading',
            id: 'pageNativeFields',
            title: 'Form fields',
            description: 'Select fields from the existing native edit view.'
        });
        for (const row of metadata.editFields || []) {
            const selected = item.fields || [];
            fields.push({
                kind: 'CheckBox',
                id: 'pageFormField_' + row.value,
                title: row.label,
                dataLabel: true,
                props: {
                    checked: selected.includes(row.value),
                    enabled: sourceReady,
                    action: { type: 'formField', name: row.value }
                }
            });
        }
    }
    if (
        binding &&
        binding !== 'static' &&
        !['image', 'form', 'action'].includes(item.kind)
    ) {
        const sourceFields = (metadata.fields || []).filter((row) =>
            item.kind === 'markdown'
                ? type(row) === 'text'
                : type(row) !== 'complex'
        );
        choice(
            'pageBindingField',
            'Source field',
            item.field || '',
            [{ value: '', label: tr('Choose a source field') }].concat(
                sourceFields
            ),
            'field'
        );
    }
    if (collection) {
        fields.push({
            kind: 'Heading',
            id: 'pageFiltersHeading',
            title: 'Filters',
            description: 'All conditions must match (AND).'
        });
        (item.filters || []).forEach((row, index) => {
            const id = 'pageFilter_' + index,
                sourceField = (metadata.fields || []).find(
                    (field) => field.value === row.column
                ),
                empty = row.value == null;
            const w = width - 32,
                children = [];
            children.push(
                node('Choice', id + '_column', rect(0, 0, w - 40, 34), {
                    label: tr('Filter field'),
                    value: row.column,
                    options: options(
                        (metadata.fields || []).filter(
                            (row) => type(row) !== 'complex'
                        ),
                        row.column,
                        language
                    ),
                    enabled: sourceReady,
                    action: { type: 'filter', index, field: 'column' }
                })
            );
            children.push(
                node('Button', id + '_remove', rect(w - 32, 0, 32, 34), {
                    text: tr('Remove condition'),
                    icon: 'delete',
                    iconOnly: true,
                    enabled,
                    action: { type: 'filter', index, action: 'remove' }
                })
            );
            const operators = [
                ['=', 'Is'],
                ['!=', 'Is not'],
                ...(['number', 'date'].includes(type(sourceField))
                    ? [
                          ['<', 'Less than'],
                          ['<=', 'At most'],
                          ['>', 'Greater than'],
                          ['>=', 'At least']
                      ]
                    : []),
                ...(type(sourceField) === 'text'
                    ? [['like', 'Matches text pattern']]
                    : []),
                ['empty', 'Is empty'],
                ['notEmpty', 'Is not empty']
            ];
            children.push(
                node('Choice', id + '_relation', rect(0, 42, w, 34), {
                    label: tr('Filter condition'),
                    value: relation(row),
                    enabled: sourceReady && !!sourceField,
                    options: options(
                        operators.map(([value, label]) => ({
                            value,
                            label: tr(label)
                        })),
                        relation(row),
                        language
                    ),
                    action: { type: 'filter', index, field: 'relation' }
                })
            );
            if (!empty) {
                const key = 'filter:' + index,
                    content = Object.prototype.hasOwnProperty.call(ui.text, key)
                        ? ui.text[key]
                        : String(row.value);
                const props = {
                    label: tr('Filter value'),
                    text: content,
                    enabled: sourceReady && !!sourceField,
                    inputMode:
                        type(sourceField) === 'number' ? 'decimal' : 'text',
                    action: { type: 'buffer', key },
                    commitAction: { type: 'filterCommit', index, key }
                };
                if (type(sourceField) === 'boolean')
                    Object.assign(props, {
                        value: String(row.value),
                        options: [
                            { value: 'true', label: tr('Yes') },
                            { value: 'false', label: tr('No') }
                        ],
                        action: { type: 'filter', index, field: 'value' }
                    });
                if (type(sourceField) === 'date')
                    Object.assign(props, {
                        includeTime: /time/i.test(sourceField.dataType),
                        action: { type: 'filter', index, field: 'value' },
                        commitAction: null
                    });
                children.push(
                    node(
                        type(sourceField) === 'boolean'
                            ? 'Choice'
                            : type(sourceField) === 'date'
                              ? 'DateChoice'
                              : 'Field',
                        id + '_value',
                        rect(0, 84, w, 36),
                        props
                    )
                );
            }
            fields.push({
                kind: 'Box',
                id,
                fullWidth: true,
                height: empty ? 84 : 128,
                props: { children }
            });
        });
        if ((item.filters || []).some((row) => row.relation === 'like'))
            fields.push({
                kind: 'Heading',
                id: 'pagePatternHint',
                title: 'Use % to match any text, for example %robot%.'
            });
        fields.push({
            kind: 'Button',
            id: 'pageFilterAdd',
            title: 'Add condition',
            props: {
                icon: 'add',
                enabled:
                    sourceReady &&
                    !!metadata.fields?.length &&
                    (item.filters || []).length < 32,
                action: { type: 'filter', action: 'add' }
            }
        });
    }
    return fields;
}
