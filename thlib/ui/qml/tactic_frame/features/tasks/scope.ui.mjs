import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { row as menuRow } from '../../controls/menus/action.ui.mjs';

export function actions(model, language) {
    const tr = (text) => translate(text, language);
    const entries = [
        ['selected', 'Selected', model.selectedIcon || 'inventory-2', 'object'],
        [
            'search_type',
            model.searchTypeTitle
                ? tr('All') + ' ' + model.searchTypeTitle
                : tr('Search Type'),
            'table-view',
            'search_type'
        ],
        ['project', 'Project tasks', 'workspaces', 'project'],
        ['team', 'Teams', 'groups', 'teams'],
        ['user', 'My tasks', 'person', 'my_tasks']
    ];
    return entries.map(([value, title, icon, command]) => ({
        value,
        title: value === 'search_type' ? title : tr(title),
        translate: false,
        icon,
        command,
        checked:
            model.scope === value &&
            (value !== 'user' || model.personal !== false),
        enabled:
            !model.blocked &&
            (value !== 'search_type' || model.searchTypeAvailable !== false)
    }));
}

export function describe(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let y = 0;
    for (const record of actions(model, language)) {
        nodes.push(
            node('Action', 'taskScope_' + record.value, rect(0, y, width, 32), {
                text: record.title,
                role: 'checkbox',
                checked: record.checked,
                enabled: record.enabled,
                radius: model.radius,
                action: { type: 'scope', value: record.value },
                children: menuRow(record, width, {
                    extent: 32,
                    radius: model.radius
                }).nodes
            })
        );
        y += 33;
    }
    const target = model.chooseTeam ? 'team' : model.scope;
    if (target === 'user' || target === 'team') {
        y += 8;
        nodes.push(
            label(
                'taskScopeIdentityTitle',
                rect(0, y, width, 16),
                tr(target === 'team' ? 'Team' : 'User'),
                {
                    fontRole: 'caption',
                    color: 'secondaryText'
                }
            )
        );
        y += 20;
        if (target === 'team' && !model.teams?.length) {
            nodes.push(
                label(
                    'taskScopeNoTeams',
                    rect(0, y, width, 48),
                    tr(
                        'No team scopes are available from your TACTIC login groups'
                    ),
                    {
                        fontRole: 'secondary',
                        color: 'secondaryText',
                        wrap: true
                    }
                )
            );
            return { nodes, height: y + 52 };
        }
        nodes.push(
            node(
                target === 'user' ? 'UserChoice' : 'Choice',
                'taskScopeIdentity',
                rect(0, y, width, 32),
                {
                    label: tr(target === 'team' ? 'Team' : 'User'),
                    value: target === model.scope ? model.identity || '' : '',
                    options:
                        target === 'team'
                            ? model.teams || []
                            : model.users || [],
                    enabled: !model.blocked,
                    action: { type: 'identity', scope: target }
                }
            )
        );
        y += 36;
    }
    return { nodes, height: y };
}
