import { node, rect, label } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { controls } from '../../../core/foundation.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function describe(progress, width, language) {
    if (!progress || !Object.keys(progress).length)
        return { nodes: [], height: 0 };
    const tr = (text, values) => translate(text, language, values),
        nodes = [];
    let y = 0;
    function text(id, value, color = 'secondaryText', fontRole = 'caption') {
        const height = Math.max(18, captionHeight(value, width));
        nodes.push(
            label(id, rect(0, y, width, height), value, {
                fontRole,
                color,
                wrap: true,
                role: 'status'
            })
        );
        y += height + 4;
    }
    const phase = progress.phase,
        message = progress.uploadInterrupted
            ? 'Upload interrupted. Use Retry to resume the existing batch.'
            : progress.error
              ? 'Progress unavailable. Check-in results are not confirmed; retrying status requests.'
              : phase === 'hooks'
                ? 'Running before check-in hooks'
                : phase === 'preparing'
                  ? 'Preparing files and checksums'
                  : phase === 'uploading'
                    ? 'Uploading files'
                    : phase === 'committing'
                      ? 'Checking in on server'
                      : 'Finished';
    text(
        'queueProgressStage',
        tr(message),
        progress.error ? 'error' : 'primaryText',
        'secondary'
    );
    if (progress.filename) text('queueProgressFile', progress.filename);
    function bar(id, title, value, maximum, indeterminate) {
        nodes.push(
            node(
                'View',
                id,
                rect(0, y, width, controls.feedback.progressHeight),
                {
                    view: 'progress',
                    label: tr(title),
                    value,
                    min: 0,
                    max: Math.max(1, maximum || 0),
                    indeterminate: !!indeterminate
                }
            )
        );
        y += controls.feedback.progressHeight + 4;
    }
    if (phase !== 'hooks')
        bar(
            'queueUploadProgress',
            'Upload progress',
            progress.totalBytes > 0 ? progress.bytesDone : progress.filesDone,
            progress.totalBytes > 0 ? progress.totalBytes : progress.totalFiles,
            progress.busy && !progress.totalsKnown
        );
    if (progress.totalFiles > 0) {
        const values = {
            done: progress.filesDone || 0,
            total: progress.totalFiles,
            bytes: ((progress.bytesDone || 0) / 1048576).toFixed(1),
            totalBytes: ((progress.totalBytes || 0) / 1048576).toFixed(1)
        };
        text(
            'queueUploadSummary',
            tr(
                progress.totalsKnown
                    ? 'Uploaded {done} / {total} files · {bytes} / {totalBytes} MB'
                    : 'Uploaded {done} files · {bytes} MB',
                values
            )
        );
    }
    bar(
        'queueServerProgress',
        'Server check-in progress',
        (progress.completed || 0) +
            (progress.failed || 0) +
            (progress.cancelled || 0),
        progress.totalOperations,
        false
    );
    text(
        'queueServerSummary',
        tr(
            'Check-ins: {completed} / {total} completed · {failed} failed · {cancelled} cancelled · {running} running',
            {
                completed: progress.completed || 0,
                total: progress.totalOperations || 0,
                failed: progress.failed || 0,
                cancelled: progress.cancelled || 0,
                running: progress.running || 0
            }
        )
    );
    if (progress.elapsed != null)
        text(
            'queueProgressElapsed',
            tr('Elapsed: {seconds} s', { seconds: progress.elapsed }) +
                (progress.busy && progress.idleSeconds >= 15
                    ? ' · ' +
                      tr('No new progress for {seconds} s', {
                          seconds: progress.idleSeconds
                      })
                    : '')
        );
    return { nodes, height: y };
}
