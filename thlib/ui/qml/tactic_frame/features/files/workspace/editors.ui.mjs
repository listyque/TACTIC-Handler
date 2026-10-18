import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';
import { actionLayout } from '../../../controls/buttons/metrics.mjs';

export function actions(kind, model, language) {
    const tr = (text) => translate(text, language);
    return [
        {
            id: kind + 'Cancel',
            text: tr(
                kind === 'workspaceSetup' && model.busy
                    ? 'Stop waiting'
                    : 'Cancel'
            ),
            icon: 'close',
            action: { type: 'reject' },
            enabled: true
        },
        {
            id: kind + 'Save',
            text: tr(
                kind === 'workspaceSetup'
                    ? model.editing
                        ? 'Save workspace'
                        : 'Create'
                    : 'Save'
            ),
            icon:
                kind === 'workspaceSetup' && !model.editing
                    ? 'add'
                    : 'content-save',
            action: { type: 'accept' },
            enabled:
                !model.busy &&
                (kind !== 'workspaceSetup' ||
                    !!String(model.code || '').trim()),
            highlighted: true
        }
    ];
}

function finish(kind, model, width, height, language, children, contentHeight) {
    const buttons = actions(kind, model, language),
        footer = actionLayout(buttons, width, model.buttonWidths || []);
    return {
        preferredHeight: contentHeight + footer.height + 8,
        nodes: [
            node(
                'Scroll',
                kind + 'Body',
                rect(0, 0, width, Math.max(0, height - footer.height - 8)),
                { contentHeight, scrollbarId: kind + 'ScrollBar', children }
            ),
            ...buttons.map((item, index) =>
                button(
                    item.id,
                    rect(
                        footer.positions[index].x,
                        height - footer.height + footer.positions[index].y,
                        footer.positions[index].width,
                        footer.positions[index].height
                    ),
                    item.text,
                    item.icon,
                    item.action,
                    item.enabled,
                    { highlighted: !!item.highlighted }
                )
            )
        ]
    };
}

export function tab(model, width, height, language) {
    const tr = (text) => translate(text, language),
        draft = model.draft || {},
        inner = Math.max(0, width - 16),
        children = [];
    let y = 0;
    function choice(id, title, key, options) {
        children.push(
            node('Choice', id, rect(0, y, inner, 38), {
                label: tr(title),
                value: draft[key] || '',
                options,
                action: { type: 'field', key }
            })
        );
        y += 48;
    }
    children.push(
        node('Field', 'workspaceTabTitle', rect(0, y, inner, 38), {
            label: tr('Tab title'),
            placeholder: tr('Tab title'),
            text: draft.title || '',
            action: { type: 'field', key: 'title' }
        })
    );
    y += 48;
    choice(
        'workspaceTabPreset',
        'View',
        'preset',
        (model.presets || []).map((row) => ({
            value: row.id,
            label: tr(row.title)
        }))
    );
    choice(
        'workspaceTabSource',
        'File source',
        'source',
        [
            ['selection', 'Selected tree'],
            ['depot', 'Depot files'],
            ['have', 'Have'],
            ['local', 'Local changes'],
            ['change', 'Changelist files']
        ].map(([value, label]) => ({ value, label: tr(label) }))
    );
    if (draft.preset === 'history') {
        children.push(
            node('CheckBox', 'workspaceTabPinned', rect(0, y, inner, 32), {
                text: tr('Pin file history'),
                checked: !!draft.pinned,
                action: { type: 'field', key: 'pinned' }
            })
        );
        y += 42;
    }
    if (draft.preset !== 'files')
        choice(
            'workspaceTabScope',
            'Changelist scope',
            'scope',
            [
                ['mine', 'My changes'],
                ['workspace', 'This workspace'],
                ['stream', 'This stream'],
                ['all', 'All permitted changes']
            ].map(([value, label]) => ({ value, label: tr(label) }))
        );
    children.push(
        node('Field', 'workspaceTabPrefix', rect(0, y, inner, 38), {
            label: tr('Path prefix'),
            placeholder: tr('Path prefix'),
            text: draft.prefix || '',
            action: { type: 'field', key: 'prefix' }
        })
    );
    y += 48;
    return finish('workspaceTab', model, width, height, language, children, y);
}

export function setup(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        children = [];
    let y = 0;
    function field(id, title, key, enabled = true) {
        children.push(
            node('Field', id, rect(0, y, inner, 38), {
                label: tr(title),
                placeholder: tr(title),
                text: model[key] || '',
                enabled: !model.busy && enabled,
                action: { type: 'field', key }
            })
        );
        y += 48;
    }
    function text(id, value, error = false) {
        const h = Math.max(28, captionHeight(value, inner) * 1.2);
        children.push(
            label(id, rect(0, y, inner, h), value, {
                wrap: true,
                color: error ? 'error' : 'secondaryText'
            })
        );
        y += h + 10;
    }
    children.push(
        node('Choice', 'workspaceSetupKind', rect(0, y, inner, 38), {
            label: tr('Create'),
            value: model.kind || 'workspace',
            options: [
                ['workspace', 'Workspace'],
                ['stream', 'Stream'],
                ['depot', 'Depot']
            ].map(([value, label]) => ({ value, label: tr(label) })),
            enabled: !model.editing && !model.busy,
            action: { type: 'kind' }
        })
    );
    y += 48;
    field('workspaceSetupCode', 'Code', 'code', !model.editing);
    if (model.kind === 'workspace') {
        field('workspaceSetupStream', 'Stream', 'stream');
        field('workspaceSetupRoot', 'Local workspace root', 'root');
        children.push(
            node(
                'CheckBox',
                'workspaceSetupCaseSensitive',
                rect(0, y, inner, 38),
                {
                    text: tr('Case-sensitive local paths'),
                    checked: !!model.case_sensitive,
                    enabled: !model.busy,
                    wrapText: true,
                    action: { type: 'field', key: 'case_sensitive' }
                }
            )
        );
        y += 48;
        children.push(
            node(
                'View',
                'workspaceSetupMappings',
                rect(0, y, inner, model.mappingHeight || 40),
                { view: 'mappings' }
            )
        );
        y += (model.mappingHeight || 40) + 10;
        field('workspaceSetupPreviewPath', 'Sample depot path', 'previewPath');
        children.push(
            button(
                'workspaceSetupPreview',
                rect(0, y, inner, 38),
                tr('Preview mappings'),
                'visibility',
                { type: 'preview' },
                !model.busy && !!model.stream
            )
        );
        y += 48;
        for (const [index, row] of (model.mappingPreview || []).entries())
            text(
                'workspaceSetupMappingResult' + index,
                row.source_path +
                    ' → ' +
                    (row.excluded
                        ? tr('Excluded by workspace mapping')
                        : row.local_path) +
                    ' · ' +
                    tr(row.writable ? 'Writable' : 'Read-only'),
                !!row.collision
            );
    } else if (model.kind === 'stream') {
        field('workspaceSetupDepot', 'Depot', 'depot');
        field('workspaceSetupParent', 'Parent stream', 'source');
    }
    if (model.busy) text('workspaceSetupProgress', model.progress || '');
    if (model.error) text('workspaceSetupError', model.error, true);
    return finish(
        'workspaceSetup',
        model,
        width,
        height,
        language,
        children,
        y
    );
}
