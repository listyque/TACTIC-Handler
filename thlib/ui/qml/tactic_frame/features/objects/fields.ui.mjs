import { node, rect, label } from '../../core/frame.mjs';
import { controls, spacing } from '../../core/foundation.mjs';
import { translate } from '../../core/strings.mjs';

export function columnCount(
    width,
    count,
    minimum = 430,
    maximum = 3,
    gap = spacing.content
) {
    return Math.max(
        1,
        Math.min(
            maximum,
            Math.max(1, count),
            Math.floor((width + gap) / (minimum + gap))
        )
    );
}

export function arrange(
    width,
    heights,
    minimum = 430,
    maximum = 3,
    gap = spacing.content
) {
    const columns = columnCount(width, heights.length, minimum, maximum, gap);
    const cellWidth = Math.max(0, (width - gap * (columns - 1)) / columns);
    const bottoms = Array(columns).fill(0);
    const cells = heights.map((height, index) => {
        const column = index % columns,
            top = bottoms[column];
        bottoms[column] += Math.max(0, height) + gap;
        return rect(column * (cellWidth + gap), top, cellWidth, height);
    });
    return {
        columns,
        cells,
        cellWidth,
        height: Math.max(0, Math.max(...bottoms) - gap)
    };
}

function lines(text, width, maximum = Infinity) {
    // shortcut: the same bounded Segoe UI caption estimate as settings forms; use glyph advances for configurable fonts.
    return Math.min(
        maximum,
        Math.max(
            1,
            Math.ceil((String(text || '').length * 6) / Math.max(1, width))
        )
    );
}

export function columns(model, width) {
    const m = controls.formField,
        compact = width < m.compactBreakpoint;
    const labelWidth = compact
        ? Math.max(0, width - m.padding * 2)
        : m.labelWidth;
    const textWidth = Math.max(0, labelWidth - m.iconExtent - m.labelSpacing);
    const caption = model.description || model.name || '';
    const captionHeight = lines(caption, textWidth, 2) * 15;
    const labelHeight = Math.max(
        m.iconExtent,
        19 + m.textSpacing + captionHeight + (model.readOnly ? 17 : 0)
    );
    const inputX = compact
        ? m.padding
        : m.padding + m.labelWidth + m.columnSpacing;
    const inputWidth = Math.max(0, width - inputX - m.padding);
    const inputY = m.padding + (compact ? labelHeight + m.rowSpacing : 0);
    return {
        compact,
        labelWidth,
        textWidth,
        caption,
        captionHeight,
        labelHeight,
        inputX,
        inputWidth,
        inputY
    };
}

export function field(model, width, editorHeight, language) {
    const m = controls.formField;
    const {
        compact,
        labelWidth,
        textWidth,
        caption,
        captionHeight,
        labelHeight,
        inputX,
        inputWidth,
        inputY
    } = columns(model, width);
    const inputHeight = Math.max(model.minimumHeight || 36, editorHeight || 0);
    const errorHeight = model.error
        ? lines(model.error, inputWidth) * 15 + m.editorSpacing
        : 0;
    const height = compact
        ? inputY + inputHeight + errorHeight + m.padding
        : Math.max(labelHeight, inputHeight + errorHeight) + m.padding * 2;
    const prefix = 'objectField_' + model.name + '_';
    const nodes = [
        node(
            'Box',
            'sobjectFieldSurface_' + model.name,
            rect(0, 0, width, height),
            {
                background: 'surfaceContainerLow',
                border: model.error ? 'error' : 'outlineVariant'
            }
        ),
        node(
            'Box',
            prefix + 'iconSurface',
            rect(m.padding, m.padding, m.iconExtent, m.iconExtent),
            {
                background: model.error
                    ? 'errorContainer'
                    : 'secondaryContainer',
                radius: 10
            }
        ),
        node(
            'Icon',
            prefix + 'icon',
            rect(
                m.padding + (m.iconExtent - m.iconSize) / 2,
                m.padding + (m.iconExtent - m.iconSize) / 2,
                m.iconSize,
                m.iconSize
            ),
            {
                icon: model.icon || 'type',
                color: model.error ? 'error' : 'action'
            }
        ),
        label(
            prefix + 'title',
            rect(
                m.padding + m.iconExtent + m.labelSpacing,
                m.padding,
                textWidth - (model.required ? 14 : 0),
                19
            ),
            model.title || model.name,
            {
                fontRole: 'bodyLarge',
                weight: 600,
                color: model.error ? 'error' : 'primaryText'
            }
        ),
        label(
            prefix + 'caption',
            rect(
                m.padding + m.iconExtent + m.labelSpacing,
                m.padding + 19 + m.textSpacing,
                textWidth,
                captionHeight
            ),
            caption,
            {
                fontRole: 'caption',
                color: 'secondaryText',
                wrap: true,
                maxLines: 2
            }
        )
    ];
    if (model.required)
        nodes.push(
            label(
                prefix + 'required',
                rect(m.padding + labelWidth - 12, m.padding, 12, 19),
                '*',
                { fontRole: 'bodyLarge', color: 'error', weight: 700 }
            )
        );
    if (model.readOnly)
        nodes.push(
            label(
                prefix + 'readOnly',
                rect(
                    m.padding + m.iconExtent + m.labelSpacing,
                    m.padding + labelHeight - 15,
                    textWidth,
                    15
                ),
                translate('Read only', language),
                { fontRole: 'caption', color: 'secondaryText', weight: 600 }
            )
        );
    if (model.error)
        nodes.push(
            label(
                prefix + 'error',
                rect(
                    inputX,
                    inputY + inputHeight + m.editorSpacing,
                    inputWidth,
                    errorHeight - m.editorSpacing
                ),
                model.error,
                {
                    fontRole: 'caption',
                    color: 'error',
                    wrap: true,
                    role: 'alert'
                }
            )
        );
    return {
        nodes,
        height,
        editor: rect(inputX, inputY, inputWidth, inputHeight),
        compact
    };
}
