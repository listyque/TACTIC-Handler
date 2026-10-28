import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { controls } from '../../core/foundation.mjs';

export function initial() {
    return {
        connections: [],
        tools: [],
        selected: [],
        enabled: false,
        unlimited_lifetime: false,
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
    if (action.type === 'all')
        return Object.assign({}, model, {
            selected: model.tools.map((tool) => tool.name)
        });
    if (action.type === 'clear')
        return Object.assign({}, model, { selected: [] });
    return model;
}
export function describe(model, width, height, language) {
    const tr = (value) => translate(value, language),
        inner = Math.max(0, width - 24 - controls.scrollBar.extent - 8),
        lifetimeWidth = inner >= 560 ? 152 : inner,
        fieldWidth = inner >= 560 ? inner - lifetimeWidth - 12 : inner;
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
        40
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
        node('Field', 'mcpTitle', rect(0, y, fieldWidth, 36), {
            text: model.title,
            label: tr('Connection name'),
            placeholder: tr('Connection name'),
            enabled: !model.busy,
            action: { type: 'field', field: 'title' }
        })
    );
    content.push(
        node(
            'Choice',
            'mcpLifetime',
            rect(
                inner >= 560 ? fieldWidth + 12 : 0,
                inner >= 560 ? y : y + 44,
                lifetimeWidth,
                36
            ),
            {
                value: model.minutes,
                enabled: !model.busy,
                options: [
                    { value: '5', label: tr('5 minutes') },
                    { value: '60', label: tr('1 hour') },
                    { value: '480', label: tr('8 hours') }
                ].concat(
                    model.unlimited_lifetime
                        ? [{ value: '0', label: tr('No expiration') }]
                        : []
                ),
                action: { type: 'field', field: 'minutes' }
            }
        )
    );
    y += inner >= 560 ? 44 : 88;
    content.push(
        node('Area', 'mcpInstructions', rect(0, y, inner, 72), {
            text: model.instructions,
            placeholder: tr('Instructions for this connection'),
            enabled: !model.busy,
            action: { type: 'field', field: 'instructions' }
        })
    );
    y += 84;
    caption(
        'mcpToolsTitle',
        tr('Allowed tools') +
            ' · ' +
            model.selected.length +
            '/' +
            model.tools.length
    );
    let left = 0;
    for (const [id, text, type, icon, preferred] of [
        ['mcpAllTools', 'Select all tools', 'all', 'check', 164],
        ['mcpReadTools', 'Select read tools', 'readonly', 'check', 200],
        ['mcpClearTools', 'Clear', 'clear', 'close', 96]
    ]) {
        const extent = Math.min(preferred, inner);
        if (left && left + extent > inner) {
            left = 0;
            y += 40;
        }
        content.push(
            button(
                id,
                rect(left, y, extent, 32),
                tr(text),
                icon,
                { type },
                !model.busy
            )
        );
        left += extent + 8;
    }
    y += 40;
    const toolRows = [],
        rowHeight = inner < 480 ? 88 : 68;
    for (const [index, tool] of model.tools.entries()) {
        const toolY = index * rowHeight,
            rowWidth = inner - 8 - controls.scrollBar.extent - 4,
            nameWidth = Math.max(0, rowWidth - (inner < 480 ? 56 : 164));
        if (index)
            toolRows.push(
                node(
                    'Box',
                    'mcpToolDivider_' + index,
                    rect(12, toolY, rowWidth - 24, 1),
                    { background: 'outline' }
                )
            );
        toolRows.push(
            node(
                'CheckBox',
                'mcpTool_' + index,
                rect(0, toolY, rowWidth, rowHeight),
                {
                    label:
                        (tool.title || tool.name) +
                        ' · ' +
                        tr(tool.readonly ? 'Read only' : 'Write'),
                    text: tool.title || tool.name,
                    description: tool.description,
                    indicatorX: 12,
                    selectedColor: 'contentSelection',
                    checked: model.selected.includes(tool.name),
                    enabled: !model.busy,
                    action: { type: 'tool', name: tool.name },
                    children: [
                        label(
                            'mcpToolName_' + index,
                            rect(44, 8, nameWidth, 22),
                            tool.title || tool.name,
                            { weight: 600 }
                        ),
                        label(
                            'mcpToolAccess_' + index,
                            rect(
                                inner < 480 ? 44 : rowWidth - 112,
                                inner < 480 ? 28 : 8,
                                inner < 480 ? rowWidth - 56 : 100,
                                22
                            ),
                            tr(tool.readonly ? 'Read only' : 'Write'),
                            Object.assign({}, muted, {
                                align: inner < 480 ? 'left' : 'right',
                                color: tool.readonly
                                    ? 'secondaryText'
                                    : 'contentAccent'
                            })
                        ),
                        label(
                            'mcpToolDescription_' + index,
                            rect(44, inner < 480 ? 52 : 32, rowWidth - 56, 30),
                            tool.description,
                            Object.assign({}, muted, {
                                wrap: true,
                                maxLines: 2
                            })
                        )
                    ]
                }
            )
        );
    }
    const toolHeight = Math.min(
        Math.max(160, height - y - 88),
        340,
        model.tools.length * rowHeight
    );
    content.push(
        node('Box', 'mcpToolSurface', rect(0, y, inner, toolHeight + 8), {
            background: 'panel',
            border: 'outline',
            radius: 4,
            children: [
                node(
                    'Scroll',
                    'mcpToolList',
                    rect(4, 4, inner - 8, toolHeight),
                    {
                        contentHeight: model.tools.length * rowHeight,
                        scrollbarId: 'mcpToolListBar',
                        children: toolRows
                    }
                )
            ]
        })
    );
    y += toolHeight + 20;
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
                      : item.expires == null
                        ? tr('No expiration')
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
            rect(
                12,
                8,
                width - 24,
                Math.max(0, height - (model.error ? 108 : 64))
            ),
            {
                contentHeight: y,
                scrollbarId: 'mcpScrollBar',
                children: content
            }
        )
    );
    nodes.push(
        node('Box', 'mcpFooterDivider', rect(12, height - 56, width - 24, 1), {
            background: 'outline'
        })
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
