import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { parse } from '../../controls/forms/calendar.mjs';

export function describe(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let y = 0;
    function field(id, title, value, kind, enabled, field) {
        nodes.push(
            label(id + 'Title', rect(0, y, width, 20), tr(title), {
                fontRole: 'body'
            })
        );
        nodes.push(
            node(kind, id, rect(0, y + 25, width, 32), {
                label: tr(title),
                text: String(value == null ? '' : value),
                includeTime: false,
                allowClear: false,
                enabled: !model.busy && enabled,
                action: { type: 'change', field },
                selectOnFocus: true
            })
        );
        y += 68;
    }
    field(
        'ganttEditorStart',
        'Start date',
        model.start,
        'DateChoice',
        model.dates,
        'start'
    );
    field(
        'ganttEditorDuration',
        model.workingDays
            ? 'Duration in working days'
            : 'Duration in calendar days',
        model.duration,
        'Field',
        model.dates,
        'duration'
    );
    nodes.push(
        node('CheckBox', 'ganttEditorWorking', rect(0, y, width, 28), {
            text: tr('Working days only'),
            checked: !!model.workingDays,
            enabled: !model.busy && model.dates,
            action: { type: 'working' }
        })
    );
    y += 36;
    if (model.progressField)
        field(
            'ganttEditorProgress',
            'Progress',
            model.progress,
            'Field',
            true,
            'progress'
        );
    if (model.multi) {
        nodes.push(
            node('CheckBox', 'ganttEditorMove', rect(0, y, width, 28), {
                text: tr('Move selected tasks together'),
                checked: !!model.move,
                enabled: !model.busy && model.dates,
                action: { type: 'change', field: 'move' }
            })
        );
        y += 36;
    }
    if (model.error) {
        nodes.push(
            label('ganttEditorError', rect(0, y, width, 36), tr(model.error), {
                fontRole: 'caption',
                color: 'error',
                wrap: true
            })
        );
        y += 44;
    }
    const valid =
        (!model.dates ||
            (!!parse(model.start, false) &&
                Number.isInteger(Number(model.duration)) &&
                Number(model.duration) >= 1 &&
                Number(model.duration) <= 3650)) &&
        (!model.progressField ||
            (Number.isFinite(Number(model.progress)) &&
                Number(model.progress) >= 0 &&
                Number(model.progress) <= 100));
    nodes.push(
        button(
            'ganttEditorCancel',
            rect(Math.max(0, width - 244), y, 84, 32),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'ganttEditorApply',
            rect(Math.max(0, width - 152), y, 152, 32),
            tr('Apply to draft'),
            'check',
            { type: 'apply' },
            !model.busy && valid && (model.dates || !!model.progressField),
            { highlighted: true }
        )
    );
    for (const field of nodes.filter((node) => node.kind === 'Field'))
        field.keys = valid && !model.busy ? { Enter: { type: 'apply' } } : {};
    return { nodes, height: y + 40 };
}
