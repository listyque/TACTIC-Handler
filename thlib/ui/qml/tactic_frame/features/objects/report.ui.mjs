import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const sections = [
    { value: 'tasks', label: 'Tasks', icon: 'task' },
    { value: 'notes', label: 'Notes', icon: 'notes' },
    { value: 'children', label: 'Children', icon: 'account-tree' },
    { value: 'snapshots', label: 'Snapshots', icon: 'snapshot' },
    { value: 'activity', label: 'Activity', icon: 'activity-feed' }
];

function metric(id, title, value, bounds, color, language) {
    return node('Box', id, bounds, {
        background: 'transparent',
        radius: 0,
        children: [
            label(
                id + 'Value',
                rect(0, 0, bounds.width, 28),
                String(value ?? 0),
                {
                    fontRole: 'statistic',
                    weight: 600,
                    color: color || 'primaryText'
                }
            ),
            label(
                id + 'Label',
                rect(0, 29, bounds.width, 15),
                translate(title, language),
                { fontRole: 'caption', weight: 600, color: 'secondaryText' }
            )
        ]
    });
}

// Hosts measure their house font; layout and intrinsic GridLayout proportions remain shared.
export function header(
    model,
    width,
    language,
    measure = (text, size) => String(text).length * size * 0.55
) {
    const tr = (text) => translate(text, language),
        summary = model.summary || {},
        metrics = model.metrics || {};
    const preview = width >= 700 ? 142 : width >= 420 ? 116 : 82;
    const left = 14 + preview + (width >= 560 ? 18 : 10),
        textWidth = Math.max(0, width - left - 14);
    const columns = width >= 1040 ? 4 : width >= 560 ? 2 : 1;
    const fields = [
        ['Code', summary.code, 'code'],
        ['Search Type', summary.searchType, 'sobject'],
        ['Project', summary.project, 'project-diagram'],
        ['Pipeline', summary.pipeline, 'workflow']
    ].filter((row) => row[1]);
    function gridWidths(rows, count, available, gap, preferred) {
        const hints = Array.from({ length: count }, (_, column) =>
            Math.max(
                1,
                ...rows
                    .filter((_, index) => index % count === column)
                    .map(preferred)
            )
        );
        const total = hints.reduce((sum, hint) => sum + hint, 0),
            room = Math.max(0, available - gap * (count - 1));
        return hints.map((hint) => (room * hint) / total);
    }
    const fieldWidths = gridWidths(
        fields,
        columns,
        textWidth,
        14,
        ([title, value]) =>
            24 +
            Math.max(
                Math.ceil(measure(tr(title), 11)),
                Math.ceil(measure(String(value), 13))
            )
    );
    const description = summary.description || tr('No description provided');
    const descriptionHeight = Math.min(
        42,
        Math.max(
            1,
            Math.ceil(measure(description, 13) / Math.max(1, textWidth))
        ) * 17
    );
    const infoY = 80 + descriptionHeight,
        infoHeight = fields.length
            ? Math.ceil(fields.length / columns) * 38 - 5
            : 0;
    const topHeight = Math.max(preview, infoY - 14 + infoHeight + 40);
    const metricColumns =
        width >= 1040 ? 8 : width >= 560 ? 4 : width >= 340 ? 2 : 1;
    const values = [
        ['TASKS', metrics.tasks || 0],
        ['NOTES', metrics.notes || 0],
        ['CHILDREN', metrics.children || 0],
        ['PEOPLE', metrics.participants || 0],
        [
            'WORK HOURS',
            Number(metrics.workHours || 0).toFixed(1) + ' ' + tr('h')
        ],
        ['FILES', metrics.files || 0],
        ['SNAPSHOTS', metrics.snapshots || 0],
        [
            metrics.canViewCosts ? 'TOTAL COST' : 'TOTAL SIZE',
            metrics.canViewCosts
                ? Number(metrics.totalCost || 0).toFixed(2)
                : metrics.totalSize || '0 B'
        ]
    ];
    const metricRows = Math.ceil(8 / metricColumns),
        metricHeight =
            width >= 1040
                ? 50
                : width >= 560
                  ? 86
                  : metricRows * 44 + (metricRows - 1) * 5;
    const height = Math.max(256, 28 + topHeight + 21 + metricHeight),
        extra = height - (28 + topHeight + 21 + metricHeight);
    const nodes = [
        node('Box', 'objectReportHeaderSurface', rect(0, 0, width, height), {
            background: 'surfaceContainerHigh',
            border: 'outlineVariant'
        }),
        node(
            'Preview',
            'objectReportPreview',
            rect(14, 14 + (topHeight - preview) / 2, preview, preview),
            {
                source: summary.previewUrl || '',
                initials: String(summary.title || '?')
                    .slice(0, 2)
                    .toUpperCase(),
                icon: 'sobject',
                accent: summary.accent || 'action',
                outlined: true,
                radius: 12,
                round: false
            }
        ),
        label(
            'objectReportTitle',
            rect(left, 14, textWidth, 24),
            summary.title || tr('No sObject selected'),
            { fontRole: 'display', weight: 600 }
        ),
        node(
            'StatusChip',
            'objectReportType',
            rect(
                left,
                44,
                Math.min(
                    textWidth,
                    Math.ceil(measure(summary.typeTitle || '', 11, 600)) + 34
                ),
                24
            ),
            {
                text: summary.typeTitle || '',
                icon: 'sobject',
                accent: summary.accent || 'action'
            }
        ),
        node(
            'View',
            'objectReportDescription',
            rect(left, 74, textWidth, descriptionHeight),
            {
                view: 'reportDescription',
                text: description,
                empty: !summary.description
            }
        )
    ];
    fields.forEach(([title, value, icon], index) => {
        const column = index % columns,
            x =
                left +
                fieldWidths
                    .slice(0, column)
                    .reduce((sum, value) => sum + value + 14, 0),
            y = infoY + Math.floor(index / columns) * 38,
            cell = fieldWidths[column];
        nodes.push(
            node(
                'Icon',
                'objectReportFieldIcon_' + index,
                rect(x, y + 9, 15, 15),
                { icon, color: 'secondaryText', iconSize: 15 }
            )
        );
        nodes.push(
            label(
                'objectReportFieldLabel_' + index,
                rect(x + 24, y, cell - 24, 15),
                tr(title),
                Object.assign({}, muted, { fontRole: 'caption' })
            )
        );
        nodes.push(
            label(
                'objectReportFieldValue_' + index,
                rect(x + 24, y + 15, cell - 24, 18),
                String(value),
                { fontRole: 'body', elide: 'middle' }
            )
        );
    });
    nodes.push(
        label(
            'objectReportUpdated',
            rect(left, 14 + topHeight - 28, textWidth - 66, 28),
            summary.updatedPretty
                ? tr('Updated') + ': ' + summary.updatedPretty
                : '',
            Object.assign({}, muted, {
                fontRole: 'caption',
                tooltip: summary.updatedFull || ''
            })
        )
    );
    [
        ['open', 'Open sObject', 'open-in-new'],
        ['refresh', 'Refresh report', 'refresh']
    ].forEach(([type, text, icon], index) =>
        nodes.push(
            button(
                'objectReport_' + type,
                rect(width - 74 + index * 33, topHeight - 14, 28, 28),
                tr(text),
                icon,
                { type },
                !!summary.searchKey && (type !== 'refresh' || !model.busy),
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        )
    );
    nodes.push(
        node(
            'Box',
            'objectReportHeaderDivider',
            rect(14, 24 + topHeight, width - 28, 1),
            { background: 'separator', radius: 0 }
        )
    );
    const widths = gridWidths(
        values,
        metricColumns,
        width - 28,
        12,
        ([title, value]) =>
            Math.max(
                Math.ceil(
                    measure(tr(title), 11, 600) + tr(title).length * 0.25
                ),
                Math.ceil(measure(String(value), 21, 600))
            )
    );
    values.forEach(([title, value], index) => {
        const column = index % metricColumns;
        nodes.push(
            metric(
                'objectReportMetric_' + index,
                title,
                value,
                rect(
                    14 +
                        widths
                            .slice(0, column)
                            .reduce((sum, value) => sum + value + 12, 0),
                    35 +
                        topHeight +
                        extra +
                        Math.floor(index / metricColumns) * 49,
                    widths[column],
                    44
                ),
                '',
                language
            )
        );
    });
    return { nodes, height };
}

export function tabs(page, width, language) {
    const gap = 2,
        cell = Math.max(0, (width - gap * 4) / 5),
        narrow = width < 420;
    return {
        height: 36,
        nodes: sections.map((section, index) =>
            button(
                'objectReportTab_' + section.value,
                rect(index * (cell + gap), 0, cell, 36),
                translate(section.label, language),
                section.icon,
                { type: 'page', value: section.value },
                true,
                {
                    radio: true,
                    selected: page === section.value,
                    iconOnly: narrow,
                    iconSize: 16
                }
            )
        )
    };
}

function status(id, text, x, y, maximum, accent, icon) {
    // shortcut: bounded Segoe UI chips; replace with glyph advances for configurable fonts.
    const width = Math.min(
        Math.max(0, maximum),
        String(text || '').length * 6 + 30
    );
    return node('StatusChip', id, rect(x, y, width, 24), {
        text,
        icon,
        accent: accent || 'secondaryText',
        fontRole: 'caption',
        weight: 600
    });
}

export function row(kind, record, width, index, language) {
    const tr = (text) => translate(text, language),
        children = [];
    const accent =
        record.processColor || record.authorColor || record.accent || 'action';
    let height = kind === 'person' ? 76 : kind === 'child' ? 68 : 72;
    let title = record.title || '',
        subtitle = record.subtitle || '';
    function text(id, x, y, w, h, value, options) {
        children.push(label(id, rect(x, y, w, h), value || '', options));
    }
    function preview(size, x, y, source, initials, round) {
        children.push(
            node('Preview', 'objectReportRowPreview', rect(x, y, size, size), {
                source: source || '',
                initials: initials || '',
                icon: kind === 'child' ? 'sobject' : 'person',
                accent:
                    kind === 'person' ? record.avatarColor || accent : accent,
                round,
                radius: round ? size / 2 : 12,
                outlined: round
            })
        );
    }
    if (kind === 'person') {
        title = record.displayName;
        preview(42, 10, 17, record.avatarUrl, record.initials, true);
        text('objectReportRowTitle', 61, 17, width - 161, 22, title, {
            weight: 600
        });
        subtitle = translate(
            '{tasks} tasks · {notes} notes · {snapshots} snapshots',
            language,
            {
                tasks: record.taskCount,
                notes: record.noteCount,
                snapshots: record.snapshotCount
            }
        );
        text('objectReportRowSubtitle', 61, 42, width - 161, 17, subtitle, {
            fontRole: 'caption',
            color: 'secondaryText'
        });
        text(
            'objectReportRowHours',
            width - 92,
            27,
            62,
            22,
            Number(record.hours || 0).toFixed(1) + ' ' + tr('h'),
            {
                align: 'right',
                color:
                    record.hours > 0
                        ? record.accent || 'action'
                        : 'secondaryText',
                weight: 600
            }
        );
        if (record.cost > 0)
            text(
                'objectReportRowCost',
                width - 130,
                42,
                100,
                17,
                tr('Cost') + ' ' + Number(record.cost).toFixed(2),
                { fontRole: 'caption', align: 'right', color: 'secondaryText' }
            );
    } else if (kind === 'task') {
        title = record.processLabel;
        children.push(
            node('Box', 'objectReportTaskIconSurface', rect(12, 17, 38, 38), {
                background: 'panelRaised',
                radius: 12,
                children: [
                    node('Icon', 'taskProcessIcon', rect(11, 11, 16, 16), {
                        icon: 'workflow',
                        color: accent
                    })
                ]
            })
        );
        let right = width - 30;
        if (width >= 760) {
            text(
                'taskNotes',
                right - 20,
                26,
                20,
                18,
                String(record.notesCount || 0),
                { fontRole: 'caption', color: 'secondaryText' }
            );
            right -= 30;
            children.push(
                node('Icon', 'taskNotesIcon', rect(right - 14, 29, 14, 14), {
                    icon: 'notes',
                    color: 'secondaryText'
                })
            );
            right -= 24;
            text(
                'taskProgress',
                right - 38,
                26,
                38,
                18,
                (record.progress || 0) + '%',
                { fontRole: 'secondary', weight: 600 }
            );
            right -= 48;
            if (record.endPretty) {
                const extent = Math.min(
                    110,
                    String(record.endPretty).length * 6 + 4
                );
                text(
                    'taskDeadline',
                    right - extent,
                    26,
                    extent,
                    18,
                    record.endPretty,
                    {
                        fontRole: 'caption',
                        color:
                            record.dueState === 'overdue'
                                ? 'error'
                                : 'secondaryText',
                        tooltip: record.endFull || ''
                    }
                );
                right -= extent + 10;
            }
            text(
                'taskHours',
                right - 84,
                26,
                84,
                18,
                Number(record.loggedHours || 0).toFixed(1) +
                    ' / ' +
                    Number(record.plannedHours || 0).toFixed(1) +
                    ' ' +
                    tr('h'),
                { fontRole: 'caption', color: 'secondaryText' }
            );
            right -= 94;
            const assignedWidth = 140;
            children.push(
                node(
                    'Preview',
                    'taskAssigneeAvatar',
                    rect(right - assignedWidth, 23, 26, 26),
                    {
                        source: record.assignedAvatar || '',
                        initials: String(record.assignedLabel || '')
                            .slice(0, 2)
                            .toUpperCase(),
                        icon: 'person',
                        accent: record.assignedColor || 'action',
                        round: true,
                        outlined: false
                    }
                )
            );
            text(
                'taskAssignee',
                right - assignedWidth + 32,
                26,
                assignedWidth - 32,
                18,
                record.assignedLabel,
                { fontRole: 'caption', color: 'secondaryText' }
            );
            right -= assignedWidth + 10;
            const chip = status(
                'taskStatus',
                record.status || '',
                Math.max(60, right - 110),
                13,
                110,
                record.statusColor,
                'system-activity'
            );
            children.push(chip);
            text(
                'objectReportRowTitle',
                60,
                13,
                Math.max(0, right - 60 - chip.width - 8),
                22,
                title,
                { fontRole: 'bodyLarge', weight: 600 }
            );
            text(
                'objectReportRowSubtitle',
                60,
                39,
                right - 60,
                18,
                record.description || record.assignedLabel,
                { fontRole: 'caption', color: 'secondaryText' }
            );
        } else {
            text('objectReportRowTitle', 60, 7, width - 90, 22, title, {
                fontRole: 'bodyLarge',
                weight: 600
            });
            text(
                'objectReportRowSubtitle',
                60,
                30,
                width - 90,
                17,
                record.description || record.assignedLabel,
                { fontRole: 'caption', color: 'secondaryText' }
            );
            const detail = [
                record.status,
                record.assignedLabel,
                Number(record.loggedHours || 0).toFixed(1) +
                    ' / ' +
                    Number(record.plannedHours || 0).toFixed(1) +
                    ' ' +
                    tr('h'),
                record.endPretty,
                (record.progress || 0) + '%'
            ]
                .filter(Boolean)
                .join(' · ');
            text('objectReportRowMeta', 60, 50, width - 90, 17, detail, {
                fontRole: 'caption',
                color: record.dueState === 'overdue' ? 'error' : 'secondaryText'
            });
        }
    } else if (kind === 'note') {
        title = record.authorLabel;
        // shortcut: fixed Segoe UI wrapping estimate, shared with the existing form captions; measure glyph advances for configurable fonts.
        const available = Math.max(1, width - 90);
        let lines = 0;
        for (const paragraph of String(record.body || '').split('\n'))
            lines += Math.max(1, Math.ceil((paragraph.length * 7) / available));
        height = Math.max(84, lines * 18 + 54);
        preview(34, 11, 11, record.avatarUrl, record.initials, true);
        const chip = status(
            'noteContext',
            record.isTaskNote
                ? record.taskTitle || tr('Task note')
                : tr('Object note'),
            Math.max(55, width - 220),
            10,
            116,
            accent,
            record.isTaskNote ? 'task' : 'sobject'
        );
        children.push(chip);
        text('noteTimestamp', width - 96, 13, 70, 18, record.timestampPretty, {
            fontRole: 'caption',
            color: 'secondaryText',
            tooltip: record.timestampFull || ''
        });
        text(
            'objectReportRowTitle',
            55,
            10,
            Math.max(0, chip.x - 61),
            22,
            title,
            { weight: 600 }
        );
        text(
            'objectReportRowSubtitle',
            55,
            40,
            width - 85,
            height - 54,
            record.body,
            { wrap: true }
        );
    } else {
        preview(
            44,
            9,
            12,
            record.previewUrl,
            String(title).slice(0, 2).toUpperCase(),
            false
        );
        const wide = width >= 600,
            extent = wide ? 270 : 0;
        text('objectReportRowTitle', 63, 14, width - 93 - extent, 22, title, {
            weight: 600
        });
        text(
            'objectReportRowSubtitle',
            63,
            39,
            width - 93 - extent,
            17,
            subtitle,
            { fontRole: 'caption', color: 'secondaryText' }
        );
        if (wide) {
            children.push(
                status(
                    'childType',
                    record.typeTitle,
                    width - 285,
                    22,
                    100,
                    accent,
                    'sobject'
                )
            );
            if (record.status)
                children.push(
                    status(
                        'childStatus',
                        record.status,
                        width - 177,
                        22,
                        100,
                        'secondaryText',
                        'system-activity'
                    )
                );
            text(
                'childRelationship',
                width - 70,
                25,
                40,
                18,
                record.relationship,
                { fontRole: 'caption', color: 'secondaryText' }
            );
        }
    }
    children.push(
        node(
            'Icon',
            'objectReportRowArrow',
            rect(Math.max(0, width - 25), (height - 15) / 2, 15, 15),
            { icon: 'arrow-forward', color: 'secondaryText' }
        )
    );
    if (kind !== 'person' || record.hours > 0)
        children.push(
            node('Box', 'objectReportRowRail', rect(0, 5, 3, height - 10), {
                background: accent,
                radius: 0
            })
        );
    return {
        height,
        nodes: [
            node(
                'Action',
                'objectReportRow_' + kind + '_' + index,
                rect(0, 0, width, height),
                {
                    text: title || subtitle || '',
                    normalColor: 'transparent',
                    radius: 0,
                    action: {
                        type: kind,
                        index,
                        key: record.searchKey || record.login || '',
                        process: record.process || '',
                        taskCode: record.taskCode || ''
                    },
                    children
                }
            )
        ]
    };
}

export function page(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        metrics = model.metrics || {};
    let y = 0;
    function panel(
        id,
        title,
        icon,
        children,
        height,
        x = 0,
        panelWidth = width,
        detail = ''
    ) {
        nodes.push(
            node('Box', id, rect(x, y, panelWidth, height), {
                background: 'panel',
                border: 'outlineVariant',
                children: [
                    node('Icon', id + 'Icon', rect(14, 14, 15, 15), {
                        icon,
                        color: 'action'
                    }),
                    label(
                        id + 'Title',
                        rect(
                            37,
                            10,
                            Math.max(0, panelWidth - 51 - (detail ? 144 : 0)),
                            24
                        ),
                        tr(title),
                        { weight: 600 }
                    ),
                    ...(detail
                        ? [
                              label(
                                  id + 'Detail',
                                  rect(
                                      Math.max(0, panelWidth - 155),
                                      13,
                                      141,
                                      18
                                  ),
                                  detail,
                                  {
                                      align: 'right',
                                      fontRole: 'caption',
                                      color: 'secondaryText'
                                  }
                              )
                          ]
                        : []),
                    ...children
                ]
            })
        );
        y += height + 12;
    }
    function rows(id, title, icon, kind, records, empty) {
        const columns =
            kind === 'person' ? (width >= 940 ? 3 : width >= 600 ? 2 : 1) : 1;
        const gap = kind === 'person' ? 8 : 6,
            padding = kind === 'person' ? 14 : 12;
        const rowWidth = Math.max(
            0,
            (width - padding * 2 - gap * (columns - 1)) / columns
        );
        let top = kind === 'person' ? 52 : 44;
        const children = [];
        let rowHeight = 0;
        records.forEach((record, index) => {
            const value = Object.assign({}, record, {
                accent: record.accent || model.summary?.accent || 'action'
            });
            const scene = row(kind, value, rowWidth, index, language);
            if (index > 0 && index % columns === 0) {
                top += rowHeight + gap;
                rowHeight = 0;
            }
            children.push(
                node(
                    'Box',
                    id + 'Row_' + index,
                    rect(
                        padding + (index % columns) * (rowWidth + gap),
                        top,
                        rowWidth,
                        scene.height
                    ),
                    { background: 'transparent', children: scene.nodes }
                )
            );
            rowHeight = Math.max(rowHeight, scene.height);
        });
        if (!records.length) {
            children.push(
                node(
                    'Icon',
                    id + 'EmptyIcon',
                    rect(width / 2 - 15, 99, 30, 30),
                    { icon, color: 'secondaryText' }
                )
            );
            children.push(
                label(
                    id + 'Empty',
                    rect(12, 137, Math.max(0, width - 24), 36),
                    tr(empty),
                    Object.assign({}, muted, { align: 'center', wrap: true })
                )
            );
        }
        const height = Math.max(
            kind === 'person' ? 150 : 0,
            records.length ? top + rowHeight + 14 : 198
        );
        const detail =
            kind === 'person'
                ? translate('{count} people · {hours} h', language, {
                      count: metrics.participants || 0,
                      hours: Number(metrics.workHours || 0).toFixed(1)
                  })
                : kind === 'task'
                  ? translate('{count} tasks', language, {
                        count: metrics.tasks || 0
                    })
                  : kind === 'child'
                    ? translate('{count} children', language, {
                          count: metrics.children || 0
                      })
                    : kind === 'note'
                      ? translate(
                            '{objects} object · {tasks} task notes',
                            language,
                            {
                                objects: metrics.objectNotes || 0,
                                tasks: metrics.taskNotes || 0
                            }
                        )
                      : '';
        panel(id, title, icon, children, height, 0, width, detail);
    }
    function chips(
        id,
        title,
        icon,
        records,
        action,
        x = 0,
        panelWidth = width,
        detail = ''
    ) {
        let left = 14,
            top = 44;
        const children = records.map((record, index) => {
            const chip = status(
                id + 'Chip_' + index,
                (record.label || record.value || tr('Unspecified')) +
                    '  ' +
                    (record.count || 0),
                0,
                0,
                Math.max(0, panelWidth - 28),
                record.accent || 'action',
                icon
            );
            if (left > 14 && left + chip.width > panelWidth - 14) {
                left = 14;
                top += 31;
            }
            chip.x = left;
            chip.y = top;
            chip.action = action
                ? { type: 'filter', field: action, value: record.value }
                : null;
            left += chip.width + 7;
            return chip;
        });
        panel(
            id,
            title,
            icon,
            children,
            id === 'objectChildTypes'
                ? records.length
                    ? top + 24 + 12
                    : 52
                : Math.max(150, top + 38),
            x,
            panelWidth,
            id === 'objectChildTypes'
                ? translate('{count} relations', language, {
                      count: metrics.childTypes || records.length
                  })
                : detail
        );
    }
    if (model.page === 'tasks') {
        const values = [
            ['TOTAL', metrics.tasks, ''],
            ['ACTIVE TASKS', metrics.activeTasks, ''],
            ['COMPLETED', metrics.completedTasks, 'green'],
            [
                'OVERDUE',
                metrics.overdueTasks,
                metrics.overdueTasks ? 'error' : ''
            ],
            ['UNASSIGNED', metrics.unassignedTasks, ''],
            ['AVERAGE PROGRESS', (metrics.averageProgress || 0) + '%', '']
        ];
        const wideMetrics = width >= 780,
            panelWidth = wideMetrics ? (width - 20) / 2 : width;
        const cell = Math.max(0, (panelWidth - 32 - 28) / 3);
        for (let group = 0; group < 2; group++)
            nodes.push(
                node(
                    'Box',
                    'objectTaskMetrics_' + group,
                    rect(
                        wideMetrics ? group * (panelWidth + 20) : 0,
                        y + (wideMetrics ? 0 : group * 122),
                        panelWidth,
                        110
                    ),
                    {
                        background: 'panel',
                        children: [
                            node(
                                'Box',
                                'metricDivider_' + group + '_0',
                                rect(16 + cell + 6, 34, 1, 42),
                                { background: 'separator' }
                            ),
                            node(
                                'Box',
                                'metricDivider_' + group + '_1',
                                rect(16 + 2 * (cell + 14) - 8, 34, 1, 42),
                                { background: 'separator' }
                            ),
                            ...values
                                .slice(group * 3, group * 3 + 3)
                                .map(([title, value, color], index) =>
                                    metric(
                                        'objectTaskMetric_' +
                                            (group * 3 + index),
                                        title,
                                        value,
                                        rect(
                                            16 + index * (cell + 14),
                                            30,
                                            cell,
                                            50
                                        ),
                                        color,
                                        language
                                    )
                                )
                        ]
                    }
                )
            );
        y += (wideMetrics ? 110 : 232) + 12;
        const groupY = y,
            groupWidth = width >= 860 ? (width - 12) / 2 : width;
        chips(
            'objectStatusGroups',
            'TASKS BY STATUS',
            'system-activity',
            model.task_statuses || [],
            'status',
            0,
            groupWidth
        );
        const statusBottom = y;
        if (width >= 860) y = groupY;
        chips(
            'objectProcessGroups',
            'TASKS BY PROCESS',
            'workflow',
            model.task_processes || [],
            'process',
            width >= 860 ? groupWidth + 12 : 0,
            groupWidth
        );
        y = Math.max(y, statusBottom);
        const participants = (model.participants || []).map((record) => {
            const value = Object.assign({}, record);
            if (!metrics.canViewCosts) delete value.cost;
            return value;
        });
        rows(
            'objectParticipants',
            'PEOPLE AND WORK HOURS',
            'group',
            'person',
            participants,
            'No participants found'
        );
        rows(
            'objectTasks',
            'TASKS',
            'task',
            'task',
            model.tasks || [],
            'No tasks for this sObject'
        );
    } else if (model.page === 'notes')
        rows(
            'objectNotes',
            'OBJECT AND TASK NOTES',
            'notes',
            'note',
            model.notes || [],
            'No object or task notes'
        );
    else if (model.page === 'children') {
        chips(
            'objectChildTypes',
            'CHILD TYPES',
            'account-tree',
            model.child_types || []
        );
        rows(
            'objectChildren',
            'CHILDREN',
            'account-tree',
            'child',
            model.children || [],
            'No related children'
        );
    }
    return { nodes, height: Math.max(0, y - 12) };
}
