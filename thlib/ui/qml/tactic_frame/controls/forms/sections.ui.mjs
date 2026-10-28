import { node, rect, label, muted } from '../../core/frame.mjs';
import { metrics } from '../../core/foundation.mjs';
import { translate } from '../../core/strings.mjs';
import { fieldProperties } from './fields.mjs';

export function captionHeight(text, width) {
    if (!text) return 0;
    // shortcut: Segoe UI EN/RU word estimates; use font advances for arbitrary fonts/scripts.
    const available = Math.max(1, width);
    let lines = 0;
    for (const paragraph of text.split('\n')) {
        let used = 0;
        lines++;
        for (const word of paragraph.split(/\s+/).filter(Boolean)) {
            const advance = word.length * 7;
            if (used && used + 4 + advance > available) {
                lines++;
                used = 0;
            }
            const wraps = Math.max(1, Math.ceil(advance / available));
            lines += wraps - 1;
            used = (used ? used + 4 : 0) + advance - (wraps - 1) * available;
        }
    }
    return lines * 15;
}

function choices(field, properties, width, controlHeight) {
    const options = properties.options,
        columns = width >= 206 ? 2 : 1;
    const cellWidth = (width - (columns - 1) * 6) / columns;
    const children = options.map((option, index) =>
        node(
            'Action',
            field.id + '_' + option.value,
            rect(
                (index % columns) * (cellWidth + 6),
                Math.floor(index / columns) * (controlHeight + 6),
                cellWidth,
                controlHeight
            ),
            {
                text: option.label,
                enabled: properties.enabled,
                selected: properties.value === option.value,
                normalColor: 'surfaceContainerHigh',
                selectedColor: 'contentSelection',
                children: [
                    label(
                        field.id + '_label_' + option.value,
                        rect(10, 0, cellWidth - 20, controlHeight),
                        option.label
                    )
                ],
                action: Object.assign({}, properties.action, {
                    value: option.value
                })
            }
        )
    );
    return {
        children,
        height: Math.max(
            0,
            Math.ceil(options.length / columns) * (controlHeight + 6) - 6
        )
    };
}

export function sections(fields, width, language, enabled, style) {
    const sizing = metrics(style),
        groups = [],
        nodes = [];
    for (const field of fields) {
        if (field.when === false) continue;
        if (field.kind === 'Heading')
            groups.push({ heading: field, fields: [] });
        else {
            if (!groups.length) groups.push({ heading: null, fields: [] });
            groups[groups.length - 1].fields.push(field);
        }
    }

    let contentY = 0;
    for (const group of groups) {
        if (group.heading) {
            const heading = group.heading;
            const title = heading.dataLabel
                ? heading.title
                : translate(heading.title, language);
            nodes.push(
                label(heading.id, rect(1, contentY, width - 2, 20), title, {
                    fontRole: 'bodyLarge',
                    weight: 600,
                    role: 'heading',
                    level: 3
                })
            );
            contentY += 28;
            if (heading.description) {
                const description = translate(heading.description, language);
                const height = captionHeight(description, width - 2);
                nodes.push(
                    label(
                        heading.id + 'Description',
                        rect(1, contentY, width - 2, height),
                        description,
                        Object.assign({}, muted, {
                            fontRole: 'caption',
                            wrap: true
                        })
                    )
                );
                contentY += height + 8;
            }
        }
        if (!group.fields.length) continue;
        const children = [],
            rowWidth = Math.max(1, width - 40);
        let rowY = 16;
        for (let index = 0; index < group.fields.length; index++) {
            const field = group.fields[index];
            const properties = fieldProperties(field, language, enabled);
            if (field.kind === 'CheckBox') properties.text = '';
            const controlHeight = field.height || sizing.controlHeight;
            if (field.kind === 'ChoiceGrid') {
                const grid = choices(
                    field,
                    properties,
                    width - 32,
                    controlHeight
                );
                children.push(
                    node(
                        'Box',
                        field.id,
                        rect(16, rowY, width - 32, grid.height),
                        { children: grid.children }
                    )
                );
                rowY += grid.height + 8;
                continue;
            }
            if (field.fullWidth || field.kind === 'Button') {
                children.push(
                    node(
                        field.kind,
                        field.id,
                        rect(16, rowY, width - 32, controlHeight),
                        properties
                    )
                );
                rowY += controlHeight + 8;
                continue;
            }

            const controlWidth = Math.max(
                1,
                Math.min(field.controlWidth || 280, width - 48)
            );
            const stacked = rowWidth - controlWidth - 20 < 210;
            const textWidth = stacked ? rowWidth : rowWidth - controlWidth - 20;
            const description = translate(field.description || '', language);
            const descriptionHeight = captionHeight(description, textWidth);
            const textHeight = 18 + (description ? 3 + descriptionHeight : 0);
            const rowHeight = Math.max(
                54,
                stacked
                    ? textHeight + 8 + controlHeight + 20
                    : Math.max(textHeight, controlHeight) + 20
            );
            children.push(
                label(
                    field.id + 'Label',
                    rect(20, rowY + 10, textWidth, 18),
                    properties.label,
                    { fontRole: 'body', weight: 600 }
                )
            );
            if (description)
                children.push(
                    label(
                        field.id + 'Description',
                        rect(20, rowY + 31, textWidth, descriptionHeight),
                        description,
                        Object.assign({}, muted, {
                            fontRole: 'caption',
                            wrap: true
                        })
                    )
                );
            const controlY = stacked
                ? rowY + 10 + textHeight + 8
                : rowY + (rowHeight - controlHeight) / 2;
            const controlX = width - 20 - controlWidth;
            if (field.kind === 'Number') {
                children.push(
                    node(
                        'Box',
                        field.id,
                        rect(controlX, controlY, controlWidth, controlHeight),
                        {
                            background: 'surfaceContainerHigh',
                            border: 'outlineVariant',
                            radius: 10,
                            children: [
                                node(
                                    'Button',
                                    field.id + 'Decrease',
                                    rect(0, 0, 34, controlHeight),
                                    {
                                        text: translate(
                                            'Decrease width',
                                            language
                                        ),
                                        icon: 'chevron-down',
                                        iconOnly: true,
                                        enabled:
                                            properties.enabled &&
                                            field.value > field.min,
                                        action: {
                                            type: 'step',
                                            field: field.field,
                                            value: -field.step
                                        }
                                    }
                                ),
                                node(
                                    'Field',
                                    field.id + 'Input',
                                    rect(
                                        34,
                                        0,
                                        controlWidth - 68,
                                        controlHeight
                                    ),
                                    Object.assign({}, properties, {
                                        tableCell: true,
                                        align: 'center'
                                    })
                                ),
                                node(
                                    'Button',
                                    field.id + 'Increase',
                                    rect(
                                        controlWidth - 34,
                                        0,
                                        34,
                                        controlHeight
                                    ),
                                    {
                                        text: translate(
                                            'Increase width',
                                            language
                                        ),
                                        icon: 'chevron-up',
                                        iconOnly: true,
                                        enabled:
                                            properties.enabled &&
                                            field.value < field.max,
                                        action: {
                                            type: 'step',
                                            field: field.field,
                                            value: field.step
                                        }
                                    }
                                )
                            ]
                        }
                    )
                );
            } else {
                const trailing = field.trailingAction;
                children.push(
                    node(
                        field.kind || 'Field',
                        field.id,
                        rect(
                            controlX,
                            controlY,
                            Math.max(
                                0,
                                controlWidth -
                                    (trailing ? controlHeight + 6 : 0)
                            ),
                            controlHeight
                        ),
                        properties
                    )
                );
                if (trailing)
                    children.push(
                        node(
                            'Button',
                            field.id + 'Open',
                            rect(
                                controlX + controlWidth - controlHeight,
                                controlY,
                                controlHeight,
                                controlHeight
                            ),
                            {
                                text: translate(trailing.title, language),
                                icon: trailing.icon,
                                iconOnly: true,
                                enabled: trailing.enabled !== false,
                                action: trailing.action
                            }
                        )
                    );
            }
            rowY += rowHeight;
            if (
                index < group.fields.length - 1 &&
                field.showDivider !== false
            ) {
                children.push(
                    node(
                        'Box',
                        field.id + 'Divider',
                        rect(20, rowY - 1, rowWidth, 1),
                        { background: 'outlineVariant' }
                    )
                );
            }
        }
        const last = group.fields[group.fields.length - 1];
        const cardHeight =
            rowY + (last.fullWidth || last.kind === 'Button' ? 8 : 16);
        nodes.push(
            node(
                'Box',
                'section_' +
                    (group.heading ? group.heading.id : group.fields[0].id),
                rect(0, contentY, width, cardHeight),
                {
                    background: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    borderWidth: 1,
                    radius: sizing.sectionRadius,
                    children
                }
            )
        );
        contentY += cardHeight + 16;
    }
    return { nodes, height: contentY };
}
