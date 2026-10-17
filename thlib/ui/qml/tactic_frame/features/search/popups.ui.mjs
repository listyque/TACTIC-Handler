import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const popup = {
    width: 440,
    minimumWidth: 280,
    maximumHeight: 400,
    inset: 12,
    groupGap: 16,
    titleHeight: 24,
    optionGap: 9
};
export const tagHeaderHeight = 90;
export const quickHeaderHeight = 36;

export function tagHeader(model, width, language) {
    const text = (key) => translate(key, language);
    const nodes = [
        label(
            'tagsTitle',
            rect(0, 0, width - 84, 32),
            text(model.busy ? 'Loading tags…' : 'TAGS'),
            { weight: 600, fontRole: 'bodyLarge' }
        )
    ];
    if (model.selected)
        nodes.push(
            button(
                'resetSearchTagsButton',
                rect(width - 72, 0, 32, 32),
                text('Clear tags'),
                'close',
                { type: 'clearTags' },
                !model.disabled,
                { iconOnly: true }
            )
        );
    nodes.push(
        button(
            'reloadSearchTagsButton',
            rect(width - 34, 0, 32, 32),
            text('Reload tags'),
            'refresh',
            { type: 'reload' },
            !model.busy,
            { iconOnly: true }
        )
    );
    nodes.push(
        node('Icon', 'tagsSearchIcon', rect(0, 52, 18, 18), {
            icon: 'search',
            color: 'secondaryText'
        })
    );
    nodes.push(
        node(
            'Field',
            'tagCloudSearchField',
            rect(25, 42, width - 25 - (model.search ? 38 : 0), 38),
            {
                label: text('Search tags'),
                placeholder: text('Search tags'),
                text: model.search || '',
                inputType: 'search',
                action: { type: 'search' },
                keys: {
                    ArrowDown: { type: 'firstTag' },
                    Enter: { type: 'firstTag' }
                }
            }
        )
    );
    if (model.search)
        nodes.push(
            button(
                'clearTagSearchButton',
                rect(width - 32, 45, 32, 32),
                text('Clear search'),
                'close',
                { type: 'clearSearch' },
                true,
                { iconOnly: true }
            )
        );
    return { nodes };
}

export function quickHeader(model, width, language) {
    const text = (key) => translate(key, language),
        nodes = [];
    const editWidth = language === 'ru' ? 148 : 82,
        stacked = width < editWidth + 200,
        top = stacked ? 32 : 0;
    let right = width - editWidth;
    nodes.push(
        button(
            'editQuickFiltersButton',
            rect(right, top, editWidth, quickHeaderHeight),
            text('Edit'),
            'edit',
            { type: 'edit' },
            !model.busy && model.loaded,
            { tonal: true, keys: { Backtab: { type: 'lastGroup' } } }
        )
    );
    for (const [visible, id, title, icon, type] of [
        [
            model.count,
            'resetSearchQuickFiltersButton',
            'Clear quick filters',
            'close',
            'clear'
        ],
        [
            model.personalized,
            'restoreStandardQuickFiltersButton',
            'Apply the shared default to this tab',
            'reset',
            'reset'
        ]
    ]) {
        if (!visible) continue;
        right -= 36;
        nodes.push(
            button(
                id,
                rect(right, top + 4, 28, 28),
                text(title),
                icon,
                { type },
                !model.disabled,
                { iconOnly: true }
            )
        );
    }
    nodes.unshift(
        label(
            'quickFiltersTitle',
            rect(
                0,
                0,
                stacked ? width : right - 8,
                stacked ? 28 : quickHeaderHeight
            ),
            text('QUICK FILTERS'),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    return { nodes, contentHeight: top + quickHeaderHeight };
}

export function groupHeader(title, width) {
    return {
        nodes: [
            label(
                'quickFilterGroupTitle',
                rect(0, 0, width, popup.titleHeight),
                title,
                { fontRole: 'bodyLarge', weight: 600 }
            )
        ]
    };
}
