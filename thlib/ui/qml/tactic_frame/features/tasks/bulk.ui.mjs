import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export const fields = [
    'status',
    'assigned',
    'bid_start_date',
    'bid_end_date',
    'priority',
    'milestone_code',
    'supervisor',
    'progress',
    'description'
];
export function bar(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [],
        compact = width < 760,
        y = 8;
    nodes.push(
        node('Box', 'taskBulkSurface', rect(0, 0, width, 48), {
            background: 'secondaryContainer',
            radiusRole: 'itemRadius'
        })
    );
    nodes.push(
        node('Icon', 'taskBulkIcon', rect(9, 15, 17, 17), {
            icon: 'edit-note',
            color: 'action'
        })
    );
    let right = width - 7;
    const icon = (id, title, glyph, type, enabled, extra) => {
        right -= 32;
        nodes.push(
            button(
                id,
                rect(right, y, 32, 32),
                tr(title),
                glyph,
                { type },
                enabled,
                Object.assign(
                    { iconOnly: true, iconAction: true, iconSize: 17 },
                    extra || {}
                )
            )
        );
        right -= 6;
    };
    icon(
        'taskBulkCancel',
        'Cancel bulk edit and clear selection',
        'close',
        'cancel',
        !model.busy
    );
    icon(
        'taskBulkDeleteButton',
        'Delete selected tasks',
        'delete',
        'delete',
        !model.blocked && !model.busy,
        { destructive: true, iconColor: 'error' }
    );
    const applyWidth = width < 380 ? 32 : 96;
    right -= applyWidth;
    nodes.push(
        button(
            'taskBulkApply',
            rect(right, y, applyWidth, 32),
            tr(model.busy ? 'APPLYING' : 'APPLY'),
            'done-all',
            { type: 'apply' },
            !!model.canApply,
            {
                highlighted: true,
                iconOnly: width < 380,
                label: tr('Apply bulk changes')
            }
        )
    );
    right -= 6;
    const titleWidth = compact
        ? Math.min(86, Math.max(0, right - 32 - 44))
        : 112;
    nodes.push(
        label(
            'taskBulkCount',
            rect(32, 14, titleWidth, 20),
            tr(
                model.count === 1
                    ? '{count} task selected'
                    : '{count} tasks selected',
                { count: model.count }
            ),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    let x = 32 + titleWidth + 6;
    if (!compact)
        for (const [key, extent] of [
            ['status', 132],
            ['assigned', 150]
        ]) {
            nodes.push(
                node('CheckBox', 'taskBulkEnable_' + key, rect(x, y, 32, 32), {
                    label: tr(key === 'status' ? 'Status' : 'Assigned to'),
                    checked: !!model.enabled?.includes(key),
                    enabled: !model.blocked && !model.busy,
                    action: { type: 'enable', field: key }
                })
            );
            x += 34;
            nodes.push(
                node('View', 'taskBulkValue_' + key, rect(x, y, extent, 32), {
                    view: key,
                    enabled: !model.busy && !!model.enabled?.includes(key)
                })
            );
            x += extent + 6;
        }
    nodes.push(
        button(
            'taskBulkMore',
            rect(x, y, 32, 32),
            tr('Edit selected tasks'),
            'tune',
            { type: 'more' },
            !model.busy,
            {
                iconOnly: true,
                iconAction: true,
                iconSize: 17,
                pressAction: { type: 'more-press' }
            }
        )
    );
    x += 38;
    if (right > x)
        nodes.push(
            label(
                'taskBulkPreview',
                rect(x, 14, right - x, 20),
                model.preview || tr('Choose fields to change'),
                {
                    fontRole: 'caption',
                    color: model.invalid ? 'error' : 'secondaryText',
                    align: 'right'
                }
            )
        );
    return { nodes, height: 48, compact };
}

export function prepare(plans) {
    if (!plans.length) return null;
    const first = plans[0],
        common = (source) =>
            (first[source] || []).filter(
                (row) =>
                    row.available !== false &&
                    plans.every((plan) =>
                        (plan[source] || []).some(
                            (other) =>
                                String(other.value) === String(row.value) &&
                                other.available !== false
                        )
                    )
            );
    const record = (plan) => Object.assign({}, plan.task, plan.data || {}),
        initial = record(first),
        mixed = [];
    const available = first.fields
        .filter(
            (field) =>
                fields.includes(field.name) || field.name === 'completion'
        )
        .filter(
            (field) =>
                field.editable &&
                plans.every((plan) =>
                    plan.fields.some(
                        (other) => other.name === field.name && other.editable
                    )
                )
        );
    for (const field of available)
        if (
            plans.some(
                (plan) =>
                    String(record(plan)[field.name] ?? '') !==
                    String(initial[field.name] ?? '')
            )
        )
            mixed.push(field.name);
    const catalog = Object.assign({}, first.catalog);
    for (const key of ['priorityChoices', 'milestoneChoices'])
        catalog[key] = (first.catalog[key] || []).filter((row) =>
            plans.every((plan) =>
                (plan.catalog[key] || []).some(
                    (other) => String(other.value) === String(row.value)
                )
            )
        );
    return {
        plans,
        fields: available,
        values: initial,
        enabled: [],
        mixed,
        set: [],
        statuses: common('statusChoices').map((row) => row.value),
        statusChoices: common('statusChoices'),
        users: common('users'),
        catalog
    };
}
export function preview(form) {
    const result = {
        eligible: 0,
        unchanged: 0,
        invalid: 0,
        fields: form?.enabled?.length || 0
    };
    if (!result.fields) return result;
    for (const plan of form.plans) {
        let changed = false,
            invalid = false;
        const before = Object.assign({}, plan.task, plan.data || {});
        for (const key of form.enabled) {
            const value = form.values[key] ?? '';
            if (form.mixed.includes(key) && !form.set.includes(key))
                invalid = true;
            if (key === 'status' && !form.statuses.includes(value))
                invalid = true;
            if (
                ['assigned', 'supervisor'].includes(key) &&
                !(form.users || []).some((row) => row.value === value)
            )
                invalid = true;
            if (
                ['progress', 'completion'].includes(key) &&
                (!Number.isFinite(Number(value)) ||
                    Number(value) < 0 ||
                    Number(value) > 100)
            )
                invalid = true;
            if (String(value) !== String(before[key] ?? '')) changed = true;
        }
        const start = form.enabled.includes('bid_start_date')
            ? form.values.bid_start_date
            : before.bid_start_date;
        const end = form.enabled.includes('bid_end_date')
            ? form.values.bid_end_date
            : before.bid_end_date;
        if (
            (start && !Number.isFinite(Date.parse(start))) ||
            (end && !Number.isFinite(Date.parse(end))) ||
            (start && end && Date.parse(end) < Date.parse(start))
        )
            invalid = true;
        result[invalid ? 'invalid' : changed ? 'eligible' : 'unchanged']++;
    }
    return result;
}
