import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { sections } from '../../../controls/forms/sections.ui.mjs';
import { translate } from '../../../core/strings.mjs';

export const fields = ['name', 'isProtected', 'isActive', 'selected'];

export function row(record, width, language) {
    return {
        nodes: [
            node(
                'Action',
                'serverPreset_' + record.name,
                rect(0, 0, width - 42, 44),
                {
                    text: record.name,
                    selected: record.selected,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    action: { type: 'select', name: record.name },
                    children: [
                        label(
                            'presetName',
                            rect(10, 0, width - 64, 24),
                            record.name,
                            { weight: record.isActive ? 600 : 400 }
                        ),
                        label(
                            'presetActive',
                            rect(10, 24, width - 64, 18),
                            record.isActive
                                ? translate('Active preset', language)
                                : '',
                            muted
                        )
                    ]
                }
            ),
            button(
                'presetRemove_' + record.name,
                rect(width - 38, 5, 32, 32),
                translate('Remove preset', language),
                'delete',
                { type: 'remove', name: record.name },
                !record.isProtected,
                { iconOnly: true, destructive: true }
            )
        ]
    };
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 760,
        margin = 14,
        inner = width - margin * 2;
    const footerHeight = model.error ? 114 : 54,
        bodyY = 82,
        bodyHeight = height - bodyY - footerHeight;
    const catalogWidth = compact ? inner : Math.min(260, inner * 0.34);
    const nodes = [
        label(
            'presetsTitle',
            rect(margin, 10, inner, 28),
            text('Connection presets'),
            { fontRole: 'title', weight: 600 }
        ),
        label(
            'presetsDescription',
            rect(margin, 42, inner, 32),
            text(
                'Choose a preset on the left and edit its connection and routing settings.'
            ),
            Object.assign({}, muted, { wrap: true })
        )
    ];
    const showCatalog = !compact || !model.editing;
    if (showCatalog) {
        nodes.push(
            node(
                'Box',
                'presetsCatalog',
                rect(margin, bodyY, catalogWidth, Math.max(0, bodyHeight)),
                {
                    background: 'panel',
                    border: 'outlineVariant',
                    radius: 12,
                    children: [
                        node(
                            'Field',
                            'presetName',
                            rect(12, 12, catalogWidth - 64, 38),
                            {
                                text: model.newName || '',
                                label: text('New preset'),
                                placeholder: text('New preset'),
                                enabled: true,
                                action: { type: 'newName' },
                                keys: {
                                    Return: { type: 'add' },
                                    Enter: { type: 'add' }
                                }
                            }
                        ),
                        button(
                            'presetAdd',
                            rect(catalogWidth - 46, 13, 34, 36),
                            text('Add preset'),
                            'add',
                            { type: 'add' },
                            !!String(model.newName || '').trim(),
                            { iconOnly: true }
                        ),
                        node(
                            'List',
                            'serverPresetsList',
                            rect(
                                6,
                                60,
                                catalogWidth - 12,
                                Math.max(0, bodyHeight - 66)
                            ),
                            {
                                source: 'presets',
                                keyField: 'name',
                                fields,
                                rowHeight: 48,
                                scrollbarId: 'serverPresetsScrollBar'
                            }
                        )
                    ]
                }
            )
        );
    }
    if (!compact || model.editing) {
        const left = compact ? margin : margin + catalogWidth + 12,
            formWidth = width - margin - left;
        const values = model.values || {},
            field = (
                key,
                title,
                kind = 'Field',
                description = '',
                props = {}
            ) => ({
                id: 'preset_' + key,
                field: key,
                title,
                kind,
                description,
                value: values[key],
                options: props.options,
                props: Object.assign(
                    {
                        text: values[key] || '',
                        checked: !!values[key],
                        value: values[key]
                    },
                    props
                )
            });
        const definitions = [
            {
                id: 'presetConnection',
                kind: 'Heading',
                title: model.selected || text('Presets'),
                dataLabel: true
            },
            field('serverUrl', 'Server address'),
            field('rpcTransport', 'API transport', 'Choice', '', {
                options: [
                    { value: 'xmlrpc', label: 'XML-RPC' },
                    { value: 'json', label: text('JSON (TACTIC Stream)') }
                ]
            }),
            field('storedUser', 'Stored account', 'Field', '', {
                readOnly: true,
                text: values.storedUser || text('No account saved')
            }),
            field(
                'hasTicket',
                'Stored ticket',
                'Field',
                'Sign-in is changed only through Generate ticket; the preset editor never asks for a TACTIC password.',
                {
                    readOnly: true,
                    text: text(values.hasTicket ? 'Ticket stored' : 'No ticket')
                }
            ),
            field(
                'teamLocalRepository',
                'TACTIC TEAM Mode (local repository)',
                'CheckBox',
                'Use when TACTIC and Handler share local storage. If paths differ, sync them in Repository configuration. Preview, check-in, and check-out methods are locked to local access.'
            ),
            { id: 'presetRouting', title: 'Site and proxy', kind: 'Heading' },
            field('siteEnabled', 'Use portal site', 'CheckBox'),
            field('siteName', 'Site name', 'Field', '', {
                enabled: !!values.siteEnabled
            }),
            field('proxyEnabled', 'Use proxy', 'CheckBox'),
            field('proxyServer', 'Proxy server', 'Field', '', {
                enabled: !!values.proxyEnabled
            }),
            field('proxyLogin', 'Proxy login', 'Field', '', {
                enabled: !!values.proxyEnabled
            }),
            field(
                'proxyPassword',
                'Proxy password',
                'Field',
                values.hasProxyPassword
                    ? 'Leave empty to keep the stored password.'
                    : '',
                { password: true, enabled: !!values.proxyEnabled }
            )
        ];
        const form = sections(
            definitions,
            formWidth - 16,
            language,
            !!model.selected,
            model.style
        );
        nodes.push(
            node(
                'Scroll',
                'presetDetails',
                rect(left, bodyY, formWidth, Math.max(0, bodyHeight)),
                {
                    contentHeight: form.height + (compact ? 44 : 0),
                    scrollbarId: 'presetDetailsScrollBar',
                    children: compact
                        ? [
                              button(
                                  'presetBack',
                                  rect(0, 0, formWidth - 16, 36),
                                  text('Presets'),
                                  'chevron-left',
                                  { type: 'back' },
                                  true
                              )
                          ].concat(
                              form.nodes.map((item) =>
                                  Object.assign({}, item, { y: item.y + 44 })
                              )
                          )
                        : form.nodes
                }
            )
        );
    }
    const footerY = height - footerHeight + 6;
    if (model.error)
        nodes.push(
            label(
                'presetError',
                rect(margin, footerY, inner, 54),
                text(model.error),
                { wrap: true, color: 'red', role: 'alert' }
            )
        );
    const actionsY = height - 48;
    nodes.push(
        button(
            'presetHelp',
            rect(margin, actionsY, 84, 36),
            text('Help'),
            'help',
            { type: 'help' },
            true
        )
    );
    nodes.push(
        button(
            'presetCancel',
            rect(width - margin - 190, actionsY, 90, 36),
            text('Cancel'),
            '',
            { type: 'cancel' },
            true
        )
    );
    nodes.push(
        button(
            'presetSave',
            rect(width - margin - 94, actionsY, 94, 36),
            text('Save'),
            'save',
            { type: 'save' },
            true,
            { highlighted: true }
        )
    );
    return { nodes };
}
