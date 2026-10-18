import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import { translate } from '../../core/strings.mjs';

export function layout(width, height, error) {
    const inset = 12,
        gap = 10,
        clientWidth = Math.min(250, Math.max(190, width * 0.27));
    const right = inset + clientWidth + gap,
        inner = Math.max(0, width - right - inset);
    return {
        clients: rect(inset + 10, 112, clientWidth - 20, height - 178),
        results: rect(right, 262, inner, height - 274 - (error ? 52 : 0)),
        timeout: rect(Math.max(right, width - 232), 100, 110, 38),
        right,
        inner,
        clientWidth
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        bounds = layout(width, height, model.error);
    const nodes = [
        node('Box', 'handlerBackground', rect(0, 0, width, height), {
            background: 'workspace'
        })
    ];
    nodes.push(
        node('Box', 'handlerIconSurface', rect(12, 12, 44, 44), {
            background: 'secondaryContainer',
            radius: 14,
            children: [
                node('Icon', 'handlerIcon', rect(11, 11, 22, 22), {
                    icon: 'hub',
                    color: 'action'
                })
            ]
        })
    );
    nodes.push(
        label(
            'handlerTitle',
            rect(66, 12, Math.max(0, width - 380), 22),
            tr('TACTIC Handler Server'),
            { fontRole: 'bodyLarge', weight: 600 }
        )
    );
    nodes.push(
        label(
            'handlerEndpoint',
            rect(66, 36, Math.max(0, width - 380), 20),
            tr('Local DCC command router') + ' · ' + model.endpoint,
            muted
        )
    );
    nodes.push(
        label(
            'handlerState',
            rect(width - 310, 18, 90, 32),
            tr(model.state).toUpperCase(),
            {
                color: model.state === 'running' ? 'green' : 'secondaryText',
                weight: 600
            }
        )
    );
    nodes.push(
        button(
            'handlerHelp',
            rect(width - 212, 15, 30, 30),
            tr('DCC clients help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'handlerStart',
            rect(width - 176, 12, 78, 38),
            tr('Start'),
            'play-arrow',
            { type: 'start' },
            model.state === 'stopped',
            { highlighted: true }
        )
    );
    nodes.push(
        button(
            'handlerStop',
            rect(width - 90, 12, 78, 38),
            tr('Stop'),
            'stop',
            { type: 'stop' },
            model.state !== 'stopped',
            { destructive: true }
        )
    );
    nodes.push(
        node(
            'Box',
            'handlerClientsSurface',
            rect(12, 76, bounds.clientWidth, height - 88),
            {
                background: 'panelDeep',
                radius: 14,
                border: 'outlineVariant',
                borderWidth: 1
            }
        )
    );
    nodes.push(
        label(
            'handlerClientsTitle',
            rect(22, 82, bounds.clientWidth - 60, 28),
            tr('CONNECTED CLIENTS'),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    nodes.push(
        button(
            'handlerDemo',
            rect(bounds.clientWidth - 28, 82, 30, 28),
            tr(
                model.demo
                    ? 'Stop simulated Maya client'
                    : 'Start simulated Maya client'
            ),
            model.demo ? 'stop' : 'deployed-code',
            { type: 'demo' },
            model.state === 'running',
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'handlerDisconnect',
            rect(22, height - 58, bounds.clientWidth - 20, 38),
            tr('Disconnect selected'),
            'link-off',
            { type: 'disconnect' },
            !!model.selectedClient,
            { destructive: true }
        )
    );
    nodes.push(
        label(
            'handlerCommandTitle',
            rect(bounds.right, 76, bounds.inner, 20),
            tr('COMMAND'),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    nodes.push(
        node(
            'Choice',
            'handlerCommand',
            rect(bounds.right, 100, Math.max(0, bounds.inner - 246), 38),
            {
                label: tr('Command'),
                value: model.command,
                options: model.capabilities.map((row) => ({
                    value: row.name,
                    label: row.name
                })),
                enabled:
                    model.state === 'running' && model.capabilities.length > 0,
                action: { type: 'command' }
            }
        )
    );
    nodes.push(
        node('View', 'handlerTimeout', bounds.timeout, { view: 'timeout' })
    );
    nodes.push(
        button(
            'handlerSend',
            rect(width - 112, 100, 100, 38),
            tr('Send'),
            'send',
            { type: 'send' },
            model.state === 'running' &&
                !!model.command &&
                !!model.selectedClient,
            { highlighted: true }
        )
    );
    nodes.push(
        node(
            'Area',
            'handlerPayload',
            rect(bounds.right, 148, bounds.inner, 72),
            {
                label: tr('JSON payload'),
                placeholder: tr('JSON payload'),
                text: model.payload,
                monospace: true,
                action: { type: 'payload' }
            }
        )
    );
    nodes.push(
        label(
            'handlerResultsTitle',
            rect(bounds.right, 230, bounds.inner - 40, 28),
            tr('RESULTS'),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    nodes.push(
        button(
            'handlerClear',
            rect(width - 42, 230, 30, 28),
            tr('Clear results'),
            'delete-sweep',
            { type: 'clear' },
            true,
            { iconOnly: true }
        )
    );
    if (model.error)
        nodes.push(
            label(
                'handlerError',
                rect(bounds.right, height - 64, bounds.inner, 52),
                model.error,
                { color: 'error', wrap: true }
            )
        );
    return { nodes };
}

export function clientRow(record, width, language) {
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            node('Action', 'handlerClientSurface', rect(0, 0, width, 70), {
                surface: true,
                selected: record.selected,
                rail: !!record.selected,
                action: { type: 'select', index: record.index },
                children: [
                    node('Icon', 'handlerClientIcon', rect(9, 10, 17, 17), {
                        icon:
                            record.applicationType === 'maya'
                                ? 'view-in-ar'
                                : 'description',
                        color: 'action'
                    }),
                    label(
                        'handlerClientName',
                        rect(32, 7, width - 90, 22),
                        record.clientId,
                        { weight: 600 }
                    ),
                    label(
                        'handlerClientSelected',
                        rect(width - 62, 6, 54, 15),
                        record.selected ? tr('ACTIVE') : '',
                        { color: 'action', fontRole: 'caption' }
                    ),
                    label(
                        'handlerClientPid',
                        rect(width - 72, 24, 64, 18),
                        'PID ' + record.processId,
                        Object.assign({}, muted, {
                            fontRole: 'caption',
                            align: 'right'
                        })
                    ),
                    label(
                        'handlerClientCapabilities',
                        rect(9, 46, width - 18, 18),
                        record.capabilityText,
                        Object.assign({}, muted, { fontRole: 'caption' })
                    )
                ]
            })
        ]
    };
}

export function resultHeight(record, width) {
    return (
        42 +
        captionHeight(record.summary || '', Math.max(1, width - 18)) +
        captionHeight(record.detail || '', Math.max(1, width - 18))
    );
}

export function resultRow(record, width, language) {
    const height = resultHeight(record, width),
        summaryHeight = captionHeight(
            record.summary || '',
            Math.max(1, width - 18)
        );
    return {
        nodes: [
            node('Box', 'handlerResultSurface', rect(0, 0, width, height), {
                surface: true,
                rail: ['error', 'completed'].includes(record.status),
                accent:
                    record.status === 'error'
                        ? 'red'
                        : record.status === 'completed'
                          ? 'green'
                          : 'action',
                children: [
                    label(
                        'handlerResultTimestamp',
                        rect(9, 7, 82, 20),
                        record.timestamp,
                        Object.assign({}, muted, {
                            fontRole: 'caption',
                            monospace: true
                        })
                    ),
                    label(
                        'handlerResultCommand',
                        rect(99, 7, width - 210, 20),
                        record.target + ' · ' + record.action,
                        { weight: 600 }
                    ),
                    label(
                        'handlerResultState',
                        rect(width - 104, 7, 95, 20),
                        translate(record.status, language).toUpperCase(),
                        {
                            fontRole: 'caption',
                            align: 'right',
                            color:
                                record.status === 'error'
                                    ? 'red'
                                    : record.status === 'completed'
                                      ? 'green'
                                      : 'secondaryText'
                        }
                    ),
                    label(
                        'handlerResultSummary',
                        rect(9, 30, width - 18, summaryHeight),
                        record.summary || '',
                        Object.assign({}, muted, { wrap: true })
                    ),
                    label(
                        'handlerResultDetail',
                        rect(
                            9,
                            34 + summaryHeight,
                            width - 18,
                            Math.max(0, height - 42 - summaryHeight)
                        ),
                        record.detail || '',
                        { fontRole: 'caption', monospace: true, wrap: true }
                    )
                ]
            })
        ]
    };
}
