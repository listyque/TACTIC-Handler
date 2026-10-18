import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export const messagesChange =
    'Adds the text column metadata to sthpw/message and sthpw/message_log. It stores conversation summaries, replies, reactions, pins, forwarding and delivery state.';
export const knowledgeChange =
    'Creates PROJECT/th_knowledge_article when it is missing, then adds kind, parent_code, content, content_text, sort_order, updated_by and linked_skeys.';
export const preservation =
    'Existing columns and data are kept. Nothing is deleted. The schema changes affect every user of this server and project.';

export function dialogSize(width, height) {
    return {
        width: Math.min(620, Math.max(300, width - 32)),
        height: Math.min(560, Math.max(300, height - 24))
    };
}

export function state(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, Math.min(520, width - 32)),
        left = (width - inner) / 2,
        top = Math.max(8, (height - 230) / 2);
    const nodes = [
        node('Box', 'collaborationStateSurface', rect(0, 0, width, height), {
            background: 'workspace'
        })
    ];
    nodes.push(
        node(
            'Icon',
            'collaborationStateIcon',
            rect(Math.max(0, (width - 32) / 2), top, 32, 32),
            {
                icon: model.busy ? 'hourglass-empty' : model.icon || 'database',
                color: 'action'
            }
        )
    );
    nodes.push(
        label(
            'collaborationStateTitle',
            rect(left, top + 43, inner, 48),
            tr(model.title || ''),
            { fontRole: 'title', weight: 600, align: 'center', wrap: true }
        )
    );
    const message =
        model.error ||
        (!model.canInitialize
            ? 'A TACTIC administrator must initialize these features once.'
            : model.message || '');
    nodes.push(
        label(
            'collaborationStateMessage',
            rect(left, top + 95, inner, 68),
            tr(message),
            {
                color: model.error ? 'error' : 'secondaryText',
                align: 'center',
                wrap: true,
                fontRole: 'caption'
            }
        )
    );
    nodes.push(
        button(
            'collaborationInitializeButton',
            rect(left, top + 175, inner, 38),
            tr('Initialize'),
            'add-circle',
            { type: 'open' },
            !model.busy,
            { visible: !!model.canInitialize, highlighted: true }
        )
    );
    if (model.canRefresh)
        nodes.push(
            button(
                'collaborationRefresh',
                rect(left, top + 220, inner, 32),
                tr('Refresh'),
                'refresh',
                { type: 'refresh' },
                !model.busy
            )
        );
    return { nodes };
}

export function confirmation(model, width, height, language) {
    const tr = (text) => translate(text, language),
        compact = width < 380,
        footer = compact ? 92 : 46,
        cardWidth = Math.max(0, width - 16),
        row = compact ? 170 : 120;
    const content = [];
    function card(id, title, body, y) {
        content.push(
            node('Box', id + 'Surface', rect(0, y, cardWidth, row), {
                background: 'surfaceContainer',
                border: 'outlineVariant',
                radius: 8
            })
        );
        content.push(
            label(
                id + 'Title',
                rect(12, y + 10, Math.max(0, cardWidth - 24), 24),
                title,
                { weight: 600 }
            )
        );
        content.push(
            label(
                id,
                rect(12, y + 39, Math.max(0, cardWidth - 24), row - 49),
                tr(body),
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    wrap: true,
                    elide: false
                }
            )
        );
    }
    card('collaborationMessagesChange', tr('Messages'), messagesChange, 0);
    card(
        'collaborationKnowledgeChange',
        tr('Knowledge Base') + ' · ' + (model.project || tr('current project')),
        knowledgeChange,
        row + 10
    );
    content.push(
        label(
            'collaborationPreservationNotice',
            rect(0, 2 * row + 20, cardWidth, 110),
            tr(preservation),
            {
                fontRole: 'caption',
                color: 'secondaryText',
                wrap: true,
                elide: false
            }
        )
    );
    const nodes = [
        node(
            'Scroll',
            'collaborationInitializationDetails',
            rect(0, 0, width, Math.max(0, height - footer)),
            {
                contentHeight: 2 * row + 140,
                resetKey: model.epoch || 0,
                scrollbarId: 'collaborationInitializationScrollBar',
                children: content
            }
        )
    ];
    const y = Math.max(0, height - footer + 8),
        size = compact ? width : Math.max(0, (width - 8) / 2);
    nodes.push(
        button(
            'collaborationInitializationCancel',
            rect(0, y, size, 38),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'collaborationInitializationConfirm',
            rect(compact ? 0 : size + 8, compact ? y + 46 : y, size, 38),
            tr('Initialize'),
            'add-circle',
            { type: 'initialize' },
            !model.busy,
            { highlighted: true }
        )
    );
    return { nodes };
}
