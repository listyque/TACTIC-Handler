import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { phase } from './presentation.mjs';

export function status(model, language) {
    const tr = (text) => translate(text, language),
        p = model.progress || {};
    if (!model.busy && !p.phase && !p.state)
        return (
            tr('Ready') +
            (model.workspace ? ' · ' + model.workspace : '') +
            (model.selected
                ? ' · ' + model.selected + ' ' + tr('selected')
                : '')
        );
    const step = p.operation_stage
        ? tr('Step {step} of {total}')
              .replace('{step}', p.operation_stage)
              .replace('{total}', p.operation_stages) + ' · '
        : '';
    return (
        step +
        phase(p.phase || p.state, language) +
        ' · ' +
        (p.phase_files_done ?? p.files_done ?? 0) +
        (p.total_known ? ' / ' + (p.files_total || 0) : '') +
        ' ' +
        tr('files') +
        ' · ' +
        ((p.phase_bytes_done ?? p.bytes_done ?? 0) / 1048576).toFixed(1) +
        (p.total_known
            ? ' / ' + ((p.bytes_total || 0) / 1048576).toFixed(1)
            : '') +
        ' MB'
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        p = model.progress || {},
        narrow = width < 800,
        nodes = [];
    let right = width - 8;
    const iconY = (height - 28) / 2;
    if (model.busy) {
        right -= 28;
        nodes.push(
            button(
                'fileWorkspaceStop',
                rect(right, iconY, 28, 28),
                tr('Stop waiting'),
                'close',
                { type: 'stop' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
        right -= 8;
    }
    right -= 28;
    nodes.push(
        button(
            'fileWorkspaceToggleLog',
            rect(right, iconY, 28, 28),
            tr(model.logVisible ? 'Hide log' : 'Show log'),
            'terminal',
            { type: 'log' },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    right -= 8;
    let x = 8;
    if (model.busy) {
        nodes.push(
            node(
                'View',
                'workspaceBusyPort',
                rect(x, (height - 24) / 2, 24, 24),
                { view: 'busy' }
            )
        );
        x += 32;
    }
    const remaining = Math.max(0, right - x),
        progressWidth = model.busy
            ? Math.min(narrow ? 60 : 120, remaining * 0.3)
            : 0;
    let speed = '';
    if (!narrow && p.bytes_per_second > 0)
        speed =
            ((p.bytes_per_second || 0) / 1048576).toFixed(1) +
            ' MB/s' +
            (p.eta_seconds > 0
                ? ' · ~' + Math.ceil(p.eta_seconds) + ' ' + tr('seconds')
                : '');
    const speedWidth = speed ? Math.min(180, remaining * 0.25) : 0,
        pathWidth = !narrow ? remaining * 0.25 : 0;
    const statusWidth = Math.max(
        0,
        remaining -
            progressWidth -
            speedWidth -
            pathWidth -
            (model.busy ? 8 : 0)
    );
    nodes.push(
        label(
            'fileWorkspaceStatus',
            rect(x, 0, statusWidth, height),
            status(model, language),
            { fontRole: 'secondary', color: 'secondaryText', role: 'status' }
        )
    );
    x += statusWidth + 8;
    if (model.busy) {
        const progress = ['staging', 'verifying', 'running'].includes(
            p.phase || p.state
        )
            ? (p.phase_files_done ?? p.files_done ?? 0) /
              Math.max(1, p.files_total || 0)
            : p.bytes_total > 0
              ? (p.phase_bytes_done ?? p.bytes_done ?? 0) / p.bytes_total
              : 0;
        nodes.push(
            node(
                'View',
                'workspaceTransferProgress',
                rect(x, (height - 8) / 2, progressWidth, 8),
                {
                    view: 'progress',
                    value: Math.max(0, Math.min(1, progress)),
                    indeterminate: !p.total_known,
                    label: tr('Transfer progress')
                }
            )
        );
        x += progressWidth;
    }
    if (speed) {
        nodes.push(
            label(
                'workspaceTransferSpeed',
                rect(x, 0, speedWidth, height),
                speed,
                { color: 'secondaryText', fontRole: 'secondary' }
            )
        );
        x += speedWidth;
    }
    if (pathWidth)
        nodes.push(
            label(
                'workspaceTransferPath',
                rect(x, 0, pathWidth, height),
                p.path || '',
                {
                    color: 'secondaryText',
                    elideMiddle: true,
                    fontRole: 'secondary'
                }
            )
        );
    return { nodes };
}
