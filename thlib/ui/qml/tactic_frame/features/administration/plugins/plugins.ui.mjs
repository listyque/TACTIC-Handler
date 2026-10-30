import {
    initial,
    transition,
    catalog,
    destructive,
    canCreate
} from './plugins.state.mjs';
export { initial, transition, catalog, destructive, canCreate };
import * as Guide from './plugins.guide.mjs';
import * as Resources from './plugins.resources.mjs';
import {
    node,
    rect,
    label,
    button,
    listRowHeight
} from '../../../core/frame.mjs';
import { translate as commonTranslate } from '../../../core/strings.mjs';

const russian = {
    'Package source': 'Источник пакета',
    Overview: 'Обзор',
    'Plugin guide': 'Руководство по плагинам',
    'More actions': 'Другие действия',
    'Add capabilities to your project': 'Расширьте возможности проекта',
    'Install a ready-made package or create your own. A package lives on the server; activation applies it to the selected project.':
        'Установите готовый пакет или создайте свой. Пакет хранится на сервере, а активация применяет его к выбранному проекту.',
    'Choose a package': 'Выберите пакет',
    'Review its contents': 'Проверьте содержимое',
    'Activate in project': 'Активируйте в проекте',
    'Install a package': 'Установить пакет',
    'Have a plugin ZIP or download link? Upload it, review the manifest and documentation, then activate it in this project.':
        'Есть ZIP плагина или ссылка? Загрузите пакет, проверьте манифест и документацию, затем активируйте его в проекте.',
    'Create your own plugin': 'Создать свой плагин',
    'Start with an empty package or a Widget, Column or Theme template. Add files and project data, then publish a version.':
        'Начните с пустого пакета или шаблона виджета, колонки, темы. Добавьте файлы и данные проекта, затем опубликуйте версию.',
    'First add the package to this server. Nothing is activated in your project until you review and confirm the next step.':
        'Сначала добавьте пакет на сервер. В проекте ничего не активируется, пока вы не проверите и не подтвердите следующий шаг.',
    'ZIP file': 'ZIP-файл',
    'Download link': 'Ссылка для загрузки',
    'Choose a ZIP containing manifest.xml and the plugin files. The file is uploaded from this computer to the selected server.':
        'Выберите ZIP с manifest.xml и файлами плагина. Архив будет загружен с этого компьютера на выбранный сервер.',
    'Choose ZIP and upload': 'Выбрать и загрузить ZIP',
    'The server downloads the ZIP from this address. Add a checksum if the publisher provides one.':
        'Сервер скачает ZIP по этому адресу. Укажите контрольную сумму, если автор пакета её предоставил.',
    'Download package': 'Скачать пакет',
    'Project activation': 'Активация в проекте',
    'Active in this project. Manifest changes are applied only when you reload the plugin.':
        'Активен в этом проекте. Изменения манифеста применяются при перезагрузке плагина.',
    'Package available on the server. Review its manifest and documentation before activating it here.':
        'Пакет доступен на сервере. Перед активацией проверьте манифест и документацию.',
    'Review activation': 'Проверить активацию',
    'Review and develop': 'Проверка и разработка',
    'Inspect the project data, dependencies and commands declared by this package.':
        'Проверьте данные проекта, зависимости и команды, объявленные в пакете.',
    'Read setup instructions supplied by the package author.':
        'Прочитайте инструкции по настройке от автора пакета.',
    'Browse and edit source files, upload assets or download a local copy.':
        'Просматривайте и редактируйте исходники, загружайте файлы или скачайте локальную копию.',
    'Share a package': 'Передача пакета',
    'Export a ZIP to share the current package. Publish version creates a separate release; it does not activate it.':
        'Экспортируйте ZIP, чтобы передать пакет. Публикация версии создаёт отдельный выпуск без автоматической активации.',
    'Package details': 'Сведения о пакете',
    'Activate this package in the selected project? Its manifest can create or update project data and run server code.':
        'Активировать пакет в выбранном проекте? Манифест может создавать и менять данные проекта и выполнять серверный код.',
    'Package added. Review its contents, then activate it in this project.':
        'Пакет добавлен. Проверьте содержимое, затем активируйте его в проекте.',
    'Plugin created and active in this project. Add files and configure its manifest.':
        'Плагин создан и активен в проекте. Добавьте файлы и настройте манифест.',
    'Plugin is now active in this project.':
        'Плагин активирован в этом проекте.',
    'Plugin removed from this project. The package remains on the server.':
        'Плагин удалён из проекта. Пакет остаётся на сервере.',
    'Changes saved. Reload the plugin to apply manifest changes to this project.':
        'Изменения сохранены. Перезагрузите плагин, чтобы применить изменения манифеста к проекту.',
    'Changes saved.': 'Изменения сохранены.',
    'Package exported. Check your downloads.':
        'Пакет экспортирован. Проверьте загрузки.',
    'Version published. Review the new release before activating it.':
        'Версия опубликована. Проверьте новый выпуск перед активацией.',
    'Define the package': 'Опишите пакет',
    'Choose a unique code such as studio_tools. Creation makes a DEV package and registers it in the current project.':
        'Выберите уникальный код, например studio_tools. Создание добавит пакет DEV и зарегистрирует его в текущем проекте.',
    'Use letters, digits, underscores or hyphens. The code cannot be changed after creation.':
        'Используйте буквы, цифры, подчёркивания и дефисы. После создания код менять нельзя.',
    'Empty package: add your own manifest entries and files.':
        'Пустой пакет: добавьте свои записи манифеста и файлы.',
    'Widget template: starts with a modern reusable item layout.':
        'Шаблон виджета: основа — современный переиспользуемый макет элемента.',
    'Column template: configure a table column through the existing widget system.':
        'Шаблон колонки: настройте колонку таблицы через существующую систему виджетов.',
    'Theme template: package a theme using the native theme configuration.':
        'Шаблон темы: создайте пакет с настройками темы.',
    'Project template exports the selected project. No new plugin is activated.':
        'Шаблон проекта экспортирует выбранный проект. Новый плагин не активируется.',
    'Save changes the manifest file. Reload plugin applies its project data; review that confirmation first.':
        'Сохранение меняет файл манифеста. Перезагрузка плагина применяет данные к проекту — сначала прочитайте подтверждение.',
    'Select a file to edit. Save commits the source; generated .spt files can be cleaned from More actions.':
        'Выберите файл для редактирования. Сохранение записывает исходник; сгенерированные .spt можно удалить через «Другие действия».',
    'Read or edit the author’s documentation as source. Legacy HTML is not executed here.':
        'Читайте и редактируйте документацию автора как исходный текст. Легаси HTML здесь не выполняется.',
    'No matching plugins. Change the search or the project filter.':
        'Плагины не найдены. Измените поиск или фильтр проекта.',
    'Back to overview': 'Назад к обзору',
    Back: 'Назад',
    'Server package': 'Пакет на сервере',
    'No plugins yet': 'Плагинов пока нет',
    Package: 'Пакет',
    Project: 'Проект',
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
    if (language === 'ru' && Resources.russian[text])
        return Resources.russian[text];
    return language === 'ru' && russian[text]
        ? russian[text]
        : commonTranslate(text, language);
}

export const toolbarGap = 8;
const parent = (path) => path.split('/').slice(0, -1).join('/');

export function actions(model, language) {
    const meta = model.metadata || {},
        ready = !model.busy && !model.dirty && !model.uncertain;
    return [
        ['reload', 'Reload plugin', 'refresh', meta.active],
        ['deactivate', 'Remove from project', 'remove', meta.active],
        ['clean', 'Clean project data', 'delete', !meta.active],
        ['clear_spt', 'Clear .spt files', 'delete', !meta.builtin],
        ['delete', 'Delete package', 'delete', !meta.builtin]
    ]
        .filter((row) => row[3])
        .map(([command, title, icon]) => ({
            command,
            title: translate(title, language),
            icon,
            enabled:
                ready &&
                (command !== 'delete' || !meta.active) &&
                (!['reload', 'deactivate', 'clean'].includes(command) ||
                    !['admin', 'sthpw'].includes(meta.project)),
            translate: false
        }));
}

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        compact = width < 420;
    const commands = [
        [
            'pluginReload',
            'Refresh',
            'refresh',
            { type: 'reload' },
            !model.busy,
            40
        ]
    ];
    if (model.dirty || model.uncertain) {
        commands.push([
            'pluginDiscard',
            'Discard',
            'undo',
            { type: 'discard' },
            !model.busy,
            compact ? 40 : 120
        ]);
        if (!model.metadata?.new)
            commands.push([
                'pluginSave',
                'Save',
                'save',
                { type: 'save' },
                model.canWrite && !model.busy && !model.uncertain,
                compact ? 100 : 140
            ]);
    }
    commands.push([
        'pluginHelp',
        'Plugin guide',
        'help',
        { type: 'help' },
        true,
        40
    ]);
    let x = Math.max(
        0,
        width - commands.reduce((sum, row) => sum + row[5] + 4, 0)
    );
    for (const [id, title, icon, event, enabled, w] of commands) {
        nodes.push(
            button(id, rect(x, 0, w, 40), tr(title), icon, event, enabled, {
                iconOnly: w === 40
            })
        );
        x += w + 4;
    }
    return { nodes };
}

const metaNew = (model) => !!model.metadata?.new;
export function describe(model, ui, width, height, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        gap = 12,
        compact = width < 760,
        hasCatalogue = !!(model.catalog || []).length,
        nav =
            !hasCatalogue || metaNew(model)
                ? 0
                : ui.collapsed
                  ? 44
                  : compact
                    ? 200
                    : 250,
        right = nav ? nav + gap : 0,
        bodyWidth = Math.max(0, width - right),
        editable = !model.busy && !model.uncertain && model.canWrite,
        clean = !model.busy && !model.dirty && !model.uncertain,
        doc = model.document || {},
        meta = model.metadata || {},
        exists = !!model.identity;
    const btn = (id, r, text, icon, action, enabled = clean, extra = {}) =>
        button(id, r, tr(text), icon, action, enabled, extra);
    if (nav) {
        if (!ui.collapsed)
            nodes.push(
                label(
                    'pluginCatalogueCaption',
                    rect(0, 0, nav - 36, 28),
                    tr('Plugin catalogue'),
                    { weight: 600 }
                )
            );
        nodes.push(
            btn(
                'pluginCollapse',
                rect(ui.collapsed ? 0 : nav - 28, 0, 28, 28),
                'Plugin catalogue',
                ui.collapsed ? 'next' : 'previous',
                { type: 'collapse' },
                true,
                { iconOnly: true }
            )
        );
    }
    if (nav && !ui.collapsed) {
        nodes.push(
            btn('pluginNew', rect(0, 36, nav, 36), 'New', 'add', {
                type: 'new'
            })
        );
        nodes.push(
            btn(
                'pluginInstall',
                rect(0, 80, nav, 36),
                'Install a package',
                'upload',
                { type: 'install' },
                clean,
                { iconOnly: false }
            )
        );
        nodes.push(
            node('Field', 'pluginSearch', rect(0, 128, nav, 36), {
                text: ui.query,
                placeholder: tr('Search plugins'),
                action: { type: 'query' },
                clearable: true
            })
        );
        nodes.push(
            node('CheckBox', 'pluginActiveOnly', rect(0, 172, nav, 36), {
                text: tr('Active in this project'),
                checked: ui.activeOnly,
                action: { type: 'activeOnly' }
            })
        );
        nodes.push(
            node(
                'List',
                'pluginCatalogue',
                rect(0, 216, nav, Math.max(0, height - 216)),
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
    if (nav > 44 && !catalog(model, ui).length)
        nodes.push(
            label(
                'pluginNoMatches',
                rect(8, 224, nav - 24, 80),
                tr(
                    'No matching plugins. Change the search or the project filter.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
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
            w = Math.max(0, Math.min(1040, bodyWidth - 48));
        let oy = 0;
        const heading = {
            install: 'Install a package',
            activate: 'Review activation',
            deactivate: 'Remove from project',
            reload: 'Reload plugin',
            clean: 'Clean project data',
            delete: 'Delete package',
            clear_spt: 'Clear .spt files',
            replace_file: 'Replace file',
            delete_file: 'Delete',
            reload_catalog: 'Refresh',
            new_file: 'New file',
            new_folder: 'New folder',
            rename: 'Rename or move',
            publish: 'Publish version',
            run_resource: 'Run Python action'
        }[ui.operation];
        content.push(
            label('pluginOperationTitle', rect(0, oy, w, 36), tr(heading), {
                weight: 600,
                fontRole: 'title'
            })
        );
        oy += 48;
        if (ui.operation === 'activate') {
            const progress = Guide.steps(w, 2, tr);
            progress.nodes.forEach((item) => {
                item.y += oy;
                content.push(item);
            });
            oy += progress.height + 8;
        }
        if (destructive[ui.operation]) {
            content.push(
                label(
                    'pluginOperationExplanation',
                    rect(0, oy, w, 96),
                    tr(destructive[ui.operation]),
                    { wrap: true }
                )
            );
            oy += 108;
        }
        if (ui.operation === 'install') {
            const guide = Guide.installation(ui, w, clean, tr);
            guide.nodes.forEach((item) => {
                item.y += oy;
                content.push(item);
            });
            oy += guide.height;
        } else {
            content.push(
                label(
                    'pluginOperationContext',
                    rect(0, oy, w, 50),
                    tr('Package') +
                        ': ' +
                        (doc.title || doc.code || '') +
                        '\n' +
                        tr('Project') +
                        ': ' +
                        (meta.project || ''),
                    { wrap: true, color: 'secondaryText' }
                )
            );
            oy += 62;
            if (!destructive[ui.operation]) {
                content.push(
                    node('Field', 'pluginOperationValue', rect(0, oy, w, 40), {
                        text: ui.value,
                        placeholder: tr(
                            ui.operation === 'publish'
                                ? 'Version'
                                : 'Relative path'
                        ),
                        action: { type: 'input', field: 'value' },
                        enabled: clean
                    })
                );
                oy += 52;
            }
        }
        if (ui.operation !== 'install')
            content.push(
                btn(
                    'pluginConfirm',
                    rect(0, oy, Math.min(180, w / 2 - 4), 40),
                    ui.operation === 'activate' ? 'Activate' : 'Confirm',
                    'check',
                    { type: 'confirm' },
                    (clean &&
                        (![
                            'publish',
                            'new_file',
                            'new_folder',
                            'rename'
                        ].includes(ui.operation) ||
                            !!ui.value.trim())) ||
                        (ui.operation === 'reload_catalog' && !model.busy)
                )
            );
        content.push(
            btn(
                'pluginCancel',
                rect(
                    ui.operation === 'install' ? 0 : Math.min(188, w / 2 + 4),
                    oy,
                    Math.min(150, w / 2 - 4),
                    40
                ),
                ui.operation === 'install' ? 'Back' : 'Cancel',
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
                    contentHeight: oy + 84,
                    scrollbarId: 'pluginOperationScrollBar',
                    scrollbarReserved: 16,
                    children: [
                        node(
                            'Box',
                            'pluginOperationPanel',
                            rect(0, 0, w + 32, oy + 84),
                            {
                                background: 'surfaceContainer',
                                border: 'outlineVariant',
                                radius: 8,
                                children: content.map((item) =>
                                    Object.assign({}, item, {
                                        x: item.x + 16,
                                        y: item.y + 16
                                    })
                                )
                            }
                        )
                    ]
                }
            )
        );
        return { nodes };
    }
    if (ui.notice) {
        nodes.push(
            label(
                'pluginResult',
                rect(right, y, bodyWidth, 60),
                tr(ui.notice),
                { wrap: true, weight: 600, role: 'status' }
            )
        );
        y += 72;
    }
    if (!exists && !meta.new) {
        const guide = Guide.start(Math.max(0, bodyWidth - 16), clean, tr);
        nodes.push(
            node(
                'Scroll',
                'pluginWelcome',
                rect(right, y, bodyWidth, Math.max(0, height - y)),
                {
                    children: guide.nodes,
                    contentHeight: guide.height,
                    scrollbarId: 'pluginWelcomeScrollBar',
                    scrollbarReserved: 16
                }
            )
        );
        return { nodes };
    }
    nodes.push(
        label(
            'pluginTitle',
            rect(right, y, Math.max(0, bodyWidth - (exists ? 190 : 0)), 28),
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
        nodes.push(
            node(
                'View',
                'pluginToolsMenu',
                rect(right + bodyWidth - 180, y - 66, 180, 36),
                {
                    view: 'pluginTools',
                    actions: actions(model, language),
                    label: tr('More actions')
                }
            )
        );
        const tabs = [
                ['info', 'Overview'],
                ['resources', 'Resources'],
                ['details', 'Package details'],
                ['manifest', 'Manifest XML'],
                ['files', 'Files'],
                ['docs', 'Documentation']
            ],
            tw = bodyWidth / tabs.length;
        nodes.push(
            node(
                bodyWidth < 740 ? 'Choice' : 'Segmented',
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
        w = Math.max(
            0,
            Math.min(
                meta.new || ui.tab === 'info' || ui.tab === 'details'
                    ? 1040
                    : Infinity,
                bodyWidth - 16
            )
        );
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
                    label: tr(title),
                    text: doc[name] || '',
                    readOnly: readonly || !editable,
                    enabled: !model.busy,
                    action: { type: 'field', field: name }
                }
            )
        );
        cy += area ? 122 : 52;
    }
    if (!meta.new && ui.tab === 'info') {
        const guide = Guide.project(model, w, tr);
        guide.nodes.forEach((item) => content.push(item));
        cy = guide.height;
        content.push(
            label(
                'pluginPackageIdentity',
                rect(0, cy, w, 28),
                [doc.code, doc.version || 'DEV'].join(' · '),
                { weight: 600 }
            )
        );
        cy += 36;
        if (doc.description) {
            content.push(
                label(
                    'pluginPackageDescription',
                    rect(0, cy, w, 80),
                    doc.description,
                    { wrap: true, color: 'secondaryText' }
                )
            );
            cy += 92;
        }
        content.push(
            btn(
                'pluginEditDetails',
                rect(0, cy, Math.min(300, w), 36),
                'Package details',
                'edit',
                { type: 'tab', value: 'details' }
            )
        );
        cy += 48;
    } else if (meta.new || ui.tab === 'details') {
        if (meta.new) {
            content.push(
                label(
                    'pluginCreateIntro',
                    rect(0, cy, w, 68),
                    tr(
                        'Choose a unique code such as studio_tools. Creation makes a DEV package and registers it in the current project.'
                    ),
                    { wrap: true, color: 'secondaryText' }
                )
            );
            cy += 80;
        }
        if (!meta.new || doc.type !== 'project') {
            field('title', 'Title');
            field('code', 'Code', false, !meta.new);
            if (meta.new) {
                content.push(
                    label(
                        'pluginCodeHint',
                        rect(0, cy, w, 50),
                        tr(
                            'Use letters, digits, underscores or hyphens. The code cannot be changed after creation.'
                        ),
                        { wrap: true, color: 'secondaryText' }
                    )
                );
                cy += 62;
            }
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
        if (meta.new) {
            const hint = {
                '': 'Empty package: add your own manifest entries and files.',
                widget: 'Widget template: starts with a modern reusable item layout.',
                column: 'Column template: configure a table column through the existing widget system.',
                theme: 'Theme template: package a theme using the native theme configuration.',
                project:
                    'Project template exports the selected project. No new plugin is activated.'
            }[doc.type || ''];
            content.push(
                label('pluginCreateHint', rect(0, cy, w, 56), tr(hint), {
                    wrap: true,
                    color: 'secondaryText'
                })
            );
            cy += 68;
        }
    } else if (ui.tab === 'resources') {
        const resources = Resources.describe(
            model,
            ui,
            w,
            Math.max(360, height - y),
            language,
            tr
        );
        resources.nodes.forEach((item) => content.push(item));
        cy = resources.height;
    } else if (ui.tab === 'manifest') {
        content.push(
            label(
                'pluginManifestHint',
                rect(0, 0, w, 56),
                tr(
                    'Save changes the manifest file. Reload plugin applies its project data; review that confirmation first.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
        content.push(
            node(
                'Code',
                'pluginManifest',
                rect(0, 68, w, Math.max(260, height - y - 80)),
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
        cy = 68 + Math.max(260, height - y - 80);
    } else {
        const files = ui.tab === 'files';
        content.push(
            label(
                'pluginSourceHint',
                rect(0, cy, w, 56),
                tr(
                    files
                        ? 'Select a file to edit. Save commits the source; generated .spt files can be cleaned from More actions.'
                        : 'Read or edit the author’s documentation as source. Legacy HTML is not executed here.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
        cy += 68;
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
                ['upload', 'Upload file', 'upload']
            ];
            let x = 0;
            for (const [action, title, icon, event] of tools) {
                const labelled = ['new_file', 'new_folder', 'upload'].includes(
                        action
                    ),
                    toolWidth = labelled
                        ? Math.min(w, Math.max(140, tr(title).length * 7 + 48))
                        : 40;
                if (x && x + toolWidth > w) {
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
                        rect(x, cy, toolWidth, 40),
                        title,
                        icon,
                        event || {
                            type: action === 'upload' ? 'upload' : 'operation',
                            action
                        },
                        enabled,
                        { iconOnly: !labelled }
                    )
                );
                x += toolWidth + 4;
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
    if (meta.new) {
        const bw = Math.min(260, (bodyWidth - 32) / 2);
        nodes.push(
            node(
                'Box',
                'pluginCreateFooter',
                rect(right, height - 52, bodyWidth, 52),
                {
                    background: 'surfaceContainer',
                    border: 'outlineVariant',
                    radius: 0,
                    children: [
                        btn(
                            'pluginCreate',
                            rect(8, 6, bw, 40),
                            doc.type === 'project'
                                ? 'Export template'
                                : 'Create plugin',
                            'add',
                            { type: 'save' },
                            editable && canCreate(model),
                            { highlighted: true }
                        ),
                        btn(
                            'pluginCancelCreate',
                            rect(bw + 16, 6, bw, 40),
                            'Cancel',
                            'close',
                            { type: 'cancel' },
                            !model.busy
                        )
                    ]
                }
            )
        );
    }
    nodes.push(
        node(
            'Scroll',
            'pluginEditorScroll',
            rect(
                right,
                y,
                bodyWidth,
                Math.max(0, height - y - (meta.new ? 60 : 0))
            ),
            {
                resetKey: model.identity + ':' + !!meta.new + ':' + ui.tab,
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
        w = Math.max(0, list.width - 16),
        h = listRowHeight(list);
    if (list.id === 'pluginResources')
        return Resources.row(list, record, model, tr);
    if (list.id === 'pluginFiles')
        return {
            nodes: [
                button(
                    'pluginFile_' + record.path,
                    rect(0, 0, w, h),
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
            node('Box', 'pluginRowBackground', rect(0, 0, w, h), {
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
            label(
                'pluginRowPath',
                rect(36, 52, w - 44, Math.min(22, h - 52)),
                record.path,
                {
                    color: 'secondaryText',
                    fontRole: 'secondary'
                }
            ),
            node('Action', 'pluginSelect', rect(0, 0, w, h), {
                text: record.title || record.code,
                action: { type: 'select', identity: record.identity },
                enabled: !model.busy
            })
        ]
    };
}
