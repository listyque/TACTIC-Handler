import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function tileHeader(model, width, language) {
    const open =
            !!model.hasChildren ||
            model.kind === 'snapshot' ||
            model.kind === 'file',
        left = open ? 26 : 0,
        badgeWidth = Math.min(
            width - left,
            30 + Math.ceil(model.typeWidth || 0)
        );
    return {
        nodes: [
            node('Action', 'resultTileOpen', rect(0, 0, 22, 22), {
                text: translate(
                    model.hasChildren
                        ? 'Open card contents'
                        : model.kind === 'snapshot'
                          ? 'Open snapshot'
                          : 'Open item',
                    language
                ),
                visible: open,
                radius: 11,
                normalColor: model.typeColor,
                action: { type: 'open' },
                children: [
                    node('Icon', 'resultTileOpenIcon', rect(5, 5, 12, 12), {
                        icon: 'chevron_right',
                        color: model.foreground
                    })
                ]
            }),
            node('Box', 'resultTileType', rect(left, 0, badgeWidth, 22), {
                background: model.typeColor,
                radius: 7,
                children: [
                    node('Icon', 'resultTileTypeIcon', rect(6, 5, 12, 12), {
                        icon: model.typeIcon,
                        color: model.foreground
                    }),
                    label(
                        'resultTileTypeLabel',
                        rect(22, 0, badgeWidth - 28, 22),
                        model.typeTitle,
                        {
                            fontRole: 'caption',
                            weight: 700,
                            color: model.foreground
                        }
                    )
                ]
            })
        ]
    };
}

export function previewOverlay(model, width, language) {
    const size = Math.ceil(model.textWidth || 50) + 12;
    return {
        nodes: model.latest
            ? [
                  node(
                      'Box',
                      'resultPreviewLatest',
                      rect(width - size - 8, 8, size, 20),
                      {
                          background: 'action',
                          radius: 10,
                          children: [
                              label(
                                  'resultPreviewLatestLabel',
                                  rect(6, 0, size - 12, 20),
                                  translate('LATEST', language),
                                  {
                                      fontRole: 'caption',
                                      weight: 700,
                                      color: model.foreground,
                                      align: 'center'
                                  }
                              )
                          ]
                      }
                  )
              ]
            : []
    };
}

export function branchPreview(model, width, height, language) {
    const process = model.kind === 'process',
        nodes = [
            node('Box', 'resultBranchTileSurface', rect(0, 0, width, height), {
                radius: 10,
                background: 'panel',
                border: model.typeColor
            })
        ];
    if (process) {
        let x = (width - 91) / 2;
        for (let index = 0; index < 4; index++) {
            const size = index === 1 ? 22 : 15;
            nodes.push(
                node(
                    'Box',
                    'resultBranchTileShape_' + index,
                    rect(x, (height - 22) / 2, size, size),
                    {
                        radius: size / 2,
                        background: index === 1 ? model.typeColor : 'outline'
                    }
                )
            );
            x += size + 8;
        }
    } else
        for (let index = 0; index < 3; index++)
            nodes.push(
                node(
                    'Box',
                    'resultBranchTileShape_' + index,
                    rect(
                        (width - 78) / 2,
                        (height - 33) / 2 + index * 13,
                        78 - index * 13,
                        7
                    ),
                    {
                        radius: 3,
                        background: index === 0 ? model.typeColor : 'outline'
                    }
                )
            );
    const key = process
        ? model.count === 1
            ? '{count} check-in'
            : '{count} check-ins'
        : model.count === 1
          ? '{count} related item'
          : '{count} related items';
    nodes.push(
        label(
            'resultBranchTileCount',
            rect(0, height - 24, width, 16),
            translate(key, language, { count: model.count || 0 }),
            {
                fontRole: 'secondary',
                weight: 600,
                color: model.typeColor,
                align: 'center',
                visible: process || model.count > 0
            }
        )
    );
    return { nodes };
}

export function tileHeight(model) {
    return model.kind === 'process' || model.kind === 'relation'
        ? 160
        : model.compact
          ? 164
          : 244;
}

export function tileLayout(model, width) {
    const height = tileHeight(model),
        object = model.kind === 'object',
        relation = model.kind === 'relation',
        previewHeight = object
            ? 30
            : relation
              ? 50
              : ['snapshot', 'file'].includes(model.kind)
                ? 158
                : 76;
    return {
        height,
        indent: 0,
        inset: 0,
        surfaceLeft: 0,
        reserve: 0,
        titleSize: 14,
        subtitleSize: 11,
        metadataHeight: 24,
        header: rect(8, 8, width - 16, previewHeight),
        disclosure: rect(8, 8, 22, 22),
        preview: object
            ? rect(0, 0, width, height)
            : rect((width - 154) / 2, 10, 154, 154),
        content: rect(
            8,
            8 + previewHeight + 4,
            width - 16,
            Math.max(0, height - previewHeight - 27)
        ),
        counts: rect(width - 71, height - 37, 63, 30)
    };
}

export function layout(model, width) {
    if (model.tile) return tileLayout(model, width);
    const kind = model.kind,
        object = kind === 'object',
        snapshot = kind === 'snapshot',
        branch = kind === 'process' || kind === 'relation',
        compact = !!model.compact,
        mobile = !!model.mobile,
        tile = !!model.tile,
        indent = Math.max(0, model.depth || 0) * 24;
    const height = tile
        ? 196
        : mobile
          ? object
              ? 104
              : snapshot
                ? 92
                : branch
                  ? 54
                  : 48
          : kind === 'group'
            ? 40
            : kind === 'relation'
              ? 38
              : kind === 'process'
                ? 32
                : compact
                  ? object
                      ? 64
                      : snapshot
                        ? 56
                        : 42
                  : object
                    ? 100
                    : snapshot
                      ? 84
                      : 49;
    const disclosure = rect(
        indent + (snapshot ? 9 : branch ? 2 : object ? (compact ? 12 : 24) : 0),
        0,
        object && !compact ? 36 : branch ? 28 : 30,
        height
    );
    const previewSize = tile
        ? 100
        : mobile
          ? 40
          : object
            ? compact
                ? 42
                : 68
            : snapshot
              ? compact
                  ? 38
                  : 58
              : branch
                ? 24
                : 28;
    const preview = rect(
        tile
            ? (width - previewSize) / 2
            : mobile
              ? 12
              : object
                ? disclosure.x + disclosure.width + (compact ? 8 : 18)
                : snapshot
                  ? indent + (model.hasChildren ? 45 : 14)
                  : indent + 45,
        (height - previewSize) / 2,
        previewSize,
        previewSize
    );
    if (tile) preview.y = 12;
    const contentLeft = tile
        ? 12
        : mobile
          ? 62
          : kind === 'file'
            ? indent + 47
            : preview.x +
              preview.width +
              (object ? (compact ? 10 : 26) : snapshot ? 12 : 9);
    const content = rect(
        contentLeft,
        tile ? 118 : 0,
        width - contentLeft - (snapshot ? 14 : 9),
        tile ? 66 : height
    );
    const reserve = tile
        ? 0
        : mobile
          ? 34
          : object
            ? compact
                ? 76
                : 170
            : snapshot
              ? 0
              : branch
                ? 84
                : 112;
    return {
        height,
        indent,
        disclosure,
        preview,
        content,
        reserve,
        surfaceLeft: indent + (branch ? 32 : 0),
        inset: object ? (compact ? 3 : 4) : snapshot ? 2 : 1,
        titleSize: object ? (compact ? 12 : 15) : 13,
        subtitleSize: compact ? 11 : 13,
        metadataHeight: compact ? 20 : 24
    };
}

export function body(model, width, height) {
    const geometry = layout(model, width),
        nodes = [],
        object = model.kind === 'object',
        snapshot = model.kind === 'snapshot',
        compact = !!model.compact,
        reserve = model.reserve == null ? geometry.reserve : model.reserve,
        available = Math.min(width, Math.max(48, width - reserve)),
        color = model.selected ? 'contentSelectionText' : 'secondaryText';
    if (model.tile) {
        let top = 0;
        nodes.push(
            node('View', 'resultTitle', rect(0, top, width, 18), {
                view: 'title',
                fontRole: 'bodyLarge',
                weight: 700
            })
        );
        top += 22;
        nodes.push(
            node('View', 'resultMetadata', rect(0, top, width, 24), {
                view: 'metadata',
                fontRole: 'caption',
                visible: !!model.hasMetadata
            })
        );
        if (model.hasMetadata) top += 28;
        nodes.push(
            label(
                'resultTileTechnical',
                rect(0, top, width, 16),
                model.technical || '',
                {
                    fontRole: 'secondary',
                    color: 'secondaryText',
                    visible: !!model.technical
                }
            )
        );
        if (model.technical) top += 20;
        nodes.push(
            label(
                'resultTileDescription',
                rect(
                    4,
                    top,
                    width - 12,
                    model.kind === 'object' && !compact ? 30 : 15
                ),
                model.subtitle || '',
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    visible: !!model.subtitle,
                    wrap: true
                }
            )
        );
    } else if (object) {
        const subtitle = !!model.subtitle,
            titleHeight = compact ? 18 : 22,
            subtitleHeight = compact ? 16 : 18,
            gap = compact ? 1 : 3,
            total =
                titleHeight +
                (subtitle ? subtitleHeight + gap : 0) +
                geometry.metadataHeight +
                gap,
            top = Math.max(0, (height - total) / 2);
        nodes.push(
            node('View', 'resultTitle', rect(0, top, width, titleHeight), {
                view: 'title',
                fontRole: compact ? 'secondary' : 'section',
                weight: 600
            })
        );
        let next = top + titleHeight + gap;
        if (subtitle) {
            nodes.push(
                label(
                    'workspaceObjectSubtitle',
                    rect(0, next, available, subtitleHeight),
                    model.subtitle,
                    { color, fontRole: compact ? 'caption' : 'body' }
                )
            );
            next += subtitleHeight + gap;
        }
        nodes.push(
            node(
                'View',
                'resultMetadata',
                rect(0, next, available, geometry.metadataHeight),
                { view: 'metadata', fontRole: 'caption' }
            )
        );
    } else if (
        model.mobile &&
        (snapshot || model.kind === 'process' || model.kind === 'relation')
    ) {
        const top = Math.max(0, (height - 42) / 2);
        nodes.push(
            node('View', 'resultTitle', rect(0, top, available, 22), {
                view: 'title',
                fontRole: 'body',
                weight: 600
            })
        );
        nodes.push(
            node(
                'View',
                'resultSnapshotTechnical',
                rect(0, top + 22, available, 20),
                { view: 'technical', fontRole: 'secondary' }
            )
        );
    } else if (model.kind === 'file' && !compact) {
        nodes.push(
            node('View', 'resultTitle', rect(0, (height - 34) / 2, width, 18), {
                view: 'title',
                fontRole: 'body',
                weight: 600
            })
        );
        nodes.push(
            node(
                'View',
                'resultFilePath',
                rect(0, (height - 34) / 2 + 20, width, 14),
                { view: 'technical', fontRole: 'caption' }
            )
        );
    } else if (snapshot && !compact && !model.mobile) {
        const top = (height - 68) / 2;
        nodes.push(
            node('View', 'resultTitle', rect(0, top, width, 24), {
                view: 'title'
            })
        );
        nodes.push(
            node(
                'View',
                'resultSnapshotTechnical',
                rect(0, top + 24, width, 24),
                { view: 'technical', fontRole: 'secondary' }
            )
        );
        nodes.push(
            node(
                'View',
                'resultSnapshotDescription',
                rect(0, top + 48, width, 20),
                { view: 'description', fontRole: 'secondary' }
            )
        );
    } else {
        nodes.push(
            node('View', 'resultTitle', rect(0, (height - 24) / 2, width, 24), {
                view: 'title',
                fontRole: model.kind === 'process' ? 'body' : 'secondary',
                weight: 600
            })
        );
    }
    return { nodes };
}
