import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = {
    inset: 12,
    bubblePadding: 14,
    messageGap: 16,
    attachmentHeight: 28
};
export function initial(context = {}) {
    return {
        context,
        prompt: '',
        allowChanges: false,
        allowWeb: false,
        hosts: [],
        requests: [],
        selected: '',
        request: {},
        busy: false,
        error: '',
        pending: null,
        attachments: [],
        uploading: false,
        model: null,
        effort: null,
        contextExpanded: false
    };
}
export function active(model) {
    return ['queued', 'running', 'cancelling'].includes(model.request?.status);
}
export function host(model) {
    const allowed = model.hosts.filter(
        (item) =>
            !(model.request?.document?.allow_changes ?? model.allowChanges) ||
            item.capabilities.changes
    );
    return (
        allowed.find((item) => item.host_id === model.request?.host_id) ||
        allowed[0]
    );
}
export function canSend(model) {
    const connected = host(model);
    return (
        !model.busy &&
        !model.uploading &&
        !!model.context?.project &&
        (!!model.prompt.trim() || !!model.attachments.length) &&
        model.prompt.length <= 12000 &&
        !!connected &&
        (!model.allowChanges || connected.capabilities.changes) &&
        (!model.selected || model.request.status !== 'cancelling') &&
        (!active(model) || connected.capabilities.steering === true)
    );
}
export function selectedModel(model) {
    const id = model.model ?? model.request?.model ?? '';
    return host(model)?.capabilities.models?.find((item) =>
        id ? item.id === id : item.is_default
    );
}
export function messages(model) {
    const current = model.request || {};
    const rows = current.messages?.length
        ? current.messages
        : current.document
          ? [
                {
                    id: current.request_id,
                    role: 'user',
                    text: current.document.prompt,
                    attachments: []
                },
                ...(current.answer
                    ? [
                          {
                              id: 'answer',
                              role: 'assistant',
                              text: current.answer,
                              attachments: []
                          }
                      ]
                    : [])
            ]
          : [];
    return rows.concat(
        current.output && active(model)
            ? [
                  {
                      id: 'progress',
                      role: 'assistant',
                      text: current.output,
                      attachments: []
                  }
              ]
            : []
    );
}
export function activity(model, language) {
    const names = {
        agent_context: 'Reading conversation context',
        agent_capabilities: 'Checking available tools',
        reference_read: 'Reading TACTIC documentation',
        agent_selection: 'Reading selected objects',
        ts_records: 'Reading project objects',
        ts_snapshots: 'Reading file history',
        ts_workflow_read: 'Reading workflows',
        ts_workflow_apply: 'Saving workflow',
        ts_attachment_checkin: 'Checking in attached files',
        ts_edit_operation: 'Checking saved changes',
        ts_naming_read: 'Reading naming rules',
        ts_naming_preview: 'Checking file naming',
        agent_attachment_image: 'Viewing attached image',
        agent_web_download: 'Downloading reference file',
        webSearch: 'Searching the web'
    };
    const events = model.request?.events || [];
    return events
        .slice(events.lastIndexOf('External agent started') + 1)
        .map((event) => {
            const match = event.match(
                /^([a-zA-Z_]+): (inProgress|completed|failed)$/
            );
            if (!match) return event;
            const label = translate(names[match[1]] || match[1], language);
            return (
                label +
                ' · ' +
                translate(
                    {
                        inProgress: 'Working',
                        completed: 'Done',
                        failed: 'Failed'
                    }[match[2]],
                    language
                )
            );
        });
}
export function safeMarkdown(text) {
    return String(text || '')
        .replace(/<[^>]*>/g, (value) =>
            value.replace(/</g, '&lt;').replace(/>/g, '&gt;')
        )
        .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
        .replace(/!\[/g, '[');
}
export function messageGeometry(width, role, bodyHeight, attachments) {
    const inner = Math.min(800, Math.max(0, width - 32)),
        bubbleWidth = Math.min(role === 'user' ? 640 : 800, inner);
    const padding = role === 'user' ? metrics.bubblePadding : 0;
    return {
        x: (width - inner) / 2 + (role === 'user' ? inner - bubbleWidth : 0),
        width: bubbleWidth,
        padding,
        height:
            padding * 2 +
            Math.max(20, bodyHeight) +
            (Array.isArray(attachments)
                ? attachments.reduce(
                      (height, file) => height + attachmentHeight(file),
                      0
                  )
                : attachments * metrics.attachmentHeight)
    };
}
export function attachmentHeight(file) {
    return /^image\/(png|jpeg|webp|gif)$/.test(file.media_type || '')
        ? 172
        : metrics.attachmentHeight;
}

export function contextItems(context, language) {
    const tr = (text) => translate(text, language);
    return [
        { value: context.project || '', icon: 'folder' },
        { value: context.title || context.page || '', icon: 'table' },
        { value: context.search_type || '', icon: 'database' },
        {
            value:
                tr('Selected objects') +
                ': ' +
                (context.search_keys || []).length,
            icon: 'check'
        }
    ]
        .filter((item) => item.value)
        .map((item) =>
            Object.assign({}, item, {
                width: Math.min(220, Math.max(80, item.value.length * 7 + 40))
            })
        );
}
export function status(model, language) {
    const tr = (text) => translate(text, language),
        current = model.request || {};
    if (model.error || current.error)
        return {
            text: tr(model.error || current.error),
            color: 'error',
            icon: 'error'
        };
    if (current.status === 'completed')
        return current.outcome === 'needs_input'
            ? {
                  text: tr('Waiting for your reply'),
                  color: 'action',
                  icon: 'help'
              }
            : current.outcome === 'blocked'
              ? {
                    text: tr('Task blocked — see the answer'),
                    color: 'error',
                    icon: 'warning'
                }
              : {
                    text: tr(
                        current.outcome === 'completed'
                            ? 'Task completed'
                            : 'Agent finished — review the answer'
                    ),
                    color: 'green',
                    icon: 'check'
                };
    const texts = {
        queued: 'Request queued',
        running: 'Agent working',
        cancelling: 'Request cancelling',
        cancelled: 'Request cancelled',
        failed: 'Request failed',
        interrupted: 'Request interrupted'
    };
    return {
        text: tr(
            texts[current.status] ||
                (model.hosts.length
                    ? 'External agent connected'
                    : 'External agent is offline')
        ),
        color: 'secondaryText',
        icon: active(model) ? 'sync' : 'chat'
    };
}
export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        current = model.request || {},
        context = current.document?.context || model.context || {};
    const inset = metrics.inset,
        inner = Math.max(0, width - inset * 2),
        narrow = width < 640,
        connected = host(model);
    const composerWidth = Math.min(880, inner),
        composerX = (width - composerWidth) / 2;
    const contextHeight = model.contextExpanded ? 122 : 38;
    const composerHeight =
        188 +
        contextHeight +
        (model.attachments.length ? 42 : 0) +
        (narrow ? 40 : 0);
    const composerTop = Math.max(180, height - composerHeight - 12),
        modelWidth = narrow ? Math.max(80, (composerWidth - 32) / 2) : 200;
    const state = status(model, language),
        working = active(model),
        sendVisible =
            !working || !!model.prompt.trim() || !!model.attachments.length;
    const nodes = [
        node(
            'Choice',
            'agentRequestHistory',
            rect(inset, 10, Math.max(70, inner - 88), 32),
            {
                label: tr('Agent requests'),
                value: model.selected,
                enabled: !model.busy && !model.uploading,
                options: [
                    { value: '', label: tr('New conversation') },
                    ...(model.requests || []).map((row) => ({
                        value: row.request_id,
                        label:
                            row.prompt === 'Attachments'
                                ? tr('Attachments')
                                : row.prompt
                    }))
                ],
                action: { type: 'select' }
            }
        ),
        button(
            'agentRequestNew',
            rect(width - inset - 72, 10, 32, 32),
            tr('New conversation'),
            'add',
            { type: 'select', value: '' },
            !model.busy && !model.uploading,
            { iconOnly: true }
        ),
        button(
            'agentRequestRefresh',
            rect(width - inset - 32, 10, 32, 32),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy && !model.uploading,
            { iconOnly: true }
        ),
        node('Icon', 'agentRequestStatusIcon', rect(inset, 52, 18, 18), {
            icon: state.icon,
            color: state.color
        }),
        label(
            'agentRequestStatus',
            rect(
                inset + 26,
                50,
                Math.max(0, inner - 26 - (current.undo_operation ? 142 : 0)),
                24
            ),
            state.text,
            Object.assign({}, muted, { color: state.color, role: 'alert' })
        ),
        node(
            'View',
            'agentRequestOutput',
            rect(0, 84, width, Math.max(70, composerTop - 96)),
            {
                view: 'transcript',
                messages: messages(model),
                events: activity(model, language),
                active: working
            }
        ),
        node(
            'Box',
            'agentComposerSurface',
            rect(
                composerX,
                composerTop,
                composerWidth,
                height - composerTop - 12
            ),
            {
                background: 'surfaceContainerHigh',
                border: 'outlineVariant',
                borderWidth: 1,
                radius: 20
            }
        ),
        node(
            'View',
            'agentRequestContext',
            rect(
                composerX + 12,
                composerTop + 10,
                Math.max(0, composerWidth - 24),
                contextHeight
            ),
            { view: 'context', context, expanded: model.contextExpanded }
        ),
        node(
            'Area',
            'agentRequestPrompt',
            rect(
                composerX + 10,
                composerTop + contextHeight + 18,
                Math.max(0, composerWidth - 20),
                64
            ),
            {
                label: tr(
                    working
                        ? 'Add a correction while the agent works'
                        : 'What should the agent do?'
                ),
                placeholder: tr(
                    working
                        ? 'Add a correction while the agent works'
                        : 'Describe the task. Attach files or paste an image.'
                ),
                text: model.prompt,
                flat: true,
                readOnly: !!model.pending,
                enabled: !model.busy,
                sendOnEnter: true,
                sendAction: { type: 'send' },
                action: { type: 'prompt' }
            }
        ),
        node(
            'CheckBox',
            'agentRequestChanges',
            rect(
                composerX + 16,
                height - 114 - (narrow ? 40 : 0),
                Math.max(0, composerWidth - 32),
                26
            ),
            {
                text: tr('Allow requested changes'),
                wrapText: true,
                checked: current.document?.allow_changes ?? model.allowChanges,
                enabled: !model.busy && !model.selected && !model.pending,
                action: { type: 'changes' }
            }
        ),
        node(
            'CheckBox',
            'agentRequestWeb',
            rect(
                composerX + 16,
                height - 84 - (narrow ? 40 : 0),
                Math.max(0, composerWidth - 32),
                26
            ),
            {
                text: tr('Allow internet access'),
                checked: current.document?.allow_web ?? model.allowWeb,
                enabled:
                    !model.busy &&
                    !model.selected &&
                    !model.pending &&
                    !!connected?.capabilities.web_search,
                action: { type: 'web' }
            }
        ),
        button(
            'agentRequestAttach',
            rect(composerX + 12, height - 52, 32, 32),
            tr('Attach files'),
            'add',
            { type: 'attach' },
            !model.uploading && !model.pending && !model.busy,
            { iconOnly: true }
        ),
        button(
            'agentRequestPaste',
            rect(composerX + 50, height - 52, 32, 32),
            tr('Paste attachment'),
            'content-paste',
            { type: 'paste' },
            !model.uploading && !model.pending && !model.busy,
            { iconOnly: true }
        )
    ];
    if (sendVisible)
        nodes.push(
            button(
                'agentRequestSend',
                rect(
                    composerX + composerWidth - 44 - (working ? 40 : 0),
                    height - 52,
                    32,
                    32
                ),
                tr(working ? 'Send correction' : 'Send to agent'),
                'arrow-upward',
                { type: 'send' },
                canSend(model),
                { iconOnly: true, highlighted: true }
            )
        );
    if (working)
        nodes.push(
            button(
                'agentRequestCancel',
                rect(composerX + composerWidth - 44, height - 52, 32, 32),
                tr('Cancel request'),
                'stop',
                { type: 'cancel' },
                !model.busy && current.status !== 'cancelling',
                { iconOnly: true }
            )
        );
    if (connected?.capabilities.models?.length)
        nodes.push(
            node(
                'Choice',
                'agentRequestModel',
                rect(
                    narrow
                        ? composerX + 12
                        : composerX +
                              composerWidth -
                              modelWidth -
                              52 -
                              (narrow ? 0 : 144) -
                              (working && sendVisible ? 40 : 0),
                    height - (narrow ? 92 : 52),
                    modelWidth,
                    32
                ),
                {
                    label: tr('Model'),
                    value: model.model ?? current.model ?? '',
                    enabled: !model.busy && !working && !model.pending,
                    options: [
                        { value: '', label: tr('Agent default') },
                        ...connected.capabilities.models.map((item) => ({
                            value: item.id,
                            label: item.label
                        }))
                    ],
                    action: { type: 'model' }
                }
            )
        );
    const efforts = selectedModel(model)?.efforts || [];
    if (efforts.length)
        nodes.push(
            node(
                'Choice',
                'agentRequestEffort',
                rect(
                    narrow
                        ? composerX + 20 + modelWidth
                        : composerX +
                              composerWidth -
                              188 -
                              (working && sendVisible ? 40 : 0),
                    height - (narrow ? 92 : 52),
                    narrow ? modelWidth : 136,
                    32
                ),
                {
                    label: tr('Reasoning effort'),
                    value: model.effort ?? current.effort ?? '',
                    enabled: !model.busy && !working && !model.pending,
                    options: [
                        { value: '', label: tr('Agent default') },
                        ...efforts.map((value) => ({
                            value,
                            label: tr(
                                {
                                    none: 'None',
                                    minimal: 'Minimal',
                                    low: 'Low',
                                    medium: 'Medium',
                                    high: 'High',
                                    xhigh: 'Extra high',
                                    max: 'Maximum',
                                    ultra: 'Ultra'
                                }[value] || value
                            )
                        }))
                    ],
                    action: { type: 'effort' }
                }
            )
        );
    if (model.attachments.length)
        nodes.push(
            node(
                'View',
                'agentRequestAttachments',
                rect(
                    composerX + 12,
                    height - 156 - (narrow ? 40 : 0),
                    composerWidth - 24,
                    36
                ),
                { view: 'attachments', files: model.attachments }
            )
        );
    if (current.undo_operation)
        nodes.push(
            button(
                'agentRequestUndo',
                rect(width - inset - 134, 50, 134, 26),
                tr('Undo field change'),
                'undo',
                { type: 'undo' },
                !working && !model.busy && !model.uploading
            )
        );
    return { nodes };
}
