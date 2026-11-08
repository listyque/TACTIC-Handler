import { spacing } from '../../core/foundation.mjs';
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = {
    toolbar: 46,
    summary: 59,
    splitter: 8,
    bodyMargin: spacing.content,
    minimumRatio: 0.22,
    maximumRatio: 0.78
};

export function clampRatio(value, extent, vertical) {
    const candidate = Number.isFinite(value) ? value : 0.52;
    const primary = vertical ? 120 : 90,
        secondary = vertical ? 180 : 120;
    if (extent <= 1) return Math.max(0.22, Math.min(0.78, candidate));
    const lower = Math.max(0.22, (primary + metrics.splitter / 2) / extent);
    const upper = Math.min(
        0.78,
        1 - (secondary + metrics.splitter / 2) / extent
    );
    return lower > upper
        ? primary / (primary + secondary)
        : Math.max(lower, Math.min(upper, candidate));
}

export function fileColumns(showMore, width) {
    return {
        size: !!showMore && width >= 340,
        path: !!showMore && width >= 650,
        repository: !!showMore && width >= 820,
        base: !!showMore && width >= 940
    };
}

export function fileIcon(rowType, fileType, baseType, filename) {
    if (rowType === 'snapshot') return 'snapshot';
    if (rowType === 'type') return 'folder';
    const type = String(fileType || '').toLowerCase();
    if (['image', 'icon', 'web'].indexOf(type) >= 0) return 'image';
    if (['playblast', 'movie', 'video'].indexOf(type) >= 0) return 'movie';
    if (
        String(baseType || '')
            .toLowerCase()
            .indexOf('sequence') >= 0
    )
        return 'sequence';
    if (/\.(zip|rar|7z|tar|gz)$/i.test(String(filename || '')))
        return 'archive';
    return 'file';
}

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language);
    const nodes = [
        node('Box', 'snapshotToolbarSurface', rect(0, 0, width, 46), {
            background: 'surfaceContainerLow',
            radius: 0
        }),
        node('View', 'snapshotOptions', rect(10, 5, 36, 36), {
            view: 'options'
        }),
        node('Box', 'snapshotToolbarDivider', rect(0, 45, width, 1), {
            background: 'outlineVariant',
            radius: 0
        })
    ];
    if (model.contentMode !== 'files' && !model.phone) {
        const size = Math.min(206, Math.max(0, width - 106));
        ['fit', 'fill'].forEach((value, index) =>
            nodes.push(
                button(
                    'snapshotImage_' + value,
                    rect(
                        (width - size) / 2 + index * (size / 2 + 2),
                        6,
                        size / 2 - 2,
                        34
                    ),
                    tr(value === 'fit' ? 'Fit' : 'Fill'),
                    '',
                    { type: 'image', value },
                    true,
                    { radio: true, selected: model.imageMode === value }
                )
            )
        );
    }
    nodes.push(
        button(
            'snapshotRefresh',
            rect(Math.max(0, width - 44), 5, 36, 36),
            tr('Refresh snapshots'),
            'refresh',
            { type: 'refresh' },
            model.canRefresh !== false,
            { iconOnly: true, iconSize: 16 }
        )
    );
    return { nodes, height: 46 };
}

export function optionActions(model) {
    return [
        ...(model.canCompare !== undefined
            ? [
                  {
                      title: 'Compare snapshots',
                      icon: 'image',
                      command: 'compare',
                      enabled: model.canCompare
                  },
                  { separator: true }
              ]
            : []),
        {
            title: 'Preview and Files',
            icon: 'grid-view',
            command: 'content_both',
            checked: model.contentMode === 'both'
        },
        {
            title: 'Preview Only',
            icon: 'image',
            command: 'content_preview',
            checked: model.contentMode === 'preview'
        },
        {
            title: 'Files Only',
            icon: 'view-list',
            command: 'content_files',
            checked: model.contentMode === 'files'
        },
        { separator: true },
        {
            title: 'Show All Files',
            icon: 'visibility',
            command: 'show_all',
            checked: !!model.showAll,
            role: 'menuitemcheckbox'
        },
        {
            title: 'Show More Info',
            icon: 'info',
            command: 'show_more',
            checked: !!model.showMore,
            role: 'menuitemcheckbox'
        },
        { separator: true }
    ].concat(
        model.phone
            ? [
                  {
                      title: 'Fit',
                      command: 'image_fit',
                      checked: model.imageMode === 'fit'
                  },
                  {
                      title: 'Fill',
                      command: 'image_fill',
                      checked: model.imageMode === 'fill'
                  }
              ]
            : [
                  {
                      title: 'Horizontal orientation',
                      icon: 'view-agenda',
                      command: 'horizontal',
                      checked: model.orientation === 'horizontal'
                  },
                  {
                      title: 'Vertical orientation',
                      icon: 'view-column',
                      command: 'vertical',
                      checked: model.orientation === 'vertical'
                  }
              ]
    );
}

export function comparisonChoices(records) {
    return Array.from(records)
        .filter(
            (record) =>
                record.url &&
                record.snapshotId &&
                /\.(png|jpe?g|webp|gif|bmp|tiff?)$/i.test(record.title)
        )
        .map((record) =>
            Object.assign({}, record, {
                value: record.token,
                label: ['v' + record.version, record.context, record.title]
                    .filter(Boolean)
                    .join(' · ')
            })
        );
}

export function comparisonPair(choices, left, right) {
    const a =
        choices.find((row) => row.value === left) ||
        choices.find((row) => Number(row.version) > 0) ||
        choices[0];
    const b =
        choices.find(
            (row) => row.value === right && row.snapshotId !== a?.snapshotId
        ) ||
        choices.find(
            (row) => Number(row.version) > 0 && row.snapshotId !== a?.snapshotId
        ) ||
        choices.find((row) => row.snapshotId !== a?.snapshotId);
    return [a, b];
}

export function comparisonLayout(width, height, mode, position) {
    const margin = metrics.bodyMargin,
        gap = metrics.splitter;
    const w = Math.max(0, width - 2 * margin),
        half = Math.max(0, (w - gap) / 2);
    const top = 88,
        divider = mode === 'divider';
    const h = Math.max(0, height - top - margin - (divider ? 30 : 0));
    const split = Math.max(0, Math.min(1, position / 100)) * w;
    return {
        pickers: [
            rect(margin, 44, half, 36),
            rect(margin + half + gap, 44, half, 36)
        ],
        a: rect(margin, top, divider ? w : half, h),
        b: rect(
            margin + (divider ? split : half + gap),
            top,
            divider ? w - split : half,
            h
        ),
        bOffset: divider ? -split : 0,
        bWidth: divider ? w : half,
        line: rect(margin + split, top, 1, h),
        slider: rect(margin, top + h + 2, w, 26)
    };
}

export function comparisonToolbar(mode, width, language) {
    const margin = metrics.bodyMargin,
        gap = metrics.splitter;
    const size = Math.min(
        140,
        Math.max(0, (width - 2 * margin - 36 - 2 * gap) / 2)
    );
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            button(
                'snapshotCompareSide',
                rect(margin, 5, size, 34),
                tr('Side by side'),
                '',
                { type: 'mode', value: 'side' },
                true,
                { radio: true, selected: mode === 'side' }
            ),
            button(
                'snapshotCompareDivider',
                rect(margin + size + gap, 5, size, 34),
                tr('Image divider'),
                '',
                { type: 'mode', value: 'divider' },
                true,
                { radio: true, selected: mode === 'divider' }
            ),
            button(
                'snapshotCompareClose',
                rect(Math.max(0, width - margin - 36), 5, 36, 34),
                tr('Close comparison'),
                'close',
                { type: 'close' },
                true,
                { iconOnly: true, round: false }
            )
        ],
        height: 44
    };
}

export function optionChange(model, command) {
    if (command.startsWith('content_'))
        return { key: 'contentMode', value: command.slice(8) };
    if (command.startsWith('image_'))
        return { key: 'imageMode', value: command.slice(6) };
    if (command === 'show_all')
        return { key: 'showAll', value: !model.showAll };
    if (command === 'show_more')
        return { key: 'showMore', value: !model.showMore };
    if (command === 'horizontal' || command === 'vertical')
        return { key: 'orientation', value: command };
    throw Error('Unknown snapshot option: ' + command);
}

export function layout(model, width, height) {
    const preview = model.contentMode !== 'files',
        files = model.contentMode !== 'preview';
    const gap = metrics.splitter;
    const margin = 0;
    const w = Math.max(0, width - margin * 2),
        h = Math.max(0, height - margin * 2);
    const vertical = model.orientation === 'vertical';
    const ratio = clampRatio(model.ratio, vertical ? w : h, vertical);
    const split = (vertical ? w : h) * ratio;
    return {
        preview: rect(
            margin,
            margin,
            preview && files && vertical ? split - gap / 2 : w,
            preview && files && !vertical ? split - gap / 2 : h
        ),
        files: rect(
            margin + (preview && files && vertical ? split + gap / 2 : 0),
            margin + (preview && files && !vertical ? split + gap / 2 : 0),
            preview && files && vertical ? w - split - gap / 2 : w,
            preview && files && !vertical ? h - split - gap / 2 : h
        ),
        splitter: vertical
            ? rect(margin + split - gap / 2, margin, gap, h)
            : rect(margin, margin + split - gap / 2, w, gap),
        previewVisible: preview,
        filesVisible: files,
        splitVisible: preview && files,
        ratio
    };
}

export function summary(
    model,
    width,
    language,
    measure = (text, size) => String(text).length * size * 0.55
) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const color = model.selected ? 'selectedText' : 'primaryText';
    const muted = model.selected ? 'selectedText' : 'secondaryText';
    const advance = (text, maximum, size = 11, weight = 400, padding = 12) =>
        Math.min(
            maximum,
            Math.ceil(measure(text || '', size, weight)) + padding
        );
    const metadata = [
        model.isLatest ? { text: tr('LATEST'), badge: true } : null,
        model.version
            ? { text: model.version, color: 'action', weight: 600 }
            : null,
        model.revision ? { text: model.revision } : null,
        model.repository
            ? {
                  text: model.repository,
                  color: model.repositoryColor || 'action'
              }
            : null
    ].filter(Boolean);
    const metaWidth = Math.min(
        width * 0.62,
        metadata.reduce(
            (sum, row) =>
                sum +
                advance(
                    row.text,
                    86,
                    row.badge ? 11 : 12,
                    row.badge ? 700 : row.weight || 400,
                    row.badge ? 8 : 0
                ) +
                5,
            -5
        )
    );
    const offline =
        model.fileExists === false && model.title
            ? '(' + tr('File Offline') + ')'
            : '';
    const offlineWidth = offline
        ? Math.min(width * 0.3, advance(offline, 142, 12, 400, 0))
        : 0;
    const titleWidth = Math.max(
        0,
        Math.min(
            Math.ceil(measure(model.title || '', 14, 600)),
            width -
                Math.max(0, metaWidth) -
                7 -
                offlineWidth -
                (offline ? 7 : 0)
        )
    );
    nodes.push(
        label(
            'snapshotSummaryTitle',
            rect(0, 0, titleWidth, 18),
            model.title || '',
            { fontRole: 'bodyLarge', weight: 600, color, elideMiddle: true }
        )
    );
    if (offline)
        nodes.push(
            label(
                'snapshotSummaryOffline',
                rect(titleWidth + 7, 0, offlineWidth, 18),
                offline,
                { color: 'error', fontRole: 'secondary' }
            )
        );
    let left = Math.max(0, width - metaWidth);
    for (let index = 0; index < metadata.length; index++) {
        const row = metadata[index],
            w = Math.min(
                advance(
                    row.text,
                    86,
                    row.badge ? 11 : 12,
                    row.badge ? 700 : row.weight || 400,
                    row.badge ? 8 : 0
                ),
                Math.max(0, width - left)
            );
        if (row.badge)
            nodes.push(
                node(
                    'Box',
                    'snapshotSummaryLatestBadge',
                    rect(left, 1, w, 16),
                    { background: 'contentSelection', radius: 8 }
                )
            );
        nodes.push(
            label(
                'snapshotSummaryMeta_' + index,
                rect(left, 0, w, 18),
                row.text,
                {
                    color: row.badge ? 'action' : row.color || muted,
                    align: row.badge ? 'center' : 'left',
                    weight: row.badge ? 700 : row.weight || 400,
                    fontRole: row.badge ? 'caption' : 'secondary'
                }
            )
        );
        left += w + 5;
    }
    function infoChip(id, text, x, y, w, raised) {
        return node('Box', id, rect(x, y, w, 17), {
            background: model.selected
                ? 'selected'
                : raised
                  ? 'surfaceContainerHigh'
                  : 'transparent',
            border: model.selected ? 'action' : 'outline',
            radius: 8.5,
            children: [
                label(id + 'Text', rect(5, 1, Math.max(0, w - 10), 15), text, {
                    fontRole: 'caption',
                    color: muted,
                    align: 'center'
                })
            ]
        });
    }
    left = 0;
    const chips = [model.fileSize, model.author, model.timestamp].filter(
        Boolean
    );
    for (let index = 0; index < chips.length; index++) {
        const w = Math.min(
            advance(chips[index], 142),
            Math.max(0, width - left)
        );
        nodes.push(
            infoChip(
                'snapshotSummaryChip_' + index,
                chips[index],
                left,
                22,
                w,
                false
            )
        );
        left += w + 5;
    }
    const info = model.infoChips || [];
    const descriptionWidth = info.length
        ? Math.min(width, Math.max(48, width * 0.36))
        : width;
    nodes.push(
        label(
            'snapshotSummaryDescription',
            rect(0, 43, descriptionWidth, 16),
            model.description || '',
            { fontRole: 'secondary', color: muted }
        )
    );
    left = info.length ? descriptionWidth + 9 : width;
    for (let index = 0; index < info.length; index++) {
        const text = tr(info[index].label) + ': ' + info[index].value;
        const w = Math.min(advance(text, 132), Math.max(0, width - left));
        nodes.push(
            infoChip('snapshotSummaryInfo_' + index, text, left, 43, w, true)
        );
        left += w + 9;
    }
    return { nodes, height: metrics.summary };
}
