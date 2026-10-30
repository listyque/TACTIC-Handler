import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Settings from './settings.ui.mjs';
import * as Executor from '../scripts/executor.ui.mjs';

export function initial() {
    return {
        profiles: [],
        kinds: [],
        default: 'codex',
        revision: '',
        selected: 'codex',
        draft: {},
        baseline: {},
        busy: false,
        error: '',
        notice: '',
        executor: {}
    };
}
export function select(model, id) {
    const row = model.profiles.find((item) => item.id === id);
    const draft = {
        name: row?.name || '',
        kind: row?.kind || 'compatible',
        url: row?.url || '',
        secret: '',
        secret_env: row?.secret_env || '',
        clear_secret: false,
        enabled: row?.enabled ?? true,
        default_model: row?.default_model || '',
        default: id === model.default
    };
    return Object.assign({}, model, {
        selected: id,
        draft,
        baseline: Object.assign({}, draft),
        error: '',
        notice: ''
    });
}
export function dirty(model) {
    return JSON.stringify(model.draft) !== JSON.stringify(model.baseline);
}
export function edit(model, field, value) {
    const draft = Object.assign({}, model.draft, { [field]: value });
    if (field === 'kind')
        draft.url = model.kinds.find((kind) => kind.value === value)?.url || '';
    return Object.assign({}, model, { draft, error: '', notice: '' });
}
export function describe(model, width, height, language) {
    const tr = (key) => translate(key, language),
        locked = model.busy;
    const selected = model.profiles.find((item) => item.id === model.selected);
    const narrow = width < 620,
        rowHeight = narrow ? 80 : 40,
        toolsWidth = narrow ? width - 24 : Math.min(320, width / 2);
    const nodes = [
        node(
            'Choice',
            'agentProviderProfile',
            rect(12, 8, narrow ? width - 24 : width - toolsWidth - 36, 32),
            {
                label: tr('AI connection'),
                value: model.selected,
                enabled: !locked && !dirty(model),
                options: model.profiles
                    .map((item) => ({ value: item.id, label: item.name }))
                    .concat(
                        model.selected
                            ? []
                            : [{ value: '', label: tr('New connection') }]
                    ),
                action: { type: 'select' }
            }
        )
    ];
    const left = narrow ? 12 : width - toolsWidth - 12,
        top = narrow ? 48 : 8;
    [
        ['New', 'add', 'new'],
        ['Discard', 'undo', 'reset'],
        ['Remove', 'delete', 'remove'],
        ['Refresh', 'refresh', 'refresh']
    ].forEach(([text, icon, type], index) =>
        nodes.push(
            button(
                'agentProvider_' + type,
                rect(left + index * 38, top, 32, 32),
                tr(text),
                icon,
                { type },
                !locked &&
                    (type === 'reset' || !dirty(model)) &&
                    (type !== 'remove' ||
                        (!!model.selected && model.selected !== 'codex')),
                { iconOnly: true, destructive: type === 'remove' }
            )
        )
    );
    nodes.push(
        label(
            'agentProviderNotice',
            rect(12, rowHeight + 8, width - 24, 44),
            tr(
                model.error ||
                    (['starting', 'stopping', 'failed'].includes(
                        model.executor?.state
                    )
                        ? Executor.status(model.executor, language)
                        : '') ||
                    (selected?.status === 'waiting' &&
                    !['connected', 'external'].includes(model.executor?.state)
                        ? 'Connect an agent to check this connection.'
                        : '') ||
                    model.notice ||
                    selected?.error ||
                    {
                        connected: 'Connection checked',
                        failed: 'Connection failed',
                        waiting: 'Waiting for the external host',
                        unchecked: 'Connection has not been checked'
                    }[selected?.status] ||
                    'Configure a connection, then check it from the external host.'
            ),
            Object.assign({}, muted, {
                wrap: true,
                color:
                    model.error ||
                    model.executor?.error ||
                    selected?.status === 'failed'
                        ? 'error'
                        : 'muted'
            })
        )
    );
    const fields = [
        {
            kind: 'Field',
            field: 'name',
            title: 'Connection name',
            props: { maxLength: 128 }
        },
        {
            kind: 'Choice',
            field: 'kind',
            title: 'Provider',
            enabled: model.selected !== 'codex',
            options: model.kinds.filter((item) =>
                model.selected === 'codex'
                    ? item.value === 'codex'
                    : item.value !== 'codex'
            )
        },
        { kind: 'Switch', field: 'enabled', title: 'Enable connection' },
        { kind: 'Switch', field: 'default', title: 'Default connection' }
    ];
    if (model.draft.kind === 'codex')
        fields.push({
            kind: 'Heading',
            id: 'agentCodexAccount',
            title: 'Account authorization',
            description:
                'Codex uses the account signed in on the external host. Provider API keys are not required.'
        });
    else
        fields.push(
            {
                kind: 'Field',
                field: 'url',
                title: 'API base URL',
                description:
                    'The external host connects to this address. Localhost means the machine running that host.',
                props: { maxLength: 2048 }
            },
            {
                kind: 'Field',
                field: 'secret',
                title: 'API key',
                description: selected?.has_secret
                    ? 'A key is stored. Leave empty to keep it.'
                    : 'Write-only credential. It is encrypted and never returned to this form.',
                props: {
                    password: true,
                    maxLength: 4096,
                    autocomplete: 'new-password'
                }
            },
            {
                kind: 'Switch',
                field: 'clear_secret',
                title: 'Remove stored API key'
            },
            {
                kind: 'Field',
                field: 'secret_env',
                title: 'Host key environment variable',
                description:
                    'Optional alternative to a stored API key. Enter the variable name, not its value.',
                props: { maxLength: 128 }
            }
        );
    const models = selected?.models || [];
    fields.push(
        {
            kind: models.length ? 'Choice' : 'Field',
            field: 'default_model',
            title: 'Default model',
            options: [{ value: '', label: tr('Agent default') }].concat(
                models.map((item) => ({ value: item.id, label: item.label }))
            ),
            props: { maxLength: 256 }
        },
        {
            kind: 'Heading',
            id: 'agentProviderDataNotice',
            title: 'Project data',
            description:
                'Chat messages, project context and attachments go only to the selected connection after Send. Connection checks do not send project data.'
        }
    );
    nodes.push(
        Executor.control(
            model.executor,
            rect(12, rowHeight + 56, 180, 32),
            language,
            !locked && !dirty(model) && !!model.selected
        )
    );
    nodes.push(
        label(
            'agentProviderExecutorScope',
            rect(204, rowHeight + 56, Math.max(0, width - 216), 32),
            model.executor?.state === 'external'
                ? Executor.status(model.executor, language)
                : tr('Runs on the TACTIC server for this project.'),
            { color: 'secondaryText', visible: !narrow }
        )
    );
    const contentY = rowHeight + 96;
    nodes.push(
        node(
            'Box',
            'agentProviderForm',
            rect(0, contentY, width, Math.max(80, height - contentY - 52)),
            {
                children: Settings.describe(
                    { fields, values: model.draft, busy: locked, options: {} },
                    width,
                    Math.max(80, height - contentY - 52),
                    language
                ).nodes
            }
        )
    );
    nodes.push(
        button(
            'agentProviderSave',
            rect(
                Math.max(12, width - 344),
                height - 44,
                Math.min(120, width - 236),
                32
            ),
            tr('Save'),
            'save',
            { type: 'save' },
            !locked && !!model.draft.name?.trim(),
            { highlighted: true, iconOnly: width < 360 }
        ),
        button(
            'agentProviderCheck',
            rect(width - 212, height - 44, 200, 32),
            tr('Check connection'),
            'refresh',
            { type: 'check' },
            !locked && !!model.selected && !dirty(model)
        )
    );
    return { nodes };
}
