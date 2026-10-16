import { label, node, rect } from '../core/frame.mjs';

export const dimensions = {
    cardHeight: 258,
    gap: 8,
    headerHeight: 133,
    gutter: 12,
    filterPadding: 8
};

export function categoryHeader(width, title, count, translate) {
    return {
        width,
        height: 42,
        nodes: [
            label(
                'projectCategoryTitle',
                rect(8, 0, width - 8, 42),
                (title || translate('No Category')) +
                    '\u00a0\u00a0·\u00a0\u00a0' +
                    count,
                {
                    fontRole: 'bodyLarge',
                    weight: 600,
                    role: 'heading',
                    level: 3
                }
            )
        ]
    };
}

export function popup(width, height, phone = false) {
    return {
        width: Math.max(0, Math.min(800, width - (phone ? 24 : 40))),
        height: Math.max(0, Math.min(680, height - 72))
    };
}

export function header(
    width,
    visible,
    total,
    translate,
    inline = false,
    phone = false
) {
    return {
        width,
        height: inline ? (phone ? 82 : 42) : phone ? 149 : 133,
        nodes: inline
            ? []
            : [
                  label(
                      'projectChooserTitle',
                      rect(20, 14, width - 82, 24),
                      translate('Projects'),
                      { fontRole: 'display', weight: 600 }
                  ),
                  label(
                      'projectChooserSummary',
                      rect(20, 39, width - 82, 17),
                      translate('{visible} of {total} projects shown', {
                          visible,
                          total
                      }),
                      { fontRole: 'body', color: 'secondaryText' }
                  ),
                  node(
                      'Box',
                      'projectChooserDivider',
                      rect(0, phone ? 148 : 132, width, 1),
                      {
                          background: 'separator'
                      }
                  ),
                  node(
                      'View',
                      'projectChooserClose',
                      rect(width - 52, 8, 44, 44),
                      { view: 'close' }
                  )
              ]
    };
}

// Category order and project availability belong to the existing catalog owner.
export function category(width, count, phone = false) {
    const columns = phone ? (width < 360 ? 1 : 2) : 3;
    const cardWidth = Math.floor(
        Math.max(0, width - (columns - 1) * 8) / columns
    );
    return {
        columns,
        cardWidth,
        height: 48 + Math.ceil(count / columns) * 266 - 8,
        cards: Array.from({ length: count }, (_, i) =>
            rect(
                (i % columns) * (cardWidth + 8),
                48 + Math.floor(i / columns) * 266,
                cardWidth,
                258
            )
        )
    };
}

export function lifecycle(record) {
    return record.isBuiltin
        ? 'BUILT-IN'
        : record.isTemplate
          ? 'TEMPLATE'
          : record.isRetired
            ? 'ARCHIVED'
            : 'ACTIVE';
}

export function card(width, record, options, translate) {
    const labelWidth = Math.max(45, Math.round(options.detailLabelWidth));
    const long =
        options.descriptionWidth > width - 18 ||
        /\n/.test(record.description || '');
    const chipWidth = Math.min(width - 18, Math.floor(options.chipWidth) + 16);
    const chipY = long ? 143 : 155;
    const descriptionY = long ? 176 : 189;
    const detailY = long ? 216 : 215;
    const color = record.isRetired
        ? 'yellow'
        : record.isBuiltin
          ? 'secondaryText'
          : 'action';
    return {
        width,
        height: 258,
        nodes: [
            node('Box', 'projectCardSurface', rect(0, 0, width, 258), {
                radius: options.radius,
                border: options.selected ? 'action' : 'outlineVariant',
                background: options.pressed
                    ? 'selected'
                    : options.hovered || options.focused
                      ? 'rowHover'
                      : 'surfaceContainerHigh'
            }),
            node(
                'Preview',
                'projectGridPreview',
                rect(Math.floor((width - 120) / 2), long ? 12 : 18, 120, 120),
                {
                    source: record.preview || '',
                    initials: record.initials,
                    round: false,
                    radius: options.previewRadius,
                    accent: 'toolBar',
                    outlined: true
                }
            ),
            label(
                'projectCardTitle',
                rect(9, chipY + 4, width - 26 - chipWidth, 17),
                record.title || record.code,
                { fontRole: 'body', weight: 600 }
            ),
            node(
                'Box',
                'projectCardLifecycle',
                rect(width - 9 - chipWidth, chipY, chipWidth, 24),
                {
                    background: 'surfaceContainerHigh',
                    radius: 12,
                    children: [
                        label(
                            'projectCardLifecycleText',
                            rect(7.5, 0, chipWidth - 15, 24),
                            translate(lifecycle(record)),
                            {
                                fontRole: 'caption',
                                weight: 600,
                                color,
                                align: 'center'
                            }
                        )
                    ]
                }
            ),
            label(
                'projectCardDescription',
                rect(9, descriptionY, width - 18, long ? 32 : 16),
                record.description || translate('No project description'),
                {
                    fontRole: 'secondary',
                    color: 'secondaryText',
                    wrap: true,
                    maxLines: 2
                }
            ),
            label(
                'projectCardCategoryLabel',
                rect(9, detailY, labelWidth, 15),
                translate('Category'),
                { fontRole: 'caption', color: 'secondaryText', elide: false }
            ),
            label(
                'projectCardCategory',
                rect(17 + labelWidth, detailY, width - 26 - labelWidth, 15),
                record.category || translate('Not set'),
                { fontRole: 'caption' }
            ),
            label(
                'projectCardTypeLabel',
                rect(9, detailY + 17, labelWidth, 15),
                translate('Type'),
                { fontRole: 'caption', color: 'secondaryText', elide: false }
            ),
            label(
                'projectCardType',
                rect(
                    17 + labelWidth,
                    detailY + 17,
                    width - 26 - labelWidth,
                    15
                ),
                record.projectType || translate('Not set'),
                { fontRole: 'caption' }
            )
        ]
    };
}

export function keyTarget(codes, current, key, columns) {
    if (!codes.length) return null;
    const index = codes.indexOf(current);
    if (key === 'Home') return codes[0];
    if (key === 'End') return codes[codes.length - 1];
    const step = {
        ArrowLeft: -1,
        ArrowRight: 1,
        ArrowUp: -columns,
        ArrowDown: columns
    }[key];
    if (step === undefined) return null;
    return codes[
        Math.max(0, Math.min(codes.length - 1, (index < 0 ? 0 : index) + step))
    ];
}
