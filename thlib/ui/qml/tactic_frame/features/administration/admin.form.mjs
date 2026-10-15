import { fieldProperties } from '../../controls/forms/fields.mjs';
import { node } from '../../core/frame.mjs';
import { rect, label, muted } from './admin.document.mjs';
import { translate } from '../../core/strings.mjs';

// Form rows share their geometry; engines only supply the named control.
export function form(fields, width, language, enabled) {
    const nodes = [],
        tr = (text) => translate(text, language);
    let y = 0;
    for (const field of fields) {
        if (field.when === false) continue;
        const id = field.id,
            narrow = width < 420;
        if (field.kind === 'Heading') {
            nodes.push(
                label(
                    id,
                    rect(0, y, width, 28),
                    field.dataLabel ? field.title : tr(field.title),
                    {
                        fontRole: 'section',
                        weight: 600,
                        role: 'heading',
                        level: 2
                    }
                )
            );
            y += 34;
            if (field.description) {
                const h = Math.max(
                    narrow ? 72 : 48,
                    Math.ceil(
                        (tr(field.description).length * 7) / Math.max(80, width)
                    ) *
                        16 +
                        16
                );
                nodes.push(
                    label(
                        id + 'Description',
                        rect(0, y, width, h),
                        tr(field.description),
                        Object.assign(
                            {
                                wrap: true
                            },
                            muted
                        )
                    )
                );
                y += h + 8;
            }
            continue;
        }
        const controlWidth = narrow ? width : Math.min(270, width * 0.44),
            x = narrow ? 0 : width - controlWidth;
        const detailHeight = field.description
            ? Math.max(
                  narrow ? 60 : 48,
                  Math.ceil(
                      (tr(field.description).length * 7) /
                          Math.max(80, narrow ? width : x - 16)
                  ) *
                      16 +
                      16
              )
            : 0;
        const h = narrow
                ? 30 + detailHeight + (field.height || 38) + 20
                : Math.max(62, 28 + detailHeight, (field.height || 38) + 16),
            controlY = narrow ? y + 26 + detailHeight : y + 8;
        nodes.push(
            label(
                id + 'Label',
                rect(0, y, narrow ? width : x - 16, 26),
                field.dataLabel ? field.title : tr(field.title)
            )
        );
        if (field.description)
            nodes.push(
                label(
                    id + 'Description',
                    rect(0, y + 28, narrow ? width : x - 16, detailHeight),
                    tr(field.description),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
        const props = fieldProperties(field, language, enabled);
        if (field.kind === 'Number') {
            const children = [
                node('Button', id + 'Decrease', rect(0, 0, 34, 38), {
                    text: tr('Decrease width'),
                    icon: 'chevron-down',
                    iconOnly: true,
                    enabled: enabled && field.value > field.min,
                    action: {
                        type: 'step',
                        value: -field.step
                    }
                }),
                node(
                    'Field',
                    id + 'Input',
                    rect(34, 0, controlWidth - 68, 38),
                    Object.assign({}, props, {
                        tableCell: true,
                        align: 'center'
                    })
                ),
                node(
                    'Button',
                    id + 'Increase',
                    rect(controlWidth - 34, 0, 34, 38),
                    {
                        text: tr('Increase width'),
                        icon: 'chevron-up',
                        iconOnly: true,
                        enabled: enabled && field.value < field.max,
                        action: {
                            type: 'step',
                            value: field.step
                        }
                    }
                )
            ];
            nodes.push(
                node('Box', id, rect(x, controlY, controlWidth, 38), {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 10,
                    children
                })
            );
            y += h + 8;
            continue;
        }
        nodes.push(
            node(
                field.kind || 'Field',
                id,
                rect(
                    x,
                    controlY,
                    field.kind === 'IconChoice' || field.kind === 'CheckBox'
                        ? 38
                        : controlWidth,
                    field.height || 38
                ),
                props
            )
        );
        y += h + 8;
    }
    return {
        nodes,
        height: y
    };
}
