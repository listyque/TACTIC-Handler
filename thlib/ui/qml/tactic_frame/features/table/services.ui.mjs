import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Parallel from './parallel.ui.mjs';
import * as Drop from './drop.ui.mjs';
import * as Layout from './layout.ui.mjs';

export function describe(
    cell,
    width,
    height,
    language,
    editable = true,
    expanded = {},
    server = ''
) {
    if (cell.layoutNodes)
        return Layout.describe(cell, width, height, language, editable, server);
    if (cell.groups && cell.steps)
        return Parallel.describe(cell, width, height, language, expanded);
    if (cell.links)
        return Drop.describe(cell, width, height, language, editable);
    const actions = cell.actions || [];
    const size = 28,
        gap = 4;
    const inner = Math.max(0, width - 24);
    const textWidth = cell.text ? Math.max(0, inner - size - 8) : 0;
    const capacity = Math.max(1, Math.floor((inner + gap) / (size + gap)));
    const contentHeight = Math.max(
        size,
        Math.ceil(actions.length / capacity) * (size + gap) - gap
    );
    const children = [];
    if (cell.text)
        children.push(
            label(
                'tableServiceValue',
                rect(6, 0, textWidth, size),
                String(cell.text)
            )
        );
    actions.forEach((action, index) => {
        const left =
            cell.align === 'center' && !cell.text && actions.length === 1
                ? (width - size) / 2
                : cell.text
                  ? inner - size
                  : 4 + (index % capacity) * (size + gap);
        const top = cell.text ? 0 : Math.floor(index / capacity) * (size + gap);
        children.push(
            button(
                'tableServiceAction_' + index,
                rect(Math.max(0, left), top, size, size),
                action.translateLabel === false
                    ? action.label
                    : translate(action.label, language),
                action.icon,
                { type: 'service', name: action.name, view: action.view || '' },
                editable && action.enabled !== false,
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
