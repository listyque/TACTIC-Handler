import { node, rect, label } from '../../core/frame.mjs';
import { controls } from '../../core/foundation.mjs';

// The primitive keeps the full hit target; the passive caption never steals its input.
export function captionedSwitch(id, bounds, properties) {
    const enabled = properties.enabled !== false,
        textX = controls.switch.width + controls.switch.spacing;
    return node('Box', id + 'Row', bounds, {
        children: [
            node(
                'Switch',
                id,
                rect(0, 0, bounds.width, bounds.height),
                properties
            ),
            label(
                id + 'Text',
                rect(
                    textX,
                    0,
                    Math.max(0, bounds.width - textX),
                    bounds.height
                ),
                properties.text,
                {
                    pointerTransparent: true,
                    color: enabled ? 'primaryText' : 'disabledText'
                }
            )
        ]
    });
}
