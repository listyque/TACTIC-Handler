import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function entryText(record) {
    return (
        record.time +
        ' · ' +
        record.operation +
        ' · ' +
        record.message +
        (record.path ? '\n' + record.path : '')
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        buttons = [
            ['fileWorkspaceCopyLog', 'Copy log', 'copy', 'copy'],
            ['fileWorkspaceClearLog', 'Clear log', 'delete', 'clear'],
            ['fileWorkspaceDebugLog', 'Debug Log', 'bug-report', 'debug'],
            [
                'fileWorkspaceHideLog',
                model.native
                    ? 'Hide log'
                    : model.expanded
                      ? 'Collapse log'
                      : 'Expand log',
                model.native
                    ? 'close'
                    : model.expanded
                      ? 'chevron-down'
                      : 'chevron-right',
                'visibility'
            ]
        ];
    const nodes = [
        node('Box', 'workspaceLogBackground', rect(0, 0, width, height), {
            background: 'panelDeep',
            radius: 14
        }),
        node('Icon', 'workspaceLogIcon', rect(6, 10, 16, 16), {
            icon: 'terminal',
            color: 'secondaryText'
        }),
        label(
            'workspaceLogTitle',
            rect(28, 4, Math.max(0, width - 164), 28),
            tr('Log'),
            { fontRole: 'secondary' }
        )
    ];
    for (const [index, [id, title, icon, type]] of buttons.entries())
        nodes.push(
            button(
                id,
                rect(Math.max(0, width - 136) + index * 32, 4, 28, 28),
                tr(title),
                icon,
                { type },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    nodes.push(
        node(
            'View',
            'workspaceLogEntries',
            rect(
                4,
                36,
                Math.max(0, width - 8),
                model.expanded ? Math.max(0, height - 40) : 100
            ),
            { view: 'entries', visible: !!model.expanded }
        )
    );
    return { nodes };
}

export function entry(record, width, height) {
    const color =
        record.level === 'ERROR'
            ? 'error'
            : record.level === 'WARNING'
              ? 'yellow'
              : 'secondaryText';
    return {
        nodes: [
            node('Icon', 'workspaceLogEntryIcon', rect(0, 0, 16, 16), {
                icon:
                    record.level === 'ERROR'
                        ? 'error'
                        : record.level === 'WARNING'
                          ? 'warning'
                          : 'info',
                color
            }),
            node(
                'View',
                'workspaceLogMessagePort',
                rect(22, 0, Math.max(0, width - 22), height),
                {
                    view: 'message',
                    text: entryText(record),
                    fontRole: 'secondary',
                    color: record.level === 'ERROR' ? 'error' : 'primaryText'
                }
            )
        ]
    };
}
