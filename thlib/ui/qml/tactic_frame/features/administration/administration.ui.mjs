import { node } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export const sections = [
    {
        id: 'types',
        title: 'Search Types',
        description: 'Entities and fields',
        icon: 'sobject',
        type: 'sthpw/search_object'
    },
    {
        id: 'schema',
        title: 'Project schema',
        description: 'Relationships between entities',
        icon: 'schema',
        type: 'sthpw/schema'
    },
    {
        id: 'workflow',
        title: 'Workflow',
        description: 'Processes, dependencies and scripts',
        icon: 'workflow',
        type: 'sthpw/pipeline'
    },
    {
        id: 'columns',
        title: 'Columns Editor',
        description: 'Table views and columns',
        icon: 'table',
        type: 'config/widget_config'
    },
    {
        id: 'raw',
        title: 'Raw database',
        description: 'Direct table editing and CSV export',
        icon: 'table',
        type: 'sthpw/project'
    },
    {
        id: 'layouts',
        title: 'Layout Editor',
        description: 'Custom views and SObject item layouts',
        icon: 'table',
        type: 'config/widget_config'
    },
    {
        id: 'sidebar',
        title: 'Sidebar Editor',
        description: 'Project navigation and sidebar items',
        icon: 'menu',
        type: 'config/widget_config',
        field: 'search_type',
        value: 'SideBarWdg'
    },
    {
        id: 'users',
        title: 'Users',
        description: 'Profiles and accounts',
        icon: 'person',
        type: 'sthpw/login'
    },
    {
        id: 'groups',
        title: 'Groups',
        description: 'Members and group management',
        icon: 'groups',
        type: 'sthpw/login_group'
    },
    {
        id: 'rules',
        title: 'Access rules',
        description: 'Projects, entities, processes and interface',
        icon: 'security',
        type: 'sthpw/login_group'
    }
];
const rect = (x, y, width, height) => ({
    x,
    y,
    width: Math.max(0, width),
    height: Math.max(0, height)
});
export function geometry(
    width,
    height,
    collapsed,
    workflow = false,
    navigationWidth = 250
) {
    const mobile = width < 1000,
        nav = mobile
            ? 0
            : collapsed
              ? 56
              : workflow
                ? Math.min(navigationWidth, width * 0.35)
                : 250,
        body = width - nav,
        pad = mobile ? 12 : 20;
    const header = mobile ? 166 : 76,
        toolbar = Math.max(
            0,
            Math.min(body - (mobile ? 24 : 120), width < 1080 ? 420 : 620)
        );
    return {
        mobile,
        nav,
        body,
        pad,
        header,
        toolbar,
        content: rect(
            nav + pad,
            header + pad,
            body - pad * 2,
            height - header - pad * 2
        )
    };
}
export function describe(model, ui, width, height, language) {
    const tr = (text) => translate(text, language),
        workflow = model.section === 'workflow',
        g = geometry(
            width,
            height,
            ui.collapsed,
            workflow,
            ui.workflowNavigationWidth
        ),
        nodes = [],
        current =
            sections.find((row) => row.id === model.section) || sections[0];
    const label = (id, r, text, props) =>
        node(
            'Label',
            id,
            r,
            Object.assign(
                {
                    text: tr(text)
                },
                props || {}
            )
        );
    const button = (id, r, text, icon, action, enabled) =>
        node('Button', id, r, {
            text: tr(text),
            icon,
            iconOnly: true,
            action,
            enabled: enabled !== false
        });
    nodes.push(
        node('Box', 'administrationBackground', rect(0, 0, width, height), {
            background: 'workspace'
        })
    );
    if (!g.mobile) {
        const nav = [
            label(
                'administrationTitle',
                rect(20, 15, g.nav - 60, 28),
                'Administration',
                {
                    fontRole: 'heading',
                    weight: 600
                }
            ),
            label(
                'administrationBrand',
                rect(20, 43, g.nav - 28, 20),
                'TACTIC · ADMIN',
                {
                    fontRole: 'caption',
                    color: 'secondaryText'
                }
            )
        ];
        if (ui.collapsed) nav.length = 0;
        nav.push(
            button(
                'adminToggleNavigation',
                rect(g.nav - 46, 19, 38, 38),
                ui.collapsed ? 'Expand navigation' : 'Collapse navigation',
                ui.collapsed ? 'chevron-right' : 'chevron-left',
                {
                    type: 'collapse'
                }
            )
        );
        if (!ui.collapsed) {
            nav.push(
                label(
                    'administrationProjectLabel',
                    rect(12, 88, g.nav - 24, 22),
                    'Project',
                    {
                        color: 'secondaryText'
                    }
                )
            );
            nav.push(
                node(
                    'Choice',
                    'administrationProjectSelector',
                    rect(12, 114, g.nav - 24, 38),
                    {
                        label: tr('Administration project'),
                        value: model.project,
                        options: model.projects || [],
                        enabled: !model.locked,
                        action: {
                            type: 'project'
                        }
                    }
                )
            );
        }
        const top = ui.collapsed ? 88 : 170;
        if (workflow && !ui.collapsed) {
            const columns = 3,
                cell = (g.nav - 24) / columns;
            for (const [index, section] of sections.entries()) {
                const bounds = rect(
                    8 + (index % columns) * cell,
                    top + Math.floor(index / columns) * 44,
                    cell - 4,
                    40
                );
                nav.push(
                    node('Action', 'adminSection_' + section.id, bounds, {
                        text: tr(section.title),
                        description: tr(section.description),
                        selected: model.section === section.id,
                        normalColor: 'transparent',
                        selectedColor: 'selected',
                        action: { type: 'section', value: section.id },
                        children: [
                            node(
                                'Icon',
                                'adminSectionIcon_' + section.id,
                                rect((bounds.width - 22) / 2, 9, 22, 22),
                                {
                                    icon: section.icon,
                                    color:
                                        model.section === section.id
                                            ? 'action'
                                            : 'secondaryText'
                                }
                            )
                        ]
                    })
                );
            }
            const catalogTop =
                top + Math.ceil(sections.length / columns) * 44 + 8;
            nav.push(
                node(
                    'View',
                    'administrationWorkflowLibrary',
                    rect(8, catalogTop, g.nav - 26, height - catalogTop - 12),
                    { view: 'workflowLibrary' }
                )
            );
            nav.push(
                node(
                    'Splitter',
                    'administrationNavigationSplit',
                    rect(g.nav - 10, 0, 10, height),
                    {
                        text: tr('Workflow list width'),
                        value: g.nav,
                        min: 180,
                        max: Math.min(420, width * 0.35),
                        action: { type: 'navigationSplit' }
                    }
                )
            );
        } else
            nav.push(
                node(
                    'List',
                    'administrationNavigation',
                    rect(8, top, g.nav - 16, height - top - 12),
                    {
                        source: 'sections',
                        keyField: 'id',
                        rowHeight: ui.collapsed ? 48 : 76,
                        scrollbarId: 'administrationNavigationScrollBar',
                        label: tr('Administration sections')
                    }
                )
            );
        nodes.push(
            node('Box', 'administrationSidebar', rect(0, 0, g.nav, height), {
                background: 'surfaceContainerLow',
                children: nav
            })
        );
    }
    const head = [
        label(
            'administrationSectionTitle',
            rect(
                20,
                10,
                g.mobile ? g.body - 120 : Math.max(0, g.body - g.toolbar - 148),
                28
            ),
            current.title,
            {
                fontRole: 'display',
                weight: 600
            }
        ),
        label(
            'administrationSectionDescription',
            rect(
                20,
                40,
                g.mobile ? g.body - 40 : Math.max(0, g.body - g.toolbar - 148),
                22
            ),
            ui.error && model.locked ? ui.error : current.description,
            {
                fontRole: 'secondary',
                color: ui.error && model.locked ? 'error' : 'secondaryText'
            }
        )
    ];
    head.push(
        node(
            'View',
            'administrationToolbar',
            rect(
                g.mobile ? 12 : g.body - g.toolbar - 104,
                g.mobile ? 116 : 19,
                g.toolbar,
                38
            ),
            {
                view: 'toolbar'
            }
        )
    );
    head.push(
        button(
            'administrationHelpButton',
            rect(g.body - 92, 10, 38, 38),
            'Help',
            'help',
            {
                type: 'help'
            }
        )
    );
    head.push(
        button(
            'administrationCloseButton',
            rect(g.body - 48, 10, 38, 38),
            'Close administration',
            'close',
            {
                type: 'close'
            },
            !model.busy
        )
    );
    if (g.mobile) {
        const half = (g.body - 32) / 2;
        head.push(
            node(
                'Choice',
                'administrationProjectSelector',
                rect(12, 70, half, 38),
                {
                    label: tr('Administration project'),
                    value: model.project,
                    options: model.projects || [],
                    enabled: !model.locked,
                    action: {
                        type: 'project'
                    }
                }
            )
        );
        head.push(
            node(
                'Choice',
                'administrationSectionSelector',
                rect(20 + half, 70, half, 38),
                {
                    label: tr('Administration section'),
                    value: model.section,
                    options: sections.map((row) => ({
                        value: row.id,
                        label: tr(row.title)
                    })),
                    action: {
                        type: 'section'
                    }
                }
            )
        );
    }
    nodes.push(
        node('Box', 'administrationHeader', rect(g.nav, 0, g.body, g.header), {
            background: 'surfaceContainerLow',
            children: head
        })
    );
    nodes.push(
        node('View', 'administrationContent', g.content, {
            view: 'content'
        })
    );
    return { nodes, geometry: g };
}
export function row(list, record, model, ui, language) {
    const tr = (text) => translate(text, language),
        compact = !!ui.collapsed,
        w = list.width - 16,
        h = list.rowHeight - 4;
    const children = [
        node(
            'Icon',
            'adminSectionIcon_' + record.id,
            rect(12, (h - 22) / 2, 22, 22),
            {
                icon: record.icon,
                color: record.id === model.section ? 'action' : 'secondaryText'
            }
        )
    ];
    if (!compact) {
        children.push(
            node(
                'Label',
                'adminSectionTitle_' + record.id,
                rect(46, 10, w - 58, 24),
                {
                    text: tr(record.title),
                    weight: 600
                }
            )
        );
        children.push(
            node(
                'Label',
                'adminSectionDescription_' + record.id,
                rect(46, 36, w - 58, 24),
                {
                    text: tr(record.description),
                    fontRole: 'secondary',
                    color: 'secondaryText'
                }
            )
        );
    }
    if ((model.drafts || []).indexOf(record.id) >= 0)
        children.push(
            node(
                'Icon',
                'adminSectionDraft_' + record.id,
                rect(w - 14, 6, 8, 8),
                {
                    icon: 'circle',
                    color: 'action'
                }
            )
        );
    return {
        nodes: [
            node('Action', 'adminSection_' + record.id, rect(0, 0, w, h), {
                text: tr(record.title),
                description: tr(record.description),
                selected: model.section === record.id,
                normalColor: 'transparent',
                selectedColor: 'selected',
                rail: true,
                action: {
                    type: 'section',
                    value: record.id
                },
                children
            })
        ]
    };
}
