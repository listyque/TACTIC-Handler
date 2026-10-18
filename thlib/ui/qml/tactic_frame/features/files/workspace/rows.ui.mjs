import { node, rect, label } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { badges, value, columnTitles } from './presentation.mjs';

export const toneRole = (tone) =>
    ({
        error: 'error',
        warning: 'yellow',
        success: 'green',
        action: 'action',
        other: 'violet'
    })[tone] || 'secondaryText';
export const isBranch = (row) =>
    ['depot', 'stream', 'workspace', 'directory', 'change'].includes(row.kind);

export function treeMetrics(row, subtitle = '') {
    const indent = Math.min(8, Math.max(0, row.depth || 0)) * 16 + 2;
    return { height: subtitle ? 42 : 30, indent, captionX: indent + 26 };
}

export function treeTitle(row, language) {
    const tr = (text) => translate(text, language);
    if (row.kind === 'more') return tr('Load more');
    if (row.kind !== 'change') return row.name || row.path || '';
    return (
        tr('Changelist #{number}').replace('{number}', row.number || row.code) +
        ' · ' +
        (row.description || tr('No description'))
    );
}

export function treeSubtitle(row, language) {
    if (row.kind !== 'change') return '';
    const tr = (text) => translate(text, language),
        actions = row.file_actions;
    const counts = actions
        ? (actions.checkout || 0) +
          ' ' +
          tr('waiting') +
          ' / ' +
          Object.entries(actions)
              .filter(([action]) => action !== 'checkout')
              .reduce((sum, [, count]) => sum + count, 0) +
          ' ' +
          tr('staged')
        : tr('Counts not indexed');
    const state =
        {
            pending: 'Pending',
            submitted: 'Submitted',
            shelved: 'Shelved',
            reverted: 'Reverted'
        }[row.state] ||
        row.state ||
        '';
    return [
        tr(state),
        row.owner,
        row.workspace,
        row.stream,
        (row.opened_files || 0) + ' ' + tr('files'),
        counts,
        (row.conflict_files || 0) + ' ' + tr('conflicts'),
        row.state === 'pending' && row.local_counts?.files
            ? row.local_counts.files + ' ' + tr('local unstaged')
            : '',
        ((row.opened_bytes || 0) / 1048576).toFixed(1) + ' MB'
    ]
        .filter(Boolean)
        .join(' · ');
}

export function treeRow(model, width) {
    const row = model.row,
        metrics = treeMetrics(row, model.subtitle),
        height = metrics.height;
    const captionX = model.contentOnly ? 0 : metrics.captionX;
    const icon =
        {
            workspace: 'desktop',
            depot: 'database',
            stream: 'workflow',
            directory: row.expanded ? 'folder-open' : 'folder',
            change: 'archive',
            more: 'add',
            file: 'file'
        }[row.kind] || 'file';
    const color =
        row.kind === 'change'
            ? row.state === 'submitted'
                ? 'green'
                : row.state === 'shelved'
                  ? 'violet'
                  : 'yellow'
            : 'secondaryText';
    const textWidth = Math.max(
        0,
        width - captionX - 26 - (row.kind === 'change' ? 20 : 4)
    );
    const children = [
        node(
            'Icon',
            'workspaceTreeIcon',
            rect(captionX, (height - 17) / 2, 17, 17),
            { icon, color }
        ),
        label(
            'workspaceTreeCaption',
            rect(
                captionX + 21,
                model.subtitle ? 1 : 0,
                textWidth,
                model.subtitle ? 22 : height
            ),
            model.caption,
            { elideMiddle: true, fontRole: 'secondary' }
        )
    ];
    if (model.subtitle)
        children.push(
            label(
                'workspaceTreeSubtitle',
                rect(captionX + 21, 23, textWidth, 17),
                model.subtitle,
                { color: 'secondaryText', fontRole: 'caption' }
            )
        );
    if (row.kind === 'change')
        children.push(
            node(
                'Icon',
                'workspaceTreeState',
                rect(Math.max(captionX, width - 18), (height - 14) / 2, 14, 14),
                {
                    icon:
                        {
                            submitted: 'check-circle',
                            shelved: 'archive',
                            reverted: 'undo'
                        }[row.state] || 'schedule',
                    color: 'secondaryText'
                }
            )
        );
    return {
        nodes: [
            node('Box', 'workspaceTreeSurface', rect(0, 0, width, height), {
                background: model.selected
                    ? 'selected'
                    : model.pressed
                      ? 'rowHover'
                      : model.hovered
                        ? 'rowHover'
                        : 'transparent',
                radius: 10,
                children
            })
        ]
    };
}

export function fileRow(model, width, language) {
    const row = model.row,
        badge = badges(row)[0],
        height = 34,
        left = (model.leftPadding || 0) + 4;
    const columns = model.columns?.length
        ? model.columns.filter((column) => column.visible)
        : [
              { key: 'path', width: 300 },
              { key: 'local_status', width: 120 },
              { key: 'server_status', width: 120 },
              { key: 'number', width: 72 }
          ];
    const children = [
        node('CheckBox', 'workspaceFileCheck', rect(left, 0, 24, height), {
            checked: !!model.selected,
            compact: true,
            label: row.path,
            action: { type: 'check' }
        }),
        node('Icon', 'workspaceFileIcon', rect(left + 30, 8.5, 17, 17), {
            icon: badge.icon,
            color: toneRole(badge.tone)
        })
    ];
    let x = left + 53;
    for (const column of columns) {
        const text =
            column.key === 'checkout'
                ? model.checkoutLabel
                : column.key === 'local_status'
                  ? model.localLabel
                  : column.key === 'server_status'
                    ? model.serverLabel
                    : value(row, column.key);
        children.push(
            label(
                'workspaceFileCell_' + column.key,
                rect(x, 0, column.width, height),
                text || '',
                {
                    fontRole: 'secondary',
                    elideMiddle: true,
                    color: model.selected
                        ? 'selectedText'
                        : column.key === 'path'
                          ? 'primaryText'
                          : column.key === 'server_status'
                            ? toneRole(badge.tone)
                            : 'secondaryText',
                    toolTip: text || ''
                }
            )
        );
        x += column.width + 6;
    }
    if (
        model.checkoutLabel &&
        model.checkoutLabel !== translate('No active checkout', language)
    )
        children.push(
            node(
                'Icon',
                'workspaceFileLock',
                rect(Math.max(x, width - 18), 10, 14, 14),
                {
                    icon: 'lock',
                    color: (model.checkoutHolders || []).some(
                        (holder) => holder.owner !== model.currentUser
                    )
                        ? 'violet'
                        : 'action'
                }
            )
        );
    return {
        nodes: [
            node('Box', 'workspaceFileSurface', rect(0, 0, width, height), {
                background: model.selected
                    ? 'selected'
                    : model.pressed
                      ? 'rowHover'
                      : model.hovered
                        ? 'rowHover'
                        : 'transparent',
                children
            }),
            node(
                'Box',
                'workspaceFileSeparator',
                rect(0, height - 1, width, 1),
                { background: 'outlineVariant' }
            )
        ]
    };
}

export function fileHeader(model, width, language) {
    const nodes = [];
    let x = 57;
    for (const column of (model.columns || []).filter(
        (column) => column.visible
    )) {
        const title = translate(
            columnTitles[column.key] || column.key,
            language
        );
        const text =
            title +
            (model.sortColumn === column.key
                ? model.sortDesc
                    ? ' ↓'
                    : ' ↑'
                : '');
        nodes.push(
            node(
                'Action',
                'workspaceSort_' + column.key,
                rect(x, 0, column.width, 28),
                {
                    text: title,
                    normalColor: 'transparent',
                    selectedColor: 'transparent',
                    action: { type: 'sort', key: column.key },
                    children: [
                        label(
                            'workspaceHeading_' + column.key,
                            rect(0, 0, column.width, 28),
                            text,
                            { fontRole: 'secondary', color: 'secondaryText' }
                        )
                    ]
                }
            )
        );
        x += column.width + 6;
    }
    return { nodes };
}
