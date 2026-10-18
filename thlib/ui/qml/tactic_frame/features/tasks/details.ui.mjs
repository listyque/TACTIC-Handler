import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const titles = {
    process: 'Process',
    context: 'Context',
    status: 'Status',
    assigned: 'Assignee',
    bid_start_date: 'Start',
    bid_end_date: 'Deadline',
    progress: 'Progress',
    completion: 'Progress',
    bid_duration: 'Expected work hours',
    notes: 'Notes',
    priority: 'Priority',
    milestone_code: 'Milestone',
    supervisor: 'Supervisor'
};

export function columnCount(width) {
    return width >= 1280
        ? 5
        : width >= 960
          ? 4
          : width >= 720
            ? 3
            : width >= 440
              ? 2
              : 1;
}

export function describe(model, width, language) {
    const tr = (text) => translate(text, language);
    const left = model.left === undefined ? 12 : model.left;
    const right = model.right === undefined ? 12 : model.right;
    const columns = columnCount(width),
        gap = 8;
    const cellWidth = Math.max(
        0,
        (width - left - right - (columns - 1) * gap) / columns
    );
    const fields = model.fields || [];
    const nodes = [];
    let top = 8;
    for (let start = 0; start < fields.length; start += columns) {
        const row = fields.slice(start, start + columns);
        let rowHeight = 0;
        row.forEach((field, index) => {
            const x = left + index * (cellWidth + gap);
            const progress = ['progress', 'completion'].includes(field.name);
            const valueHeight = progress ? 26 : 32;
            nodes.push(
                label(
                    'taskDetailTitle_' + field.name,
                    rect(x, top, cellWidth - (progress ? 45 : 0), 15),
                    tr(
                        titles[field.name] || field.title || field.name
                    ).toUpperCase(),
                    {
                        fontRole: 'caption',
                        weight: 600,
                        color: 'secondaryText',
                        letterSpacing: 0.35
                    }
                )
            );
            if (progress)
                nodes.push(
                    label(
                        'taskDetailProgress_' + field.name,
                        rect(x + cellWidth - 45, top, 45, 15),
                        Math.round(
                            field.value === undefined
                                ? model.progress || 0
                                : field.value
                        ) + '%',
                        { fontRole: 'caption', weight: 600, align: 'right' }
                    )
                );
            nodes.push(
                node(
                    'View',
                    'taskDetailField_' + field.name,
                    rect(x, top + 18, cellWidth, valueHeight),
                    { view: field.name }
                )
            );
            rowHeight = Math.max(rowHeight, 18 + valueHeight);
        });
        top += rowHeight + gap;
    }
    if (fields.length) top -= gap;
    if (model.description) {
        top += 10;
        nodes.push(
            node(
                'Box',
                'taskDescriptionSeparator',
                rect(left, top, width - left - 18, 1),
                { background: 'separator', opacity: 0.75, radius: 0 }
            )
        );
        top += 9;
        nodes.push(
            label(
                'taskDescriptionTitle',
                rect(left, top, width - left - 18, 15),
                tr('Description').toUpperCase(),
                {
                    fontRole: 'caption',
                    weight: 600,
                    color: 'secondaryText',
                    letterSpacing: 0.35
                }
            )
        );
        top += 19;
        nodes.push(
            node(
                'View',
                'taskDescriptionValue',
                rect(left, top, width - left - 18, 58),
                { view: 'description' }
            )
        );
        nodes.push(
            button(
                'taskDescriptionEditButton',
                rect(width - 18 - 33, top + 15, 28, 28),
                tr(
                    model.editingDescription
                        ? 'Finish editing description'
                        : 'Edit task description'
                ),
                model.editingDescription ? 'check' : 'edit',
                { type: 'description' },
                !model.busy && model.descriptionEditable !== false,
                {
                    retainFocus: true,
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 17,
                    visible: !model.creating
                }
            )
        );
        top += 68;
    } else top += 8;
    nodes.unshift(
        node('Box', 'taskDetailsBackground', rect(0, 0, width, top), {
            background: 'panelDeep',
            radius: 0
        })
    );
    if (model.topSeparator !== false)
        nodes.push(
            node('Box', 'taskDetailsTopSeparator', rect(0, 0, width, 1), {
                background: 'separator',
                radius: 0
            })
        );
    return { nodes, height: top, columns, cellWidth };
}
