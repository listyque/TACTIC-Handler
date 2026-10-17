import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = {
    margin: 8,
    compactMargin: 6,
    gap: 6,
    heading: 16,
    action: 28,
    actionGap: 2,
    textPadding: 10,
    actionReserve: 38
};

export function presentation(model, language) {
    const tr = (text) => translate(text, language);
    const managed = model.managed !== false;
    return {
        managed,
        editable: !managed || !!model.editing || !!model.pinned,
        enabled: !!model.enabled || !!model.pinned,
        emphasized: managed && (!!model.editing || !!model.pinned),
        outline: model.error ? 'error' : model.pinned ? 'tertiary' : 'action',
        fontRole: model.compact ? 'menuHeading' : 'caption',
        bottomPadding: managed ? metrics.actionReserve : model.compact ? 8 : 10,
        placeholder: tr(
            model.enabled
                ? 'Description'
                : 'Select an sObject, process or snapshot'
        ),
        empty: tr(
            model.enabled || model.title
                ? 'No description'
                : 'Select an sObject, process or snapshot'
        ),
        status: !managed
            ? ''
            : model.saving
              ? tr('Saving…')
              : model.pinned
                ? tr('Used for check-in')
                : model.editing
                  ? tr(model.dirty ? 'Unsaved' : 'Editing')
                  : ''
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const state = presentation(model, language);
    const margin = model.compact ? metrics.compactMargin : metrics.margin;
    const inner = Math.max(0, width - margin * 2);
    const nodes = [
        node('Box', 'descriptionSurface', rect(0, 0, width, height), {
            background: 'surfaceContainerLow'
        })
    ];
    let top = margin;
    if (state.managed && model.header !== false) {
        nodes.push(
            node('Icon', 'descriptionKind', rect(margin, top, 15, 15), {
                icon: model.pinned
                    ? 'push-pin'
                    : model.kind === 'snapshot'
                      ? 'snapshot'
                      : model.kind === 'process'
                        ? 'settings-suggest'
                        : 'description',
                color: model.pinned
                    ? 'tertiary'
                    : model.editing
                      ? 'action'
                      : 'secondaryText'
            })
        );
        const statusWidth = state.status ? Math.min(135, inner / 2) : 0;
        nodes.push(
            label(
                'descriptionTarget',
                rect(margin + 21, top, inner - 21 - statusWidth, 16),
                model.title || tr('No sObject selected'),
                { fontRole: 'secondary', weight: 600 }
            )
        );
        if (state.status)
            nodes.push(
                label(
                    'descriptionState',
                    rect(width - margin - statusWidth, top, statusWidth, 16),
                    state.status,
                    {
                        fontRole: 'caption',
                        align: 'right',
                        color: model.pinned
                            ? 'tertiary'
                            : model.saving
                              ? 'secondaryText'
                              : 'action'
                    }
                )
            );
        top += metrics.heading + metrics.gap;
    }
    if (model.drafts?.length) {
        nodes.push(
            node('Choice', 'descriptionDrafts', rect(margin, top, inner, 36), {
                label: tr('Retained description drafts'),
                options: [
                    {
                        value: '',
                        label: tr('Retained description drafts'),
                        disabled: true
                    }
                ].concat(model.drafts),
                value: model.editing ? model.current || '' : '',
                enabled: !model.saving,
                action: { type: 'draft' }
            })
        );
        top += 36 + metrics.gap;
    }
    const bodyHeight = Math.max(0, height - margin - top);
    nodes.push(
        node('View', 'descriptionValue', rect(margin, top, inner, bodyHeight), {
            view: 'value'
        })
    );
    if (state.managed) {
        const actions = model.pinned
            ? [
                  [
                      'unpin',
                      'Stop using this text for check-in',
                      'unlock-alt',
                      !model.saving
                  ]
              ]
            : model.editing
              ? [
                    ['cancel', 'Discard changes', 'close', !model.saving],
                    [
                        'save',
                        model.canSave
                            ? 'Save description'
                            : 'This item has no description field',
                        'save',
                        !!model.canSave && !!model.dirty && !model.saving
                    ],
                    [
                        'pin',
                        'Use this text for check-in',
                        'push-pin',
                        !model.saving
                    ]
                ]
              : [
                    [
                        'edit',
                        'Edit description',
                        'edit',
                        !!model.enabled && !model.saving
                    ]
                ];
        const total =
            actions.length * (metrics.action + metrics.actionGap) -
            metrics.actionGap;
        const left = width - margin - 7 - total;
        const y = Math.max(top, height - margin - metrics.action - 5);
        for (let index = 0; index < actions.length; index++) {
            const [type, title, icon, enabled] = actions[index];
            nodes.push(
                button(
                    'description_' + type,
                    rect(left + index * 30, y, 28, 28),
                    tr(title),
                    icon,
                    { type },
                    enabled,
                    {
                        iconOnly: true,
                        iconAction: true,
                        iconSize: 17,
                        iconColor:
                            type === 'save'
                                ? 'green'
                                : ['pin', 'unpin'].includes(type)
                                  ? 'tertiary'
                                  : type === 'cancel'
                                    ? 'secondaryText'
                                    : 'primaryText',
                        label:
                            type === 'save' ? tr('Save description') : tr(title)
                    }
                )
            );
        }
        if (model.error)
            nodes.push(
                label(
                    'descriptionError',
                    rect(margin + 12, y + 6, left - margin - 18, 18),
                    model.error,
                    { color: 'error', fontRole: 'caption', role: 'alert' }
                )
            );
        else if (model.header === false && state.status)
            nodes.push(
                label(
                    'descriptionState',
                    rect(margin + 12, y + 6, left - margin - 18, 18),
                    state.status,
                    {
                        color: model.pinned ? 'tertiary' : 'secondaryText',
                        fontRole: 'caption',
                        role: 'status'
                    }
                )
            );
    }
    return { nodes, height };
}
