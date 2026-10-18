import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { phase } from './presentation.mjs';

export function rowText(kind, row, language) {
    if (kind === 'conflicts') return row.path || '';
    if (kind === 'taskFiles')
        return (
            row.path +
            ' · ' +
            translate(row.state, language) +
            ' · ' +
            ((row.received || 0) / 1048576).toFixed(1) +
            ' / ' +
            ((row.size || 0) / 1048576).toFixed(1) +
            ' MB'
        );
    return (
        phase(row.phase || row.state, language) +
        ' · ' +
        (row.files_done || 0) +
        ' · ' +
        (row.change || row.workspace || row.task)
    );
}

export function row(kind, row, width, selected, language) {
    const hasIcon = kind !== 'taskFiles',
        height = hasIcon ? 36 : 32,
        nodes = [];
    nodes.push(
        node('Box', 'workspaceDetailRowSurface', rect(0, 0, width, height), {
            background: selected ? 'selected' : 'transparent',
            radius: 8
        })
    );
    if (hasIcon)
        nodes.push(
            node(
                'Icon',
                'workspaceDetailRowIcon',
                rect(6, (height - 18) / 2, 18, 18),
                {
                    icon: kind === 'conflicts' ? 'warning' : 'cloud-upload',
                    color: 'action'
                }
            )
        );
    const x = hasIcon ? 32 : 6;
    nodes.push(
        label(
            'workspaceDetailRowText',
            rect(x, 0, Math.max(0, width - x - 6), height),
            rowText(kind, row, language),
            { elideMiddle: kind === 'conflicts' }
        )
    );
    return { nodes };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        conflicts = model.kind === 'conflicts',
        nodes = [];
    let y = 8;
    nodes.push(
        label(
            'workspaceDetailsTitle',
            rect(8, y, Math.max(0, width - 52), 32),
            model.title || tr(conflicts ? 'Conflicts' : 'Transfers'),
            { elideMiddle: true }
        )
    );
    if (model.native)
        nodes.push(
            button(
                'workspaceDetailsMenu',
                rect(Math.max(8, width - 36), y + 2, 28, 28),
                tr('Detail actions'),
                'more_vert',
                { type: 'menu' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    y += 36;
    if (conflicts) {
        const w = Math.min(160, Math.max(0, (width - 20) / 2));
        for (const [index, title] of ['Unresolved', 'Resolved'].entries())
            nodes.push(
                button(
                    'workspaceConflicts_' + index,
                    rect(8 + index * (w + 4), y, w, 36),
                    tr(title),
                    '',
                    { type: 'resolved', value: !!index },
                    true,
                    { tab: true, selected: !!model.showResolved === !!index }
                )
            );
        y += 40;
    }
    const preview = !!model.preview,
        tasks = !conflicts;
    const count = 1 + Number(tasks) + Number(preview),
        bodyWidth = Math.max(0, (width - 16 - (count - 1) * 8) / count),
        bodyHeight = Math.max(0, height - y - 8);
    nodes.push(
        node(
            'View',
            'workspaceDetailsListPort',
            rect(8, y, bodyWidth, bodyHeight),
            { view: 'rows', label: tr(conflicts ? 'Conflicts' : 'Transfers') }
        )
    );
    if (tasks) {
        const x = 16 + bodyWidth,
            errorHeight = model.taskError ? 48 : 0,
            moreHeight = model.after ? 40 : 0;
        if (model.taskError)
            nodes.push(
                label(
                    'workspaceTaskError',
                    rect(x, y, bodyWidth, errorHeight),
                    model.taskError,
                    { wrap: true, color: 'error' }
                )
            );
        nodes.push(
            node(
                'View',
                'workspaceTaskFilesPort',
                rect(
                    x,
                    y + errorHeight,
                    bodyWidth,
                    Math.max(0, bodyHeight - errorHeight - moreHeight)
                ),
                { view: 'taskFiles' }
            )
        );
        if (model.after)
            nodes.push(
                button(
                    'workspaceTaskFilesMore',
                    rect(x, y + bodyHeight - 36, bodyWidth, 36),
                    tr('Next files'),
                    'chevron-right',
                    { type: 'more' },
                    !model.busy
                )
            );
    }
    if (preview)
        nodes.push(
            node(
                'Area',
                'workspaceDetailsPreview',
                rect(
                    8 + (count - 1) * (bodyWidth + 8),
                    y,
                    bodyWidth,
                    bodyHeight
                ),
                {
                    text: model.preview,
                    readOnly: true,
                    label: tr('File preview')
                }
            )
        );
    return { nodes };
}
