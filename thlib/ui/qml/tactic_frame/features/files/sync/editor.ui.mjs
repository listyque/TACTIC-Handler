import { spacing } from '../../../core/foundation.mjs';
import { captionedSwitch } from '../../../controls/forms/toggle.ui.mjs';
import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { actionLayout } from '../../../controls/buttons/metrics.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function actions(language) {
    return [
        { text: translate('Close', language), type: 'close' },
        {
            text: translate('Begin Repo Sync', language),
            type: 'start',
            icon: 'sync'
        }
    ];
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        margin = 9,
        gap = spacing.content,
        compact = width < 760,
        inner = Math.max(0, width - margin * 2),
        footerActions = actions(language),
        footerLayout = actionLayout(footerActions, inner, model.buttonWidths),
        status =
            model.error ||
            (model.dirty ? tr('Preset has unsaved changes') : ''),
        statusTextHeight = status
            ? Math.max(30, captionHeight(status, Math.max(1, inner - 16)) * 1.2)
            : 0,
        statusHeight = Math.min(statusTextHeight, Math.max(36, height * 0.2)),
        footerHeight = footerLayout.height + statusHeight,
        bodyHeight = Math.max(0, height - margin * 2 - footerHeight - 6),
        leftWidth = compact
            ? inner
            : Math.min(Math.max(330, model.paneWidth || 350), inner * 0.44),
        leftHeight = compact
            ? Math.max(180, Math.min(300, bodyHeight * 0.42))
            : bodyHeight,
        rightX = compact ? 0 : leftWidth + gap,
        rightY = compact ? leftHeight + gap : 0,
        rightWidth = compact ? inner : Math.max(0, inner - rightX),
        rightHeight = compact ? Math.max(0, bodyHeight - rightY) : bodyHeight,
        children = [],
        toolbar = [],
        expanded = !!model.togglersExpanded;
    let x = 0;
    if (expanded) {
        toolbar.push(
            button(
                'repositorySyncPresetDeleteButton',
                rect(0, 4, 28, 28),
                tr('Remove Current Preset'),
                'delete',
                { type: 'delete' },
                model.selected >= 0 && !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
        x = 32;
    }
    const tail = expanded ? 68 : 0;
    toolbar.push(
        node(
            'Choice',
            'repositorySyncPresetChoice',
            rect(x, 0, Math.max(0, leftWidth - x - tail), 36),
            {
                label: tr('Repository Sync preset'),
                value: model.presetName || '',
                options: model.presets || [],
                enabled: model.presets.length > 0 && !model.busy,
                action: { type: 'preset' }
            }
        )
    );
    if (expanded) {
        toolbar.push(
            button(
                'repositorySyncPresetSaveButton',
                rect(leftWidth - 64, 4, 28, 28),
                tr('Save Current Preset Changes'),
                'save',
                { type: 'save' },
                model.selected >= 0 && !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
        toolbar.push(
            button(
                'repositorySyncPresetAddButton',
                rect(leftWidth - 30, 4, 28, 28),
                tr('Create new Preset and Save'),
                'plus-box',
                { type: 'add' },
                !!model.validContext && !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
    }
    children.push(
        node('Box', 'repositorySyncPresetToolbar', rect(0, 0, leftWidth, 36), {
            children: toolbar
        })
    );
    children.push(
        node(
            'View',
            'repositorySyncProcessSlot',
            rect(0, 42, leftWidth, Math.max(0, leftHeight - 42)),
            { view: 'processes' }
        )
    );
    if (!compact)
        children.push(
            node(
                'Splitter',
                'repositorySyncEditorSplitter',
                rect(leftWidth, 0, gap, bodyHeight),
                {
                    orientation: 'vertical',
                    value: leftWidth,
                    min: Math.min(330, inner * 0.44),
                    max: inner * 0.44,
                    action: { type: 'paneWidth' }
                }
            )
        );
    const narrowOptions = rightWidth < 650,
        optionsHeight = narrowOptions ? 90 : 48,
        optionChildren = [
            node(
                'Segmented',
                'repositorySyncScope',
                rect(6, 6, Math.min(300, rightWidth - 152), 36),
                {
                    label: tr('Repository Sync scope'),
                    value: model.scopeMode,
                    options: [
                        {
                            value: 'full',
                            label: tr('Full scope'),
                            icon: 'inventory-2'
                        },
                        {
                            value: 'partial',
                            label: tr('Partial scope'),
                            icon: 'stream'
                        }
                    ],
                    action: { type: 'scope' }
                }
            )
        ];
    const chunkX = rightWidth - 82;
    optionChildren.push(
        label(
            'repositorySyncChunkLabel',
            rect(chunkX - 56, 6, 50, 36),
            tr('Chunk'),
            {
                color:
                    model.scopeMode === 'partial'
                        ? 'secondaryText'
                        : 'disabledText'
            }
        )
    );
    optionChildren.push(
        node('View', 'repositorySyncChunk', rect(chunkX, 6, 76, 36), {
            view: 'chunk'
        })
    );
    optionChildren.push(
        captionedSwitch(
            'repositorySyncOnlyUpdates',
            rect(
                narrowOptions ? 6 : 308,
                narrowOptions ? 48 : 8,
                narrowOptions ? rightWidth - 12 : Math.max(0, rightWidth - 448),
                32
            ),
            {
                text: tr('Only updates'),
                checked: !!model.onlyUpdates,
                action: { type: 'onlyUpdates' }
            }
        )
    );
    children.push(
        node(
            'Box',
            'repositorySyncOptionsPanel',
            rect(rightX, rightY, rightWidth, optionsHeight),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 12,
                children: optionChildren
            }
        )
    );
    children.push(
        node(
            'Box',
            'repositorySyncQueuePanel',
            rect(
                rightX,
                rightY + optionsHeight + 6,
                rightWidth,
                Math.max(0, rightHeight - optionsHeight - 6)
            ),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 12,
                children: [
                    node(
                        'View',
                        'repositorySyncEmbeddedQueue',
                        rect(
                            1,
                            1,
                            Math.max(0, rightWidth - 2),
                            Math.max(0, rightHeight - optionsHeight - 8)
                        ),
                        { view: 'queue' }
                    )
                ]
            }
        )
    );
    const footer = [
        node(
            'Scroll',
            'repositorySyncEditorStatusScroll',
            rect(0, 0, inner, statusHeight),
            {
                contentHeight: statusTextHeight,
                children: [
                    label(
                        'repositorySyncEditorStatus',
                        rect(0, 0, Math.max(0, inner - 16), statusTextHeight),
                        status,
                        {
                            fontRole: 'secondary',
                            color: model.error ? 'error' : 'secondaryText',
                            wrap: true,
                            wrapAnywhere: true
                        }
                    )
                ]
            }
        ),
        button(
            'repositorySyncEditorClose',
            rect(
                footerLayout.positions[0].x,
                footerLayout.positions[0].y + statusHeight,
                footerLayout.positions[0].width,
                38
            ),
            tr('Close'),
            '',
            { type: 'close' },
            true
        ),
        button(
            'repositorySyncEditorStart',
            rect(
                footerLayout.positions[1].x,
                footerLayout.positions[1].y + statusHeight,
                footerLayout.positions[1].width,
                38
            ),
            tr('Begin Repo Sync'),
            'sync',
            { type: 'start' },
            !!model.validContext &&
                model.selected >= 0 &&
                !model.busy &&
                !model.discovering &&
                !model.active,
            { highlighted: true }
        )
    ];
    children.push(
        node(
            'Box',
            'repositorySyncEditorFooter',
            rect(0, bodyHeight + 6, inner, footerHeight),
            { children: footer }
        )
    );
    return {
        nodes: [
            node(
                'Box',
                'repositorySyncEditorBackground',
                rect(0, 0, width, height),
                {
                    background: 'panelDeep',
                    children: [
                        node(
                            'Box',
                            'repositorySyncEditorContent',
                            rect(margin, margin, inner, height - margin * 2),
                            { children }
                        )
                    ]
                }
            )
        ]
    };
}

export function createPreset(model, width, language) {
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            node('Field', 'repositorySyncPresetName', rect(0, 0, width, 36), {
                label: tr('Preset name'),
                placeholder: tr('Preset name'),
                text: model.name || '',
                enabled: !model.busy,
                action: { type: 'name' },
                keys: { Enter: { type: 'accept' } }
            }),
            button(
                'repositorySyncPresetCancel',
                rect(0, 56, (width - 8) / 2, 38),
                tr('Cancel'),
                '',
                { type: 'reject' },
                !model.busy
            ),
            button(
                'repositorySyncPresetCreate',
                rect((width + 8) / 2, 56, (width - 8) / 2, 38),
                tr('Create and save'),
                '',
                { type: 'accept' },
                !model.busy && !!String(model.name || '').trim(),
                { highlighted: true }
            )
        ]
    };
}
