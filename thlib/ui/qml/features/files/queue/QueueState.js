.pragma library

function record(value, busy) {
    const result = Object.assign({}, value);
    const editable = !busy && !!value.canEdit;
    result.canOptions = editable;
    result.canDescription = editable;
    result.canRepository = editable;
    result.canVersion = editable;
    result.canContext = editable;
    result.canPreview = editable;
    result.canNaming = true;
    result.canRetry = value.status === 'Failed';
    result.canInspect = false;
    result.needsFiles = false;
    return result;
}

function files(record) {
    const sources = record.sourceFiles || [],
        previews = record.previewFiles || [],
        versioned = record.versionedPaths || [];
    return sources
        .map((path, index) => ({
            key: 'main_' + index,
            index,
            path,
            target: versioned[index] || '',
            preview: false,
            canRemove: !!record.canEdit
        }))
        .concat(
            previews.map((path, index) => ({
                key: 'preview_' + index,
                index,
                path,
                target: '',
                preview: true,
                canRemove: !!record.canEdit
            }))
        );
}

function previews(record) {
    return (record.previewFiles || []).map((path, index) => ({
        key: 'preview_' + index,
        index,
        title: path.replace(/\\/g, '/').split('/').pop(),
        operationId: record.operationId,
        source: (record.previewUrls || [])[index] || '',
        canRemove: !!record.canPreview
    }));
}
