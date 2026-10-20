import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function droppedKeys(value, accepted) {
    if (
        !value ||
        value.searchType !== accepted ||
        !Array.isArray(value.searchKeys) ||
        value.searchKeys.length > 500 ||
        value.searchKeys.some((key) => typeof key !== 'string' || !key)
    )
        throw new Error('Dropped objects belong to another Search Type');
    return [...new Set(value.searchKeys)];
}

export function describe(cell, width, height, language, editable) {
    const inner = Math.max(0, width - 24),
        links = cell.links || [],
        children = [];
    if (cell.available === false) {
        children.push(
            label(
                'dropDiagnostic',
                rect(4, 0, inner, 28),
                translate(cell.diagnostic, language),
                {
                    color: 'secondaryText',
                    tooltip: translate(cell.diagnostic, language)
                }
            )
        );
    } else {
        children.push(
            button(
                'dropEdit',
                rect(4, 0, 28, 28),
                translate('Link SObjects', language),
                'link',
                { type: 'service', name: 'edit-links' },
                editable,
                { iconOnly: true, iconAction: true }
            )
        );
        children.push(
            label(
                'dropCount',
                rect(36, 0, Math.max(0, inner - 36), 28),
                String(links.length),
                { color: 'secondaryText' }
            )
        );
        links.forEach((link, index) =>
            children.push(
                node(
                    'Action',
                    'dropItem_' + index,
                    rect(4, 32 + index * 28, Math.max(0, inner - 8), 26),
                    {
                        text: link.label,
                        tooltip: link.label,
                        action: {
                            type: 'service',
                            name: 'sobject_detail',
                            targetSearchKey: link.searchKey
                        },
                        dragValue: editable
                            ? {
                                  searchType: cell.acceptedType,
                                  searchKeys: [link.searchKey]
                              }
                            : null,
                        enabled: true,
                        background: 'transparent',
                        radius: 4
                    }
                )
            )
        );
    }
    return {
        nodes: [
            node('Box', 'dropSurface', rect(0, 0, width, height), {
                background: cell.backgroundColor || 'transparent',
                radius: 0,
                enabled: true,
                dropAction:
                    editable && cell.available !== false
                        ? { type: 'service', name: 'drop-links' }
                        : null,
                children: [
                    node('Scroll', 'dropScroll', rect(0, 0, width, height), {
                        contentHeight:
                            cell.available === false
                                ? 28
                                : 32 + links.length * 28,
                        scrollbarId: 'dropScrollBar',
                        children
                    })
                ]
            })
        ]
    };
}
