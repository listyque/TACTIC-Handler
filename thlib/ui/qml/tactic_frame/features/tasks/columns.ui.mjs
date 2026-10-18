import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export function describe(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [
            label(
                'taskColumnsTitle',
                rect(0, 0, width, 24),
                tr('Task columns'),
                { fontRole: 'secondary', weight: 600 }
            )
        ];
    let y = 32;
    for (let index = 0; index < (model.columns || []).length; index++) {
        const record = model.columns[index],
            name = record.key,
            required = record.required || name === 'object',
            tail = width - 144;
        const children = [
            node(
                'CheckBox',
                'taskColumnVisible_' + name,
                rect(0, 3, Math.max(32, tail - 8), 32),
                {
                    text: tr(record.label),
                    label: tr(record.label),
                    checked: !!record.visible,
                    enabled: !required && !model.busy,
                    action: { type: 'visible', field: name }
                }
            ),
            node('View', 'taskColumnWidth_' + name, rect(tail, 3, 72, 32), {
                view: 'width',
                record,
                enabled: !model.busy,
                label: tr('Width of {column}', { column: tr(record.label) })
            }),
            button(
                'taskColumnLeft_' + name,
                rect(width - 68, 3, 32, 32),
                tr('Move column left'),
                'previous',
                { type: 'move', field: name, value: -1 },
                !model.busy && index > 0,
                { iconOnly: true, iconAction: true, iconSize: 17 }
            ),
            button(
                'taskColumnRight_' + name,
                rect(width - 32, 3, 32, 32),
                tr('Move column right'),
                'next',
                { type: 'move', field: name, value: 1 },
                !model.busy && index < model.columns.length - 1,
                { iconOnly: true, iconAction: true, iconSize: 17 }
            )
        ];
        nodes.push(
            node('Box', 'taskColumn_' + name, rect(0, y, width, 38), {
                role: 'group',
                label: tr(record.label),
                children
            })
        );
        y += 44;
    }
    nodes.push(
        button(
            'taskColumnReset',
            rect(0, y, width, 32),
            tr('Reset task columns'),
            'undo',
            { type: 'reset' },
            !model.busy
        )
    );
    y += 40;
    if (model.configure) {
        nodes.push(
            button(
                'taskColumnConfigure',
                rect(0, y, width, 32),
                tr('Configure columns'),
                'view-column',
                { type: 'configure' },
                !model.busy
            )
        );
        y += 40;
    }
    return { nodes, height: y };
}
