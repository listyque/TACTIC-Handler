import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { link } from './cells.ui.mjs';

export function describe(cell, width, height, language) {
    if (!cell.connectionRows?.length) {
        return {
            nodes: [
                label(
                    'tableConnectionsEmpty',
                    rect(8, 0, Math.max(0, width - 16), height),
                    translate('No connections', language),
                    { color: 'secondaryText' }
                )
            ]
        };
    }
    return {
        nodes: [
            node('List', 'tableConnections', rect(0, 0, width, height), {
                source: 'connectionRows',
                keyField: 'connectionKey',
                fields: [
                    'connectionKey',
                    'expectedRevision',
                    'available',
                    'searchKey',
                    'code',
                    'name',
                    'description',
                    'keywords',
                    'retired',
                    'preview'
                ],
                rowHeight: Math.max(64, cell.iconSize || 60) + 32,
                scrollbarId: 'tableConnectionsScrollBar',
                label: translate('Connections', language),
                role: 'list'
            })
        ]
    };
}

export function row(record, cell, width, language, editable, server) {
    const tr = (text) => translate(text, language),
        iconSize = cell.iconSize || 60;
    const title = record.available
        ? [record.code, record.name]
              .filter(
                  (value, index, values) =>
                      value && values.indexOf(value) === index
              )
              .join(' · ')
        : tr('Object is unavailable');
    const content = [],
        textLeft = iconSize + 12,
        textWidth = Math.max(0, width - textLeft - 40);
    if (record.available) {
        content.push(
            node(
                'Action',
                'tableConnectionPreviewAction',
                rect(4, 4, iconSize, iconSize),
                {
                    text: tr('Details'),
                    action: {
                        type: 'service',
                        name: 'sobject_detail',
                        targetSearchKey: record.searchKey
                    },
                    children: [
                        node(
                            'Preview',
                            'tableConnectionPreview',
                            rect(0, 0, iconSize, iconSize),
                            {
                                source:
                                    link(record.preview?.image, server) || '',
                                initials: String(record.code || '').slice(0, 2),
                                icon: 'sobject',
                                round: false,
                                outlined: false
                            }
                        )
                    ]
                }
            )
        );
        if (record.preview?.filename && link(record.preview.text, server)) {
            content.push(
                node(
                    'Action',
                    'tableConnectionFile',
                    rect(
                        4,
                        Math.max(iconSize, 64) + 6,
                        Math.max(0, width - (record.retired ? 100 : 8)),
                        22
                    ),
                    {
                        text: record.preview.filename,
                        action: {
                            type: 'service',
                            name: 'layout-link',
                            href: link(record.preview.text, server)
                        },
                        children: [
                            label(
                                'tableConnectionFilename',
                                rect(
                                    0,
                                    0,
                                    Math.max(
                                        0,
                                        width - (record.retired ? 100 : 8)
                                    ),
                                    22
                                ),
                                record.preview.filename,
                                {
                                    color: 'action',
                                    fontRole: 'caption',
                                    toolTip: record.preview.filename
                                }
                            )
                        ]
                    }
                )
            );
        }
        content.push(
            label(
                'tableConnectionObject',
                rect(textLeft, 1, textWidth, 24),
                title,
                { toolTip: title }
            )
        );
        content.push(
            label(
                'tableConnectionDescription',
                rect(textLeft, 25, textWidth, 20),
                record.description || '',
                { color: 'secondaryText', toolTip: record.description || '' }
            )
        );
        content.push(
            label(
                'tableConnectionKeywords',
                rect(textLeft, 45, textWidth, 18),
                record.keywords || '',
                { color: 'secondaryText', fontRole: 'caption' }
            )
        );
        if (record.retired)
            content.push(
                label(
                    'tableConnectionRetired',
                    rect(
                        Math.max(4, width - 92),
                        Math.max(iconSize, 64) + 6,
                        Math.min(88, width),
                        22
                    ),
                    tr('Retired'),
                    { color: 'secondaryText', fontRole: 'caption' }
                )
            );
    } else {
        content.push(
            label(
                'tableConnectionMissing',
                rect(8, 4, Math.max(0, width - 52), Math.max(64, iconSize)),
                title,
                { color: 'secondaryText', wrap: true }
            )
        );
    }
    content.push(
        button(
            'tableConnectionRemove',
            rect(
                Math.max(0, width - 36),
                Math.max(0, (iconSize - 24) / 2),
                32,
                32
            ),
            tr('Remove connection'),
            'delete',
            {
                type: 'service',
                name: 'remove-connection',
                connectionKey: record.connectionKey,
                expectedRevision: record.expectedRevision,
                parentKey: cell.targetSearchKey,
                direction: cell.direction || 'dst'
            },
            editable,
            { iconOnly: true, destructive: true }
        )
    );
    return { nodes: content };
}
