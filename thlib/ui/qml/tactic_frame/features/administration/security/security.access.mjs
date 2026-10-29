import { node, button } from '../../../core/frame.mjs';
import { rect, label, muted } from '../admin.document.mjs';
import { translate } from '../../../core/strings.mjs';

const accessLabels = {
    allow: 'Full access',
    deny: 'Deny',
    view: 'Read',
    edit: 'Modify',
    insert: 'Create',
    retire: 'Archive',
    delete: 'Delete',
    true: 'Read',
    false: 'Deny'
};
const scopeLabels = {
    builtin: 'Application features',
    project: 'Projects',
    search_type: 'Search Types',
    process: 'Processes',
    sobject: 'Search Objects',
    sobject_column: 'Field access',
    search_filter: 'Search restrictions',
    link: 'Sidebar links',
    gear_menu: 'Menu actions',
    agent_tool: 'AI tools',
    mcp_tool: 'MCP tools'
};

export function toolSettings(model, scope) {
    const rules = model.records.filter(
        (row) => (row.group || row.category) === scope
    );
    const ranks = {
            deny: 0,
            false: 0,
            view: 1,
            true: 1,
            edit: 2,
            insert: 3,
            retire: 4,
            delete: 5,
            allow: 5
        },
        byKey = {};
    let fallback = 0;
    for (const rule of rules) {
        if (rule.default) fallback = ranks[rule.default] || 0;
        else if (rule.key)
            byKey[rule.key] = Math.max(
                byKey[rule.key] ?? -1,
                ranks[rule.access] ?? -1
            );
    }
    const catalog =
            model.metadata[scope === 'mcp_tool' ? 'mcpTools' : 'agentTools'] ||
            [],
        names = catalog
            .filter((tool) => (byKey[tool.name] ?? byKey['*'] ?? fallback) >= 5)
            .map((tool) => tool.name),
        all =
            (byKey['*'] ?? fallback) >= 5 &&
            Object.keys(byKey).every((key) => byKey[key] >= 5);
    return {
        mode: !rules.length ? 'inherit' : all ? 'all' : 'selected',
        names
    };
}

export function models(model, ui, language) {
    const tr = (text) => translate(text, language),
        metadata = model.metadata || {},
        report = metadata.effective,
        match = (text) =>
            String(text).toLowerCase().includes(ui.query.toLowerCase().trim()),
        scope = ui.scope,
        settings = toolSettings(model, scope);
    const effective = [],
        reportView = ui.reportView || 'summary';
    const summary = new Map();
    for (const check of reportView === 'summary' ? report?.checks || [] : []) {
        const key = check.scope + ':' + JSON.stringify(check.attributes),
            entry = summary.get(key) || {
                id: 'check:' + key,
                title: check.label,
                detail:
                    tr(scopeLabels[check.scope] || check.scope) +
                    ' · ' +
                    Object.values(check.attributes).join(' · '),
                value: tr('Denied'),
                context: '',
                allowed: false
            };
        if (check.allowed) {
            entry.allowed = true;
            entry.value = tr(
                check.required === 'allow'
                    ? 'Allowed'
                    : check.required === 'delete'
                      ? 'Full access'
                      : accessLabels[check.required] || check.required
            );
        }
        summary.set(key, entry);
    }
    effective.push(...summary.values());
    for (const group of reportView === 'groups' ? report?.groups || [] : []) {
        effective.push({
            id: (group.default ? 'defaults:' : 'group:') + group.name,
            title: group.name,
            value: tr(
                group.default
                    ? 'System defaults'
                    : group.direct
                      ? 'Direct group'
                      : 'Inherited group'
            ),
            detail: group.default
                ? tr('Combined native access level')
                : group.paths.map((path) => path.join(' → ')).join('; '),
            context: [group.accessLevel, group.project]
                .filter(Boolean)
                .join(' · '),
            icon: 'groups'
        });
    }
    for (const rule of reportView === 'rules' ? report?.rules || [] : []) {
        const attrs = rule.attributes || {},
            title =
                Object.keys(attrs)
                    .map((key) => key + ': ' + attrs[key])
                    .join(' · ') || rule.key;
        effective.push({
            id: rule.scope + ':' + rule.key,
            title: tr(scopeLabels[rule.scope] || rule.scope) + ' · ' + title,
            value: tr(
                accessLabels[rule.access] ||
                    rule.access ||
                    'Search restrictions'
            ),
            detail: (rule.sources || [])
                .map(
                    (source) =>
                        (source.default
                            ? tr('System defaults')
                            : source.group) +
                        ': ' +
                        tr(
                            accessLabels[source.access] ||
                                source.access ||
                                'Search restrictions'
                        )
                )
                .join(' · '),
            context: rule.key,
            icon: 'security'
        });
    }
    for (const [transport, catalog] of [
        ['chat', metadata.agentTools],
        ['mcp', metadata.mcpTools]
    ]) {
        for (const tool of reportView === 'tools' ? catalog || [] : []) {
            const allowed = report?.tools?.[transport]?.includes(tool.name),
                eligible =
                    !metadata.agentAdministratorRequired ||
                    report?.administrator;
            if (report)
                effective.push({
                    id: transport + ':' + tool.name,
                    title:
                        (transport === 'chat' ? tr('AI tools') : 'MCP') +
                        ' · ' +
                        tool.title,
                    value: tr(
                        !eligible
                            ? 'Administrator access required'
                            : allowed
                              ? 'Allowed'
                              : 'Denied'
                    ),
                    detail: tool.description,
                    context: tool.name,
                    icon: 'security'
                });
        }
    }
    return {
        effective: effective.filter((row) => match(JSON.stringify(row))),
        agentTools: (scope === 'mcp_tool'
            ? metadata.mcpTools || []
            : metadata.agentTools || []
        )
            .filter((tool) =>
                match(tool.title + ' ' + tool.description + ' ' + tool.name)
            )
            .map((tool) =>
                Object.assign({}, tool, {
                    checked:
                        settings.mode === 'all' ||
                        settings.names.includes(tool.name)
                })
            )
    };
}

export function workspace(model, ui, width, height, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        effective = ui.scope === 'effective',
        settings = toolSettings(model, ui.scope),
        report = model.metadata.effective,
        available =
            !model.busy && !model.dirty && !model.uncertain && model.ready;
    let y = 0;
    if (effective) {
        nodes.push(
            node(
                'Choice',
                'adminEffectiveUser',
                rect(0, y, Math.max(1, width - 48), 38),
                {
                    label: tr('User'),
                    value: report?.login || '',
                    options: [{ value: '', label: tr('Select a user') }].concat(
                        model.metadata.users || []
                    ),
                    enabled: available,
                    action: { type: 'effectiveUser' }
                }
            ),
            button(
                'adminEffectiveRefresh',
                rect(width - 38, y, 38, 38),
                tr('Refresh'),
                'refresh',
                { type: 'effectiveUser', value: report?.login || '' },
                available && !!report?.login,
                { iconOnly: true }
            )
        );
        y += 46;
        nodes.push(
            label(
                'adminEffectiveNotice',
                rect(0, y, width, width < 520 ? 82 : 62),
                tr(
                    model.dirty
                        ? 'Save or discard changes to inspect saved user permissions.'
                        : !report
                          ? 'Select a user to inspect saved permissions.'
                          : report.administrator
                            ? 'Native administrator: full application rights. Explicit AI and MCP restrictions still apply.'
                            : 'Saved native rules from all groups. Record filters, field rules and operation checks still apply.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
        y += width < 520 ? 90 : 70;
    } else {
        const narrow = width < 520,
            buttonWidth = narrow ? (width - 8) / 2 : 148;
        nodes.push(
            node(
                'Choice',
                'adminToolMode',
                rect(0, y, narrow ? width : Math.max(1, width - 312), 38),
                {
                    label: tr('Group tool policy'),
                    value: settings.mode,
                    options: [
                        ['inherit', 'Inherit'],
                        ['selected', 'Selected tools'],
                        ['all', 'All tools']
                    ].map(([value, text]) => ({ value, label: tr(text) })),
                    enabled: model.canWrite && !model.busy && !model.uncertain,
                    action: { type: 'toolMode' }
                }
            )
        );
        if (narrow) y += 46;
        const start = narrow ? 0 : width - 304;
        nodes.push(
            button(
                'adminToolsRead',
                rect(start, y, buttonWidth, 38),
                tr('Read tools'),
                'visibility',
                { type: 'toolRead' },
                model.canWrite && !model.busy && !model.uncertain
            ),
            button(
                'adminToolsNone',
                rect(start + buttonWidth + 8, y, buttonWidth, 38),
                tr('Clear'),
                'close',
                { type: 'toolNone' },
                model.canWrite && !model.busy && !model.uncertain
            )
        );
        y += 46;
        nodes.push(
            label(
                'adminToolPolicyNotice',
                rect(0, y, width, width < 520 ? 106 : 80),
                tr(
                    'Tool access combines all inherited groups. A local deny does not cancel another group grant. Native operation rights and the connection scope still apply.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
        y += width < 520 ? 114 : 88;
        if (!(model.metadata.agentTools || []).length) {
            nodes.push(
                label(
                    'adminToolUnavailable',
                    rect(0, y, width, 80),
                    tr('This server does not expose the agent tool catalogue.'),
                    { wrap: true }
                )
            );
            return { nodes };
        }
    }
    if (effective) {
        nodes.push(
            node('Choice', 'adminEffectiveView', rect(0, y, width, 38), {
                label: tr('Report'),
                value: ui.reportView || 'summary',
                enabled: !model.busy,
                options: [
                    ['summary', 'Permission summary'],
                    ['groups', 'Groups and inheritance'],
                    ['rules', 'Rule sources'],
                    ['tools', 'AI and MCP tools']
                ].map(([value, text]) => ({ value, label: tr(text) })),
                action: { type: 'reportView' }
            })
        );
        y += 46;
    }
    nodes.push(
        node('Field', 'adminAccessSearch', rect(0, y, width, 38), {
            text: ui.query,
            placeholder: tr('Search'),
            enabled: !model.busy,
            action: { type: 'query' }
        })
    );
    y += 46;
    const source = effective ? 'effective' : 'agentTools';
    nodes.push(
        node(
            'List',
            'adminAccessDetailsList_' + source,
            rect(0, y, width, Math.max(1, height - y)),
            {
                source,
                rowHeight: effective
                    ? width < 520
                        ? 104
                        : 84
                    : width < 520
                      ? 120
                      : 100,
                keyField: effective ? 'id' : 'name',
                fields: [],
                scrollbarId: 'adminAccessDetailsScrollBar'
            }
        )
    );
    return { nodes };
}

export function row(list, record, model, ui, language) {
    const tr = (text) => translate(text, language),
        width = Math.max(1, list.width - 20),
        height = list.rowHeight;
    const effective = list.source === 'effective',
        left = effective ? 8 : 44,
        id = record.id || record.name;
    const nodes = [
        label(
            'adminAccessRowTitle_' + id,
            rect(left, 4, width - left - 8, 24),
            record.title,
            { weight: 600 }
        ),
        label(
            'adminAccessRowDetail_' + id,
            rect(left, 32, width - left - 8, height - 60),
            effective ? record.detail : record.description,
            {
                wrap: true,
                maxLines: height < 100 ? 1 : 2,
                toolTip: effective ? record.detail : record.description,
                color: 'secondaryText'
            }
        ),
        label(
            'adminAccessRowValue_' + id,
            rect(left, height - 24, width - left - 8, 20),
            effective
                ? [record.value, record.context].filter(Boolean).join(' · ')
                : tr(record.readonly ? 'Read only' : 'Changes data'),
            Object.assign(
                {},
                muted,
                record.allowed === undefined
                    ? {}
                    : { color: record.allowed ? 'action' : 'error' }
            )
        ),
        node(
            'Box',
            'adminAccessRowDivider_' + id,
            rect(8, height - 1, width - 16, 1),
            { background: 'outlineVariant' }
        )
    ];
    if (!effective)
        nodes.unshift(
            node('CheckBox', 'adminTool_' + record.name, rect(0, 0, 38, 38), {
                text: record.title,
                checked: record.checked,
                enabled: model.canWrite && !model.busy && !model.uncertain,
                indicatorX: 8,
                action: { type: 'toolToggle', name: record.name }
            })
        );
    return { nodes };
}
