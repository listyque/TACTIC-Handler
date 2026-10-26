import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Confirmation from '../../controls/feedback/confirmation.ui.mjs';

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 560;
    const nodes = [
        label(
            'templatesTitle',
            rect(20, 12, width - 200, 28),
            text('Manage templates'),
            { fontRole: 'title', weight: 600, role: 'heading' }
        ),
        button(
            'templatesHelp',
            rect(width - 86, 12, 32, 32),
            text('Project creation help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true }
        ),
        button(
            'templatesClose',
            rect(width - 48, 12, 32, 32),
            text('Close'),
            'close',
            { type: 'close' },
            !model.busy,
            { iconOnly: true }
        ),
        button(
            'templateInstall',
            rect(20, 54, 230, 36),
            text('Install template archive'),
            'upload',
            { type: 'install' },
            !model.busy
        ),
        button(
            'templateRefresh',
            rect(width - 52, 54, 32, 36),
            text('Refresh templates'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true }
        )
    ];
    let top = 102;
    if (model.error || model.busy) {
        nodes.push(
            label(
                'templatesStatus',
                rect(20, top, width - 40, 44),
                model.error || text('Working…'),
                { color: model.error ? 'error' : 'secondaryText', wrap: true }
            )
        );
        top += 52;
    }
    if (!(model.packages || []).length)
        nodes.push(
            label(
                'templatesEmpty',
                rect(20, top, width - 40, 36),
                text('No installed template packages.'),
                Object.assign({}, muted, { wrap: true })
            )
        );
    const rows = (model.packages || []).map((row, index) =>
        node(
            'Action',
            'template_' + row.code,
            rect(0, index * 62, width - 56, 58),
            {
                text: row.code,
                selected: model.selected === row.code,
                enabled: !model.busy,
                normalColor: 'transparent',
                selectedColor: 'contentSelection',
                action: { type: 'select', code: row.code },
                children: [
                    label(
                        'templateCode_' + row.code,
                        rect(14, 4, width - 84, 26),
                        row.code,
                        { weight: 600 }
                    ),
                    label(
                        'templatePath_' + row.code,
                        rect(14, 30, width - 84, 20),
                        row.path,
                        muted
                    )
                ]
            }
        )
    );
    const footer = 62;
    nodes.push(
        node(
            'Scroll',
            'templatesPackages',
            rect(20, top, width - 40, Math.max(0, height - top - footer)),
            { contentHeight: rows.length * 62 + 8, children: rows }
        )
    );
    nodes.push(
        node(
            'Box',
            'templatesFooter',
            rect(0, height - footer, width, footer),
            { background: 'surfaceContainerLow', radius: 0 }
        )
    );

    nodes.push(
        button(
            'templateDownload',
            rect(20, height - 48, compact ? 180 : 210, 36),
            text('Download archive'),
            'download',
            { type: 'download' },
            !!model.selected && !model.busy
        )
    );
    nodes.push(
        button(
            'templateDelete',
            rect(width - 130, height - 48, 110, 36),
            text('Delete'),
            'delete',
            { type: 'delete' },
            !!model.selected && !model.busy,
            { destructive: true }
        )
    );

    const header = nodes.splice(0, 3);
    nodes.unshift(
        node('Box', 'templatesHeader', rect(0, 0, width, 48), {
            titlebar: true,
            chromeRight: 86,
            background: 'surfaceContainerLow',
            radius: 0,
            children: header
        })
    );
    return { nodes };
}

export function confirmation(model, width, height, language) {
    return Confirmation.describe(
        {
            message: translate(
                'Remove template {code}? Existing projects are not removed.',
                language,
                { code: model.code }
            ),
            accept: 'Delete',
            reject: 'Cancel',
            destructive: true,
            busy: model.busy,
            acceptId: 'templateDeleteConfirm',
            rejectId: 'templateDeleteCancel'
        },
        width,
        height,
        language
    );
}
