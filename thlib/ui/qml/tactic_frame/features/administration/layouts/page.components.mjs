import { translate } from '../../../core/strings.mjs';
import * as Document from './page.document.mjs';

export function componentFields(fields, item, ui, canEdit, language, field) {
    const tr = (text) => translate(text, language);
    function choice(name, title, value, options) {
        fields.push({
            kind: 'Choice',
            id: 'pageProperty_' + name,
            title,
            options: options.map(([value, label]) => ({
                value: String(value),
                label: tr(label)
            })),
            props: {
                value: String(value),
                enabled: canEdit && (ui.selection || []).length < 2,
                action: { type: 'change', field: name }
            }
        });
    }
    if (['icon', 'button', 'action', 'metric'].includes(item.kind))
        fields.push({
            kind: 'IconChoice',
            id: 'pageProperty_icon',
            title: 'Icon',
            props: {
                value: item.icon || '',
                enabled: canEdit,
                action: { type: 'change', field: 'icon' }
            }
        });
    if (item.kind === 'icon')
        field('icon_size', 'Icon size', item.icon_size || 32);
    if (['button', 'action'].includes(item.kind))
        choice('button_style', 'Button style', item.button_style || 'normal', [
            ['normal', 'Normal'],
            ['primary', 'Primary'],
            ['tonal', 'Tonal']
        ]);
    if (['text', 'heading', 'field'].includes(item.kind)) {
        choice('text_role', 'Text style', item.text_role || 'auto', [
            ['auto', 'Auto'],
            ['caption', 'Caption'],
            ['body', 'Body'],
            ['bodyLarge', 'Large body'],
            ['title', 'Title'],
            ['heading', 'Heading'],
            ['display', 'Display'],
            ['statistic', 'Statistic'],
            ['hero', 'Hero']
        ]);
        choice('text_weight', 'Text weight', item.text_weight || 400, [
            [400, 'Normal'],
            [600, 'Semibold'],
            [700, 'Bold']
        ]);
        choice('text_align', 'Text alignment', item.text_align || 'left', [
            ['left', 'Left'],
            ['center', 'Center'],
            ['right', 'Right']
        ]);
    }
    if (['text', 'heading', 'icon', 'divider', 'field'].includes(item.kind)) {
        choice(
            'text_color',
            'Text / icon color',
            item.text_color || 'auto',
            [
                ['auto', 'Auto'],
                ['primaryText', 'Primary text'],
                ['secondaryText', 'Secondary text'],
                ['contentAccent', 'Accent'],
                ['error', 'Error']
            ].concat(
                (item.text_color || '').startsWith('#')
                    ? [[item.text_color, item.text_color]]
                    : []
            )
        );
        fields.push({
            kind: 'ColorChoice',
            id: 'pageCustomTextColor',
            title: 'Custom text / icon color',
            props: {
                value: (item.text_color || '').startsWith('#')
                    ? item.text_color
                    : '#607D8B',
                enabled: canEdit,
                action: { type: 'change', field: 'text_color' }
            }
        });
    }
    if (item.kind === 'field') {
        choice('format', 'Field display', item.format || 'plain', [
            ['plain', 'Text'],
            ['badge', 'Status badge'],
            ['progress', 'Progress'],
            ['date', 'Date'],
            ['datetime', 'Date and time'],
            ['number', 'Number']
        ]);
        fields.push({
            id: 'pageProperty_suffix',
            title: 'Value suffix',
            props: {
                text: Object.prototype.hasOwnProperty.call(
                    ui.text,
                    ui.selected + ':suffix'
                )
                    ? ui.text[ui.selected + ':suffix']
                    : item.suffix || '',
                enabled: canEdit,
                action: { type: 'buffer', key: ui.selected + ':suffix' },
                commitAction: {
                    type: 'commit',
                    field: 'suffix',
                    key: ui.selected + ':suffix'
                }
            }
        });
    }
    if (item.kind === 'action')
        choice(
            'native_action',
            'Native action',
            item.native_action || 'details',
            [
                ['details', 'Open details'],
                ['edit', 'Edit record'],
                ['notes', 'Notes'],
                ['copy_link', 'Copy link'],
                ['refresh', 'Refresh']
            ]
        );
    if (['form', 'action'].includes(item.kind))
        fields.push({
            id: 'pageProperty_edit_view',
            title: 'Native edit view',
            props: {
                text: Object.prototype.hasOwnProperty.call(
                    ui.text,
                    ui.selected + ':edit_view'
                )
                    ? ui.text[ui.selected + ':edit_view']
                    : item.edit_view || 'edit',
                enabled: canEdit,
                action: { type: 'buffer', key: ui.selected + ':edit_view' },
                commitAction: {
                    type: 'commit',
                    field: 'edit_view',
                    key: ui.selected + ':edit_view'
                }
            }
        });
    if (item.kind === 'image')
        choice('image_fit', 'Image fit', item.image_fit || 'contain', [
            ['contain', 'Contain'],
            ['cover', 'Cover']
        ]);
}

export function sizingFields(
    fields,
    item,
    ui,
    document,
    parent,
    canEdit,
    language,
    field
) {
    const tr = (text) => translate(text, language);
    const sizing = Object.assign(
        {
            width_mode: 'auto',
            height_mode: 'auto',
            min_width: 0,
            min_height: 0,
            max_width: null,
            max_height: null
        },
        item.sizing || {}
    );
    for (const [name, title] of [
        ['width_mode', 'Width behavior'],
        ['height_mode', 'Height behavior']
    ])
        fields.push({
            kind: 'Choice',
            id: 'pageSizing_' + name,
            title,
            options: [
                ['auto', 'Auto'],
                ['fixed', 'Fixed'],
                ['fill', 'Fill container'],
                ['content', 'Fit content']
            ].map(([value, label]) => ({ value, label: tr(label) })),
            props: {
                value: sizing[name],
                enabled: canEdit && (ui.selection || []).length < 2,
                action: { type: 'sizing', field: name }
            }
        });
    for (const [name, title] of [
        ['min_width', 'Minimum width'],
        ['max_width', 'Maximum width'],
        ['min_height', 'Minimum height'],
        ['max_height', 'Maximum height']
    ]) {
        const key = ui.selected + ':sizing:' + name;
        fields.push({
            id: 'pageSizing_' + name,
            title,
            props: {
                text: Object.prototype.hasOwnProperty.call(ui.text, key)
                    ? ui.text[key]
                    : String(sizing[name] ?? ''),
                enabled: canEdit && (ui.selection || []).length < 2,
                action: { type: 'buffer', key },
                commitAction: { type: 'sizingCommit', key, field: name }
            }
        });
    }
    if (['grid', 'form'].includes(item.kind)) {
        field('columns', 'Grid columns', item.columns || 3);
        field(
            'min_cell_width',
            'Minimum cell width',
            item.min_cell_width || 200
        );
        if (item.kind === 'grid')
            field('row_height', 'Grid row height', item.row_height || 120);
    }
    if (item.kind === 'row')
        field(
            'collapse_width',
            'Stack below width',
            item.collapse_width ?? 600
        );
    if (parent && Document.block(document, parent)?.kind === 'grid') {
        field('column_span', 'Column span', item.column_span || 1);
        field('row_span', 'Row span', item.row_span || 1);
    }
}
