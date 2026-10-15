// Handler's docking zones, in workspace pixels. Adapters own panel trees and persistence.
export const dragThreshold = 6;

export function finishDrop(zone, target, wasFloating) {
    if (zone) return { type: target ? 'place' : 'snap', zone, target };
    return { type: wasFloating ? 'move' : 'cancel' };
}

export function rootZone(x, y, width, height) {
    if (x <= 24) return 'left';
    if (x >= width - 24) return 'right';
    if (y <= 24) return 'top';
    if (y >= height - 24) return 'bottom';
    return '';
}

export function targetZone(x, y, rect, titleHeight, allowCenter) {
    const localX = x - rect.x,
        localY = y - rect.y;
    const edgeX = Math.min(88, rect.width * 0.27);
    const edgeY = Math.min(76, rect.height * 0.27);
    if (
        allowCenter &&
        localY <= Math.min(titleHeight, rect.height * 0.18) &&
        localX > edgeX &&
        localX < rect.width - edgeX
    )
        return 'swap';
    const distances = [
        { zone: 'left', value: localX / Math.max(1, edgeX) },
        { zone: 'right', value: (rect.width - localX) / Math.max(1, edgeX) },
        { zone: 'top', value: localY / Math.max(1, edgeY) },
        { zone: 'bottom', value: (rect.height - localY) / Math.max(1, edgeY) }
    ];
    distances.sort((first, second) => first.value - second.value);
    return distances[0].value <= 1 || !allowCenter
        ? distances[0].zone
        : 'center';
}

export function preview(zone, rect, root) {
    const x = rect.x,
        y = rect.y,
        w = rect.width,
        h = rect.height;
    if (zone === 'left')
        return { x, y, width: w * (root ? 0.28 : 0.5), height: h };
    if (zone === 'right')
        return {
            x: x + w * (root ? 0.66 : 0.5),
            y,
            width: w * (root ? 0.34 : 0.5),
            height: h
        };
    if (zone === 'top')
        return { x, y, width: w, height: h * (root ? 0.28 : 0.5) };
    if (zone === 'bottom')
        return {
            x,
            y: y + h * (root ? 0.7 : 0.5),
            width: w,
            height: h * (root ? 0.3 : 0.5)
        };
    return zone === 'center' || zone === 'swap'
        ? rect
        : { x: 0, y: 0, width: 0, height: 0 };
}
