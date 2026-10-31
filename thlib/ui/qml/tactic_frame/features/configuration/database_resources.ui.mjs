import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { spacing } from '../../core/foundation.mjs';
import { describe as confirmation } from '../../controls/feedback/confirmation.ui.mjs';

export function describe(model, width, language) {
    const tr = (key) => translate(key, language);
    const inset = spacing.content,
        gap = spacing.compact,
        body = width - 2 * inset;
    const enabled = !!model.canWrite && !model.busy && !model.uncertain;
    const saved = model.identity && model.identity !== 'new';
    const clean = enabled && saved && !model.dirty;
    const document = model.document || {},
        metadata = model.metadata || {};
    if (model.confirm) {
        const messages = {
            delete: 'Delete this unused connection? Project databases and their data will remain intact.',
            bind: 'Change the project connection? Existing data is not moved. Verify that the target database contains the project data.',
            unbind: 'Use the server default connection for this project? Existing data is not moved.',
            upgrade:
                'Update the bound project database schema? Configuration migrations run in a transaction. Back up this database before proceeding.',
            save: 'Change this connection for its bound projects? Their next requests will use the new connection. Existing data is not moved.'
        };
        return Object.assign(
            confirmation(
                {
                    message: tr(messages[model.confirm]),
                    accept: 'Continue',
                    reject: 'Cancel',
                    busy: model.busy,
                    acceptId: 'databaseResourceConfirm',
                    rejectId: 'databaseResourceReject'
                },
                width,
                220,
                language
            ),
            { height: 220 }
        );
    }
    const nodes = [];
    let y = inset;
    function text(id, value, height = 24, props = {}) {
        nodes.push(label(id, rect(inset, y, body, height), tr(value), props));
        y += height + gap;
    }
    if (!model.canWrite && !model.busy) {
        text(
            'resourceAccess',
            'Database resources require administrator access',
            60,
            { wrap: true }
        );
        return { nodes, height: y };
    }
    nodes.push(
        node(
            'Choice',
            'resourceSelector',
            rect(inset, y, Math.max(80, body - 88), 38),
            {
                value: model.identity,
                options: (model.catalog || []).map((row) => ({
                    value: row.identity,
                    label:
                        row.identity === 'new' ? tr('New resource') : row.title
                })),
                enabled: enabled && !model.dirty,
                action: { type: 'select' },
                label: tr('Database resource')
            }
        )
    );
    nodes.push(
        button(
            'resourceNew',
            rect(width - inset - 80, y, 36, 36),
            tr('New resource'),
            'add',
            { type: 'new' },
            enabled && !model.dirty,
            { iconOnly: true }
        )
    );
    nodes.push(
        button(
            'resourceRefresh',
            rect(width - inset - 36, y, 36, 36),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy && (!model.dirty || model.uncertain),
            { iconOnly: true }
        )
    );
    y += 38 + spacing.section;
    if (model.busy) text('resourceBusy', 'Working…');
    if (model.error)
        text('resourceError', model.error, 60, { wrap: true, color: 'error' });
    if (metadata.notice)
        text('resourceNotice', metadata.notice, 44, { wrap: true });
    if (model.uncertain)
        text(
            'resourceUncertain',
            'The save result is unknown. Reload before editing again.',
            60,
            { wrap: true, color: 'error' }
        );
    const fields = [
        ['code', 'Resource code', 'Field'],
        ['vendor', 'Database engine', 'Choice'],
        ['host', 'Database host', 'Field'],
        ['port', 'Database port', 'Field'],
        ['login', 'Database user', 'Field'],
        [
            'password',
            metadata.hasPassword
                ? 'Replacement password (leave empty to keep)'
                : 'Database password',
            'Field'
        ]
    ];
    const columns = width >= 640 ? 2 : 1,
        cell = (body - gap * (columns - 1)) / columns;
    fields.forEach(([key, title, kind], index) => {
        const x = inset + (index % columns) * (cell + gap),
            row = y + Math.floor(index / columns) * 76;
        nodes.push(
            label('resourceLabel_' + key, rect(x, row, cell, 24), tr(title))
        );
        nodes.push(
            node(kind, 'resourceField_' + key, rect(x, row + 28, cell, 38), {
                value: document[key] || '',
                text: document[key] || '',
                label: tr(title),
                enabled: enabled && (key !== 'code' || !saved),
                password: key === 'password',
                action: { type: 'field', field: key },
                options:
                    key === 'vendor'
                        ? [
                              { value: 'PostgreSQL', label: 'PostgreSQL' },
                              { value: 'Sqlite', label: 'SQLite' }
                          ]
                        : []
            })
        );
    });
    y += Math.ceil(fields.length / columns) * 76;
    nodes.push(
        node('CheckBox', 'resourceClearPassword', rect(inset, y, body, 36), {
            text: tr('Clear stored password'),
            checked: !!document.clearPassword,
            enabled: enabled && !!metadata.hasPassword,
            action: { type: 'field', field: 'clearPassword' }
        })
    );
    y += 44;
    text(
        'resourceSaveHint',
        'Save connection changes before testing or changing project bindings.',
        44,
        { wrap: true, color: 'muted' }
    );
    const buttons = [
        ['save', 'Save connection', 'save', enabled && model.dirty],
        ['discard', 'Discard changes', 'undo', !model.busy && model.dirty],
        ['delete', 'Delete connection', 'delete', clean]
    ];
    const buttonColumns = width >= 640 ? 3 : 1,
        buttonWidth = (body - gap * (buttonColumns - 1)) / buttonColumns;
    buttons.forEach(([type, title, icon, active], index) =>
        nodes.push(
            button(
                'resource_' + type,
                rect(
                    inset + (index % buttonColumns) * (buttonWidth + gap),
                    y + Math.floor(index / buttonColumns) * 44,
                    buttonWidth,
                    36
                ),
                tr(title),
                icon,
                { type },
                active,
                { destructive: type === 'delete', highlighted: type === 'save' }
            )
        )
    );
    y += Math.ceil(buttons.length / buttonColumns) * 44 + spacing.section;
    text('resourceDatabaseTitle', 'Connection and schema', 24, { bold: true });
    nodes.push(
        node('Field', 'resourceDatabase', rect(inset, y, body, 38), {
            text: model.database || '',
            label: tr('Database name'),
            placeholder: tr('Database name'),
            enabled: clean,
            action: { type: 'database' }
        })
    );
    y += 46;
    const targets = [
        ['test', 'Test connection', 'link'],
        ['upgrade', 'Update schema', 'database']
    ];
    targets.forEach(([type, title, icon], index) =>
        nodes.push(
            button(
                'resource_' + type,
                rect(
                    inset + ((index % columns) * (body + gap)) / columns,
                    y + Math.floor(index / columns) * 44,
                    (body - gap * (columns - 1)) / columns,
                    36
                ),
                tr(title),
                icon,
                { type },
                clean && !!model.database
            )
        )
    );
    y += Math.ceil(targets.length / columns) * 44 + spacing.section;
    text('resourceProjectTitle', 'Project connection', 24, { bold: true });
    nodes.push(
        node('Choice', 'resourceProject', rect(inset, y, body, 38), {
            value: model.project || '',
            options: (metadata.projects || [])
                .filter((row) => !row.retired)
                .map((row) => ({
                    value: row.code,
                    label: row.title + ' · ' + row.database
                })),
            enabled: clean,
            label: tr('Project'),
            action: { type: 'project' }
        })
    );
    y += 46;
    [
        ['bind', 'Bind project'],
        ['unbind', 'Use server defaults']
    ].forEach(([type, title], index) =>
        nodes.push(
            button(
                'resource_' + type,
                rect(
                    inset + ((index % columns) * (body + gap)) / columns,
                    y + Math.floor(index / columns) * 44,
                    (body - gap * (columns - 1)) / columns,
                    36
                ),
                tr(title),
                'link',
                { type },
                clean && !!model.project
            )
        )
    );
    y += Math.ceil(2 / columns) * 44;
    text(
        'resourceBindHint',
        'Binding changes the connection only. It does not create a database or copy project data.',
        60,
        { wrap: true, color: 'muted' }
    );
    text('resourceBindingsTitle', 'Bound projects', 24, { bold: true });
    const bound = (metadata.projects || []).filter(
        (row) => row.resource === model.identity
    );
    if (!bound.length)
        text('resourceNoBindings', 'No projects use this connection', 36, {
            wrap: true
        });
    bound.forEach((row, index) =>
        text('resourceBound_' + index, row.title + ' · ' + row.database, 36, {
            wrap: true
        })
    );
    return { nodes, height: y + inset };
}

export function page(model, width, height, language) {
    const content = describe(
        model,
        Math.max(0, width - spacing.content),
        language
    );
    return {
        nodes: [
            node('Scroll', 'resourceScroll', rect(0, 0, width, height), {
                contentHeight: content.height,
                scrollbarId: 'resourceScrollbar',
                children: content.nodes
            })
        ]
    };
}
