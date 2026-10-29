import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function message(text, width, language) {
    return {
        nodes: text
            ? [
                  label(
                      'relatedError',
                      rect(12, 12, Math.max(0, width - 24), 40),
                      translate(text, language),
                      { color: 'secondaryText' }
                  )
              ]
            : []
    };
}

export function menuActions(items) {
    return items.some((item) => item.command === 'open_related_objects')
        ? items
        : [
              ...items,
              {
                  title: 'Related objects',
                  icon: 'link',
                  command: 'open_related_objects'
              }
          ];
}

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language);
    const narrow = width < 650;
    const createWidth = Math.min(
        width - 24,
        Math.max(210, tr('Create related object').length * 8 + 44)
    );
    const height = narrow && model.canCreate ? 124 : 84;
    const nodes = [
        label(
            'relatedParent',
            rect(12, 8, Math.max(0, width - 24), 20),
            model.parentTitle || '',
            { color: 'secondaryText' }
        ),
        node(
            'Choice',
            'relatedType',
            rect(
                12,
                36,
                Math.max(
                    0,
                    width -
                        24 -
                        (!narrow && model.canCreate ? createWidth + 12 : 0)
                ),
                36
            ),
            {
                label: tr('Related type'),
                options: model.relations || [],
                value: model.selectedType || '',
                enabled:
                    !model.busy && !model.locked && !!model.relations?.length,
                action: { type: 'relation' }
            }
        )
    ];
    if (model.canCreate)
        nodes.push(
            button(
                'relatedCreate',
                rect(
                    narrow ? 12 : width - 12 - createWidth,
                    narrow ? 80 : 36,
                    createWidth,
                    36
                ),
                tr('Create related object'),
                'add',
                { type: 'create' },
                !model.busy,
                { highlighted: true }
            )
        );
    return { height, nodes };
}
