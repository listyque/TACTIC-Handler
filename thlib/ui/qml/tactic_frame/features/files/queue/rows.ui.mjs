import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { sourceIcon, extension, fileName } from '../file_values.mjs';
import { status, statusTitle } from './actions.ui.mjs';

export function operationRow(model, record, index, width, language) {
    const tr = (text, values) => translate(text, language, values),
        state = status(record.status),
        id = record.operationId,
        action = { type: 'select', index, key: id },
        textWidth = Math.max(0, width - 150),
        keys = {
            ArrowUp: {
                type: 'select',
                index: Math.max(0, index - 1),
                focus: true
            },
            ArrowDown: {
                type: 'select',
                index: Math.min(model.count - 1, index + 1),
                focus: true
            },
            Home: { type: 'select', index: 0, focus: true },
            End: { type: 'select', index: model.count - 1, focus: true }
        },
        children = [
            node('Action', 'commitQueueSelect_' + id, rect(0, 0, width, 68), {
                text: record.title,
                selected: record.selected,
                normalColor: 'surfaceContainerLow',
                selectedColor: 'selected',
                accent: state.color,
                rail: record.selected || record.status !== 'Prepared',
                radius: 12,
                action,
                keys,
                children: [
                    node(
                        'View',
                        'commitQueuePreview_' + id,
                        rect(42, 15, 38, 38),
                        {
                            view: 'preview',
                            sourceKey: id,
                            source: record.previewUrl || '',
                            icon: state.icon,
                            accent: state.color,
                            radius: 9
                        }
                    ),
                    label(
                        'commitQueueTitle_' + id,
                        rect(86, 7, textWidth, 19),
                        record.title,
                        { weight: 600, elideMiddle: true }
                    ),
                    label(
                        'commitQueueObject_' + id,
                        rect(86, 29, textWidth, 16),
                        record.objectTitle,
                        { fontRole: 'secondary', color: 'secondaryText' }
                    ),
                    label(
                        'commitQueueState_' + id,
                        rect(86, 47, textWidth, 15),
                        tr(statusTitle(record)) +
                            ' · ' +
                            tr('{count} files', { count: record.fileCount }) +
                            ' · ' +
                            (record.error ||
                                record.context ||
                                tr('No context')),
                        {
                            fontRole: 'caption',
                            color: record.error ? 'error' : state.color
                        }
                    )
                ]
            }),
            node('CheckBox', 'commitQueueCheck_' + id, rect(7, 20, 28, 28), {
                label: tr('Select operation for commit'),
                checked: !!record.checked,
                enabled:
                    record.status !== 'Running' &&
                    !model.busy &&
                    record.canCheck !== false,
                indicatorX: 4,
                action: { type: 'check', index, key: id }
            }),
            button(
                'commitQueueMenu_' + id,
                rect(width - 60, 20, 28, 28),
                tr('Operation actions'),
                'more',
                { type: 'operationMenu', index, key: id },
                true,
                { iconOnly: true, iconAction: true }
            ),
            button(
                'commitQueueRemove_' + id,
                rect(width - 30, 20, 28, 28),
                tr('Remove operation'),
                'close',
                { type: 'remove', index, key: id },
                !model.busy && record.status !== 'Running',
                { iconOnly: true, iconAction: true }
            )
        ];
    if (record.status === 'Running')
        children.push(
            node(
                'View',
                'commitQueueRowProgress_' + id,
                rect(9, 64, width - 18, 3),
                {
                    view: 'progress',
                    label: tr('Upload progress'),
                    value: record.progress || 0,
                    min: 0,
                    max: 1
                }
            )
        );
    return {
        nodes: [
            node('Box', 'commitQueueOperation_' + id, rect(0, 0, width, 68), {
                contextAction: { type: 'operationMenu', index, key: id },
                children
            })
        ]
    };
}

export function sourceRow(model, record, width, language) {
    const tr = (text) => translate(text, language),
        id = record.key,
        h = model.sourceTargets ? 43 : 32,
        textWidth = Math.max(0, width - 112),
        children = [
            node(
                'Box',
                'commitQueueSourceIconBox_' + id,
                rect(6, (h - 26) / 2, 26, 26),
                {
                    background: 'surfaceContainerHigh',
                    radius: 8,
                    children: [
                        node(
                            'Icon',
                            'commitQueueSourceIcon_' + id,
                            rect(5, 5, 16, 16),
                            { icon: sourceIcon(record.path), color: 'action' }
                        )
                    ]
                }
            ),
            label(
                'commitQueueSourceTitle_' + id,
                rect(
                    39,
                    record.target ? 2 : 0,
                    textWidth,
                    record.target ? 21 : h
                ),
                fileName(record.path),
                {
                    fontRole: 'secondary',
                    elideMiddle: true,
                    toolTip: record.path
                }
            ),
            label(
                'commitQueueSourceExtension_' + id,
                rect(width - 65, 0, 30, h),
                extension(record.path),
                {
                    fontRole: 'menuHeading',
                    color: 'secondaryText',
                    align: 'right'
                }
            ),
            button(
                'commitQueueSourceRemove_' + id,
                rect(width - 30, (h - 26) / 2, 26, 26),
                tr('Remove file from operation'),
                'close',
                {
                    type: 'removeFile',
                    operationId: model.record.operationId,
                    index: record.index,
                    preview: !!record.preview
                },
                !!record.canRemove && !model.busy,
                { iconOnly: true, iconAction: true, iconSize: 12 }
            )
        ];
    if (record.target)
        children.push(
            label(
                'commitQueueSourceTarget_' + id,
                rect(39, 23, textWidth, 16),
                record.target,
                {
                    fontRole: 'menuHeading',
                    color: 'secondaryText',
                    elideMiddle: true,
                    toolTip: record.target
                }
            )
        );
    return { nodes: children };
}
