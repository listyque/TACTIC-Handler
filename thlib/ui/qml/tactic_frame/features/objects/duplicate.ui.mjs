import { controls } from '../../core/foundation.mjs';
export const scrollbarExtent = controls.scrollBar.extent;
import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

export const steps = [
    { label: 'Fields', icon: 'edit' },
    { label: 'Relations', icon: 'account-tree' },
    { label: 'Snapshots', icon: 'inventory-2' },
    { label: 'Tasks and messages', icon: 'task' },
    { label: 'Review', icon: 'fact-check' }
];
export const choices = [
    {
        name: 'copySnapshots',
        label: 'Snapshots',
        count: 'snapshotCount',
        page: 2
    },
    { name: 'copyTasks', label: 'Tasks', count: 'taskCount', page: 3 },
    {
        name: 'copyProcessMessages',
        label: 'Process messages',
        count: 'processMessageCount',
        page: 3
    },
    {
        name: 'copyProcessAttachments',
        label: 'Process attachments',
        count: 'processAttachmentCount',
        page: 3
    },
    {
        name: 'copyTaskMessages',
        label: 'Task messages',
        count: 'taskMessageCount',
        page: 3
    },
    {
        name: 'copyTaskAttachments',
        label: 'Task attachments',
        count: 'taskAttachmentCount',
        page: 3
    }
];

export function busyState(model, language) {
    return model.busy || model.saving
        ? {
              message: translate(
                  model.saving
                      ? 'Creating duplicate on the server… You can continue working.'
                      : 'Analyzing fields, relations and process content…',
                  language
              ),
              cancellable: !model.saving
          }
        : null;
}

export function header(model, width, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 700;
    const badgeWidth = narrow ? 0 : 132,
        right = 48 + badgeWidth;
    return {
        height: 68,
        nodes: [
            node('Box', 'duplicateSObjectHeader', rect(0, 0, width, 68), {
                background: 'surfaceContainer',
                radiusRole: 'sectionRadius'
            }),
            node('Box', 'duplicateIconSurface', rect(12, 13, 42, 42), {
                background: 'surfaceContainerHigh',
                children: [
                    node('Icon', 'duplicateIcon', rect(10, 10, 22, 22), {
                        icon: 'control-point-duplicate',
                        color: 'action'
                    })
                ]
            }),
            label(
                'duplicateTitle',
                rect(65, 12, Math.max(0, width - 65 - right), 24),
                tr('Duplicate') + ' ' + (model.title || tr('sObject')),
                { fontRole: 'bodyLarge', weight: 600 }
            ),
            label(
                'duplicateSearchType',
                rect(65, 38, Math.max(0, width - 65 - right), 18),
                model.searchType || '',
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    elideMiddle: true
                }
            ),
            ...(narrow
                ? []
                : [
                      node(
                          'StatusChip',
                          'duplicateStepCount',
                          rect(width - right, 22, badgeWidth - 8, 24),
                          {
                              text: translate('Step {step} of 5', language, {
                                  step: model.step + 1
                              }),
                              icon: steps[model.step].icon,
                              accent: 'action'
                          }
                      )
                  ]),
            button(
                'duplicateHelp',
                rect(width - 42, 18, 32, 32),
                tr('Duplication help'),
                'help',
                { type: 'help' },
                true,
                { iconOnly: true, iconAction: true }
            )
        ]
    };
}

export function tabs(model, width, language) {
    const cell = Math.max(0, (width - 16) / 5);
    return {
        height: 36,
        nodes: [
            node('Box', 'duplicateStepSurface', rect(0, 0, width, 36), {
                background: 'surfaceContainerHigh',
                radius: 8
            }),
            ...steps.map((step, index) =>
                button(
                    'duplicateStep_' + index,
                    rect(4 + index * (cell + 2), 2, cell, 32),
                    translate(step.label, language),
                    step.icon,
                    { type: 'step', value: index },
                    !model.busy && !model.saving,
                    {
                        radio: true,
                        selected: model.step === index,
                        iconOnly: width < 600,
                        iconSize: 16
                    }
                )
            )
        ]
    };
}

export function footer(model, width, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 680,
        height = narrow ? 104 : 64;
    const nodes = [
        node('Box', 'duplicateSObjectFooter', rect(0, 0, width, height), {
            background: 'surfaceContainer'
        })
    ];
    if (model.ready)
        nodes.push(
            node(
                'CheckBox',
                'duplicateRememberSettings',
                rect(
                    13,
                    10,
                    narrow ? width - 26 : Math.max(80, width - 398),
                    36
                ),
                {
                    label: tr('Remember choices'),
                    text: tr(
                        width < 1000
                            ? 'Remember'
                            : 'Remember for this Search Type'
                    ),
                    checked: model.remember,
                    enabled: !model.saving,
                    action: { type: 'remember' }
                }
            )
        );
    const actions = [
        ['cancel', 'Cancel', '', true],
        ...(model.ready && model.step > 0
            ? [['back', 'Back', 'arrow-back', !model.busy && !model.saving]]
            : []),
        ...(model.ready && model.step < 4
            ? [['next', 'Next', 'arrow-forward', !model.busy && !model.saving]]
            : []),
        [
            'duplicate',
            'Duplicate',
            'control-point-duplicate',
            model.ready &&
                !model.busy &&
                !model.saving &&
                !model.uncertain &&
                model.valid !== false
        ]
    ];
    const gap = 6,
        available = width - 26;
    const widths = actions.map(([type]) =>
        narrow
            ? Math.max(
                  0,
                  (available - gap * (actions.length - 1)) / actions.length
              )
            : type === 'duplicate'
              ? 110
              : type === 'cancel'
                ? 72
                : 36
    );
    const start =
        width -
        13 -
        widths.reduce((sum, w) => sum + w, 0) -
        gap * (actions.length - 1);
    actions.forEach(([type, text, icon, enabled], index) =>
        nodes.push(
            button(
                'duplicate_' + type,
                rect(
                    start +
                        widths
                            .slice(0, index)
                            .reduce((sum, w) => sum + w + gap, 0),
                    narrow ? 58 : 14,
                    widths[index],
                    36
                ),
                tr(text),
                icon,
                { type },
                enabled && (type !== 'cancel' || !model.saving),
                {
                    highlighted: type === 'duplicate',
                    iconSize: 16,
                    iconOnly: !narrow && ['back', 'next'].includes(type)
                }
            )
        )
    );
    return { height, nodes };
}

export function body(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let y = 0;
    function paragraph(id, text, icon, background = 'surfaceContainerLow') {
        const h = Math.max(
            44,
            captionHeight(text, Math.max(1, width - (icon ? 62 : 28))) + 24
        );
        nodes.push(
            node('Box', id, rect(0, y, width, h), {
                background,
                children: [
                    ...(icon
                        ? [
                              node(
                                  'Icon',
                                  id + 'Icon',
                                  rect(12, (h - 18) / 2, 18, 18),
                                  { icon, color: 'action' }
                              )
                          ]
                        : []),
                    label(
                        id + 'Text',
                        rect(
                            icon ? 40 : 14,
                            12,
                            Math.max(0, width - (icon ? 54 : 28)),
                            h - 24
                        ),
                        text,
                        { wrap: true, color: 'secondaryText' }
                    )
                ]
            })
        );
        y += h + 10;
    }
    function intro(id, text) {
        const h = captionHeight(text, Math.max(1, width));
        nodes.push(
            label(id + 'Text', rect(0, y, width, h), text, {
                wrap: true,
                color: 'secondaryText'
            })
        );
        y += h + 8;
    }
    if (model.error) {
        paragraph(
            'duplicateError',
            tr(model.error),
            'warning',
            'errorContainer'
        );
        if (!model.uncertain) {
            nodes.push(
                button(
                    'duplicateRetry',
                    rect(0, y, 120, 36),
                    tr(model.ready ? 'Analyze again' : 'Retry'),
                    'refresh',
                    { type: 'retry' },
                    !model.busy
                )
            );
            y += 46;
        }
    }
    if (!model.ready) return { height: Math.max(0, y - 10), nodes };
    if (model.step === 0)
        paragraph(
            'duplicateFieldIntro',
            tr(
                'Edit the values of the new object. Identity, project and relationship columns are generated or managed automatically.'
            ),
            'edit'
        );
    else if (model.step === 1) {
        intro(
            'duplicateRelationIntro',
            tr(
                'Choose what happens to each relationship already attached to the source object.'
            )
        );
        (model.relations || []).forEach((record, index) => {
            const children = [
                node('Box', 'relationIconSurface', rect(11, 11, 34, 34), {
                    background: 'surfaceContainerHigh',
                    children: [
                        node('Icon', 'relationIcon', rect(8, 8, 18, 18), {
                            icon:
                                record.kind === 'instance'
                                    ? 'hub'
                                    : record.kind === 'parent'
                                      ? 'arrow-upward'
                                      : 'arrow-downward',
                            color: 'action'
                        })
                    ]
                }),
                label(
                    'relationTitle',
                    rect(55, 11, Math.max(0, width - 66), 20),
                    record.title,
                    { weight: 600 }
                ),
                label(
                    'relationDetails',
                    rect(55, 32, Math.max(0, width - 66), 17),
                    tr(
                        record.kind === 'instance'
                            ? 'Instance links'
                            : record.kind === 'parent'
                              ? 'Parent'
                              : 'Children'
                    ) +
                        ' · ' +
                        record.count +
                        (record.path ? ' · ' + record.path : ''),
                    { fontRole: 'caption', color: 'secondaryText' }
                )
            ];
            const options = record.options || [],
                cell = Math.max(
                    0,
                    (width - 22 - 6 * (options.length - 1)) /
                        Math.max(1, options.length)
                );
            options.forEach((option, i) =>
                children.push(
                    button(
                        'duplicateRelationMode_' + index + '_' + i,
                        rect(11 + i * (cell + 6), 58, cell, 36),
                        tr(option.label),
                        '',
                        {
                            type: 'relation',
                            index,
                            key: record.key,
                            value: option.value
                        },
                        !model.saving,
                        { radio: true, selected: record.mode === option.value }
                    )
                )
            );
            const text = (record.items || [])
                .map((item) => item.title)
                .join('  ·  ');
            if (text)
                children.push(
                    label(
                        'relationItems',
                        rect(11, 102, width - 22, 18),
                        text,
                        {
                            fontRole: 'caption',
                            color: 'secondaryText',
                            tooltip: text
                        }
                    )
                );
            const height = text ? 131 : 105;
            nodes.push(
                node(
                    'Box',
                    'duplicateRelation_' + index,
                    rect(0, y, width, height),
                    {
                        background: 'surfaceContainer',
                        radiusRole: 'sectionRadius',
                        children
                    }
                )
            );
            y += height + 8;
        });
        if (!(model.relations || []).length)
            paragraph(
                'duplicateRelationsEmpty',
                tr('No linked objects'),
                'link-off'
            );
    } else if (model.step === 2 || model.step === 3) {
        intro(
            'duplicateContentIntro',
            tr(
                model.step === 2
                    ? 'Choose current snapshots and files to duplicate for each process. Message attachments are handled with their messages on the next step.'
                    : 'Choose tasks, process messages, task messages, and their attached files. Copying task messages also copies their parent tasks.'
            )
        );
        let count = 0;
        (model.processes || []).forEach((record, index) => {
            const available = choices.filter(
                (choice) => choice.page === model.step && record[choice.count]
            );
            if (!available.length) return;
            count++;
            const children = [
                node('Icon', 'processIcon', rect(16, 18, 20, 20), {
                    icon: 'account-tree',
                    color: 'action'
                }),
                label(
                    'processTitle',
                    rect(47, 12, Math.max(0, width - 60), 24),
                    record.name,
                    { weight: 600 }
                )
            ];
            children.push(
                node(
                    'StatusChip',
                    'processCount',
                    rect(Math.max(47, width - 106), 10, 94, 24),
                    {
                        icon: 'inventory-2',
                        text: translate('{count} items', language, {
                            count:
                                model.step === 2
                                    ? record.snapshotCount
                                    : Number(record.taskCount || 0) +
                                      Number(record.processMessageCount || 0) +
                                      Number(record.taskMessageCount || 0)
                        }),
                        accent: 'secondaryText'
                    }
                )
            );
            let top = 42,
                left = 11;
            available.forEach((choice) => {
                const text =
                    tr(choice.label) +
                    ' ' +
                    record[choice.count] +
                    (choice.name === 'copySnapshots'
                        ? ' · ' + tr('Files') + ' ' + record.fileCount
                        : '');
                const w = Math.min(
                    Math.max(0, width - 22),
                    text.length * 6.5 + 32
                );
                if (left > 11 && left + w > width - 11) {
                    left = 11;
                    top += 36;
                }
                children.push(
                    node(
                        'CheckBox',
                        'duplicateChoice_' + index + '_' + choice.name,
                        rect(left, top, w, 32),
                        {
                            label: tr(choice.label),
                            text,
                            checked: !!record[choice.name],
                            enabled: !model.saving,
                            action: { type: 'choice', index, name: choice.name }
                        }
                    )
                );
                left += w + 8;
            });
            top += 32;
            nodes.push(
                node(
                    'Box',
                    'duplicateProcess_' + index,
                    rect(0, y, width, top + 7),
                    {
                        background: 'surfaceContainer',
                        radiusRole: 'sectionRadius',
                        children
                    }
                )
            );
            y += top + 15;
        });
        if (!count)
            paragraph(
                'duplicateContentEmpty',
                tr(
                    model.step === 2
                        ? 'No current snapshots'
                        : 'No tasks or messages'
                ),
                'inventory-2'
            );
    } else {
        const totals = model.totals || {},
            columns = width >= 600 ? 4 : 2,
            cell = (width - 28 - 7 * (columns - 1)) / columns;
        const text = tr(
                'The new object receives the edited fields. Selected links are recreated; original instance targets are never duplicated.'
            ),
            textHeight = captionHeight(text, Math.max(1, width - 28));
        const top = 92 + textHeight,
            height = top + Math.ceil(4 / columns) * 36 + 14;
        const children = [
            node(
                'Icon',
                'duplicateReviewIcon',
                rect((width - 34) / 2, 14, 34, 34),
                { icon: 'control-point-duplicate', color: 'action' }
            ),
            label(
                'duplicateReviewTitle',
                rect(14, 58, width - 28, 25),
                tr('Ready to create the duplicate'),
                { fontRole: 'bodyLarge', weight: 600, align: 'center' }
            ),
            label(
                'duplicateReviewExplanation',
                rect(14, 88, width - 28, textHeight),
                text,
                { color: 'secondaryText', wrap: true, align: 'center' }
            )
        ];
        [
            ['Related', totals.related],
            ['Snapshots', totals.snapshots],
            ['Tasks', totals.tasks],
            ['Messages and files', totals.messages]
        ].forEach(([text, count], i) =>
            children.push(
                node(
                    'SummaryChip',
                    'duplicateTotal_' + i,
                    rect(
                        14 + (i % columns) * (cell + 7),
                        top + Math.floor(i / columns) * 36,
                        cell,
                        28
                    ),
                    {
                        text: tr(text),
                        count: count || 0,
                        showCount: true,
                        accent: 'action'
                    }
                )
            )
        );
        nodes.push(
            node('Box', 'duplicateReview', rect(0, y, width, height), {
                background: 'surfaceContainer',
                children
            })
        );
        y += height + 10;
        paragraph(
            'duplicateQuickChoice',
            tr(
                model.remember
                    ? 'These choices will enable Quick duplicate for this Search Type.'
                    : 'These choices will be used only once.'
            ),
            'bolt'
        );
    }
    return { height: Math.max(0, y - 10), nodes };
}
