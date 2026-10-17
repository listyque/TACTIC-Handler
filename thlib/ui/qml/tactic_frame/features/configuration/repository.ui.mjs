import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Settings from './settings.ui.mjs';

export const fields = [
    'alias',
    'title',
    'code',
    'active',
    'isDefault',
    'defaultEligible',
    'custom',
    'windowsPath',
    'linuxPath',
    'status',
    'statusText',
    'projectMapping'
];

export function row(model, record, width) {
    return {
        nodes: [
            node(
                'Action',
                'repository_' + record.alias,
                rect(0, 0, width, 54),
                {
                    text: record.title || record.alias,
                    enabled: !model.busy,
                    selected: model.selected === record.alias,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    action: { type: 'select', alias: record.alias },
                    children: [
                        node('Box', 'repositoryActive', rect(10, 23, 8, 8), {
                            radius: 4,
                            background: record.active
                                ? 'action'
                                : 'secondaryText'
                        }),
                        label(
                            'repositoryTitle',
                            rect(28, 5, width - 38, 24),
                            record.title || record.alias,
                            { weight: 600 }
                        ),
                        label(
                            'repositoryCode',
                            rect(28, 30, width - 38, 18),
                            record.code || record.alias,
                            muted
                        )
                    ]
                }
            )
        ]
    };
}

export function editorFields(model) {
    const record = model.record || {};
    const fields = [
        {
            kind: 'Heading',
            id: 'repositoryIdentity',
            title: record.title || 'Repository',
            dataLabel: !!record.title,
            description: model.native
                ? 'Paths are stored in the active server preset'
                : 'Paths are stored in the server configuration'
        },
        {
            kind: 'CheckBox',
            field: 'active',
            title: 'Enabled',
            enabled: model.editable !== false && record.alias !== 'plugins'
        },
        {
            kind: 'CheckBox',
            field: 'isDefault',
            title: 'Default',
            enabled: !!record.active && record.defaultEligible !== false
        },
        {
            kind: 'Field',
            field: 'title',
            title: 'Display name',
            props: { maxLength: 100 }
        }
    ];
    if (!model.native)
        fields.push(
            {
                kind: 'Field',
                field: 'serverPath',
                title: 'Server repository path',
                readOnly: record.alias === 'plugins'
            },
            { kind: 'Field', field: 'webPath', title: 'Repository web URL' }
        );
    fields.push(
        {
            kind: 'Field',
            field: 'windowsPath',
            title: model.native ? 'Windows path' : 'Windows client path'
        },
        {
            kind: 'Field',
            field: 'linuxPath',
            title: model.native ? 'Linux path' : 'Linux client path'
        }
    );
    if (model.native)
        fields.push({
            kind: 'Area',
            field: 'projectMapping',
            title: 'PROJECT MAPPING',
            height: 80,
            readOnly: true
        });
    else fields.push({ kind: 'ColorChoice', field: 'color', title: 'Color' });
    fields.push(
        {
            kind: 'Field',
            field: 'statusText',
            title: 'Path status',
            readOnly: true
        },
        {
            kind: 'Button',
            field: 'check',
            title: 'Check paths',
            props: { icon: 'check' },
            action: { type: 'check' }
        }
    );
    if (record.custom)
        fields.push({
            kind: 'Button',
            field: 'remove',
            title: 'Delete',
            description: 'Remove custom repository',
            props: { destructive: true, icon: 'delete' },
            action: { type: 'remove' }
        });
    if (!model.native)
        fields.push({
            kind: 'Button',
            field: 'advanced',
            title: 'Advanced settings',
            props: { icon: 'settings' },
            action: { type: 'advanced' }
        });
    return fields.map((field) =>
        Object.assign({}, field, {
            enabled:
                field.enabled !== false &&
                (model.editable !== false || field.action?.type === 'advanced')
        })
    );
}

export function editor(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 700,
        footerCompact = width < 560,
        margin = 16;
    const sidebar = compact ? width - 32 : Math.min(220, width * 0.34);
    const showCatalog = !compact || !model.editing;
    const showDetails = !compact || model.editing;
    const nodes = [
        label(
            'repositoryEditorTitle',
            rect(margin, 12, width - 180, 26),
            text('Repository Editor'),
            { fontRole: 'title', weight: 600, role: 'heading' }
        ),
        button(
            'repositoryEditorClose',
            rect(width - 48, 10, 32, 32),
            text('Close'),
            'close',
            { type: 'close' },
            !model.busy,
            { iconOnly: true }
        )
    ];
    if (showCatalog) {
        nodes.push(
            node(
                'Box',
                'repositoryCatalog',
                rect(margin, 52, sidebar, Math.max(0, height - 120)),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 12
                }
            )
        );
        nodes.push(
            label(
                'repositoryCatalogTitle',
                rect(margin + 12, 62, sidebar - 64, 28),
                text('REPOSITORIES'),
                muted
            )
        );
        nodes.push(
            button(
                'repositoryAdd',
                rect(margin + sidebar - 44, 60, 32, 32),
                text('Add custom repository'),
                'add',
                { type: 'add' },
                !model.busy && model.editable !== false,
                { iconOnly: true }
            )
        );
        nodes.push(
            node(
                'List',
                'repositoryCatalogRows',
                rect(margin + 8, 100, sidebar - 16, Math.max(0, height - 176)),
                {
                    source: 'repositories',
                    fields,
                    keyField: 'alias',
                    rowHeight: 58,
                    rowGap: 4
                }
            )
        );
    }
    if (showDetails) {
        const left = compact ? 0 : sidebar + margin + 12,
            top = compact ? 90 : 48;
        if (compact)
            nodes.push(
                button(
                    'repositoryBack',
                    rect(16, 50, 150, 34),
                    text('Repositories'),
                    'previous',
                    { type: 'back' },
                    true
                )
            );
        const body = Settings.describe(
            {
                fields: editorFields(model),
                values: model.record || {},
                busy: model.busy,
                error: model.error,
                notice: model.notice,
                style: model.style
            },
            width - left - margin,
            Math.max(0, height - top - 68),
            language
        );
        for (const child of body.nodes)
            nodes.push(
                Object.assign({}, child, {
                    x: child.x + left,
                    y: child.y + top
                })
            );
    }
    nodes.push(
        node('Box', 'repositoryFooter', rect(0, height - 62, width, 62), {
            background: 'surfaceContainerLow'
        })
    );
    nodes.push(
        button(
            'repositoryReset',
            rect(16, height - 48, footerCompact ? 36 : 120, 36),
            text('Reset'),
            'undo',
            { type: 'reset' },
            model.dirty && !model.busy,
            { iconOnly: footerCompact }
        )
    );
    if (model.teamLocal && !model.dirty)
        nodes.push(
            button(
                'repositorySync',
                rect(
                    width - (footerCompact ? 192 : 336),
                    height - 48,
                    footerCompact ? 36 : 180,
                    36
                ),
                text('Sync'),
                'refresh',
                { type: 'sync' },
                !model.busy,
                { iconOnly: footerCompact }
            )
        );
    nodes.push(
        button(
            'repositorySave',
            rect(width - 146, height - 48, 130, 36),
            text('Save'),
            'save',
            { type: 'save' },
            model.dirty && !model.busy,
            { highlighted: true }
        )
    );
    const header = nodes.splice(0, 2);
    nodes.unshift(
        node('Box', 'repositoryEditorHeader', rect(0, 0, width, 48), {
            titlebar: true,
            chromeRight: 48,
            background: 'surfaceContainerLow',
            radius: 0,
            children: header
        })
    );
    return { nodes };
}

export function summary(model, width, height, language) {
    const text = (key) => translate(key, language),
        fields = [
            {
                kind: 'Heading',
                id: 'repositoryStorage',
                title: 'Repository storage',
                description:
                    'Snapshots, previews, check-in, check-out and synchronization depend on a valid repository path.'
            },
            {
                kind: 'Field',
                field: 'currentPath',
                title:
                    model.currentTitle || 'Repository configuration is loading',
                dataLabel: !!model.currentTitle,
                readOnly: true
            },
            {
                kind: 'Button',
                field: 'edit',
                title: 'Open Repository Editor',
                props: { icon: 'database' },
                action: { type: 'edit' }
            },
            {
                kind: 'Button',
                field: 'check',
                title: model.busy ? 'Checking…' : 'Check paths',
                props: { icon: 'check' },
                action: { type: 'check' }
            },
            {
                kind: 'Heading',
                id: 'repositoryActive',
                title: 'Active repositories',
                description:
                    'The default repository is used when an operation does not choose another destination explicitly.'
            }
        ];
    for (const record of model.records || [])
        fields.push({
            kind: 'Field',
            field: 'repositoryPath_' + record.alias,
            title: record.title || record.alias,
            dataLabel: true,
            readOnly: true,
            description: [
                record.code || record.alias,
                record.isDefault ? text('Default') : '',
                text(record.active ? 'Enabled' : 'Disabled'),
                text(record.statusText || 'Not checked')
            ]
                .filter(Boolean)
                .join(' · ')
        });
    const values = { currentPath: model.currentPath || '' };
    for (const record of model.records || [])
        values['repositoryPath_' + record.alias] =
            record.path || record.windowsPath || record.linuxPath || '';
    return Settings.describe(
        {
            fields,
            values,
            error: model.error,
            notice: model.notice,
            busy: model.busy,
            style: model.style
        },
        width,
        height,
        language
    );
}
