import { spacing } from '../../core/foundation.mjs';
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language);
    const nodes = [],
        enabled = !model.busy && !model.locked;
    nodes.push(
        button(
            'timesheetPrevious',
            rect(8, 7, 30, 30),
            tr('Previous week'),
            'chevron-left',
            { type: 'week', value: -1 },
            enabled,
            { iconOnly: true }
        )
    );
    nodes.push(
        node('DateChoice', 'timesheetWeek', rect(44, 6, 176, 32), {
            text: model.weekStart || '',
            label: tr('Week'),
            includeTime: false,
            allowClear: false,
            enabled,
            action: { type: 'date' }
        })
    );
    nodes.push(
        button(
            'timesheetNext',
            rect(226, 7, 30, 30),
            tr('Next week'),
            'chevron-right',
            { type: 'week', value: 1 },
            enabled,
            { iconOnly: true }
        )
    );
    let right = width - 7;
    for (const record of [
        ['timesheetRefresh', 'Refresh timesheet', 'refresh', 'refresh', true],
        ['timesheetReports', 'Open work reports', 'bar-chart', 'reports', true],
        [
            'timesheetCreate',
            model.canCreate
                ? 'Log time for the selected task'
                : 'Select a task before logging time',
            'add-alarm',
            'create',
            !!model.canCreate
        ]
    ]) {
        right -= 30;
        nodes.push(
            button(
                record[0],
                rect(right, width < 384 ? 44 : 7, 30, 30),
                tr(record[1]),
                record[2],
                { type: record[3] },
                enabled && record[4],
                { iconOnly: true }
            )
        );
        right -= 6;
    }
    let top = width < 384 ? 81 : 44;
    if (model.canManage) {
        nodes.push(
            node(
                'UserChoice',
                'timesheetUser',
                rect(8, top, Math.max(0, Math.min(260, width - 16)), 32),
                {
                    label: tr('Team member'),
                    value: model.login || '',
                    options: model.users || [],
                    enabled,
                    action: { type: 'user' }
                }
            )
        );
        top += 39;
    }
    if (model.selectedCount) {
        nodes.push(
            label(
                'timesheetSelection',
                rect(8, top, Math.max(0, width - 132), 30),
                tr('{count} selected').replace('{count}', model.selectedCount),
                { color: 'secondaryText' }
            )
        );
        let x = width - 116;
        for (const record of [
            ['approve', 'Approve selected entries', 'approval'],
            ['reject', 'Return selected entries to pending', 'undo'],
            ['clear', 'Clear selection', 'close']
        ]) {
            nodes.push(
                button(
                    'timesheetBulk-' + record[0],
                    rect(x, top, 30, 30),
                    tr(record[1]),
                    record[2],
                    { type: record[0] },
                    enabled,
                    { iconOnly: true }
                )
            );
            x += 36;
        }
        top += 37;
    }
    return { nodes, height: top };
}

export function summary(values, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        keys = ['logged', 'approved', 'pending', 'overtime'];
    const columns = width < 480 ? 2 : 4;
    const size = Math.max(0, (width - 7 * (columns - 1)) / columns);
    for (let index = 0; index < keys.length; index++) {
        const key = keys[index],
            x = (index % columns) * (size + 7),
            y = Math.floor(index / columns) * 59;
        nodes.push(
            node('Box', 'timesheetSummary-' + key, rect(x, y, size, 52), {
                background: 'surfaceContainerHigh',
                radius: 8
            })
        );
        nodes.push(
            label(
                'timesheetSummaryValue-' + key,
                rect(x + 4, y + 5, Math.max(0, size - 8), 24),
                String(values?.[key] || 0) + tr(' h'),
                { fontRole: 'bodyLarge', weight: 600, align: 'center' }
            )
        );
        nodes.push(
            label(
                'timesheetSummaryLabel-' + key,
                rect(x + 4, y + 30, Math.max(0, size - 8), 18),
                tr(key[0].toUpperCase() + key.slice(1)),
                { fontRole: 'caption', color: 'secondaryText', align: 'center' }
            )
        );
    }
    return { nodes, height: columns === 2 ? 111 : 52 };
}

export function entry(record, width, language) {
    const tr = (text) => translate(text, language),
        compact = width < 650,
        height = compact ? 100 : 62,
        nodes = [];
    const actions = [];
    if (record.canApprove)
        actions.push([
            'approval',
            record.status === 'approved'
                ? 'Return to pending'
                : 'Approve entry',
            record.status === 'approved' ? 'undo' : 'approval'
        ]);
    if (record.canEdit) {
        actions.push(['edit', 'Edit entry', 'edit']);
        actions.push(['delete', 'Delete entry', 'delete']);
    }
    const actionWidth = actions.length * 36;
    const left = record.selectable ? 44 : 10,
        detailX = left + 49;
    const end = compact ? width - 10 : width - actionWidth - 10;
    nodes.push(
        node('Box', 'timesheetEntrySurface', rect(0, 0, width, height), {
            background: record.selected
                ? 'surfaceContainerHighest'
                : 'surfaceContainerLow',
            radius: 8
        })
    );
    if (record.selectable)
        nodes.push(
            node('CheckBox', 'timesheetEntrySelect', rect(0, 9, 44, 44), {
                text: '',
                indicatorX: 10,
                label:
                    tr('Select time entry') +
                    ': ' +
                    [record.taskTitle, record.day].filter(Boolean).join(' · '),
                checked: !!record.selected,
                enabled: !record.disabled,
                action: { type: 'select', id: record.id }
            })
        );
    nodes.push(
        node('Box', 'timesheetEntryDaySurface', rect(left, 11, 40, 40), {
            background: 'surfaceContainerHighest',
            radius: 8
        })
    );
    nodes.push(
        label(
            'timesheetEntryDay',
            rect(left, 13, 40, 22),
            String(record.day || '').slice(8, 10),
            { weight: 600, align: 'center' }
        )
    );
    nodes.push(
        label(
            'timesheetEntryMonth',
            rect(left, 34, 40, 16),
            String(record.day || '').slice(5, 7),
            { fontRole: 'caption', color: 'secondaryText', align: 'center' }
        )
    );
    nodes.push(
        label(
            'timesheetEntryTask',
            rect(detailX, 8, Math.max(0, end - detailX - 95), 24),
            [record.taskTitle, record.process].filter(Boolean).join(' · '),
            { weight: 600 }
        )
    );
    nodes.push(
        label(
            'timesheetEntryDescription',
            rect(
                detailX,
                34,
                Math.max(
                    0,
                    end -
                        detailX -
                        95 -
                        (record.overtimeHours > 0 && !compact ? 65 : 0)
                ),
                20
            ),
            [record.loginLabel, record.description].filter(Boolean).join(' · '),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    nodes.push(
        label(
            'timesheetEntryHours',
            rect(Math.max(0, end - 88), 8, 88, 24),
            String(record.hours || 0) + tr(' h'),
            { align: 'right', weight: 600 }
        )
    );
    nodes.push(
        label(
            'timesheetEntryStatus',
            rect(Math.max(0, end - 88), 34, 88, 20),
            tr(record.status === 'approved' ? 'Approved' : 'Pending'),
            {
                align: 'right',
                fontRole: 'caption',
                color: record.status === 'approved' ? 'action' : 'secondaryText'
            }
        )
    );
    if (record.overtimeHours > 0)
        nodes.push(
            label(
                'timesheetEntryOvertime',
                rect(
                    compact ? 10 : Math.max(0, end - 155),
                    compact ? 66 : 34,
                    compact ? Math.max(0, width - actionWidth - 20) : 62,
                    24
                ),
                tr('OT ') + record.overtimeHours + tr(' h'),
                { fontRole: 'caption', color: 'tertiary' }
            )
        );
    let x = width - actionWidth;
    for (const [type, text, icon] of actions) {
        nodes.push(
            button(
                'timesheetEntry-' + type,
                rect(x, compact ? 65 : 16, 30, 30),
                tr(text),
                icon,
                { type, id: record.id },
                !record.disabled,
                { iconOnly: true, destructive: type === 'delete' }
            )
        );
        x += 36;
    }
    return { nodes, height };
}

export function validHours(value) {
    return (
        /^\d+(?:[.,]\d{1,2})?$/.test(String(value)) &&
        Number(String(value).replace(',', '.')) > 0 &&
        Number(String(value).replace(',', '.')) <= 24
    );
}

export function editor(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        gap = spacing.content,
        half = Math.max(0, (width - gap) / 2),
        enabled = !model.busy;
    function field(kind, id, title, text, x, y, w, field, extra) {
        nodes.push(label(id + 'Label', rect(x, y, w, 20), tr(title)));
        nodes.push(
            node(
                kind,
                id,
                rect(x, y + 24, w, kind === 'Area' ? 64 : 32),
                Object.assign(
                    {
                        text: String(text ?? ''),
                        label: tr(title),
                        enabled,
                        action: { type: 'change', field }
                    },
                    extra || {}
                )
            )
        );
    }
    field(
        'DateChoice',
        'workHourDay',
        'Work date',
        model.day,
        0,
        0,
        half,
        'day',
        { includeTime: false, allowClear: false }
    );
    field(
        'Field',
        'workHourDuration',
        'Duration, hours',
        model.hours,
        half + gap,
        0,
        half,
        'hours',
        {
            inputMode: 'decimal',
            error:
                model.hours && !validHours(model.hours)
                    ? tr('Enter hours between 0.01 and 24.')
                    : '',
            selectOnFocus: true
        }
    );
    nodes.push(
        node('Segmented', 'workHourCategory', rect(0, 66, width, 32), {
            label: tr('Category'),
            value: model.category || 'regular',
            options: [
                { value: 'regular', label: tr('Regular'), icon: 'schedule' },
                { value: 'overtime', label: tr('Overtime'), icon: 'more-time' }
            ],
            enabled,
            action: { type: 'change', field: 'category' }
        })
    );
    let y = 108;
    if (model.canManage) {
        nodes.push(
            node('UserChoice', 'workHourUser', rect(0, y, width, 32), {
                label: tr('User'),
                value: model.login || '',
                options: model.users || [],
                enabled,
                action: { type: 'change', field: 'login' }
            })
        );
        y += 42;
    }
    field(
        'Area',
        'workHourDescription',
        'Description',
        model.description,
        0,
        y,
        width,
        'description'
    );
    y += 102;
    if (model.error) {
        nodes.push(
            label('workHourError', rect(0, y, width, 40), model.error, {
                color: 'error',
                maxLines: 2
            })
        );
        y += 46;
    }
    const canSave =
        enabled &&
        validHours(model.hours) &&
        /^\d{4}-\d{2}-\d{2}$/.test(String(model.day || ''));
    const wrapApproval = !!model.canManage && width < 500;
    const approveWidth = model.canManage && !wrapApproval ? 220 : 0;
    nodes.push(
        button(
            'workHourCancel',
            rect(0, y, 112, 32),
            tr('Cancel'),
            'close',
            { type: 'cancel' },
            enabled
        )
    );
    nodes.push(
        button(
            'workHourSave',
            rect(Math.max(0, width - approveWidth - 143), y, 136, 32),
            tr('Save'),
            'save',
            { type: 'save' },
            canSave
        )
    );
    if (model.canManage)
        nodes.push(
            button(
                'workHourApprove',
                rect(
                    wrapApproval ? 0 : Math.max(0, width - 220),
                    wrapApproval ? y + 39 : y,
                    wrapApproval ? width : 220,
                    32
                ),
                tr('Save & Approve'),
                'approval',
                { type: 'approve' },
                canSave,
                { highlighted: true }
            )
        );
    return { nodes, height: y + 32 + (wrapApproval ? 39 : 0) };
}
