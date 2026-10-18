import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function describe(model, width, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width),
        nodes = [];
    nodes.push(
        label(
            'workspaceMappingsTitle',
            rect(0, 0, Math.max(0, inner - 72), 32),
            tr('Mappings and exclusions')
        )
    );
    nodes.push(
        button(
            'workspaceMappingAdd',
            rect(Math.max(0, inner - 68), 0, 30, 30),
            tr('Add mapping'),
            'add',
            { type: 'add' },
            !!model.enabled && (model.rows || []).length < 256,
            { iconOnly: true, iconAction: true }
        )
    );
    nodes.push(
        button(
            'workspaceMappingsTechnical',
            rect(Math.max(0, inner - 34), 0, 30, 30),
            tr('Technical JSON'),
            'code',
            { type: 'technical' },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    let y = 40;
    if (model.error) {
        const h = Math.max(36, captionHeight(model.error, inner) * 1.2);
        nodes.push(
            label('workspaceMappingError', rect(0, y, inner, h), model.error, {
                color: 'error',
                wrap: true
            })
        );
        y += h + 8;
    }
    if (model.technical) {
        nodes.push(
            node('Area', 'workspaceMappingsJson', rect(0, y, inner, 180), {
                text: model.value || '',
                readOnly: !model.enabled,
                label: tr('Workspace mappings (JSON)'),
                monospace: true,
                action: { type: 'json' }
            })
        );
        y += 188;
    } else
        for (const [index, row] of (model.rows || []).entries()) {
            const children = [],
                key = row.id;
            children.push(
                node(
                    'Field',
                    'workspaceMappingStream:' + key,
                    rect(0, 0, Math.max(0, inner - 38), 38),
                    {
                        text: row.stream,
                        label: tr('Mapping stream'),
                        placeholder: tr('Stream'),
                        enabled: !!model.enabled,
                        action: { type: 'field', key, field: 'stream' }
                    }
                )
            );
            children.push(
                button(
                    'workspaceMappingRemove:' + key,
                    rect(Math.max(0, inner - 32), 3, 30, 30),
                    tr('Remove mapping'),
                    'delete',
                    { type: 'remove', key },
                    !!model.enabled,
                    { iconOnly: true, iconAction: true }
                )
            );
            children.push(
                node(
                    'Field',
                    'workspaceMappingSource:' + index,
                    rect(0, 46, inner, 38),
                    {
                        text: row.source,
                        label: tr('Depot pattern'),
                        placeholder: tr('Depot pattern, e.g. assets/...'),
                        enabled: !!model.enabled,
                        action: { type: 'field', key, field: 'source' }
                    }
                )
            );
            let rowY = 92;
            if (!row.exclude) {
                children.push(
                    node(
                        'Field',
                        'workspaceMappingTarget:' + key,
                        rect(0, rowY, inner, 38),
                        {
                            text: row.target,
                            label: tr('Local pattern'),
                            placeholder: tr('Local pattern, e.g. art/...'),
                            enabled: !!model.enabled,
                            action: { type: 'field', key, field: 'target' }
                        }
                    )
                );
                rowY += 46;
            }
            const half = (inner - 8) / 2;
            children.push(
                node(
                    'CheckBox',
                    'workspaceMappingExclude:' + key,
                    rect(0, rowY, half, 32),
                    {
                        text: tr('Exclude'),
                        checked: !!row.exclude,
                        enabled: !!model.enabled,
                        action: { type: 'field', key, field: 'exclude' }
                    }
                )
            );
            children.push(
                node(
                    'CheckBox',
                    'workspaceMappingWritable:' + key,
                    rect(half + 8, rowY, half, 32),
                    {
                        text: tr('Writable'),
                        checked: !!row.writable,
                        enabled: !!model.enabled && !row.exclude,
                        action: { type: 'field', key, field: 'writable' }
                    }
                )
            );
            rowY += 40;
            children.push(
                node(
                    'Box',
                    'workspaceMappingSeparator',
                    rect(0, rowY, inner, 1),
                    { background: 'outlineVariant' }
                )
            );
            nodes.push(
                node(
                    'Box',
                    'workspaceMappingRow:' + key,
                    rect(0, y, inner, rowY + 8),
                    { children }
                )
            );
            y += rowY + 12;
        }
    return { height: y, nodes };
}
