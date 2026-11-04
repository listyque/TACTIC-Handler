import { fieldGroups } from './workflow.fields.mjs';
import { translate } from '../../../core/strings.mjs';

export function nodeTypeMeta(kind, tr = (text) => text) {
    const key = kind === 'node' ? 'manual' : kind || 'manual';
    const map = {
        manual: {
            value: 'manual',
            label: tr('Manual · Task'),
            shortLabel: tr('Manual'),
            icon: 'person',
            color: '#4d79b8',
            badge: 'TASK',
            description: tr(
                'Standard human task stage (rectangular card). Creates an artist task and advances when its status reaches complete.'
            )
        },
        action: {
            value: 'action',
            label: tr('Action · Auto script'),
            shortLabel: tr('Action'),
            icon: 'bolt',
            color: '#2e9b88',
            badge: 'AUTO',
            description: tr(
                'Automated process (rounded pill). Runs a server script or command class automatically when triggered by upstream stages.'
            )
        },
        condition: {
            value: 'condition',
            label: tr('Condition · Branching'),
            shortLabel: tr('Condition'),
            icon: 'help',
            color: '#cf8a2e',
            badge: 'IF / ?',
            description: tr(
                'Conditional branch (diamond markers). Evaluates a script condition and routes flow to success or failure output streams.'
            )
        },
        approval: {
            value: 'approval',
            label: tr('Approval · Sign-off'),
            shortLabel: tr('Approval'),
            icon: 'approval',
            color: '#8a5ec4',
            badge: 'GATE',
            description: tr(
                'Review gate (double-ring stadium). Requires supervisor approval; rejecting sends status back to upstream stages.'
            )
        },
        hierarchy: {
            value: 'hierarchy',
            label: tr('Hierarchy · Sub-workflow'),
            shortLabel: tr('Hierarchy'),
            icon: 'hierarchy',
            color: '#3e8eb8',
            badge: 'SUB',
            description: tr(
                'Nested sub-pipeline container. Expands into child workflow processes and can create parent and child tasks.'
            )
        },
        dependency: {
            value: 'dependency',
            label: tr('Dependency · External wait'),
            shortLabel: tr('Dependency'),
            icon: 'link',
            color: '#c76a3e',
            badge: 'WAIT',
            description: tr(
                'Cross-object dependency node. Waits for or triggers a process on a related Search Type (parent, child, or expression).'
            )
        },
        progress: {
            value: 'progress',
            label: tr('Progress · Tracker'),
            shortLabel: tr('Progress'),
            icon: 'progress',
            color: '#49a065',
            badge: '%',
            description: tr(
                'Circular progress aggregator. Tracks completion across related objects in another Search Type and pipeline.'
            )
        },
        status: {
            value: 'status',
            label: tr('Status · Task state'),
            shortLabel: tr('Status'),
            icon: 'status',
            color: '#5b73c7',
            badge: 'STATE',
            description: tr(
                'Task status state (used in sthpw/task status pipelines). Defines a status name, color, and completion flag.'
            )
        }
    };
    return (
        map[key] || {
            value: key,
            label: key,
            shortLabel: key,
            icon: 'schema',
            color: '#4d79b8',
            badge: String(key).toUpperCase(),
            description: ''
        }
    );
}

export function section(field, kind) {
    return field.section === undefined
        ? kind === 'progress'
            ? 'progress'
            : 'default'
        : field.section;
}
export function value(model, field) {
    const part = section(field, model.processKind),
        source =
            part === 'properties'
                ? model.processProperties
                : part
                  ? (model.processSettings || {})[part]
                  : model.processSettings;
    return source && source[field.key] !== undefined
        ? source[field.key]
        : field.initial === undefined
          ? ''
          : field.initial;
}
export function options(model, field, language) {
    const tr = (text) => translate(text, language),
        settings = model.processSettings || {},
        related =
            settings[
                model.processKind === 'progress' ? 'progress' : 'default'
            ] || {},
        catalog = model.processCatalog || model.metadata || {};
    let rows = field.choices || catalog[field.options] || [];
    if (field.options === 'relatedPipelines')
        rows = (catalog.pipelines || []).filter(
            (row) => row.searchType === related.related_search_type
        );
    if (field.options === 'relatedProcesses')
        rows = (catalog.processes || [])
            .filter((row) => row.pipeline === related.related_pipeline_code)
            .map((row) => ({
                identity:
                    model.processKind === 'progress' ? row.identity : row.label,
                label: row.label
            }));
    return [
        {
            value: '',
            label: tr('Not set')
        }
    ].concat(
        rows.map((row) => ({
            value: row.identity,
            label: field.choices ? tr(row.label) : row.label || row.identity
        }))
    );
}
export function fields(model, ui, language) {
    const tr = (text) => translate(text, language),
        kind = model.processKind,
        currentMeta = nodeTypeMeta(kind, tr),
        settings = model.processSettings || {},
        defaults = settings.default || {},
        catalog = model.processCatalog || model.metadata || {};
    const out = [
        {
            kind: 'Heading',
            id: 'processHeading',
            title: model.selectedNode,
            dataLabel: true,
            description:
                tr('Node type: %1').replace(
                    '%1',
                    currentMeta.label + ' (' + kind + ')'
                ) +
                (currentMeta.description ? '\n' + currentMeta.description : '')
        },
        {
            id: 'adminProcessDescription',
            title: 'Description',
            description: 'Explain what happens at this stage of the workflow.',
            props: {
                text: model.processDescription || '',
                action: {
                    type: 'description'
                }
            }
        }
    ];
    const setting = (key, title, part, initial, choices, description) => ({
        id: 'adminProcessField_' + key,
        title,
        description,
        kind: choices ? 'Choice' : 'Field',
        options: choices,
        props: Object.assign(
            {
                action: {
                    type: 'setting',
                    section: part,
                    key
                }
            },
            choices
                ? {
                      value:
                          (settings[part] || {})[key] === undefined
                              ? initial
                              : (settings[part] || {})[key]
                  }
                : {
                      text: String((settings[part] || {})[key] || initial || '')
                  }
        )
    });
    if (['manual', 'node', 'approval'].indexOf(kind) >= 0) {
        out.push(
            {
                kind: 'Heading',
                id: 'processTaskPipelineHeading',
                title: 'Task status workflow',
                description:
                    'Defines statuses only for tasks of this process, not stages of the parent Search Object workflow.'
            },
            {
                kind: 'Choice',
                id: 'adminProcessField_task_pipeline',
                fullWidth: true,
                title: 'Task status workflow',
                options: [
                    {
                        value: '',
                        label: tr('Use TACTIC default')
                    }
                ].concat(
                    (catalog.pipelines || [])
                        .filter((row) => row.searchType === 'sthpw/task')
                        .map((row) => ({
                            value: row.identity,
                            label: row.label || row.identity
                        }))
                ),
                props: {
                    value: model.processProperties.task_pipeline || '',
                    action: {
                        type: 'setting',
                        section: 'properties',
                        key: 'task_pipeline'
                    }
                }
            },
            {
                kind: 'Button',
                id: 'adminEditTaskWorkflow',
                title: 'Edit task status workflow',
                props: {
                    icon: 'edit',
                    enabled:
                        !model.busy && !!model.processProperties.task_pipeline,
                    action: {
                        type: 'taskWorkflow'
                    }
                }
            }
        );
    }
    for (const group of fieldGroups.filter(
        (row) => !row.kinds || row.kinds.indexOf(kind) >= 0
    )) {
        out.push({
            kind: 'Heading',
            id: 'processGroup_' + group.title.replace(/\W/g, ''),
            title: group.title,
            description: group.description
        });
        for (const field of group.fields.filter(
            (row) => !row.kinds || row.kinds.indexOf(kind) >= 0
        )) {
            const current = value(model, field),
                part = section(field, kind),
                id = 'adminProcessField_' + field.key,
                integer = field.editor === 'integer';
            out.push({
                id,
                title: field.label,
                description: field.help,
                kind:
                    field.editor === 'boolean'
                        ? 'Switch'
                        : field.editor === 'color'
                          ? 'ColorChoice'
                          : !field.editor
                            ? 'Choice'
                            : 'Field',
                options: !field.editor
                    ? options(model, field, language)
                    : undefined,
                props: Object.assign(
                    {
                        action: integer
                            ? {
                                  type: 'buffer',
                                  key: 'integer_' + part + '_' + field.key
                              }
                            : {
                                  type: 'setting',
                                  section: part,
                                  key: field.key
                              }
                    },
                    field.editor === 'boolean'
                        ? {
                              checked: current === true || current === 'true'
                          }
                        : !field.editor || field.editor === 'color'
                          ? {
                                value: current
                            }
                          : {
                                text: Object.prototype.hasOwnProperty.call(
                                    ui.text,
                                    'integer_' + part + '_' + field.key
                                )
                                    ? ui.text[
                                          'integer_' + part + '_' + field.key
                                      ]
                                    : String(current),
                                inputMode: integer ? 'numeric' : 'text',
                                commitAction: integer
                                    ? {
                                          type: 'integer',
                                          section: part,
                                          key: field.key,
                                          min: field.minimum || 0,
                                          max: field.maximum || 1000000
                                      }
                                    : null
                            }
                )
            });
        }
    }
    out.push(
        {
            kind: 'Heading',
            id: 'processDependenciesHeading',
            title: 'Process dependencies',
            description:
                'Triggers, notifications, naming conventions and objects using this pipeline. Save node changes before editing dependencies.'
        },
        {
            kind: 'Button',
            id: 'adminOpenProcessDependencies',
            title: 'Open process dependencies',
            props: {
                icon: 'schema',
                enabled: !model.busy && !model.uncertain,
                action: {
                    type: 'dependencies'
                }
            }
        }
    );
    if (['action', 'condition'].indexOf(kind) >= 0) {
        out.push(
            {
                kind: 'Heading',
                id: 'processActionHeading',
                title: 'Process action',
                description:
                    'Action and condition nodes use a native process|action trigger. Script changes are saved, not executed by this editor.'
            },
            setting(
                'action',
                'Action',
                'default',
                'create_new',
                [
                    {
                        value: 'create_new',
                        label: tr('Script')
                    },
                    {
                        value: 'command',
                        label: tr('Command class')
                    }
                ],
                'Use a script or an installed server command class.'
            )
        );
        if (defaults.action === 'command')
            out.push(
                setting(
                    'on_action_class',
                    'Native command class',
                    'default',
                    '',
                    '',
                    'The installed Python command that handles this action.'
                )
            );
        else
            out.push(
                setting(
                    'script_path',
                    'Script path (optional)',
                    'default',
                    '',
                    '',
                    'Use an existing server script, or provide a script body below.'
                ),
                setting(
                    'language',
                    'Script language',
                    'default',
                    'python',
                    [
                        {
                            value: 'python',
                            label: 'python'
                        },
                        {
                            value: 'server_js',
                            label: 'server_js'
                        }
                    ],
                    'The language used by the native server handler.'
                )
            );
        out.push(
            setting(
                'execute_mode',
                'Trigger execution mode',
                'default',
                '',
                [
                    {
                        value: '',
                        label: tr('Not set')
                    },
                    {
                        value: 'same process,same transaction',
                        label: tr('In process')
                    },
                    {
                        value: 'separate process,blocking',
                        label: tr('Separate process, blocking')
                    },
                    {
                        value: 'separate process,non-blocking',
                        label: tr('Separate process, non-blocking')
                    },
                    {
                        value: 'separate process,queued',
                        label: tr('Queued')
                    }
                ],
                'Use the execution mode supported by the installed server handler.'
            )
        );
    }
    if (kind === 'hierarchy')
        out.push(
            {
                kind: 'Heading',
                id: 'processSubpipelineHeading',
                title: 'Subpipeline',
                description: 'Choose the pipeline this hierarchy process opens.'
            },
            {
                id: 'adminSubpipelineFilter',
                title: 'Find a pipeline',
                props: {
                    text: ui.subpipelineQuery,
                    action: {
                        type: 'subpipelineQuery'
                    }
                }
            },
            setting(
                'subpipeline',
                'Subpipeline',
                'hierarchy',
                '',
                [
                    {
                        value: '',
                        label: tr('Not set')
                    }
                ].concat(
                    (catalog.pipelines || [])
                        .filter(
                            (row) =>
                                row.identity !== model.identity &&
                                row.searchType === model.document.searchType &&
                                (row.label + ' ' + row.identity)
                                    .toLowerCase()
                                    .includes(ui.subpipelineQuery.toLowerCase())
                        )
                        .map((row) => ({
                            value: row.identity,
                            label: row.label || row.identity
                        }))
                )
            ),
            setting(
                'task_creation',
                'Create tasks',
                'default',
                'subtasks_only',
                [
                    {
                        value: 'subtasks_only',
                        label: tr('Create subtasks only')
                    },
                    {
                        value: 'top_only',
                        label: tr('Create parent task only')
                    },
                    {
                        value: 'all',
                        label: tr('Create parent task and subtasks')
                    },
                    {
                        value: 'none',
                        label: tr('Do not create tasks')
                    }
                ]
            )
        );
    if (model.document.searchType !== 'sthpw/task')
        out.push(
            {
                kind: 'Heading',
                id: 'processKindHeading',
                title: 'Node type',
                description:
                    tr(
                        'Choose how this stage behaves in the workflow and how it is drawn on the canvas:'
                    ) +
                    '\n• ' +
                    currentMeta.label +
                    ': ' +
                    currentMeta.description
            },
            {
                kind: 'ChoiceGrid',
                id: 'adminProcessKind',
                title: 'Node type',
                description: 'Choose the native behavior of this process.',
                options: (model.metadata.nodeTypes || []).map((value) => {
                    const meta = nodeTypeMeta(value, tr);
                    return {
                        value,
                        label: meta.label,
                        icon: meta.icon,
                        color: meta.color,
                        description: meta.description
                    };
                }),
                props: {
                    value: kind,
                    action: {
                        type: 'attribute',
                        key: 'type'
                    }
                }
            }
        );
    return out;
}
