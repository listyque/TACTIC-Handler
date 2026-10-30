import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        rules = model.projectRules,
        inner = Math.max(0, width - 24),
        idle = !model.busy,
        helpHeight = width < 520 ? 84 : width < 760 ? 64 : 48,
        contentY = 68 + helpHeight,
        footer = height - 52;
    return {
        nodes: [
            node('Box', 'agentRulesHeader', rect(0, 0, width, 52), {
                background: 'surfaceContainerLow'
            }),
            label(
                'agentRulesTitle',
                rect(12, 6, inner, 22),
                tr('Project chat rules'),
                { weight: 600 }
            ),
            label(
                'agentRulesProject',
                rect(12, 28, inner, 18),
                model.context.project,
                { color: 'secondaryText', fontRole: 'caption' }
            ),
            label(
                'agentRulesHelp',
                rect(12, 62, inner, helpHeight),
                tr(
                    'Shared by all chats in this project. Changes apply on the next send; the current turn keeps its captured rules.'
                ),
                { wrap: true, color: 'secondaryText' }
            ),
            node(
                'Area',
                'agentRulesText',
                rect(12, contentY, inner, Math.max(40, footer - contentY - 40)),
                {
                    text: rules.text,
                    maxLength: 16000,
                    placeholder: tr(
                        'Describe naming, preview destinations and comment preferences.'
                    ),
                    enabled: idle && !!rules.revision,
                    action: { type: 'rulesText' }
                }
            ),
            label(
                'agentRulesError',
                rect(12, footer - 36, inner, 32),
                tr(model.error || ''),
                { wrap: true, color: 'error' }
            ),
            node('Box', 'agentRulesFooter', rect(0, footer, width, 52), {
                background: 'surfaceContainerLow'
            }),
            button(
                'agentRulesCancel',
                rect(12, footer + 10, Math.min(128, (inner - 8) / 2), 32),
                tr('Cancel'),
                'close',
                { type: 'rulesCancel' },
                idle
            ),
            button(
                'agentRulesSave',
                rect(
                    width - 12 - Math.min(164, (inner - 8) / 2),
                    footer + 10,
                    Math.min(164, (inner - 8) / 2),
                    32
                ),
                tr('Save project rules'),
                'save',
                { type: 'rulesSave' },
                idle &&
                    !!rules.revision &&
                    rules.text !== rules.original &&
                    rules.text.length <= 16000
            )
        ]
    };
}
