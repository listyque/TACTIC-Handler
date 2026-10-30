import {
    node,
    rect,
    label,
    button,
    listRowHeight
} from '../../../core/frame.mjs';
import * as Composition from '../layouts/layout.preview.mjs';

export const russian = {
    Resources: 'Состав пакета',
    'Add resource': 'Добавить ресурс',
    'Resource type': 'Тип ресурса',
    'Resource name': 'Имя ресурса',
    'Python action': 'Python-действие',
    'Project data': 'Данные проекта',
    'Search Type': 'Тип объектов',
    'Record code (empty = all records)': 'Код записи (пусто = все записи)',
    'Include table schema': 'Включить схему таблицы',
    'Activate this package to edit its project resources. Inspect packaged files before activation.':
        'Активируйте пакет для редактирования его ресурсов в проекте. До активации проверьте файлы пакета.',
    'Add a widget, column, theme, Python action or selected project data.':
        'Добавьте виджет, колонку, тему, Python-действие или выбранные данные проекта.',
    Source: 'Исходник',
    'Saved preview': 'Предпросмотр сохранённого',
    'Save validates the resource, updates the project and exports it into the package.':
        'Сохранение проверяет ресурс, обновляет проект и экспортирует его в пакет.',
    'Apply theme to project': 'Применить тему к проекту',
    'Use personal appearance': 'Использовать личное оформление',
    'Theme style': 'Стиль темы',
    'Light base': 'Светлый фон',
    'Light accent': 'Светлый акцент',
    'Dark base': 'Тёмный фон',
    'Dark accent': 'Тёмный акцент',
    'Install and removal hooks are Python files referenced by python path/undo_path in Manifest XML.':
        'Обработчики установки и удаления — Python-файлы, указанные в python path/undo_path в XML манифеста.',
    'Review data selection in Manifest XML before publishing. Removing the plugin removes its selected records.':
        'Перед публикацией проверьте выборку данных в XML манифеста. Удаление плагина удаляет выбранные записи.',
    'Resource added to this project and package.':
        'Ресурс добавлен в проект и пакет.',
    'Project theme applied. Personal appearance settings are preserved.':
        'Тема проекта применена. Личные настройки оформления сохранены.',
    'Personal appearance restored.': 'Личное оформление восстановлено.',
    'Install/removal hooks': 'Обработчики установки и удаления',
    'Run Python action': 'Выполнить Python-действие',
    'Arguments (JSON object)': 'Аргументы (JSON-объект)',
    'Run this trusted server Python action? It may modify project data.':
        'Выполнить этот доверенный Python-код на сервере? Он может изменить данные проекта.',
    'Action result': 'Результат действия',
    Schema: 'Схема',
    Script: 'Скрипт',
    Configuration: 'Конфигурация'
};
const names = {
    widget: 'Widget',
    column: 'Column',
    theme: 'Theme',
    python: 'Python action',
    script: 'Script',
    data: 'Project data',
    hooks: 'Install/removal hooks'
};
const icons = {
    widget: 'extension',
    column: 'view-column',
    theme: 'appearance',
    python: 'code',
    script: 'code',
    data: 'table-view',
    search_type: 'table-view',
    include: 'code',
    plugin: 'extension'
};

export function row(list, entry, model, tr) {
    const w = Math.max(0, list.width - 16),
        h = listRowHeight(list);
    return {
        nodes: [
            node('Box', 'pluginResourceBackground', rect(0, 0, w, h), {
                background:
                    model.document?.resource?.key === entry.key
                        ? 'contentSelection'
                        : 'transparent',
                radius: 0
            }),
            node('Icon', 'pluginResourceIcon', rect(8, 10, 24, 24), {
                icon: icons[entry.kind] || 'settings'
            }),
            label('pluginResourceTitle', rect(44, 0, w - 48, 24), entry.title, {
                weight: 600
            }),
            label(
                'pluginResourceKind',
                rect(44, 24, w - 48, Math.min(22, h - 24)),
                tr(
                    names[entry.kind] ||
                        {
                            search_type: 'Schema',
                            configuration: 'Configuration'
                        }[entry.kind] ||
                        entry.kind
                ) +
                    (entry.searchType ? ' · ' + entry.searchType : '') +
                    (entry.count === undefined ? '' : ' · ' + entry.count),
                { color: 'secondaryText', fontRole: 'secondary' }
            ),
            node('Action', 'pluginResourceSelect', rect(0, 0, w, h), {
                text: entry.title,
                selected: model.document?.resource?.key === entry.key,
                enabled: !model.busy && !!(entry.field || entry.path),
                action: entry.field
                    ? { type: 'resource', key: entry.key }
                    : { type: 'file', path: entry.path, directory: false }
            })
        ]
    };
}

export function themeSource(source, field, value) {
    const parts = field.split('_'),
        mode = field === 'style' ? 'theme' : parts[0],
        key = field === 'style' ? 'style' : parts[1];
    return source.replace(new RegExp('<' + mode + '\\b[^>]*>'), (tag) =>
        tag.replace(
            new RegExp('(\\b' + key + '\\s*=\\s*)(["\x27])(.*?)\\2'),
            (_, prefix, quote) => prefix + quote + value + quote
        )
    );
}

export function describe(model, ui, width, height, language, tr) {
    const nodes = [],
        meta = model.metadata || {},
        resource = model.document?.resource,
        writable = model.canWrite && !model.busy && !model.uncertain,
        clean = !model.busy && !model.uncertain && !model.dirty;
    let y = 0;
    const text = (id, value, h = 44) => {
        nodes.push(
            label(id, rect(0, y, width, h), tr(value), {
                wrap: true,
                color: 'secondaryText'
            })
        );
        y += h + 8;
    };
    const action = (id, title, icon, event, enabled = clean) =>
        button(id, rect(0, 0, width, 36), tr(title), icon, event, enabled);
    if (!meta.active) {
        text(
            'pluginInactiveResources',
            'Activate this package to edit its project resources. Inspect packaged files before activation.',
            72
        );
        return { nodes, height: y };
    }
    const add = action(
        'pluginAddResource',
        'Add resource',
        'add',
        {
            type: 'resource-add'
        },
        clean && model.canWrite
    );
    add.width = Math.min(240, width);
    nodes.push(add);
    y += 44;
    if (ui.resourceAdd) {
        const input = (field, title, options = null) => {
            nodes.push(
                label(
                    'pluginResourceLabel_' + field,
                    rect(0, y, width, 24),
                    tr(title)
                )
            );
            y += 28;
            nodes.push(
                node(
                    options ? 'Choice' : 'Field',
                    'pluginResourceInput_' + field,
                    rect(0, y, width, 40),
                    Object.assign(
                        {
                            label: tr(title),
                            action: { type: 'input', field },
                            enabled: !model.busy
                        },
                        options
                            ? { value: ui[field], options }
                            : { text: ui[field] || '' }
                    )
                )
            );
            y += 48;
        };
        input(
            'resourceKind',
            'Resource type',
            Object.keys(names).map((value) => ({
                value,
                label: tr(names[value])
            }))
        );
        input('resourceName', 'Resource name');
        if (ui.resourceKind === 'data') {
            input('resourceType', 'Search Type', meta.dataTypes || []);
            input('resourceCode', 'Record code (empty = all records)');
            nodes.push(
                node(
                    'CheckBox',
                    'pluginResourceSchema',
                    rect(0, y, width, 36),
                    {
                        text: tr('Include table schema'),
                        checked: ui.resourceSchema,
                        action: { type: 'input', field: 'resourceSchema' }
                    }
                )
            );
            y += 44;
            text(
                'pluginDataRemovalHint',
                'Review data selection in Manifest XML before publishing. Removing the plugin removes its selected records.',
                60
            );
        }
        const create = action(
            'pluginResourceCreate',
            'Add resource',
            'add',
            { type: 'resource-create' },
            clean &&
                !!ui.resourceName?.trim() &&
                (ui.resourceKind !== 'data' || !!ui.resourceType)
        );
        create.y = y;
        create.width = Math.min(width / 2 - 4, 240);
        nodes.push(create);
        const cancel = action(
            'pluginResourceCancel',
            'Cancel',
            'close',
            { type: 'resource-cancel' },
            !model.busy
        );
        cancel.x = create.width + 8;
        cancel.y = y;
        cancel.width = Math.min(width - create.width - 8, 160);
        nodes.push(cancel);
        y += 48;
    }
    text(
        'pluginResourceHint',
        'Add a widget, column, theme, Python action or selected project data.'
    );
    const wide = width >= 700,
        listTop = y,
        listHeight = wide ? Math.max(240, height - y - 16) : 192,
        editorStart = nodes.length + 1;
    nodes.push(
        node(
            'List',
            'pluginResources',
            rect(0, y, wide ? 240 : width, listHeight),
            {
                source: 'pluginResources',
                keyField: 'key',
                fields: [
                    'key',
                    'kind',
                    'title',
                    'searchType',
                    'field',
                    'path',
                    'count'
                ],
                rowHeight: 48,
                scrollbarId: 'pluginResourceScroll',
                scrollbarReserved: 16,
                label: tr('Resources'),
                resetKey: model.identity
            }
        )
    );
    if (wide) width -= 252;
    else y += 204;
    if (resource) {
        nodes.push(
            label(
                'pluginResourceSelected',
                rect(0, y, width, 28),
                resource.title,
                { weight: 600 }
            )
        );
        y += 36;
        if (resource.validationError) {
            nodes.push(
                label(
                    'pluginResourceValidation',
                    rect(0, y, width, 64),
                    resource.validationError,
                    { wrap: true, color: 'error' }
                )
            );
            y += 72;
        }
        if (resource.kind === 'python') {
            nodes.push(
                label(
                    'pluginPythonInputsLabel',
                    rect(0, y, width, 24),
                    tr('Arguments (JSON object)')
                )
            );
            y += 28;
            nodes.push(
                node('Area', 'pluginPythonInputs', rect(0, y, width, 76), {
                    text: ui.resourceArguments || '{}',
                    enabled: !model.busy,
                    action: { type: 'input', field: 'resourceArguments' }
                })
            );
            y += 84;
            const run = action(
                'pluginPythonRun',
                'Run Python action',
                'play-arrow',
                { type: 'operation', action: 'run_resource' }
            );
            run.y = y;
            nodes.push(run);
            y += 44;
            if (meta.runResult !== undefined) {
                text('pluginPythonResultLabel', 'Action result', 24);
                nodes.push(
                    label(
                        'pluginPythonResult',
                        rect(0, y, width, 100),
                        JSON.stringify(meta.runResult, null, 2),
                        { wrap: true }
                    )
                );
                y += 108;
            }
        }
        if (resource.kind === 'theme' && resource.palette) {
            const tools = [
                [
                    'pluginApplyTheme',
                    'Apply theme to project',
                    'palette',
                    'apply_theme'
                ],
                [
                    'pluginResetTheme',
                    'Use personal appearance',
                    'reset',
                    'reset_theme'
                ]
            ];
            for (const [id, title, icon, operation] of tools) {
                const b = action(id, title, icon, {
                    type: 'run',
                    action: operation,
                    values: { resource: resource.key }
                });
                b.y = y;
                nodes.push(b);
                y += 44;
            }
            nodes.push(
                node('Choice', 'pluginThemeStyle', rect(0, y, width, 40), {
                    label: tr('Theme style'),
                    value: resource.palette?.style || 'md3',
                    enabled: writable,
                    options: ['md3', 'material5', 'fluent'].map((value) => ({
                        value,
                        label: value
                    })),
                    action: { type: 'resource-theme', field: 'style' }
                })
            );
            y += 48;
            for (const mode of ['light', 'dark'])
                for (const color of ['base', 'accent']) {
                    const field = mode + '_' + color,
                        title =
                            (mode === 'light' ? 'Light' : 'Dark') + ' ' + color;
                    nodes.push(
                        label(
                            'pluginThemeLabel_' + field,
                            rect(0, y, width, 24),
                            tr(title)
                        )
                    );
                    y += 28;
                    nodes.push(
                        node(
                            'ColorChoice',
                            'pluginTheme_' + field,
                            rect(0, y, Math.min(width, 400), 40),
                            {
                                label: tr(title),
                                value: resource.palette?.[mode]?.[color] || '',
                                enabled: writable,
                                action: { type: 'resource-theme', field }
                            }
                        )
                    );
                    y += 48;
                }
        }
        if (resource.layout) {
            nodes.push(
                node('Segmented', 'pluginResourceMode', rect(0, y, width, 36), {
                    label: tr('Resources'),
                    value: ui.resourceMode,
                    options: ['source', 'preview'].map((value) => ({
                        value,
                        label: tr(
                            value === 'source' ? 'Source' : 'Saved preview'
                        )
                    })),
                    action: { type: 'input', field: 'resourceMode' }
                })
            );
            y += 44;
        }
        if (resource.layout && ui.resourceMode === 'preview') {
            const previewWidth = Math.min(
                width,
                resource.kind === 'column' ? 320 : 480
            );
            const scene = Composition.describe(
                resource.layout,
                resource.sample,
                previewWidth,
                '',
                language,
                width,
                '',
                'pluginResourcePreview',
                0,
                true
            );
            nodes.push(
                node(
                    'Box',
                    'pluginResourcePreview',
                    rect(0, y, width, scene.height),
                    { children: scene.nodes }
                )
            );
            y += scene.height + 12;
        } else {
            text(
                'pluginResourceSaveHint',
                'Save validates the resource, updates the project and exports it into the package.',
                52
            );
            const h = Math.max(300, height - y);
            nodes.push(
                node('Code', 'pluginResourceSource', rect(0, y, width, h), {
                    text: resource.source,
                    syntax:
                        resource.field === 'script'
                            ? resource.kind === 'python'
                                ? 'python'
                                : 'javascript'
                            : 'xml',
                    language,
                    service: 'sourceEditor',
                    bufferKey: model.identity + ':' + resource.key,
                    readOnly: !writable,
                    action: { type: 'field', field: 'resource_source' }
                })
            );
            y += h + 12;
        }
    } else
        text(
            'pluginHooksHint',
            'Install and removal hooks are Python files referenced by python path/undo_path in Manifest XML.',
            56
        );
    if (wide) {
        for (const child of nodes.slice(editorStart)) child.x += 252;
        y = Math.max(y, listTop + listHeight);
    }
    return { nodes, height: y };
}
