import { node } from '../../../core/frame.mjs';
import { rect, label, muted } from '../admin.document.mjs';
import { translate } from '../../../core/strings.mjs';
import { binding } from './layout.document.mjs';
const number = (value, fallback, min, max) =>
    Number.isFinite(Number(value))
        ? Math.max(min, Math.min(max, Number(value)))
        : fallback;
function variant(sample) {
    return sample.kind === 'branch'
        ? (sample.branch || {}).kind || 'versions'
        : sample.kind === 'object'
          ? sample.depth
              ? 'children'
              : 'main'
          : sample.kind;
}
function visible(item, sample, layout, width) {
    const branch = sample.branch || {},
        snapshot = sample.snapshot_display || {},
        conditions = {
            desktop: width >= 700,
            mobile: width < 700,
            tree: layout.collection === 'tree',
            'not-tree': layout.collection !== 'tree',
            object: sample.kind === 'object',
            'object-or-process':
                sample.kind === 'object' || branch.kind === 'process',
            'not-branch': sample.kind !== 'branch',
            description:
                sample.kind !== 'branch' &&
                sample.kind !== 'snapshot' &&
                !!(sample.subtitle || (sample.record || {}).description),
            snapshot: sample.kind === 'snapshot',
            branch: sample.kind === 'branch',
            relation: branch.kind === 'relation',
            'mobile-upload':
                sample.kind === 'object' || branch.kind === 'process'
        };
    return (
        !item.hidden &&
        (item.variant === 'all' || item.variant === variant(sample)) &&
        (item.when || []).every((key) => conditions[key]) &&
        (item.kind !== 'knowledge' || (sample.knowledge || []).length > 0) &&
        (item.kind !== 'snapshot-size' || snapshot.size !== undefined) &&
        (item.kind !== 'file-offline' || !snapshot.exists)
    );
}
function tracks(value, count, width) {
    const tokens = String(value || '')
            .trim()
            .split(/\s+/),
        sizes = [],
        weights = [];
    let fixed = 0,
        weight = 0;
    for (let index = 0; index < count; index++) {
        const token = tokens.length === count ? tokens[index] : '1fr',
            pixels = /^\d+px$/.test(token) ? Number(token.slice(0, -2)) : 0,
            flex = /^\d+fr$/.test(token)
                ? Number(token.slice(0, -2))
                : token === 'auto'
                  ? 1
                  : 0;
        sizes.push(pixels);
        weights.push(flex);
        fixed += pixels;
        weight += flex;
    }
    const scale = fixed > width ? width / fixed : 1;
    return sizes.map((value, index) =>
        value
            ? value * scale
            : (Math.max(0, width - fixed) * weights[index]) /
              Math.max(1, weight)
    );
}
function safeImage(value, base, local) {
    const text = String(value || '');
    if (
        !text ||
        /[\u0000-\u0020\u007f\\]/.test(text) ||
        text.indexOf('//') === 0
    )
        return '';
    if (text.charAt(0) === '/') return (base || '') + text;
    return /^(https?:|blob:|data:image\/(?:png|jpeg|webp|gif);base64,)/i.test(
        text
    ) ||
        (local && /^file:/i.test(text))
        ? text
        : '';
}
export function sample(model, ui, language) {
    const tr = (text) => translate(text, language),
        item = (model.sampleItems || [])[0] || {
            record: {
                name: tr('Example object'),
                description: tr('Example description')
            },
            title: tr('Example object'),
            subtitle: tr('Example description'),
            task_count: 3,
            note_count: 2
        },
        kind =
            ['process', 'relation', 'versions'].indexOf(ui.sampleVariant) >= 0
                ? 'branch'
                : ['snapshot', 'file'].indexOf(ui.sampleVariant) >= 0
                  ? ui.sampleVariant
                  : 'object';
    return Object.assign({}, item, {
        kind,
        depth: ui.sampleVariant === 'children' ? 1 : 0,
        branch:
            kind === 'branch'
                ? {
                      kind: ui.sampleVariant,
                      title: tr(
                          ui.sampleVariant === 'process'
                              ? 'Process'
                              : 'Related and child objects'
                      ),
                      count: 3,
                      relationship: 'instance'
                  }
                : undefined
    });
}
export function describe(
    layout,
    sample,
    width,
    selected,
    language,
    screenWidth,
    assetBase,
    prefix,
    depth
) {
    const tr = (text) => translate(text, language),
        nodes = [],
        namePrefix = prefix || 'layoutPreview',
        level = depth || 0;
    if (level >= 8)
        return {
            nodes: [
                label(
                    namePrefix + 'Depth',
                    rect(0, 0, width, 64),
                    tr('Layout container depth exceeds 8'),
                    {
                        wrap: true,
                        color: 'error'
                    }
                )
            ],
            height: 72
        };
    const elements = (layout.elements || []).filter((item) =>
            visible(item, sample, layout, screenWidth || width)
        ),
        snapshot = sample.snapshot_display || {},
        record = sample.record || {},
        title =
            sample.title ||
            record.name ||
            record.title ||
            record.code ||
            String(record.id || ''),
        subtitle = sample.subtitle || record.description || '';
    function draw(item, box, inner) {
        const id = namePrefix + '_' + item.name,
            children = [],
            options = item.options || {},
            value = options.bind
                ? binding(options.bind, sample)
                : options.text || '',
            text =
                typeof value === 'object'
                    ? JSON.stringify(value)
                    : String(value),
            color = item.tone === 'muted' ? 'secondaryText' : 'primaryText',
            weight =
                item.tone === 'strong' || item.kind === 'title' ? 600 : 400;
        if (item.kind === 'group') {
            children.push(
                node(
                    'Box',
                    id + 'Group',
                    rect(
                        4,
                        4,
                        Math.max(0, box.width - 8),
                        Math.max(0, box.height - 8)
                    ),
                    {
                        children: inner ? inner.nodes : []
                    }
                )
            );
        } else if (item.kind === 'view') {
            if (inner) {
                const owned = (nodes) =>
                    nodes.map((row) =>
                        Object.assign({}, row, {
                            action:
                                row.action && row.action.type === 'select'
                                    ? {
                                          type: 'select',
                                          name: item.name
                                      }
                                    : row.action,
                            children: owned(row.children || [])
                        })
                    );
                children.push(
                    node(
                        'Box',
                        id + 'View',
                        rect(4, 4, box.width - 8, box.height - 8),
                        {
                            children: owned(inner.nodes)
                        }
                    )
                );
            } else
                children.push(
                    label(
                        id + 'ViewHelp',
                        rect(4, 4, box.width - 8, box.height - 8),
                        tr('Reusable view') +
                            ': ' +
                            (options.view || '') +
                            ' · ' +
                            tr('Check and preview'),
                        {
                            wrap: true,
                            color: 'secondaryText'
                        }
                    )
                );
        } else if (item.kind === 'image') {
            const initials =
                title
                    .split(/\s+/)
                    .map((part) => part.charAt(0))
                    .slice(0, 2)
                    .join('')
                    .toUpperCase() || '?';
            children.push(
                node(
                    'Preview',
                    id + 'Image',
                    rect(
                        4,
                        4,
                        Math.max(0, box.width - 8),
                        Math.max(0, box.height - 8)
                    ),
                    {
                        source: safeImage(
                            value,
                            assetBase,
                            options.bind === 'node.preview.image' &&
                                sample.preview &&
                                sample.preview.local === true
                        ),
                        initials,
                        icon: 'image',
                        round: item.role === 'preview',
                        outlined: false,
                        fit: options.fit || 'cover'
                    }
                )
            );
        } else if (item.kind === 'button' || item.kind === 'link') {
            const badge = options.badge
                    ? Number(binding(options.badge, sample))
                    : 0,
                caption =
                    text ||
                    (item.kind === 'button'
                        ? tr(
                              {
                                  tasks: 'Tasks',
                                  notes: 'Notes',
                                  inspect: 'Object details',
                                  operate: 'Object actions',
                                  upload: 'Add files',
                                  create: 'Create related object',
                                  preview: 'File preview',
                                  relations: 'Relationship actions',
                                  link: 'Link'
                              }[options.action] || 'Button'
                          )
                        : options.href || tr('Link'));
            children.push(
                node(
                    'Button',
                    id + 'Button',
                    rect(
                        4,
                        4,
                        Math.max(0, box.width - 8),
                        Math.max(0, Math.min(38, box.height - 8))
                    ),
                    {
                        text:
                            caption +
                            (Number.isFinite(badge) && badge > 0
                                ? ' · ' + badge
                                : ''),
                        icon:
                            options.icon ||
                            {
                                tasks: 'task',
                                notes: 'notes',
                                upload: 'upload',
                                inspect: 'search',
                                relations: 'link'
                            }[options.action] ||
                            ''
                    }
                )
            );
        } else if (item.kind === 'item-menu')
            children.push(
                node(
                    'Button',
                    id + 'Menu',
                    rect(
                        Math.max(0, box.width - 38),
                        0,
                        Math.min(38, box.width),
                        38
                    ),
                    {
                        text: tr('Item actions'),
                        icon: 'more-vert',
                        iconOnly: true
                    }
                )
            );
        else if (item.kind === 'quick-actions' || item.kind === 'relations') {
            const icons =
                    item.kind === 'relations'
                        ? ['link', 'add']
                        : ['preview', 'download', 'upload'],
                size = Math.min(32, box.width / icons.length);
            icons.forEach((icon, index) =>
                children.push(
                    node(
                        'Button',
                        id + 'Action_' + index,
                        rect(index * size, 0, size, 32),
                        {
                            text: tr(
                                item.kind === 'relations'
                                    ? 'Relationship actions'
                                    : 'Snapshot actions'
                            ),
                            icon,
                            iconOnly: true
                        }
                    )
                )
            );
        } else {
            let content = text;
            if (item.kind === 'title') content = text || title;
            else if (item.kind === 'description') content = text || subtitle;
            else if (item.kind === 'metadata')
                content = [
                    sample.search_type_label || record.search_type || '',
                    record.category || '',
                    record.process || ''
                ]
                    .filter(Boolean)
                    .join(' · ');
            else if (item.kind === 'snapshot-details')
                content = [
                    snapshot.version === undefined
                        ? ''
                        : 'v' + snapshot.version,
                    snapshot.author || '',
                    snapshot.context || ''
                ]
                    .filter(Boolean)
                    .join(' · ');
            else if (item.kind === 'snapshot-size') {
                const bytes = Number(snapshot.size) || 0,
                    unit =
                        bytes >= 1073741824
                            ? 'GB'
                            : bytes >= 1048576
                              ? 'MB'
                              : bytes >= 1024
                                ? 'KB'
                                : 'B',
                    divisor = {
                        GB: 1073741824,
                        MB: 1048576,
                        KB: 1024,
                        B: 1
                    }[unit];
                content =
                    (bytes / divisor).toFixed(unit === 'B' ? 0 : 1) +
                    ' ' +
                    unit;
            } else if (item.kind === 'snapshot-summary')
                content = [
                    snapshot.title || '',
                    snapshot.description || '',
                    snapshot.author || ''
                ]
                    .filter(Boolean)
                    .join(' · ');
            else if (item.kind === 'branch-summary')
                content = [
                    (sample.branch || {}).title || '',
                    String((sample.branch || {}).count || 0)
                ].join(' · ');
            else if (item.kind === 'file-offline') content = tr('File Offline');
            else if (item.kind === 'knowledge')
                content = (sample.knowledge || [])
                    .map((row) => row.title || row.name || row.code || '')
                    .join(' · ');
            children.push(
                label(
                    id + 'Text',
                    rect(
                        6,
                        4,
                        Math.max(0, box.width - 12),
                        Math.max(0, box.height - 8)
                    ),
                    content,
                    {
                        wrap: true,
                        color,
                        weight,
                        fontSize: item.kind === 'title' ? 15 : 13,
                        align:
                            item.align === 'center'
                                ? 'center'
                                : item.align === 'end'
                                  ? 'right'
                                  : 'left'
                    }
                )
            );
        }
        if (item.kind === 'group' || (item.kind === 'view' && inner))
            return node('Box', id, box, {
                background:
                    selected === item.name ? 'contentSelection' : 'transparent',
                children: [
                    node(
                        'Action',
                        id + 'Select',
                        rect(0, 0, box.width, box.height),
                        {
                            text: item.title || item.name,
                            normalColor: 'transparent',
                            selectedColor: 'transparent',
                            action: {
                                type: 'select',
                                name: item.name
                            }
                        }
                    )
                ].concat(children)
            });
        return node('Action', id, box, {
            text: item.title || item.name,
            selected: selected === item.name,
            normalColor: 'transparent',
            selectedColor: 'contentSelection',
            children,
            action: {
                type: 'select',
                name: item.name
            }
        });
    }
    function container(parent, w, nesting) {
        if (nesting >= 8)
            return {
                nodes: [],
                height: 40
            };
        const definition = elements.find((item) => item.name === parent),
            items = elements.filter((item) => item.parent === parent),
            flow = definition ? definition.flow : layout.flow,
            columns = number(
                definition ? definition.columns : layout.columns,
                12,
                1,
                12
            ),
            result = [],
            placements = [];
        if (flow === 'contents') {
            const preview = items.some((item) => item.role === 'preview'),
                copyX = preview ? Math.min(96, w * 0.28) : 8;
            let cursor = 8;
            for (const item of items) {
                let box,
                    child =
                        item.kind === 'group' && item.role !== 'copy'
                            ? container(
                                  item.name,
                                  Math.max(1, w - 16),
                                  nesting + 1
                              )
                            : item.kind === 'view' && item.widget_layout
                              ? describe(
                                    item.widget_layout,
                                    sample,
                                    Math.max(1, w - 16),
                                    selected,
                                    language,
                                    screenWidth,
                                    assetBase,
                                    namePrefix + '_' + item.name,
                                    nesting + 1
                                )
                              : null;
                if (item.role === 'preview')
                    box = rect(8, 8, Math.min(76, w * 0.24), 76);
                else if (item.role === 'copy') {
                    child = container(
                        item.name,
                        Math.max(1, w - copyX - 16),
                        nesting + 1
                    );
                    box = rect(
                        copyX,
                        8,
                        Math.max(1, w - copyX - 8),
                        child.height + 8
                    );
                    cursor = Math.max(cursor, box.height + 16);
                } else {
                    const h = child
                        ? child.height + 8
                        : item.role === 'title-line'
                          ? 36
                          : item.kind === 'image'
                            ? number(item.height, 76, 24, 1200)
                            : item.kind === 'description'
                              ? 44
                              : 38;
                    box = rect(8, cursor, w - 16, h);
                    cursor += h + 4;
                }
                placements.push({
                    item,
                    box,
                    child
                });
                cursor = Math.max(cursor, box.y + box.height + 8);
            }
            placements
                .sort((a, b) => (a.item.layer || 0) - (b.item.layer || 0))
                .forEach((row) =>
                    result.push(draw(row.item, row.box, row.child))
                );
            return {
                nodes: result,
                height: Math.max(92, cursor)
            };
        }
        const gap = 6,
            available = Math.max(1, w - gap * (columns - 1)),
            sizes = tracks(definition ? '' : layout.tracks, columns, available),
            rows = [];
        for (const item of items) {
            const start = number(item.row, 1, 1, 100) - 1,
                span = number(item.rows, 1, 1, 100),
                column = number(item.column, 1, 1, columns) - 1,
                columnsWide = number(item.span, 1, 1, columns - column),
                cellWidth =
                    sizes
                        .slice(column, column + columnsWide)
                        .reduce((a, b) => a + b, 0) +
                    gap * (columnsWide - 1),
                child =
                    item.kind === 'group'
                        ? container(
                              item.name,
                              Math.max(1, cellWidth - 8),
                              nesting + 1
                          )
                        : item.kind === 'view' && item.widget_layout
                          ? describe(
                                item.widget_layout,
                                sample,
                                Math.max(1, cellWidth - 8),
                                selected,
                                language,
                                screenWidth,
                                assetBase,
                                namePrefix + '_' + item.name,
                                nesting + 1
                            )
                          : null,
                h = child
                    ? child.height + 8
                    : item.kind === 'image'
                      ? number(item.height, 40, 1, 1200)
                      : 40;
            for (let index = start; index < start + span; index++)
                rows[index] = Math.max(
                    rows[index] || 40,
                    (h - gap * (span - 1)) / span
                );
            placements.push({
                item,
                start,
                span,
                column,
                columnsWide,
                cellWidth,
                child
            });
        }
        const sum = (values, start, end) => {
            let total = 0;
            for (let index = start; index < end; index++)
                total += values[index] || 40;
            return total;
        };
        placements
            .sort((a, b) => (a.item.layer || 0) - (b.item.layer || 0))
            .forEach((row) => {
                const x =
                        sizes.slice(0, row.column).reduce((a, b) => a + b, 0) +
                        gap * row.column,
                    y = sum(rows, 0, row.start) + gap * row.start,
                    h =
                        sum(rows, row.start, row.start + row.span) +
                        gap * (row.span - 1);
                result.push(
                    draw(row.item, rect(x, y, row.cellWidth, h), row.child)
                );
            });
        return {
            nodes: result,
            height: rows.length
                ? sum(rows, 0, rows.length) + gap * (rows.length - 1)
                : 64
        };
    }
    let body;
    if (layout.collection === 'table') {
        const items = elements.filter((item) => !item.parent),
            total =
                items.reduce(
                    (sum, item) => sum + number(item.span, 1, 1, 12),
                    0
                ) || 1;
        let x = 0;
        body = {
            nodes: [],
            height: 160
        };
        for (const item of items) {
            const w = (width * number(item.span, 1, 1, 12)) / total,
                child =
                    item.kind === 'group'
                        ? container(item.name, Math.max(1, w - 8), level + 1)
                        : item.kind === 'view' && item.widget_layout
                          ? describe(
                                item.widget_layout,
                                sample,
                                Math.max(1, w - 8),
                                selected,
                                language,
                                screenWidth,
                                assetBase,
                                namePrefix + '_' + item.name,
                                level + 1
                            )
                          : null;
            body.height = Math.max(
                body.height,
                (child ? child.height : 108) + 52
            );
            body.nodes.push(
                label(
                    namePrefix + 'Header_' + item.name,
                    rect(x, 0, w, 38),
                    item.title || item.name,
                    {
                        weight: 600
                    }
                ),
                draw(
                    item,
                    rect(x, 44, w, Math.max(108, child ? child.height : 0)),
                    child
                )
            );
            x += w;
        }
    } else body = container('', width, level);
    nodes.push.apply(nodes, body.nodes);
    return {
        nodes,
        height: body.height
    };
}
