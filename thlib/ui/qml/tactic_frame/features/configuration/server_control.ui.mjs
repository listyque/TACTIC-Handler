import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { describe as confirmation } from '../../controls/feedback/confirmation.ui.mjs';

export function viewport(model, width, height, language) {
    const card = describe(model, Math.max(1, width - 24), language);
    return {
        nodes: [
            node(
                'Scroll',
                'serverControlBody',
                rect(12, 12, Math.max(1, width - 24), Math.max(1, height - 24)),
                { contentHeight: card.height, children: card.nodes }
            )
        ]
    };
}

export function describe(model, width, language) {
    const tr = (text) => translate(text, language);
    const compact = width < 480;
    const height = compact ? 344 : 250;
    if (model.confirm) {
        const scene = confirmation(
            {
                message: tr(
                    'Restart TACTIC Stream? Connections and running operations may be interrupted while saved settings are applied. Unsaved changes will not be applied.'
                ),
                accept: 'Restart TACTIC Stream',
                reject: 'Cancel',
                busy: model.busy,
                acceptId: 'serverRestartAccept',
                rejectId: 'serverRestartCancel'
            },
            width,
            height,
            language
        );
        return Object.assign(scene, { height });
    }
    const runtime = model.runtime || {};
    const enabled = !model.busy && !model.restarting;
    const nodes = [
        node('Box', 'serverControlSurface', rect(0, 0, width, height), {
            color: 'panel',
            border: 'outline',
            borderWidth: 1,
            radius: 6
        }),
        label(
            'serverControlTitle',
            rect(12, 12, width - 112, 24),
            tr('Server processes'),
            { bold: true }
        ),
        button(
            'serverControlDiscard',
            rect(width - 88, 8, 36, 36),
            tr('Discard changes'),
            'undo',
            { type: 'discard' },
            enabled && model.dirty,
            { iconOnly: true }
        ),
        button(
            'serverControlRefresh',
            rect(width - 48, 8, 36, 36),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            enabled && !model.dirty,
            { iconOnly: true }
        ),
        label(
            'serverWorkerLabel',
            rect(12, 50, width - 24, 22),
            tr('Web workers')
        ),
        node(
            'Field',
            'serverWorkerCount',
            rect(12, 76, Math.min(144, width - 24), 38),
            {
                text: String(model.workers || ''),
                label: tr('Web workers'),
                enabled,
                inputMode: 'numeric',
                action: { type: 'workers' }
            }
        ),
        label(
            'serverRunningWorkers',
            rect(
                compact ? 12 : 172,
                compact ? 124 : 82,
                compact ? width - 24 : width - 184,
                44
            ),
            tr('Running web workers') + ': ' + (runtime.web_workers ?? '—'),
            { wrap: true, color: 'secondaryText' }
        ),
        label(
            'serverControlNotice',
            rect(12, compact ? 176 : 132, width - 24, compact ? 64 : 54),
            tr(
                model.error ||
                    (model.restarting
                        ? 'Restarting TACTIC Stream…'
                        : model.dirty
                          ? 'Save changes before restarting.'
                          : model.notice) ||
                    (!runtime.available
                        ? runtime.reason ||
                          'The server monitor is unavailable or outdated.'
                        : 'Saved settings are applied only after restarting the server.')
            ) || '',
            {
                wrap: true,
                color: model.error ? 'red' : 'secondaryText',
                role: model.error ? 'alert' : 'status'
            }
        )
    ];
    const buttonWidth = compact ? width - 24 : Math.min(220, (width - 32) / 2);
    nodes.push(
        button(
            'serverWorkersSave',
            rect(12, height - (compact ? 88 : 50), buttonWidth, 36),
            tr('Save'),
            'save',
            { type: 'save' },
            enabled && model.dirty
        )
    );
    nodes.push(
        button(
            'serverRestart',
            rect(compact ? 12 : 20 + buttonWidth, height - 50, buttonWidth, 36),
            tr('Restart TACTIC Stream'),
            'refresh',
            { type: 'restart' },
            enabled &&
                !model.dirty &&
                runtime.available &&
                runtime.state === 'running'
        )
    );
    return { nodes, height };
}
