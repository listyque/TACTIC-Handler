import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

function actions(
    width,
    height,
    language,
    reject,
    accept,
    busy,
    prefix,
    canAccept = true
) {
    const tr = (text) => translate(text, language),
        stacked = width < 360,
        footer = stacked ? 90 : 44,
        buttonWidth = stacked ? width : (width - 8) / 2;
    return {
        height: footer,
        nodes: [
            button(
                prefix + 'Cancel',
                rect(0, height - footer, buttonWidth, 38),
                tr(reject),
                '',
                { type: 'reject' },
                !busy
            ),
            button(
                prefix + 'Accept',
                rect(
                    stacked ? 0 : buttonWidth + 8,
                    height - footer + (stacked ? 46 : 0),
                    buttonWidth,
                    38
                ),
                tr(accept),
                '',
                { type: 'accept' },
                !busy && canAccept,
                { highlighted: true }
            )
        ]
    };
}

export function team(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        path = String(model.code || '') + ' → ' + String(model.path || ''),
        warning = tr(
            'This affects every TACTIC client. Confirm only if the server can access this folder.'
        ),
        pathHeight = Math.max(36, captionHeight(path, inner) * 1.2 + 18),
        warningHeight = Math.max(54, captionHeight(warning, inner) * 1.2),
        footer = actions(
            width,
            height,
            language,
            'Cancel',
            'Update server path',
            !!model.busy,
            'repositoryTeam',
            !model.changed
        ),
        noticeHeight = model.changed ? 64 : 0,
        body = [
            label(
                'repositoryTeamMessage',
                rect(0, noticeHeight, inner, 40),
                tr("TACTIC's server-wide repository path will be set to:"),
                { wrap: true }
            ),
            label(
                'repositoryTeamPath',
                rect(0, noticeHeight + 48, inner, pathHeight),
                path,
                {
                    wrap: true,
                    wrapAnywhere: true,
                    monospace: true,
                    toolTip: path
                }
            ),
            label(
                'repositoryTeamWarning',
                rect(0, noticeHeight + 60 + pathHeight, inner, warningHeight),
                warning,
                { wrap: true }
            )
        ];
    if (model.changed)
        body.unshift(
            label(
                'repositoryTeamChanged',
                rect(0, 0, inner, 56),
                tr(
                    'Repository changed. Close this dialog and review the current path before confirming again.'
                ),
                { color: 'error', role: 'alert', wrap: true }
            )
        );
    return {
        nodes: [
            node(
                'Scroll',
                'repositoryTeamDetails',
                rect(0, 0, width, Math.max(0, height - footer.height - 8)),
                {
                    scrollbarId: 'repositoryTeamScrollBar',
                    contentHeight:
                        noticeHeight + 60 + pathHeight + warningHeight,
                    children: body
                }
            )
        ].concat(footer.nodes)
    };
}

export function setup(model, width, height, language) {
    const tr = (text) => translate(text, language),
        textX = width < 340 ? 0 : 60,
        inner = Math.max(0, width - textX - 16),
        heading = tr('Repository storage is not configured'),
        message = tr(
            'TACTIC-Handler needs a repository path for snapshots, previews, check-in, check-out and synchronization. Configure it now to avoid missing files.'
        ),
        headingHeight = Math.max(28, captionHeight(heading, inner) * 1.4),
        textHeight = Math.max(72, captionHeight(message, inner) * 1.2),
        footer = actions(
            width,
            height,
            language,
            'Later',
            'Configure repositories',
            false,
            'repositorySetup'
        ),
        children = [
            label(
                'repositorySetupHeading',
                rect(textX, 0, inner, headingHeight),
                heading,
                { wrap: true, fontRole: 'section', weight: 600 }
            ),
            label(
                'repositorySetupMessage',
                rect(textX, headingHeight + 6, inner, textHeight),
                message,
                { wrap: true, color: 'secondaryText' }
            )
        ];
    if (textX)
        children.push(
            node('Box', 'repositorySetupIconPanel', rect(0, 0, 44, 44), {
                background: 'errorContainer',
                radius: 14,
                children: [
                    node('Icon', 'repositorySetupIcon', rect(11, 11, 22, 22), {
                        icon: 'database',
                        color: 'error'
                    })
                ]
            })
        );
    return {
        nodes: [
            node(
                'Scroll',
                'repositorySetupContent',
                rect(0, 0, width, Math.max(0, height - footer.height - 8)),
                {
                    scrollbarId: 'repositorySetupScrollBar',
                    contentHeight: headingHeight + 6 + textHeight,
                    children
                }
            )
        ].concat(footer.nodes)
    };
}
