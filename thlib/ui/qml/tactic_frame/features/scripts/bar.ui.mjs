import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function layout(width, height, dcc) {
    const y = (height - 24) / 2;
    return {
        modes: rect(2, (height - 46) / 2, 26, 46),
        buttons: rect(31, 0, width - 31 - 6 - 27 - 24 - (dcc ? 27 : 0), height),
        edit: rect(width - 30, y, 24, 24),
        export: rect(width - 57, y, 24, 24),
        busy: rect(width - 54 - (dcc ? 27 : 0), (height - 18) / 2, 18, 18)
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        bounds = layout(width, height, model.dcc);
    const nodes = [
        node('Box', 'scriptShelfMode', bounds.modes, {
            background: 'surfaceContainerHigh',
            border: 'outlineVariant',
            borderWidth: 1,
            radius: 10,
            children: ['personal', 'shared'].map((value, index) =>
                node(
                    'Button',
                    'scriptShelfMode_' + value,
                    rect(2, 2 + index * 21, 22, 21),
                    {
                        text: tr(
                            value === 'personal' ? 'My shelf' : 'Shared shelf'
                        ),
                        icon: value === 'personal' ? 'user' : 'users',
                        iconSize: 13,
                        iconOnly: true,
                        radio: true,
                        selected: value === model.mode,
                        enabled:
                            value !== 'personal' || model.hasLogin !== false,
                        action: { type: 'mode', value }
                    }
                )
            )
        }),
        button(
            'editScriptShelfButton',
            bounds.edit,
            tr('Edit script shelf'),
            model.error ? 'warning' : 'edit',
            { type: 'edit' },
            !model.busy && !model.running,
            {
                iconOnly: true,
                iconColor: model.error ? 'error' : 'primaryText',
                toolTip: model.error || tr('Edit script shelf')
            }
        )
    ];
    nodes.push(
        button(
            'exportDccShelfButton',
            bounds.export,
            tr('Create this shelf in the selected DCC'),
            model.exportBusy ? 'hourglass-empty' : 'upload',
            { type: 'export' },
            !model.exportBusy,
            { iconOnly: true, visible: !!model.dcc }
        )
    );
    if (model.busy || model.running)
        nodes.push(
            node('Icon', 'scriptShelfBusy', bounds.busy, {
                icon: 'hourglass-empty',
                color: 'action'
            })
        );
    else if (!model.count)
        nodes.push(
            label(
                'scriptShelfEmpty',
                bounds.buttons,
                tr('No shelf buttons'),
                muted
            )
        );
    return { nodes };
}

export function actionHeight(count, width) {
    return count * 44 - 4 > width ? 36 : 40;
}

export function action(record, running, language, height) {
    height = height === undefined ? 40 : height;
    const enabled = record.available && !running;
    const description = record.available
        ? record.description || record.title
        : translate('Script is unavailable: ', language) + record.script;
    return {
        nodes: [
            node(
                'Action',
                'scriptShelfAction_' + record.buttonId,
                rect(0, 0, 40, height),
                {
                    text: record.title,
                    description,
                    toolTip: description,
                    enabled,
                    normalColor: 'transparent',
                    radius: 10,
                    action: { type: 'run', buttonId: record.buttonId },
                    children: [
                        node(
                            'Icon',
                            'scriptShelfActionIcon',
                            rect(12, 1, 16, 16),
                            {
                                icon: record.running
                                    ? 'hourglass-empty'
                                    : record.iconName,
                                color: enabled ? 'primaryText' : 'disabledText'
                            }
                        ),
                        label(
                            'scriptShelfActionLabel',
                            rect(0, height - 16, 40, 15),
                            record.title,
                            {
                                fontRole: 'caption',
                                align: 'center',
                                color: enabled ? 'primaryText' : 'disabledText'
                            }
                        )
                    ]
                }
            )
        ]
    };
}
