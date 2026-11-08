export function status(value) {
    if (value === 'Completed') return { color: 'green', icon: 'check-circle' };
    if (['Failed', 'Invalid', 'Missing files'].includes(value))
        return { color: 'error', icon: 'error' };
    if (['Running', 'Queued'].includes(value))
        return { color: 'action', icon: 'sync' };
    if (value === 'Cancelled') return { color: 'yellow', icon: 'cancel' };
    if (['Validating', 'Needs validation'].includes(value))
        return { color: 'secondaryText', icon: 'hourglass-top' };
    return { color: 'secondaryText', icon: 'archive' };
}

export function statusTitle(record) {
    return record.status === 'Prepared'
        ? 'Ready to send'
        : record.status || 'Prepared';
}

export function preview(model) {
    const record = model.record || {},
        enabled = !model.busy && !!record.canPreview;
    return [
        {
            title: 'Capture screenshot',
            command: 'capture',
            icon: 'camera',
            enabled
        },
        {
            title: 'Choose preview images',
            command: 'choose',
            icon: 'image',
            enabled
        },
        {
            title: 'Paste preview image from clipboard',
            command: 'paste',
            icon: 'clipboard',
            enabled:
                enabled && (!model.clipboardKnown || model.clipboardHasImage)
        },
        {
            title: 'Manage selected previews',
            command: 'manage',
            icon: 'collections',
            enabled: record.previewCount > 0
        },
        { separator: true },
        {
            title: 'Clear operation previews',
            command: 'clearPreviews',
            icon: 'delete-sweep',
            enabled: enabled && record.previewCount > 0
        }
    ];
}

export function send(model) {
    const record = model.record || {};
    return [
        {
            title: 'Commit current',
            command: 'current',
            icon: 'upload',
            enabled:
                !model.busy &&
                !model.versionError &&
                !!record.canCommit &&
                record.status !== 'Completed'
        },
        {
            title: 'Commit selected',
            command: 'selected',
            icon: 'done-all',
            enabled:
                !model.busy && !model.versionError && !!model.hasCheckedReady
        }
    ];
}

export function operation(model, record) {
    const result = [
        {
            title: 'Commit current',
            command: 'current',
            icon: 'upload',
            enabled:
                !model.busy &&
                !model.versionError &&
                !!record.canCommit &&
                record.status !== 'Completed'
        }
    ];
    if (['Failed', 'Cancelled'].includes(record.status))
        result.push({
            title: 'Retry',
            command: 'retry',
            icon: 'refresh',
            enabled: !!record.canRetry && !model.busy
        });
    if (model.cancelPrepared)
        result.push({
            title: 'Cancel',
            command: 'cancelOperation',
            icon: 'close',
            enabled: !model.busy && !!(record.canCancel ?? record.canEdit)
        });
    result.push({
        title: 'Remove operation',
        command: 'remove',
        icon: 'delete',
        enabled:
            !model.busy &&
            record.status !== 'Running' &&
            record.canRemove !== false
    });
    return result;
}

export function toolbar(model) {
    return [
        {
            title: 'Move operation up',
            command: 'up',
            icon: 'arrow-up',
            visible: model.count > 1,
            enabled: !model.busy && model.selected > 0
        },
        {
            title: 'Move operation down',
            command: 'down',
            icon: 'arrow-down',
            visible: model.count > 1,
            enabled:
                !model.busy &&
                model.selected >= 0 &&
                model.selected < model.count - 1
        },
        {
            title: 'Clear completed',
            command: 'completed',
            icon: 'check',
            visible: !!model.hasCompleted,
            enabled: !model.busy
        },
        {
            title: 'Clear queue',
            command: 'clear',
            icon: 'delete-sweep',
            visible:
                model.count > 0 ||
                (!!model.progress && Object.keys(model.progress).length > 0),
            enabled: !model.busy
        }
    ];
}
