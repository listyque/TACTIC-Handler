import { button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function status(executor = {}, language) {
    return translate(
        executor.error ||
            {
                starting: 'Connecting agent…',
                connected: 'Agent connected',
                stopping: 'Disconnecting agent…',
                external:
                    'Connected outside this UI. Stop it where it was started.'
            }[executor.state] ||
            'Connect an agent to send requests.',
        language
    );
}

export function control(executor = {}, bounds, language, enabled = true) {
    const running = ['starting', 'connected', 'stopping'].includes(
        executor.state
    );
    return button(
        'agentExecutorControl',
        bounds,
        translate(
            {
                starting: 'Stop connecting',
                connected: 'Disconnect agent',
                stopping: 'Disconnecting…',
                external: 'Agent connected'
            }[executor.state] || 'Connect agent',
            language
        ),
        running ? 'stop' : 'play',
        { type: 'executor', value: running ? 'stop' : 'start' },
        enabled && !['stopping', 'external'].includes(executor.state),
        { highlighted: !running && executor.state !== 'external' }
    );
}
