import { node, rect, label } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function methods(catalog, status, query, language) {
    query = String(query || '').toLowerCase();
    return (catalog || []).filter(
        (record) =>
            (status === 'all' ||
                (status === 'common' &&
                    record.status === 'available' &&
                    (query || record.examples?.length)) ||
                record.status === status) &&
            `${record.name} ${record.signature} ${record.help?.[language] || record.help?.en || ''} ${record.reference}`
                .toLowerCase()
                .includes(query)
    );
}

export function method(record, selected, common, width, language) {
    const example =
        common && record.examples?.length
            ? translate(record.examples[0].label, language)
            : '';
    const height = example ? 54 : 34;
    const children = [
        label(
            'apiMethodName',
            rect(10, example ? 27 : 5, Math.max(0, width - 60), 24),
            record.name
        )
    ];
    if (example)
        children.push(
            label(
                'apiMethodExample',
                rect(10, 3, Math.max(0, width - 20), 24),
                example,
                { weight: 600 }
            )
        );
    if (record.writes)
        children.push(
            label(
                'apiMethodWrites',
                rect(Math.max(0, width - 50), example ? 27 : 5, 45, 24),
                translate('Write', language),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    return {
        nodes: [
            node(
                'Action',
                'apiMethod-' + record.name,
                rect(0, 0, width, height),
                {
                    text: record.name,
                    selected: record.name === selected,
                    normalColor: 'transparent',
                    selectedColor: 'selected',
                    action: { type: 'choose', name: record.name },
                    children
                }
            )
        ],
        height
    };
}

export function parameter(field, value, busy, width, language) {
    const tr = (text) => translate(text, language),
        controlY = 44;
    const height = field.type === 'json' ? 150 : 86;
    const nodes = [
        label('apiFieldTitle', rect(0, 0, width, 22), tr(field.label), {
            weight: 600
        }),
        label(
            'apiFieldDescription',
            rect(0, 22, width, 18),
            field.description ? tr(field.description) : field.name,
            { fontRole: 'caption', color: 'secondaryText' }
        )
    ];
    const kind =
        field.type === 'boolean'
            ? 'Switch'
            : field.type === 'json'
              ? 'Area'
              : 'Field';
    nodes.push(
        node(
            kind,
            'api-' + field.name,
            rect(0, controlY, width, height - controlY),
            {
                text: kind === 'Switch' ? tr(field.label) : String(value ?? ''),
                label: tr(field.label),
                checked: !!value,
                enabled: !busy,
                error: field.error || '',
                inputType:
                    field.type === 'password'
                        ? 'password'
                        : field.type === 'number'
                          ? 'number'
                          : 'text',
                action: { type: 'parameter', name: field.name },
                description: tr(field.description || '')
            }
        )
    );
    return { nodes, height };
}
