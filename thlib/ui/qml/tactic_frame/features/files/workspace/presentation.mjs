// File status precedence is shared; controllers retain filesystem state.
import { translate } from '../../../core/strings.mjs';

export const columnTitles = {
    path: 'File',
    local_status: 'Local changes',
    server_status: 'Server state',
    checkout: 'Checkout / locks',
    number: 'Version',
    local_number: 'Local revision',
    have_number: 'Have',
    head_number: 'Head',
    size: 'Size',
    type: 'Type'
};

export function localStatus(value, language) {
    return translate(
        {
            modified: 'Modified',
            missing: 'Missing',
            added: 'Added',
            clean: 'Clean',
            unmapped: 'Not mapped to workspace'
        }[value] || 'Not inspected',
        language
    );
}

export function serverStatus(value, language) {
    return translate(
        {
            modified_after_upload: 'Modified after upload',
            newer: 'Newer on server',
            current: 'Current',
            write: 'Uploaded',
            delete: 'Deleted',
            deleted: 'Deleted',
            checkout: 'Checked out',
            untracked: 'Untracked',
            unmapped: 'Not mapped to workspace',
            'move/add': 'Renamed / moved',
            'move/delete': 'Renamed / moved'
        }[value] || 'Published',
        language
    );
}

export function phase(value, language) {
    return translate(
        {
            manifest: 'Preparing manifest',
            offline: 'Connection lost; work retained',
            preparing: 'Preparing local changes',
            applying: 'Applying atomic batch',
            submitting: 'Submitting changelist',
            recovering: 'Recovering submit result',
            verifying: 'Verifying files',
            staging: 'Staging files',
            unavailable: 'Unavailable locally',
            indexing_history: 'Indexing revision history',
            blocked: 'Sync stopped',
            cancelled: 'Cancelled',
            waiting: 'Waiting for server',
            discovering: 'Discovering files',
            reconciling: 'Reconciling workspace',
            collecting: 'Uploading files',
            uploading: 'Uploading files',
            queued: 'Queued on server',
            running: 'Verifying and staging',
            downloading: 'Downloading files',
            streaming: 'Downloading files',
            resolving: 'Resolving conflicts',
            error: 'Failed',
            submitted: 'Submitted',
            ready: 'Ready to submit',
            complete: 'Finished'
        }[value] || 'Ready',
        language
    );
}

export function badges(row) {
    const result = [];
    const action = row.action || row.server_status || '';
    const local = row.local_status || '';
    if (row.transfer_state && ['staged'].indexOf(row.transfer_state) < 0)
        result.push({
            label:
                {
                    waiting: 'Waiting for upload',
                    uploading: 'Uploading',
                    uploaded: 'Uploaded; waiting for verification',
                    verifying: 'Verifying',
                    verified: 'Verified; waiting for staging',
                    error: 'Failed'
                }[row.transfer_state] || row.transfer_state,
            icon: 'cloud-upload',
            tone: row.transfer_state === 'error' ? 'error' : 'action'
        });
    if (local === 'unmapped' || action === 'unmapped')
        result.push({
            label: 'Not mapped to workspace',
            icon: 'folder-lock',
            tone: 'neutral'
        });
    if (action === 'move/add' || action === 'move/delete')
        result.push({
            label: 'Renamed / moved',
            icon: 'swap-horizontal',
            tone: 'action'
        });
    if (action === 'checkout' && !row.base && !row.file && !row.transfer_state)
        result.push({
            label: 'Waiting for upload',
            icon: 'cloud-upload',
            tone: 'warning'
        });
    if (row.conflict || row.needs_resolve)
        result.push({ label: 'Conflict', icon: 'warning', tone: 'error' });
    if (row.error)
        result.push({ label: 'Failed', icon: 'error', tone: 'error' });
    if (local === 'modified')
        result.push({
            label:
                action === 'write' &&
                row.change_state === 'pending' &&
                row.staged_current === false
                    ? 'Modified after upload'
                    : 'Modified',
            icon: 'edit',
            tone: 'warning'
        });
    if (local === 'added')
        result.push({ label: 'Added', icon: 'add', tone: 'success' });
    if (local === 'missing')
        result.push({ label: 'Missing', icon: 'file-remove', tone: 'error' });
    if (action === 'delete' || row.deleted)
        result.push({
            label: 'Marked for delete',
            icon: 'delete',
            tone: 'error'
        });
    if (row.staged_current === false && local !== 'modified')
        result.push({
            label: 'Modified after upload',
            icon: 'edit',
            tone: 'warning'
        });
    if (action === 'write' && row.staged_current !== false)
        result.push({
            label:
                row.change_state === 'shelved'
                    ? 'Shelved'
                    : row.change_state === 'submitted'
                      ? 'Submitted'
                      : 'Uploaded',
            icon: 'cloud-check',
            tone: 'success'
        });
    if (action === 'checkout')
        result.push({ label: 'Checked out', icon: 'edit', tone: 'action' });
    if (action === 'newer')
        result.push({
            label: 'Newer on server',
            icon: 'cloud-download',
            tone: 'warning'
        });
    if (row.head_state === 'server-only')
        result.push({ label: 'Server only', icon: 'cloud', tone: 'neutral' });
    if (row.head_state === 'newer' && action !== 'newer')
        result.push({
            label: 'Newer on server',
            icon: 'cloud-download',
            tone: 'warning'
        });
    if (row.head_state === 'deleted')
        result.push({
            label: 'Deleted on server',
            icon: 'delete',
            tone: 'error'
        });
    if (action === 'untracked')
        result.push({ label: 'Untracked', icon: 'file-plus', tone: 'warning' });
    if (!result.length)
        result.push({
            label:
                action === 'current' || row.head_state === 'current'
                    ? 'Current'
                    : row.head_state === 'server-absent'
                      ? 'Not on server'
                      : 'Published',
            icon: 'file',
            tone: 'neutral'
        });
    return result;
}

export function color(theme, tone) {
    return tone === 'error'
        ? theme.error
        : tone === 'warning'
          ? theme.yellow
          : tone === 'success'
            ? theme.green
            : tone === 'action'
              ? theme.action
              : tone === 'other'
                ? theme.violet
                : theme.secondaryText;
}

export function value(row, key) {
    const file = row.file || row.head || row.have || row;
    if (key === 'path') return row.path || '';
    if (key === 'local_number')
        return row.local_number
            ? '#' + row.local_number + (row.local_modified ? ' *' : '')
            : '—';
    if (key === 'have_number') return row.have ? '#' + row.have.number : '—';
    if (key === 'head_number') return row.head ? '#' + row.head.number : '—';
    if (key === 'number') return '#' + (file.number || '—');
    if (key === 'size') return ((file.size || 0) / 1048576).toFixed(2) + ' MB';
    if (key === 'type')
        return (row.path || '').split('.').slice(1).pop() || '—';
    return row[key] || '';
}

export function matches(row, text, status) {
    return (
        (!text ||
            (row.path || '').toLowerCase().indexOf(text.toLowerCase()) >= 0) &&
        (!status || badges(row).some((badge) => badge.label === status))
    );
}
