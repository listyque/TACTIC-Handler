import { node, rect } from '../../core/frame.mjs';

export const desktopHeight = 77;

export function describe(id, width, height, children) {
    return node('Box', id, rect(0, 0, width, height), {
        background: 'surfaceContainerLow',
        radius: 0,
        titlebar: true,
        chromeRight: 94,
        chromeTop: 12,
        chromeHeight: 34,
        children
    });
}
