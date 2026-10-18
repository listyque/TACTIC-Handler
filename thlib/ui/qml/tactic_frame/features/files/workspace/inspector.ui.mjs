import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function date(value) {
    if (!value) return '—';
    const current = new Date(value / 1000);
    if (!Number.isFinite(current.getTime())) return '—';
    const pad = (value) => String(value).padStart(2, '0');
    return (
        pad(current.getDate()) +
        '.' +
        pad(current.getMonth() + 1) +
        '.' +
        current.getFullYear() +
        ' ' +
        pad(current.getHours()) +
        ':' +
        pad(current.getMinutes()) +
        ':' +
        pad(current.getSeconds())
    );
}

export function size(value) {
    return value < 1024
        ? value + ' B'
        : value < 1048576
          ? (value / 1024).toFixed(1) + ' KiB'
          : (value / 1048576).toFixed(1) + ' MiB';
}

export function fileType(file) {
    const path = file.path || '';
    return (
        file.file_type ||
        (path.lastIndexOf('.') > path.lastIndexOf('/')
            ? path.slice(path.lastIndexOf('.') + 1).toUpperCase()
            : '—')
    );
}

export function details(info, history = false) {
    const file = info.file || {},
        change = info.change_number ? '#' + info.change_number : '—';
    const bytes = size(file.size ?? info.local_size ?? 0);
    if (history)
        return [
            ['Date submitted', date(info.submitted_at)],
            ['Changelist', change],
            ['Submitted by', info.author || '—'],
            ['Type', fileType(Object.assign({}, file, { path: info.path }))],
            ['Workspace', info.workspace || '—'],
            ['File size', bytes],
            ['Action', info.action || '—']
        ];
    return [
        [
            'Workspace location',
            info.workspace_location || info.local_path || '—'
        ],
        ['Depot location', '//' + info.stream + '/' + info.path],
        [
            'Revision',
            '#' +
                (file.number || '—') +
                ' · Have #' +
                (info.have?.number || '—') +
                ' · Head #' +
                (info.head?.number || '—')
        ],
        [
            'Local modification date',
            info.local_modified_ns ? date(info.local_modified_ns / 1000) : '—'
        ],
        ['Submitted at', date(info.submitted_at)],
        ['File size', bytes],
        ['Author', info.author || '—'],
        ['Changelist', change],
        ['Type', fileType(Object.assign({}, file, { path: info.path }))],
        ['SHA-256', file.sha256 || '—'],
        [
            'Integration source',
            info.provenance
                ? info.provenance.stream +
                  ' · ' +
                  info.provenance.change +
                  ' · ' +
                  info.provenance.version
                : '—'
        ]
    ];
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        info = model.info || {},
        preview = model.preview || {};
    const margin = 8,
        inner = Math.max(0, width - margin * 2),
        bodyWidth = Math.max(0, inner - 16);
    const tabs = [
        { id: 'details', title: 'Details' },
        model.history
            ? { id: 'integrations', title: 'Integrations' }
            : { id: 'checkout', title: 'Checked Out By' },
        { id: 'preview', title: 'Preview' }
    ];
    const tabWidth = inner / 3;
    const nodes = [
        node('Box', 'workspaceInspectorBackground', rect(0, 0, width, height), {
            background: 'panelDeep'
        })
    ];
    for (const [index, tab] of tabs.entries())
        nodes.push(
            button(
                (model.history ? 'historyTab_' : 'fileInspectorTab_') + tab.id,
                rect(margin + index * tabWidth, margin, tabWidth, 32),
                tr(tab.title),
                '',
                { type: 'tab', value: tab.id },
                true,
                {
                    tab: true,
                    selected: model.tab === tab.id,
                    color: model.tab === tab.id ? 'action' : 'primaryText',
                    weight: model.tab === tab.id ? 600 : 400
                }
            )
        );
    const body = [];
    let y = 0;
    function message(id, text, color = 'secondaryText') {
        const h = Math.max(28, captionHeight(text, bodyWidth) * 1.2);
        body.push(
            label(id, rect(0, y, bodyWidth, h), text, {
                wrap: true,
                wrapAnywhere: true,
                color
            })
        );
        y += h + 6;
    }
    if (model.error || !info.path)
        message(
            'workspaceInspectorNotice',
            model.error ||
                tr(
                    model.busy
                        ? 'Loading'
                        : model.history
                          ? 'Select a revision'
                          : 'Select a file to inspect'
                ),
            model.error ? 'error' : 'secondaryText'
        );
    else if (model.tab === 'details') {
        if (model.history)
            message(
                'workspaceInspectorRevisionPath',
                '//' +
                    info.stream +
                    '/' +
                    info.path +
                    '#' +
                    (info.file?.number || ''),
                'primaryText'
            );
        const columns = width < 650 ? 1 : 2,
            columnWidth = (bodyWidth - (columns - 1) * 20) / columns;
        for (const [index, [title, value]] of details(
            info,
            !!model.history
        ).entries()) {
            const x = (index % columns) * (columnWidth + 20),
                top = y + Math.floor(index / columns) * 32;
            const caption = Math.min(145, width * 0.3);
            body.push(
                label(
                    'workspaceInspectorFieldLabel' + index,
                    rect(x, top, caption - 6, 30),
                    tr(title),
                    {
                        color: 'secondaryText',
                        fontRole: 'secondary',
                        toolTip: tr(title)
                    }
                )
            );
            body.push(
                node(
                    'Field',
                    'workspaceInspectorField' + index,
                    rect(
                        x + caption,
                        top,
                        Math.max(0, columnWidth - caption),
                        30
                    ),
                    {
                        text: String(value),
                        label: tr(title),
                        readOnly: true,
                        tableCell: true,
                        toolTip: String(value)
                    }
                )
            );
        }
        y +=
            Math.ceil(details(info, !!model.history).length / columns) * 32 + 6;
        body.push(
            label(
                'workspaceInspectorDescriptionLabel',
                rect(0, y, bodyWidth, 24),
                tr('Description'),
                { color: 'secondaryText' }
            )
        );
        y += 28;
        body.push(
            node(
                'Area',
                model.history
                    ? 'historyRevisionDescription'
                    : 'fileInspectorDescription',
                rect(0, y, bodyWidth, 85),
                {
                    text: info.description || '',
                    readOnly: true,
                    label: tr('Description')
                }
            )
        );
        y += 93;
    } else if (model.tab === 'integrations') {
        if (!info.provenance)
            message(
                'workspaceInspectorNoIntegration',
                tr('No integration source for this revision')
            );
        else
            for (const [title, value] of [
                ['Stream', info.provenance.stream],
                ['Changelist', info.provenance.change],
                ['Revision', info.provenance.version]
            ])
                message(
                    'workspaceInspectorIntegration' + title,
                    tr(title) + ': ' + value,
                    'primaryText'
                );
    } else if (model.tab === 'checkout') {
        if (!(info.holders || []).length)
            message('workspaceInspectorNoCheckout', tr('No active checkout'));
        for (const [index, holder] of (info.holders || []).entries()) {
            const text =
                holder.owner +
                ' · ' +
                holder.workspace +
                ' · #' +
                (holder.number || holder.change) +
                ' · ' +
                tr(
                    holder.mode === 'exclusive'
                        ? 'Exclusive checkout'
                        : 'Ordinary checkout'
                );
            const h = Math.max(28, captionHeight(text, bodyWidth - 24) * 1.2);
            body.push(
                node(
                    'Icon',
                    'workspaceInspectorCheckoutIcon' + index,
                    rect(0, y, 18, 18),
                    {
                        icon:
                            holder.mode === 'exclusive'
                                ? 'lock'
                                : 'lock-open-variant',
                        color: 'action'
                    }
                )
            );
            body.push(
                label(
                    'workspaceInspectorCheckout' + index,
                    rect(24, y, Math.max(0, bodyWidth - 24), h),
                    text,
                    { wrap: true }
                )
            );
            y += h + 6;
        }
    } else if (model.tab === 'preview') {
        if (!preview.kind || preview.error)
            message(
                'workspaceInspectorNoPreview',
                preview.error ||
                    tr(
                        model.busy
                            ? 'Loading preview…'
                            : 'No content available for this file'
                    ),
                preview.error ? 'error' : 'secondaryText'
            );
        if (preview.kind === 'binary' || preview.truncated)
            message(
                'workspaceInspectorPreviewNotice',
                (preview.kind === 'binary' ? tr('Binary file') : '') +
                    (preview.truncated
                        ? ' · ' + tr('Preview shows the first 256 KiB')
                        : '')
            );
        const previewHeight = Math.max(120, height - 100 - y);
        if (!preview.kind || ['text', 'binary'].includes(preview.kind))
            body.push(
                node(
                    'Area',
                    model.history
                        ? 'historyRevisionPreview'
                        : 'fileInspectorPreview',
                    rect(0, y, bodyWidth, previewHeight),
                    {
                        text: preview.text || '',
                        readOnly: true,
                        label: tr('File preview')
                    }
                )
            );
        else if (preview.kind === 'image')
            body.push(
                node(
                    'Preview',
                    'workspaceInspectorImage',
                    rect(0, y, bodyWidth, previewHeight),
                    {
                        source: preview.image || '',
                        round: false,
                        outlined: false,
                        fit: 'contain',
                        icon: 'file-image'
                    }
                )
            );
        y += previewHeight + 8;
    }
    nodes.push(
        node(
            'Scroll',
            'workspaceInspectorBody',
            rect(margin, 48, inner, Math.max(0, height - 56)),
            {
                scrollbarId: 'workspaceInspectorScrollBar',
                contentHeight: y,
                children: body
            }
        )
    );
    return { nodes };
}
