import { label, node, rect } from '../core/frame.mjs';
import { navigate } from '../controls/lists/tree.ui.mjs';

export const dimensions = {
    maximumWidth: 360,
    minimumWidth: 280,
    edgeGap: 56,
    exitDistance: 120
};

// The workspace owns project data; hosts supply real buttons, scroll and input.
export function describe(model, translate = (text) => text) {
    const width = Math.min(
        Math.max(0, model.width),
        dimensions.maximumWidth,
        Math.max(dimensions.minimumWidth, model.width - dimensions.edgeGap)
    );
    const height = Math.max(0, model.height);
    const closeX = width - 48;
    const editX = closeX - 42;
    const titleRight = (model.editable ? editX : closeX) - 12;
    const contentY = 85 + Math.max(0, model.extraHeight || 0);
    const nodes = [
        node('Box', 'navigationSurface', rect(0, 0, width, height), {
            background: 'panelRaised'
        }),
        label(
            'navigationTitle',
            rect(20, 17, titleRight - 20, 24),
            translate('Navigation'),
            { fontRole: 'display', weight: 600 }
        ),
        label(
            'navigationSubtitle',
            rect(20, 42, titleRight - 20, 17),
            translate('Project workspace'),
            { fontRole: 'body', color: 'secondaryText' }
        ),
        node('View', 'navigationEdit', rect(editX, 8, 40, 40), {
            view: 'edit',
            visible: !!model.editable
        }),
        node('View', 'navigationClose', rect(closeX, 8, 40, 40), {
            view: 'close'
        }),
        node('Box', 'navigationDivider', rect(16, 76, width - 32, 1), {
            background: 'separator'
        }),
        node(
            'View',
            'navigationContent',
            rect(0, contentY, width, height - contentY - 8),
            { view: 'content' }
        )
    ];
    return { width, height, nodes };
}

export function shouldClose(entered, pointer, x, right) {
    return (
        !!entered && pointer === 'mouse' && x > right + dimensions.exitDistance
    );
}

// Projection includes off-screen rows; recycled delegates cannot own navigation.
export function move(rows, id, key) {
    const available = rows.filter(
        (row) =>
            row.visible !== false &&
            row.enabled !== false &&
            row.kind !== 'separator'
    );
    if (
        ![
            'ArrowDown',
            'ArrowUp',
            'ArrowLeft',
            'ArrowRight',
            'Home',
            'End'
        ].includes(key)
    )
        return null;
    if (available.length && !available.some((row) => row.id === id))
        return {
            type: 'select',
            id: available[key === 'End' ? available.length - 1 : 0].id
        };
    return navigate(available, id, key);
}
