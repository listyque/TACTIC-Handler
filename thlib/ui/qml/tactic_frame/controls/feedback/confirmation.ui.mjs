import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// The existing modal host owns Escape, focus return and command execution.
export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 380,
        margin = 16,
        inner = width - margin * 2;
    const rows = compact ? 2 : 1,
        buttonHeight = 38,
        gap = 8,
        footer = rows * (buttonHeight + gap) + margin;
    const nodes = [
        label(
            'confirmationMessage',
            rect(margin, 12, inner, Math.max(40, height - footer - 20)),
            model.message,
            { wrap: true }
        )
    ];
    const actions = [
        {
            id: model.rejectId || 'confirmationReject',
            text: model.reject || 'Cancel',
            type: 'reject'
        },
        {
            id: model.acceptId || 'confirmationAccept',
            text: model.accept || 'Continue',
            type: 'accept'
        }
    ];
    actions.forEach((action, index) =>
        nodes.push(
            button(
                action.id,
                rect(
                    margin + (compact ? 0 : (index * (inner + gap)) / 2),
                    height -
                        footer +
                        (compact ? index * (buttonHeight + gap) : 0),
                    compact ? inner : (inner - gap) / 2,
                    buttonHeight
                ),
                text(action.text),
                '',
                { type: action.type },
                !model.busy,
                {
                    highlighted: index === 1 && !model.destructive,
                    destructive: index === 1 && model.destructive
                }
            )
        )
    );
    return { nodes };
}
