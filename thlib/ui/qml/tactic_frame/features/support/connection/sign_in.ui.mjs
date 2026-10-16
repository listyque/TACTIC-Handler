import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function canSubmit(model) {
    return (
        !model.busy &&
        model.ready !== false &&
        !!String(model.login || '').trim() &&
        !!model.password
    );
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        margin = 18;
    const inner = Math.max(0, width - margin * 2),
        contentHeight = Math.max(376, height);
    const bodyWidth = Math.max(0, inner - 48),
        nodes = [
            node('Box', 'signInHeading', rect(0, 0, inner, 86), {
                background: 'panelRaised',
                radius: 28,
                children: [
                    node('Icon', 'signInIcon', rect(22, 23, 34, 34), {
                        icon: 'key',
                        color: 'action'
                    }),
                    label(
                        'signInTitle',
                        rect(68, 15, inner - (model.cancelable ? 122 : 88), 28),
                        text('Sign in to TACTIC'),
                        { fontRole: 'title', weight: 600 }
                    ),
                    label(
                        'signInServer',
                        rect(68, 47, inner - (model.cancelable ? 122 : 88), 22),
                        model.server || model.product || '',
                        muted
                    )
                ]
            })
        ];
    if (model.cancelable)
        nodes[0].children.push(
            button(
                'signInClose',
                rect(inner - 46, 24, 32, 32),
                text('Cancel'),
                'close',
                { type: 'cancel' },
                !model.busy,
                { iconOnly: true }
            )
        );
    let y = 104;
    if (model.ready === false) {
        nodes.push(
            label(
                'signInSetup',
                rect(24, y, bodyWidth, 80),
                text(
                    'The server has not been set up yet. Initialize its database and set an administrator password.'
                ),
                { wrap: true, color: 'yellow', role: 'status' }
            )
        );
        y += 88;
    }
    for (const [key, name, password] of [
        ['login', 'Login', false],
        ['password', 'Password', true]
    ]) {
        nodes.push(
            node('Field', 'signIn_' + key, rect(24, y, bodyWidth, 44), {
                text: model[key] || '',
                label: text(name),
                placeholder: text(name),
                password,
                autocomplete: password ? 'current-password' : 'username',
                name: key,
                enabled: !model.busy,
                keys: { Return: { type: 'submit' }, Enter: { type: 'submit' } },
                action: { type: key }
            })
        );
        y += 54;
    }
    if (model.error) {
        nodes.push(
            label(
                'signInError',
                rect(24, y, bodyWidth, 64),
                text(model.error),
                { wrap: true, color: 'red', role: 'alert' }
            )
        );
        y += 72;
    }
    const footerY = Math.max(y + 6, contentHeight - 110),
        actionWidth = language === 'ru' ? 174 : 158;
    if (model.canHelp)
        nodes.push(
            button(
                'signInHelp',
                rect(24, footerY, 36, 38),
                text('Help'),
                'help',
                { type: 'help' },
                true,
                { iconOnly: true }
            )
        );
    if (model.cancelable)
        nodes.push(
            button(
                'signInCancel',
                rect(
                    model.canHelp ? 68 : 24,
                    footerY,
                    Math.max(
                        72,
                        bodyWidth - actionWidth - 8 - (model.canHelp ? 44 : 0)
                    ),
                    38
                ),
                text('Cancel'),
                '',
                { type: 'cancel' },
                !model.busy
            )
        );
    nodes.push(
        button(
            'signInSubmit',
            rect(inner - 24 - actionWidth, footerY, actionWidth, 38),
            text(
                model.busy
                    ? model.nativeTicket
                        ? 'Generating…'
                        : 'Signing in…'
                    : model.nativeTicket
                      ? 'Generate ticket'
                      : 'Sign in'
            ),
            'key',
            { type: 'submit' },
            canSubmit(model),
            { highlighted: true }
        )
    );
    if (model.version)
        nodes.push(
            label(
                'signInVersion',
                rect(24, footerY + 44, bodyWidth, 20),
                'v' + model.version,
                { fontRole: 'caption', color: 'secondaryText', align: 'right' }
            )
        );
    const surfaceHeight = Math.max(contentHeight - margin * 2, footerY + 70);
    return {
        contentHeight: surfaceHeight + margin * 2,
        nodes: [
            node('Scroll', 'signInBody', rect(0, 0, width, height), {
                contentHeight: surfaceHeight + margin * 2,
                children: [
                    node(
                        'Box',
                        'signInSurface',
                        rect(margin, margin, inner, surfaceHeight),
                        {
                            background: 'panel',
                            border: 'outlineVariant',
                            radius: 28,
                            children: nodes
                        }
                    )
                ]
            })
        ]
    };
}
