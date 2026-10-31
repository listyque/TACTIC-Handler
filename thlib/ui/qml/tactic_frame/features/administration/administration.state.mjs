import { sections } from './administration.ui.mjs';
export function initial() {
    return {
        collapsed: false,
        error: ''
    };
}
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [];
    switch (event.type) {
        case 'collapse':
            next.collapsed = !next.collapsed;
            break;
        case 'section':
            if (sections.some((row) => row.id === event.value))
                commands.push(event);
            break;
        case 'project':
            if (
                !model.locked &&
                (model.projects || []).some((row) => row.value === event.value)
            )
                commands.push(event);
            break;
        case 'help':
            commands.push({
                type: 'help',
                topic:
                    model.section === 'showcase'
                        ? 'frame_showcase'
                        : model.section === 'plugins'
                          ? 'plugins'
                          : ['layouts', 'dashboards'].includes(model.section)
                            ? 'item_layouts'
                            : model.section === 'sidebar'
                              ? 'sidebar_editor'
                              : 'administration'
            });
            break;
        case 'return-layout':
            if (model.layoutParent?.name && !model.busy) commands.push(event);
            break;
        case 'close':
            if (model.locked) {
                next.error = 'Save or discard changes before continuing';
                if ((model.drafts || []).length)
                    commands.push({
                        type: 'section',
                        value: model.drafts[0]
                    });
            } else if (!model.busy) {
                next.error = '';
                commands.push(event);
            }
            break;
        default:
            throw Error('Unsupported Administration event: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}
