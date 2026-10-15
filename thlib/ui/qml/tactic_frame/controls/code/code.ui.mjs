import { node, rect, label, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export function toolbar(model, width, language, revision) {
    const tr = (text) => translate(text, language),
        nodes = [],
        actions = [
            ['undo', 'Undo', 'undo', !model.readOnly && model.canUndo],
            ['redo', 'Redo', 'redo', !model.readOnly && model.canRedo],
            ['cut', 'Cut', 'content-cut', !model.readOnly && model.canCopy],
            ['copy', 'Copy', 'copy', model.canCopy],
            ['paste', 'Paste', 'content-paste', !model.readOnly],
            ['find', 'Find', 'search', true],
            ['replace', 'Replace', 'edit', !model.readOnly],
            ['help', 'Code editor help', 'help', true]
        ],
        compact = width < 620;
    let x = 0;
    if (compact) {
        const size = Math.max(110, width * 0.43);
        nodes.push(
            node('Choice', 'frameCodeCommands', rect(0, 0, size, 30), {
                label: tr('Source'),
                value: '',
                resetKey: revision,
                options: [
                    {
                        value: '',
                        label: tr('Source')
                    }
                ].concat(
                    actions.map((row) => ({
                        value: row[0],
                        label: tr(row[1]),
                        disabled: !row[3]
                    }))
                ),
                action: {
                    type: 'command'
                }
            })
        );
        x = size + 6;
    } else {
        nodes.push(
            label('frameCodeSource', rect(0, 0, 58, 30), tr('Source'), muted)
        );
        x = 60;
        for (const row of actions) {
            nodes.push(
                node('Button', 'frameCode_' + row[0], rect(x, 0, 28, 28), {
                    text: tr(row[1]),
                    icon: row[2],
                    iconOnly: true,
                    enabled: row[3],
                    action: {
                        type: 'command',
                        value: row[0]
                    }
                })
            );
            x += 30;
        }
    }
    const fontWidth = compact ? Math.min(90, width * 0.23) : 100;
    nodes.push(
        node('Choice', 'frameCodeFontSize', rect(x, 0, fontWidth, 30), {
            label: tr('Text size'),
            value: model.fontSize,
            options: [8, 9.25, 11, 13, 15].map((value, index) => ({
                value,
                label: tr(
                    ['Small', 'Normal', 'Medium', 'Large', 'Extra large'][index]
                )
            })),
            action: {
                type: 'font'
            }
        })
    );
    x += fontWidth + 6;
    const history = [];
    for (let index = model.historyCount - 1; index >= 0; index--) {
        const distance = model.historyIndex - index;
        history.push({
            value: index,
            label:
                distance === 0
                    ? tr('Current state')
                    : String(Math.abs(distance)) +
                      ' ' +
                      tr(distance > 0 ? 'edits back' : 'edits forward')
        });
    }
    nodes.push(
        node(
            'Choice',
            'frameCodeHistory',
            rect(x, 0, Math.max(1, width - x), 30),
            {
                label: tr('Edit history'),
                value: model.historyIndex,
                options: history,
                enabled: !model.readOnly && model.historyCount > 1,
                action: {
                    type: 'history'
                }
            }
        )
    );
    return {
        nodes
    };
}
