import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { describe as confirm } from '../../controls/feedback/confirmation.ui.mjs';

export function confirmation(model, width, height, language) {
    const text = (key) => translate(key, language);
    if (model.kind === 'clear')
        return confirm(
            {
                message: text(
                    model.scope === 'tabs'
                        ? 'Object, process and version branches will collapse. Search tabs, filters and dock layouts remain unchanged.'
                        : 'Projects, Search Types, search results and navigation will be downloaded again. Saved layouts and preferences remain unchanged.'
                ),
                reject: 'Cancel',
                accept:
                    model.scope === 'tabs' ? 'Clear tabs cache' : 'Clear cache',
                destructive: true,
                busy: model.busy,
                acceptId: 'configurationClearAccept',
                rejectId: 'configurationClearCancel'
            },
            width,
            height,
            language
        );
    const nodes = [
        label(
            'configurationDiscardMessage',
            rect(16, 12, width - 32, 84),
            text('Save changes before closing Configuration?'),
            { wrap: true }
        )
    ];
    for (const [index, action] of [
        ['Continue editing', 'keep'],
        ['Discard changes', 'discard'],
        ['Save', 'save']
    ].entries())
        nodes.push(
            button(
                'configurationConfirm_' + action[1],
                rect(16, height - 132 + index * 44, width - 32, 36),
                text(action[0]),
                '',
                { type: action[1] },
                !model.busy,
                {
                    destructive: action[1] === 'discard',
                    highlighted: action[1] === 'save'
                }
            )
        );
    return { nodes };
}

export const pages = [
    {
        id: 'server',
        title: 'Server',
        icon: 'cloud',
        description: 'Connection, sign-in status and server presets',
        help: 'server_configuration'
    },
    {
        id: 'repository',
        title: 'Repositories',
        icon: 'database',
        description: 'Repository locations, availability and default storage',
        help: 'repository_configuration'
    },
    {
        id: 'project',
        title: 'Projects',
        icon: 'project-diagram',
        description: 'Active project and workspace context',
        help: 'configuration.projects'
    },
    {
        id: 'checkin',
        nativeId: 'checkin_preferences',
        title: 'Check-in Options',
        icon: 'tune',
        description: 'Naming and file handling defaults',
        help: 'configuration.checkin'
    },
    {
        id: 'global',
        nativeId: 'global_preferences',
        title: 'Global',
        icon: 'settings',
        description: 'Application behavior and diagnostics',
        help: 'configuration.global'
    },
    {
        id: 'appearance',
        title: 'Appearance',
        icon: 'palette',
        description: 'Themes, animations, language and rendering',
        help: 'appearance'
    },
    {
        id: 'cache',
        title: 'Cache',
        icon: 'cached',
        description: 'Persistent server data and cache policy',
        help: 'configuration.cache'
    },
    {
        id: 'tasks',
        nativeId: 'tasks_preferences',
        title: 'Tasks',
        icon: 'briefcase',
        description: 'Task Browser layout and Notes inspector defaults',
        help: 'configuration.tasks'
    }
];

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language);
    const entries = model.pages || pages;
    const current =
        entries.find((page) => page.id === model.page) || entries[0];
    const phone = width < 560,
        compact = width < 960;
    const sidebar = phone ? 0 : 216,
        header = phone ? 116 : 77;
    const contentWidth = Math.max(0, width - sidebar);
    const nodes = [
        node('Box', 'configurationSurface', rect(0, 0, width, height), {
            background: 'workspace'
        }),
        node('Box', 'configurationHeader', rect(0, 0, width, header), {
            background: 'surfaceContainerLow'
        })
    ];
    if (!phone) {
        nodes.push(
            node('Box', 'configurationSidebar', rect(0, 0, sidebar, height), {
                background: 'surfaceContainerLow'
            }),
            label(
                'configurationTitle',
                rect(20, 18, sidebar - 36, 24),
                text(model.title || 'Configuration'),
                { fontRole: 'heading', weight: 600, role: 'heading' }
            ),
            label(
                'configurationProduct',
                rect(20, 48, sidebar - 32, 16),
                model.product + ' · ' + text('Preferences'),
                Object.assign({}, muted, { fontRole: 'caption' })
            )
        );
        const navigation = entries.map((entry, index) =>
            node(
                'Action',
                'configurationPage_' + (entry.nativeId || entry.id),
                rect(8, index * 52, sidebar - 28, 48),
                {
                    text: text(entry.title),
                    selected: entry.id === model.page,
                    enabled: entry.enabled !== false,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    action: { type: 'page', value: entry.id },
                    children: [
                        node(
                            'Icon',
                            'configurationIcon_' + entry.id,
                            rect(16, 14, 20, 20),
                            {
                                icon: entry.icon,
                                color:
                                    entry.id === model.page
                                        ? 'action'
                                        : 'secondaryText'
                            }
                        ),
                        label(
                            'configurationLabel_' + entry.id,
                            rect(48, 0, sidebar - 92, 48),
                            text(entry.title)
                        ),
                        ...(model.dirtyPages?.includes(entry.id)
                            ? [
                                  node(
                                      'Box',
                                      'configurationDirty_' + entry.id,
                                      rect(sidebar - 34, 21, 6, 6),
                                      { background: 'action', radius: 3 }
                                  )
                              ]
                            : [])
                    ]
                }
            )
        );
        nodes.push(
            node(
                'Scroll',
                'configurationNavigation',
                rect(
                    0,
                    header + 12,
                    sidebar,
                    Math.max(0, height - header - 12)
                ),
                {
                    contentHeight: entries.length * 52 + 12,
                    scrollbarId: 'configurationNavigationScrollBar',
                    children: navigation
                }
            )
        );
    } else
        nodes.push(
            node(
                'Choice',
                'configurationPageChoice',
                rect(14, 62, width - 28, 38),
                {
                    label: text('Configuration sections'),
                    enabled: true,
                    value: model.page,
                    options: entries.map((entry) => ({
                        value: entry.id,
                        label: text(entry.title)
                    })),
                    action: { type: 'page' }
                }
            )
        );
    const actions = model.actions || [
        ['Reset', 'undo', 'reset', model.canReset && model.currentDirty],
        ['Apply', 'check', 'apply', model.currentDirty],
        ['Save', 'save', 'save', model.dirty],
        ['Configuration help', 'help', 'help', true],
        ['Close', 'close', 'close', true]
    ];
    let actionX = width - 14;
    const actionNodes = [];
    for (let index = actions.length - 1; index >= 0; index--) {
        if (index === 2 && width > 700) actionX -= 80;
        const [title, icon, type, enabled] = actions[index];
        const iconOnly = compact || ['help', 'close'].includes(type),
            actionWidth = iconOnly ? 34 : 130;
        actionX -= actionWidth;
        actionNodes.push(
            button(
                'configuration' + type[0].toUpperCase() + type.slice(1),
                rect(actionX, 12, actionWidth, 34),
                text(title),
                icon,
                { type },
                enabled && !model.busy,
                { iconOnly, highlighted: type === 'save' }
            )
        );
        actionX -= 6;
    }
    nodes.push(...actionNodes.reverse());
    if (actions.length <= 2 && width > 700) actionX -= 80;
    nodes.push(
        label(
            'configurationPageTitle',
            rect(sidebar + 24, 11, Math.max(0, actionX - sidebar - 30), 28),
            text(current.title),
            { fontRole: 'display', weight: 600, role: 'heading' }
        )
    );
    if (!phone)
        nodes.push(
            label(
                'configurationPageDescription',
                rect(sidebar + 24, 46, contentWidth - 48, 20),
                text(current.description),
                muted
            )
        );
    nodes.push(
        node(
            'Box',
            'configurationHeaderDivider',
            rect(0, header - 1, width, 1),
            { background: 'outlineVariant' }
        )
    );
    const headerNodes = nodes.filter(
        (item) =>
            item.id !== 'configurationSurface' &&
            item.id !== 'configurationSidebar' &&
            item.id !== 'configurationHeader' &&
            item.y < header
    );
    const headerBox = nodes.find((item) => item.id === 'configurationHeader');
    headerBox.titlebar = true;
    headerBox.radius = 0;
    headerBox.chromeRight = 86;
    headerBox.children = headerNodes;
    const contentNodes = nodes.filter(
        (item) => item !== headerBox && !headerNodes.includes(item)
    );
    for (const item of contentNodes)
        if (['configurationSurface', 'configurationSidebar'].includes(item.id))
            item.radius = 0;
    const sidebarBox = contentNodes.findIndex(
        (item) => item.id === 'configurationSidebar'
    );
    contentNodes.splice(sidebarBox >= 0 ? sidebarBox + 1 : 1, 0, headerBox);
    return {
        nodes: contentNodes,
        pageBounds: rect(
            sidebar,
            header,
            contentWidth,
            Math.max(0, height - header)
        )
    };
}
