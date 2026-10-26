import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(model, width, language) {
    const tr = (text) => translate(text, language),
        groups = model.groups || [],
        metrics = model.metrics || {},
        nodes = [];
    nodes.push(
        node('Box', 'objectSnapshotTreeHeader', rect(0, 0, width, 64), {
            background: 'panel',
            border: 'separator',
            children: [
                node('Icon', 'objectSnapshotTreeIcon', rect(14, 23, 18, 18), {
                    icon: 'account-tree',
                    color: 'action'
                }),
                label(
                    'objectSnapshotTreeTitle',
                    rect(42, 10, Math.max(0, width - 56), 22),
                    tr('SNAPSHOTS BY PROCESS'),
                    { fontRole: 'bodyLarge', weight: 600 }
                ),
                label(
                    'objectSnapshotTreeCounts',
                    rect(42, 34, Math.max(0, width - 56), 18),
                    translate(
                        '{processes} processes · {snapshots} snapshots · {files} files',
                        language,
                        {
                            processes: groups.length,
                            snapshots: metrics.snapshots || 0,
                            files: metrics.files || 0
                        }
                    ),
                    { color: 'secondaryText', fontRole: 'caption' }
                )
            ]
        })
    );
    let y = 74;
    groups.forEach((group, index) => {
        const inner = Math.max(0, width - 16),
            expanded = !!(model.expanded || {})[group.value],
            children = [];
        children.push(
            node(
                'Action',
                'objectSnapshotProcess_' + index,
                rect(8, 8, inner, 62),
                {
                    text: group.label,
                    normalColor: 'transparent',
                    radius: 12,
                    action: { type: 'expand', value: group.value },
                    children: [
                        node('Icon', 'processExpand', rect(12, 22, 18, 18), {
                            icon: expanded ? 'expand-more' : 'chevron-right',
                            color: 'secondaryText'
                        }),
                        node('Icon', 'processIcon', rect(40, 22, 18, 18), {
                            icon: 'workflow',
                            color: group.accent || 'action'
                        }),
                        label(
                            'processLabel',
                            rect(70, 8, Math.max(0, inner - 128), 23),
                            group.label,
                            { fontRole: 'bodyLarge', weight: 600 }
                        ),
                        label(
                            'processCounts',
                            rect(70, 34, Math.max(0, inner - 128), 18),
                            translate(
                                '{snapshots} snapshots · {files} files · {size}',
                                language,
                                {
                                    snapshots: group.snapshotCount,
                                    files: group.fileCount,
                                    size: group.sizeText || '0 B'
                                }
                            ),
                            { fontRole: 'caption', color: 'secondaryText' }
                        ),
                        node(
                            'StatusChip',
                            'processBadge',
                            rect(Math.max(0, inner - 48), 18, 40, 26),
                            {
                                text: String(group.snapshotCount),
                                icon: 'snapshot',
                                accent: group.accent || 'action'
                            }
                        )
                    ]
                }
            )
        );
        let top = 78;
        if (expanded) {
            children.push(
                label(
                    'snapshotsHeading',
                    rect(18, top, Math.max(0, width - 36), 24),
                    tr('SNAPSHOTS AND VERSIONS'),
                    { fontRole: 'secondary', weight: 600 }
                )
            );
            top += 32;
            (group.snapshots || []).forEach((snapshot, row) => {
                children.push(
                    node(
                        'Action',
                        'objectReportSnapshot_' + index + '_' + row,
                        rect(8, top, inner, 72),
                        {
                            text: snapshot.title,
                            normalColor: 'transparent',
                            radius: 12,
                            action: {
                                type: 'snapshot',
                                index: snapshot.modelIndex,
                                key: snapshot.searchKey
                            },
                            children: [
                                node(
                                    'Preview',
                                    'snapshotPreview',
                                    rect(8, 9, 54, 54),
                                    {
                                        source: snapshot.previewUrl || '',
                                        initials: snapshot.version,
                                        icon: 'snapshot',
                                        outlined: true
                                    }
                                ),
                                label(
                                    'snapshotTitle',
                                    rect(72, 7, Math.max(0, inner - 152), 22),
                                    snapshot.title,
                                    { fontRole: 'bodyLarge', weight: 600 }
                                ),
                                label(
                                    'snapshotContext',
                                    rect(72, 31, Math.max(0, inner - 152), 17),
                                    [
                                        snapshot.context,
                                        snapshot.author,
                                        snapshot.repository
                                    ]
                                        .filter(Boolean)
                                        .join(' · '),
                                    {
                                        fontRole: 'caption',
                                        color: 'secondaryText'
                                    }
                                ),
                                label(
                                    'snapshotFiles',
                                    rect(72, 50, Math.max(0, inner - 152), 17),
                                    translate(
                                        '{files} files · {size} · {timestamp}',
                                        language,
                                        {
                                            files: snapshot.fileCount,
                                            size: snapshot.sizeText,
                                            timestamp: snapshot.timestampPretty
                                        }
                                    ),
                                    {
                                        fontRole: 'caption',
                                        color: 'secondaryText',
                                        tooltip: snapshot.timestampFull || ''
                                    }
                                ),
                                node(
                                    'StatusChip',
                                    'snapshotVersion',
                                    rect(Math.max(0, inner - 72), 23, 64, 26),
                                    {
                                        text: snapshot.isVersionless
                                            ? tr('Current')
                                            : snapshot.version,
                                        icon: snapshot.isVersionless
                                            ? 'sync'
                                            : 'history',
                                        accent: snapshot.isLatest
                                            ? 'green'
                                            : 'action'
                                    }
                                )
                            ]
                        }
                    )
                );
                top += 80;
            });
            if ((group.files || []).length) {
                children.push(
                    label(
                        'filesHeading',
                        rect(18, top, Math.max(0, width - 36), 24),
                        tr('FILES'),
                        { fontRole: 'secondary', weight: 600 }
                    )
                );
                top += 32;
            }
            (group.files || []).forEach((file, row) => {
                const height = (model.fileHeights || {})[file.token] || 64;
                children.push(
                    node(
                        'View',
                        'objectReportFile_' + index + '_' + row,
                        rect(8, top, inner, height),
                        { view: 'attachment', record: file }
                    )
                );
                top += height + 8;
            });
        }
        const height = expanded ? top + 8 : 78;
        nodes.push(
            node(
                'Box',
                'objectSnapshotProcessSurface_' + index,
                rect(0, y, width, height),
                { background: 'panel', border: 'separator', children }
            )
        );
        y += height + 10;
    });
    if (!groups.length) {
        nodes.push(
            label(
                'objectSnapshotTreeEmpty',
                rect(0, y, width, 72),
                tr('No snapshots found'),
                { color: 'secondaryText', align: 'center' }
            )
        );
        y += 72;
    }
    return { nodes, height: y };
}
