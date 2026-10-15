import { node, rect } from '../core/frame.mjs';
import { layout } from '../core/foundation.mjs';

export const dimensions = {
    controlExtent: 36,
    surfaceExtent: 32,
    projectPreviewExtent: 28,
    projectPreviewRadius: 6
};

// Each host supplies a house control for these named positions, never a second layout.
export function describe(model) {
    const width = Math.max(0, model.width);
    const compact = !!model.compact;
    const height = layout.appBarHeight;
    const extent = dimensions.controlExtent;
    const gap = 2;
    const left = compact ? 4 : 8;
    const right = compact ? 4 : 12;
    const connectionExpanded = width >= 900;
    const dccExpanded = width >= 1280;
    const compactProgress = width < 760;
    const progressReveal = Math.max(0, Math.min(1, model.progressReveal || 0));
    const activityWidth =
        extent + (compactProgress ? 0 : 220 - extent) * progressReveal;
    const trailing = [
        ['mainActivity', activityWidth, !compact],
        ['mainConnection', connectionExpanded ? 106 : extent, !compact],
        [
            'mainDcc',
            dccExpanded ? 238 : width < 720 ? extent : 104,
            !!model.dccClient && !compact
        ],
        ['mainQueue', extent, !compact],
        ['mainFeed', extent, !compact],
        ['mainAppearance', extent, !compact],
        ['mainSettings', extent, true],
        ['mainAccount', extent, true]
    ];
    const visible = trailing.filter((item) => item[2]);
    const trailingWidth =
        visible.reduce((sum, item) => sum + item[1], 0) +
        (visible.length - 1) * gap;
    const projectWidth = compact
        ? Math.max(0, width - left - right - extent - trailingWidth - gap * 3)
        : Math.min(260, Math.max(width < 640 ? 132 : 176, width * 0.21));
    const nodes = [
        node(
            'View',
            'mainNavigation',
            rect(left, (height - extent) / 2, extent, extent),
            { view: 'navigation' }
        ),
        node(
            'View',
            'mainProject',
            rect(
                left + extent + gap,
                (height - extent) / 2,
                projectWidth,
                extent
            ),
            { view: 'project' }
        )
    ];
    let position = Math.max(
        left + extent + projectWidth + gap * 2,
        width - right - trailingWidth
    );
    for (const [id, itemWidth, visible] of trailing) {
        nodes.push(
            node(
                'View',
                id,
                rect(position, (height - extent) / 2, itemWidth, extent),
                { view: id.slice(4), visible }
            )
        );
        if (visible) position += itemWidth + gap;
    }
    return {
        width,
        height,
        nodes,
        dimensions,
        connectionExpanded,
        dccExpanded,
        compactProgress
    };
}

export function positions(scene) {
    const result = {};
    for (const item of scene.nodes) result[item.id] = item;
    return result;
}
