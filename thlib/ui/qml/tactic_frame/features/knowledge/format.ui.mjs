import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { aliases, semanticName } from '../../core/icons.mjs';

export const textActions = [
    { action: 'bold', icon: 'bold', tip: 'Bold · Ctrl+B', minimumWidth: 0 },
    {
        action: 'italic',
        icon: 'italic',
        tip: 'Italic · Ctrl+I',
        minimumWidth: 640
    },
    {
        action: 'underline',
        icon: 'underline',
        tip: 'Underline',
        minimumWidth: 650
    },
    {
        action: 'strike',
        icon: 'strikethrough',
        tip: 'Strikethrough',
        minimumWidth: 690
    },
    {
        action: 'small-text',
        icon: 'small-text',
        tip: 'Small text',
        minimumWidth: 730
    }
];
export const insertActions = [
    {
        action: 'link',
        icon: 'link',
        tip: 'Insert link · Ctrl+K',
        minimumWidth: 0
    },
    {
        action: 'attach',
        icon: 'attachments-editor',
        tip: 'Show attached files',
        minimumWidth: 640
    },
    {
        action: 'quote',
        icon: 'format-quote',
        tip: 'Insert quote',
        minimumWidth: 770
    },
    {
        action: 'code-block',
        icon: 'code-block',
        tip: 'Insert code block',
        minimumWidth: 810
    },
    {
        action: 'checklist',
        icon: 'checkbox-multiple-marked-outline',
        tip: 'Checklist',
        minimumWidth: 850
    }
];
export const historyActions = [
    { action: 'undo', icon: 'undo', tip: 'Undo' },
    { action: 'redo', icon: 'redo', tip: 'Redo' }
];
export const alignmentActions = ['left', 'center', 'right'].map((action) => ({
    action,
    icon: 'align-' + action,
    tip: 'Align ' + action
}));

export function describe(model, width, language) {
    if (width <= 0) return { nodes: [], height: 32 };
    const tr = (text) => translate(text, language),
        nodes = [];
    const visual = model.mode !== 'markdown',
        modeWidth = width < 460 ? 76 : 208;
    let x = 0,
        y = 0;
    function room(size) {
        if (x + size > width && x > 0) {
            x = 0;
            y += 37;
        }
    }
    function action(id, text, icon, type, checked, shown) {
        const visible = visual && shown !== false;
        if (visible) room(32);
        const name = semanticName(icon);
        nodes.push(
            button(
                id,
                rect(x, y, 32, 32),
                tr(text),
                'fontawesome-solid:' + (aliases[name] || name),
                { type },
                !model.disabled,
                {
                    visible,
                    iconOnly: true,
                    tonal: !!checked,
                    pressAction:
                        ['lists', 'overflow'].indexOf(type) >= 0
                            ? { type, pressed: true }
                            : undefined
                }
            )
        );
        if (visible) x += 35;
    }
    function separator(name) {
        if (visual) room(7);
        nodes.push(
            node(
                'Box',
                'knowledgeToolbarSeparator-' + name,
                rect(x, y + 5, 1, 22),
                { visible: visual, background: 'outlineVariant', radius: 0 }
            )
        );
        if (visual) x += 7;
    }
    for (const record of historyActions)
        action(
            'knowledgeToolbarAction-' + record.action,
            record.tip,
            record.icon,
            record.action
        );
    separator('history');
    if (visual) room(32);
    nodes.push(
        node('Action', 'knowledgeTextStyle', rect(x, y, 32, 32), {
            text: tr('Text style'),
            visible: visual,
            enabled: !model.disabled,
            selected: !!model.blockStyle,
            normalColor: 'transparent',
            selectedColor: 'selected',
            action: { type: 'textStyle' },
            pressAction: { type: 'textStyle', pressed: true },
            children: [
                label('knowledgeTextStyleLabel', rect(0, 0, 32, 32), 'Aa', {
                    weight: 600,
                    align: 'center'
                })
            ]
        })
    );
    if (visual) x += 35;
    for (const record of textActions)
        action(
            'knowledgeToolbarAction-' + record.action,
            record.tip,
            record.icon,
            record.action,
            model.checked?.[record.action],
            width >= record.minimumWidth
        );
    separator('text');
    for (const record of insertActions)
        action(
            'knowledgeToolbarAction-' + record.action,
            record.tip,
            record.icon,
            record.action,
            model.checked?.[record.action],
            width >= record.minimumWidth
        );
    action('knowledgeListStyle', 'Lists', 'list-ul', 'lists', model.listStyle);
    action(
        'knowledgeToolbarAction-table',
        'Insert table',
        'table-view',
        'table',
        false,
        width >= 760
    );
    action(
        'knowledgeToolbarAction-divider',
        'Insert divider',
        'divider',
        'divider'
    );
    separator('blocks');
    for (const record of alignmentActions)
        action(
            'knowledgeToolbarAction-' + record.action,
            record.tip,
            record.icon,
            record.action,
            model.checked?.[record.action],
            width >= 1000
        );
    action(
        'knowledgeToolbarOverflow',
        'More formatting actions',
        'more',
        'overflow'
    );
    separator('mode');
    const modeY = x + modeWidth > width ? y + 37 : y;
    nodes.push(
        node(
            'Segmented',
            'knowledgeContentMode',
            rect(Math.max(0, width - modeWidth), modeY, modeWidth, 32),
            {
                label: tr('Editor mode'),
                value: model.mode || 'visual',
                iconOnly: width < 460,
                options: [
                    { value: 'visual', label: tr('Visual'), icon: 'edit' },
                    { value: 'markdown', label: 'Markdown', icon: 'code' }
                ],
                enabled: !model.disabled,
                action: { type: 'mode' }
            }
        )
    );
    return { nodes, height: modeY + 32 };
}
