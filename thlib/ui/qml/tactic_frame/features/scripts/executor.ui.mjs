import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

const busy = ['preparing', 'starting', 'connected', 'stopping'];

export function current(model) {
    const snapshot = model.executor || {},
        targets = snapshot.targets || [];
    const active = targets.find(
        (row) => busy.includes(row.state) || row.state === 'external'
    );
    const target =
        model.executorTarget ??
        active?.id ??
        targets.find((row) => row.id === snapshot.preferred)?.id ??
        snapshot.target ??
        '';
    const selected = targets.find((row) => row.id === target);
    return Object.assign({ state: 'stopped', error: '' }, selected, {
        target,
        unavailable:
            !selected ||
            (!busy.includes(selected.state) && !!active && active.id !== target)
    });
}

export function status(executor = {}, language) {
    return translate(
        executor.error ||
            {
                preparing: 'Preparing the local agent environment…',
                starting: 'Connecting agent…',
                connected: 'Agent connected',
                stopping: 'Disconnecting agent…',
                external:
                    'Connected outside this UI. Stop it where it was started.'
            }[executor.state] ||
            (executor.target === ''
                ? 'Open TACTIC Handler to connect locally, or choose TACTIC server.'
                : 'Connect an agent to send requests.'),
        language
    );
}

export function controls(model, width, y, language, enabled = true) {
    const tr = (value) => translate(value, language),
        executor = current(model);
    const compact = width < 480,
        choiceWidth = Math.min(240, width - (compact ? 72 : 216));
    const scopeX = Math.min(width - 12, choiceWidth + 212);
    const targets = model.executor?.targets || [],
        running = busy.includes(executor.state);
    const options = [{ value: '', label: tr('Choose computer') }].concat(
        targets.map((row) => ({
            value: row.id,
            label:
                row.kind === 'server'
                    ? tr('TACTIC server')
                    : row.kind === 'external'
                      ? tr('External agent')
                      : (row.id === model.executor?.preferred
                            ? tr('This computer')
                            : 'TH') +
                        ' · ' +
                        row.label
        }))
    );
    if (executor.target && !targets.some((row) => row.id === executor.target))
        options.push({
            value: executor.target,
            label: tr('Disconnected desktop')
        });
    const explanation = executor.error
        ? status(executor, language)
        : !executor.target
          ? tr(
                'Open TACTIC Handler to connect locally, or choose TACTIC server.'
            )
          : executor.unavailable
            ? tr(
                  'Disconnect the current agent before starting it on another computer.'
              )
            : executor.target === 'server'
              ? tr('Runs on the TACTIC server for this project.')
              : tr(
                    'Uses Codex sign-in and local API addresses on the selected computer.'
                );
    const text = tr(
        {
            preparing: 'Stop connecting',
            starting: 'Stop connecting',
            connected: 'Disconnect agent',
            stopping: 'Disconnecting…',
            external: 'Agent connected'
        }[executor.state] || 'Connect agent'
    );
    return [
        node('Choice', 'agentExecutorTarget', rect(12, y, choiceWidth, 32), {
            value: executor.target,
            options,
            label: tr('Run agent on'),
            tooltip: explanation,
            enabled,
            action: { type: 'executorTarget' }
        }),
        button(
            'agentExecutorControl',
            rect(choiceWidth + 20, y, compact ? 32 : 180, 32),
            text,
            running ? 'stop' : 'play',
            {
                type: 'executor',
                value: {
                    action: running ? 'stop' : 'start',
                    target: executor.target
                }
            },
            enabled &&
                !executor.unavailable &&
                !['stopping', 'external'].includes(executor.state),
            { highlighted: !running, iconOnly: compact, tooltip: explanation }
        ),
        label(
            'agentExecutorScope',
            rect(scopeX, y, width - scopeX - 12, 32),
            explanation,
            {
                color: executor.error ? 'error' : 'secondaryText',
                visible: width > 900
            }
        )
    ];
}
