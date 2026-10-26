import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 650,
        footerHeight = narrow ? 92 : 64;
    const errorHeight = model.error
        ? Math.max(
              44,
              captionHeight(tr(model.error), Math.max(1, width - 50)) + 20
          )
        : 0;
    const bodyHeight = Math.max(
            0,
            height - 68 - footerHeight - errorHeight - 28
        ),
        paneWidth = narrow ? width - 28 : (width - 80) / 2;
    const paneHeight = narrow ? Math.max(0, (bodyHeight - 44) / 2) : bodyHeight;
    const nodes = [
        node('Box', 'linkHeader', rect(0, 0, width, 68), {
            background: 'panel',
            children: [
                node('Box', 'linkHeaderIconSurface', rect(18, 15, 38, 38), {
                    background: 'secondaryContainer',
                    children: [
                        node('Icon', 'linkHeaderIcon', rect(10, 10, 18, 18), {
                            icon: 'link',
                            color: 'action'
                        })
                    ]
                }),
                label(
                    'linkTitle',
                    rect(68, 12, Math.max(0, width - 122), 23),
                    model.targetTitle && model.parentTitle
                        ? tr('Objects') +
                              ': ' +
                              model.targetTitle +
                              ' → ' +
                              tr('Parent object') +
                              ': ' +
                              model.parentTitle
                        : tr('Select an instance relation'),
                    { weight: 600 }
                ),
                label(
                    'linkSubtitle',
                    rect(68, 37, Math.max(0, width - 122), 18),
                    model.subtitle || tr('Choose objects to link'),
                    { color: 'secondaryText' }
                ),
                button(
                    'linkRefresh',
                    rect(width - 46, 18, 32, 32),
                    tr('Reload related objects'),
                    'refresh',
                    { type: 'refresh' },
                    !model.busy && !model.dirty && !model.uncertain,
                    { iconOnly: true, iconAction: true }
                )
            ]
        })
    ];
    for (const [index, scope] of ['available', 'linked'].entries()) {
        const x = narrow ? 14 : 14 + index * (paneWidth + 52),
            y = 82 + (narrow ? index * (paneHeight + 44) : 0);
        nodes.push(
            node(
                'Box',
                scope + 'LinkPane',
                rect(x, y, Math.max(0, paneWidth), paneHeight),
                {
                    background: 'panel',
                    border: 'outlineVariant',
                    children: [
                        node(
                            'View',
                            scope + 'LinkSearch',
                            rect(10, 10, Math.max(0, paneWidth - 20), 40),
                            { view: scope + 'Search' }
                        ),
                        node(
                            'View',
                            scope + 'LinkList',
                            rect(
                                10,
                                58,
                                Math.max(0, paneWidth - 20),
                                Math.max(0, paneHeight - 68)
                            ),
                            { view: scope + 'List' }
                        )
                    ]
                }
            )
        );
    }
    const direction = model.direction || 'add';
    nodes.push(
        button(
            'linkTransferButton',
            rect(
                narrow ? (width - 42) / 2 : 14 + paneWidth + 5,
                narrow ? 82 + paneHeight + 1 : 82 + (bodyHeight - 42) / 2,
                42,
                42
            ),
            tr(
                direction === 'remove'
                    ? 'Remove selected links'
                    : 'Link selected objects'
            ),
            direction === 'remove'
                ? narrow
                    ? 'arrow-upward'
                    : 'arrow-left'
                : narrow
                  ? 'arrow-downward'
                  : 'arrow-forward',
            { type: 'transfer' },
            !model.busy && !model.uncertain && model.canTransfer,
            { iconOnly: true, round: true, iconSize: 18 }
        )
    );
    if (errorHeight)
        nodes.push(
            node(
                'Box',
                'linkError',
                rect(
                    0,
                    height - footerHeight - errorHeight,
                    width,
                    errorHeight
                ),
                {
                    background: 'errorContainer',
                    children: [
                        node('Icon', 'linkErrorIcon', rect(18, 12, 17, 17), {
                            icon: 'error',
                            color: 'error'
                        }),
                        label(
                            'linkErrorText',
                            rect(
                                45,
                                10,
                                Math.max(0, width - 63),
                                errorHeight - 20
                            ),
                            tr(model.error),
                            { wrap: true, color: 'error' }
                        )
                    ]
                }
            )
        );
    const footerTop = height - footerHeight;
    nodes.push(
        node('Box', 'linkFooter', rect(0, footerTop, width, footerHeight), {
            background: 'panel',
            children: [
                label(
                    'linkSelectionStatus',
                    rect(
                        18,
                        narrow ? 4 : 17,
                        Math.max(0, width - (narrow ? 36 : 250)),
                        28
                    ),
                    model.selectedCount > 0
                        ? tr('Selected') + ': ' + model.selectedCount
                        : tr(
                              model.dirty
                                  ? 'Links have unsaved changes'
                                  : 'Select objects and use the center button'
                          ),
                    { color: model.dirty ? 'action' : 'secondaryText' }
                ),
                button(
                    'linkClose',
                    rect(Math.max(8, width - 208), narrow ? 46 : 14, 90, 36),
                    tr('Close'),
                    '',
                    { type: 'close' },
                    !model.saving
                ),
                button(
                    'linkSave',
                    rect(Math.max(106, width - 110), narrow ? 46 : 14, 92, 36),
                    tr('Save'),
                    'save',
                    { type: 'save' },
                    !model.busy &&
                        model.dirty &&
                        !model.uncertain &&
                        model.valid !== false,
                    { highlighted: true }
                )
            ]
        })
    );
    return { nodes };
}

export function listHeader(model, width, language) {
    const count =
        model.total > model.count
            ? model.count + ' / ' + model.total
            : String(model.count);
    return {
        height: 42,
        nodes: [
            node('Box', 'linkListHeading', rect(0, 0, width, 42), {
                background: 'panelRaised',
                children: [
                    label(
                        'linkListTitle',
                        rect(12, 8, Math.max(0, width - 92), 26),
                        translate(
                            model.scope === 'available'
                                ? 'Available objects'
                                : 'Linked objects',
                            language
                        ),
                        { fontRole: 'bodyLarge', weight: 600 }
                    ),
                    label(
                        'linkListCount',
                        rect(Math.max(0, width - 76), 8, 66, 26),
                        count,
                        {
                            align: 'right',
                            color: 'secondaryText',
                            fontRole: 'secondary'
                        }
                    )
                ]
            })
        ]
    };
}

export function list(model, width, height, language) {
    const result = listHeader(model, width, language);
    result.body = rect(0, 42, width, Math.max(0, height - 42));
    result.viewport = rect(
        4,
        46,
        Math.max(0, width - 14),
        Math.max(0, height - 52)
    );
    result.rowInsets = { left: 6, right: 18, top: 6, bottom: 6 };
    result.rowWidth = Math.max(
        0,
        result.viewport.width - result.rowInsets.left - result.rowInsets.right
    );
    result.loading = !!model.loading && !model.count;
    if (!model.count && !result.loading && result.body.height > 0)
        result.nodes.push(
            label(
                'linkEmpty_' + model.scope,
                rect(
                    16,
                    42 + Math.max(0, (result.body.height - 80) / 2),
                    Math.max(0, width - 32),
                    Math.min(80, result.body.height)
                ),
                translate(
                    model.scope === 'available'
                        ? 'No available objects'
                        : 'No linked objects',
                    language
                ),
                { wrap: true, align: 'center', color: 'secondaryText' }
            )
        );
    return result;
}

export function row(record, width) {
    return {
        height: 64,
        nodes: [
            node('Action', 'linkRow_' + record.key, rect(0, 0, width, 64), {
                text: record.title,
                selected: !!record.selected,
                normalColor: 'transparent',
                rail: true,
                radius: 12,
                action: { type: 'select', key: record.key },
                dragValue: record.dragValue,
                children: [
                    node('Preview', 'linkRowPreview', rect(10, 10, 44, 44), {
                        source: record.previewUrl || '',
                        initials:
                            record.fallbackText ||
                            String(record.title).slice(0, 2).toUpperCase(),
                        icon: 'sobject',
                        accent: record.accent || 'action',
                        outlined: true,
                        round: false,
                        selected: !!record.selected,
                        radius: 12
                    }),
                    label(
                        'linkRowTitle',
                        rect(
                            64,
                            record.subtitle ? 10 : 21,
                            Math.max(0, width - 98),
                            23
                        ),
                        record.title,
                        { fontRole: 'bodyLarge', weight: 600 }
                    ),
                    ...(record.subtitle
                        ? [
                              label(
                                  'linkRowSubtitle',
                                  rect(64, 35, Math.max(0, width - 98), 18),
                                  String(record.subtitle).replace(
                                      /[\r\n\t]+/g,
                                      ' '
                                  ),
                                  {
                                      fontRole: 'secondary',
                                      color: 'secondaryText',
                                      maxLines: 1
                                  }
                              )
                          ]
                        : []),
                    ...(record.selected
                        ? [
                              node(
                                  'Icon',
                                  'linkRowCheck',
                                  rect(width - 26, 24, 16, 16),
                                  { icon: 'check-circle', color: 'action' }
                              )
                          ]
                        : [])
                ]
            })
        ]
    };
}

export function select(keys, records, index, anchor, control, shift) {
    if (index < 0 || index >= records.length) return keys;
    const key = records[index].key;
    if (shift && anchor >= 0) {
        const selected = records
            .slice(Math.min(anchor, index), Math.max(anchor, index) + 1)
            .map((row) => row.key);
        return control ? [...new Set([...keys, ...selected])] : selected;
    }
    return control
        ? keys.includes(key)
            ? keys.filter((value) => value !== key)
            : [...keys, key]
        : [key];
}
