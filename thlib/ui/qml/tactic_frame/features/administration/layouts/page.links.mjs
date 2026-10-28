// Only references to an existing page in this project open a layout editor.
export function target(href, project, origin, catalog) {
    if (
        typeof href !== 'string' ||
        href.length > 16384 ||
        /[\x00-\x20\\]/.test(href)
    )
        return '';
    let path = href;
    const absolute = /^(https?:\/\/[^/]+)(\/.*)$/i.exec(path);
    if (absolute) {
        if (
            !origin ||
            absolute[1].toLowerCase() !==
                origin.replace(/\/$/, '').toLowerCase()
        )
            return '';
        path = absolute[2];
    }
    const match =
        /^\/(?:projects\/([^/]+)\/)?dashboard\/([^/?#]+)(?:[?#].*)?$/.exec(
            path
        );
    if (!match) return '';
    try {
        if (match[1] && decodeURIComponent(match[1]) !== project) return '';
        const name = decodeURIComponent(match[2]);
        return (catalog || []).some((row) => row.identity === name) ? name : '';
    } catch (error) {
        return '';
    }
}

// Retain view state when following links, without retaining drafts or undo documents.
export function context(ui) {
    const result = {};
    for (const key of [
        'selected',
        'selection',
        'multiSelect',
        'snap',
        'panel',
        'canvas',
        'canvasWidthText',
        'layersWidth',
        'propertiesWidth',
        'layersHidden',
        'propertiesHidden',
        'collapsed'
    ])
        result[key] = ui[key];
    return result;
}
