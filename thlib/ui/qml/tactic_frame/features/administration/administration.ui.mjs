import { spacing } from '../../core/foundation.mjs';
import { node } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Header from '../../controls/layout/page_header.ui.mjs';
export const sections = [
    {
        id: 'server',
        title: 'Backend server',
        description: 'Worker processes and server restart',
        icon: 'cloud',
        type: ''
    },
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
        id: 'dashboards',
        title: 'Page layouts',
        description: 'Whole pages linked from navigation',
        icon: 'table',
        type: 'config/widget_config'
    },
    {
        id: 'layouts',
        title: 'Item layouts',
        description: 'Object cards and reusable item views',
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
        id: 'plugins',
        title: 'Plugins',
        description: 'Packages, versions and project activation',
        icon: 'extension',
        type: 'config/plugin'
    },
    {
        id: 'showcase',
        title: 'Component showcase',
        description: 'Foundations, controls and interaction states',
        icon: 'view-grid',
        type: ''
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
export function geometry(width, height, collapsed) {
    const mobile = width < 1000,
        nav = mobile ? 0 : collapsed ? 56 : 250,
        body = width - nav,
        pad = spacing.content;
    const header = mobile ? 166 : Header.desktopHeight,
        toolbar = Math.max(0, Math.min(body - (mobile ? 24 : 434), 620));
    return {
        mobile,
        nav,
        body,
        pad,
        header,
        toolbar,
        compactHeight: sections.length * 48 - 8,
        compactWidth:
            nav - (height - 88 - 12 < sections.length * 48 - 8 ? 16 : 0),
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
        g = geometry(width, height, ui.collapsed),
        nodes = [],
        branding = [],
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
        const nav = [];
        branding.push(
            label(
                'administrationTitle',
                rect(20, 18, g.nav - 60, 24),
                'Administration',
                {
                    fontRole: 'heading',
                    weight: 600
                }
            ),
            label(
                'administrationBrand',
                rect(20, 48, g.nav - 28, 16),
                'TACTIC · ADMIN',
                {
                    fontRole: 'caption',
                    color: 'secondaryText'
                }
            )
        );
        if (ui.collapsed) branding.length = 0;
        branding.push(
            button(
                'adminToggleNavigation',
                rect(
                    ui.collapsed ? (g.compactWidth - 34) / 2 : g.nav - 46,
                    12,
                    34,
                    34
                ),
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
                    'View',
                    'administrationProjectPicker',
                    rect(12, 114, g.nav - 24, 38),
                    {
                        view: 'projectPicker'
                    }
                )
            );
        }
        const top = ui.collapsed ? 88 : 170;
        if (ui.collapsed) {
            const children = [];
            sections.forEach((record, index) => {
                const scene = row(
                    {
                        width: g.nav,
                        contentWidth: g.compactWidth,
                        rowHeight: 48
                    },
                    record,
                    model,
                    ui,
                    language
                );
                scene.nodes.forEach((item) => {
                    item.y += index * 48;
                    children.push(item);
                });
            });
            nav.push(
                node(
                    'Scroll',
                    'administrationNavigation',
                    rect(0, top, g.nav, height - top - 12),
                    {
                        contentHeight: g.compactHeight,
                        children,
                        scrollbarId: 'administrationNavigationScrollBar'
                    }
                )
            );
        } else
            nav.push(
                node(
                    'List',
                    'administrationNavigation',
                    rect(
                        ui.collapsed ? 0 : 8,
                        top,
                        g.nav - (ui.collapsed ? 0 : 16),
                        height - top - 12
                    ),
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
    const linked = !!model.layoutParent?.name;
    const head = [
        label(
            'administrationSectionTitle',
            rect(
                linked ? 58 : 12,
                11,
                g.mobile
                    ? g.body - (width > 700 ? 200 : 120) - (linked ? 46 : 0)
                    : Math.max(0, g.body - g.toolbar - 218 - (linked ? 46 : 0)),
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
            rect(12, 46, Math.max(0, g.body - 24), 22),
            ui.error && model.locked ? ui.error : current.description,
            {
                fontRole: 'secondary',
                color: ui.error && model.locked ? 'error' : 'secondaryText'
            }
        )
    ];
    if (linked)
        head.push(
            node('Button', 'adminReturnToLayout', rect(12, 11, 38, 38), {
                text:
                    tr(
                        model.layoutParent.kind === 'item'
                            ? 'Back to item layout'
                            : 'Back to page layout'
                    ) +
                    ': ' +
                    model.layoutParent.title,
                icon: 'arrow-back',
                iconOnly: true,
                action: { type: 'return-layout' },
                enabled: !model.busy
            })
        );
    head.push(
        node(
            'View',
            'administrationToolbar',
            rect(
                g.mobile ? 12 : g.body - g.toolbar - 174,
                g.mobile ? 116 : 10,
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
            rect(g.body - 88, g.mobile ? 10 : 12, 34, 34),
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
            rect(g.body - 48, g.mobile ? 10 : 12, 34, 34),
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
                'View',
                'administrationProjectPicker',
                rect(12, 70, half, 38),
                {
                    view: 'projectPicker'
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
    for (const item of head) item.x += g.nav;
    head.unshift(...branding);
    head.push(
        node(
            'Box',
            'administrationHeaderDivider',
            rect(0, g.header - 1, width, 1),
            { background: 'outlineVariant' }
        )
    );
    nodes.push(Header.describe('administrationHeader', width, g.header, head));
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
        available =
            compact && list.contentWidth !== undefined
                ? list.contentWidth
                : list.width - 16,
        w = compact ? 40 : available,
        h = list.rowHeight - (compact ? 8 : 4);
    const children = [
        node(
            'Icon',
            'adminSectionIcon_' + record.id,
            rect(compact ? (w - 22) / 2 : 12, (h - 22) / 2, 22, 22),
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
            node(
                'Action',
                'adminSection_' + record.id,
                rect(compact ? (available - w) / 2 : 0, 0, w, h),
                {
                    text: tr(record.title),
                    description: tr(record.description),
                    selected: model.section === record.id,
                    normalColor: 'transparent',
                    selectedColor: 'selected',
                    rail: !compact && model.section === record.id,
                    toolTip: compact ? tr(record.title) : '',
                    action: {
                        type: 'section',
                        value: record.id
                    },
                    children
                }
            )
        ]
    };
}
