import { translate } from '../../core/strings.mjs';
import { node, rect, label } from '../../core/frame.mjs';
import { textStyles, spacing } from '../../core/foundation.mjs';
import * as Chart from '../../controls/charts/chart.ui.mjs';
import { buttonWidth } from '../../controls/buttons/metrics.mjs';

export function presentationOptions(options = {}, attributes = {}) {
    const result = Object.assign({}, options);
    for (const key of ['value_icon', 'value_style', 'value_text_style'])
        if (Object.prototype.hasOwnProperty.call(attributes, key))
            result[key] = attributes[key];
    return result;
}

const valueFonts = {
    heading: { role: 'title', size: textStyles.title, weight: 600 },
    small: { role: 'secondary', size: textStyles.secondary, weight: 400 },
    body: { role: 'body', size: textStyles.body, weight: 0 }
};

export function valueFont(options = {}) {
    return Object.prototype.hasOwnProperty.call(
        valueFonts,
        options.value_text_style
    )
        ? valueFonts[options.value_text_style]
        : valueFonts.body;
}

export function valuePresentation(field, options = {}) {
    const badge = options.value_style
        ? options.value_style === 'badge'
        : field === 'duration';
    const icon = Object.prototype.hasOwnProperty.call(options, 'value_icon')
        ? options.value_icon
        : badge && field === 'duration'
          ? 'clock'
          : '';
    return badge || icon
        ? {
              badge,
              icon,
              align: alignment(options),
              value_text_style: options.value_text_style || ''
          }
        : null;
}

export function valueLabel(text, width, height, presentation) {
    text = String(text ?? '');
    const font = valueFont(presentation),
        icon = presentation.icon || '',
        h = Math.max(0, Math.min(30, height)),
        w = Math.min(
            Math.max(0, width - 12),
            buttonWidth((text.length * 7 * font.size) / textStyles.body, !!icon)
        ),
        left = icon ? 36 : 12;
    const children = [
        label(
            'tableValueLabel',
            rect(left, 0, Math.max(0, w - left - 12), h),
            text,
            { fontRole: font.role, weight: font.weight || 400 }
        )
    ];
    if (icon)
        children.unshift(
            node('Icon', 'tableValueIcon', rect(12, (h - 16) / 2, 16, 16), {
                icon,
                color: 'action'
            })
        );
    const x =
        presentation.align === 'left'
            ? 6
            : presentation.align === 'right'
              ? width - w - 6
              : (width - w) / 2;
    return {
        nodes: [
            node(
                'Box',
                'tableValueBadge',
                rect(Math.max(0, x), (height - h) / 2, w, h),
                {
                    background: presentation.badge
                        ? 'surfaceContainerHigh'
                        : undefined,
                    border: presentation.badge ? 'outlineVariant' : undefined,
                    radius: 4,
                    children
                }
            )
        ]
    };
}

export function relatedLabel(text, options = {}) {
    text = String(text ?? '').trim();
    const count =
        String(options.label || '').includes('@COUNT(') &&
        text.match(/^(\d+)\s+(.+)$/);
    return count
        ? count[2].charAt(0).toUpperCase() + count[2].slice(1) + ' ' + count[1]
        : text;
}

const actions = {
    sobject_detail: ['search', 'Open details'],
    checkin: ['upload', 'Check-in'],
    explorer: ['folder-open', 'Open folder'],
    file_list: ['inventory-2', 'Open files'],
    metadata: ['description', 'Open metadata'],
    delete: ['delete', 'Delete sObject']
};

export const metrics = {
    bodyFont: textStyles.body,
    taskWidth: 107,
    taskGap: 4,
    taskMenu: 32,
    taskPreviewWidth: 128,
    taskMaximumHeight: 88,
    taskDatesHeight: 76,
    taskHeading: 15,
    noteHeight: 26,
    noteGap: 2,
    noteMargin: 7,
    action: 28,
    previewInset: 8
};

export const status = { foregroundMix: 0.45 };

export function alignment(options = {}) {
    const value = options.justify || options.align;
    return ['left', 'right', 'center'].includes(value) ? value : 'center';
}

export function completionGroups(count, width, height) {
    const rowHeight = 18,
        gap = 4;
    const contentHeight = Math.max(0, count * (rowHeight + gap) - gap);
    const gutter = contentHeight > height ? 16 : 0;
    return {
        rowHeight,
        gap,
        contentHeight,
        gutter,
        width: Math.max(0, width - gutter)
    };
}

export function action(kind, language) {
    const source = actions[kind];
    return source
        ? {
              icon: source[0],
              label: translate(source[1], language),
              destructive: kind === 'delete'
          }
        : null;
}

export function text(cell, fallback, language) {
    if (cell.error)
        return (
            translate('Cell calculation failed', language) + ': ' + cell.error
        );
    if (cell.label) return translate(cell.label, language, cell.parameters);
    const value = cell.text === undefined ? fallback : cell.text;
    return value == null
        ? ''
        : typeof value === 'object'
          ? JSON.stringify(value)
          : String(value);
}

export function textRole(cell) {
    if (cell.error || cell.negative || cell.urgency === 'critical')
        return 'error';
    if (cell.urgency === 'warning_1' || cell.urgency === 'warning_2')
        return 'yellow';
    return 'primaryText';
}

export function taskLayout(count, width, height) {
    const stride = metrics.taskWidth + metrics.taskGap;
    const capacity = Math.max(
        0,
        Math.floor((width + metrics.taskGap) / stride)
    );
    const overflow = count === 0 || count > capacity;
    const visible = Math.max(
        0,
        Math.min(
            count,
            Math.floor(
                (width - (overflow ? metrics.taskMenu : 0) + metrics.taskGap) /
                    stride
            )
        )
    );
    const cardHeight = Math.max(
        0,
        Math.min(metrics.taskMaximumHeight, height - 2)
    );
    const dates = cardHeight >= metrics.taskDatesHeight;
    return {
        overflow,
        visible,
        width: metrics.taskWidth,
        gap: metrics.taskGap,
        visibleWidth: Math.max(0, visible * stride - metrics.taskGap),
        previewWidth: Math.max(
            metrics.taskWidth,
            count * stride - metrics.taskGap
        ),
        cardHeight,
        dates,
        editorHeight: Math.max(
            10,
            Math.min(24, (cardHeight - (dates ? 36 : 21)) / 2)
        )
    };
}

export function taskCardLayout(height, expanded = false, style) {
    if (!expanded)
        return Object.assign(taskLayout(1, 0, height), {
            headingHeight: metrics.taskHeading,
            datesHeight: 14,
            padding: 2,
            gap: 1
        });
    const padding = spacing.tight,
        gap = spacing.text,
        editorHeight = 20,
        headingHeight = 16,
        datesHeight = 14;
    return {
        dates: true,
        editorHeight,
        headingHeight,
        datesHeight,
        padding,
        gap,
        cardHeight:
            padding * 2 +
            headingHeight +
            editorHeight * 2 +
            datesHeight +
            gap * 3
    };
}

export function taskPreviewLayout(count, viewportWidth, viewportHeight, style) {
    const card = taskCardLayout(0, true, style),
        padding = spacing.content,
        gap = spacing.compact,
        footerHeight = 36,
        scrollWidth = 16,
        availableWidth = Math.max(0, viewportWidth - 16),
        columns = Math.max(
            1,
            Math.min(
                3,
                Math.ceil(Math.sqrt(count)),
                Math.floor(
                    (availableWidth - padding * 2 - scrollWidth + gap) /
                        (metrics.taskPreviewWidth + gap)
                )
            )
        ),
        rows = Math.ceil(count / columns),
        contentWidth = columns * metrics.taskPreviewWidth + (columns - 1) * gap,
        contentHeight = Math.max(0, rows * card.cardHeight + (rows - 1) * gap),
        height = Math.max(
            0,
            Math.min(
                viewportHeight - 16,
                Math.min(contentHeight, card.cardHeight * 3 + gap * 2) +
                    padding * 2 +
                    footerHeight
            )
        ),
        vertical = contentHeight > height - padding * 2 - footerHeight;
    return {
        cardWidth: metrics.taskPreviewWidth,
        cardHeight: card.cardHeight,
        contentWidth,
        contentHeight,
        columns,
        rows,
        gap,
        footerHeight,
        padding,
        width: Math.max(
            0,
            Math.min(
                availableWidth,
                contentWidth + padding * 2 + (vertical ? scrollWidth : 0)
            )
        ),
        height,
        vertical
    };
}

export function taskCardsHovered(x, y, inlineWidth, height) {
    return x >= 0 && x < inlineWidth && y >= 0 && y < height;
}

export function previewSize(width, height) {
    return Math.max(0, Math.min(width, height) - metrics.previewInset);
}

export function assigneeLabel(task, language) {
    return task.assigned
        ? (task.assignedIdentity && task.assignedIdentity.displayName) ||
              task.assignedLabel ||
              task.assigned
        : translate('Not assigned', language);
}

export function taskDate(value, simple) {
    const date = value ? String(value).slice(0, 10) : '—';
    return simple && date.length === 10 ? date.slice(5) : date;
}

export function taskDateRange(task, language) {
    if (
        !task.bidStart &&
        !task.bidEnd &&
        !task.bidStartLabel &&
        !task.bidEndLabel
    )
        return translate('Not set', language);
    const start =
        task.simpleDates === undefined && task.bidStartLabel
            ? task.bidStartLabel
            : taskDate(task.bidStart, task.simpleDates);
    const end =
        task.simpleDates === undefined && task.bidEndLabel
            ? task.bidEndLabel
            : taskDate(task.bidEnd, task.simpleDates);
    return start + ' – ' + end;
}

export function processProgress(task, width, height, language) {
    const summary = task.progress || {},
        ready = summary.state === 'ready',
        total = Math.max(0, Number(summary.total) || 0),
        complete = Math.max(0, Math.min(total, Number(summary.complete) || 0)),
        text = ready ? complete + '/' + total : 'N/A',
        chart = Chart.geometry(
            { type: 'donut', values: [complete, total - complete] },
            width,
            height
        ),
        radius = Math.max(0, Math.min(width, height) / 2 - 2);
    Object.assign(chart, {
        cx: width / 2,
        cy: height / 2,
        radius,
        inner: Math.max(0, radius - 4),
        marks: chart.marks.slice(0, 1)
    });
    if (/^#[0-9a-f]{6}([0-9a-f]{2})?$/i.test(summary.color || ''))
        chart.marks[0].color = summary.color;
    const children = ready
        ? [
              node('Chart', 'processProgressRing', rect(0, 0, width, height), {
                  chart,
                  labels: [translate('Completed', language)],
                  text,
                  language,
                  focusable: false
              })
          ]
        : [];
    children.push(
        label(
            'processProgressCount',
            rect(
                width / 2 - Math.max(24, chart.inner),
                height / 2 - 10,
                Math.max(48, chart.inner * 2),
                20
            ),
            text,
            {
                fontRole: 'caption',
                weight: 600,
                align: 'center',
                color: ready ? 'primaryText' : 'secondaryText'
            }
        )
    );
    return {
        width,
        height,
        nodes: [
            node('Action', 'processProgressOpen', rect(0, 0, width, height), {
                text: translate('Related tasks', language),
                enabled: true,
                radius: 4,
                action: { type: 'inspect' },
                children
            })
        ]
    };
}

export function taskEditable(task, field, editable = true) {
    if (!editable || task.processType === 'progress') return false;
    if (field === 'assigned') return task.editAssigned !== false;
    if (field === 'bid_start_date' || field === 'bid_end_date')
        return task.editDates !== false;
    return true;
}

export function message(cell, width, height, language) {
    const inner = Math.max(0, width - 16);
    const heading = [
        cell.author || '',
        cell.messageLabel ? translate(cell.messageLabel, language) : ''
    ]
        .filter(Boolean)
        .join(' · ');
    const top = heading ? 20 : 0;
    const progress = cell.progress == null ? 0 : 14;
    const bodyHeight = Math.max(20, height - top - progress - 8);
    const children = [
        label('tableMessageAuthor', rect(6, 0, inner, top), heading, {
            fontRole: 'caption',
            color: 'secondaryText',
            tooltip: heading
        }),
        label(
            'tableMessageBody',
            rect(6, top, inner, bodyHeight),
            cell.text || '',
            { tooltip: cell.text || '', wrap: true }
        )
    ];
    if (progress) {
        const percent = Math.max(0, Math.min(100, Number(cell.progress) || 0));
        children.push(
            node(
                'Box',
                'tableMessageTrack',
                rect(6, top + bodyHeight + 3, inner, 5),
                { background: 'surfaceContainerHigh', radius: 2 }
            ),
            node(
                'Box',
                'tableMessageProgress',
                rect(6, top + bodyHeight + 3, (inner * percent) / 100, 5),
                { background: 'action', radius: 2 }
            )
        );
    }
    return {
        nodes: [
            node('Scroll', 'tableMessageScroll', rect(0, 0, width, height), {
                contentHeight: top + bodyHeight + progress,
                scrollbarId: 'tableMessageScrollBar',
                children
            })
        ]
    };
}

export function checked(cell, value) {
    return cell.checked !== undefined
        ? !!cell.checked
        : ['1', 'true', 'yes', 'on'].indexOf(String(value).toLowerCase()) >= 0;
}

export function link(value, server) {
    const href = String(value || '').trim();
    if (!href || /[\s\\\u0000-\u001f\u007f]/.test(href)) return '';
    if (/^(https?:|mailto:)/i.test(href)) return href;
    if (href[0] !== '/' || href[1] === '/') return '';
    if (server === undefined) return href;
    const address = String(server || '').trim();
    if (!address || /[\s\\@]/.test(address)) return '';
    const base = address.indexOf('://') < 0 ? 'http://' + address : address;
    const origin = base.match(/^https?:\/\/[^/?#]+/i);
    return origin ? origin[0] + href : '';
}

export function taskSummary(tasks, width, height) {
    const columns = Math.max(1, Math.floor(Math.max(0, width - 16) / 54));
    const cellWidth = Math.max(1, (width - 16) / columns);
    const contentHeight = Math.ceil(tasks.length / columns) * 44;
    const children = [];
    for (let index = 0; index < tasks.length; index++) {
        const task = tasks[index];
        children.push(
            node(
                'Action',
                'tableTaskSummary_' + index,
                rect(
                    (index % columns) * cellWidth,
                    Math.floor(index / columns) * 44,
                    cellWidth - 3,
                    41
                ),
                {
                    text: task.processLabel || task.process || task.context,
                    normalColor: 'surfaceContainerHigh',
                    action: { type: 'inspect', index },
                    children: [
                        node(
                            'Box',
                            'tableTaskSummaryRail_' + index,
                            rect(0, 0, 3, 41),
                            {
                                background:
                                    task.statusColor ||
                                    task.processColor ||
                                    'action',
                                radius: 1.5
                            }
                        ),
                        label(
                            'tableTaskSummaryLabel_' + index,
                            rect(3, 2, cellWidth - 9, 19),
                            task.processLabel || task.process || task.context,
                            { fontRole: 'caption', align: 'center' }
                        ),
                        label(
                            'tableTaskSummaryStatus_' + index,
                            rect(3, 21, cellWidth - 9, 17),
                            task.status || '',
                            { fontRole: 'caption', align: 'center' }
                        )
                    ]
                }
            )
        );
    }
    return {
        nodes: [
            node(
                'Scroll',
                'tableTaskSummaryScroll',
                rect(0, 0, width, height),
                {
                    contentHeight,
                    scrollbarId: 'tableTaskSummaryScrollBar',
                    children
                }
            )
        ]
    };
}

export function keyValues(entries, width, height, language) {
    const inner = Math.max(0, width - 16),
        titleWidth = inner * 0.38;
    const children = [];
    for (let index = 0; index < entries.length; index++) {
        const entry = entries[index];
        let title =
            entry.translate || entry.translateTitle
                ? translate(entry.title, language)
                : entry.title;
        if (entry.period) title += ' · ' + translate(entry.period, language);
        const value = entry.translate
            ? translate(entry.value, language)
            : entry.value;
        children.push(
            label(
                'tableFieldTitle_' + index,
                rect(6, index * 24, titleWidth - 6, 24),
                title,
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
        children.push(
            label(
                'tableFieldValue_' + index,
                rect(titleWidth + 4, index * 24, inner - titleWidth - 4, 24),
                value,
                { fontRole: 'caption', color: entry.color || 'primaryText' }
            )
        );
    }
    return {
        nodes: [
            node('Scroll', 'tableFieldsScroll', rect(0, 0, width, height), {
                contentHeight: entries.length * 24,
                scrollbarId: 'tableFieldsScrollBar',
                children
            })
        ]
    };
}
