import { translate } from '../../core/strings.mjs';

export function fieldProperties(field, language, enabled) {
    const title = field.dataLabel
        ? field.title
        : translate(field.title, language);
    const properties = Object.assign(
        {
            label: title,
            enabled,
            action: field.field ? { type: 'field', field: field.field } : null
        },
        field.props || {}
    );

    if (['Button', 'CheckBox', 'Switch'].indexOf(field.kind) >= 0)
        properties.text = title;
    if (field.kind === 'Choice' || field.kind === 'ChoiceGrid') {
        properties.options = (field.options || []).map((option) => {
            const item = {
                value: option.value,
                label: option.label
            };
            if (option.icon) item.icon = option.icon;
            if (option.color) item.color = option.color;
            if (option.description) item.description = option.description;
            return item;
        });
    }
    return properties;
}
