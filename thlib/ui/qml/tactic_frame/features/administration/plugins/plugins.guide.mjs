import { node, rect, label, button } from '../../../core/frame.mjs';

// Package availability and project activation are separate native operations.
export function steps(width, stage, tr) {
    const narrow = width < 600,
        row = narrow ? 38 : 0;
    return {
        nodes: [
            'Choose a package',
            'Review its contents',
            'Activate in project'
        ].map((text, index) =>
            label(
                'pluginStep_' + index,
                rect(
                    narrow ? 0 : (index * width) / 3,
                    index * row,
                    narrow ? width : width / 3 - 8,
                    30
                ),
                index + 1 + '  ' + tr(text),
                {
                    weight: index === stage ? 600 : 400,
                    color: index === stage ? 'primaryText' : 'secondaryText'
                }
            )
        ),
        height: narrow ? 118 : 42
    };
}

export function start(width, ready, tr) {
    const nodes = [],
        w = Math.min(width, 1120),
        stacked = w < 720;
    nodes.push(
        label(
            'pluginWelcomeTitle',
            rect(0, 0, w, 32),
            tr('Add capabilities to your project'),
            { fontRole: 'title', weight: 600 }
        )
    );
    nodes.push(
        label(
            'pluginWelcomeIntro',
            rect(0, 40, w, 50),
            tr(
                'Install a ready-made package or create your own. A package lives on the server; activation applies it to the selected project.'
            ),
            { wrap: true, color: 'secondaryText' }
        )
    );
    const progress = steps(w, 0, tr);
    progress.nodes.forEach((item) => {
        item.y += 100;
        nodes.push(item);
    });
    const y = 100 + progress.height + 12,
        cardWidth = stacked ? w : (w - 16) / 2,
        cardHeight = 208;
    for (const [index, title, description, icon, action, id] of [
        [
            0,
            'Install a package',
            'Have a plugin ZIP or download link? Upload it, review the manifest and documentation, then activate it in this project.',
            'upload',
            'install',
            'pluginEmptyInstall'
        ],
        [
            1,
            'Create your own plugin',
            'Start with an empty package or a Widget, Column or Theme template. Add files and project data, then publish a version.',
            'add',
            'new',
            'pluginEmptyNew'
        ]
    ]) {
        const x = stacked ? 0 : index * (cardWidth + 16),
            top = y + (stacked ? index * (cardHeight + 12) : 0);
        nodes.push(
            node(
                'Box',
                'pluginStartCard_' + index,
                rect(x, top, cardWidth, cardHeight),
                {
                    background: 'surfaceContainer',
                    border: 'outlineVariant',
                    radius: 8,
                    children: [
                        node(
                            'Icon',
                            'pluginStartIcon_' + index,
                            rect(16, 16, 24, 24),
                            { icon }
                        ),
                        label(
                            'pluginStartTitle_' + index,
                            rect(52, 12, cardWidth - 68, 32),
                            tr(title),
                            { weight: 600 }
                        ),
                        label(
                            'pluginStartDescription_' + index,
                            rect(16, 56, cardWidth - 32, 88),
                            tr(description),
                            { wrap: true, color: 'secondaryText' }
                        ),
                        button(
                            id,
                            rect(16, 156, cardWidth - 32, 36),
                            tr(title),
                            icon,
                            { type: action },
                            ready,
                            { highlighted: index === 0 }
                        )
                    ]
                }
            )
        );
    }
    const bottom = y + (stacked ? cardHeight * 2 + 12 : cardHeight) + 20;
    nodes.push(
        button(
            'pluginStartHelp',
            rect(0, bottom, Math.min(300, w), 36),
            tr('Plugin guide'),
            'help',
            { type: 'help' },
            true
        )
    );
    return { nodes, height: bottom + 48 };
}

export function installation(ui, width, ready, tr) {
    const nodes = [],
        progress = steps(width, 0, tr);
    progress.nodes.forEach((item) => nodes.push(item));
    let y = progress.height + 8;
    nodes.push(
        label(
            'pluginInstallNotice',
            rect(0, y, width, 58),
            tr(
                'First add the package to this server. Nothing is activated in your project until you review and confirm the next step.'
            ),
            { wrap: true, color: 'secondaryText' }
        )
    );
    y += 70;
    nodes.push(
        node('Segmented', 'pluginInstallSource', rect(0, y, width, 36), {
            label: tr('Package source'),
            value: ui.source,
            options: [
                { value: 'zip', label: tr('ZIP file') },
                { value: 'url', label: tr('Download link') }
            ],
            action: { type: 'input', field: 'source' },
            enabled: ready
        })
    );
    y += 52;
    if (ui.source === 'zip') {
        nodes.push(
            label(
                'pluginZipInstructions',
                rect(0, y, width, 62),
                tr(
                    'Choose a ZIP containing manifest.xml and the plugin files. The file is uploaded from this computer to the selected server.'
                ),
                { wrap: true }
            )
        );
        y += 74;
        nodes.push(
            button(
                'pluginBrowseZip',
                rect(0, y, Math.min(300, width), 40),
                tr('Choose ZIP and upload'),
                'folder',
                { type: 'upload', package: true },
                ready,
                { highlighted: true }
            )
        );
        y += 52;
    } else {
        nodes.push(
            label(
                'pluginUrlInstructions',
                rect(0, y, width, 56),
                tr(
                    'The server downloads the ZIP from this address. Add a checksum if the publisher provides one.'
                ),
                { wrap: true }
            )
        );
        y += 68;
        for (const [field, title] of [
            ['url', 'Plugin ZIP URL'],
            ['checksum', 'SHA-256 or MD5 (optional)']
        ]) {
            nodes.push(
                label(
                    'pluginInstallLabel_' + field,
                    rect(0, y, width, 24),
                    tr(title)
                )
            );
            y += 28;
            nodes.push(
                node('Field', 'pluginInstall_' + field, rect(0, y, width, 40), {
                    label: tr(title),
                    text: ui[field],
                    placeholder:
                        field === 'url' ? 'https://example.org/plugin.zip' : '',
                    action: { type: 'input', field },
                    enabled: ready
                })
            );
            y += 52;
        }
        nodes.push(
            button(
                'pluginConfirm',
                rect(0, y, Math.min(300, width), 40),
                tr('Download package'),
                'download',
                { type: 'confirm' },
                ready && !!ui.url.trim(),
                { highlighted: true }
            )
        );
        y += 52;
    }
    return { nodes, height: y };
}

export function project(model, width, tr) {
    const meta = model.metadata || {},
        nodes = [],
        compact = width < 620;
    const progress = steps(width, meta.active ? 2 : 1, tr);
    progress.nodes.forEach((item) => nodes.push(item));
    let y = progress.height + 8;
    const lineHeight = compact ? 78 : 54;
    nodes.push(
        node('Box', 'pluginProjectState', rect(0, y, width, lineHeight + 100), {
            background: 'surfaceContainer',
            border: 'outlineVariant',
            radius: 8,
            children: [
                label(
                    'pluginProjectTitle',
                    rect(16, 10, width - 32, 24),
                    tr('Project activation'),
                    { weight: 600 }
                ),
                label(
                    'pluginProjectName',
                    rect(16, 40, width - 32, 28),
                    meta.project || '',
                    { weight: 600 }
                ),
                label(
                    'pluginProjectExplanation',
                    rect(16, 74, width - 32, lineHeight),
                    tr(
                        meta.active
                            ? 'Active in this project. Manifest changes are applied only when you reload the plugin.'
                            : 'Package available on the server. Review its manifest and documentation before activating it here.'
                    ),
                    { wrap: true, color: 'secondaryText' }
                )
            ]
        })
    );
    y += lineHeight + 112;
    const ready =
        !model.busy &&
        !model.dirty &&
        !model.uncertain &&
        !['admin', 'sthpw'].includes(meta.project);
    nodes.push(
        button(
            'pluginAction_' + (meta.active ? 'deactivate' : 'activate'),
            rect(0, y, Math.min(width, 320), 40),
            tr(meta.active ? 'Remove from project' : 'Review activation'),
            meta.active ? 'remove' : 'check',
            {
                type: 'operation',
                action: meta.active ? 'deactivate' : 'activate'
            },
            ready,
            { highlighted: !meta.active }
        )
    );
    y += 54;
    if (['admin', 'sthpw'].includes(meta.project)) {
        nodes.push(
            label(
                'pluginBusinessProject',
                rect(0, y, width, 50),
                tr('Select a business project to activate or remove a plugin'),
                { wrap: true, color: 'secondaryText' }
            )
        );
        y += 62;
    }
    nodes.push(
        label(
            'pluginReviewTitle',
            rect(0, y, width, 28),
            tr('Review and develop'),
            { weight: 600 }
        )
    );
    y += 36;
    for (const [tab, title, description, icon] of [
        [
            'manifest',
            'Manifest XML',
            'Inspect the project data, dependencies and commands declared by this package.',
            'code'
        ],
        [
            'docs',
            'Documentation',
            'Read setup instructions supplied by the package author.',
            'help'
        ],
        [
            'files',
            'Files',
            'Browse and edit source files, upload assets or download a local copy.',
            'folder'
        ]
    ]) {
        const h = compact ? 112 : 78;
        nodes.push(
            node('Box', 'pluginReview_' + tab, rect(0, y, width, h), {
                background: 'transparent',
                border: 'outlineVariant',
                radius: 4,
                children: [
                    button(
                        'pluginOpen_' + tab,
                        rect(8, 8, Math.min(235, width - 16), 32),
                        tr(title),
                        icon,
                        { type: 'tab', value: tab },
                        !model.busy && !model.dirty && !model.uncertain,
                        { alignment: 'left' }
                    ),
                    label(
                        'pluginReviewDescription_' + tab,
                        rect(16, 44, width - 32, h - 48),
                        tr(description),
                        { wrap: true, color: 'secondaryText' }
                    )
                ]
            })
        );
        y += h + 8;
    }
    if (!meta.builtin) {
        y += 12;
        nodes.push(
            label(
                'pluginDistributionTitle',
                rect(0, y, width, 28),
                tr('Share a package'),
                { weight: 600 }
            )
        );
        y += 36;
        nodes.push(
            label(
                'pluginDistributionHint',
                rect(0, y, width, 54),
                tr(
                    'Export a ZIP to share the current package. Publish version creates a separate release; it does not activate it.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
        y += 62;
        const bw = Math.min(260, (width - 8) / 2),
            enabled = !model.busy && !model.dirty && !model.uncertain;
        nodes.push(
            button(
                'pluginAction_export',
                rect(0, y, bw, 40),
                tr('Export ZIP'),
                'download',
                { type: 'run', action: 'export' },
                enabled
            )
        );
        nodes.push(
            button(
                'pluginAction_publish',
                rect(bw + 8, y, bw, 40),
                tr('Publish version'),
                'publish',
                { type: 'operation', action: 'publish' },
                enabled
            )
        );
        y += 56;
    }
    nodes.push(
        label(
            'pluginDetailsTitle',
            rect(0, y, width, 28),
            tr('Package details'),
            { weight: 600 }
        )
    );
    return { nodes, height: y + 40 };
}
