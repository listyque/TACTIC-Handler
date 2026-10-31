import { spacing } from '../../core/foundation.mjs';
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export const titles = {
    process: 'Process',
    context: 'Context',
    status: 'Status',
    assigned: 'Assigned to',
    supervisor: 'Supervisor',
    bid_start_date: 'Start date',
    bid_end_date: 'End date',
    bid_duration: 'Planned hours',
    progress: 'Progress',
    completion: 'Progress',
    description: 'Description',
    priority: 'Priority',
    milestone_code: 'Milestone'
};
export function describe(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        single = model.inline && model.immediate && model.fields?.length === 1,
        rowHeight = single ? 40 : 72,
        gap = spacing.content,
        columns = width >= (model.live ? 420 : 520) ? 2 : 1,
        cell = (width - gap * (columns - 1)) / columns;
    let y = 0,
        slot = 0;
    if (model.inline) {
        nodes.push(
            label(
                'taskInlineTitle',
                rect(0, 0, width - 40, 28),
                tr(
                    single
                        ? titles[model.fields[0].name] || model.fields[0].name
                        : model.title || 'Edit task draft'
                ),
                { fontRole: 'body', weight: 600 }
            )
        );
        nodes.push(
            button(
                'taskInlineClose',
                rect(width - 28, 0, 28, 28),
                tr('Close'),
                'close',
                { type: 'cancel' },
                !model.busy,
                { iconOnly: true, iconAction: true, iconSize: 17 }
            )
        );
        y = 40;
    }
    if (!model.immediate) {
        nodes.push(
            label(
                'taskEditorHint',
                rect(0, y, width, 32),
                tr(
                    model.live
                        ? 'Each checked field replaces its current value'
                        : 'Changes remain pending until Save.'
                ),
                { fontRole: 'caption', color: 'secondaryText', wrap: true }
            )
        );
        y += 40;
    }
    for (const field of model.fields || []) {
        const wide = field.name === 'description';
        if (wide && slot) {
            y += 70;
            slot = 0;
        }
        const x = slot * (cell + gap),
            w = wide ? width : cell,
            title = tr(titles[field.name] || field.name),
            enabled =
                !model.busy && !model.readOnly && field.editable !== false;
        if (model.bulk)
            nodes.push(
                node(
                    'CheckBox',
                    'taskEditorEnable_' + field.name,
                    rect(x, y, w, 24),
                    {
                        text: title,
                        label: title,
                        checked: (model.enabled || []).includes(field.name),
                        enabled,
                        action: { type: 'enable', field: field.name }
                    }
                )
            );
        else if (!single)
            nodes.push(
                label(
                    'taskEditorTitle_' + field.name,
                    rect(x, y, w, 20),
                    title,
                    { fontRole: 'body' }
                )
            );
        const h = wide ? 64 : 32;
        nodes.push(
            node(
                'View',
                'taskEditorValue_' + field.name,
                rect(x, y + (single ? 0 : 28), w, h),
                {
                    view: 'field',
                    field,
                    enabled:
                        enabled &&
                        (!model.bulk ||
                            (model.enabled || []).includes(field.name))
                }
            )
        );
        if (wide) y += h + 40;
        else {
            slot++;
            if (slot === columns) {
                slot = 0;
                y += rowHeight;
            }
        }
    }
    if (slot) y += rowHeight;
    if (!model.immediate) {
        const hasApply = !model.live || model.staging;
        const stacked = hasApply && width < 256;
        const applyWidth = stacked ? width : 152,
            cancelWidth = stacked ? width : Math.min(width, 96);
        nodes.push(
            button(
                'taskEditorCancel',
                rect(
                    stacked
                        ? 0
                        : Math.max(
                              0,
                              width -
                                  cancelWidth -
                                  (hasApply ? applyWidth + 8 : 0)
                          ),
                    y,
                    cancelWidth,
                    32
                ),
                tr(model.live ? 'Done' : 'Cancel'),
                '',
                { type: 'cancel' },
                !model.busy
            )
        );
        if (hasApply)
            nodes.push(
                button(
                    'taskEditorApply',
                    rect(
                        width - applyWidth,
                        y + (stacked ? 40 : 0),
                        applyWidth,
                        32
                    ),
                    tr('Apply to draft'),
                    'check',
                    { type: 'apply' },
                    !model.busy && !model.readOnly,
                    { highlighted: true }
                )
            );
        y += stacked ? 80 : 40;
    }
    return { nodes, height: y };
}
