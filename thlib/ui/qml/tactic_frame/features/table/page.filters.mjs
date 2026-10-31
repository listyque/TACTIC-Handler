import { node, rect, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { value } from '../administration/layouts/page.data.mjs';
import { buttonWidth } from '../../controls/buttons/metrics.mjs';
import { textStyles } from '../../core/foundation.mjs';

export function initial(definitions = []) {
    const result = {};
    for (const item of definitions || [])
        result[item.name] = {
            enabled: item.enabled,
            value: item.value ?? null
        };
    return result;
}
export function change(draft, event) {
    const result = Object.assign({}, draft);
    result[event.name] = Object.assign({}, draft[event.name]);
    result[event.name][event.field] = event.value;
    return result;
}
export function values(definitions, draft) {
    const result = {};
    for (const item of definitions) {
        const row = draft[item.name] || item;
        const raw =
            row.enabled && item.value != null
                ? value({ dataType: item.dataType }, row.value)
                : row.value;
        result[item.name] = { enabled: row.enabled, value: raw ?? null };
    }
    return result;
}
export function query(definitions, text) {
    const colon = text.indexOf(':');
    if (colon < 0) return { field: '', text: text.trim() };
    const key = text.slice(0, colon).trim().toLocaleLowerCase();
    const field = definitions.find((item) =>
        [item.name, item.title].some((name) => name.toLocaleLowerCase() === key)
    );
    if (!field) throw Error('Choose a configured page filter');
    return { field: field.name, text: text.slice(colon + 1).trim() };
}
export function suggestions(definitions, text, records = [], language = 'en') {
    if (!text.trim()) return [];
    const tr = (text) => translate(text, language),
        request = query(definitions, text);
    const fields = request.field
        ? []
        : definitions
              .filter((item) =>
                  [item.name, item.title].some((name) =>
                      name
                          .toLocaleLowerCase()
                          .includes(request.text.toLocaleLowerCase())
                  )
              )
              .map((item) => ({
                  title: item.title + ':',
                  description: tr('Choose a value'),
                  name: item.name,
                  field: true
              }));
    return fields
        .concat(
            records
                .map((record) => {
                    const field = definitions.find(
                        (item) => item.name === record.name
                    );
                    return field
                        ? Object.assign({}, record, {
                              title:
                                  record.value === null
                                      ? tr('Is empty')
                                      : String(record.value),
                              description: field.title
                          })
                        : null;
                })
                .filter(Boolean)
        )
        .slice(0, 20);
}
export function choose(definitions, draft, record) {
    const field = definitions.find((item) => item.name === record.name);
    if (!field) throw Error('Choose a configured page filter');
    if (record.field) return { text: field.title + ': ', draft, apply: false };
    return {
        text: '',
        draft: Object.assign({}, draft, {
            [field.name]: { enabled: true, value: record.value }
        }),
        apply: true
    };
}
export function submit(definitions, draft, text, records) {
    const request = query(definitions, text);
    if (request.field) {
        const field = definitions.find((item) => item.name === request.field);
        const raw = request.text.replace(/^"(.*)"$/, '$1');
        return choose(definitions, draft, {
            name: field.name,
            value: value({ dataType: field.dataType }, raw)
        });
    }
    const candidates = records.filter((record) => !record.field);
    if (candidates.length === 1)
        return choose(definitions, draft, candidates[0]);
    throw Error('Choose a suggestion or enter Field: value');
}
export function describe(
    definitions,
    draft,
    width,
    language,
    enabled = true,
    measure = (text) => text.length * 7
) {
    if (!definitions?.length) return { height: 0, nodes: [] };
    const tr = (text) => translate(text, language),
        nodes = [
            node('View', 'pageRuntimeSearch', rect(0, 0, width, 38), {
                view: 'pageFilterSearch'
            })
        ];
    let x = 0,
        y = 46;
    for (const field of definitions) {
        const row = draft[field.name] || field;
        if (!row.enabled) continue;
        const caption =
            field.title +
            ' ' +
            (field.relation === '=' ? ':' : field.relation) +
            ' ' +
            (row.value === null ? tr('Is empty') : String(row.value));
        const size = Math.min(
            width,
            buttonWidth(measure(caption, textStyles.body, 600), true)
        );
        if (x && x + size > width) {
            x = 0;
            y += 38;
        }
        nodes.push(
            button(
                'pageRuntimeRemove_' + field.name,
                rect(x, y, size, 32),
                caption,
                'close',
                { type: 'page-filter-remove', name: field.name },
                enabled,
                { tonal: true }
            )
        );
        x += size + 8;
    }
    return { height: nodes.length > 1 ? y + 32 : 38, nodes };
}
