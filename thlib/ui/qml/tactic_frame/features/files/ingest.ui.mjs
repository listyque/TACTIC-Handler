import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

export function optionValue(field, value) {
    return field === 'updateMode' ? (value ? 'update' : 'insert') : value;
}

export function status(status) {
    if (status === 'Completed') return { icon: 'check-circle', color: 'green' };
    if (status === 'Failed') return { icon: 'error', color: 'error' };
    if (status === 'Conflict') return { icon: 'warning', color: 'yellow' };
    if (['Skipped', 'Cancelled'].includes(status))
        return { icon: 'cancel', color: 'yellow' };
    if (['Queued', 'Running', 'Checking'].includes(status))
        return { icon: 'sync', color: 'action' };
    return { icon: 'file', color: 'secondaryText' };
}

export function fileHeight(record) {
    return record.error ? 62 : 46;
}

export function fileRow(model, record, index, width, language) {
    const tr = (text) => translate(text, language),
        height = fileHeight(record),
        state = status(record.status),
        key = String(index),
        textWidth = Math.max(0, width - 138);
    return {
        nodes: [
            node('Box', 'ingestFile_' + key, rect(0, 0, width, height), {
                background: 'row',
                border: 'outlineVariant',
                radius: 12,
                children: [
                    node(
                        'Icon',
                        'ingestFileStatus_' + key,
                        rect(10, (height - 17) / 2, 17, 17),
                        state
                    ),
                    label(
                        'ingestFileTitle_' + key,
                        rect(
                            35,
                            record.error ? 8 : 0,
                            textWidth,
                            record.error ? 22 : height
                        ),
                        record.title,
                        {
                            elideMiddle: true,
                            toolTip:
                                record.title +
                                '\n' +
                                tr(record.status) +
                                (record.size == null
                                    ? ''
                                    : ' · ' + record.size + ' ' + tr('bytes'))
                        }
                    ),
                    ...(record.error
                        ? [
                              label(
                                  'ingestFileError_' + key,
                                  rect(35, 32, textWidth, 20),
                                  tr(record.error),
                                  { fontRole: 'caption', color: 'error' }
                              )
                          ]
                        : []),
                    label(
                        'ingestFileExtension_' + key,
                        rect(width - 96, 0, 48, height),
                        (record.extension || 'FILE').toUpperCase(),
                        {
                            fontRole: 'caption',
                            color: 'secondaryText',
                            align: 'right'
                        }
                    ),
                    button(
                        'ingestFileRemove_' + key,
                        rect(width - 40, (height - 28) / 2, 28, 28),
                        tr('Remove file'),
                        'close',
                        { type: 'remove', index },
                        !model.busy,
                        { iconOnly: true, iconAction: true }
                    )
                ]
            })
        ]
    };
}

export function ruleRow(model, record, width, language) {
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            node(
                'Action',
                'ingestRule_' + record.ruleId,
                rect(0, 0, width, 50),
                {
                    text: record.title,
                    selected: record.selected,
                    enabled: record.applicable && !model.busy,
                    opacity: record.applicable ? 1 : 0.5,
                    normalColor: 'row',
                    selectedColor: 'selected',
                    radius: 12,
                    action: { type: 'rule', key: record.ruleId },
                    children: [
                        node(
                            'Icon',
                            'ingestRuleIcon_' + record.ruleId,
                            rect(10, 16, 17, 17),
                            {
                                icon: record.builtIn
                                    ? 'upload'
                                    : 'script-python',
                                color: record.selected
                                    ? 'action'
                                    : 'secondaryText'
                            }
                        ),
                        label(
                            'ingestRuleTitle_' + record.ruleId,
                            rect(35, 5, width - 45, 22),
                            record.builtIn ? tr('Quick ingest') : record.title,
                            { weight: 600 }
                        ),
                        label(
                            'ingestRuleSubtitle_' + record.ruleId,
                            rect(35, 27, width - 45, 18),
                            !record.applicable
                                ? tr('For another Search Type')
                                : record.builtIn
                                  ? tr(
                                        'Create one child item per file and publish immediately'
                                    )
                                  : record.subtitle,
                            { fontRole: 'caption', color: 'secondaryText' }
                        )
                    ]
                }
            )
        ]
    };
}

export function ruleEditor(model, width, language) {
    const tr = (text) => translate(text, language),
        options = model.options || {},
        nodes = [],
        enabled = !model.busy,
        stacked = width < 430;
    let y = 0;
    function heading(id, title) {
        nodes.push(
            label(
                id,
                rect(0, y, width, 24),
                tr(title),
                Object.assign({}, muted, { weight: 600 })
            )
        );
        y += 32;
    }
    function field(name, title, x, fieldWidth, top = y, active = enabled) {
        nodes.push(
            node(
                'Field',
                'ingestOption_' + name,
                rect(x, top, fieldWidth, 36),
                {
                    label: tr(title),
                    placeholder: tr(title),
                    text: options[name] || '',
                    enabled: active,
                    action: { type: 'option', field: name }
                }
            )
        );
    }
    function pair(left, right) {
        const w = stacked ? width : (width - 8) / 2;
        field(left[0], left[1], 0, w);
        field(
            right[0],
            right[1],
            stacked ? 0 : w + 8,
            w,
            y + (stacked ? 44 : 0)
        );
        y += stacked ? 88 : 44;
    }
    function check(name, title, checked) {
        const h = Math.max(32, captionHeight(tr(title), width - 40));
        nodes.push(
            node('CheckBox', 'ingestOption_' + name, rect(0, y, width, h), {
                text: tr(title),
                checked: checked === undefined ? !!options[name] : checked,
                enabled,
                action: { type: 'option', field: name }
            })
        );
        y += h + 8;
    }
    function choice(name, title, values) {
        nodes.push(
            label(
                'ingestLabel_' + name,
                rect(0, y, width, 20),
                tr(title),
                muted
            )
        );
        y += 26;
        nodes.push(
            node('Choice', 'ingestOption_' + name, rect(0, y, width, 36), {
                label: tr(title),
                value: options[name],
                options: values.map(([value, title]) => ({
                    value,
                    label: tr(title)
                })),
                enabled,
                action: { type: 'option', field: name }
            })
        );
        y += 46;
    }
    heading('ingestSelectionHeading', 'File selection');
    pair(['filter', 'Include: .mov, /regex/'], ['ignore', 'Ignore: .tmp, .db']);
    check('usePattern', 'Parse values from a path pattern');
    field(
        'pattern',
        '{sobject.name}_{snapshot.context}.mov',
        0,
        width,
        y,
        enabled && !!options.usePattern
    );
    y += 46;
    heading('ingestPublishHeading', 'Publish target');
    pair(['process', 'Process'], ['context', 'Context']);
    check(
        'updateMode',
        'Update matching item',
        options.updateMode === 'update'
    );
    check('createIcon', 'Create preview when supported');
    nodes.push(
        label(
            'ingestExtraLabel',
            rect(0, y, width, 20),
            tr('Extra Search Object values (JSON)'),
            muted
        )
    );
    y += 26;
    nodes.push(
        node('Area', 'ingestOption_extraDataJson', rect(0, y, width, 82), {
            label: tr('Extra Search Object values (JSON)'),
            text: options.extraDataJson || '{}',
            enabled,
            action: { type: 'option', field: 'extraDataJson' }
        })
    );
    y += 92;
    field('keywords', 'Keywords', 0, width);
    y += 46;
    choice('keywordMode', 'Keyword mode', [
        ['default', 'Default'],
        ['simplified', 'Simplified'],
        ['none', 'None']
    ]);
    choice('contextMode', 'Context case', [
        ['case_sensitive', 'Case sensitive'],
        ['case_insensitive', 'Lowercase']
    ]);
    heading('ingestScriptsHeading', 'TACTIC server scripts');
    const help = tr(
            'Scripts receive path, sobject, parent and snapshot. Return a truthy value to accept the file.'
        ),
        helpHeight = captionHeight(help, width);
    nodes.push(
        label(
            'ingestScriptsHelp',
            rect(0, y, width, helpHeight),
            help,
            Object.assign({}, muted, { wrap: true })
        )
    );
    y += helpHeight + 10;
    for (const [name, title] of [
        ['validationScript', 'Validation script path'],
        ['processScript', 'Process script path']
    ]) {
        field(name, title, 0, Math.max(0, width - 44));
        nodes.push(
            button(
                'ingestOpen_' + name,
                rect(width - 36, y, 36, 36),
                tr('Open Script Editor'),
                'script-python',
                { type: 'script', field: name },
                enabled && model.canOpenScript !== false,
                { iconOnly: true, iconAction: true }
            )
        );
        y += 46;
    }
    field('title', 'Rule title', 0, width);
    y += 46;
    nodes.push(
        button(
            'ingestSaveRule',
            rect(0, y, (width - 8) / 2, 38),
            tr('Save rule'),
            'save',
            { type: 'saveRule' },
            enabled
        )
    );
    nodes.push(
        button(
            'ingestDeleteRule',
            rect((width + 8) / 2, y, (width - 8) / 2, 38),
            tr('Delete rule'),
            'delete',
            { type: 'deleteRule' },
            enabled && !!model.canDeleteRule,
            { destructive: true }
        )
    );
    return { nodes, height: y + 46 };
}

export function describe(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values),
        narrow = width < 720,
        footerHeight = 58,
        headerHeight = width < 480 ? 76 : 62,
        inner = Math.max(0, width - 20),
        bodyHeight = Math.max(0, height - headerHeight - footerHeight - 20),
        filesWidth = narrow ? inner : Math.min(380, Math.max(280, inner * 0.4)),
        filesHeight = narrow ? Math.min(220, bodyHeight * 0.42) : bodyHeight,
        rulesWidth = narrow ? inner : inner - filesWidth - 10,
        rulesHeight = narrow
            ? Math.max(0, bodyHeight - filesHeight - 10)
            : bodyHeight,
        nodes = [
            node('Box', 'ingestBackground', rect(0, 0, width, height), {
                background: 'workspace',
                radius: 0
            })
        ];
    nodes.push(
        node('Box', 'ingestContext', rect(0, 0, width, headerHeight), {
            background: 'surfaceContainer',
            children: [
                node('Icon', 'ingestContextIcon', rect(14, 17, 22, 22), {
                    icon: 'upload',
                    color: 'action'
                }),
                label(
                    'ingestTarget',
                    rect(46, 9, width - 60, 25),
                    (model.parentTitle || tr('Parent')) +
                        ' → ' +
                        (model.targetTitle || tr('Child items')),
                    { fontRole: 'bodyLarge', weight: 600 }
                ),
                label(
                    'ingestSubtitle',
                    rect(46, 35, width - 60, headerHeight - 40),
                    tr('One Search Object per file · snapshot in publish') +
                        ' · ' +
                        (model.searchType || ''),
                    {
                        fontRole: 'caption',
                        color: 'secondaryText',
                        wrap: narrow
                    }
                )
            ]
        })
    );
    const fileChildren = [
        label(
            'ingestFilesHeading',
            rect(10, 8, filesWidth - 90, 28),
            tr('Files') + ' · ' + model.count,
            { weight: 600 }
        ),
        button(
            'ingestClearFiles',
            rect(filesWidth - 76, 8, 28, 28),
            tr('Clear'),
            'delete-sweep',
            { type: 'clear' },
            !model.busy && model.count > 0,
            { iconOnly: true, iconAction: true }
        ),
        button(
            'ingestAddFiles',
            rect(filesWidth - 38, 8, 28, 28),
            tr('Add files'),
            'add',
            { type: 'add' },
            !model.busy,
            { iconOnly: true, iconAction: true }
        ),
        node('Box', 'ingestFilesDivider', rect(0, 44, filesWidth, 1), {
            background: 'outlineVariant'
        })
    ];
    if (model.count)
        fileChildren.push(
            node(
                'View',
                'ingestFileList',
                rect(0, 45, filesWidth, Math.max(0, filesHeight - 45)),
                { view: 'files' }
            )
        );
    else {
        const top = Math.max(48, (filesHeight - 72) / 2);
        fileChildren.push(
            label(
                'ingestEmptyTitle',
                rect(12, top, filesWidth - 24, 26),
                tr('Drop files here'),
                { weight: 600, align: 'center' }
            )
        );
        fileChildren.push(
            label(
                'ingestEmptyHelp',
                rect(12, top + 30, filesWidth - 24, 42),
                tr(
                    'Each file creates a child item named without its extension.'
                ),
                Object.assign({}, muted, { wrap: true, align: 'center' })
            )
        );
    }
    nodes.push(
        node(
            'Box',
            'ingestFilesPanel',
            rect(10, headerHeight + 10, filesWidth, filesHeight),
            {
                background: 'panelDeep',
                border: 'outlineVariant',
                radius: 16,
                clip: true,
                children: fileChildren
            }
        )
    );
    const rw = Math.max(0, rulesWidth - 32),
        listHeight = Math.min(174, Math.max(52, model.ruleCount * 54)),
        children = [
            label('ingestRuleHeading', rect(0, 0, rw, 24), tr('Ingest rule'), {
                weight: 600
            }),
            node('List', 'ingestRules', rect(0, 32, rw, listHeight), {
                source: 'rules',
                keyField: 'ruleId',
                rowHeight: 54,
                rowGap: 4,
                label: tr('Ingest rule'),
                fields: [
                    'ruleId',
                    'title',
                    'subtitle',
                    'selected',
                    'builtIn',
                    'applicable'
                ]
            })
        ];
    let y = 42 + listHeight;
    const checkboxHeight = Math.max(
        32,
        captionHeight(tr('Remove extension from item name'), rw - 40)
    );
    children.push(
        node(
            'CheckBox',
            'ingestOption_ignoreExtension',
            rect(0, y, rw, checkboxHeight),
            {
                text: tr('Remove extension from item name'),
                checked: !!model.options?.ignoreExtension,
                enabled: !model.busy,
                action: { type: 'option', field: 'ignoreExtension' }
            }
        )
    );
    y += checkboxHeight + 8;
    children.push(
        button(
            'ingestAdvanced',
            rect(0, y, rw, 36),
            tr(model.advanced ? 'Hide rule details' : 'Edit rule details'),
            model.advanced ? 'expand-less' : 'settings',
            { type: 'advanced' },
            !model.busy
        )
    );
    y += 46;
    if (model.advanced) {
        const form = ruleEditor(model, rw, language);
        children.push(
            node('Box', 'ingestRuleEditor', rect(0, y, rw, form.height), {
                children: form.nodes
            })
        );
        y += form.height;
    }
    if (model.rulesBusy)
        children.push(
            label(
                'ingestRulesLoading',
                rect(0, y, rw, 28),
                tr('Loading ingest rules…'),
                Object.assign({}, muted, { role: 'status' })
            )
        );
    nodes.push(
        node(
            'Box',
            'ingestRulePanel',
            rect(
                narrow ? 10 : filesWidth + 20,
                headerHeight + 10 + (narrow ? filesHeight + 10 : 0),
                rulesWidth,
                rulesHeight
            ),
            {
                background: 'panelDeep',
                border: 'outlineVariant',
                radius: 16,
                children: [
                    node(
                        'Scroll',
                        'ingestOptionsViewport',
                        rect(8, 8, rulesWidth - 16, rulesHeight - 16),
                        {
                            contentHeight: y + (model.rulesBusy ? 38 : 0),
                            children
                        }
                    )
                ]
            }
        )
    );
    const footerY = Math.max(0, height - footerHeight),
        actionWidth = width < 480 ? 126 : 150,
        closeWidth = 90,
        actionX = width - actionWidth - 12;
    nodes.push(
        node('Box', 'ingestFooter', rect(0, footerY, width, footerHeight), {
            background: 'surfaceContainer',
            children: [
                label(
                    'ingestMessage',
                    rect(12, 6, Math.max(0, actionX - closeWidth - 40), 46),
                    model.error ||
                        model.message ||
                        (model.busy ? tr('Loading data…') : ''),
                    {
                        fontRole: 'caption',
                        wrap: true,
                        color: model.error ? 'error' : 'secondaryText',
                        role: model.error ? 'alert' : 'status'
                    }
                ),
                button(
                    'ingestClose',
                    rect(actionX - closeWidth - 8, 10, closeWidth, 38),
                    tr(model.busy && model.canStop ? 'Stop' : 'Close'),
                    '',
                    { type: model.busy && model.canStop ? 'stop' : 'close' },
                    !model.busy || !!model.canStop
                ),
                button(
                    'ingestStart',
                    rect(actionX, 10, actionWidth, 38),
                    tr('Ingest {count}', { count: model.count }),
                    'upload',
                    { type: 'start' },
                    !model.busy &&
                        !model.rulesBusy &&
                        model.ready !== false &&
                        model.count > 0 &&
                        model.canStart !== false,
                    { highlighted: true }
                )
            ]
        })
    );
    return { nodes };
}

export function conflict(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [],
        inner = Math.max(0, width - 32),
        compact = width < 480,
        message = tr(
            '{count} file(s) match existing child items or repeat a name in this batch. What should ingest do?',
            { count: model.conflictCount }
        ),
        messageHeight = Math.max(40, captionHeight(message, inner));
    nodes.push(
        label(
            'ingestConflictMessage',
            rect(16, 12, inner, messageHeight),
            message,
            { wrap: true }
        )
    );
    let y = 22 + messageHeight;
    if (model.conflictNames?.length) {
        nodes.push(
            label(
                'ingestConflictNames',
                rect(16, y, inner, 22),
                tr('Conflicts: {names}', {
                    names: model.conflictNames.slice(0, 5).join(', ')
                }),
                muted
            )
        );
        y += 32;
    }
    if (!model.canUpdateConflicts) {
        const text = tr(
                'Update is unavailable because at least one name does not identify exactly one existing item.'
            ),
            h = captionHeight(text, inner);
        nodes.push(
            label(
                'ingestConflictUnavailable',
                rect(16, y, inner, h),
                text,
                Object.assign({}, muted, { wrap: true })
            )
        );
        y += h + 10;
    }
    const columns = compact ? 1 : 2,
        w = (inner - (columns - 1) * 8) / columns;
    for (const [index, [decision, text, icon]] of [
        ['cancel', 'Cancel', ''],
        ['duplicates', 'Create duplicates', 'copy'],
        ['skip', 'Skip existing', 'cancel'],
        ['update', 'Update existing', 'refresh']
    ].entries())
        nodes.push(
            button(
                'ingestConflict_' + decision,
                rect(
                    16 + (index % columns) * (w + 8),
                    y + Math.floor(index / columns) * 46,
                    w,
                    38
                ),
                tr(text),
                icon,
                { type: 'conflict', decision },
                decision !== 'update' || !!model.canUpdateConflicts,
                {
                    highlighted: model.canUpdateConflicts
                        ? decision === 'update'
                        : decision === 'skip'
                }
            )
        );
    return { nodes, height: y + (4 / columns) * 46 + 8 };
}
