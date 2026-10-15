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
        properties.options = (field.options || []).map((option) => ({
            value: option.value,
            label: option.label
        }));
    }
    return properties;
}
