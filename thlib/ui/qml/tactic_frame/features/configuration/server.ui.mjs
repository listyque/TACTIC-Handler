import { translate } from '../../core/strings.mjs';

export function fields(model, language) {
    const text = (key) => translate(key, language),
        result = [];
    for (const [index, group] of (model.groups || []).entries()) {
        result.push({
            kind: 'Heading',
            id: 'serverGroup' + index,
            title: group.title
        });
        for (const setting of group.settings) {
            const key = setting.path;
            const definition = {
                id: 'serverSetting_' + key,
                field: key,
                title: setting.label,
                description: setting.description,
                readOnly: !setting.editable,
                props: { maxLength: 4096, error: model.errorField === key }
            };
            if (setting.restart)
                definition.description +=
                    '\n' + text('Restart required after changes');
            if (setting.input_type === 'services') {
                for (const [name, title] of [
                    ['queue', 'Background jobs'],
                    ['files', 'Bulk file transfers']
                ])
                    result.push(
                        Object.assign({}, definition, {
                            kind: 'Switch',
                            id: 'serverService_' + name,
                            field: key + '#' + name,
                            title,
                            enabled: setting.editable,
                            action: { type: 'service', path: key, name }
                        })
                    );
            } else if (setting.editable && setting.input_type === 'boolean')
                result.push(Object.assign({}, definition, { kind: 'Switch' }));
            else if (setting.editable && setting.choices)
                result.push(
                    Object.assign({}, definition, {
                        kind: 'Choice',
                        options: setting.choices
                    })
                );
            else
                result.push(
                    Object.assign({}, definition, {
                        kind: 'Field',
                        props: Object.assign({}, definition.props, {
                            password: !!setting.secret,
                            placeholder: setting.secret
                                ? text('Leave empty to keep the stored secret')
                                : String(setting.default ?? '')
                        })
                    })
                );
            if (setting.editable && setting.input_type === 'boolean')
                result.push({
                    kind: 'Button',
                    id: 'serverDefault_' + key,
                    title: 'Use default',
                    props: { icon: 'undo' },
                    enabled: model.draft[key] !== '',
                    action: { type: 'default', path: key }
                });
            if (setting.editable && setting.secret && setting.configured)
                result.push({
                    kind: 'Button',
                    id: 'serverClear_' + key,
                    title: 'Clear stored secret',
                    enabled: model.draft[key] !== '',
                    props: { icon: 'delete', destructive: true },
                    action: { type: 'clear', path: key }
                });
            if (model.showDetails) {
                result.push({
                    kind: 'Button',
                    id: 'serverDetails_' + key,
                    title: 'Details',
                    props: { icon: 'info' },
                    action: { type: 'details', path: key }
                });
                if (model.expanded?.includes(key)) {
                    const lines = [key];
                    if (setting.editable)
                        lines.push(
                            text('Saved value: {value}').replace(
                                '{value}',
                                setting.secret
                                    ? text(
                                          setting.configured
                                              ? 'Configured (hidden)'
                                              : 'Not set'
                                      )
                                    : String(setting.value ?? text('Not set'))
                            )
                        );
                    if (!setting.configured && setting.default !== null)
                        lines.push(
                            text('Default when empty: {value}').replace(
                                '{value}',
                                String(setting.default)
                            )
                        );
                    if (setting.environment_override)
                        lines.push(
                            text('Environment override: {value}').replace(
                                '{value}',
                                String(setting.environment_override)
                            )
                        );
                    if (setting.note) lines.push(text(setting.note));
                    if (setting.services)
                        for (const service of setting.services)
                            lines.push(
                                text(
                                    service.name === 'tactic'
                                        ? 'Web and API'
                                        : service.name === 'files'
                                          ? 'Bulk file transfers'
                                          : 'Background jobs'
                                ) +
                                    ' · ' +
                                    text(
                                        service.enabled ? 'Enabled' : 'Disabled'
                                    )
                            );
                    result.push({
                        kind: 'Area',
                        id: 'serverDetailsText_' + key,
                        field: 'details_' + key,
                        title: 'Details',
                        height: Math.max(80, lines.length * 20),
                        readOnly: true,
                        detailsText: lines.join('\n')
                    });
                }
            }
        }
    }
    return result;
}
