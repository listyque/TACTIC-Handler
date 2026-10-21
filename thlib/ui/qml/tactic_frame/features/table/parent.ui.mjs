import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import * as Confirmation from '../../controls/feedback/confirmation.ui.mjs';
import * as State from './parent.state.mjs';
import { link } from './cells.ui.mjs';

export const groupHeight = 64;
export const popupMetrics = {
    width: 380,
    height: 500,
    padding: 10,
    minimumBody: 308
};

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    if (model.confirmAction)
        return Confirmation.describe(
            {
                message: tr(
                    model.uncertain
                        ? 'Discard this draft? Some changes may already have been saved.'
                        : 'Discard this draft?'
                ),
                accept: 'Discard',
                destructive: true
            },
            width,
            height,
            language
        );
    const stacked = width < 340 || model.uncertain,
        footer = stacked ? 124 : 80,
        sourceHeight = height >= 440 ? 28 : 0,
        errorHeight = model.error
            ? Math.min(
                  Math.max(0, height - footer - 160 - sourceHeight),
                  80,
                  Math.max(36, captionHeight(tr(model.error), width - 16) + 12)
              )
            : 0,
        listTop = 160 + sourceHeight + errorHeight,
        bottom = height - footer,
        enabled = model.ready && !model.uncertain && model.busy !== 'save';
    const nodes = [
        label(
            'parentHeading',
            rect(0, 0, Math.max(0, width - 40), 28),
            tr('Change parent'),
            { weight: 600 }
        ),
        button(
            'parentRefresh',
            rect(width - 32, 0, 32, 32),
            tr('Refresh'),
            model.busy === 'prepare' ? 'loading' : 'refresh',
            { type: 'refresh' },
            !model.busy && !model.uncertain,
            { iconOnly: true, iconAction: true }
        )
    ];
    if (sourceHeight)
        nodes.push(
            label(
                'parentSource',
                rect(0, 32, width, 24),
                model.seed.sourceTitle || '',
                {
                    color: 'secondaryText',
                    toolTip: model.seed.sourceTitle || ''
                }
            )
        );
    nodes.push(
        node('Choice', 'parentType', rect(0, 36 + sourceHeight, width, 36), {
            label: tr('Search Type'),
            value: model.parentType,
            options: model.parentTypes,
            enabled: enabled && !model.busy,
            action: { type: 'type' }
        }),
        node(
            'Field',
            'parentQuery',
            rect(0, 82 + sourceHeight, Math.max(0, width - 40), 40),
            {
                label: tr('Find parent'),
                placeholder: tr('Find parent'),
                text: model.draftQuery,
                maxLength: 200,
                enabled,
                action: { type: 'query-text' },
                keys: { Enter: { type: 'query' } }
            }
        ),
        button(
            'parentSearch',
            rect(width - 32, 86 + sourceHeight, 32, 32),
            tr('Search'),
            model.busy === 'candidates' ? 'loading' : 'search',
            { type: 'query' },
            enabled && !model.busy,
            { iconOnly: true, iconAction: true }
        ),
        label(
            'parentCurrent',
            rect(0, 130 + sourceHeight, width, 24),
            tr('Current parent') +
                ': ' +
                (model.currentParent?.title || tr('No parent')),
            {
                color: 'secondaryText',
                toolTip: model.currentParent?.searchKey || ''
            }
        )
    );
    if (errorHeight)
        nodes.push(
            node(
                'Scroll',
                'parentError',
                rect(0, 158 + sourceHeight, width, errorHeight),
                {
                    contentHeight:
                        captionHeight(tr(model.error), width - 16) + 12,
                    scrollbarId: 'parentErrorScrollBar',
                    children: [
                        label(
                            'parentErrorText',
                            rect(
                                0,
                                0,
                                width - 16,
                                captionHeight(tr(model.error), width - 16) + 12
                            ),
                            tr(model.error),
                            { color: 'error', role: 'alert', wrap: true }
                        )
                    ]
                }
            )
        );
    const listHeight = Math.max(
        0,
        bottom - listTop - 8 - (model.hasNext ? 32 : 0)
    );
    nodes.push(
        node('List', 'parentRows', rect(0, listTop, width, listHeight), {
            source: 'parentRows',
            keyField: 'searchKey',
            rowHeight: 48,
            scrollbarId: 'parentScrollBar',
            role: 'listbox',
            label: tr('Available parents'),
            fields: [
                'searchKey',
                'title',
                'code',
                'revision',
                'retired',
                'selected',
                'enabled'
            ]
        })
    );
    if (model.ready && !model.rows.length && !model.busy)
        nodes.push(
            label(
                'parentEmpty',
                rect(0, listTop, width - 16, Math.min(48, listHeight)),
                tr('No matching parents'),
                { color: 'secondaryText' }
            )
        );
    if (model.hasNext)
        nodes.push(
            button(
                'parentMore',
                rect(0, bottom - 36, width, 28),
                tr('Show more'),
                'expand-more',
                { type: 'more' },
                !model.busy && !model.uncertain
            )
        );
    const selected = model.selectedParent,
        selectedText = selected ? selected.title : tr('No parent selected');
    nodes.push(
        label(
            'parentSelected',
            rect(0, bottom, width, 24),
            tr('Selected parent') + ': ' + selectedText,
            { toolTip: selected?.searchKey || '' }
        ),
        button(
            'parentSave',
            rect(
                0,
                bottom + 32,
                stacked ? width : Math.max(0, (width - 8) / 2),
                40
            ),
            tr(model.uncertain ? 'Check saved changes' : 'Save'),
            model.busy ? 'loading' : model.uncertain ? 'refresh' : 'check',
            { type: model.uncertain ? 'check' : 'save' },
            model.uncertain ? !model.busy : State.canSave(model),
            { highlighted: true }
        ),
        button(
            'parentCancel',
            rect(
                stacked ? 0 : (width + 8) / 2,
                bottom + (stacked ? 80 : 32),
                stacked ? width : Math.max(0, (width - 8) / 2),
                40
            ),
            tr('Cancel'),
            'close',
            { type: 'cancel' },
            model.busy !== 'save'
        )
    );
    return { nodes, height };
}

export function row(record, width, language) {
    const key = record.searchKey,
        caption = [
            record.title !== record.code ? record.code : '',
            record.retired ? translate('Retired', language) : ''
        ]
            .filter(Boolean)
            .join(' · '),
        inner = Math.max(0, width - 40);
    const nodes = [
        node('Action', 'parentCandidate:' + key, rect(0, 0, width, 46), {
            text: record.title,
            role: 'option',
            selected: !!record.selected,
            enabled: record.enabled,
            normalColor: 'transparent',
            selectedColor: 'contentSelection',
            action: { type: 'select', searchKey: key },
            children: [
                label(
                    'parentCandidateTitle:' + key,
                    rect(10, caption ? 5 : 13, inner, 22),
                    record.title,
                    { toolTip: record.title }
                ),
                label(
                    'parentCandidateCode:' + key,
                    rect(10, 27, inner, 16),
                    caption,
                    { color: 'secondaryText', fontRole: 'caption' }
                )
            ]
        })
    ];
    if (record.selected)
        nodes.push(
            node(
                'Icon',
                'parentCandidateSelected:' + key,
                rect(Math.max(0, width - 28), 13, 20, 20),
                { icon: 'check', color: 'action' }
            )
        );
    return { nodes };
}

export function cell(model, width, height, language, editable) {
    const tr = (text) => translate(text, language),
        canEdit = editable && !!model.parentEditable,
        text =
            model.text ||
            tr(model.missingParentKey ? 'Parent unavailable' : 'No parent');
    const children = [
        label(
            'parentCellValue',
            rect(4, 0, Math.max(0, width - (canEdit ? 44 : 8)), height),
            text,
            { toolTip: model.parent?.searchKey || model.missingParentKey || '' }
        )
    ];
    if (canEdit)
        children.push(
            button(
                'parentCellChange',
                rect(
                    Math.max(0, width - 36),
                    Math.max(0, (height - 32) / 2),
                    32,
                    32
                ),
                tr('Change parent'),
                'account-tree',
                { type: 'service', name: 'change-parent' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    return {
        nodes: [
            node('Box', 'parentCell', rect(0, 0, width, height), {
                background: 'transparent',
                radius: 0,
                children,
                dropAction: canEdit
                    ? { type: 'service', name: 'drop-parent' }
                    : null
            })
        ]
    };
}

export function group(model, width, language, editable, server) {
    const tr = (text) => translate(text, language),
        cell = model.cell,
        parent = cell.parent,
        title = parent
            ? [parent.code || cell.text, parent.name]
                  .filter(Boolean)
                  .join(' — ')
            : tr(cell.missingParentKey ? 'Parent unavailable' : 'No parent'),
        caption = parent
            ? [parent.searchKey.split('?')[0], parent.description]
                  .filter(Boolean)
                  .join(' · ')
            : cell.missingParentKey || '',
        content = [
            node('Icon', 'parentGroupDisclosure', rect(0, 22, 20, 20), {
                icon: model.closed ? 'chevron-right' : 'expand-more',
                color: 'secondaryText'
            }),
            node('Preview', 'parentGroupPreview', rect(28, 12, 40, 40), {
                source: link(parent?.preview?.image || '', server) || '',
                initials: String(parent?.code || cell.text || '').slice(0, 2),
                icon: 'sobject',
                round: false,
                outlined: false
            }),
            label(
                'parentGroupTitle',
                rect(80, 8, Math.max(0, width - 164), 22),
                title,
                { weight: 600, toolTip: title }
            ),
            label(
                'parentGroupDescription',
                rect(80, 34, Math.max(0, width - 164), 18),
                caption,
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    toolTip: caption
                }
            ),
            label(
                'parentGroupCount',
                rect(Math.max(0, width - 80), 18, 38, 28),
                String(model.count),
                { color: 'secondaryText' }
            )
        ],
        nodes = [
            node(
                'Action',
                'parentGroupToggle',
                rect(0, 0, width, groupHeight),
                {
                    text: title + ' · ' + model.count,
                    role: 'button',
                    expanded: !model.closed,
                    enabled: true,
                    normalColor: 'transparent',
                    action: { type: 'toggle' },
                    children: content
                }
            )
        ];
    if (parent && editable)
        nodes.push(
            button(
                'parentGroupCreate',
                rect(Math.max(0, width - 36), 16, 32, 32),
                tr('Add Another Item'),
                'add',
                { type: 'create-child' },
                !parent.retired,
                { iconOnly: true, iconAction: true }
            )
        );
    return { nodes };
}
