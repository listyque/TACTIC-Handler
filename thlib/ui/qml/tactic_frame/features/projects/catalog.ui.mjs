import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { lifecycle } from '../../shell/projects.ui.mjs';

export const fields = ['projectCode', 'projectDetails'];

export function row(model, record, width, language) {
    const project = record.projectDetails,
        text = (key) => translate(key, language);
    const content = [
        node('Preview', 'configurationProjectPreview', rect(10, 10, 96, 96), {
            source: project.preview || '',
            fallbackText:
                project.initials || project.code.slice(0, 2).toUpperCase(),
            radius: 10
        }),
        label(
            'configurationProjectTitle',
            rect(118, 10, width - 132, 26),
            project.title || project.code,
            { fontRole: 'bodyLarge', weight: 600 }
        ),
        label(
            'configurationProjectCode',
            rect(118, 40, width - 132, 22),
            project.code,
            muted
        ),
        label(
            'configurationProjectCategory',
            rect(118, 66, width - 132, 20),
            project.category || text('No Category'),
            muted
        ),
        label(
            'configurationProjectLifecycle',
            rect(118, 90, width - 132, 18),
            text(lifecycle(project)),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    ];
    return {
        nodes: [
            node(
                'Action',
                'configurationProject_' + project.code,
                rect(0, 0, width, 116),
                {
                    text: project.title || project.code,
                    enabled: !model.busy,
                    selected: model.selected?.code === project.code,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    action: { type: 'select', record: project },
                    doubleAction: { type: 'activate', code: project.code },
                    children: content
                }
            )
        ]
    };
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 900,
        margin = 12;
    const selected = model.selected || {},
        actionsWidth = compact ? width - margin * 2 - 24 : 280;
    const catalogWidth = compact
        ? width - margin * 2 - 24
        : width - actionsWidth - margin * 2 - 14 - 48;
    const catalogX = margin + 12,
        catalogTop = compact ? 148 : margin,
        bottom = height - margin - (model.error ? 54 : 0),
        actionsX = compact ? margin + 12 : width - actionsWidth - margin - 12,
        actionsY = margin + 12;
    const nodes = [
        node(
            'Box',
            'configurationProjectsPanel',
            rect(margin, catalogTop, catalogWidth + 24, bottom - catalogTop),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 8
            }
        ),
        node(
            'Box',
            'configurationProjectDetailsPanel',
            rect(
                actionsX - 12,
                margin,
                actionsWidth + 24,
                compact ? 124 : bottom - margin
            ),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 8
            }
        ),
        node(
            'Box',
            'configurationProjectsHeaderDivider',
            rect(catalogX, catalogTop + 80, catalogWidth, 1),
            { background: 'outlineVariant' }
        ),
        node(
            'Box',
            'configurationProjectsFooterDivider',
            rect(catalogX, bottom - 40, catalogWidth, 1),
            { background: 'outlineVariant' }
        ),
        label(
            'configurationProjectsTitle',
            rect(catalogX, catalogTop + 12, catalogWidth, 24),
            text('Available projects'),
            { fontRole: 'bodyLarge', weight: 600, role: 'heading' }
        )
    ];
    let x = catalogX;
    for (const [key, title] of [
        ['retired', 'Retired'],
        ['templates', 'Templates'],
        ['builtins', 'Built-in']
    ]) {
        const fieldWidth = Math.max(85, Math.min(126, catalogWidth / 3));
        nodes.push(
            node(
                'CheckBox',
                'projectFilter_' + key,
                rect(x, catalogTop + 42, fieldWidth, 32),
                {
                    text:
                        text(title) +
                        (model.counts ? ' · ' + model.counts[key] : ''),
                    checked: !!model.filters?.[key],
                    enabled: !model.busy,
                    action: { type: 'filter', field: key }
                }
            )
        );
        x += fieldWidth;
    }
    const controls = [
        [
            'Activate selected project',
            'check',
            'activate',
            !!selected.code && selected.code !== model.currentCode
        ],
        [
            'Edit selected project',
            'edit',
            'edit',
            !!selected.code && !selected.isBuiltin && model.canManage
        ],
        [
            'Deactivate current project',
            'close',
            'deactivate',
            !!model.currentCode
        ],
        [
            'Create template archive',
            'download',
            'archive',
            !!selected.code && !selected.isBuiltin && model.canManage
        ],
        ['Create new project', 'add', 'create', model.canManage],
        ['Refresh projects', 'refresh', 'refresh', true]
    ];
    for (const [index, [title, icon, type, enabled]] of controls.entries()) {
        nodes.push(
            button(
                'configurationProjectAction_' + type,
                rect(
                    compact ? actionsX + index * 42 : actionsX,
                    compact ? actionsY + 46 : actionsY + 112 + index * 44,
                    compact ? 34 : actionsWidth,
                    36
                ),
                text(title),
                icon,
                { type, code: selected.code },
                enabled && !model.busy,
                { iconOnly: compact }
            )
        );
    }
    nodes.push(
        label(
            'configurationCurrentProject',
            rect(actionsX, actionsY, actionsWidth, 28),
            model.currentTitle || text('No active project'),
            { weight: 600, role: 'heading' }
        )
    );
    if (!compact) {
        nodes.push(
            label(
                'configurationSelectedProject',
                rect(actionsX, actionsY + 42, actionsWidth, 28),
                selected.title || text('Select a project'),
                { weight: 600 }
            )
        );
        nodes.push(
            label(
                'configurationSelectedCode',
                rect(actionsX, actionsY + 74, actionsWidth, 22),
                selected.code || '',
                muted
            )
        );
    }
    nodes.push(
        label(
            'configurationProjectsCount',
            rect(catalogX, bottom - 30, catalogWidth, 20),
            translate('{visible} of {total} projects shown', language, {
                visible: model.visibleCount || 0,
                total: model.totalCount || 0
            }),
            muted
        )
    );
    const top = catalogTop + 88;
    nodes.push(
        node(
            'List',
            'configurationProjects',
            rect(catalogX, top, catalogWidth, Math.max(0, bottom - 48 - top)),
            {
                source: 'projects',
                fields,
                keyField: 'projectCode',
                rowHeight: 120,
                rowGap: 4
            }
        )
    );
    if (model.error)
        nodes.push(
            label(
                'configurationProjectsError',
                rect(margin, height - 60, width - margin * 2, 48),
                model.error,
                { color: 'error', wrap: true }
            )
        );
    return { nodes };
}

export function visibleProjects(projects, filters) {
    return projects.filter((project) =>
        project.isBuiltin
            ? filters.builtins
            : project.isTemplate
              ? filters.templates
              : filters.retired || !project.isRetired
    );
}
