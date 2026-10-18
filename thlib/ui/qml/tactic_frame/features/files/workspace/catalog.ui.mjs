import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { actionLayout } from '../../../controls/buttons/metrics.mjs';

export function workspaceActions(model, language) {
    const tr = (text) => translate(text, language);
    return [
        {
            id: 'workspaceCatalogSwitch',
            text: tr('Switch workspace'),
            icon: 'desktop',
            type: 'switch',
            enabled: !!model.selected?.code && !model.busy
        },
        {
            id: 'workspaceCatalogEdit',
            text: tr('Edit workspace'),
            icon: 'edit',
            type: 'edit',
            enabled:
                !!model.selected?.code &&
                model.selected.code === model.workspace &&
                !model.busy
        },
        {
            id: 'workspaceCatalogSetup',
            text: tr('Workspace setup'),
            icon: 'add',
            type: 'setup',
            enabled: !model.busy
        }
    ];
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 600;
    const actions = workspaceActions(model, language),
        buttons = actionLayout(
            actions,
            Math.max(0, width - 16),
            model.buttonWidths || []
        );
    const footer =
        model.native && model.source === 'workspaces' ? buttons.height + 4 : 0;
    const available = Math.max(
        0,
        (narrow ? height - 104 - footer : width - 16) - 10
    );
    const extent = Math.max(
        0,
        Math.min(available, model.extent ?? available * (narrow ? 0.6 : 0.55))
    );
    const body = Math.max(0, height - 60 - footer);
    const list = rect(
        8,
        52,
        narrow ? width - 16 : extent,
        narrow ? extent : body
    );
    const detail = rect(
        narrow ? 8 : 18 + extent,
        narrow ? 62 + extent : 52,
        narrow ? width - 16 : width - 26 - extent,
        narrow ? body - extent - 10 : body
    );
    const nodes = [
        label(
            'workspaceCatalogTitle',
            rect(8, 8, Math.max(0, width - 88), 36),
            tr('Server metadata')
        ),
        button(
            'workspaceCatalogRefresh',
            rect(Math.max(8, width - 76), 12, 28, 28),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true, iconAction: true }
        ),
        button(
            'workspaceCatalogMore',
            rect(Math.max(40, width - 40), 12, 28, 28),
            tr('Next page'),
            'chevron-right',
            { type: 'more' },
            !model.busy,
            { iconOnly: true, iconAction: true, visible: !!model.after }
        ),
        node('List', 'workspaceCatalogList', list, {
            source: 'catalog',
            keyField: 'id',
            fields: ['id', 'node'],
            rowHeight: 62,
            rowGap: 4,
            label: tr('Server metadata'),
            scrollbarId: 'workspaceCatalogScrollBar'
        }),
        node(
            'Splitter',
            'workspaceCatalogSplitter',
            rect(
                narrow ? 8 : extent + 8,
                narrow ? extent + 52 : 52,
                narrow ? width - 16 : 10,
                narrow ? 10 : body
            ),
            {
                horizontal: narrow,
                value: extent,
                min: 0,
                max: available,
                text: tr('Server metadata'),
                action: { type: 'split' }
            }
        ),
        node('Area', 'workspaceCatalogRecord', detail, {
            text: JSON.stringify(model.selected || {}, null, 2),
            readOnly: true,
            label: tr('Selected server record')
        })
    ];
    if (!model.count)
        nodes.push(
            label(
                'workspaceCatalogEmpty',
                rect(list.x, list.y, list.width, Math.min(80, list.height)),
                tr('No permitted records on this page'),
                { wrap: true, color: 'secondaryText' }
            )
        );
    if (footer) {
        // Native local workspace operations stay outside browser inspection.
        for (const [index, action] of actions.entries())
            nodes.push(
                button(
                    action.id,
                    rect(
                        8 + buttons.positions[index].x,
                        height - footer + buttons.positions[index].y,
                        buttons.positions[index].width,
                        buttons.positions[index].height
                    ),
                    action.text,
                    action.icon,
                    { type: action.type },
                    action.enabled
                )
            );
    }
    return { nodes };
}

export function row(model, record, width, language) {
    const tr = (text) => translate(text, language),
        data = record.node;
    const subtitle = [
        data.depot,
        data.stream,
        data.owner,
        data.local_root,
        data.parent
            ? tr('Parent: {parent}').replace('{parent}', data.parent)
            : ''
    ]
        .filter(Boolean)
        .join(' · ');
    return {
        nodes: [
            node(
                'Action',
                'workspaceCatalog_' + record.id,
                rect(0, 0, width, 58),
                {
                    text: data.code,
                    role: 'option',
                    selected: model.selected?.code === data.code,
                    selectedColor: 'selected',
                    normalColor: 'transparent',
                    action: { type: 'select', key: record.id },
                    children: [
                        node(
                            'Icon',
                            'workspaceCatalogIcon',
                            rect(10, 20, 18, 18),
                            {
                                icon:
                                    model.source === 'workspaces'
                                        ? 'desktop'
                                        : 'source-branch',
                                color: 'action'
                            }
                        ),
                        label(
                            'workspaceCatalogCode',
                            rect(36, 4, Math.max(0, width - 44), 24),
                            data.code,
                            { elideMiddle: true }
                        ),
                        label(
                            'workspaceCatalogSubtitle',
                            rect(36, 30, Math.max(0, width - 44), 20),
                            subtitle,
                            { fontRole: 'secondary', color: 'secondaryText' }
                        )
                    ]
                }
            )
        ]
    };
}
