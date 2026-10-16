import { node, rect } from '../core/frame.mjs';
import { layout } from '../core/foundation.mjs';

// The shell places hosts; their existing owners retain drafts, routing and persistence.
export function describe(width, height, compact = false) {
    const toolbar = Math.min(height, layout.appBarHeight);
    const rail = compact ? 0 : Math.min(width, layout.sectionRailWidth);
    const body = Math.max(0, height - toolbar);
    return {
        width,
        height,
        compact,
        grid: {
            areas: compact ? '"bar" "main"' : '"bar bar" "rail main"',
            columns: compact ? 'minmax(0,1fr)' : rail + 'px minmax(0,1fr)',
            rows: toolbar + 'px minmax(0,1fr)'
        },
        nodes: [
            node('View', 'mainToolbarHost', rect(0, 0, width, toolbar), {
                view: 'toolbar'
            }),
            node('View', 'mainSectionRailHost', rect(0, toolbar, rail, body), {
                view: 'sections',
                visible: !compact
            }),
            node(
                'View',
                'mainDockHost',
                rect(rail, toolbar, Math.max(0, width - rail), body),
                { view: 'docks' }
            )
        ]
    };
}

export function positions(scene) {
    const result = {};
    for (const item of scene.nodes) result[item.id] = item;
    return result;
}
