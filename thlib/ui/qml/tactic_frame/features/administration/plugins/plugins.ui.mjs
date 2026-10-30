import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate as commonTranslate } from '../../../core/strings.mjs';

const russian = {
    New: 'Создать',
    Activate: 'Активировать',
    Information: 'Информация',
    Files: 'Файлы',
    Widget: 'Виджет',
    Column: 'Колонка',
    Theme: 'Тема',
    Confirm: 'Подтвердить',
    'Plugin sections': 'Разделы плагина',
    'Discard unsaved changes and reload the plugin catalogue?':
        'Сбросить несохранённые изменения и обновить каталог плагинов?',
    'Plugin catalogue': 'Каталог плагинов',
    'Install plugin': 'Установить плагин',
    'Search plugins': 'Поиск плагинов',
    'Active in this project': 'Активен в этом проекте',
    'Create plugin': 'Создать плагин',
    'New plugin': 'Новый плагин',
    'Built-in plugin · read-only files':
        'Встроенный плагин · файлы только для чтения',
    'Not active in this project': 'Не активен в этом проекте',
    'Select a plugin, create a new package or install a ZIP.':
        'Выберите плагин, создайте пакет или установите ZIP.',
    'The operation result is unknown. Reload before continuing.':
        'Результат операции неизвестен. Обновите данные перед продолжением.',
    'Working…': 'Выполняется…',
    'Reload removes and reinstalls the plugin in this project. Its data may be replaced.':
        'Перезагрузка удалит и заново установит плагин в этом проекте. Его данные могут быть заменены.',
    'Remove this plugin and its manifest-defined data from the current project?':
        'Удалить плагин и описанные его манифестом данные из текущего проекта?',
    'Clean all project entries described by this plugin manifest?':
        'Удалить из проекта все записи, описанные манифестом этого плагина?',
    'Delete this package from the server? It must be inactive in every project.':
        'Удалить пакет с сервера? Он должен быть отключён во всех проектах.',
    'Delete the selected plugin file or folder and its contents?':
        'Удалить выбранный файл или папку плагина со всем содержимым?',
    'Delete all generated .spt files in this package?':
        'Удалить все сгенерированные файлы .spt в этом пакете?',
    'New file': 'Новый файл',
    'New folder': 'Новая папка',
    'Rename or move': 'Переименовать или переместить',
    'Publish version': 'Опубликовать версию',
    'ZIP installation adds a package to the server. Activate it separately in the selected project. Plugins can execute trusted server code.':
        'Установка ZIP добавляет пакет на сервер. Активируйте его отдельно в выбранном проекте. Плагины могут выполнять доверенный код на сервере.',
    'Browse ZIP…': 'Выбрать ZIP…',
    'Plugin ZIP URL': 'Ссылка на ZIP плагина',
    'SHA-256 or MD5 (optional)': 'SHA-256 или MD5 (необязательно)',
    'Download ZIP': 'Загрузить ZIP',
    'Relative path': 'Относительный путь',
    'Remove from project': 'Удалить из проекта',
    'Reload plugin': 'Перезагрузить плагин',
    'Export ZIP': 'Экспорт ZIP',
    'Clean project data': 'Очистить данные проекта',
    'Delete package': 'Удалить пакет',
    'Manifest XML': 'Манифест XML',
    Documentation: 'Документация',
    'Plugin type': 'Тип плагина',
    'Empty plugin': 'Пустой плагин',
    'Project template': 'Шаблон проекта',
    'Export template': 'Экспорт шаблона',
    'Create a project template from the selected project.':
        'Создать шаблон из выбранного проекта.',
    'Parent folder': 'Родительская папка',
    'Upload file': 'Загрузить файл',
    'Clear .spt files': 'Очистить файлы .spt',
    'Download file': 'Скачать файл',
    'Replace file': 'Заменить файл',
    'Replace the selected file with a local upload?':
        'Заменить выбранный файл содержимым локального файла?',
    'This file is binary or exceeds 2 MiB. Download it to edit locally.':
        'Двоичный файл или размер больше 2 МиБ. Скачайте его для редактирования.',
    'Create documentation': 'Создать документацию',
    Inactive: 'Неактивен',
    'Plugin changed on the server. Reload before continuing.':
        'Плагин изменён на сервере. Обновите данные перед продолжением.',
    'File changed on the server. Reload before saving.':
        'Файл изменён на сервере. Обновите его перед сохранением.',
    'Use Publish to change a plugin code or version':
        'Для изменения кода или версии используйте публикацию',
    'Another version is active. Remove it from this project first.':
        'Активна другая версия. Сначала удалите её из этого проекта.',
    'Remove this plugin from every project before deleting its files':
        'Перед удалением файлов отключите плагин во всех проектах',
    'This plugin directory already exists; choose another version':
        'Каталог плагина уже существует. Выберите другую версию',
    'This plugin version already exists': 'Эта версия плагина уже существует',
    'A file or folder with that name already exists':
        'Файл или папка с таким именем уже существует',
    'Built-in plugin files are read-only':
        'Файлы встроенных плагинов доступны только для чтения',
    'Select a business project to activate or remove a plugin':
        'Выберите рабочий проект для активации или удаления плагина',
    'Enter a release version before publishing':
        'Укажите номер выпуска перед публикацией',
    'Plugin checksum does not match': 'Контрольная сумма плагина не совпадает'
};
export function translate(text, language) {
    return language === 'ru' && russian[text]
        ? russian[text]
        : commonTranslate(text, language);
}

export function initial() {
    return {
        query: '',
        activeOnly: false,
        tab: 'info',
        operation: '',
        value: '',
        url: '',
        checksum: '',
        collapsed: false
    };
}
export const toolbarGap = 8;
export const destructive = {
    replace_file: 'Replace the selected file with a local upload?',
    reload_catalog: 'Discard unsaved changes and reload the plugin catalogue?',
    reload: 'Reload removes and reinstalls the plugin in this project. Its data may be replaced.',
    deactivate:
        'Remove this plugin and its manifest-defined data from the current project?',
    clean: 'Clean all project entries described by this plugin manifest?',
    delete: 'Delete this package from the server? It must be inactive in every project.',
    delete_file: 'Delete the selected plugin file or folder and its contents?',
    clear_spt: 'Delete all generated .spt files in this package?'
};
export function catalog(model, ui) {
    const query = ui.query.trim().toLowerCase();
    return (model.catalog || []).filter(
        (row) =>
            (!ui.activeOnly || row.active) &&
            (!query ||
                [row.code, row.title, row.path]
                    .join(' ')
                    .toLowerCase()
                    .includes(query))
    );
}
const parent = (path) => path.split('/').slice(0, -1).join('/');
export function transition(ui, model, event) {
    const next = Object.assign({}, ui),
        commands = [],
        request = (action, values = {}) =>
            commands.push({ type: 'request', action, values }),
        blocked = model.busy || model.uncertain,
        clean = () => {
            if (model.dirty || model.uncertain) {
                commands.push({
                    type: 'error',
                    value: 'Apply or discard unsaved changes first'
                });
                return false;
            }
            return !model.busy;
        };
    if (event.type === 'help')
        commands.push({ type: 'help', topic: 'plugins' });
    else if (event.type === 'query') next.query = event.value;
    else if (event.type === 'activeOnly') next.activeOnly = event.value;
    else if (event.type === 'collapse') next.collapsed = !ui.collapsed;
    else if (event.type === 'input') next[event.field] = event.value;
    else if (event.type === 'field' && !blocked && model.canWrite)
        commands.push(event);
    else if (event.type === 'select' && clean()) {
        next.operation = '';
        next.tab = 'info';
        commands.push(event);
    } else if (event.type === 'tab' && clean()) {
        next.tab = event.value;
        next.operation = '';
        if (event.value === 'docs') {
            if (model.metadata.docsExist)
                request('open_file', { file: model.metadata.docs });
        } else if (model.document?.file) request('load');
    } else if (event.type === 'reload' && !model.busy) {
        if (model.dirty) next.operation = 'reload_catalog';
        else {
            commands.push({ type: 'discard' });
            request('list');
        }
    } else if (event.type === 'discard' && !model.busy) commands.push(event);
    else if (event.type === 'save' && !blocked) commands.push(event);
    else if (event.type === 'new' && clean()) {
        next.operation = '';
        next.tab = 'info';
        request('new');
    } else if (event.type === 'install' && clean()) {
        next.operation = 'install';
        next.url = '';
        next.checksum = '';
    } else if (event.type === 'file' && clean()) {
        next.tab = 'files';
        next.operation = '';
        request(
            event.directory ? 'browse' : 'open_file',
            event.directory
                ? { folder: event.path }
                : { file: event.path, folder: model.metadata.folder || '' }
        );
    } else if (event.type === 'docs_create' && clean()) {
        next.tab = 'docs';
        request('new_file', { path: model.metadata.docs });
    } else if (event.type === 'upload' && clean()) commands.push(event);
    else if (event.type === 'operation' && clean()) {
        next.operation = event.action;
        next.value =
            event.action === 'rename'
                ? model.document?.file?.path || model.metadata.folder || ''
                : '';
    } else if (event.type === 'cancel') next.operation = '';
    else if (
        event.type === 'confirm' &&
        ui.operation === 'reload_catalog' &&
        !model.busy
    ) {
        commands.push({ type: 'discard' });
        request('list');
        next.operation = '';
    } else if (event.type === 'confirm' && clean()) {
        const action = ui.operation,
            values = { confirmation: true };
        if (action === 'replace_file') {
            commands.push({ type: 'upload', package: false, replace: true });
        } else if (action === 'install') {
            values.url = ui.url;
            values.checksum = ui.checksum;
            request('download_url', values);
        } else {
            const selected =
                model.document?.file?.path || model.metadata.folder || '';
            if (['new_file', 'new_folder'].includes(action))
                values.path = [model.metadata.folder, ui.value]
                    .filter(Boolean)
                    .join('/');
            if (action === 'publish') values.version = ui.value;
            if (action === 'rename') {
                values.path = selected;
                values.destination = ui.value;
            }
            if (action === 'delete_file') values.path = selected;
            if (action === 'delete_file' || action === 'rename')
                values.folder = parent(selected);
            request(action, values);
        }
        next.operation = '';
    } else if (event.type === 'run' && clean())
        request(event.action, event.values || {});
    return { ui: next, commands };
}

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        busy = model.busy,
        commands = [
            ['pluginReload', 'Refresh', 'refresh', { type: 'reload' }, !busy],
            [
                'pluginDiscard',
                'Discard',
                'undo',
                { type: 'discard' },
                !busy && (model.dirty || model.uncertain)
            ],
            [
                'pluginSave',
                model.metadata?.new
                    ? model.document?.type === 'project'
                        ? 'Export template'
                        : 'Create plugin'
                    : 'Save',
                'save',
                { type: 'save' },
                !busy &&
                    !model.uncertain &&
                    model.canWrite &&
                    (model.dirty || model.metadata?.new)
            ]
        ];
    const compact = width < 420,
        save = compact ? 140 : 180,
        start = Math.max(0, width - save - (compact ? 96 : 192));
    let x = start;
    for (let index = 0; index < commands.length; index++) {
        const [id, text, icon, action, enabled] = commands[index],
            w = index === 2 ? save : index === 0 || compact ? 44 : 140;
        nodes.push(
            button(id, rect(x, 0, w, 40), tr(text), icon, action, enabled, {
                iconOnly: index === 0 || (compact && index !== 2)
            })
        );
        x += w + 4;
    }
    return { nodes };
}

export function describe(model, ui, width, height, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        gap = 12,
        compact = width < 760,
        nav = ui.collapsed ? 44 : compact ? 200 : 250,
        right = nav + gap,
        bodyWidth = Math.max(0, width - right),
        editable = !model.busy && !model.uncertain && model.canWrite,
        clean = !model.busy && !model.dirty && !model.uncertain,
        doc = model.document || {},
        meta = model.metadata || {},
        exists = !!model.identity;
    const btn = (id, r, text, icon, action, enabled = clean, extra = {}) =>
        button(id, r, tr(text), icon, action, enabled, extra);
    nodes.push(
        btn(
            'pluginCollapse',
            rect(0, 0, 40, 40),
            'Plugin catalogue',
            ui.collapsed ? 'next' : 'previous',
            { type: 'collapse' },
            true,
            { iconOnly: true }
        )
    );
    if (!ui.collapsed) {
        nodes.push(
            btn('pluginNew', rect(44, 0, nav - 88, 40), 'New', 'add', {
                type: 'new'
            })
        );
        nodes.push(
            btn(
                'pluginInstall',
                rect(nav - 40, 0, 40, 40),
                'Install plugin',
                'upload',
                { type: 'install' },
                clean,
                { iconOnly: true }
            )
        );
        nodes.push(
            node('Field', 'pluginSearch', rect(0, 48, nav, 40), {
                text: ui.query,
                placeholder: tr('Search plugins'),
                action: { type: 'query' },
                clearable: true
            })
        );
        nodes.push(
            node('CheckBox', 'pluginActiveOnly', rect(0, 96, nav, 36), {
                text: tr('Active in this project'),
                checked: ui.activeOnly,
                action: { type: 'activeOnly' }
            })
        );
        nodes.push(
            node(
                'List',
                'pluginCatalogue',
                rect(0, 140, nav, Math.max(0, height - 140)),
                {
                    source: 'plugins',
                    keyField: 'identity',
                    fields: [
                        'identity',
                        'title',
                        'code',
                        'version',
                        'builtin',
                        'active',
                        'path'
                    ],
                    rowHeight: 76,
                    rowGap: 0,
                    scrollbarId: 'pluginCatalogueScrollBar',
                    scrollbarReserved: 16
                }
            )
        );
    }
    let y = 0;
    if (model.error || model.uncertain) {
        const message =
            model.error ||
            'The operation result is unknown. Reload before continuing.';
        nodes.push(
            node('Area', 'pluginError', rect(right, y, bodyWidth, 72), {
                text: tr(message),
                readOnly: true,
                notice: true,
                wrap: true,
                color: 'red',
                role: 'alert'
            })
        );
        y += 80;
    }
    if (model.busy) {
        nodes.push(
            label('pluginBusy', rect(right, y, bodyWidth, 32), tr('Working…'), {
                color: 'secondaryText'
            })
        );
        y += 40;
    }
    if (ui.operation) {
        const content = [],
            w = Math.max(0, bodyWidth - 16);
        let oy = 0;
        const heading =
            destructive[ui.operation] ||
            {
                install: 'Install plugin',
                new_file: 'New file',
                new_folder: 'New folder',
                rename: 'Rename or move',
                publish: 'Publish version'
            }[ui.operation];
        content.push(
            label('pluginOperationTitle', rect(0, oy, w, 72), tr(heading), {
                wrap: true,
                weight: 600
            })
        );
        oy += 80;
        if (ui.operation === 'install') {
            content.push(
                label(
                    'pluginInstallNotice',
                    rect(0, oy, w, 64),
                    tr(
                        'ZIP installation adds a package to the server. Activate it separately in the selected project. Plugins can execute trusted server code.'
                    ),
                    { wrap: true }
                )
            );
            oy += 72;
            content.push(
                btn(
                    'pluginBrowseZip',
                    rect(0, oy, Math.min(w, 270), 40),
                    'Browse ZIP…',
                    'folder',
                    { type: 'upload', package: true }
                )
            );
            oy += 52;
            for (const [field, title] of [
                ['url', 'Plugin ZIP URL'],
                ['checksum', 'SHA-256 or MD5 (optional)']
            ]) {
                content.push(
                    label(
                        'pluginInstallLabel_' + field,
                        rect(0, oy, w, 24),
                        tr(title)
                    )
                );
                oy += 28;
                content.push(
                    node(
                        'Field',
                        'pluginInstall_' + field,
                        rect(0, oy, w, 40),
                        {
                            text: ui[field],
                            action: { type: 'input', field },
                            enabled: clean
                        }
                    )
                );
                oy += 52;
            }
        } else if (!destructive[ui.operation]) {
            content.push(
                node('Field', 'pluginOperationValue', rect(0, oy, w, 40), {
                    text: ui.value,
                    placeholder: tr(
                        ui.operation === 'publish' ? 'Version' : 'Relative path'
                    ),
                    action: { type: 'input', field: 'value' },
                    enabled: clean
                })
            );
            oy += 52;
        }
        content.push(
            btn(
                'pluginConfirm',
                rect(0, oy, Math.min(180, w / 2 - 4), 40),
                ui.operation === 'install' ? 'Download ZIP' : 'Confirm',
                'check',
                { type: 'confirm' },
                clean || (ui.operation === 'reload_catalog' && !model.busy)
            )
        );
        content.push(
            btn(
                'pluginCancel',
                rect(
                    Math.min(188, w / 2 + 4),
                    oy,
                    Math.min(150, w / 2 - 4),
                    40
                ),
                'Cancel',
                'close',
                { type: 'cancel' },
                !model.busy
            )
        );
        nodes.push(
            node(
                'Scroll',
                'pluginOperationScroll',
                rect(right, y, bodyWidth, height - y),
                {
                    contentHeight: oy + 52,
                    scrollbarId: 'pluginOperationScrollBar',
                    scrollbarReserved: 16,
                    children: content
                }
            )
        );
        return { nodes };
    }
    if (!exists && !meta.new) {
        nodes.push(
            label(
                'pluginEmpty',
                rect(right + 12, y + 24, bodyWidth - 24, 64),
                tr('Select a plugin, create a new package or install a ZIP.'),
                { wrap: true }
            )
        );
        nodes.push(
            btn(
                'pluginEmptyInstall',
                rect(right + 12, y + 100, Math.min(240, bodyWidth - 24), 40),
                'Install plugin',
                'upload',
                { type: 'install' }
            )
        );
        return { nodes };
    }
    nodes.push(
        label(
            'pluginTitle',
            rect(right, y, bodyWidth, 28),
            doc.title || doc.code || tr('New plugin'),
            { fontRole: 'title', weight: 600 }
        )
    );
    y += 36;
    nodes.push(
        label(
            'pluginStatus',
            rect(right, y, bodyWidth, 24),
            tr(
                meta.builtin
                    ? 'Built-in plugin · read-only files'
                    : meta.active
                      ? 'Active in this project'
                      : meta.new
                        ? 'New plugin'
                        : 'Not active in this project'
            ) + (doc.version ? ' · ' + doc.version : ' · DEV'),
            { color: 'secondaryText' }
        )
    );
    y += 32;
    if (exists) {
        const operations = [
            [
                meta.active ? 'deactivate' : 'activate',
                meta.active ? 'Remove from project' : 'Activate',
                'check'
            ],
            ['reload', 'Reload plugin', 'refresh'],
            ['export', 'Export ZIP', 'download'],
            ['publish', 'Publish version', 'publish'],
            ['clean', 'Clean project data', 'delete'],
            ['delete', 'Delete package', 'delete']
        ];
        let x = 0;
        for (const [action, title, icon] of operations) {
            if (
                (meta.builtin &&
                    ['export', 'publish', 'delete'].includes(action)) ||
                (action === 'reload' && !meta.active) ||
                (action === 'clean' && meta.active)
            )
                continue;
            const w = Math.min(
                bodyWidth,
                Math.max(compact ? 160 : 185, tr(title).length * 7.5 + 56)
            );
            if (x && x + w > bodyWidth) {
                x = 0;
                y += 44;
            }
            const permitted =
                !['admin', 'sthpw'].includes(meta.project) ||
                ['export', 'publish', 'delete'].includes(action);
            nodes.push(
                btn(
                    'pluginAction_' + action,
                    rect(right + x, y, w, 40),
                    title,
                    icon,
                    {
                        type:
                            destructive[action] || action === 'publish'
                                ? 'operation'
                                : 'run',
                        action
                    },
                    clean && permitted
                )
            );
            x += w + 6;
        }
        y += 52;
        const tabs = [
                ['info', 'Information'],
                ['manifest', 'Manifest XML'],
                ['files', 'Files'],
                ['docs', 'Documentation']
            ],
            tw = bodyWidth / tabs.length;
        nodes.push(
            node(
                bodyWidth < 540 ? 'Choice' : 'Segmented',
                'pluginTabs',
                rect(right, y, bodyWidth, 40),
                {
                    value: ui.tab,
                    options: tabs.map(([value, text]) => ({
                        value,
                        label: tr(text)
                    })),
                    action: { type: 'tab' },
                    enabled: !model.busy,
                    label: tr('Plugin sections')
                }
            )
        );
        y += 52;
    }
    const content = [],
        w = Math.max(0, bodyWidth - 16);
    let cy = 0;
    function field(name, title, area = false, readonly = false) {
        content.push(
            label('pluginLabel_' + name, rect(0, cy, w, 24), tr(title))
        );
        cy += 28;
        content.push(
            node(
                area ? 'Area' : 'Field',
                'pluginField_' + name,
                rect(0, cy, w, area ? 110 : 40),
                {
                    text: doc[name] || '',
                    readOnly: readonly || !editable,
                    enabled: !model.busy,
                    action: { type: 'field', field: name }
                }
            )
        );
        cy += area ? 122 : 52;
    }
    if (meta.new || ui.tab === 'info') {
        if (!meta.new || doc.type !== 'project') {
            field('title', 'Title');
            field('code', 'Code', false, !meta.new);
            if (!meta.new) field('version', 'Version', false, true);
            field('description', 'Description', true);
        } else {
            content.push(
                label(
                    'pluginTemplateNotice',
                    rect(0, cy, w, 64),
                    tr('Create a project template from the selected project.'),
                    { wrap: true }
                )
            );
            cy += 72;
        }
        if (meta.new) {
            content.push(
                label('pluginTypeLabel', rect(0, cy, w, 24), tr('Plugin type'))
            );
            cy += 28;
            content.push(
                node('Choice', 'pluginType', rect(0, cy, w, 40), {
                    value: doc.type || '',
                    options: [
                        ['', 'Empty plugin'],
                        ['project', 'Project template'],
                        ['widget', 'Widget'],
                        ['column', 'Column'],
                        ['theme', 'Theme']
                    ].map(([value, text]) => ({ value, label: tr(text) })),
                    action: { type: 'field', field: 'type' },
                    enabled: editable
                })
            );
            cy += 52;
        }
    } else if (ui.tab === 'manifest') {
        content.push(
            node(
                'Code',
                'pluginManifest',
                rect(0, 0, w, Math.max(260, height - y - 12)),
                {
                    text: doc.manifest || '',
                    syntax: 'xml',
                    language,
                    service: 'sourceEditor',
                    bufferKey: model.identity + ':manifest',
                    readOnly: !editable,
                    action: { type: 'field', field: 'manifest' }
                }
            )
        );
        cy = Math.max(260, height - y - 12);
    } else {
        const files = ui.tab === 'files';
        if (files) {
            const tools = [
                [
                    'parent',
                    'Parent folder',
                    'previous',
                    {
                        type: 'file',
                        path: parent(meta.folder || ''),
                        directory: true
                    }
                ],
                ['new_file', 'New file', 'add'],
                ['new_folder', 'New folder', 'folder'],
                ['rename', 'Rename or move', 'edit'],
                ['delete_file', 'Delete', 'delete'],
                ['upload', 'Upload file', 'upload'],
                ['clear_spt', 'Clear .spt files', 'delete']
            ];
            let x = 0;
            for (const [action, title, icon, event] of tools) {
                if (x + 40 > w) {
                    x = 0;
                    cy += 44;
                }
                const enabled =
                    clean &&
                    (action === 'parent'
                        ? !!meta.folder
                        : !meta.builtin &&
                          (!['rename', 'delete_file'].includes(action) ||
                              !!doc.file ||
                              !!meta.folder));
                content.push(
                    btn(
                        'pluginFileAction_' + action,
                        rect(x, cy, 40, 40),
                        title,
                        icon,
                        event || {
                            type: action === 'upload' ? 'upload' : 'operation',
                            action
                        },
                        enabled,
                        { iconOnly: true }
                    )
                );
                x += 44;
            }
            cy += 48;
            content.push(
                label(
                    'pluginFolderPath',
                    rect(0, cy, w, 26),
                    meta.folder || '/',
                    { color: 'secondaryText' }
                )
            );
            cy += 32;
            content.push(
                node(
                    'List',
                    'pluginFiles',
                    rect(
                        0,
                        cy,
                        w,
                        Math.min(
                            200,
                            Math.max(76, (meta.files || []).length * 40)
                        )
                    ),
                    {
                        source: 'files',
                        keyField: 'path',
                        fields: ['name', 'path', 'directory', 'size'],
                        rowHeight: 40,
                        scrollbarId: 'pluginFilesScrollBar',
                        scrollbarReserved: 16
                    }
                )
            );
            cy +=
                Math.min(200, Math.max(76, (meta.files || []).length * 40)) +
                12;
        }
        if (doc.file) {
            content.push(
                label(
                    'pluginFileName',
                    rect(0, cy, w - 92, 30),
                    doc.file.path,
                    { weight: 600 }
                )
            );
            content.push(
                btn(
                    'pluginFileReplace',
                    rect(w - 84, cy - 4, 40, 40),
                    'Replace file',
                    'upload',
                    { type: 'operation', action: 'replace_file' },
                    editable && clean,
                    { iconOnly: true }
                )
            );
            content.push(
                btn(
                    'pluginFileDownload',
                    rect(w - 40, cy - 4, 40, 40),
                    'Download file',
                    'download',
                    {
                        type: 'run',
                        action: 'download_file',
                        values: { path: doc.file.path }
                    },
                    clean,
                    { iconOnly: true }
                )
            );
            cy += 40;
            if (doc.file.content === null) {
                content.push(
                    label(
                        'pluginBinaryFile',
                        rect(0, cy, w, 70),
                        tr(
                            'This file is binary or exceeds 2 MiB. Download it to edit locally.'
                        ),
                        { wrap: true }
                    )
                );
                cy += 78;
            } else {
                content.push(
                    node(
                        'Code',
                        'pluginFileEditor',
                        rect(0, cy, w, Math.max(200, height - y - cy - 12)),
                        {
                            text: doc.file.content || '',
                            syntax: doc.file.path.endsWith('.py')
                                ? 'python'
                                : doc.file.path.endsWith('.xml')
                                  ? 'xml'
                                  : 'text',
                            language,
                            service: 'sourceEditor',
                            bufferKey: model.identity + ':' + doc.file.path,
                            readOnly: !editable,
                            action: { type: 'field', field: 'file_content' }
                        }
                    )
                );
                cy += Math.max(200, height - y - cy - 12);
            }
        } else if (!files) {
            content.push(
                btn(
                    'pluginCreateDocs',
                    rect(0, cy, Math.min(270, w), 40),
                    'Create documentation',
                    'add',
                    { type: 'docs_create' },
                    editable && clean
                )
            );
            cy += 48;
        }
    }
    nodes.push(
        node(
            'Scroll',
            'pluginEditorScroll',
            rect(right, y, bodyWidth, height - y),
            {
                contentHeight: cy + 12,
                scrollbarId: 'pluginEditorScrollBar',
                scrollbarReserved: 16,
                children: content
            }
        )
    );
    return { nodes };
}

export function row(list, record, model, language) {
    const tr = (text) => translate(text, language),
        w = Math.max(0, list.width - 16);
    if (list.id === 'pluginFiles')
        return {
            nodes: [
                button(
                    'pluginFile_' + record.path,
                    rect(0, 0, w, 40),
                    record.name,
                    record.directory ? 'folder' : 'file',
                    {
                        type: 'file',
                        path: record.path,
                        directory: record.directory
                    },
                    !model.busy,
                    {
                        selected: model.document?.file?.path === record.path,
                        alignment: 'left'
                    }
                )
            ]
        };
    return {
        nodes: [
            node('Box', 'pluginRowBackground', rect(0, 0, w, 76), {
                background:
                    model.identity === record.identity
                        ? 'contentSelection'
                        : 'transparent',
                radius: 0
            }),
            node('Icon', 'pluginRowIcon', rect(4, 10, 24, 24), {
                icon: 'extension'
            }),
            label(
                'pluginRowTitle',
                rect(36, 2, w - 44, 28),
                record.title || record.code,
                { weight: 600 }
            ),
            label(
                'pluginRowStatus',
                rect(36, 30, w - 44, 22),
                [
                    record.version || 'DEV',
                    record.builtin ? tr('Built-in') : '',
                    tr(record.active ? 'Active' : 'Inactive')
                ]
                    .filter(Boolean)
                    .join(' · '),
                { color: 'secondaryText' }
            ),
            label('pluginRowPath', rect(36, 52, w - 44, 22), record.path, {
                color: 'secondaryText',
                fontRole: 'secondary'
            }),
            node('Action', 'pluginSelect', rect(0, 0, w, 76), {
                text: record.title || record.code,
                action: { type: 'select', identity: record.identity },
                enabled: !model.busy
            })
        ]
    };
}
