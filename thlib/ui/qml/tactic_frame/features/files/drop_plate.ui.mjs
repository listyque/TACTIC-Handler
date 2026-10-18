import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

export function matches(record, filter, mode) {
    const text = filter.trim().toLowerCase();
    return (
        mode === 'extension'
            ? record.extension
            : record.title + ' ' + record.path
    )
        .toLowerCase()
        .includes(mode === 'extension' ? text.replace(/^\./, '') : text);
}

export function actions(model) {
    return [
        {
            title: model.native ? 'Open file' : 'Download file',
            icon: 'open',
            command: 'open'
        },
        ...(model.native
            ? [{ title: 'Show folder', icon: 'folder', command: 'folder' }]
            : []),
        { separator: true },
        { title: 'Copy file path', icon: 'copy', command: 'copy' },
        { title: 'Copy all file paths', icon: 'copy', command: 'copy_all' },
        { separator: true },
        {
            title: 'Remove from Drop Plate',
            icon: 'delete',
            command: 'remove',
            enabled: !model.busy
        }
    ];
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 20),
        wide = width >= 940,
        nodes = [
            node('Box', 'dropPlateBackground', rect(0, 0, width, height), {
                background: 'panelDeep',
                radius: 0
            })
        ],
        tools = [
            ['dropPlateFiles', 'Files', 'add', 'files', model.busy],
            [
                'dropPlateDirectory',
                'Directory',
                'folder',
                'directory',
                model.busy
            ]
        ];
    let x = 10;
    tools.forEach(([id, title, icon, type, disabled], index) => {
        const w = index ? 108 : 84;
        nodes.push(
            button(id, rect(x, 10, w, 36), tr(title), icon, { type }, !disabled)
        );
        x += w + 6;
    });
    [
        ['dropPlatePaste', 'Paste files', 'clipboard', 'paste'],
        ['dropPlateTemplates', 'Matching Templates', 'tune', 'templates'],
        ['dropPlateClear', 'Clear', 'delete-sweep', 'clear']
    ].forEach(([id, title, icon, type], index) => {
        nodes.push(
            button(
                id,
                rect(width - 106 + index * 34, 14, 28, 28),
                tr(title),
                icon,
                { type },
                type === 'templates' ||
                    (!model.busy && (type !== 'clear' || model.count > 0)),
                { iconOnly: true, iconAction: true }
            )
        );
    });
    const checkWidth = (wide ? width - x - 112 : inner - 12) / 3,
        checkHeight = Math.max(
            32,
            ...['Include subfolders', 'Group check-in', 'Keep filename'].map(
                (text) => captionHeight(tr(text), checkWidth - 40)
            )
        );
    [
        ['recursive', 'Include subfolders'],
        ['groupCheckin', 'Group check-in'],
        ['keepFileName', 'Keep filename']
    ].forEach(([field, title], index) => {
        nodes.push(
            node(
                'CheckBox',
                'dropPlate_' + field,
                rect(
                    (wide ? x : 10) + index * (checkWidth + 6),
                    wide ? 12 : 54,
                    checkWidth,
                    checkHeight
                ),
                {
                    text: tr(title),
                    checked: !!model[field],
                    action: { type: 'preference', field },
                    enabled: !model.busy
                }
            )
        );
    });
    const filterY = wide ? 54 : 62 + checkHeight;
    nodes.push(
        node(
            'Choice',
            'dropPlateFilterMode',
            rect(10, filterY, Math.min(130, inner * 0.36), 36),
            {
                label: tr('Filter mode'),
                value: model.filterMode,
                options: [
                    { value: 'name', label: tr('Filename') },
                    { value: 'extension', label: tr('Extension') }
                ],
                action: { type: 'filterMode' }
            }
        )
    );
    const filterX = 18 + Math.min(130, inner * 0.36);
    nodes.push(
        node(
            'Field',
            'dropPlateFilter',
            rect(filterX, filterY, width - filterX - 10, 36),
            {
                label: tr('Filter files'),
                placeholder: tr(
                    model.filterMode === 'extension'
                        ? 'Filter by extension'
                        : 'Filter files'
                ),
                text: model.filter || '',
                action: { type: 'filter' }
            }
        )
    );
    const footerHeight = model.hasTarget ? (width < 480 ? 146 : 104) : 58,
        footerY = Math.max(filterY + 54, height - footerHeight),
        errorHeight = model.error
            ? Math.max(24, captionHeight(model.error, inner)) + 6
            : 0,
        listY = filterY + 44,
        listHeight = Math.max(0, footerY - listY - 8 - errorHeight),
        listChildren = [
            node(
                'List',
                'dropPlateGroups',
                rect(7, 7, inner - 14, listHeight - 14),
                {
                    source: 'groups',
                    keyField: 'groupId',
                    rowHeight: 67,
                    rowGap: 5,
                    label: tr('Drop Plate'),
                    fields: [
                        'groupId',
                        'title',
                        'path',
                        'extension',
                        'fileCount',
                        'size',
                        'checked',
                        'status',
                        'matchingType',
                        'sequenceInfo',
                        'error'
                    ]
                }
            )
        ];
    if (model.busy || !model.count) {
        const center = Math.max(0, (listHeight - 74) / 2);
        listChildren.push(
            node(
                'Icon',
                'dropPlateEmptyIcon',
                rect((inner - 32) / 2, center, 32, 32),
                { icon: 'upload', color: 'disabledText' }
            )
        );
        listChildren.push(
            label(
                'dropPlateEmptyText',
                rect(12, center + 40, inner - 24, 34),
                tr(
                    model.busy
                        ? 'Matching files…'
                        : 'Drop files or directories here'
                ),
                {
                    color: 'secondaryText',
                    align: 'center',
                    wrap: true,
                    role: 'status'
                }
            )
        );
    }
    nodes.push(
        node('Box', 'dropPlateListPanel', rect(10, listY, inner, listHeight), {
            background: 'surfaceContainerLow',
            border: model.dragging ? 'action' : 'outlineVariant',
            radius: 16,
            children: listChildren
        })
    );
    if (model.error)
        nodes.push(
            label(
                'dropPlateError',
                rect(10, footerY - errorHeight, inner, errorHeight - 6),
                model.error,
                { color: 'error', wrap: true, role: 'alert' }
            )
        );
    const footer = [
        label(
            'dropPlateTarget',
            rect(
                10,
                model.hasTarget ? 0 : 10,
                model.hasTarget ? width - 20 : width - 188,
                model.hasTarget ? 24 : 38
            ),
            model.targetTitle ||
                tr('Select an object, process and context first'),
            muted
        )
    ];
    if (model.hasTarget) {
        const fieldWidth = width < 480 ? inner : width - 188,
            half = (fieldWidth - 8) / 2;
        footer.push(
            node('Choice', 'dropPlateProcess', rect(10, 32, half, 36), {
                label: tr('Process'),
                value: model.process,
                options: (model.processes || []).map((value) =>
                    typeof value === 'string' ? { value, label: value } : value
                ),
                action: { type: 'process' },
                enabled: !model.busy
            })
        );
        footer.push(
            node('Field', 'dropPlateContext', rect(18 + half, 32, half, 36), {
                label: tr('Context'),
                placeholder: tr('Context'),
                text: model.context || '',
                action: { type: 'context' },
                enabled: !model.busy
            })
        );
    }
    footer.push(
        button(
            'dropPlateQueue',
            rect(
                width < 480 && model.hasTarget ? 10 : width - 168,
                width < 480 && model.hasTarget ? 80 : model.hasTarget ? 31 : 10,
                width < 480 && model.hasTarget ? inner : 158,
                38
            ),
            tr('Add to queue'),
            'queue',
            { type: 'queue' },
            !model.busy &&
                model.hasTarget &&
                model.hasChecked &&
                model.canQueue !== false &&
                !!model.context?.trim(),
            { highlighted: true }
        )
    );
    nodes.push(
        node(
            'Box',
            'dropPlateFooter',
            rect(0, footerY, width, Math.max(0, height - footerY)),
            { children: footer }
        )
    );
    return { nodes };
}

export function row(model, record, width, language) {
    const tr = (text, values) => translate(text, language, values),
        key = record.groupId,
        menu = { type: 'menu', key },
        textWidth = Math.max(0, width - 196),
        subtitle =
            (record.sequenceInfo || record.matchingType) +
            ' · ' +
            tr('{count} file(s)', { count: record.fileCount }) +
            (record.size ? ' · ' + record.size : '');
    return {
        nodes: [
            node('Box', 'dropPlateGroup_' + key, rect(0, 0, width, 62), {
                background: 'surfaceContainerHigh',
                radius: 12,
                contextAction: menu,
                children: [
                    node(
                        'CheckBox',
                        'dropPlateCheck_' + key,
                        rect(8, 13, 36, 36),
                        {
                            label: tr('Select file group'),
                            indicatorX: 6,
                            checked: record.checked,
                            enabled: !model.busy && record.status !== 'Queued',
                            action: { type: 'check', key }
                        }
                    ),
                    node('Icon', 'dropPlateIcon_' + key, rect(48, 22, 18, 18), {
                        icon: record.matchingType.includes('sequence')
                            ? 'movie'
                            : 'file',
                        color: record.error ? 'error' : 'action'
                    }),
                    label(
                        'dropPlateTitle_' + key,
                        rect(74, 5, textWidth, 20),
                        record.title,
                        { weight: 600, elideMiddle: true }
                    ),
                    label(
                        'dropPlateInfo_' + key,
                        rect(74, 27, textWidth, 15),
                        subtitle,
                        { fontRole: 'secondary', color: 'secondaryText' }
                    ),
                    label(
                        'dropPlatePath_' + key,
                        rect(74, 44, textWidth, 14),
                        record.error || record.path,
                        {
                            fontRole: 'caption',
                            color: record.error ? 'error' : 'disabledText',
                            elideMiddle: true,
                            toolTip: record.error || record.path
                        }
                    ),
                    label(
                        'dropPlateStatus_' + key,
                        rect(width - 116, 0, 48, 62),
                        tr(record.status),
                        {
                            fontRole: 'secondary',
                            color:
                                record.status === 'Queued'
                                    ? 'green'
                                    : 'secondaryText'
                        }
                    ),
                    button(
                        'dropPlateMenu_' + key,
                        rect(width - 64, 17, 28, 28),
                        tr('File actions'),
                        'more',
                        menu,
                        true,
                        { iconOnly: true, iconAction: true }
                    ),
                    button(
                        'dropPlateRemove_' + key,
                        rect(width - 32, 17, 28, 28),
                        tr('Remove from Drop Plate'),
                        'close',
                        { type: 'remove', key },
                        !model.busy,
                        { iconOnly: true, iconAction: true }
                    )
                ]
            })
        ]
    };
}
