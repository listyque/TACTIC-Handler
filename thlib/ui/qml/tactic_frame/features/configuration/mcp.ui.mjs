import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function initial() {
    return {
        connections: [],
        tools: [],
        selected: [],
        enabled: false,
        title: '',
        instructions: '',
        minutes: '60',
        busy: false,
        error: '',
        issued: ''
    };
}
export function agentLink(issued) {
    const connection = JSON.parse(issued);
    return (
        connection.url +
        '#access_token=' +
        encodeURIComponent(
            connection.headers.Authorization.replace(/^Bearer /, '')
        )
    );
}
export function edit(model, action) {
    if (action.type === 'field')
        return Object.assign({}, model, { [action.field]: action.value });
    if (action.type === 'tool')
        return Object.assign({}, model, {
            selected: action.value
                ? model.selected.concat(action.name)
                : model.selected.filter((name) => name !== action.name)
        });
    if (action.type === 'readonly')
        return Object.assign({}, model, {
            selected: model.tools
                .filter((tool) => tool.readonly)
                .map((tool) => tool.name)
        });
    if (action.type === 'clear')
        return Object.assign({}, model, { selected: [] });
    return model;
}
export function describe(model, width, height, language) {
    const tr = (value) => translate(value, language),
        inner = Math.max(0, width - 40);
    const nodes = [],
        content = [];
    let y = 0;
    function caption(id, text, extent = 28) {
        content.push(
            label(id, rect(0, y, inner, extent), text, { wrap: true })
        );
        y += extent + 8;
    }
    caption('mcpProject', tr('Project') + ': ' + (model.project || ''));
    caption(
        'mcpScope',
        tr(
            'External access is limited to this project and the tools you select. Revoke it at any time.'
        ),
        48
    );
    if (!model.enabled)
        caption(
            'mcpDisabled',
            tr(
                'Enable external MCP connections in Server configuration and restart first.'
            ),
            48
        );
    content.push(
        node('Field', 'mcpTitle', rect(0, y, inner, 40), {
            text: model.title,
            placeholder: tr('Connection name'),
            enabled: !model.busy,
            action: { type: 'field', field: 'title' }
        })
    );
    y += 48;
    content.push(
        node('Area', 'mcpInstructions', rect(0, y, inner, 112), {
            text: model.instructions,
            placeholder: tr('Instructions for this connection'),
            enabled: !model.busy,
            action: { type: 'field', field: 'instructions' }
        })
    );
    y += 120;
    content.push(
        node('Choice', 'mcpLifetime', rect(0, y, inner, 36), {
            value: model.minutes,
            enabled: !model.busy,
            options: [
                { value: '5', label: tr('5 minutes') },
                { value: '60', label: tr('1 hour') },
                { value: '480', label: tr('8 hours') }
            ],
            action: { type: 'field', field: 'minutes' }
        })
    );
    y += 44;
    caption('mcpToolsTitle', tr('Allowed tools'));
    content.push(
        button(
            'mcpReadTools',
            rect(0, y, Math.min(200, inner / 2), 32),
            tr('Select read tools'),
            'check',
            { type: 'readonly' },
            !model.busy
        )
    );
    content.push(
        button(
            'mcpClearTools',
            rect(Math.min(208, inner / 2), y, Math.min(120, inner / 2), 32),
            tr('Clear'),
            'close',
            { type: 'clear' },
            !model.busy
        )
    );
    y += 40;
    const toolRows = [];
    for (const [index, tool] of model.tools.entries()) {
        const toolY = index * 84;
        toolRows.push(
            node(
                'CheckBox',
                'mcpTool_' + index,
                rect(0, toolY, inner - 16, 32),
                {
                    label: tool.name,
                    checked: model.selected.includes(tool.name),
                    enabled: !model.busy,
                    action: { type: 'tool', name: tool.name }
                }
            )
        );
        toolRows.push(
            label(
                'mcpToolDescription_' + index,
                rect(28, toolY + 32, inner - 44, 44),
                tool.description,
                Object.assign({}, muted, { wrap: true })
            )
        );
    }
    const toolHeight = Math.min(252, model.tools.length * 84);
    content.push(
        node('Scroll', 'mcpToolList', rect(0, y, inner, toolHeight), {
            contentHeight: model.tools.length * 84,
            scrollbarId: 'mcpToolListBar',
            children: toolRows
        })
    );
    y += toolHeight + 12;
    if (model.issued) {
        caption(
            'mcpAgentLinkTitle',
            tr('Agent link — includes access and startup instructions'),
            48
        );
        content.push(
            node('Area', 'mcpAgentLink', rect(0, y, inner, 72), {
                text: agentLink(model.issued),
                readOnly: true
            })
        );
        y += 80;
        content.push(
            button(
                'mcpCopyAgentLink',
                rect(0, y, Math.min(260, inner), 32),
                tr('Copy agent link'),
                'link',
                { type: 'copy_link' },
                !model.busy
            )
        );
        y += 44;
        caption(
            'mcpIssuedTitle',
            tr(
                'Copy this connection now. The access token will not be shown again.'
            ),
            48
        );
        content.push(
            node('Area', 'mcpIssued', rect(0, y, inner, 180), {
                text: model.issued,
                readOnly: true
            })
        );
        y += 188;
        content.push(
            button(
                'mcpCopy',
                rect(0, y, Math.min(240, inner), 32),
                tr('Copy connection'),
                'content-copy',
                { type: 'copy' },
                !model.busy
            )
        );
        y += 48;
    }
    caption('mcpExistingTitle', tr('Existing connections'));
    for (const [index, item] of model.connections.entries()) {
        if (item.pending && !item.revoked && !item.expired) {
            content.push(
                button(
                    'mcpCollect_' + index,
                    rect(0, y, Math.min(240, inner), 32),
                    tr('Copy agent link'),
                    'key',
                    { type: 'reveal_link', id: item.id },
                    !model.busy
                )
            );
            y += 40;
        }
        caption(
            'mcpExisting_' + index,
            item.title +
                ' · ' +
                (item.revoked
                    ? tr('Revoked')
                    : item.expired
                      ? tr('Expired')
                      : item.expiresLabel)
        );
        content.push(
            button(
                'mcpRevoke_' + index,
                rect(0, y, Math.min(160, inner), 32),
                tr('Revoke access'),
                'block',
                { type: 'revoke', id: item.id },
                !model.busy && !item.revoked
            )
        );
        y += 44;
    }
    nodes.push(
        node(
            'Scroll',
            'mcpScroll',
            rect(12, 8, width - 24, Math.max(0, height - 108)),
            {
                contentHeight: y,
                scrollbarId: 'mcpScrollBar',
                children: content
            }
        )
    );
    if (model.error)
        nodes.push(
            label(
                'mcpError',
                rect(12, height - 96, width - 24, 44),
                tr(model.error),
                { wrap: true, color: 'error' }
            )
        );
    nodes.push(
        button(
            'mcpRefresh',
            rect(12, height - 44, 36, 32),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'mcpCreate',
            rect(
                Math.max(56, width - 240),
                height - 44,
                Math.min(228, width - 68),
                32
            ),
            tr('Create connection'),
            'add',
            { type: 'create' },
            !model.busy &&
                model.enabled &&
                !!model.title.trim() &&
                model.selected.length > 0,
            { highlighted: true }
        )
    );
    return { nodes };
}
