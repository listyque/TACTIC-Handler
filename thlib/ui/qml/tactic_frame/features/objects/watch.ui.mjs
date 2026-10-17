import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const desktopReason =
    'Watch Folders require a desktop connection, which is not enabled in this web version.';

export function available(repositories, selected, language) {
    return repositories
        .filter((row) => selected.indexOf(row.value) < 0)
        .concat({ value: '__all__', label: translate('All Repos', language) });
}

export function repositoryRow(model, row, width, language) {
    return {
        nodes: [
            node('Box', 'watchRepositorySurface', rect(0, 0, width, 40), {
                background: 'row',
                radius: 10
            }),
            label(
                'watchRepositoryName',
                rect(10, 0, width - 52, 40),
                row.label
            ),
            button(
                'watchRepositoryRemove',
                rect(Math.max(0, width - 38), 4, 32, 32),
                translate('Remove', language),
                'delete',
                { type: 'remove', value: row.value },
                !model.busy,
                { destructive: true, iconOnly: true }
            )
        ]
    };
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const w = Math.max(0, width - 32),
        nodes = [
            node('Box', 'watchEditorSurface', rect(0, 0, width, height), {
                background: 'workspace',
                radius: 0
            })
        ];
    if (model.desktop === false)
        return {
            nodes: nodes.concat(
                label(
                    'watchDesktopRequired',
                    rect(16, 16, w, Math.max(36, height - 32)),
                    tr(desktopReason),
                    { wrap: true, color: 'secondaryText' }
                )
            )
        };
    const narrow = width < 500,
        labelWidth = Math.min(
            width * 0.45,
            tr('Relative Watch Path:').length * 5.8
        );
    nodes.push(
        label(
            'watchPathLabel',
            rect(16, 16, narrow ? w : labelWidth, 36),
            tr('Relative Watch Path:')
        )
    );
    nodes.push(
        node(
            'Field',
            'watchPath',
            rect(
                narrow ? 16 : 24 + labelWidth,
                narrow ? 52 : 16,
                narrow ? w : width - 40 - labelWidth,
                36
            ),
            {
                text: model.path || '',
                label: tr('Relative Watch Path:'),
                enabled: !model.busy,
                action: { type: 'path' }
            }
        )
    );
    const top = narrow ? 100 : 64;
    nodes.push(
        node('Choice', 'watchRepositoryChoice', rect(16, top, w - 96, 36), {
            options: model.available,
            value: model.choice,
            label: tr('Repository'),
            enabled: !model.busy,
            action: { type: 'choice' }
        })
    );
    nodes.push(
        button(
            'watchRepositoryAdd',
            rect(width - 100, top, 84, 36),
            tr('Add'),
            'add',
            { type: 'add' },
            !model.busy && !!model.choice
        )
    );
    const bottom = height - 52,
        errorHeight = model.error ? 44 : 0;
    const listTop = top + 48,
        listHeight = Math.max(0, bottom - errorHeight - listTop - 12);
    nodes.push(
        node(
            'Box',
            'watchRepositoriesSurface',
            rect(16, listTop, w, listHeight),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 10
            }
        )
    );
    nodes.push(
        node(
            'List',
            'watchRepositories',
            rect(
                22,
                listTop + 6,
                Math.max(0, w - 12),
                Math.max(0, listHeight - 12)
            ),
            {
                source: 'repositories',
                keyField: 'value',
                fields: ['value', 'label'],
                rowHeight: 44,
                rowGap: 4
            }
        )
    );
    if (!model.selectedCount)
        nodes.push(
            label(
                'watchEmpty',
                rect(32, listTop, w - 32, listHeight),
                tr('No repositories selected'),
                { color: 'secondaryText', align: 'center' }
            )
        );
    if (model.error)
        nodes.push(
            label(
                'watchEditorError',
                rect(16, bottom - 44, w, 36),
                model.error,
                { color: 'error', wrap: true, role: 'alert' }
            )
        );
    nodes.push(
        button(
            'watchEditorCancel',
            rect(Math.max(16, width - 292), bottom, 100, 36),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'watchEditorSave',
            rect(Math.max(122, width - 184), bottom, 168, 36),
            tr('Save and Close'),
            'save',
            { type: 'save' },
            !!model.canSave && !model.busy,
            { highlighted: true }
        )
    );
    if (model.busy)
        nodes.push(
            label(
                'watchPreparing',
                rect(16, bottom - 36, w, 30),
                tr('Preparing watch folder…'),
                { role: 'status', color: 'secondaryText' }
            )
        );
    return { nodes };
}
