import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export const fields = [
    'version',
    'date',
    'changes',
    'misc',
    'archive',
    'selected',
    'kind'
];
export const versionKeys = ['major', 'minor', 'build', 'revision'];

export function versionValues(draft) {
    const values = versionKeys.map((key) => String(draft[key] ?? ''));
    return values.every((value) => /^\d{1,3}$/.test(value))
        ? values.map(Number)
        : null;
}

export function stepVersion(draft, key, delta) {
    if (!versionKeys.includes(key)) return draft;
    const next = Object.assign({}, draft);
    next[key] = String(
        Math.max(0, Math.min(999, (Number(draft[key]) || 0) + delta))
    );
    return next;
}

export function row(record, width) {
    return {
        nodes: [
            node(
                'Action',
                'release_' +
                    encodeURIComponent(record.archive || record.version),
                rect(0, 0, width, 72),
                {
                    text: record.version,
                    selected: record.selected,
                    normalColor: 'surfaceContainerLow',
                    selectedColor: 'contentSelection',
                    border: record.selected ? 'action' : 'outlineVariant',
                    radius: 13,
                    action: {
                        type: 'select',
                        archive: record.archive,
                        version: record.version
                    },
                    children: [
                        node('Box', 'releaseOutline', rect(0, 0, width, 72), {
                            background: 'transparent',
                            border: record.selected
                                ? 'action'
                                : 'outlineVariant',
                            radius: 10
                        }),
                        label(
                            'releaseVersion',
                            rect(10, 7, width - 140, 28),
                            record.version,
                            { fontRole: 'section', weight: 600 }
                        ),
                        label(
                            'releaseDate',
                            rect(width - 126, 7, 116, 28),
                            record.date,
                            Object.assign({}, muted, { align: 'right' })
                        ),
                        label(
                            'releaseNotes',
                            rect(10, 39, width - 20, 25),
                            record.changes || record.misc || '',
                            muted
                        )
                    ]
                }
            )
        ]
    };
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        margin = 14,
        inner = width - margin * 2,
        compact = width < 600;
    const nodes = [
        node('Icon', 'updatesIcon', rect(margin, 16, 32, 32), {
            icon: model.createMode ? 'inventory_2' : 'system-update',
            color: 'action'
        }),
        label(
            'updatesHeading',
            rect(margin + 46, 10, inner - 90, 26),
            text(model.createMode ? 'Create update' : 'Application updates'),
            { fontRole: 'section', weight: 600 }
        ),
        node(
            'View',
            'currentVersionLabel',
            rect(margin + 46, 39, inner - 90, 22),
            { view: 'version', fontRole: 'secondary', color: 'secondaryText' }
        ),
        button(
            'updatesRefresh',
            rect(width - margin - 36, 18, 36, 36),
            text('Check TACTIC update snapshots'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            {
                iconOnly: true,
                visible: model.createMode || model.page === 'updates'
            }
        )
    ];
    let y = 76;
    if (!model.createMode) {
        ['updates', 'changelog'].forEach((page, index) =>
            nodes.push(
                button(
                    'updatePage_' + page,
                    rect(
                        margin + (index * (inner + 6)) / 2,
                        y,
                        (inner - 6) / 2,
                        36
                    ),
                    text(
                        page === 'updates' ? 'Available updates' : 'Changelog'
                    ),
                    page === 'updates' ? 'system-update' : 'history',
                    { type: 'page', value: page },
                    true,
                    { radio: true, selected: model.page === page }
                )
            )
        );
        y += 48;
    } else {
        const columns = compact ? 2 : 4,
            cell = (inner - (columns - 1) * 8) / columns;
        versionKeys.forEach((key, index) => {
            const x = margin + (index % columns) * (cell + 8),
                top = y + Math.floor(index / columns) * 74;
            nodes.push(
                label(
                    'updateLabel_' + key,
                    rect(x, top, cell, 22),
                    text(key[0].toUpperCase() + key.slice(1)),
                    muted
                )
            );
            nodes.push(
                node(
                    'Field',
                    'update_' + key,
                    rect(x + 28, top + 26, cell - 56, 36),
                    {
                        text: String(model.draft?.[key] ?? '0'),
                        label: text(key[0].toUpperCase() + key.slice(1)),
                        inputMode: 'numeric',
                        enabled: !model.busy,
                        action: { type: 'field', key }
                    }
                )
            );
            nodes.push(
                button(
                    'updateMinus_' + key,
                    rect(x, top + 26, 26, 36),
                    text('Decrease value'),
                    'minus',
                    { type: 'versionStep', key, delta: -1 },
                    !model.busy,
                    { iconOnly: true }
                )
            );
            nodes.push(
                button(
                    'updatePlus_' + key,
                    rect(x + cell - 26, top + 26, 26, 36),
                    text('Increase value'),
                    'add',
                    { type: 'versionStep', key, delta: 1 },
                    !model.busy,
                    { iconOnly: true }
                )
            );
        });
        y += Math.ceil(4 / columns) * 74;
        nodes.push(
            node('Area', 'updateChanges', rect(margin, y, inner, 76), {
                text: model.draft?.changes || '',
                label: text('Changes'),
                placeholder: text('Changes'),
                enabled: !model.busy,
                action: { type: 'field', key: 'changes' }
            })
        );
        y += 86;
        nodes.push(
            node('Area', 'updateMisc', rect(margin, y, inner, 62), {
                text: model.draft?.misc || '',
                label: text('Additional information'),
                placeholder: text('Additional information'),
                enabled: !model.busy,
                action: { type: 'field', key: 'misc' }
            })
        );
        y += 72;
    }
    const footerHeight = model.busy || model.error || model.stage ? 132 : 84;
    const contentHeight = Math.max(height, y + footerHeight + 130),
        footerY = contentHeight - footerHeight;
    if (!model.createMode && model.page === 'changelog')
        nodes.push(
            node(
                'View',
                'updateChangelog',
                rect(margin, y, inner, contentHeight - y - margin),
                { view: 'changelog' }
            )
        );
    else {
        nodes.push(
            node(
                'List',
                'updateVersions',
                rect(margin, y, inner, Math.max(80, footerY - y - 10)),
                {
                    source: 'releases',
                    keyField: 'archive',
                    fields,
                    rowHeight: 77,
                    rowGap: 5,
                    scrollbarId: 'updateVersionsScrollBar'
                }
            )
        );
        if (!model.count && !model.busy)
            nodes.push(
                label(
                    'updatesEmpty',
                    rect(margin + 12, y + 12, inner - 40, 80),
                    text(
                        model.configured
                            ? 'No release ZIP snapshots found'
                            : 'Configure an update sObject in Server configuration'
                    ),
                    Object.assign({}, muted, { wrap: true })
                )
            );
        if (model.busy || model.error || model.stage)
            nodes.push(
                label(
                    'updateStatus',
                    rect(margin, footerY, inner, 48),
                    text(model.error || model.stage) +
                        (model.busy
                            ? ' · ' +
                              Math.round((model.progress || 0) * 100) +
                              '%'
                            : ''),
                    {
                        color: model.error ? 'red' : 'secondaryText',
                        wrap: true,
                        role: model.error ? 'alert' : 'status'
                    }
                )
            );
        if (!model.createMode && !model.portable)
            nodes.push(
                label(
                    'updatePortableNotice',
                    rect(margin, contentHeight - 78, inner, 30),
                    text('Automatic installation requires a portable build'),
                    Object.assign({}, muted, { wrap: true })
                )
            );
        if (model.cancelable)
            nodes.push(
                button(
                    'updateCancel',
                    rect(margin, contentHeight - 44, 92, 36),
                    text('Cancel'),
                    'stop',
                    { type: 'cancel' },
                    true
                )
            );
        nodes.push(
            button(
                model.createMode
                    ? 'createUpdateArchiveButton'
                    : 'installSelectedVersion',
                rect(
                    width - margin - Math.min(inner, 240),
                    contentHeight - 44,
                    Math.min(inner, 240),
                    36
                ),
                text(
                    model.createMode
                        ? 'Create archive'
                        : 'Install selected version'
                ),
                model.createMode ? 'archive' : 'restart_alt',
                { type: model.createMode ? 'create' : 'install' },
                model.createMode
                    ? !model.busy && !!versionValues(model.draft || {})
                    : !!model.canInstall,
                { highlighted: true }
            )
        );
    }
    return {
        nodes: [
            node('Scroll', 'updatesBody', rect(0, 0, width, height), {
                contentHeight,
                children: nodes
            })
        ]
    };
}
