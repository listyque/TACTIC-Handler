// Executable neutral control examples for the component showcase.
import { node, rect, label, button } from '../core/frame.mjs';
import { translate } from '../core/strings.mjs';
import { textStyles, lineHeights } from '../core/foundation.mjs';
import { listAction } from './lists/tree.ui.mjs';
import { users, choices } from './catalog.ui.mjs';
import * as Chart from './charts/chart.ui.mjs';

export function describe(model, family, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const enabled = !['disabled', 'readonly'].includes(model.state);
    const text =
        model.state === 'long'
            ? 'A much longer component label / Длинное название компонента'
            : model.text;
    const flags = {
        enabled: model.state !== 'disabled',
        readOnly: model.state === 'readonly',
        error: model.state === 'error'
    };
    let y = 0,
        example = null;
    function add(item) {
        nodes.push(item);
        if (!example && !['Label', 'Box'].includes(item.kind)) example = item;
    }
    function caption(title) {
        add(
            label('sampleCaption_' + y, rect(0, y, width, 24), tr(title), {
                fontRole: 'section',
                weight: 600,
                role: 'heading',
                level: 3
            })
        );
        y += 32;
    }
    function field(kind, id, properties, height = 36) {
        add(
            node(kind, id, rect(0, y, Math.min(width, 440), height), properties)
        );
        y += height + 16;
    }
    if (family === 'typography') {
        const roles = [
            'headline',
            'hero',
            'heading',
            'title',
            'bodyLarge',
            'body',
            'secondary',
            'caption'
        ];
        for (const role of roles) {
            const h = Math.max(32, lineHeights[role] + 12);
            add(
                label(
                    'type_' + role,
                    rect(0, y, width, h),
                    role === 'caption' ? 'Caption · 0123456789' : text,
                    {
                        fontRole: role,
                        weight: ['headline', 'hero', 'title'].includes(role)
                            ? 600
                            : 400,
                        role: family === 'headers' ? 'heading' : undefined,
                        level: roles.indexOf(role) + 1
                    }
                )
            );
            y += h;
            add(
                label(
                    'typeToken_' + role,
                    rect(0, y, width, 18),
                    role +
                        ' · ' +
                        textStyles[role] +
                        ' px / ' +
                        lineHeights[role] +
                        ' px',
                    { fontRole: 'caption', color: 'secondaryText' }
                )
            );
            y += 32;
        }
        example = nodes[0];
    } else if (family === 'headers') {
        caption('Section heading');
        add(
            label('sampleHeading', rect(0, y, width, 36), text, {
                fontRole: 'hero',
                weight: 600,
                role: 'heading',
                level: 2
            })
        );
        y += 44;
        add(
            label('sampleSubtitle', rect(0, y, width, 28), tr('Description'), {
                color: 'secondaryText'
            })
        );
        y += 64;
        caption('Panel heading');
        add(
            node('Box', 'samplePanelHeader', rect(0, y, width, 72), {
                background: 'surfaceContainerLow',
                radius: 0,
                children: [
                    node('Icon', 'sampleHeadingIcon', rect(12, 18, 24, 24), {
                        icon: 'folder',
                        color: 'contentAccent'
                    }),
                    label(
                        'samplePanelTitle',
                        rect(48, 8, Math.max(0, width - 100), 28),
                        text,
                        {
                            fontRole: 'title',
                            weight: 600,
                            role: 'heading',
                            level: 3
                        }
                    ),
                    label(
                        'samplePanelSubtitle',
                        rect(48, 38, Math.max(0, width - 100), 20),
                        tr('Description'),
                        { fontRole: 'secondary', color: 'secondaryText' }
                    ),
                    button(
                        'sampleHeadingAction',
                        rect(Math.max(0, width - 44), 16, 36, 36),
                        tr('Refresh'),
                        'refresh',
                        { type: 'demo-header' },
                        enabled,
                        { iconOnly: true }
                    )
                ]
            })
        );
        y += 92;
        example = nodes.find((n) => n.id === 'sampleHeading');
    } else if (family === 'colors') {
        const roles = [
            'workspace',
            'panel',
            'surfaceContainerLowest',
            'surfaceContainerLow',
            'surfaceContainerHigh',
            'tableHeader',
            'contentSelection',
            'action',
            'green',
            'yellow',
            'error',
            'secondaryText'
        ];
        const columns = Math.max(1, Math.floor(width / 220)),
            cell = width / columns;
        roles.forEach((role, i) => {
            const x = (i % columns) * cell,
                top = Math.floor(i / columns) * 64;
            add(
                node('Box', 'color_' + role, rect(x, top, 40, 40), {
                    background: role,
                    radius: 6,
                    border: 'outlineVariant'
                })
            );
            add(
                label(
                    'colorName_' + role,
                    rect(x + 52, top, cell - 60, 40),
                    role,
                    { fontRole: 'secondary', wrap: true }
                )
            );
        });
        y = Math.ceil(roles.length / columns) * 64;
        example = nodes[0];
    } else if (family === 'buttons') {
        const w = Math.min(200, (width - 12) / 2);
        [
            ['Save', 'save', { highlighted: true }],
            ['Cancel', 'close', {}],
            ['Delete', 'delete', { destructive: true }],
            ['Help', 'help', {}]
        ].forEach(([title, icon, options], i) => {
            add(
                button(
                    'sampleButton_' + i,
                    rect((i % 2) * (w + 12), Math.floor(i / 2) * 52, w, 36),
                    tr(title),
                    icon,
                    { type: 'demo-' + title },
                    enabled,
                    options
                )
            );
        });
        y = 112;
        add(
            button(
                'sampleIconButton',
                rect(0, y, 36, 36),
                tr('Refresh'),
                'refresh',
                { type: 'demo-refresh' },
                enabled,
                { iconOnly: true }
            )
        );
        y += 52;
    } else if (family === 'toggles') {
        field('CheckBox', 'sampleCheckbox', {
            text: tr('Enabled'),
            checked: model.checked,
            enabled,
            action: { type: 'checked' }
        });
        field('CheckBox', 'sampleMixed', {
            text: tr('Selection'),
            checked: true,
            mixed: true,
            enabled,
            action: { type: 'checked' }
        });
        field('Switch', 'sampleSwitch', {
            text: tr('Notifications'),
            checked: model.checked,
            enabled,
            action: { type: 'checked' }
        });
    } else if (family === 'text-fields' || family === 'numbers') {
        caption(family === 'numbers' ? 'Number' : 'Name');
        field(
            'Field',
            'sampleField',
            Object.assign({}, flags, {
                text: family === 'numbers' ? model.number : text,
                label: tr('Name'),
                inputMode: family === 'numbers' ? 'decimal' : 'text',
                action: { type: family === 'numbers' ? 'number' : 'text' }
            })
        );
        if (family === 'text-fields') {
            caption('Description');
            field(
                'Area',
                'sampleArea',
                Object.assign({}, flags, {
                    text: model.area,
                    label: tr('Description'),
                    action: { type: 'area' }
                }),
                100
            );
        }
    } else if (family === 'choices') {
        caption('Process');
        field('Choice', 'sampleChoice', {
            value: model.choice,
            options: choices,
            label: tr('Process'),
            enabled,
            action: { type: 'choice' }
        });
    } else if (family === 'dates') {
        caption('Start date');
        field(
            'DateChoice',
            'sampleDate',
            Object.assign({}, flags, {
                text: model.date,
                language,
                label: tr('Start date'),
                action: { type: 'date' },
                commitAction: { type: 'date' }
            })
        );
    } else if (family === 'user-choice') {
        caption('Assigned to');
        field('UserChoice', 'sampleUser', {
            value: model.user,
            options: users,
            label: tr('Assigned to'),
            enabled,
            action: { type: 'user' }
        });
    } else if (family === 'pickers') {
        caption('Color');
        field('ColorChoice', 'sampleColor', {
            value: model.color,
            text: tr('Color'),
            enabled,
            action: { type: 'color' }
        });
        caption('Icon');
        field('IconChoice', 'sampleIcon', {
            value: model.icon,
            enabled,
            action: { type: 'icon' }
        });
    } else if (family === 'icons') {
        const icons = [
            'save',
            'refresh',
            'search',
            'help',
            'person',
            'groups',
            'calendar',
            'folder',
            'table',
            'note',
            'workflow',
            'extension'
        ];
        const columns = Math.max(1, Math.floor(width / 116)),
            cell = width / columns;
        icons.forEach((icon, i) => {
            const x = (i % columns) * cell,
                top = Math.floor(i / columns) * 92;
            add(
                node('Icon', 'sampleIcon_' + i, rect(x + 10, top, 28, 28), {
                    icon,
                    color: 'contentAccent'
                })
            );
            add(
                label(
                    'sampleIconName_' + i,
                    rect(x, top + 36, cell - 8, 28),
                    icon,
                    { fontRole: 'caption' }
                )
            );
        });
        y = Math.ceil(icons.length / columns) * 92;
    } else if (family === 'badges') {
        caption('Semantic colors');
        const colors = [
            'action',
            'cyan',
            'green',
            'yellow',
            'error',
            'secondaryText'
        ];
        const columns = Math.max(
                1,
                Math.min(4, Math.floor((width + 12) / 148))
            ),
            w = Math.min(140, (width - (columns - 1) * 12) / columns);
        colors.forEach((accent, i) =>
            add(
                node(
                    'StatusChip',
                    'sampleBadge_' + i,
                    rect(
                        (i % columns) * (w + 12),
                        y + Math.floor(i / columns) * 40,
                        w,
                        24
                    ),
                    {
                        text: model.state === 'long' ? text : accent,
                        accent,
                        enabled,
                        icon: i === 0 ? 'clipboard-check' : ''
                    }
                )
            )
        );
        y += Math.ceil(colors.length / columns) * 40 + 16;
        caption('Sizes and icons');
        add(
            node(
                'StatusChip',
                'sampleBadgeNormal',
                rect(0, y, Math.min(width, 140), 24),
                { text: tr('Ready'), accent: 'green', enabled }
            )
        );
        y += 40;
        add(
            node(
                'StatusChip',
                'sampleBadgeDense',
                rect(0, y, Math.min(width, 140), 20),
                {
                    text: tr('Ready'),
                    accent: 'green',
                    dense: true,
                    icon: 'clipboard-check',
                    enabled
                }
            )
        );
        y += 48;
        caption('Counters');
        for (const [i, count] of [0, 1, 125].entries()) {
            add(
                node(
                    'SummaryChip',
                    'sampleCounter_' + i,
                    rect(
                        (i % columns) * (w + 12),
                        y + Math.floor(i / columns) * 44,
                        w,
                        32
                    ),
                    {
                        text: tr('Notes'),
                        count,
                        icon: 'note',
                        accent: 'action',
                        enabled,
                        action: { type: 'demo-counter-' + count }
                    }
                )
            );
        }
        y += Math.ceil(3 / columns) * 44 + 16;
    } else if (family === 'tabs') {
        field('Segmented', 'sampleTabs', {
            label: tr('Display'),
            value: model.tab,
            enabled,
            options: [
                { value: 'overview', label: tr('Overview') },
                { value: 'details', label: tr('Details') },
                { value: 'activity', label: tr('Activity') }
            ],
            action: { type: 'tab' }
        });
        add(
            label('sampleTabValue', rect(0, y, width, 28), model.tab, {
                color: 'secondaryText'
            })
        );
        y += 40;
    } else if (family === 'lists') {
        caption('List');
        for (const [i, key] of ['assets', 'shots', 'tasks'].entries()) {
            const row = listAction(
                'sampleList_' + key,
                rect(0, y, width, 56),
                key[0].toUpperCase() + key.slice(1),
                ['box', 'film', 'clipboard-check'][i],
                { type: 'row', value: key },
                enabled,
                { selected: model.row === key, endInset: 64 }
            );
            row.children.push(
                node(
                    'StatusChip',
                    'sampleListCount_' + key,
                    rect(Math.max(0, width - 60), 16, 48, 24),
                    {
                        text: String([12, 8, 24][i]),
                        accent: 'secondaryText',
                        enabled: true
                    }
                )
            );
            add(row);
            y += 60;
        }
        y += 20;
        caption('Two-line list');
        for (const [i, title] of ['Model', 'Rig', 'Publish'].entries()) {
            const row = listAction(
                'sampleDetailRow_' + i,
                rect(0, y, width, 60),
                title,
                'clipboard-check',
                { type: 'row', value: title },
                enabled,
                { selected: model.row === title }
            );
            row.children.find((n) => n.kind === 'Label').height = 28;
            row.children.push(
                label(
                    'sampleDetailSubtitle_' + i,
                    rect(34, 30, Math.max(0, width - 46), 22),
                    tr('Description'),
                    { fontRole: 'secondary', color: 'secondaryText' }
                )
            );
            add(row);
            y += 64;
        }
    } else if (family === 'charts') {
        for (const type of ['line', 'bar', 'donut']) {
            caption(
                type === 'line'
                    ? 'Line chart'
                    : type === 'bar'
                      ? 'Bar chart'
                      : 'Donut chart'
            );
            const scene = Chart.describe(
                {
                    type,
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                    values: [4, 8, 5, 12, 9]
                },
                'sampleChart_' + type,
                width,
                220,
                language
            );
            add(
                node('Box', 'sampleChartBox_' + type, rect(0, y, width, 220), {
                    background: 'transparent',
                    clip: false,
                    children: scene.nodes
                })
            );
            y += 244;
        }
    }
    const properties = {};
    if (example)
        for (const key of Object.keys(example))
            if (
                ![
                    'kind',
                    'id',
                    'x',
                    'y',
                    'width',
                    'height',
                    'fontSize'
                ].includes(key)
            )
                if (key !== 'children' || example.children.length)
                    properties[key] = example[key];
    const code =
        family === 'charts'
            ? "import { describe } from './controls/charts/chart.ui.mjs';\n\ndescribe({ type: 'line', labels: ['Mon', 'Tue', 'Wed'], values: [4, 8, 5] },\n  'chart', 600, 220, 'en');"
            : example
              ? `import { node, rect } from './core/frame.mjs';\n\nnode(${JSON.stringify(example.kind)}, 'example',\n  rect(0, 0, ${Math.round(example.width)}, ${Math.round(example.height)}),\n  ${JSON.stringify(properties, null, 2)}\n);`
              : '';
    return { nodes, height: y, code };
}
