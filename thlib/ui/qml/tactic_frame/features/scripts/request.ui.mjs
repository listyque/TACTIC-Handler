import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function initial(context = {}) {
    return {
        context,
        prompt: '',
        allowChanges: false,
        hosts: [],
        requests: [],
        selected: '',
        request: {},
        busy: false,
        error: '',
        pending: null
    };
}

export function active(model) {
    return ['queued', 'running', 'cancelling'].includes(model.request?.status);
}

export function canSend(model) {
    return (
        !model.busy &&
        !model.selected &&
        !!model.context?.project &&
        !!model.prompt.trim() &&
        model.prompt.length <= 12000 &&
        !!model.hosts.length &&
        (!model.allowChanges ||
            model.hosts.some((host) => host.capabilities.changes))
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const inset = 8,
        gap = 8,
        inner = Math.max(0, width - inset * 2);
    const current = model.request || {},
        context = current.document?.context || model.context || {};
    const statusText = (value) =>
        tr(
            {
                queued: 'Request queued',
                running: 'Agent working',
                cancelling: 'Request cancelling',
                cancelled: 'Request cancelled',
                completed: 'Request completed',
                failed: 'Request failed',
                interrupted: 'Request interrupted'
            }[value] || value
        );
    const status =
        model.error ||
        (model.busy
            ? tr('Loading…')
            : current.status
              ? statusText(current.status)
              : model.hosts.length
                ? tr('External agent connected') +
                  ': ' +
                  model.hosts.map((host) => host.label).join(', ')
                : tr('External agent is offline'));
    const contextText = [
        context.client,
        context.project,
        context.title || context.page,
        context.search_type,
        context.view,
        ...(context.search_keys || [])
    ]
        .filter(Boolean)
        .join('\n');
    const output = [
        model.error ? tr(model.error) : '',
        current.error ? tr(current.error) : '',
        ...(current.events || [])
            .filter((value) => value !== current.answer)
            .map((value) => tr(value)),
        current.answer || ''
    ]
        .filter(Boolean)
        .join('\n\n');
    const actionsTop = 326,
        outputTop = actionsTop + 44;
    return {
        nodes: [
            node(
                'Choice',
                'agentRequestHistory',
                rect(inset, 8, Math.max(0, inner - 88), 36),
                {
                    label: tr('Agent requests'),
                    value: model.selected,
                    enabled: !model.busy,
                    options: [
                        { value: '', label: tr('New request') },
                        ...(model.requests || []).map((row) => ({
                            value: row.request_id,
                            label: statusText(row.status) + ' · ' + row.prompt
                        }))
                    ],
                    action: { type: 'select' }
                }
            ),
            button(
                'agentRequestNew',
                rect(width - inset - 80, 8, 36, 36),
                tr('New request'),
                'add',
                { type: 'select', value: '' },
                !model.busy,
                { iconOnly: true }
            ),
            button(
                'agentRequestRefresh',
                rect(width - inset - 36, 8, 36, 36),
                tr('Refresh'),
                'refresh',
                { type: 'refresh' },
                !model.busy,
                { iconOnly: true }
            ),
            label(
                'agentRequestStatus',
                rect(inset, 48, inner, 28),
                status,
                muted
            ),
            node('Area', 'agentRequestContext', rect(inset, 80, inner, 100), {
                label: tr('Context sent to the agent'),
                text: contextText,
                readOnly: true,
                enabled: true
            }),
            node('Area', 'agentRequestPrompt', rect(inset, 188, inner, 96), {
                label: tr('What should the agent do?'),
                text: current.document?.prompt || model.prompt,
                readOnly: !!model.selected || !!model.pending,
                enabled: !model.busy,
                action: { type: 'prompt' }
            }),
            node(
                'CheckBox',
                'agentRequestChanges',
                rect(inset, 290, inner, 30),
                {
                    text: tr('Allow the requested configuration changes'),
                    wrapText: true,
                    checked:
                        current.document?.allow_changes ?? model.allowChanges,
                    enabled: !model.busy && !model.selected && !model.pending,
                    action: { type: 'changes' }
                }
            ),
            button(
                'agentRequestSend',
                rect(inset, actionsTop, Math.min(220, (inner - gap) / 2), 36),
                tr('Send to agent'),
                'send',
                { type: 'send' },
                canSend(model)
            ),
            button(
                'agentRequestCancel',
                rect(
                    inset + Math.min(220, (inner - gap) / 2) + gap,
                    actionsTop,
                    Math.min(200, (inner - gap) / 2),
                    36
                ),
                tr('Cancel request'),
                'close',
                { type: 'cancel' },
                !model.busy && active(model) && current.status !== 'cancelling'
            ),
            node(
                'Area',
                'agentRequestOutput',
                rect(
                    inset,
                    outputTop,
                    inner,
                    Math.max(80, height - outputTop - 42)
                ),
                {
                    label: tr('Agent progress and answer'),
                    text:
                        output ||
                        tr(
                            'The answer and operation results will appear here.'
                        ),
                    readOnly: true,
                    enabled: true
                }
            ),
            label(
                'agentRequestBoundary',
                rect(inset, height - 34, inner, 28),
                tr(
                    'Script activation remains a separate action in the Script Editor.'
                ),
                Object.assign({}, muted, { wrap: true })
            )
        ]
    };
}
