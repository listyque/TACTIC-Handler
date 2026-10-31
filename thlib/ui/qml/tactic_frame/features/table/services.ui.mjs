import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Parallel from './parallel.ui.mjs';
import * as Drop from './drop.ui.mjs';
import * as Layout from './layout.ui.mjs';
import * as Time from './time.ui.mjs';
import * as Connections from './connections.ui.mjs';
import * as Parent from './parent.ui.mjs';
import * as Publish from './publish.ui.mjs';
import * as Nested from './nested.ui.mjs';
import { buttonWidth } from '../../controls/buttons/metrics.mjs';
import * as Cells from './cells.ui.mjs';

export function describe(
    cell,
    width,
    height,
    language,
    editable = true,
    expanded = {},
    server = ''
) {
    if (cell.valuePresentation)
        return Cells.valueLabel(
            cell.text,
            width,
            height,
            cell.valuePresentation
        );
    if (cell.publish)
        return Publish.describe(
            cell,
            width,
            height,
            language,
            editable,
            server
        );
    if (cell.parentGrouping !== undefined)
        return Parent.cell(cell, width, height, language, editable);
    if (cell.summary) return summary(cell, width, height, language);
    if (cell.connectionRows)
        return Connections.describe(cell, width, height, language);
    if (cell.timeline)
        return Time.timeline(cell, width, height, language, editable);
    if (cell.timeDays)
        return Time.hours(cell, width, height, language, editable);
    if (
        cell.layoutNodes &&
        (Layout.tables(cell.layoutNodes).length || cell.layoutLoad?.length)
    )
        return {
            nodes: [
                button(
                    'tableLayoutDocument',
                    rect(4, 0, Math.max(0, width - 24), 36),
                    translate('Open details', language),
                    'description',
                    { type: 'service', name: 'layout-document' },
                    true,
                    { outlined: true }
                )
            ]
        };
    if (cell.layoutNodes)
        return Layout.describe(cell, width, height, language, editable, server);
    if (cell.groups && cell.steps)
        return Parallel.describe(cell, width, height, language, expanded);
    if (cell.links || cell.ingest)
        return Drop.describe(cell, width, height, language, editable);
    if (cell.label && !cell.text)
        cell = Object.assign({}, cell, {
            text: translate(cell.label, language)
        });
    const actions = cell.actions || [];
    const nested = expanded.__nested;
    const nestedOpen =
        !!nested?.open &&
        String(nested.column || '') === String(cell.columnName || '') &&
        Nested.identity(nested.scope) === Nested.identity(cell.nestedTable);
    const combined =
        !!cell.text &&
        actions.length === 1 &&
        actions[0].name === 'nested-table';
    const size = combined ? Math.max(0, Math.min(34, height)) : 28,
        gap = 4;
    const inner = Math.max(0, width - 24);
    const textWidth = cell.text ? Math.max(0, inner - size - 8) : 0;
    const capacity = Math.max(1, Math.floor((inner + gap) / (size + gap)));
    const contentHeight = Math.max(
        size,
        Math.ceil(actions.length / capacity) * (size + gap) - gap
    );
    const children = [];
    if (cell.text && !combined)
        children.push(
            label(
                'tableServiceValue',
                rect(6, 0, textWidth, size),
                String(cell.text)
            )
        );
    actions.forEach((action, index) => {
        const icon =
            action.name === 'nested-table'
                ? nestedOpen && nested.busy
                    ? 'loading'
                    : nestedOpen
                      ? 'expand-more'
                      : action.icon || 'chevron-right'
                : action.icon;
        const enabled = editable && action.enabled !== false;
        const command = {
            type: 'service',
            name: action.name,
            view: action.view || ''
        };
        if (combined) {
            const options = cell.displayOptions || {},
                font = Cells.valueFont(options),
                leadingIcon = Object.prototype.hasOwnProperty.call(
                    options,
                    'value_icon'
                )
                    ? options.value_icon
                    : options.icon || options.title_icon || '',
                text = Cells.relatedLabel(cell.text, options),
                left = leadingIcon ? 36 : 12,
                w = Math.min(
                    inner,
                    buttonWidth(
                        (text.length * 7 * font.size) / Cells.metrics.bodyFont,
                        true
                    ) + (leadingIcon ? 24 : 0)
                );
            children.push(
                node(
                    'Action',
                    'tableServiceAction_' + index,
                    rect(
                        Cells.contentX(width, w, Cells.alignment(options), 12),
                        0,
                        w,
                        size
                    ),
                    {
                        text,
                        icon,
                        enabled,
                        role: 'button',
                        expanded: nestedOpen,
                        description:
                            action.translateLabel === false
                                ? action.label
                                : translate(action.label, language),
                        normalColor: 'surfaceContainerHigh',
                        radius: 4,
                        action: command,
                        children: [
                            node(
                                'Box',
                                'tableServiceBorder',
                                rect(0, 0, w, size),
                                { border: 'outlineVariant', radius: 4 }
                            ),
                            label(
                                'tableServiceValue',
                                rect(left, 0, Math.max(0, w - left - 36), size),
                                text,
                                {
                                    fontRole: font.role,
                                    weight: font.weight || 600,
                                    color: enabled
                                        ? 'primaryText'
                                        : 'disabledText'
                                }
                            ),
                            ...(leadingIcon
                                ? [
                                      node(
                                          'Icon',
                                          'tableServiceLeadingIcon',
                                          rect(12, (size - 16) / 2, 16, 16),
                                          {
                                              icon: leadingIcon,
                                              color: enabled
                                                  ? 'action'
                                                  : 'disabledText'
                                          }
                                      )
                                  ]
                                : []),
                            node(
                                'Icon',
                                'tableServiceDisclosure',
                                rect(
                                    Math.max(0, w - 28),
                                    (size - 16) / 2,
                                    16,
                                    16
                                ),
                                {
                                    icon,
                                    color: enabled
                                        ? action.iconColor || 'action'
                                        : 'disabledText'
                                }
                            )
                        ]
                    }
                )
            );
            return;
        }
        const rowStart = Math.floor(index / capacity) * capacity;
        const rowCount = Math.min(capacity, actions.length - rowStart);
        const rowWidth = rowCount * size + (rowCount - 1) * gap;
        const left = cell.text
            ? inner - size
            : Cells.contentX(
                  width,
                  rowWidth,
                  Cells.alignment(cell.displayOptions),
                  12
              ) +
              (index % capacity) * (size + gap);
        const top = cell.text ? 0 : Math.floor(index / capacity) * (size + gap);
        children.push(
            button(
                'tableServiceAction_' + index,
                rect(Math.max(0, left), top, size, size),
                action.translateLabel === false
                    ? action.label
                    : translate(action.label, language),
                icon,
                command,
                enabled,
                {
                    iconOnly: true,
                    destructive: !!action.destructive,
                    iconSize: action.iconSize,
                    iconColor: action.iconColor || undefined,
                    iconAction: !!action.iconAction
                }
            )
        );
    });
    return {
        nodes: [
            node(
                'Scroll',
                'tableServiceScroll',
                rect(
                    0,
                    Math.max(0, (height - contentHeight) / 2),
                    width,
                    Math.min(height, Math.max(size, contentHeight))
                ),
                {
                    contentHeight: Math.max(size, contentHeight),
                    scrollbarId: 'tableServiceScrollBar',
                    children
                }
            )
        ]
    };
}

function summary(cell, width, height, language) {
    const nodes = [];
    cell.summary.forEach((entry, index) => {
        const top = index * 28;
        const text = translate(entry.label, language) + ': ' + entry.value;
        const contents = [
            node('Icon', 'tableSummaryIcon_' + index, rect(8, 4, 20, 20), {
                icon: entry.icon,
                color: 'secondaryText'
            }),
            label(
                'tableSummaryText_' + index,
                rect(36, 0, Math.max(0, width - 60), 28),
                text
            )
        ];
        nodes.push(
            node(
                entry.nestedTable ? 'Action' : 'Box',
                'tableSummary_' + index,
                rect(0, top, Math.max(0, width - 16), 28),
                {
                    text,
                    children: contents,
                    action: entry.nestedTable
                        ? {
                              type: 'service',
                              name: 'nested-table',
                              nestedTable: entry.nestedTable
                          }
                        : null
                }
            )
        );
    });
    return {
        nodes: [
            node('Scroll', 'tableSummary', rect(0, 0, width, height), {
                children: nodes,
                contentHeight: cell.summary.length * 28,
                scrollbarId: 'tableSummaryScrollBar'
            })
        ]
    };
}
