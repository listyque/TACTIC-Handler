import { button } from '../../../core/frame.mjs';
import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    notices,
    toolbar as documentToolbar,
    policy,
    sectionSelector
} from '../admin.document.mjs';
import { form } from '../admin.form.mjs';
import { translate } from '../../../core/strings.mjs';
export function toolbar(model, ui, width, language) {
    const result = documentToolbar(model, ui, width, language),
        tr = (text) => translate(text, language);
    result.nodes = result.nodes.filter(
        (row) => row.id !== 'adminDocumentStatus'
    );
    result.nodes.push(
        button(
            'adminAddProcessRule',
            rect(46, 0, 38, 38),
            tr('Add rule'),
            'add',
            {
                type: 'add'
            },
            model.canWrite &&
                !model.busy &&
                !model.uncertain &&
                ['trigger', 'notification'].indexOf(ui.page) >= 0,
            {
                iconOnly: true
            }
        )
    );
    return result;
}
export function models(model, ui) {
    return {
        processRules: model.document.rules
            .map((rule, index) => ({
                identity: String(index),
                index,
                rule
            }))
            .filter((row) => row.rule.kind === ui.page),
        processNaming: (model.metadata.naming || []).map((row, index) =>
            Object.assign(
                {
                    identity: String(index)
                },
                row
            )
        ),
        processObjects: (model.metadata.items || []).map((row) =>
            Object.assign(
                {
                    identity: row.key
                },
                row
            )
        )
    };
}
export function row(list, record, model, language) {
    const tr = (text) => translate(text, language),
        w = list.width - 16;
    const rule = record.rule,
        heading = rule
            ? rule.title || (rule.key ? rule.event : tr('New rule'))
            : list.source === 'processNaming'
              ? record.context || ''
              : record.label || record.key;
    const description = rule
        ? tr(
              rule.managed
                  ? 'Managed by node parameters'
                  : rule.scope === 'global'
                    ? 'All matching processes'
                    : 'This pipeline'
          )
        : list.source === 'processNaming'
          ? (record.directory || '') + ' / ' + (record.file || '')
          : record.key;
    return {
        nodes: [
            node(
                'Action',
                'processRuleRow_' + list.source + '_' + record.identity,
                rect(0, 0, w, 78),
                {
                    text: heading,
                    enabled: !model.busy,
                    selected: !!rule && model.selected === record.index,
                    normalColor: 'surfaceContainerHigh',
                    selectedColor: 'contentSelection',
                    children: [
                        label(
                            'processRuleTitle_' +
                                list.source +
                                '_' +
                                record.identity,
                            rect(12, 4, w - 24, 28),
                            heading,
                            {
                                weight: 600
                            }
                        ),
                        label(
                            'processRuleDetail_' +
                                list.source +
                                '_' +
                                record.identity,
                            rect(12, 36, w - 24, 34),
                            description,
                            muted
                        )
                    ],
                    action: rule
                        ? {
                              type: 'select',
                              index: record.index
                          }
                        : list.source === 'processObjects'
                          ? {
                                type: 'object',
                                key: record.key
                            }
                          : null
                }
            )
        ]
    };
}
export function fields(model, language) {
    const tr = (text) => translate(text, language),
        rule = model.rule,
        metadata = model.metadata,
        fields = [];
    const text = (key, title, description, area) => ({
        id: 'adminRule_' + key,
        title,
        description,
        kind: area ? 'Area' : 'Field',
        height: area ? 120 : 38,
        field: key,
        props: {
            text: rule[key] || ''
        }
    });
    const choices = (key, title, options, description, value) => ({
        id: 'adminRule_' + key,
        title,
        description,
        kind: 'Choice',
        field: key,
        options: options.map((row) => ({
            value: row.value,
            label: row.data ? row.label : tr(row.label)
        })),
        props: {
            value: value === undefined ? rule[key] || '' : value
        }
    });
    const toggle = (key, title, description) => ({
        id: 'adminRule_' + key,
        title,
        description,
        kind: 'Switch',
        field: key,
        props: {
            checked: rule[key] === true
        }
    });
    fields.push(
        text('title', 'Name', 'The readable name of this rule.'),
        text(
            'description',
            'Description',
            'Explain why this rule is needed.',
            true
        ),
        choices(
            'scope',
            'Scope',
            [
                {
                    value: 'local',
                    label: 'This pipeline'
                },
                {
                    value: 'global',
                    label: 'All matching processes'
                }
            ],
            rule.scope === 'global'
                ? 'Applies to every process with this name in the project, including other pipelines.'
                : 'Applies only to this process in this pipeline.'
        )
    );
    const events = [
            {
                value: 'change|sthpw/task|status',
                label: 'Task status changed'
            },
            {
                value: 'change|sthpw/task|assigned',
                label: 'Task assignee changed'
            },
            {
                value: 'insert|sthpw/note',
                label: 'Note created'
            },
            {
                value: 'change|sthpw/note',
                label: 'Note created or modified'
            },
            {
                value: 'checkin|' + (metadata.searchType || ''),
                label: 'File checked in'
            }
        ],
        known = events.some((row) => row.value === rule.event);
    fields.push(
        choices(
            'event',
            'Event',
            events.concat([
                {
                    value: '',
                    label: 'Custom event'
                }
            ]),
            'The native event that starts this rule.',
            known ? rule.event : ''
        )
    );
    if (!known) {
        const custom = text('event', 'Native event identifier');
        custom.id = 'adminRuleCustomEvent';
        fields.push(custom);
    }
    if (
        rule.event === 'change|sthpw/task|status' &&
        rule.action !== 'parent_status'
    )
        fields.push(
            choices(
                'srcStatus',
                'Source status',
                [
                    {
                        value: '',
                        label: 'Any status'
                    }
                ].concat(
                    (metadata.sourceStatuses || []).map((value) => ({
                        value,
                        label: value,
                        data: true
                    }))
                ),
                'Filter the source task status, or listen to any status.'
            )
        );
    if (rule.kind !== 'notification')
        fields.push(
            choices(
                'action',
                'Action',
                [
                    {
                        value: 'task_status',
                        label: 'Change task statuses'
                    },
                    {
                        value: 'parent_status',
                        label: 'Change parent status'
                    },
                    {
                        value: 'task_create',
                        label: 'Create output tasks'
                    },
                    {
                        value: 'task_date',
                        label: 'Set actual task date'
                    },
                    {
                        value: 'custom_script',
                        label: 'Server script'
                    },
                    {
                        value: 'python_class',
                        label: 'Server command class'
                    }
                ],
                'Saving configures the trigger. It does not run the action.'
            )
        );
    if (rule.action === 'task_status') {
        fields.push({
            kind: 'Heading',
            id: 'ruleTargetsHeading',
            title: 'Destination tasks',
            description: 'Each process uses its own task status workflow.'
        });
        for (const process of metadata.processes || []) {
            const target = (rule.targets || []).find(
                    (row) => row.process === process.identity
                ),
                status = target
                    ? target.status
                    : (process.statuses || [])[0] || '';
            fields.push(
                {
                    id: 'adminRuleTarget_' + process.identity,
                    title: process.label || process.identity,
                    dataLabel: true,
                    kind: 'Switch',
                    props: {
                        checked: !!target,
                        action: {
                            type: 'target',
                            process: process.identity,
                            status
                        }
                    }
                },
                {
                    id: 'adminRuleTargetStatus_' + process.identity,
                    title: 'Destination status',
                    kind: 'Choice',
                    options: (process.statuses || []).map((value) => ({
                        value,
                        label: value
                    })),
                    props: {
                        value: status,
                        enabled:
                            policy(model).editable && !rule.managed && !!target,
                        action: {
                            type: 'target',
                            process: process.identity,
                            enabled: true
                        }
                    }
                }
            );
        }
    }
    if (rule.action === 'task_create') {
        fields.push({
            kind: 'Heading',
            id: 'ruleOutputsHeading',
            title: 'Output processes',
            description:
                'Only connected output processes are available. Add connections on the canvas first.'
        });
        for (const process of metadata.outputs || [])
            fields.push({
                id: 'adminRuleOutput_' + process,
                title: process,
                dataLabel: true,
                kind: 'Switch',
                props: {
                    checked: (rule.outputs || []).indexOf(process) >= 0,
                    action: {
                        type: 'output',
                        process
                    }
                }
            });
    }
    if (rule.action === 'task_date')
        fields.push(
            choices(
                'column',
                'Actual date',
                [
                    {
                        value: 'actual_start_date',
                        label: 'Start'
                    },
                    {
                        value: 'actual_end_date',
                        label: 'End'
                    }
                ],
                'Choose which actual task date to set.'
            )
        );
    if (rule.action === 'custom_script')
        fields.push(
            choices(
                'scriptPath',
                'Server script',
                (metadata.scriptPaths || []).map((value) => ({
                    value,
                    label: value,
                    data: true
                })),
                'Select an existing server script. Its source remains in the Script Editor.'
            )
        );
    for (const field of [
        {
            key: 'targetStatus',
            title: 'Destination status',
            action: 'parent_status'
        },
        {
            key: 'classPath',
            title: 'Installed Python class',
            action: 'python_class'
        },
        {
            key: 'subject',
            title: 'Subject',
            action: 'notification'
        },
        {
            key: 'mailTo',
            title: 'Recipients',
            action: 'notification'
        },
        {
            key: 'mailCc',
            title: 'Copy recipients',
            action: 'notification'
        }
    ])
        if (rule.action === field.action)
            fields.push(
                text(
                    field.key,
                    field.title,
                    'Native action parameters. TACTIC expressions are supported by notifications.'
                )
            );
    if (rule.kind === 'notification') {
        fields.push(
            {
                kind: 'Heading',
                id: 'ruleNotificationHeading',
                title: 'Notification content',
                description:
                    'TACTIC expressions are supported in recipients, subject and body. Saving does not send a notification.'
            },
            toggle(
                'useTemplate',
                'Use the native event template on save',
                'The native event template replaces the subject and body when saved.'
            )
        );
        const body = text(
            'body',
            'Body',
            'Notification message with optional TACTIC expressions.',
            true
        );
        body.props.enabled =
            policy(model).editable && !rule.managed && !rule.useTemplate;
        fields.push(
            body,
            toggle(
                'loginTicket',
                'Generate a temporary login ticket',
                'The native notification handler may include a login ticket.'
            ),
            text(
                'rules',
                'Additional conditions (native rules XML)',
                'Conditions are checked as XML before saving.',
                true
            )
        );
    } else
        fields.push(
            choices(
                'mode',
                'Execution mode',
                [
                    {
                        value: 'same process,same transaction',
                        label: 'Same transaction'
                    },
                    {
                        value: 'separate process,blocking',
                        label: 'Separate process, wait'
                    },
                    {
                        value: 'separate process,non-blocking',
                        label: 'Separate process, background'
                    },
                    {
                        value: 'separate process,queued',
                        label: 'Queued'
                    }
                ],
                'Use the execution mode supported by the installed server handler.'
            )
        );
    return fields;
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        noticeModel = Object.assign({}, model, {
            error: model.error || ui.error
        });
    if (ui.confirmation === 'save')
        noticeModel.confirmationText =
            'Save process rules? Global rules affect matching processes in other pipelines. Removed rules are deleted; their scripts are kept. Actions are not executed by Save.';
    if (ui.confirmation === 'remove')
        noticeModel.confirmationText =
            'The rule will be removed from the server when you save. The script itself is not deleted.';
    const notice = notices(
            noticeModel,
            ui,
            width,
            language,
            undefined,
            ui.confirmation === 'remove' ? 'Remove rule' : undefined
        ),
        nodes = notice.nodes;
    let y = notice.top;
    nodes.push(
        sectionSelector(
            'adminDependencyPages',
            [
                {
                    value: 'trigger',
                    label:
                        tr('Triggers') +
                        ' · ' +
                        model.document.rules.filter(
                            (row) => row.kind === 'trigger'
                        ).length
                },
                {
                    value: 'notification',
                    label:
                        tr('Notifications') +
                        ' · ' +
                        model.document.rules.filter(
                            (row) => row.kind === 'notification'
                        ).length
                },
                {
                    value: 'naming',
                    label:
                        tr('Naming conventions') +
                        ' · ' +
                        (model.metadata.naming || []).length
                },
                {
                    value: 'objects',
                    label:
                        tr('Search Objects') +
                        ' · ' +
                        (model.metadata.itemCount || 0)
                }
            ],
            ui.page,
            rect(0, y, width, 38),
            !model.busy,
            'page'
        )
    );
    y += 46;
    const h = Math.max(1, height - y),
        rulePage = ['trigger', 'notification'].indexOf(ui.page) >= 0,
        split = width >= 800,
        left = split ? Math.min(ui.catalogWidth, width * 0.34) : width;
    if (rulePage) {
        if (split || !ui.editing)
            nodes.push(
                node('Box', 'processRulesCatalogPanel', rect(0, y, left, h), {
                    background: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    children: [
                        node(
                            'List',
                            'adminProcessRulesList',
                            rect(12, 12, left - 24, h - 24),
                            {
                                source: 'processRules',
                                keyField: 'identity',
                                rowHeight: 82,
                                scrollbarId: 'adminProcessRulesScrollBar'
                            }
                        )
                    ]
                })
            );
        if (split)
            nodes.push(
                node('Splitter', 'processRulesSplit', rect(left, y, 10, h), {
                    text: tr('Rule list width'),
                    value: left,
                    min: 180,
                    max: Math.min(420, width * 0.34),
                    action: {
                        type: 'split'
                    }
                })
            );
        if (split || ui.editing) {
            const x = split ? left + 10 : 0,
                w = width - x,
                children = [];
            let top = 12;
            if (!split) {
                children.push(
                    button(
                        'processRulesBack',
                        rect(12, top, w - 24, 36),
                        tr('Back'),
                        'chevron-left',
                        {
                            type: 'back'
                        },
                        !model.busy
                    )
                );
                top += 44;
            }
            if (model.rule.kind) {
                if (model.rule.managed) {
                    children.push(
                        label(
                            'processManagedHelp',
                            rect(12, top, w - 24, 100),
                            tr(
                                'This trigger is generated by the workflow engine. Edit its action or progress listener in the node parameters, not in a second copy here.'
                            ),
                            Object.assign(
                                {
                                    wrap: true
                                },
                                muted
                            )
                        )
                    );
                    top += 108;
                }
                const body = form(
                    fields(
                        Object.assign({}, model, {
                            busy: model.busy || !!ui.confirmation
                        }),
                        language
                    ),
                    w - 40,
                    language,
                    policy(model).editable &&
                        !model.rule.managed &&
                        !ui.confirmation
                );
                body.nodes.push(
                    button(
                        'adminRemoveProcessRule',
                        rect(0, body.height, w - 40, 38),
                        tr('Remove rule'),
                        'delete',
                        {
                            type: 'remove'
                        },
                        policy(model).editable &&
                            !model.rule.managed &&
                            !ui.confirmation
                    )
                );
                children.push(
                    node(
                        'Scroll',
                        'adminRuleViewport',
                        rect(12, top, w - 24, h - top - 12),
                        {
                            contentHeight: body.height + 46,
                            resetKey: String(model.selected),
                            scrollbarId: 'adminRuleScrollBar',
                            children: body.nodes
                        }
                    )
                );
            } else
                children.push(
                    label(
                        'processNoRule',
                        rect(12, top, w - 24, 120),
                        tr('No rules configured. Use Add rule to create one.'),
                        Object.assign(
                            {
                                wrap: true
                            },
                            muted
                        )
                    )
                );
            nodes.push(
                node('Box', 'processRuleEditorPanel', rect(x, y, w, h), {
                    background: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    children
                })
            );
        }
    } else {
        const objects = ui.page === 'objects',
            rows = objects
                ? model.metadata.items || []
                : model.metadata.naming || [],
            offset = model.metadata.itemOffset || 0,
            count = model.metadata.itemCount || 0;
        nodes.push(
            label(
                'processRelatedHelp',
                rect(12, y, width - 24, 84),
                tr(
                    objects
                        ? 'This count is for the pipeline, not the number of tasks in this process.'
                        : "Rules whose context starts with this process. Edit naming in the Search Type's existing Naming Editor."
                ),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            ),
            node(
                'List',
                'adminRelatedObjects',
                rect(12, y + 92, width - 24, h - (objects ? 146 : 104)),
                {
                    source: objects ? 'processObjects' : 'processNaming',
                    keyField: 'identity',
                    rowHeight: 82,
                    scrollbarId: 'adminRelatedObjectsScrollBar'
                }
            )
        );
        if (!rows.length)
            nodes.push(
                label(
                    'processRelatedEmpty',
                    rect(24, y + 100, width - 48, 80),
                    tr(
                        objects
                            ? 'No Search Objects'
                            : 'No naming conventions for this process.'
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
        if (objects)
            nodes.push(
                button(
                    'adminObjectsPrevious',
                    rect(12, height - 42, 100, 36),
                    tr('Previous'),
                    'chevron-left',
                    {
                        type: 'items',
                        offset: offset - 50
                    },
                    !model.busy && !model.dirty && offset > 0
                ),
                label(
                    'processObjectsPage',
                    rect(120, height - 42, width - 240, 36),
                    String(offset + (rows.length ? 1 : 0)) +
                        '–' +
                        (offset + rows.length) +
                        ' / ' +
                        count,
                    {
                        align: 'center'
                    }
                ),
                button(
                    'adminObjectsNext',
                    rect(width - 112, height - 42, 100, 36),
                    tr('Next'),
                    'chevron-right',
                    {
                        type: 'items',
                        offset: offset + 50
                    },
                    !model.busy && !model.dirty && offset + rows.length < count
                )
            );
    }
    return {
        nodes
    };
}

export function objectDetails(record, width, height, language) {
    const tr = (text) => translate(text, language),
        text = Object.keys(record || {})
            .map(
                (key) =>
                    key +
                    ': ' +
                    (typeof record[key] === 'object'
                        ? JSON.stringify(record[key], null, 2)
                        : String(record[key] ?? ''))
            )
            .join('\n\n');
    return {
        nodes: [
            node(
                'Area',
                'processObjectFields',
                rect(0, 0, width, height - 46),
                {
                    text,
                    readOnly: true,
                    monospace: true,
                    label: tr('Object details')
                }
            ),
            button(
                'processObjectClose',
                rect(Math.max(0, width - 140), height - 38, 140, 38),
                tr('Close'),
                'close',
                {
                    type: 'close'
                },
                true
            )
        ]
    };
}
