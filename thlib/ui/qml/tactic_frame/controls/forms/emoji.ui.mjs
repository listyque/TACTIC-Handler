import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const categorySpecs = [
    ['Smileys & Emotion', 'emoji'],
    ['People & Body', 'person'],
    ['Component', 'puzzle-piece'],
    ['Animals & Nature', 'paw'],
    ['Food & Drink', 'utensils'],
    ['Travel & Places', 'car'],
    ['Activities', 'futbol'],
    ['Objects', 'lightbulb'],
    ['Symbols', 'shapes'],
    ['Flags', 'flag']
];
// Surface bounds exclude the native popup's external shadow.
export function popup(screenWidth, screenHeight) {
    return {
        width: Math.max(0, Math.min(336, screenWidth - 16)),
        height: Math.max(0, Math.min(356, screenHeight - 20))
    };
}
export function layout(width, height, phone = false) {
    const columns = phone
            ? Math.max(1, Math.floor(Math.max(0, width - 12) / 44))
            : 8,
        cell = Math.floor(Math.max(0, width - 12) / columns);
    return {
        header: rect(0, 0, width, 76),
        grid: rect(0, 84, width, Math.max(0, height - 84)),
        columns,
        cell,
        fontSize: phone ? 32 : 26
    };
}
export function heading(model, width, language) {
    const tr = (text) => translate(text, language);
    return {
        height: 76,
        nodes: [
            node('Field', 'emojiPickerSearchField', rect(0, 0, width, 36), {
                label: tr('Find emoji'),
                placeholder: tr('Find emoji'),
                text: model.query || '',
                action: { type: 'query' },
                icon: 'search'
            }),
            node('Segmented', 'emojiCategorySwitcher', rect(0, 44, width, 32), {
                label: tr('Emoji categories'),
                options: categorySpecs.map(([value, icon]) => ({
                    value,
                    label: tr(value),
                    icon
                })),
                value: model.category || categorySpecs[0][0],
                iconOnly: true,
                action: { type: 'category' }
            })
        ]
    };
}
export function cell(model, size, phone = false) {
    return {
        width: size,
        height: size,
        fontSize: phone ? 32 : 26,
        text: model.emoji || model.value || '',
        label: model.emojiName || model.name || '',
        radius: 9
    };
}
export function empty(width, height, language) {
    return {
        nodes: [
            label(
                'emojiPickerEmpty',
                rect(0, Math.max(0, height / 2 - 10), width, 20),
                translate('No matching emoji', language),
                { fontRole: 'body', align: 'center', color: 'secondaryText' }
            )
        ]
    };
}
