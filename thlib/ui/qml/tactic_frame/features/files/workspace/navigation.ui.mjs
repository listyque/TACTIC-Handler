import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { metrics } from '../../../core/foundation.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function describe(model, width, language) {
    const tr = (text) => translate(text, language),
        compact = width < 240,
        h = metrics(model.style).controlHeight,
        children = [];
    const actionsWidth = compact
            ? h
            : Math.min((width - 4) / 2, model.actionWidths?.[0] || 96),
        toolsWidth = compact
            ? h
            : Math.min((width - 4) / 2, model.actionWidths?.[1] || 96);
    children.push(
        button(
            'workspaceNavigationActions',
            rect(0, 0, actionsWidth, h),
            tr('Actions'),
            'play-arrow',
            { type: 'menu', kind: 'actions' },
            true,
            { iconOnly: compact }
        )
    );
    children.push(
        button(
            'workspaceNavigationTools',
            rect(actionsWidth + 4, 0, toolsWidth, h),
            tr('Tools'),
            'settings',
            { type: 'menu', kind: 'tools' },
            true,
            { iconOnly: compact }
        )
    );
    let y = h + 4;
    children.push(
        node('Choice', 'fileWorkspaceSelector', rect(0, y, width, h), {
            label: tr('Workspace'),
            options: (model.workspaces || []).map((row) => ({
                value: row.code,
                label: row.code
            })),
            value: model.workspace || '',
            enabled: !model.busy,
            action: { type: 'workspace' }
        })
    );
    y += h + 4;
    const iconWidth = Math.min(28, Math.max(0, (width - 40) / 3));
    for (const [index, [id, title, icon, type, enabled]] of [
        [
            'workspaceNavigationBack',
            'Back',
            'chevron-left',
            'back',
            model.navigationIndex > 0
        ],
        [
            'workspaceNavigationForward',
            'Forward',
            'chevron-right',
            'forward',
            model.navigationIndex + 1 < model.navigationCount
        ],
        [
            'workspaceNavigationParent',
            'Parent folder',
            'folder-open',
            'parent',
            true
        ]
    ].entries())
        children.push(
            button(
                id,
                rect(index * (iconWidth + 2), y + (h - 28) / 2, iconWidth, 28),
                tr(title),
                icon,
                { type },
                enabled,
                { iconOnly: true, iconAction: true }
            )
        );
    const pathX = 3 * (iconWidth + 2);
    children.push(
        node(
            'Field',
            'workspaceNavigationPath',
            rect(pathX, y, Math.max(0, width - pathX), h),
            {
                label: tr('Workspace or depot path'),
                text: model.path || '',
                action: { type: 'path' },
                activateAction: { type: 'navigate' }
            }
        )
    );
    y += h + 4;
    if (model.recovery) {
        children.push(
            button(
                'workspaceResumeOperation',
                rect(0, y, 28, 28),
                tr('Resume interrupted operation'),
                'restore',
                { type: 'resume' },
                !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
        y += 32;
    }
    if (['offline', 'recovery_available'].includes(model.connectionState)) {
        const text = tr(
                model.connectionState === 'offline'
                    ? 'Connection lost; work retained'
                    : 'Interrupted operation available to resume'
            ),
            height = Math.max(36, captionHeight(text, width) * 1.2);
        children.push(
            label(
                'workspaceNavigationConnection',
                rect(0, y, width, height),
                text,
                { color: 'yellow', wrap: true }
            )
        );
        y += height + 4;
    }
    return { height: y, nodes: children };
}
