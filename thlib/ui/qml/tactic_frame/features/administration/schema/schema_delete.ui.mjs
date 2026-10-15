import { node } from '../../../core/frame.mjs';
import { rect, label, muted } from '../admin.document.mjs';
import { translate } from '../../../core/strings.mjs';
export function allowed(model) {
    return (
        model.canWrite &&
        (!model.metadata ||
            !model.metadata.schemaRevision ||
            model.metadata.schemaRevision === model.schemaRevision)
    );
}
export function transition(model, event) {
    if (event.type === 'close')
        return !model.deleting
            ? [
                  {
                      type: 'close'
                  }
              ]
            : [];
    if (event.type === 'reload')
        return !model.busy && !model.uncertain
            ? [
                  {
                      type: 'reload'
                  }
              ]
            : [];
    if (event.type === 'confirmation')
        return allowed(model) && !model.busy && !model.uncertain
            ? [
                  {
                      type: 'confirmation',
                      value: event.value
                  }
              ]
            : [];
    if (event.type === 'delete')
        return allowed(model) &&
            !model.busy &&
            !model.uncertain &&
            model.confirmation === model.identity
            ? [
                  {
                      type: 'delete'
                  }
              ]
            : [];
    return [];
}
export function describe(model, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    if (
        model.metadata &&
        model.metadata.schemaRevision &&
        model.metadata.schemaRevision !== model.schemaRevision
    )
        model = Object.assign({}, model, {
            canWrite: false,
            error: 'Schema changed on the server. Reload before deleting a Search Type.'
        });
    const tr = (text) => translate(text, language),
        nodes = [],
        children = [],
        w = width - 16,
        details = model.metadata || {};
    let y = 0;
    function message(id, text, error) {
        const h = Math.max(
            72,
            Math.ceil((String(text).length * 7) / Math.max(80, w)) * 16 + 16
        );
        children.push(
            node('Area', id, rect(0, y, w, h), {
                label: tr(error ? 'Server error' : 'Status'),
                text,
                readOnly: true,
                notice: true,
                color: error ? 'error' : 'secondaryText'
            })
        );
        y += h + 8;
    }
    if (model.error || model.busy || model.uncertain)
        message(
            'adminDeleteSearchTypeStatus',
            tr(
                model.uncertain
                    ? 'The deletion result is unknown. Close this review and reload the schema before trying again.'
                    : model.error ||
                          (model.deleting
                              ? 'Deleting Search Type…'
                              : 'Checking objects and dependencies…')
            ),
            !!model.error || model.uncertain
        );
    if (details.table) {
        const summary = [
            details.title || model.identity,
            model.identity,
            tr('Project') + ': ' + (details.project || ''),
            tr('Table') + ': ' + details.table,
            tr('Objects (including retired)') + ': ' + (details.objects || 0),
            tr('Pipelines') +
                ': ' +
                ((details.pipelines || []).join(', ') || '0')
        ].join('\n');
        children.push(
            node('Area', 'adminDeleteSearchTypeSummary', rect(0, y, w, 156), {
                label: tr('Search Type'),
                text: summary,
                readOnly: true,
                notice: true
            })
        );
        y += 164;
        if (!model.canWrite && !model.error && !model.uncertain) {
            message(
                'adminDeleteSearchTypeBlocked',
                tr(
                    'This Search Type is in use. Remove its objects and dependencies before deleting it.'
                ),
                true
            );
            const blocks = [];
            for (const part of [
                ['aliases', 'Other registrations for this table'],
                ['usedPipelines', 'Pipelines with processes'],
                ['otherSchemas', 'Other schemas using this type']
            ])
                if ((details[part[0]] || []).length)
                    blocks.push(
                        tr(part[1]) + ': ' + details[part[0]].join(', ')
                    );
            for (const reference of details.references || [])
                blocks.push(reference.type + ': ' + reference.count);
            if (blocks.length)
                message('adminDeleteSearchTypeBlocks', blocks.join('\n'), true);
        }
        if (model.canWrite) {
            message(
                'adminDeleteSearchTypeWarning',
                tr(
                    'This deletes the empty table, empty pipelines and the node with its connections in this project. This editor cannot undo the deletion. Check scripts, naming rules and saved searches that refer to this type.'
                ),
                false
            );
            if (details.sharedRegistration)
                message(
                    'adminDeleteSharedRegistration',
                    tr(
                        'The shared Search Type registration is retained for other projects.'
                    ),
                    false
                );
            children.push(
                label(
                    'adminDeleteSearchTypeLabel',
                    rect(0, y, w, 44),
                    tr('Enter the Search Type identifier to confirm') +
                        '\n' +
                        model.identity,
                    {
                        wrap: true
                    }
                ),
                node(
                    'Field',
                    'adminDeleteSearchTypeName',
                    rect(0, y + 52, w, 38),
                    {
                        text: model.confirmation,
                        label: tr('Search Type identifier'),
                        enabled: !model.busy && !model.uncertain,
                        action: {
                            type: 'confirmation'
                        }
                    }
                )
            );
            y += 98;
        }
    }
    nodes.push(
        node(
            'Scroll',
            'adminDeleteSearchTypeViewport',
            rect(0, 0, width, Math.max(1, height - 96)),
            {
                contentHeight: y,
                scrollbarId: 'adminDeleteSearchTypeScrollBar',
                children
            }
        )
    );
    const narrow = width < 520;
    nodes.push(
        node(
            'Button',
            'adminDeleteSearchTypeCancel',
            rect(0, height - 84, narrow ? (width - 8) / 2 : 110, 36),
            {
                text: tr('Cancel'),
                enabled: !model.deleting,
                action: {
                    type: 'close'
                }
            }
        )
    );
    if (!model.uncertain)
        nodes.push(
            node(
                'Button',
                'adminDeleteSearchTypeReview',
                rect(
                    narrow ? (width + 8) / 2 : 118,
                    height - 84,
                    narrow ? (width - 8) / 2 : 150,
                    36
                ),
                {
                    text: tr('Review again'),
                    icon: 'refresh',
                    enabled: !model.busy,
                    action: {
                        type: 'reload'
                    }
                }
            )
        );
    nodes.push(
        node(
            'Button',
            'adminDeleteSearchTypeApply',
            rect(0, height - 40, width, 38),
            {
                text: tr('Delete from project'),
                icon: 'delete',
                destructive: true,
                enabled:
                    model.canWrite &&
                    !model.busy &&
                    !model.uncertain &&
                    model.confirmation === model.identity,
                action: {
                    type: 'delete'
                }
            }
        )
    );
    return {
        nodes
    };
}
