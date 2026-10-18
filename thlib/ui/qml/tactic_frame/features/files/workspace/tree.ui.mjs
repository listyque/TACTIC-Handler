import { node, rect } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { metrics } from '../../../core/foundation.mjs';

export function describe(model, width, height, language) {
    const nodes = [],
        inner = Math.max(0, width - 16);
    let y = 8;
    if (model.native) {
        nodes.push(
            node(
                'View',
                'workspaceTreeNavigationPort',
                rect(8, y, inner, model.navigationHeight || 0),
                { view: 'navigation' }
            )
        );
        y += (model.navigationHeight || 0) + 4;
        const controlHeight = metrics(model.style).controlHeight;
        nodes.push(
            node(
                'Segmented',
                'workspaceTreeMode',
                rect(8, y, inner, controlHeight),
                {
                    options: [
                        {
                            value: 'depot',
                            label: translate('Depot', language),
                            icon: 'database'
                        },
                        {
                            value: 'workspace',
                            label: translate('Workspace', language),
                            icon: 'desktop'
                        }
                    ],
                    value: model.treeView,
                    action: { type: 'treeView' }
                }
            )
        );
        y += controlHeight + 4;
    }
    const viewport = rect(8, y, inner, Math.max(0, height - y - 8));
    nodes.push(
        node('View', 'workspaceDepotTreePort', viewport, {
            view: 'depot',
            visible: !model.native || model.treeView === 'depot'
        })
    );
    if (model.native)
        nodes.push(
            node('View', 'workspaceLocalTreePort', viewport, {
                view: 'workspace',
                visible: model.treeView === 'workspace'
            })
        );
    return { nodes };
}
