import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        draft = model.draft || {},
        choices = model.choices || {},
        enabled = !model.loading && !model.saving,
        children = [];
    let y = 0;
    function text(id, value, color = 'secondaryText') {
        const h = Math.max(24, captionHeight(value, inner) * 1.2);
        children.push(
            label(id, rect(0, y, inner, h), value, { wrap: true, color })
        );
        y += h + 8;
    }
    function field(key, title, id, readOnly = false) {
        text(id + 'Label', tr(title));
        children.push(
            node('Field', id, rect(0, y, inner, 38), {
                label: tr(title),
                text: draft[key] || '',
                enabled,
                readOnly,
                action: { type: 'field', key }
            })
        );
        y += 46;
    }
    if (model.notice) text('streamEditorNotice', model.notice, 'error');
    if (model.loading) text('streamEditorLoading', tr('Loading…'));
    field('code', 'Stream code', 'streamEditorCode', !model.creating);
    field('title', 'Name', 'streamEditorName');
    for (const [key, title, options, id] of [
        [
            'depot',
            'Depot',
            (choices.depots || []).map((row) => ({
                value: row.code,
                label: row.code
            })),
            'streamEditorDepot'
        ],
        [
            'stream_type',
            'Stream type',
            (choices.types || []).map((value) => ({ value, label: value })),
            'streamEditorType'
        ]
    ]) {
        text(id + 'Label', tr(title));
        children.push(
            node('Choice', id, rect(0, y, inner, 38), {
                label: tr(title),
                options,
                value: draft[key] || '',
                enabled: enabled && model.creating,
                action: { type: 'field', key }
            })
        );
        y += 46;
    }
    text('streamEditorParentLabel', tr('Parent stream'));
    const stacked = inner < 390,
        choiceWidth = stacked ? inner : 150,
        fieldWidth = stacked ? inner : Math.max(0, inner - choiceWidth - 8);
    children.push(
        node('Field', 'streamEditorParent', rect(0, y, fieldWidth, 38), {
            label: tr('Parent stream'),
            text: draft.parent || '',
            enabled: enabled && draft.stream_type !== 'mainline',
            action: { type: 'field', key: 'parent' }
        })
    );
    children.push(
        node(
            'Choice',
            'streamEditorParentChoice',
            rect(
                stacked ? 0 : fieldWidth + 8,
                y + (stacked ? 46 : 0),
                choiceWidth,
                38
            ),
            {
                label: tr('Choose parent'),
                placeholder: tr('Choose parent'),
                value: draft.parent || '',
                options: (choices.parents || [])
                    .filter(
                        (row) =>
                            row.code !== draft.code && row.depot === draft.depot
                    )
                    .map((row) => ({ value: row.code, label: row.code })),
                enabled: enabled && draft.stream_type !== 'mainline',
                action: { type: 'field', key: 'parent' }
            }
        )
    );
    y += stacked ? 92 : 46;
    if (choices.more)
        text(
            'streamEditorPickerLimit',
            tr(
                'The picker shows the first 1000 records. Enter another parent stream code directly.'
            )
        );
    text('streamEditorDescriptionLabel', tr('Description'));
    children.push(
        node('Area', 'streamEditorDescription', rect(0, y, inner, 100), {
            text: draft.description || '',
            label: tr('Description'),
            enabled,
            action: { type: 'field', key: 'description' }
        })
    );
    y += 108;
    if (!model.creating)
        text(
            'streamEditorOwner',
            tr('Owner: {owner}').replace('{owner}', model.owner || '—')
        );
    const locked = tr(
            'Only the owner and administrators may edit stream settings'
        ),
        checkHeight = Math.max(32, captionHeight(locked, inner - 32) * 1.2);
    children.push(
        node('CheckBox', 'streamEditorLocked', rect(0, y, inner, checkHeight), {
            text: locked,
            checked: !!draft.locked,
            enabled,
            wrapText: true,
            action: { type: 'field', key: 'locked' }
        })
    );
    y += checkHeight + 8;
    if (model.creating && draft.stream_type !== 'mainline')
        text(
            'streamEditorBranchNotice',
            tr(
                "The new branch starts from the parent's published files without copying file contents."
            )
        );
    else if (!model.creating)
        text(
            'streamEditorParentNotice',
            tr(
                'Changing Parent changes the hierarchy. Existing files and their branch history stay intact.'
            )
        );
    text(
        'streamEditorLimits',
        tr(
            'Virtual streams, inherited path views and automatic merge/copy policies are not supported yet.'
        )
    );
    const footer = width < 320 ? 90 : 44,
        w = width < 320 ? width : (width - 8) / 2;
    return {
        nodes: [
            node(
                'Scroll',
                'streamEditorFields',
                rect(0, 0, width, Math.max(0, height - footer - 8)),
                {
                    contentHeight: y,
                    scrollbarId: 'streamEditorScrollBar',
                    children
                }
            ),
            button(
                'streamEditorCancel',
                rect(0, height - footer, w, 38),
                tr('Cancel'),
                'close',
                { type: 'reject' },
                !model.saving
            ),
            button(
                'streamEditorSave',
                rect(
                    width < 320 ? 0 : w + 8,
                    height - footer + (width < 320 ? 46 : 0),
                    w,
                    38
                ),
                tr(model.creating ? 'Create' : 'Save'),
                'save',
                { type: 'save' },
                enabled &&
                    !!String(draft.code || '').trim() &&
                    (choices.types || []).includes(draft.stream_type) &&
                    (choices.depots || []).some(
                        (row) => row.code === draft.depot
                    )
            )
        ]
    };
}
