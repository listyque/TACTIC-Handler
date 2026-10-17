import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const barHeight = 56;

export function describe(model, width, language) {
    const text = (key) => translate(key, language),
        compact = width < 560;
    const left = compact ? 12 : 196;
    const nodes = [
        node('Box', 'savedSearchBar', rect(0, 0, width, barHeight), {
            background: 'panelDeep'
        })
    ];
    if (!compact) {
        nodes.push(
            node('Icon', 'savedSearchIcon', rect(12, 19, 18, 18), {
                icon: 'save',
                color: 'action'
            })
        );
        nodes.push(
            label(
                'savedSearchLabel',
                rect(38, 10, 150, 36),
                text('Saved searches')
            )
        );
    }
    nodes.push(
        node(
            'Choice',
            'savedSearchChoice',
            rect(left, 10, Math.max(0, width - left - 134), 36),
            {
                label: text('Select a saved search'),
                value: model.selected || '',
                options: [
                    { value: '', label: text('Select a saved search') },
                    ...(model.presets || []).map((preset) => ({
                        value: preset.view,
                        label: preset.title,
                        dataLabel: true
                    }))
                ],
                enabled: !model.busy,
                action: { type: 'selectPreset' }
            }
        )
    );
    const selected = !!model.selected,
        canSave = model.canManage !== false && !model.busy && !model.uncertain;
    for (const [index, id, title, icon, enabled] of [
        [0, 'update', 'Update selected preset', 'save', selected && canSave],
        [1, 'new', 'Save as new preset', 'add', canSave],
        [2, 'more', 'Saved search actions', 'more-vert', !model.busy]
    ])
        nodes.push(
            button(
                'savedSearch_' + id,
                rect(width - 124 + index * 38, 10, 34, 36),
                text(title),
                icon,
                { type: id },
                enabled,
                {
                    iconOnly: true,
                    pressAction: id === 'more' ? { type: 'pressMore' } : null
                }
            )
        );
    return { nodes };
}

export function actions(model) {
    const editable =
        model.canManage !== false &&
        !!model.selected &&
        !model.busy &&
        !model.uncertain;
    return [
        { title: 'Saved search actions', header: true },
        {
            title: 'Rename preset',
            icon: 'rename',
            command: 'rename',
            enabled: editable
        },
        {
            title: 'Duplicate preset',
            icon: 'duplicate',
            command: 'duplicate',
            enabled: editable
        },
        {
            title: 'Copy saved search link',
            icon: 'link',
            command: 'copy_link',
            enabled: !!model.selected && !model.busy
        },
        {
            title: 'Delete preset',
            icon: 'delete',
            command: 'delete',
            enabled: editable
        },
        { separator: true },
        {
            title: 'Refresh saved searches',
            icon: 'refresh',
            command: 'refresh',
            enabled: !model.busy
        }
    ];
}
