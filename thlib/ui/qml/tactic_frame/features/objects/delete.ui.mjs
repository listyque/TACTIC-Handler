import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function group(model, record, width, index, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const items = record.expanded ? record.items || [] : [];
    const itemHeight = Math.min(
        320,
        items.reduce((sum, item) => sum + dependencyHeight(item), 0)
    );
    const y = 47 + (items.length ? itemHeight + 4 : 0);
    if (items.length)
        nodes.push(
            node(
                'View',
                'deleteDependencyItems_' + index,
                rect(4, 47, Math.max(0, width - 8), itemHeight),
                {
                    view: 'dependencies',
                    source: 'dependencies_' + index
                }
            )
        );
    nodes.unshift(
        node(
            'CheckBox',
            'deleteDependencyCheck_' + index,
            rect(8, 11, 24, 24),
            {
                label: record.searchTypeTitle,
                prominent: !!record.defaultChecked,
                checked: !!record.checked,
                enabled: !model.busy && !model.deleting && !model.uncertain,
                action: { type: 'check', index }
            }
        ),
        button(
            'deleteDependencyExpand_' + index,
            rect(40, 9, 28, 28),
            tr(record.expanded ? 'Hide dependencies' : 'Show dependencies'),
            record.expanded ? 'expand-less' : 'expand-more',
            { type: 'expand', index },
            true,
            { iconOnly: true, iconAction: true, iconSize: 14 }
        ),
        node('Icon', 'deleteGroupIcon_' + index, rect(76, 14, 18, 18), {
            icon: record.iconName || 'sobject',
            color: 'secondaryText'
        }),
        label(
            'deleteGroupTitle_' + index,
            rect(102, 5, Math.max(0, width - 114), 21),
            record.searchTypeTitle,
            { weight: 600 }
        ),
        label(
            'deleteGroupCount_' + index,
            rect(102, 27, Math.max(0, width - 114), 16),
            translate('{count} related items', language, {
                count: record.count
            }),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    return {
        nodes: [
            node(
                'Box',
                'deleteDependencyGroup_' + index,
                rect(0, 0, width, y + (items.length ? 4 : 0)),
                {
                    radiusRole: 'sectionRadius',
                    background: record.checked
                        ? 'surfaceContainerHighest'
                        : 'surfaceContainerHigh',
                    children: nodes
                }
            )
        ],
        height: y + (items.length ? 4 : 0)
    };
}

export function models(model, language) {
    const targets = (model.targets || []).slice(0, 16);
    if (model.targetCount > targets.length)
        targets.push({
            searchKey: '__remaining__',
            remaining: true,
            title: translate('and {count} more sObjects', language, {
                count: model.targetCount - targets.length
            })
        });
    const result = { targets };
    (model.groups || []).forEach((group, index) => {
        result['dependencies_' + index] = (group.items || []).map(
            (record, position) =>
                Object.assign({}, record, {
                    position,
                    groupIndex: index,
                    iconName: group.iconName
                })
        );
    });
    return result;
}

export function dependencyHeight(record) {
    return record.details ? 52 : 44;
}

export function dependency(record, width) {
    const height = dependencyHeight(record),
        prefix =
            'dependency_' + record.groupIndex + '_' + record.position + '_';
    return {
        height,
        nodes: [
            node('Box', prefix + 'surface', rect(0, 0, width, height), {
                background:
                    record.position % 2
                        ? 'surfaceContainerLow'
                        : 'surfaceContainer',
                radius: 0
            }),
            node('Icon', prefix + 'icon', rect(14, (height - 17) / 2, 17, 17), {
                icon: record.iconName || 'sobject',
                color: 'secondaryText'
            }),
            label(
                prefix + 'title',
                rect(41, record.details ? 7 : 12, Math.max(0, width - 55), 21),
                record.title,
                { weight: 500 }
            ),
            ...(record.details
                ? [
                      label(
                          prefix + 'details',
                          rect(41, 30, Math.max(0, width - 55), 17),
                          record.details,
                          { fontRole: 'caption', color: 'secondaryText' }
                      )
                  ]
                : [])
        ]
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        margin = 16,
        w = Math.max(0, width - 32),
        groups = model.groups || [];
    const selected = groups.reduce(
            (sum, row) => sum + (row.checked ? row.count : 0),
            0
        ),
        total = groups.reduce((sum, row) => sum + row.count, 0);
    const targets = model.targets || [],
        targetHeight = Math.min(132, Math.max(56, targets.length * 30 + 20));
    const footerY = Math.max(0, height - 80),
        contentTop = 100 + targetHeight + 12;
    const errorHeight = model.error ? 64 : 0;
    const nodes = [
        node('Box', 'deleteSObjectSurface', rect(0, 0, width, height), {
            background: 'panelDeep',
            radius: 0
        }),
        node('Box', 'deleteSObjectHeader', rect(margin, 16, w, 72), {
            background: 'surfaceContainer',
            children: [
                node('Box', 'deleteIconSurface', rect(14, 15, 42, 42), {
                    background: 'errorContainer',
                    children: [
                        node('Icon', 'deleteIcon', rect(10, 10, 22, 22), {
                            icon: 'delete',
                            color: 'error'
                        })
                    ]
                }),
                label(
                    'deleteSObjectTitle',
                    rect(68, 12, Math.max(0, w - 180), 22),
                    tr(
                        model.targetCount === 1
                            ? 'Delete sObject'
                            : 'Delete sObjects'
                    ),
                    { fontRole: 'bodyLarge', weight: 600 }
                ),
                node(
                    'StatusChip',
                    'deleteTargetCount',
                    rect(Math.max(0, w - 100), 23, 46, 26),
                    {
                        text: String(model.targetCount || 0),
                        icon: 'sobject',
                        accent: 'error'
                    }
                ),
                label(
                    'deleteSObjectCaption',
                    rect(68, 37, Math.max(0, w - 120), 19),
                    tr(
                        'The selected objects and checked dependencies will be permanently removed from TACTIC.'
                    ),
                    { fontRole: 'secondary', color: 'secondaryText' }
                ),
                button(
                    'deleteHelp',
                    rect(Math.max(0, w - 42), 20, 32, 32),
                    tr('Deletion help'),
                    'help',
                    { type: 'help' },
                    true,
                    { iconOnly: true, iconAction: true }
                )
            ]
        }),
        node(
            'Box',
            'deleteSObjectTargetCard',
            rect(margin, 100, w, targetHeight),
            { background: 'surfaceContainerHigh', radiusRole: 'sectionRadius' }
        ),
        node(
            'Box',
            'deleteTargetRail',
            rect(margin + 1, 108, 3, targetHeight - 16),
            { background: 'error', radius: 1.5 }
        ),
        node(
            'List',
            'deleteSObjectTargets',
            rect(margin + 14, 110, w - 28, targetHeight - 20),
            {
                source: 'targets',
                keyField: 'searchKey',
                rowHeight: 30,
                rowGap: 2,
                background: 'surfaceContainerHigh'
            }
        ),
        node('Box', 'deleteSObjectFooter', rect(margin, footerY, w, 64), {
            background: 'surfaceContainer',
            children: [
                label(
                    'deleteFooterStatus',
                    rect(14, 18, Math.max(0, w - 236), 28),
                    model.ready
                        ? translate('{count} dependencies selected', language, {
                              count: selected
                          })
                        : tr('Reviewing selected objects'),
                    { fontRole: 'secondary', color: 'secondaryText' }
                ),
                button(
                    'deleteCancel',
                    rect(Math.max(0, w - 216), 14, 96, 36),
                    tr('Cancel'),
                    '',
                    { type: 'cancel' },
                    !model.deleting
                ),
                button(
                    'deleteSubmit',
                    rect(Math.max(0, w - 112), 14, 102, 36),
                    tr('Delete'),
                    'delete',
                    { type: 'delete' },
                    model.ready &&
                        !model.busy &&
                        !model.deleting &&
                        !model.uncertain,
                    { destructive: true, highlighted: true }
                )
            ]
        })
    ];
    const bodyHeight = Math.max(0, footerY - contentTop - 12 - errorHeight);
    if (groups.length && model.ready) {
        nodes.push(
            label(
                'deleteDependenciesTitle',
                rect(margin, contentTop, w - 128, 22),
                tr('Dependencies'),
                { weight: 600 }
            )
        );
        nodes.push(
            label(
                'deleteDependenciesCaption',
                rect(margin, contentTop + 22, w, 18),
                tr(
                    'Choose related records to remove with the selected objects.'
                ),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
        nodes.push(
            node(
                'StatusChip',
                'deleteDependencySelection',
                rect(Math.max(margin, width - 123), contentTop + 5, 107, 24),
                {
                    text: translate(
                        '{selected} of {total} selected',
                        language,
                        { selected, total }
                    ),
                    icon: 'check',
                    accent: 'secondaryText'
                }
            )
        );
        let y = 6;
        const children = [];
        groups.forEach((record, index) => {
            const scene = group(
                model,
                record,
                Math.max(0, w - 12),
                index,
                language
            );
            children.push(
                node(
                    'Box',
                    'deleteGroupRow_' + index,
                    rect(6, y, Math.max(0, w - 12), scene.height),
                    { background: 'transparent', children: scene.nodes }
                )
            );
            y += scene.height + 8;
        });
        nodes.push(
            node(
                'Box',
                'deleteDependenciesSurface',
                rect(margin, contentTop + 45, w, Math.max(0, bodyHeight - 45)),
                {
                    background: 'surfaceContainerLow',
                    radiusRole: 'sectionRadius'
                }
            )
        );
        nodes.push(
            node(
                'Scroll',
                'deleteSObjectDependencies',
                rect(margin, contentTop + 45, w, Math.max(0, bodyHeight - 45)),
                {
                    contentHeight: y,
                    children,
                    background: 'surfaceContainerLow'
                }
            )
        );
    } else if (model.ready) {
        nodes.push(
            node(
                'Box',
                'deleteEmptySurface',
                rect(margin, contentTop - 2, w, bodyHeight + 2),
                { background: 'surfaceContainerLow', border: 'outlineVariant' }
            )
        );
        nodes.push(
            node(
                'Icon',
                'deleteEmptyIcon',
                rect(width / 2 - 15, contentTop + bodyHeight / 2 - 32, 30, 30),
                { icon: 'check-circle', color: 'action' }
            )
        );
        nodes.push(
            label(
                'deleteSObjectEmptyState',
                rect(margin + 24, contentTop + bodyHeight / 2 + 6, w - 48, 36),
                tr(
                    'No dependencies were found. Only the selected objects will be deleted.'
                ),
                { align: 'center', wrap: true, color: 'secondaryText' }
            )
        );
    }
    if (model.error) {
        nodes.push(
            label(
                'deleteSObjectError',
                rect(margin, footerY - 76, Math.max(0, w - 106), 64),
                tr(model.error),
                { wrap: true, color: 'error', role: 'alert' }
            )
        );
        if (!model.ready && !model.uncertain && !model.busy)
            nodes.push(
                button(
                    'deleteRetry',
                    rect(Math.max(margin, width - 120), footerY - 68, 104, 36),
                    tr('Retry'),
                    'refresh',
                    { type: 'retry' },
                    true
                )
            );
    }
    return {
        nodes,
        height,
        loading:
            model.busy || model.deleting
                ? {
                      bounds: rect(
                          12,
                          94,
                          width - 24,
                          Math.max(0, height - 180)
                      ),
                      message: tr(
                          model.deleting
                              ? 'Deleting selected objects…'
                              : 'Discovering dependencies…'
                      ),
                      cancellable: !model.deleting
                  }
                : null
    };
}

export function target(record, width) {
    return {
        nodes: [
            node('Icon', 'deleteTargetIcon', rect(0, 7, 14, 14), {
                icon: 'sobject',
                color: 'error'
            }),
            label(
                'deleteTargetTitle',
                rect(22, 2, Math.max(0, width - 38), 26),
                record.title
            )
        ]
    };
}
