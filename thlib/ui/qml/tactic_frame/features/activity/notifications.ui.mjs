import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function accent(kind) {
    return (
        { error: 'red', warning: 'yellow', complete: 'green' }[kind] || 'action'
    );
}
export function icon(kind) {
    return (
        {
            error: 'priority-high',
            warning: 'warning',
            complete: 'check-circle',
            progress: 'sync'
        }[kind] || 'info'
    );
}
export function filters(repository, language) {
    const tr = (text) => translate(text, language),
        rows = [
            { value: 'all', label: tr('All'), icon: 'select-all' },
            { value: 'server', label: tr('Server'), icon: 'dns' }
        ];
    if (repository)
        rows.push({
            value: 'repository',
            label: tr('Repository sync'),
            icon: 'repository-sync'
        });
    return rows.concat([
        { value: 'checkin', label: tr('Check-in'), icon: 'commit-queue' },
        { value: 'client', label: tr('Client'), icon: 'desktop' }
    ]);
}
export function layout(width, height) {
    const inner = Math.max(0, width - 44),
        headerHeight = width < 480 ? 142 : 134;
    return {
        panel: rect(12, 12, Math.max(0, width - 24), Math.max(0, height - 24)),
        header: rect(22, 22, inner, headerHeight),
        history: rect(
            22,
            32 + headerHeight,
            Math.max(0, inner - 8),
            Math.max(0, height - headerHeight - 54)
        ),
        rowWidth: Math.max(0, inner - 20)
    };
}
export function header(model, width, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 436,
        height = narrow ? 142 : 134,
        clearWidth = narrow ? 36 : 170;
    return {
        height,
        nodes: [
            node('Box', 'notificationsToolbar', rect(0, 0, width, height), {
                background: 'surfaceContainerHigh',
                radius: 9
            }),
            label(
                'notificationHistoryTitle',
                rect(10, 18, Math.max(0, width - clearWidth - 28), 20),
                tr('ACTIVITY & NOTIFICATIONS'),
                { fontRole: 'body', weight: 600, color: 'secondaryText' }
            ),
            button(
                'clearNotificationHistory',
                rect(Math.max(10, width - clearWidth - 10), 10, clearWidth, 36),
                narrow ? '' : tr('Clear history'),
                'delete-sweep',
                { type: 'clear' },
                !!model.count,
                { label: tr('Clear history'), iconOnly: narrow }
            ),
            label(
                'notificationHistoryDescription',
                rect(10, 54, Math.max(0, width - 20), narrow ? 36 : 20),
                tr(
                    'Client events and background operations from this session.'
                ),
                { fontRole: 'secondary', color: 'secondaryText', wrap: true }
            ),
            node(
                'Segmented',
                'notificationHistoryFilters',
                rect(10, height - 46, Math.max(0, width - 20), 36),
                {
                    label: tr('Notification history filters'),
                    value: model.group || 'all',
                    options: filters(model.repository, language),
                    iconOnly: width < 716,
                    action: { type: 'group' }
                }
            )
        ]
    };
}
export function row(model, width, heights = {}, language) {
    const tr = (text) => translate(text, language),
        color = accent(model.kind),
        compact = width < 620,
        contentX = 41,
        contentWidth = Math.max(0, width - contentX - 10),
        timeWidth = compact ? contentWidth : Math.min(130, contentWidth * 0.3),
        messageWidth = compact
            ? contentWidth
            : Math.max(0, contentWidth - timeWidth - 8),
        messageHeight = Math.max(19, heights.message || 19),
        timeHeight = model.time ? Math.max(15, heights.time || 15) : 0,
        headerHeight = compact
            ? messageHeight + (timeHeight ? timeHeight + 2 : 0)
            : Math.max(messageHeight, timeHeight),
        detailHeight = model.detail ? Math.max(16, heights.detail || 16) : 0,
        height = headerHeight + 15 + (detailHeight ? 4 + detailHeight : 0) + 26,
        groupTitle =
            {
                repository: 'Repository sync',
                checkin: 'Check-in operations',
                server: 'Server transactions'
            }[model.group] || 'Client',
        nodes = [
            node(
                'Box',
                'notificationRowSurface',
                rect(1, 1, Math.max(0, width - 2), height - 2),
                {
                    background: model.hovered
                        ? { mix: ['surfaceContainerHigh', 'primaryText', 0.08] }
                        : 'surfaceContainerHigh',
                    radius: 9,
                    border: 'outlineVariant',
                    borderWidth: 1
                }
            ),
            node('Box', 'notificationRowRail', rect(0, 6, 3, height - 12), {
                background: color,
                radius: 1.5
            }),
            node('Icon', 'notificationKind', rect(12, 10, 19, 19), {
                icon: icon(model.kind),
                color
            }),
            node(
                'View',
                'notificationMessagePort',
                rect(contentX, 10, messageWidth, messageHeight),
                { view: 'message' }
            ),
            label(
                'notificationGroup',
                rect(contentX, 10 + headerHeight + 4, contentWidth, 15),
                tr(groupTitle),
                { fontRole: 'caption', weight: 600, color }
            )
        ];
    if (timeHeight)
        nodes.push(
            node(
                'View',
                'notificationTimePort',
                rect(
                    compact ? contentX : width - 10 - timeWidth,
                    compact ? 12 + messageHeight : 10,
                    timeWidth,
                    timeHeight
                ),
                { view: 'time' }
            )
        );
    if (detailHeight)
        nodes.push(
            node(
                'View',
                'notificationDetailPort',
                rect(
                    contentX,
                    10 + headerHeight + 23,
                    contentWidth,
                    detailHeight
                ),
                { view: 'detail' }
            )
        );
    return { height, nodes };
}
export function empty(width, height, language) {
    const tr = (text) => translate(text, language),
        y = Math.max(0, (height - 70) / 2),
        contentWidth = Math.max(0, Math.min(440, width - 24));
    return {
        nodes: [
            node(
                'Icon',
                'notificationsEmptyIcon',
                rect((width - 30) / 2, y, 30, 30),
                { icon: 'notifications', color: 'secondaryText' }
            ),
            label(
                'emptyStateTitle',
                rect((width - contentWidth) / 2, y + 44, contentWidth, 22),
                tr('No events in this group'),
                {
                    fontRole: 'bodyLarge',
                    weight: 600,
                    align: 'center',
                    wrap: true
                }
            )
        ]
    };
}
