import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { metrics } from '../../../core/foundation.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function views(model, width, height, language) {
    const tr = (text) => translate(text, language),
        h = metrics(model.style).controlHeight,
        nodes = [],
        y = Math.max(0, (h - 28) / 2);
    let x = 0;
    if (model.narrow) {
        nodes.push(
            button(
                'workspaceToggleTree',
                rect(x, y, 28, 28),
                tr('Depots'),
                'account-tree',
                { type: 'tree' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
        x += 32;
    }
    nodes.push(
        node('Box', 'workspaceViewsSurface', rect(x, 0, h, h), {
            background: 'surfaceContainerHigh',
            radius: h / 2
        })
    );
    nodes.push(
        button(
            'workspaceViewsButton',
            rect(x, 0, h, h),
            tr('View'),
            'view-column',
            { type: 'menu', kind: 'views' },
            true,
            { iconOnly: true, iconAction: true, round: false }
        )
    );
    x += h + 4;
    const right =
        (model.canCreate ? 32 : 0) +
        (model.canMaximize ? 32 : 0) +
        (model.canActions === false ? 0 : 32);
    nodes.push(
        node(
            'View',
            'workspaceViewTabsPort',
            rect(x, 0, Math.max(0, width - x - right), height),
            { view: 'tabs' }
        )
    );
    x = Math.max(x, width - right);
    if (model.canCreate) {
        nodes.push(
            button(
                'newChangelistButton',
                rect(x, y, 28, 28),
                tr('New changelist'),
                'add',
                { type: 'create' },
                !model.busy && !!model.workspace,
                { iconOnly: true, iconAction: true }
            )
        );
        x += 32;
    }
    if (model.canMaximize) {
        nodes.push(
            button(
                'fileWorkspaceMaximize',
                rect(x, y, 28, 28),
                tr(model.maximized ? 'Restore panel' : 'Maximize panel'),
                model.maximized ? 'window-restore' : 'open-in-full',
                { type: 'maximize' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
        x += 32;
    }
    if (model.canActions !== false)
        nodes.push(
            button(
                'workspaceActionsButton',
                rect(x, y, 28, 28),
                tr('Workspace actions'),
                'more_vert',
                { type: 'menu', kind: 'workspace' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    return { nodes };
}

export function filters(model, width, language) {
    const tr = (text) => translate(text, language),
        h = metrics(model.style).controlHeight,
        nodes = [];
    let y = 0;
    if (model.kind === 'files' && model.localDirty) {
        const text = tr('Local changes detected. Reconcile to review them.'),
            height = Math.max(30, captionHeight(text, width) * 1.2);
        nodes.push(
            label('workspaceLocalDirty', rect(0, y, width, height), text, {
                color: 'yellow',
                wrap: true
            })
        );
        y += height + 4;
    }
    if (model.kind === 'files') {
        nodes.push(
            node(
                'Field',
                'workspacePathPrefix',
                rect(0, y, Math.max(0, width - 32), h),
                {
                    text: model.prefix || '',
                    label: tr('Path prefix'),
                    placeholder: tr('Path prefix'),
                    enabled: !model.busy,
                    action: { type: 'field', key: 'prefix' },
                    activateAction: { type: 'files' }
                }
            )
        );
        nodes.push(
            button(
                'workspacePathFilter',
                rect(Math.max(0, width - 28), y + (h - 28) / 2, 28, 28),
                tr('Filter'),
                'filter',
                { type: 'files' },
                !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
        y += h + 4;
    }
    const showReconcile = model.kind === 'files' && model.local,
        showChange = model.kind === 'changes',
        showFile = model.kind === 'files' || model.selectedCount > 0;
    const stateWidth = model.narrow ? 0 : 150,
        reconcileWidth = showReconcile
            ? Math.min(width / 2, model.reconcileWidth || 174)
            : 0;
    const controls =
        (stateWidth ? stateWidth + 4 : 0) +
        (reconcileWidth ? reconcileWidth + 4 : 0) +
        (showChange ? 32 : 0) +
        (showFile ? 32 : 0);
    const nameWidth = Math.max(0, width - controls);
    nodes.push(
        node('Field', 'workspaceLoadedFilter', rect(0, y, nameWidth, h), {
            label: tr('Filter loaded files'),
            placeholder: tr('Filter loaded files'),
            text: model.nameFilter || '',
            action: { type: 'field', key: 'name_filter' }
        })
    );
    let x = nameWidth + 4;
    if (stateWidth) {
        nodes.push(
            node('Choice', 'workspaceStateFilter', rect(x, y, stateWidth, h), {
                label: tr('File state'),
                options: [
                    ['', 'All states'],
                    ['Modified', 'Modified'],
                    ['Added', 'Added'],
                    ['Missing', 'Missing'],
                    ['Uploaded', 'Uploaded'],
                    ['Marked for delete', 'Marked for delete']
                ].map(([value, label]) => ({ value, label: tr(label) })),
                value: model.statusFilter || '',
                action: { type: 'field', key: 'status_filter' }
            })
        );
        x += stateWidth + 4;
    }
    if (showReconcile) {
        nodes.push(
            button(
                'reconcileAddFiles',
                rect(x, y, reconcileWidth, h),
                tr('Add to changelist…'),
                'add',
                { type: 'reconcile' },
                !model.busy &&
                    model.selectionScope === 'files' &&
                    model.selectedCount > 0
            )
        );
        x += reconcileWidth + 4;
    }
    if (showChange) {
        nodes.push(
            button(
                'changelistActionsButton',
                rect(x, y + (h - 28) / 2, 28, 28),
                tr('Changelist actions'),
                'more_vert',
                { type: 'menu', kind: 'change' },
                !!model.change,
                { iconOnly: true, iconAction: true }
            )
        );
        x += 32;
    }
    if (showFile)
        nodes.push(
            button(
                'fileActionsButton',
                rect(x, y + (h - 28) / 2, 28, 28),
                tr('File actions'),
                'more_vert',
                { type: 'menu', kind: 'files' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    return { height: y + h, nodes };
}
