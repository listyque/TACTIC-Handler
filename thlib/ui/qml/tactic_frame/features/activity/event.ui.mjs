import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { metrics } from '../../core/foundation.mjs';

export function icon(model) {
    return model.relationAction
        ? 'link'
        : {
              publication: 'snapshot',
              note: 'notes',
              task: 'task',
              work_hour: 'schedule',
              status: 'system-activity',
              create: 'add',
              delete: 'delete',
              change: 'edit'
          }[model.kind] || 'activity-feed';
}
export function accent(model) {
    return (
        model.processColor ||
        model.typeColor ||
        { publication: 'green', work_hour: 'cyan', task: 'yellow' }[
            model.kind
        ] ||
        'action'
    );
}
export function geometry(width, style = 'md3') {
    const avatar = width < 380 ? 34 : 40,
        gap = metrics(style).communicationAvatarSpacing;
    const bubble = Math.max(0, Math.min(760, width - avatar - gap - 8));
    return {
        avatar,
        bubble,
        x: 4 + avatar + gap,
        inner: Math.max(0, bubble - 20)
    };
}
export function card(model, width, heights = {}, language, style = 'md3') {
    const tr = (text) => translate(text, language),
        g = geometry(width, style),
        compact = g.bubble < 520,
        timeWidth = Math.min(140, g.inner * 0.35),
        headerHeight = compact ? 33 : 16,
        nodes = [],
        sentenceHeight = Math.max(18, heights.sentence || 18),
        color = accent(model);
    let y = 4 + 10 + headerHeight + 6;
    const content = [
        label(
            'activityActorLabel',
            rect(
                10,
                10,
                compact ? g.inner : Math.max(0, g.inner - timeWidth - 8),
                16
            ),
            model.serverGenerated
                ? tr('Server trigger')
                : model.actorLabel || model.actor || tr('Unknown user'),
            { fontRole: 'secondary', weight: 600, color: 'action' }
        ),
        label(
            'activityTimestamp',
            rect(
                compact ? 10 : g.bubble - 10 - timeWidth,
                compact ? 28 : 10,
                compact ? g.inner : timeWidth,
                15
            ),
            model.time || '',
            {
                fontRole: 'caption',
                color: 'secondaryText',
                align: compact ? 'left' : 'right',
                toolTip: model.fullTime || ''
            }
        ),
        node('Icon', 'activityKind', rect(10, y - 4, 20, 20), {
            icon: icon(model),
            color
        }),
        node(
            'View',
            'activitySentencePort',
            rect(38, y - 4, Math.max(0, g.inner - 28), sentenceHeight),
            { view: 'sentence' }
        )
    ];
    y += Math.max(20, sentenceHeight) + 6;
    const changes = model.changes || [],
        changeNodes = [],
        changeTop = y - 4;
    for (let i = 0; i < changes.length; i++) {
        const rowHeight = Math.max(16, heights['change_' + i] || 16) + 10,
            labelWidth = Math.min(116, Math.max(60, g.inner * 0.25)),
            rowY = y - 4 - changeTop;
        changeNodes.push(
            node(
                'Box',
                'activityChangeRow_' + i,
                rect(0, rowY, g.inner, rowHeight),
                {
                    background: 'surfaceContainer',
                    radius: 9,
                    border: 'outlineVariant',
                    borderWidth: 1
                }
            )
        );
        changeNodes.push(
            label(
                'activityChangeLabel_' + i,
                rect(10, rowY + 5, labelWidth, 15),
                changes[i].label || changes[i].field || '',
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    toolTip: changes[i].label || changes[i].field || ''
                }
            )
        );
        changeNodes.push(
            node(
                'View',
                'activityChangePort_' + i,
                rect(
                    20 + labelWidth,
                    rowY + 5,
                    Math.max(0, g.inner - labelWidth - 30),
                    rowHeight - 10
                ),
                { view: 'change', index: i }
            )
        );
        y += rowHeight + 4;
    }
    content.push(
        node(
            'Box',
            'activityChangeList',
            rect(10, changeTop, g.inner, Math.max(0, y - 4 - changeTop)),
            {
                visible: !!changes.length,
                background: 'transparent',
                children: changeNodes
            }
        )
    );
    if (changes.length) y += 2;
    if (model.expandable) {
        const w = 120;
        content.push(
            button(
                'activityTextExpandButton',
                rect(Math.max(10, g.bubble - 10 - w), y - 4, w, 32),
                tr(model.expanded ? 'Collapse' : 'Expand'),
                model.expanded ? 'chevron-up' : 'chevron-down',
                { type: 'expand' },
                true,
                { tonal: true }
            )
        );
        y += 38;
    }
    const bubbleHeight = y - 4 + 4,
        height = Math.max(72, bubbleHeight + 8);
    nodes.push(
        node(
            'Preview',
            'activityActorPreview',
            rect(4, 4, g.avatar, g.avatar),
            {
                source: model.actorAvatar || '',
                initials: model.serverGenerated
                    ? ''
                    : model.actorInitials || '?',
                icon: model.serverGenerated ? 'system-activity' : 'person',
                round: true,
                outlined: true,
                accent: model.actorColor || 'action'
            }
        )
    );
    nodes.push(
        node(
            'Box',
            'activityEventBubble',
            rect(g.x, 4, g.bubble, bubbleHeight),
            {
                background: model.hovered
                    ? { mix: ['surfaceContainerHigh', 'primaryText', 0.08] }
                    : 'surfaceContainerHigh',
                radius: metrics(style).communicationBubbleRadius,
                border: 'outlineVariant',
                borderWidth: 1,
                children: content
            }
        )
    );
    return { height, nodes };
}
