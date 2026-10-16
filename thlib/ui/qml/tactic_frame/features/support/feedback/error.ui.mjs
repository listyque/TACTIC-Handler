import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

const errorTypes = {
    ticket_error: 'Authentication error',
    connection_timeout: 'Connection timeout',
    connection_refused: 'Connection refused',
    login_pass_error: 'Authentication error',
    sql_connection_error: 'Database connection error',
    database_query_error: 'Database query error',
    protocol_error: 'Protocol error',
    server_error: 'Server error',
    no_project_error: 'Project error',
    attribute_error: 'Attribute error',
    type_error: 'Type error',
    value_error: 'Value error',
    key_error: 'Missing data',
    index_error: 'Index error',
    file_not_found_error: 'File not found',
    permission_error: 'Permission error',
    import_error: 'Import error',
    runtime_error: 'Runtime error',
    assertion_error: 'Assertion error',
    os_error: 'Operating system error',
    qml_error: 'Interface error'
};
const connectionMessages = {
    connection_timeout:
        'The TACTIC server is unreachable or did not respond in time. Check the server address, network connection, VPN or proxy, and make sure the server is running. Then try again.',
    connection_refused:
        'A connection to the TACTIC server could not be established. Check the server address, network connection, VPN or proxy, and make sure the server is running. Then try again.'
};

export function primaryAction(type) {
    if (['ticket_error', 'login_pass_error'].includes(type)) return 'Sign In';
    return [
        'connection_refused',
        'connection_timeout',
        'sql_connection_error',
        'protocol_error',
        'no_project_error'
    ].includes(type)
        ? 'Configuration'
        : '';
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 600,
        margin = compact ? 12 : 24,
        inner = width - margin * 2;
    const actions = [
        ['openErrorDebugLog', 'Open Debug Log', 'debug'],
        ['errorHelp', 'Help', 'help']
    ];
    const primary = primaryAction(model.errorType);
    if (primary && model.canConfigure)
        actions.push(['errorPrimary', primary, 'primary']);
    actions.push(['dismissError', 'Dismiss', 'dismiss']);
    if (model.canRetry) actions.push(['retryError', 'Retry', 'retry']);
    const columns = compact ? 2 : actions.length,
        gap = 8,
        cell = (inner - (columns - 1) * gap) / columns;
    const footerHeight = Math.ceil(actions.length / columns) * 46 + 20,
        bodyHeight = Math.max(0, height - 86 - footerHeight);
    const nodes = [
        node('Box', 'errorHeading', rect(0, 0, width, 86), {
            background: 'panelRaised',
            children: [
                node('Icon', 'errorIcon', rect(margin, 24, 32, 32), {
                    icon: 'error',
                    color: 'red'
                }),
                label(
                    'errorTitle',
                    rect(margin + 48, 13, inner - 48, 30),
                    text(model.title || 'Application error'),
                    { fontRole: 'heading', weight: 600 }
                ),
                label(
                    'errorType',
                    rect(margin + 48, 49, inner - 48, 24),
                    text(
                        errorTypes[model.errorType] ||
                            model.kind ||
                            'Application error'
                    ),
                    { fontRole: 'caption', weight: 600, color: 'red' }
                )
            ]
        })
    ];
    const message = text(
        connectionMessages[model.errorType] || model.message || ''
    );
    const messageHeight = Math.min(
        260,
        Math.max(
            84,
            (message.split('\n').length +
                Math.ceil(message.length / Math.max(20, inner / 7))) *
                18
        )
    );
    const body = [
        node('Area', 'errorMessage', rect(margin, 16, inner, messageHeight), {
            text: message,
            label: text('Message'),
            readOnly: true,
            enabled: true
        })
    ];
    let y = messageHeight + 30;
    body.push(
        node(
            'View',
            'errorRequestBlocks',
            rect(margin, y, inner, model.requestHeight || 0),
            { view: 'requests' }
        )
    );
    if (model.requestHeight) y += model.requestHeight + 14;
    if (model.stacktrace) {
        body.push(
            button(
                'toggleErrorStacktrace',
                rect(margin, y, (inner - gap) / 2, 36),
                text(model.expanded ? 'Hide stacktrace' : 'Show stacktrace'),
                '',
                { type: 'expand' },
                true
            )
        );
        body.push(
            button(
                'copyErrorStacktrace',
                rect(margin + (inner + gap) / 2, y, (inner - gap) / 2, 36),
                text('Copy stacktrace'),
                'content-copy',
                { type: 'copyStacktrace' },
                true
            )
        );
        y += 48;
        if (model.expanded) {
            body.push(
                node('Area', 'errorStacktrace', rect(margin, y, inner, 320), {
                    text: model.stacktrace,
                    label: text('Stacktrace'),
                    readOnly: true,
                    enabled: true,
                    monospace: true,
                    wrap: false
                })
            );
            y += 334;
        }
    }
    if (model.status) {
        body.push(
            label(
                'errorStatus',
                rect(margin, y, inner, 44),
                text(model.status),
                Object.assign({}, muted, { wrap: true, role: 'status' })
            )
        );
        y += 50;
    }
    nodes.push(
        node('Scroll', 'errorBodyFlickable', rect(0, 86, width, bodyHeight), {
            contentHeight: Math.max(bodyHeight, y),
            children: body,
            scrollbarId: 'errorBodyScrollBar'
        })
    );
    nodes.push(
        node(
            'Box',
            'errorFooter',
            rect(0, height - footerHeight, width, footerHeight),
            {
                background: 'panelRaised',
                children: actions.map(([id, name, type], index) =>
                    button(
                        id,
                        rect(
                            margin + (index % columns) * (cell + gap),
                            10 + Math.floor(index / columns) * 46,
                            cell,
                            38
                        ),
                        text(name),
                        '',
                        { type },
                        !model.busy,
                        { highlighted: type === 'retry' }
                    )
                )
            }
        )
    );
    return { nodes };
}
