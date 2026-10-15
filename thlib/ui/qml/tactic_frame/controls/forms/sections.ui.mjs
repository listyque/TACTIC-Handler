import { node, rect, label, muted } from '../../core/frame.mjs';
import { metrics } from '../../core/foundation.mjs';
import { translate } from '../../core/strings.mjs';
import { fieldProperties } from './fields.mjs';

function captionHeight(text, width) {
    // Reserve complete caption lines in both engines; painting stays native.
    return text
        ? Math.max(15, Math.ceil((text.length * 6) / Math.max(1, width)) * 15)
        : 0;
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
                    weight: 600
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

            const controlWidth = Math.max(1, Math.min(280, width - 48));
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
            children.push(
                node(
                    field.kind || 'Field',
                    field.id,
                    rect(controlX, controlY, controlWidth, controlHeight),
                    properties
                )
            );
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
