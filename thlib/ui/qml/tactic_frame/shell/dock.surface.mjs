import { layout } from '../core/foundation.mjs';

export function footer(radius, nativeDialog, options = {}) {
    const corner = Math.max(0, radius - 1);
    return {
        radius: corner,
        height: layout.dockWorkspaceFooterHeight,
        topLeft: options.topLeft ? corner : 0,
        topRight: options.topRight ? corner : 0,
        bottomLeft: (
            options.bottomLeft === undefined
                ? !nativeDialog
                : options.bottomLeft
        )
            ? corner
            : 0,
        bottomRight: (
            options.bottomRight === undefined
                ? !nativeDialog
                : options.bottomRight
        )
            ? corner
            : 0,
        divider: options.divider === false ? 0 : 1
    };
}
