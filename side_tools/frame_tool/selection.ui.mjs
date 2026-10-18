import {
    node,
    rect,
    label,
    button,
    muted
} from '../../thlib/ui/qml/tactic_frame/core/frame.mjs';
import { translate } from '../../thlib/ui/qml/tactic_frame/core/strings.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = width - 32;
    return {
        nodes: [
            label('exampleHeading', rect(16, 12, inner, 30), tr('Selection'), {
                fontRole: 'title'
            }),
            node('Field', 'exampleName', rect(16, 50, inner, 38), {
                label: tr('Name'),
                text: model.name,
                action: { type: 'name' }
            }),
            label(
                'exampleCount',
                rect(16, 96, inner, 24),
                tr('Selected') + ': ' + model.rows.length,
                muted
            ),
            node(
                'List',
                'exampleSelection',
                rect(16, 126, inner, height - 242),
                {
                    source: 'selection',
                    fields: ['id', 'title'],
                    keyField: 'id',
                    rowHeight: 38,
                    scrollbarId: 'exampleScrollBar'
                }
            ),
            label(
                'examplePreview',
                rect(16, height - 106, inner, 52),
                model.preview,
                { wrap: true, maxLines: 2 }
            ),
            button(
                'exampleClear',
                rect(16, height - 46, 110, 32),
                tr('Clear'),
                'delete',
                { type: 'clear' },
                !!model.rows.length
            ),
            button(
                'exampleBuild',
                rect(width - 156, height - 46, 140, 32),
                tr('Preview'),
                'visibility',
                { type: 'preview' },
                !!model.rows.length && !!model.name.trim(),
                { highlighted: true }
            )
        ]
    };
}

export function row(list, record) {
    return {
        nodes: [
            label(
                'exampleRow_' + record.id,
                rect(8, 0, Math.max(0, list.width - 32), 34),
                record.title
            )
        ]
    };
}
