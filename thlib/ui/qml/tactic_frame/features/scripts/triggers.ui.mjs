import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import { translate } from '../../core/strings.mjs';

export function layout(model, width, height) {
    const errorHeight = model.error
        ? captionHeight(model.error, Math.max(1, width - 24)) + 8
        : 0;
    const top = 56 + errorHeight,
        left = Math.min(330, Math.max(260, width * 0.34));
    return {
        top,
        left,
        list: rect(12, top, left, height - top - 62),
        editor: rect(22 + left, top, width - left - 34, height - top - 62),
        errorHeight
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        bounds = layout(model, width, height),
        rule = model.rule || {},
        editable = !!rule.ruleId && model.canManage && !model.busy;
    const inner = Math.max(0, bounds.editor.width - 36),
        form = [],
        fields = (kind, id, field, y, h, text) =>
            node(kind, id, rect(10, y, inner, h), {
                text: String(rule[field] || ''),
                label: tr(text),
                placeholder: tr(text),
                enabled: editable,
                action: { type: 'field', field }
            });
    form.push(
        node('Field', 'scriptTriggerTitle', rect(10, 10, inner - 120, 38), {
            text: rule.title || '',
            label: tr('Trigger name'),
            placeholder: tr('Trigger name'),
            enabled: editable,
            action: { type: 'field', field: 'title' }
        })
    );
    form.push(
        node(
            'CheckBox',
            'scriptTriggerEnabled',
            rect(inner - 100, 10, 110, 38),
            {
                text: tr('Enabled'),
                checked: !!rule.enabled,
                enabled: editable,
                action: { type: 'field', field: 'enabled' }
            }
        )
    );
    form.push(
        fields(
            'Area',
            'scriptTriggerDescription',
            'description',
            56,
            68,
            'What this trigger does'
        )
    );
    form.push(
        label(
            'scriptTriggerRunLabel',
            rect(10, 132, inner, 20),
            tr('Run'),
            muted
        )
    );
    const stacked = inner < 500,
        phaseWidth = stacked ? inner : 220;
    form.push(
        node(
            'Choice',
            'scriptTriggerAction',
            rect(10, 158, stacked ? inner : inner - 228, 38),
            {
                label: tr('Action'),
                value: rule.action || '',
                options: model.actions,
                enabled: editable,
                action: { type: 'field', field: 'action' }
            }
        )
    );
    form.push(
        node(
            'Segmented',
            'scriptTriggerPhase',
            rect(
                stacked ? 10 : inner - phaseWidth + 10,
                stacked ? 204 : 158,
                phaseWidth,
                38
            ),
            {
                label: tr('Run'),
                value: rule.phase || 'after',
                options: model.phases,
                enabled: editable,
                action: { type: 'field', field: 'phase' }
            }
        )
    );
    let y = stacked ? 250 : 204;
    form.push(
        label(
            'scriptTriggerObjectsLabel',
            rect(10, y, inner, 20),
            tr('For objects'),
            muted
        )
    );
    y += 26;
    form.push(
        node('Choice', 'scriptTriggerSearchType', rect(10, y, inner, 38), {
            label: tr('Search Type'),
            value: rule.searchType || '',
            options: model.searchTypes,
            enabled: editable,
            action: { type: 'field', field: 'searchType' }
        })
    );
    y += 46;
    form.push(
        fields(
            'Area',
            'scriptTriggerSearchKeys',
            'searchKeysText',
            y,
            76,
            'Exact search keys, one per line (optional)'
        )
    );
    y += 84;
    form.push(
        node(
            'Field',
            'scriptTriggerProcess',
            rect(10, y, Math.max(0, (inner - 8) / 2), 38),
            {
                text: rule.process || '',
                label: tr('Process (optional)'),
                placeholder: tr('Process (optional)'),
                enabled: editable,
                action: { type: 'field', field: 'process' }
            }
        )
    );
    form.push(
        node(
            'Field',
            'scriptTriggerContext',
            rect(18 + (inner - 8) / 2, y, Math.max(0, (inner - 8) / 2), 38),
            {
                text: rule.context || '',
                label: tr('Context (optional)'),
                placeholder: tr('Context (optional)'),
                enabled: editable,
                action: { type: 'field', field: 'context' }
            }
        )
    );
    y += 46;
    const scriptHint = tr(
        String(rule.action || '').startsWith('dcc.')
            ? 'DCC Python script'
            : 'Handler or server script'
    );
    form.push(
        label(
            'scriptTriggerScriptLabel',
            rect(10, y, inner, 20),
            scriptHint,
            muted
        )
    );
    y += 26;
    form.push(
        node('View', 'scriptTriggerScript', rect(10, y, inner, 38), {
            view: 'script',
            enabled: editable
        })
    );
    y += 46;
    if (rule.error) {
        const h = captionHeight(rule.error, inner);
        form.push(
            label('scriptTriggerRuleError', rect(10, y, inner, h), rule.error, {
                color: 'error',
                wrap: true
            })
        );
        y += h + 8;
    }
    const help = tr(
        'Matching triggers run from top to bottom. A failed ‘before’ script stops the action; a failed ‘after’ script is logged and the remaining scripts continue.'
    );
    const helpHeight = captionHeight(help, inner);
    form.push(
        label(
            'scriptTriggerExplanation',
            rect(10, y, inner, helpHeight),
            help,
            Object.assign({}, muted, { fontRole: 'caption', wrap: true })
        )
    );
    y += helpHeight + 12;
    const nodes = [
        node('Box', 'scriptTriggersBackground', rect(0, 0, width, height), {
            background: 'workspace'
        }),
        label(
            'scriptTriggersTitle',
            rect(12, 12, width - 164, 32),
            tr('Script triggers'),
            { fontRole: 'title', weight: 600 }
        ),
        button(
            'scriptTriggerHelpButton',
            rect(width - 142, 12, 30, 32),
            tr('Script triggers help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true }
        ),
        button(
            'scriptTriggersReload',
            rect(width - 104, 12, 92, 32),
            tr('Reload'),
            'refresh',
            { type: 'reload' },
            !model.busy
        ),
        label(
            'scriptTriggersError',
            rect(12, 48, width - 24, bounds.errorHeight),
            model.error || '',
            { color: 'error', wrap: true }
        ),
        node('Box', 'scriptTriggersListSurface', bounds.list, {
            background: 'panel',
            border: 'outlineVariant',
            borderWidth: 1,
            radius: 14,
            children: [
                node(
                    'List',
                    'scriptTriggerRuleList',
                    rect(7, 7, bounds.list.width - 14, bounds.list.height - 14),
                    {
                        source: 'rules',
                        keyField: 'ruleId',
                        fields: [
                            'ruleId',
                            'title',
                            'summary',
                            'ruleEnabled',
                            'valid'
                        ],
                        rowHeight: 71,
                        rowGap: 5,
                        scrollbarId: 'scriptTriggerRuleScrollBar'
                    }
                ),
                label(
                    'scriptTriggersEmpty',
                    rect(12, 32, bounds.list.width - 24, 60),
                    tr('No triggers yet'),
                    Object.assign({}, muted, {
                        visible: !model.count,
                        align: 'center',
                        wrap: true
                    })
                )
            ]
        }),
        node('Scroll', 'scriptTriggerForm', bounds.editor, {
            contentHeight: y,
            scrollbarId: 'scriptTriggerFormScrollBar',
            children: form
        })
    ];
    const bottom = height - 50;
    nodes.push(
        button(
            'scriptTriggerAdd',
            rect(12, bottom, 130, 38),
            tr('Add trigger'),
            'add',
            { type: 'add' },
            model.canManage && !model.busy
        )
    );
    nodes.push(
        button(
            'scriptTriggerUp',
            rect(148, bottom, 30, 38),
            tr('Move up'),
            'arrow-up',
            { type: 'up' },
            model.canManage && !model.busy && model.selected > 0,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'scriptTriggerDown',
            rect(184, bottom, 30, 38),
            tr('Move down'),
            'arrow-down',
            { type: 'down' },
            model.canManage &&
                !model.busy &&
                model.selected >= 0 &&
                model.selected < model.count - 1,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'scriptTriggerDelete',
            rect(220, bottom, 100, 38),
            tr('Delete'),
            'delete',
            { type: 'remove' },
            editable,
            { destructive: true }
        )
    );
    nodes.push(
        button(
            'scriptTriggerDiscard',
            rect(width - 222, bottom, 100, 38),
            tr('Discard'),
            '',
            { type: 'discard' },
            model.dirty && !model.busy
        )
    );
    nodes.push(
        button(
            'scriptTriggerSave',
            rect(width - 112, bottom, 100, 38),
            tr('Save'),
            'save',
            { type: 'save' },
            model.dirty && model.canManage && !model.busy,
            { highlighted: true }
        )
    );
    return { nodes };
}

export function row(list, record, index, model) {
    const width = Math.max(0, list.width - 16),
        selected = model.selected === index;
    return {
        nodes: [
            node(
                'Action',
                'scriptTriggerRule_' + record.ruleId,
                rect(0, 0, width, 66),
                {
                    surface: true,
                    selected,
                    border: record.valid ? 'outlineVariant' : 'error',
                    borderWidth: 1,
                    opacity: record.ruleEnabled ? 1 : 0.62,
                    action: { type: 'select', value: index },
                    children: [
                        node(
                            'Icon',
                            'scriptTriggerRuleIcon',
                            rect(8, 24, 18, 18),
                            {
                                icon: record.valid ? 'bolt' : 'warning',
                                color: record.valid ? 'action' : 'error'
                            }
                        ),
                        label(
                            'scriptTriggerRuleTitle',
                            rect(34, 8, width - 42, 22),
                            record.title || '',
                            { weight: 600 }
                        ),
                        label(
                            'scriptTriggerRuleSummary',
                            rect(34, 32, width - 42, 22),
                            record.summary || '',
                            Object.assign({}, muted, { fontRole: 'caption' })
                        )
                    ]
                }
            )
        ]
    };
}
