import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(state, width, height, language) {
    const root = state.pages.root,
        tr = (text) => translate(text, language),
        identity = [
            root.identity,
            root.context,
            root.version == null ? '' : 'v' + root.version
        ]
            .filter(Boolean)
            .join(' · ');
    return {
        nodes: [
            label(
                'dependencyIdentity',
                rect(0, 0, Math.max(0, width - 80), 30),
                identity,
                { weight: 600, toolTip: identity }
            ),
            label(
                'dependencyOwner',
                rect(0, 30, Math.max(0, width - 80), 24),
                state.notice
                    ? tr(state.notice)
                    : root.owner?.title ||
                          (root.snapshotKey ? tr('Object is unavailable') : ''),
                {
                    color: state.notice ? 'error' : 'secondaryText',
                    toolTip: state.notice ? tr(state.notice) : ''
                }
            ),
            button(
                'dependencyRefresh',
                rect(Math.max(0, width - 76), 0, 32, 32),
                tr('Refresh'),
                root.busy ? 'loading' : 'refresh',
                { type: 'refresh' },
                !root.busy,
                { iconOnly: true, iconAction: true }
            ),
            button(
                'dependencyClose',
                rect(Math.max(0, width - 36), 0, 32, 32),
                tr('Close'),
                'close',
                { type: 'close' },
                true,
                { iconOnly: true, iconAction: true }
            ),
            node(
                'List',
                'dependencyRows',
                rect(0, 62, width, Math.max(0, height - 62)),
                {
                    source: 'dependencyRows',
                    keyField: 'path',
                    rowHeight: 68,
                    fields: [
                        'path',
                        'pagePath',
                        'more',
                        'depth',
                        'kind',
                        'title',
                        'group',
                        'filename',
                        'fileType',
                        'fileRange',
                        'fileIndex',
                        'fileCode',
                        'snapshotKey',
                        'projectCode',
                        'parentCode',
                        'context',
                        'version',
                        'instance',
                        'node',
                        'origin',
                        'current',
                        'retired',
                        'ownerMissing',
                        'cycle',
                        'expandable',
                        'open',
                        'busy',
                        'error',
                        'revision'
                    ],
                    scrollbarId: 'dependencyScrollBar',
                    label: tr('Dependencies'),
                    role: 'list'
                }
            )
        ]
    };
}

export function row(record, width, language) {
    const tr = (text) => translate(text, language),
        id = (name) => name + '_' + record.path.replace(/\//g, '_'),
        left = Math.min(record.depth * 20, Math.max(0, width / 3)),
        nodes = [];
    if (record.kind === 'more' || record.kind === 'status') {
        nodes.push(
            label(
                id('dependencyStatus'),
                rect(left + 4, 0, Math.max(0, width - left - 48), 68),
                record.kind === 'more' ? tr('Show more') : tr(record.title),
                { color: record.error ? 'error' : 'secondaryText', wrap: true }
            )
        );
        if (record.kind === 'more' || record.error)
            nodes.push(
                button(
                    id('dependencyRetry'),
                    rect(Math.max(left, width - 36), 18, 32, 32),
                    tr(record.kind === 'more' ? 'Show more' : 'Retry'),
                    record.busy ? 'loading' : 'refresh',
                    {
                        type: 'read',
                        path: record.pagePath,
                        more: record.kind === 'more' || !!record.more
                    },
                    !record.busy,
                    { iconOnly: true, iconAction: true }
                )
            );
        return { nodes };
    }
    const title =
            record.filename ||
            [
                record.parentCode,
                record.context,
                record.version == null ? '' : 'v' + record.version
            ]
                .filter(Boolean)
                .join(' · ') ||
            record.title ||
            tr('Object is unavailable'),
        details = [
            tr(record.group),
            record.fileType,
            record.fileRange,
            record.instance ? tr('Instance') + ': ' + record.instance : '',
            record.node,
            record.origin,
            record.current ? tr('Current') : '',
            record.retired ? tr('Retired') : '',
            record.ownerMissing ? tr('Object is unavailable') : '',
            record.cycle ? tr('Cyclic dependency') : ''
        ]
            .filter(Boolean)
            .join(' · '),
        canOpen =
            record.kind === 'file' && !record.fileRange && !!record.fileCode;
    if (record.expandable)
        nodes.push(
            button(
                id('dependencyExpand'),
                rect(left, 18, 32, 32),
                tr(record.open ? 'Collapse' : 'Expand') + ' · ' + title,
                record.busy
                    ? 'loading'
                    : record.open
                      ? 'expand-more'
                      : 'chevron-right',
                { type: 'toggle', path: record.path },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    const textLeft = left + 36,
        textWidth = Math.max(0, width - textLeft - (canOpen ? 40 : 4));
    nodes.push(
        label(id('dependencyTitle'), rect(textLeft, 5, textWidth, 26), title, {
            toolTip: title
        })
    );
    nodes.push(
        label(
            id('dependencyDetails'),
            rect(textLeft, 32, textWidth, 26),
            details,
            {
                color: 'secondaryText',
                fontRole: 'caption',
                toolTip: details
            }
        )
    );
    if (canOpen)
        nodes.push(
            button(
                id('dependencyFileOpen'),
                rect(Math.max(0, width - 36), 18, 32, 32),
                tr('Open file') + ' · ' + title,
                'file',
                {
                    type: 'file',
                    snapshotKey: record.snapshotKey,
                    projectCode: record.projectCode,
                    fileCode: record.fileCode,
                    revision: record.revision
                },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    return { nodes };
}
