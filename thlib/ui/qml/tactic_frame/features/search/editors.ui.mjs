import { spacing } from '../../core/foundation.mjs';
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const editor = {
    inset: spacing.content,
    gap: spacing.content,
    groupGap: spacing.compact,
    optionGap: spacing.compact
};

export function tabName(model, width, language) {
    const text = (key) => translate(key, language);
    return {
        nodes: [
            node('Box', 'searchTabNameSurface', rect(0, 0, width, 68), {
                background: 'surfaceContainerHigh',
                children: [
                    node('Icon', 'searchTabNameIcon', rect(14, 25, 18, 18), {
                        icon: 'tab',
                        color: 'action'
                    }),
                    label(
                        'searchTabNameLabel',
                        rect(44, 4, width - 56, 18),
                        text('Search tab name'),
                        { fontRole: 'secondary', color: 'secondaryText' }
                    ),
                    node(
                        'Field',
                        'searchTabNameField',
                        rect(44, 26, width - 56, 36),
                        {
                            label: text('Search tab name'),
                            text: model.title || '',
                            enabled: !model.busy,
                            action: { type: 'tabName' },
                            commitAction: { type: 'rename' },
                            maxLength: 256
                        }
                    )
                ]
            })
        ],
        contentHeight: 68
    };
}

export function selection(model, width, language) {
    const text = (key) => translate(key, language),
        compact = width < 620,
        nodes = [];
    nodes.push(
        label(
            'quickFilterSelectedTitle',
            rect(0, 0, width, 24),
            text('Selected filters'),
            { weight: 600 }
        )
    );
    if (!model.count)
        nodes.push(
            label(
                'quickFilterSelectedEmpty',
                rect(0, 28, width, 24),
                text('No filters selected'),
                { color: 'secondaryText' }
            )
        );
    if (model.count)
        nodes.push(
            node(
                'View',
                'selectedQuickFilterChips',
                rect(0, 28, width, model.chipHeight || 0),
                { view: 'chips' }
            )
        );
    let top = model.count ? 40 + (model.chipHeight || 0) : 60;
    if (model.canCopy !== false) {
        nodes.push(
            button(
                'useCurrentQuickFiltersAsStandardButton',
                rect(0, top, compact ? width : 300, 36),
                text('Copy selection from current tab'),
                'bookmark',
                { type: 'copy' },
                !model.busy && model.canEdit !== false,
                { tonal: true }
            )
        );
        if (compact) top += 44;
    }
    nodes.push(
        button(
            'clearQuickFilterSelection',
            rect(
                compact || model.canCopy === false ? 0 : 308,
                top,
                compact ? width : 220,
                36
            ),
            text('Clear selected filters'),
            'filter_alt_off',
            { type: 'clear' },
            !model.busy && model.canEdit !== false && model.count > 0
        )
    );
    return { nodes, contentHeight: top + 36 };
}

export function available(model, width, language) {
    const text = (key) => translate(key, language),
        compact = width < 500;
    return {
        nodes: [
            label(
                'quickFilterAvailableTitle',
                rect(0, 0, compact ? width : width - 250, 32),
                text('Available filters'),
                { weight: 600 }
            ),
            node(
                'CheckBox',
                'showHiddenQuickFilters',
                rect(
                    compact ? 0 : width - 246,
                    compact ? 32 : 0,
                    compact ? width : 246,
                    32
                ),
                {
                    text: text('Show hidden filters'),
                    checked: !!model.showHidden,
                    action: { type: 'showHidden' }
                }
            )
        ],
        contentHeight: compact ? 64 : 32
    };
}

export function group(model, width, language) {
    const text = (key) => translate(key, language),
        enabled = !model.busy && model.canEdit !== false;
    return {
        nodes: [
            node(
                'CheckBox',
                'quickFilterGroupToggle:' + model.key,
                rect(0, 0, width - 80, 36),
                {
                    text: model.title,
                    checked: !!model.enabled,
                    enabled,
                    action: { type: 'group', index: model.index }
                }
            ),
            button(
                'quickFilterGroupUp_' + model.index,
                rect(width - 76, 2, 32, 32),
                text('Move up'),
                'arrow_upward',
                { type: 'move', index: model.index, delta: -1 },
                enabled && model.index > 0,
                { iconOnly: true }
            ),
            button(
                'quickFilterGroupDown_' + model.index,
                rect(width - 36, 2, 32, 32),
                text('Move down'),
                'arrow_downward',
                { type: 'move', index: model.index, delta: 1 },
                enabled && model.index < model.total - 1,
                { iconOnly: true }
            )
        ],
        contentHeight: 36
    };
}

export function footer(model, width, language) {
    const text = (key) => translate(key, language),
        compact = width < 720,
        nodes = [],
        enabled =
            !model.busy &&
            !model.uncertain &&
            model.loaded !== false &&
            model.canEdit !== false;
    const rows = [
        ['cancelQuickFilterEditorButton', 'Cancel', 'close', 'close', true],
        [
            'saveQuickFilterDefaultsButton',
            'Save as defaults on server',
            'cloud_upload',
            'defaults',
            model.canSaveDefaults
        ],
        [
            'saveQuickFilterEditorButton',
            'Save for this tab',
            'save',
            'save',
            true
        ]
    ];
    let right = width,
        top = 0;
    for (const [id, title, icon, type, visible] of rows) {
        if (!visible) {
            nodes.push(
                button(
                    id,
                    rect(0, 0, 0, 0),
                    text(title),
                    icon,
                    { type },
                    false,
                    { visible: false }
                )
            );
            continue;
        }
        const size = compact
            ? width
            : type === 'defaults'
              ? language === 'ru'
                  ? 306
                  : 246
              : type === 'save'
                ? language === 'ru'
                    ? 240
                    : 174
                : 102;
        if (!compact) right -= size;
        nodes.push(
            button(
                id,
                rect(compact ? 0 : right, top, size, 36),
                text(title),
                icon,
                { type },
                type === 'close' ? !model.busy : enabled,
                { highlighted: type === 'save' }
            )
        );
        if (compact) top += 44;
        else right -= 8;
    }
    return { nodes, contentHeight: compact ? top - 8 : 36 };
}

export function presetName(model, width, language) {
    const text = (key) => translate(key, language),
        enabled = !model.busy && !model.uncertain;
    return {
        nodes: [
            label(
                'presetNameLabel',
                rect(0, 0, width, 24),
                text('Preset name')
            ),
            node('Field', 'presetNameField', rect(0, 28, width, 36), {
                label: text('Preset name'),
                placeholder: text('Preset name'),
                text: model.title || '',
                maxLength: 256,
                selectOnFocus: true,
                enabled,
                action: { type: 'title' },
                keys: { Enter: { type: 'save' } }
            }),
            button(
                'presetNameSave',
                rect(Math.max(0, width - 210), 80, 100, 36),
                text('Save'),
                'save',
                { type: 'save' },
                enabled && !!String(model.title || '').trim(),
                { highlighted: true }
            ),
            button(
                'presetNameCancel',
                rect(Math.max(0, width - 102), 80, 102, 36),
                text('Cancel'),
                'close',
                { type: 'close' },
                !model.busy
            )
        ],
        contentHeight: 116
    };
}
