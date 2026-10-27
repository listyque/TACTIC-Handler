import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function views(model, language) {
    const tr = (text) => translate(text, language);
    const names = model.configuration?.layout_views || model.knownViews || [];
    return [...new Set([...names, model.view].filter(Boolean))].map((value) => {
        const example = {
            continuous_example: 'Tree example',
            table_example: 'Table example',
            cards_example: 'Cards example'
        }[value];
        return { value, label: example ? tr(example) + ' · ' + value : value };
    });
}

export function context(model, ui, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const enabled = !model.busy && !model.uncertain && !ui.confirmation;
    const stacked = width < 620,
        gap = 12,
        buttonWidth = 120;
    const typeWidth = stacked ? width : Math.min(280, width * 0.32);
    const viewX = stacked ? 0 : typeWidth + gap;
    const viewY = stacked ? 62 : 0;
    const viewWidth = stacked
        ? width - buttonWidth - gap
        : Math.min(360, width - viewX - buttonWidth - gap);
    nodes.push(
        label(
            'layoutTypeLabel',
            rect(0, 0, typeWidth, 18),
            tr('Search Type'),
            muted
        ),
        node('Choice', 'layoutSearchType', rect(0, 22, typeWidth, 38), {
            label: tr('Search Type'),
            value: model.searchType,
            options: model.searchTypes || [],
            enabled,
            action: { type: 'context', field: 'searchType' }
        }),
        label(
            'layoutViewLabel',
            rect(viewX, viewY, viewWidth, 18),
            tr('View') + (model.dirty ? ' · ' + tr('Unsaved changes') : ''),
            muted
        ),
        node('Choice', 'layoutView', rect(viewX, viewY + 22, viewWidth, 38), {
            label: tr('View'),
            value: model.view,
            options: views(model, language),
            enabled,
            action: { type: 'context', field: 'view' }
        }),
        button(
            'layoutNewView',
            rect(viewX + viewWidth + gap, viewY + 22, buttonWidth, 38),
            tr('New view'),
            'add',
            { type: 'startView' },
            enabled && model.ready
        )
    );
    let height = viewY + 72;
    if (ui.creating) {
        const formWidth = Math.min(width, 760),
            narrow = formWidth < 620;
        const nameWidth = narrow ? formWidth : (formWidth - 12) / 2;
        const templateX = narrow ? 0 : nameWidth + 12,
            templateY = narrow ? height + 62 : height;
        nodes.push(
            label(
                'layoutNewNameLabel',
                rect(0, height, nameWidth, 18),
                tr('View name'),
                muted
            ),
            node(
                'Field',
                'layoutNewName',
                rect(0, height + 22, nameWidth, 38),
                {
                    label: tr('View name'),
                    text: ui.newName,
                    enabled,
                    placeholder: 'my_view',
                    action: { type: 'newName' }
                }
            ),
            label(
                'layoutTemplateLabel',
                rect(templateX, templateY, nameWidth, 18),
                tr('Starting point'),
                muted
            ),
            node(
                'Choice',
                'layoutTemplate',
                rect(templateX, templateY + 22, nameWidth, 38),
                {
                    label: tr('Starting point'),
                    value: ui.template,
                    enabled,
                    options: [
                        { value: 'blank', label: tr('Blank view') },
                        { value: 'copy', label: tr('Copy current view') },
                        { value: 'continuous', label: tr('Continuous Tree') },
                        { value: 'cards', label: tr('Cards') },
                        { value: 'table', label: tr('Table View') }
                    ],
                    action: { type: 'template' }
                }
            ),
            button(
                'layoutCreateView',
                rect(0, templateY + 72, 164, 38),
                tr('Create draft'),
                'add',
                { type: 'newView' },
                enabled && !!ui.newName.trim()
            ),
            button(
                'layoutCancelNewView',
                rect(176, templateY + 72, 120, 38),
                tr('Cancel'),
                'close',
                { type: 'cancelView' },
                enabled
            )
        );
        height = templateY + 122;
    }
    return { nodes, height };
}

export function row(list, record, model) {
    return {
        nodes: [
            node(
                'Action',
                'layoutSavedView_' + record.value,
                rect(0, 0, list.width - 16, 34),
                {
                    text: record.label,
                    selected: model.view === record.value,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    enabled: !model.busy && !model.uncertain,
                    radius: 6,
                    children: [
                        label(
                            'layoutSavedViewTitle_' + record.value,
                            rect(10, 0, list.width - 36, 34),
                            record.label
                        )
                    ],
                    action: {
                        type: 'context',
                        field: 'view',
                        value: record.value
                    }
                }
            )
        ]
    };
}
