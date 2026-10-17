import { translate } from '../../core/strings.mjs';
import { node, rect, label } from '../../core/frame.mjs';
import { textStyles } from '../../core/foundation.mjs';

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
    taskMaximumHeight: 88,
    taskDatesHeight: 76,
    taskHeading: 15,
    noteHeight: 26,
    noteGap: 2,
    noteMargin: 7,
    action: 28,
    previewInset: 8
};

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
        const title =
            entry.translate || entry.translateTitle
                ? translate(entry.title, language)
                : entry.title;
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
