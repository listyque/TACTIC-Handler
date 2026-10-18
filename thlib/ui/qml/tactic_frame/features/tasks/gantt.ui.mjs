import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as State from './gantt.state.mjs';

export const batchActions = [
    { title: 'Shift one day earlier', action: 'shift', amount: -1 },
    { title: 'Shift one day later', action: 'shift', amount: 1 },
    { title: 'Align start dates', action: 'align-start', amount: 1 },
    { title: 'Align deadlines', action: 'align-end', amount: 1 },
    { title: 'Schedule sequentially', action: 'sequence', amount: 1 },
    { title: 'Extend by one day', action: 'extend', amount: 1 },
    { title: 'Shorten by one day', action: 'shorten', amount: 1 }
];
export const scales = [
    { label: 'Fit range', value: 'auto' },
    { label: 'Days', value: 'days' },
    { label: 'Weeks', value: 'weeks' },
    { label: 'Months', value: 'months' },
    { label: 'Quarters', value: 'quarters' }
];
const box = (id, bounds, background, extra = {}) =>
    node('Box', id, bounds, Object.assign({ background, radius: 0 }, extra));

export function heading(model, width, language) {
    const t = (text) => translate(text, language);
    return {
        nodes: [
            node('Icon', 'ganttHeadingIcon', rect(10, 19, 16, 16), {
                icon: 'gantt',
                color: 'action'
            }),
            label(
                'ganttHeadingTitle',
                rect(34, 10, width - 42, 17),
                t('Task schedule').toUpperCase(),
                { fontRole: 'secondary', weight: 600 }
            ),
            label(
                'ganttHeadingCount',
                rect(34, 29, width - 42, 15),
                translate(
                    '{scheduled} scheduled · {unscheduled} unscheduled',
                    language,
                    {
                        scheduled: model.scheduled || 0,
                        unscheduled: model.unscheduled || 0
                    }
                ),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        ]
    };
}

export function section(record, width, language) {
    const scheduled = record.ganttSection === 'scheduled';
    return {
        nodes: [
            box(
                'ganttSectionSurface',
                rect(0, 0, width, State.metrics.section),
                'workspace'
            ),
            node('Icon', 'ganttSectionIcon', rect(9, 7, 14, 14), {
                icon: scheduled ? 'schedule' : 'warning',
                color: scheduled ? 'action' : 'yellow'
            }),
            label(
                'ganttSectionText',
                rect(30, 6, width - 38, 16),
                translate(
                    scheduled ? 'Scheduled tasks' : 'Unscheduled tasks',
                    language
                ).toUpperCase(),
                { fontRole: 'caption', weight: 600, color: 'secondaryText' }
            )
        ]
    };
}

export function group(record, width, collapsed) {
    return {
        nodes: [
            box(
                'ganttGroupSurface',
                rect(0, 0, width, State.metrics.group),
                'surfaceContainerLow'
            ),
            node('Icon', 'ganttGroupChevron', rect(8, 7, 13, 13), {
                icon: collapsed ? 'chevron-right' : 'expand-more',
                color: 'secondaryText'
            }),
            box(
                'ganttGroupDot',
                rect(27, 10, 7, 7),
                record.groupColor || 'action',
                { radius: 3.5 }
            ),
            label(
                'ganttGroupLabel',
                rect(40, 5.5, width - 80, 16),
                String(record.group || '').toUpperCase(),
                { fontRole: 'caption', weight: 600 }
            ),
            label(
                'ganttGroupCount',
                rect(width - 35, 5.5, 27, 16),
                String(record.groupCount || 0),
                { fontRole: 'caption', color: 'secondaryText', align: 'right' }
            )
        ]
    };
}

export function taskLabel(record, width, language) {
    const blocked = !!record.busy;
    const trailing = record.ganttWarning ? 42 : 24;
    return {
        nodes: [
            box(
                'ganttLabelSurface',
                rect(0, 0, width, State.metrics.row),
                'surfaceContainerLow',
                { opacity: 0.94 }
            ),
            ...(record.selected || record.dirty
                ? [
                      box('ganttActiveMark', rect(0, 6, 2, 38), 'action', {
                          radius: 1
                      })
                  ]
                : []),
            node('CheckBox', 'ganttTaskCheck', rect(5, 11.5, 27, 27), {
                label:
                    translate('Select task', language) +
                    ' ' +
                    record.parentTitle +
                    ' ' +
                    record.processLabel,
                checked: !!record.checked,
                enabled: !blocked,
                hideLabel: true,
                action: { type: 'select', key: record.taskCode }
            }),
            node('Preview', 'ganttTaskPreview', rect(39, 10, 30, 30), {
                source: record.parentPreviewUrl || '',
                initials: String(record.parentTitle || '')
                    .slice(0, 2)
                    .toUpperCase(),
                icon: 'sobject',
                accent: record.processColor || 'action',
                round: false,
                outlined: false
            }),
            label(
                'ganttTaskTitle',
                rect(76, 9, width - 84 - trailing, 17),
                record.parentTitle || '',
                { fontRole: 'secondary', weight: 600 }
            ),
            label(
                'ganttTaskSubtitle',
                rect(76, 27, width - 84 - trailing, 15),
                (record.processLabel || '') +
                    (record.assignedLabel
                        ? '  ·  ' + record.assignedLabel
                        : ''),
                { fontRole: 'caption', color: 'secondaryText' }
            ),
            node(
                'Action',
                'ganttTaskActivate',
                rect(72, 0, width - 80 - trailing, 50),
                {
                    text: record.parentTitle || '',
                    enabled: !blocked,
                    action: { type: 'activate', key: record.taskCode },
                    doubleAction: { type: 'object', key: record.taskCode }
                }
            ),
            button(
                'ganttTaskEdit',
                rect(width - trailing, 14, 22, 22),
                '',
                'edit',
                { type: 'edit', key: record.taskCode },
                !blocked,
                {
                    label: translate('Edit schedule', language),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 14,
                    opacity: 1
                }
            ),
            ...(record.ganttWarning
                ? [
                      node(
                          'Icon',
                          'ganttTaskWarning',
                          rect(width - 17, 18.5, 13, 13),
                          {
                              icon: 'warning',
                              color: 'yellow',
                              toolTip: record.warningText || record.ganttWarning
                          }
                      )
                  ]
                : [])
        ]
    };
}

export function scheduleBar(record, width, language) {
    const progress = Math.max(0, Math.min(100, record.progress || 0));
    const color = record.ganttColor || 'action';
    const h = State.metrics.bar;
    return {
        nodes: [
            box('ganttBarBackground', rect(0, 0, width, h), color, {
                opacity: record.editing ? 0.42 : 0.3,
                radius: record.radius || 8
            }),
            box(
                'ganttBarProgress',
                rect(0, 0, (width * progress) / 100, h),
                color,
                { opacity: 0.88, radius: record.radius || 8 }
            ),
            label(
                'ganttBarLabel',
                rect(
                    record.progressSupported ? 30 : 7,
                    6,
                    width - (record.progressSupported ? 37 : 14),
                    15
                ),
                record.editing
                    ? record.startLabel + ' — ' + record.endLabel
                    : (record.processLabel || '') + '  ' + progress + '%',
                { fontRole: 'caption', weight: 600 }
            ),
            ...[-8, width - 4].map((x, index) =>
                box(
                    index ? 'ganttEndGrip' : 'ganttStartGrip',
                    rect(x, 2.5, 12, 22),
                    'surfaceContainerHighest',
                    {
                        radius: 5,
                        border: 'primaryText',
                        borderWidth: 1,
                        children: [
                            box(
                                'ganttGripLine' + index,
                                rect(5, 6, 2, 10),
                                'primaryText',
                                { radius: 1 }
                            )
                        ]
                    }
                )
            )
        ]
    };
}

export function grid(range, day, x, width, height) {
    if (!range.rangeStart) return { nodes: [] };
    const nodes = [];
    for (const span of range.weekends || []) {
        const left = span.offsetDay * day - x,
            size = span.durationDays * day;
        if (left + size >= 0 && left <= width)
            nodes.push(
                box(
                    'ganttWeekend' + span.offsetDay,
                    rect(left, 0, size, height),
                    'surfaceContainerHigh',
                    { opacity: 0.22 }
                )
            );
    }
    if (day >= 16) {
        const first = Math.max(0, Math.floor(x / day) - 1);
        const last = Math.min(
            range.days || 1,
            Math.ceil((x + width) / day) + 1
        );
        for (let offset = first; offset <= last; offset++) {
            const level = State.boundary(range.rangeStart, offset);
            nodes.push(
                box(
                    'ganttBoundary' + offset,
                    rect(offset * day - x, 0, level === 2 ? 2 : 1, height),
                    level ? 'outline' : 'separator',
                    { opacity: level === 2 ? 0.52 : level === 1 ? 0.38 : 0.24 }
                )
            );
        }
    } else
        for (const tick of State.ticks(range, day, x, width))
            nodes.push(
                box(
                    'ganttBoundary' + tick.offsetDay,
                    rect(
                        tick.offsetDay * day - x,
                        0,
                        tick.major ? 2 : 1,
                        height
                    ),
                    tick.major ? 'outline' : 'separator',
                    { opacity: tick.major ? 0.28 : 0.38 }
                )
            );
    for (const marker of range.milestones || [])
        nodes.push(
            box(
                'ganttMilestoneLine' + marker.code,
                rect(marker.offsetDay * day - x, 0, 3, height),
                'tertiary',
                { opacity: 0.72 }
            )
        );
    if (range.todayDay >= 0)
        nodes.push(
            box(
                'ganttTodayLine',
                rect(range.todayDay * day - x, 0, 2, height),
                'error',
                { opacity: 0.52 }
            )
        );
    return { nodes };
}

export function footer(model, width, language) {
    const t = (text) => translate(text, language),
        nodes = [];
    let x = width - (model.hostWidth || 0) - 8;
    function action(id, text, icon, type, enabled = true, extra = {}) {
        x -= 28;
        nodes.push(
            button(
                id,
                rect(x, 15, 28, 28),
                '',
                icon,
                { type },
                enabled,
                Object.assign(
                    {
                        label: t(text),
                        iconOnly: true,
                        iconAction: true,
                        iconSize: 16
                    },
                    extra
                )
            )
        );
        x -= 5;
    }
    action(
        'ganttToday',
        'Center today',
        'schedule',
        'today',
        model.todayDay >= 0
    );
    if (width >= 700) {
        action('ganttZoomIn', 'Zoom in', 'zoom-in', 'zoom-in', model.zoom < 5);
        x -= 58;
        nodes.push(
            button(
                'ganttScale',
                rect(x, 15, 58, 28),
                Math.round(model.zoom * 100) + '%',
                '',
                { type: 'scale' },
                true,
                { label: t('Timeline scale'), compact: true }
            )
        );
        x -= 5;
        action(
            'ganttZoomOut',
            'Zoom out',
            'zoom-out',
            'zoom-out',
            model.zoom > (model.minZoom || 0.15)
        );
    }
    if (width >= 520) {
        action(
            'ganttResource',
            'Group workload by assignee',
            'group',
            'resource',
            !model.busy,
            { highlighted: !!model.resourceMode }
        );
        action(
            'ganttWorking',
            'Working days only',
            'calendar-today',
            'working',
            !model.busy,
            { highlighted: !!model.workingDays }
        );
    }
    action(
        'ganttRedo',
        'Redo schedule change',
        'redo',
        'redo',
        !model.busy && model.canRedo
    );
    action(
        'ganttUndo',
        'Undo schedule change',
        'undo',
        'undo',
        !model.busy && model.canUndo
    );
    action('ganttOptions', 'Schedule options', 'more', 'options', !model.busy);
    nodes.unshift(
        box(
            'ganttFooterSurface',
            rect(0, 0, width, State.metrics.footer),
            'surfaceContainer'
        )
    );
    nodes.push(
        box('ganttFooterDivider', rect(0, 0, width, 1), 'outlineVariant')
    );
    if (x > 50)
        nodes.push(
            label(
                'ganttRange',
                rect(10, 21, x - 18, 16),
                (model.rangeStart || '') + '  —  ' + (model.rangeEnd || ''),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    return { nodes, height: State.metrics.footer };
}

// TACTIC depend_id is a link between existing task IDs. A hidden/unloaded or
// unscheduled predecessor is deliberately not guessed from process order.
export function dependencies(records, collapsed, day, x = 0, y = 0) {
    const rows = State.rows(records, collapsed).items.filter(
        (row) => row.kind === 'task'
    );
    const byId = {};
    for (const row of rows)
        if (row.record.taskId) byId[row.record.taskId] = row;
    const nodes = [];
    for (const target of rows) {
        const source = byId[target.record.dependencyId];
        if (
            !source ||
            source === target ||
            !source.record.ganttScheduled ||
            !target.record.ganttScheduled
        )
            continue;
        const from = State.bar(
            source.record.ganttStartDay,
            source.record.ganttDurationDays,
            day,
            x
        );
        const to = State.bar(
            target.record.ganttStartDay,
            target.record.ganttDurationDays,
            day,
            x
        );
        const startX = from.x + from.width,
            endX = to.x - 8;
        const startY = source.top + State.metrics.row / 2 - y;
        const endY = target.top + State.metrics.row / 2 - y;
        const bend = Math.max(startX + 12, endX - 12),
            id = target.key;
        nodes.push(
            box(
                'ganttDependencyOut' + id,
                rect(startX, startY, bend - startX, 1),
                'outline'
            )
        );
        nodes.push(
            box(
                'ganttDependencyVertical' + id,
                rect(bend, Math.min(startY, endY), 1, Math.abs(endY - startY)),
                'outline'
            )
        );
        nodes.push(
            box(
                'ganttDependencyIn' + id,
                rect(Math.min(bend, endX), endY, Math.abs(endX - bend), 1),
                'outline'
            )
        );
        nodes.push(
            node(
                'Icon',
                'ganttDependencyArrow' + id,
                rect(endX - 5, endY - 6, 12, 12),
                {
                    icon: 'arrow-right',
                    color: 'outline'
                }
            )
        );
    }
    return { nodes };
}

export function dateLabel(value, language, mode = 'compact') {
    if (!value) return '—';
    const year = value.slice(0, 4),
        month = Number(value.slice(5, 7)),
        day = Number(value.slice(8, 10));
    const names =
        language === 'ru'
            ? [
                  'янв.',
                  'февр.',
                  'мар.',
                  'апр.',
                  'мая',
                  'июн.',
                  'июл.',
                  'авг.',
                  'сент.',
                  'окт.',
                  'нояб.',
                  'дек.'
              ]
            : [
                  'Jan',
                  'Feb',
                  'Mar',
                  'Apr',
                  'May',
                  'Jun',
                  'Jul',
                  'Aug',
                  'Sep',
                  'Oct',
                  'Nov',
                  'Dec'
              ];
    if (mode === 'days') return String(day);
    if (mode === 'months') return names[month - 1] + ' ' + year;
    if (mode === 'quarters')
        return translate('Q{quarter} {year}', language, {
            quarter: Math.ceil(month / 3),
            year
        });
    return language === 'ru'
        ? day + ' ' + names[month - 1]
        : names[month - 1] + ' ' + day;
}

export function timelineHeading(range, day, x, width, language) {
    const nodes = [];
    for (const tick of State.ticks(range, day, x, width)) {
        const left = tick.offsetDay * day - x;
        const size = Math.max(48, (tick.spanDays || 1) * day);
        nodes.push(
            box(
                'ganttTickLine' + tick.date,
                rect(left, 0, tick.major ? 2 : 1, 54),
                tick.major ? 'outline' : 'separator',
                { opacity: tick.major ? 0.55 : 0.7 }
            )
        );
        // The original timeline deliberately uses tiny labels; this is not a house-control text role.
        const text = label(
            'ganttTick' + tick.date,
            rect(left + 6, 21, size - 8, 12),
            dateLabel(tick.date, language, State.tickMode(day)),
            {
                fontRole: tick.major ? 'timelineMajorTick' : 'timelineTick',
                color: tick.major ? 'primaryText' : 'secondaryText',
                weight: tick.major ? 600 : 400
            }
        );
        nodes.push(text);
    }
    for (const marker of range.milestones || []) {
        const left = marker.offsetDay * day - x;
        const size = Math.min(150, Math.max(76, marker.label.length * 6 + 43));
        if (left + size < 0 || left > width) continue;
        nodes.push(
            box(
                'ganttMarkerSurface' + marker.code,
                rect(left, 2, size, 22),
                'tertiaryContainer',
                { radius: 6, border: 'tertiary', borderWidth: 1 }
            )
        );
        nodes.push(
            node(
                'Icon',
                'ganttMarkerIcon' + marker.code,
                rect(left + 6, 6.5, 13, 13),
                { icon: 'milestone', color: 'tertiary' }
            )
        );
        nodes.push(
            label(
                'ganttMarkerLabel' + marker.code,
                rect(left + 23, 5.5, size - 57, 15),
                marker.label,
                { fontRole: 'caption', weight: 600 }
            )
        );
        nodes.push(
            label(
                'ganttMarkerCompletion' + marker.code,
                rect(left + size - 30, 5.5, 26, 15),
                String(State.clamp(Number(marker.completion) || 0, 0, 100)) +
                    '%',
                { fontRole: 'caption', color: 'tertiary', align: 'right' }
            )
        );
        nodes.push(
            box(
                'ganttMarkerLine' + marker.code,
                rect(left, 24, 3, 30),
                'tertiary',
                { opacity: 0.94 }
            )
        );
        nodes.push(
            node(
                'Action',
                'ganttMarkerOpen' + marker.code,
                rect(left, 2, size, 22),
                {
                    text: marker.label + ' · ' + marker.dueDate,
                    action: { type: 'milestone', value: marker.code }
                }
            )
        );
    }
    if (range.todayDay >= 0) {
        const left = range.todayDay * day - x;
        nodes.push(
            box('ganttHeaderToday', rect(left, 0, 3, 54), 'error', {
                opacity: 0.82
            })
        );
        nodes.push(
            label(
                'ganttTodayLabel',
                rect(left - 64, 37, 60, 15),
                translate('TODAY', language),
                {
                    fontRole: 'caption',
                    color: 'error',
                    weight: 600,
                    align: 'right'
                }
            )
        );
    }
    return { nodes };
}

export function overviewGeometry(viewport, timeline, x) {
    const width = Math.min(
        viewport,
        Math.max(28, (viewport * viewport) / timeline)
    );
    return {
        width,
        x:
            timeline > viewport
                ? (x / (timeline - viewport)) * Math.max(0, viewport - width)
                : 0
    };
}

export function overview(range, labels, width, timeline, x, language) {
    const viewport = Math.max(1, width - labels),
        nodes = [];
    nodes.push(
        box(
            'ganttOverviewSurface',
            rect(0, 0, width, 30),
            'surfaceContainerLow'
        )
    );
    nodes.push(
        node('Icon', 'ganttOverviewIcon', rect(10, 9, 12, 12), {
            icon: 'visibility',
            color: 'secondaryText'
        })
    );
    nodes.push(
        label(
            'ganttOverviewLabel',
            rect(28, 7.5, labels - 36, 15),
            range.warnings
                ? translate('{count} schedule warnings', language, {
                      count: range.warnings
                  })
                : translate('Project overview', language),
            {
                fontRole: 'caption',
                color: range.warnings ? 'yellow' : 'secondaryText'
            }
        )
    );
    nodes.push(
        box(
            'ganttOverviewTrack',
            rect(labels, 10, viewport, 10),
            'surfaceContainerHigh',
            { radius: 5, border: 'outlineVariant', borderWidth: 1 }
        )
    );
    for (const [index, span] of (range.overview || []).entries())
        nodes.push(
            box(
                'ganttOverviewSpan' + index,
                rect(
                    labels +
                        (span.startDay / Math.max(1, range.days)) * viewport,
                    13.5,
                    Math.max(
                        2,
                        (span.durationDays / Math.max(1, range.days)) * viewport
                    ),
                    3
                ),
                span.warning ? 'yellow' : span.color || 'action',
                { opacity: 0.62, radius: 1.5 }
            )
        );
    for (const marker of range.milestones || [])
        nodes.push(
            box(
                'ganttOverviewMarker' + marker.code,
                rect(
                    labels +
                        (marker.offsetDay / Math.max(1, range.days)) * viewport,
                    10,
                    2,
                    10
                ),
                'tertiary',
                { opacity: 0.82 }
            )
        );
    if (range.todayDay >= 0)
        nodes.push(
            box(
                'ganttOverviewToday',
                rect(
                    labels +
                        (range.todayDay / Math.max(1, range.days)) * viewport,
                    10,
                    2,
                    10
                ),
                'error',
                { opacity: 0.68 }
            )
        );
    const thumb = overviewGeometry(viewport, timeline, x);
    nodes.push(
        box(
            'ganttOverviewThumb',
            rect(labels + thumb.x, 6, thumb.width, 18),
            'secondaryContainer',
            { radius: 6, border: 'action', borderWidth: 1 }
        )
    );
    return { nodes };
}

export function rowSurface(model, width) {
    return {
        nodes: [
            box(
                'ganttRowBackground',
                rect(0, 0, width, State.metrics.row),
                model.checked
                    ? 'secondaryContainer'
                    : model.selected
                      ? 'contentSelection'
                      : model.hovered
                        ? 'rowHover'
                        : 'transparent',
                { opacity: model.checked ? 0.55 : 1 }
            ),
            box(
                'ganttRowSeparator',
                rect(0, State.metrics.row - 1, width, 1),
                'separator'
            )
        ]
    };
}

export function band(kind, width, record = {}, collapsed = false) {
    return {
        nodes: [
            box(
                'gantt' + kind + 'Band',
                rect(
                    0,
                    0,
                    width,
                    kind === 'section'
                        ? State.metrics.section
                        : State.metrics.group
                ),
                kind === 'section' ? 'workspace' : 'surfaceContainerLow'
            ),
            ...(kind === 'group'
                ? [
                      node(
                          'Action',
                          'ganttGroupToggle',
                          rect(0, 0, width, State.metrics.group),
                          {
                              text: record.group || '',
                              role: 'button',
                              expanded: !collapsed,
                              action: {
                                  type: 'collapse',
                                  value: record.groupKey
                              }
                          }
                      )
                  ]
                : [])
        ]
    };
}

export function groupTimeline(record, day, collapsed, x = 0) {
    if (!record.ganttGroupDurationDays) return { nodes: [] };
    const width = Math.max(5, record.ganttGroupDurationDays * day - 2),
        height = collapsed ? 11 : 5;
    return {
        nodes: [
            box(
                'ganttGroupSummary',
                rect(
                    record.ganttGroupStartDay * day - x,
                    (State.metrics.group - height) / 2,
                    width,
                    height
                ),
                record.groupColor || 'action',
                {
                    radius: height / 2,
                    opacity: collapsed ? 0.55 : 0.34,
                    children: [
                        box(
                            'ganttGroupSummaryProgress',
                            rect(
                                0,
                                0,
                                (width * record.ganttGroupProgress) / 100,
                                height
                            ),
                            record.groupColor || 'action',
                            { radius: height / 2, opacity: 0.95 }
                        )
                    ]
                }
            )
        ]
    };
}

export function issue(record, width, language) {
    const text = translate(record.ganttIssue || '', language);
    const size = Math.max(0, Math.min(width - 20, text.length * 6 + 34));
    return {
        width: size,
        height: 30,
        nodes: [
            box(
                'ganttIssueSurface',
                rect(0, 0, size, 30),
                'surfaceContainerHigh',
                { radius: record.radius || 8 }
            ),
            node('Icon', 'ganttIssueIcon', rect(7, 8.5, 13, 13), {
                icon: 'warning',
                color: 'yellow'
            }),
            label(
                'ganttUnscheduledIssueLabel',
                rect(25, 7, size - 32, 16),
                text,
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        ]
    };
}

export function empty(width, height, loading, language) {
    return {
        nodes: [
            label(
                'ganttEmptyLabel',
                rect(10, Math.max(0, (height - 20) / 2), width - 20, 20),
                translate(
                    loading
                        ? 'Loading data…'
                        : 'No tasks match the current scope and filters',
                    language
                ),
                {
                    fontRole: 'secondary',
                    color: 'secondaryText',
                    align: 'center'
                }
            )
        ]
    };
}

export function options(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    for (const [index, title, type, checked] of [
        [0, 'Working days only', 'working', model.workingDays],
        [1, 'Group workload by assignee', 'resource', model.resourceMode]
    ])
        nodes.push(
            node(
                'CheckBox',
                'ganttOption' + type,
                rect(4, index * 32, width - 8, 28),
                {
                    text: tr(title),
                    checked: !!checked,
                    enabled: !model.busy,
                    action: { type }
                }
            )
        );
    nodes.push(
        node('Choice', 'ganttOptionScale', rect(4, 68, width - 8, 32), {
            label: tr('Timeline scale'),
            value: model.scale,
            options: scales.map((option) => ({
                value: option.value,
                label: tr(option.label)
            })),
            action: { type: 'scale-value' }
        })
    );
    let y = 108;
    for (const option of batchActions) {
        nodes.push(
            button(
                'ganttBatch' + option.action + option.amount,
                rect(0, y, width, 30),
                tr(option.title),
                '',
                {
                    type: 'batch',
                    operation: option.action,
                    amount: option.amount
                },
                !model.busy && model.checked > 0,
                { align: 'left' }
            )
        );
        y += 32;
    }
    nodes.push(
        button(
            'ganttDeleteSelectedTasksButton',
            rect(0, y + 4, width, 32),
            tr('Delete selected tasks'),
            'delete',
            { type: 'delete' },
            !model.busy && model.checked > 0 && !model.dirty,
            { destructive: true, align: 'left' }
        )
    );
    return { nodes, height: y + 40 };
}

export function scaleOptions(mode, width, language) {
    return {
        height: scales.length * 34,
        nodes: scales.map((option, index) =>
            button(
                'ganttScale' + option.value,
                rect(0, index * 34, width, 32),
                translate(option.label, language),
                '',
                { type: 'scale-value', value: option.value },
                true,
                { highlighted: mode === option.value, align: 'left' }
            )
        )
    };
}
