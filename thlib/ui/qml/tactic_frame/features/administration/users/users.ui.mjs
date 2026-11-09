import { node } from '../../../core/frame.mjs';
import {
    metrics,
    toolbarWidth,
    translate as commonTranslate
} from '../groups/groups.ui.mjs';
import { permissions } from './users.state.mjs';
export { metrics, toolbarWidth };

const russian = {
    'User directory': 'Каталог пользователей',
    'Create user': 'Создать пользователя',
    'New user': 'Новый пользователь',
    'Name, login or email': 'Имя, логин или почта',
    'Show retired users': 'Показать архивных пользователей',
    Profile: 'Профиль',
    Account: 'Аккаунт',
    Groups: 'Группы',
    Login: 'Логин',
    'First name': 'Имя',
    'Last name': 'Фамилия',
    'Display name': 'Отображаемое имя',
    Department: 'Отдел',
    Email: 'Почта',
    'Phone number': 'Телефон',
    Address: 'Адрес',
    UPN: 'UPN',
    Namespace: 'Пространство имён',
    'Project code': 'Код проекта',
    'Hourly wage': 'Почасовая ставка',
    Password: 'Пароль',
    'Identity & name': 'Учётная запись и имя',
    'Contact information': 'Контактные данные',
    'Directory, project & billing': 'Каталог, проект и ставка',
    'Password & authentication': 'Пароль и аутентификация',
    'Account status & lifecycle': 'Статус и жизненный цикл аккаунта',
    'Security & status': 'Безопасность и статус',
    'Public display name': 'Публичное имя в интерфейсе',
    'Department or team': 'Отдел или подразделение',
    'City, office or location': 'Город, офис или локация',
    'Default namespace': 'Пространство имён по умолчанию',
    'Default project code': 'Код проекта по умолчанию',
    'Confirm password': 'Подтверждение пароля',
    'Re-enter new password to verify': 'Повторите новый пароль для проверки',
    'Enter initial password': 'Введите начальный пароль',
    'Show password': 'Показать пароль',
    'Hide password': 'Скрыть пароль',
    'Generate password': 'Сгенерировать пароль',
    'Clear password': 'Очистить',
    'Server password kept': 'Текущий пароль сохранён',
    'Initial password': 'Начальный пароль',
    'Short password': 'Короткий пароль',
    'Good password': 'Средний пароль',
    'Strong password': 'Надёжный пароль',
    'Passwords do not match': 'Пароли не совпадают',
    'Passwords match — ready to save': 'Пароли совпадают — готово к сохранению',
    'New password will be applied when you save':
        'Новый пароль будет применён при сохранении',
    'Password hashes never leave the server. Enter or generate a new password to reset it.':
        'Хэши паролей не покидают сервер. Введите или сгенерируйте новый пароль для смены.',
    'Configure password credentials, directory identity (SSO), default project, billing rate and account status.':
        'Настройте пароль для входа, учётную запись каталога (SSO), стартовый проект, ставку и статус аккаунта.',
    'Use login': 'Из логина',
    'Active account': 'Активный аккаунт',
    'Retired account': 'Архивный аккаунт',
    Active: 'Активен',
    'Unique login, without spaces': 'Уникальный логин без пробелов',
    'Leave empty to keep the current password':
        'Оставьте пустым, чтобы сохранить текущий пароль',
    'These details are shown in profiles, messages and user pickers.':
        'Эти сведения отображаются в профилях, сообщениях и выборе пользователей.',
    "Retiring keeps this user's history. Clear this option to reactivate the account, then save.":
        'Архивация сохраняет историю пользователя. Снимите отметку и сохраните, чтобы восстановить аккаунт.',
    "Group membership changes affect this user's permissions.":
        'Состав групп влияет на права этого пользователя.',
    'Select a user or create a new account':
        'Выберите пользователя или создайте новый аккаунт',
    'Edit group membership': 'Изменить состав групп',
    'Retired user': 'Архивный пользователь',
    'Default group': 'Группа по умолчанию',
    'Project: {project}': 'Проект: {project}',
    "These account changes will be saved on the server and affect this user's permissions.":
        'Изменения аккаунта будут сохранены на сервере и повлияют на права пользователя.',
    'Discard unsaved user changes?':
        'Сбросить несохранённые изменения пользователя?',
    'Confirm save': 'Подтвердить сохранение',
    Save: 'Сохранить',
    Cancel: 'Отмена',
    'A login is required': 'Введите логин',
    'User saved on server': 'Пользователь сохранён на сервере',
    'Invalid user document': 'Некорректные данные пользователя',
    'Enter a login without spaces or slashes':
        'Введите логин без пробелов и слешей',
    'An existing login cannot be changed':
        'Логин существующего аккаунта нельзя изменить',
    'Invalid password or user groups': 'Некорректный пароль или список групп',
    'Invalid user profile field': 'Некорректное поле профиля пользователя',
    'Hourly wage must be a non-negative number':
        'Почасовая ставка должна быть неотрицательным числом',
    'Invalid account status': 'Некорректный статус учётной записи',
    'You cannot retire the account you are signed in with':
        'Нельзя отключить учётную запись, под которой вы вошли',
    'The selected user no longer exists. Refresh the list.':
        'Выбранный пользователь больше не существует. Обновите список.',
    'User details or memberships changed. Reload before saving.':
        'Данные пользователя или членство в группах изменились. Перезагрузите их перед сохранением.',
    'A user with this login already exists':
        'Пользователь с таким логином уже существует',
    'The selected user group no longer exists. Refresh the list.':
        'Выбранная группа больше не существует. Обновите список.',
    'You cannot remove your own administrator membership':
        'Нельзя удалить собственное членство в группе администраторов',
    'Save or discard user changes before leaving.':
        'Сохраните или сбросьте изменения пользователя перед выходом.',
    'The save result is unknown. Reload users before trying again.':
        'Результат сохранения неизвестен. Обновите пользователей перед повторной попыткой.'
};
export function translate(text, language, values) {
    let result =
        language === 'ru' && russian[text]
            ? russian[text]
            : commonTranslate(text, language);
    for (const key of Object.keys(values || {}))
        result = result.split('{' + key + '}').join(values[key]);
    return result;
}
const box = (x, y, width, height) => ({
    x,
    y,
    width: Math.max(0, width),
    height: Math.max(0, height)
});
const label = (id, rect, text, extra) =>
    node(
        'Label',
        id,
        rect,
        Object.assign(
            {
                text
            },
            extra || {}
        )
    );
const muted = {
    fontRole: 'secondary',
    color: 'secondaryText'
};
const profileIdentityFields = [
    ['first_name', 'First name', 'person', 'First name'],
    ['last_name', 'Last name', 'person', 'Last name'],
    ['display_name', 'Display name', 'id-card', 'Public display name'],
    ['department', 'Department', 'building', 'Department or team']
];
const profileContactFields = [
    ['email', 'Email', 'envelope', 'name@studio.com'],
    ['phone_number', 'Phone number', 'phone', '+7 (999) 000-00-00'],
    ['address', 'Address', 'map-marker', 'City, office or location']
];
const accountFields = [
    ['upn', 'UPN', 'account-circle', 'user@domain.local'],
    ['namespace', 'Namespace', 'layers', 'Default namespace'],
    ['project_code', 'Project code', 'folder-open', 'Default project code'],
    ['hourly_wage', 'Hourly wage', 'payments', '0.00']
];

export function profile(draft, record) {
    const data = draft || {},
        name =
            String(data.display_name || '').trim() ||
            [data.first_name, data.last_name]
                .filter(Boolean)
                .join(' ')
                .trim() ||
            data.login ||
            '';
    return Object.assign({}, record || {}, {
        login: data.login || '',
        displayName: name,
        initials:
            name
                .split(/\s+/)
                .filter(Boolean)
                .slice(0, 2)
                .map((word) => word[0])
                .join('')
                .toUpperCase() || '?',
        retired: data.s_status === 'retired',
        avatarColor: (record && record.avatarColor) || ''
    });
}

export function toolbar(model, ui, width, language) {
    const tr = (text) => translate(text, language),
        allow = permissions(model),
        compact = width < (language === 'ru' ? 620 : 550);
    const createWidth = compact ? 38 : language === 'ru' ? 220 : 156,
        saveWidth = compact ? 38 : language === 'ru' ? 200 : 166,
        discardWidth = compact ? 38 : 118;
    const saveX = width - saveWidth,
        discardX = saveX - discardWidth - 8;
    const button = (id, text, icon, x, size, action, enabled, highlighted) =>
        node('Button', id, box(x, 0, size, 38), {
            text: tr(text),
            icon,
            iconOnly: compact,
            enabled,
            highlighted: !!highlighted,
            action: {
                type: action
            }
        });
    const nodes = [
        button(
            'adminCreateDocument',
            'Create user',
            'person-add',
            0,
            createWidth,
            'create',
            allow.create
        ),
        node('Button', 'adminReloadDocument', box(createWidth + 6, 0, 38, 38), {
            text: tr('Reload from server'),
            icon: 'refresh',
            iconOnly: true,
            round: true,
            enabled: allow.reload,
            action: {
                type: 'reload'
            }
        }),
        button(
            'adminDiscardDocument',
            'Discard',
            'undo',
            discardX,
            discardWidth,
            'discard',
            allow.discard
        ),
        button(
            'adminSaveDocument',
            'Save to server',
            'save',
            saveX,
            saveWidth,
            'save',
            allow.save,
            true
        )
    ];
    if (!compact && discardX > createWidth + 62)
        nodes.push(
            label(
                'adminUserStatus',
                box(createWidth + 58, 0, discardX - createWidth - 66, 38),
                tr(
                    model.busy
                        ? 'Working on the server…'
                        : model.dirty
                          ? 'Unsaved changes'
                          : !model.canWrite
                            ? 'Read-only'
                            : ''
                ),
                muted
            )
        );
    return {
        nodes
    };
}

function identity(record, x, y, width, size, prefix) {
    const title = record.displayName || record.login || '',
        secondary = record.login && record.login !== title;
    return [
        node(
            'Preview',
            prefix + 'Avatar_' + record.login,
            box(x, y, size, size),
            {
                source: record.avatarUrl || '',
                initials: record.initials || '?',
                accent: record.avatarColor || '',
                opacity: record.retired ? 0.5 : 1
            }
        ),
        label(
            prefix + 'Title_' + record.login,
            box(
                x + size + 12,
                y + (secondary ? size / 2 - 21 : (size - 22) / 2),
                width - size - 12,
                22
            ),
            title,
            {
                weight: 600,
                fontRole: size > 40 ? 'section' : 'body',
                opacity: record.retired ? 0.5 : 1
            }
        ),
        label(
            prefix + 'Login_' + record.login,
            box(x + size + 12, y + size / 2 + 2, width - size - 12, 18),
            secondary ? record.login : '',
            Object.assign(
                {
                    opacity: record.retired ? 0.5 : 1
                },
                muted
            )
        )
    ];
}

export function describe(model, ui, width, height, language) {
    const tr = (text, values) => translate(text, language, values),
        allow = permissions(model),
        pad = metrics.padding,
        nodes = [];
    let top = 0;
    if (model.error || model.message) {
        const unknown =
            'The save result is unknown. Reload users before trying again.';
        const notice = model.uncertain
            ? tr(unknown) +
              (model.error && model.error !== unknown
                  ? '\n' + tr(model.error)
                  : '')
            : tr(model.error || model.message);
        nodes.push(
            node('Area', 'adminDocumentError', box(0, top, width, 58), {
                text: notice,
                role: model.error ? 'alert' : 'status',
                label: tr(model.error ? 'Server error' : 'Status'),
                color: model.error ? 'error' : 'secondaryText',
                readOnly: true,
                notice: true
            })
        );
        top += 66;
    }
    if (ui.confirmation) {
        const saving = ui.confirmation === 'save',
            narrow = width < 520,
            h = narrow ? 136 : 90;
        nodes.push(
            node('Box', 'adminUserConfirmation', box(0, top, width, h), {
                background: 'surfaceContainerHigh',
                children: [
                    label(
                        'adminUserConfirmationText',
                        box(12, 6, width - 24, narrow ? 72 : 42),
                        tr(
                            saving
                                ? "These account changes will be saved on the server and affect this user's permissions."
                                : 'Discard unsaved user changes?'
                        ),
                        {
                            wrap: true
                        }
                    ),
                    node(
                        'Button',
                        'adminCancelSave',
                        box(12, h - 44, narrow ? 128 : 164, 36),
                        {
                            text: tr(saving ? 'Cancel' : 'Keep editing'),
                            enabled: !model.busy,
                            action: {
                                type: 'keep'
                            }
                        }
                    ),
                    node(
                        'Button',
                        'adminConfirmSave',
                        box(
                            narrow ? 150 : 188,
                            h - 44,
                            narrow ? width - 162 : 220,
                            36
                        ),
                        {
                            text: tr(
                                saving
                                    ? narrow
                                        ? 'Save'
                                        : 'Confirm save'
                                    : 'Discard changes'
                            ),
                            highlighted: saving,
                            destructive: !saving,
                            enabled: !model.busy,
                            action: {
                                type: 'confirm'
                            }
                        }
                    )
                ]
            })
        );
        top += h + 8;
    }
    const stacked = width < 600,
        catalogVisible = stacked || ui.catalogVisible !== false,
        remaining = Math.max(1, height - top),
        catalogWidth = stacked
            ? width
            : catalogVisible
              ? width < 780
                  ? 220
                  : 290
              : 56;
    const catalogHeight = stacked ? Math.min(240, remaining * 0.37) : remaining;
    const docX = stacked ? 0 : catalogWidth + 12,
        docY = stacked ? top + catalogHeight + 12 : top;
    const docWidth = stacked ? width : width - docX,
        docHeight = Math.max(1, height - docY),
        inner = Math.max(1, docWidth - pad * 2);
    const catalog = [];
    if (catalogVisible) {
        catalog.push(
            label(
                'adminUsersTitle',
                box(
                    12,
                    10,
                    Math.max(0, catalogWidth - (stacked ? 24 : 62)),
                    34
                ),
                tr('User directory'),
                {
                    weight: 600
                }
            ),
            node(
                'Field',
                'adminUserSearch',
                box(pad, 52, catalogWidth - pad * 2, 38),
                {
                    text: ui.query,
                    label: tr('Name, login or email'),
                    placeholder: tr('Name, login or email'),
                    enabled: allow.search,
                    action: {
                        type: 'query'
                    }
                }
            ),
            node(
                'CheckBox',
                'adminShowRetiredUsers',
                box(pad, 96, catalogWidth - pad * 2, 30),
                {
                    text: tr('Show retired users'),
                    checked: ui.showRetired,
                    enabled: allow.search,
                    indicatorX: 0,
                    children: [
                        label(
                            'adminShowRetiredLabel',
                            box(27, 0, catalogWidth - pad * 2 - 27, 30),
                            tr('Show retired users')
                        )
                    ],
                    action: {
                        type: 'showRetired'
                    }
                }
            ),
            node(
                'List',
                'adminUsersList',
                box(
                    pad,
                    134,
                    catalogWidth - pad * 2,
                    catalogHeight - 134 - pad
                ),
                {
                    source: 'users',
                    keyField: 'login',
                    fields: [
                        'login',
                        'displayName',
                        'initials',
                        'avatarUrl',
                        'avatarColor',
                        'retired'
                    ],
                    rowHeight: 68,
                    scrollbarId: 'adminUsersScrollBar',
                    label: tr('User directory')
                }
            )
        );
        if (!model.userCount && !model.busy)
            catalog.push(
                label(
                    'adminUsersEmpty',
                    box(pad, 134, catalogWidth - pad * 2 - 16, 50),
                    tr('No users match the search'),
                    {
                        wrap: true,
                        color: 'secondaryText'
                    }
                )
            );
    }
    if (!stacked)
        catalog.push(
            node(
                'Button',
                'adminToggleUsersCatalog',
                box(
                    catalogVisible
                        ? catalogWidth - 46
                        : (catalogWidth - 34) / 2,
                    10,
                    34,
                    34
                ),
                {
                    text: tr('User directory'),
                    icon: catalogVisible ? 'chevron-left' : 'chevron-right',
                    iconOnly: true,
                    iconAction: true,
                    round: false,
                    enabled: true,
                    action: {
                        type: 'catalogVisible'
                    }
                }
            )
        );
    nodes.push(
        node(
            'Box',
            'adminUsersPanel',
            box(0, top, catalogWidth, catalogHeight),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children: catalog
            }
        )
    );
    const content = [];
    if (!model.draft)
        content.push(
            label(
                'adminUserEmpty',
                box(pad, 20, inner, 70),
                tr('Select a user or create a new account'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    else {
        const profile = Object.assign({}, model.profile);
        if (!profile.displayName) profile.displayName = tr('New user');
        const fullName = [model.draft.first_name, model.draft.last_name]
            .filter(Boolean)
            .join(' ')
            .trim();
        const headerSubtitle = [
            profile.login ? '@' + profile.login : '',
            fullName && fullName !== profile.displayName ? fullName : '',
            model.draft.department || '',
            model.draft.email || ''
        ]
            .filter(Boolean)
            .join(' · ');
        const headerProfile = Object.assign({}, profile, {
            subtitle: headerSubtitle
        });
        content.push(
            node('Box', 'adminUserHeaderCard', box(pad, pad, inner, 66), {
                background: 'surfaceContainerHigh',
                border: 'outlineVariant',
                radius: 10
            })
        );
        const headerAvatarSize = 48;
        const headerTitle =
            headerProfile.displayName || headerProfile.login || '';
        const headerSecondary =
            headerProfile.subtitle ||
            (headerProfile.login && headerProfile.login !== headerTitle
                ? headerProfile.login
                : '');
        content.push(
            node(
                'Preview',
                'userIdentityAvatar_' + headerProfile.login,
                box(pad + 10, pad + 9, headerAvatarSize, headerAvatarSize),
                {
                    source: headerProfile.avatarUrl || '',
                    initials: headerProfile.initials || '?',
                    accent: headerProfile.avatarColor || '',
                    opacity: headerProfile.retired ? 0.5 : 1
                }
            ),
            label(
                'userIdentityTitle_' + headerProfile.login,
                box(
                    pad + headerAvatarSize + 22,
                    pad + (headerSecondary ? 11 : 22),
                    Math.max(0, inner - headerAvatarSize - 80),
                    24
                ),
                headerTitle,
                {
                    weight: 600,
                    fontRole: 'section',
                    opacity: headerProfile.retired ? 0.5 : 1
                }
            ),
            label(
                'userIdentityLogin_' + headerProfile.login,
                box(
                    pad + headerAvatarSize + 22,
                    pad + 36,
                    Math.max(0, inner - headerAvatarSize - 80),
                    18
                ),
                headerSecondary,
                Object.assign(
                    {
                        opacity: headerProfile.retired ? 0.5 : 1
                    },
                    muted
                )
            )
        );
        if (inner >= 460) {
            const retired = model.draft.s_status === 'retired';
            const badgeText = tr(retired ? 'Retired user' : 'Active');
            const badgeW = retired ? 136 : 96;
            const badgeX = docWidth - pad - 48 - badgeW - 10;
            content.push(
                node(
                    'Box',
                    'adminUserStatusBadge',
                    box(badgeX, pad + 19, badgeW, 28),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 14,
                        children: [
                            node(
                                'Icon',
                                'adminUserStatusBadgeIcon',
                                box(10, 6, 16, 16),
                                {
                                    icon: retired ? 'archive' : 'verified',
                                    color: retired ? 'secondaryText' : 'action'
                                }
                            ),
                            label(
                                'adminUserStatusBadgeText',
                                box(30, 4, badgeW - 38, 20),
                                badgeText,
                                {
                                    fontRole: 'secondary',
                                    weight: 600,
                                    color: retired
                                        ? 'secondaryText'
                                        : 'primaryText'
                                }
                            )
                        ]
                    }
                )
            );
        }
        content.push(
            node(
                'Button',
                'adminUserManageGroups',
                box(docWidth - pad - 48, pad + 14, 38, 38),
                {
                    text: tr('Edit group membership'),
                    icon: 'groups',
                    iconOnly: true,
                    enabled: allow.editable,
                    action: {
                        type: 'page',
                        value: 'groups'
                    }
                }
            )
        );
        const tabs = [
                ['profile', 'Profile', 'person'],
                ['account', 'Account', 'security'],
                ['groups', 'Groups', 'groups']
            ],
            active = tabs.findIndex((tab) => tab[0] === ui.page);
        const keys = {
            ArrowLeft: {
                type: 'page',
                value: tabs[(active + 2) % 3][0]
            },
            ArrowRight: {
                type: 'page',
                value: tabs[(active + 1) % 3][0]
            },
            Home: {
                type: 'page',
                value: 'profile'
            },
            End: {
                type: 'page',
                value: 'groups'
            }
        };
        content.push(
            node('Box', 'adminUserEditorTabs', box(pad, 86, inner, 38), {
                role: 'radiogroup',
                background: 'surfaceContainerHigh',
                border: 'outlineVariant',
                radius: 9,
                children: tabs.map(([value, text, icon], index) =>
                    node(
                        'Button',
                        'segmentedButtonSegment_' + value,
                        box(
                            3 + (index * (inner - 6)) / 3,
                            3,
                            (inner - 6) / 3,
                            32
                        ),
                        {
                            text: tr(text),
                            icon,
                            radio: true,
                            selected: ui.page === value,
                            keys,
                            enabled: !model.busy,
                            action: {
                                type: 'page',
                                value
                            }
                        }
                    )
                )
            })
        );
        const formWidth = Math.max(1, inner - 16),
            fields = [];
        let y = 0;
        const help = (text, iconName) => {
            const h = formWidth < 360 ? 58 : 42;
            fields.push(
                node(
                    'Box',
                    'adminUserHelpCard_' + ui.page,
                    box(0, y, formWidth, h),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 8
                    }
                ),
                node(
                    'Icon',
                    'adminUserHelpIcon_' + ui.page,
                    box(12, y + Math.floor((h - 18) / 2), 18, 18),
                    {
                        icon:
                            iconName ||
                            (ui.page === 'profile'
                                ? 'id-card'
                                : ui.page === 'account'
                                  ? 'security'
                                  : 'groups'),
                        color: 'action'
                    }
                ),
                label(
                    'adminUserHelp_' + ui.page,
                    box(38, y + 4, Math.max(0, formWidth - 50), h - 8),
                    tr(text),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += h + 12;
        };
        const sectionHeader = (id, titleText, iconName, topY) => {
            fields.push(
                node('Icon', id + '_icon', box(14, topY + 13, 18, 18), {
                    icon: iconName,
                    color: 'action'
                }),
                label(
                    id + '_title',
                    box(38, topY + 10, Math.max(0, formWidth - 52), 24),
                    tr(titleText),
                    {
                        fontRole: 'section',
                        weight: 600
                    }
                ),
                node(
                    'Box',
                    id + '_divider',
                    box(14, topY + 40, Math.max(0, formWidth - 28), 1),
                    {
                        background: 'outlineVariant'
                    }
                )
            );
        };
        const field = (key, text, x, top, w, extra, iconName) => {
            if (iconName) {
                fields.push(
                    node(
                        'Icon',
                        'adminUserFieldIcon_' + key,
                        box(x, top + 3, 16, 16),
                        {
                            icon: iconName,
                            color: 'action'
                        }
                    )
                );
            }
            const labelOffset = iconName ? 22 : 0;
            fields.push(
                label(
                    'adminUserLabel_' + key,
                    box(x + labelOffset, top, Math.max(0, w - labelOffset), 22),
                    tr(text),
                    {
                        weight: 600
                    }
                )
            );
            fields.push(
                node(
                    'Field',
                    key === 'login'
                        ? 'adminUserLogin'
                        : key === 'password'
                          ? 'adminUserPassword'
                          : 'adminUserField_' + key,
                    box(x, top + 27, w, 38),
                    Object.assign(
                        {
                            text: String(model.draft[key] || ''),
                            label: tr(text),
                            enabled: allow.editable,
                            maxLength:
                                key === 'login'
                                    ? 256
                                    : key === 'password'
                                      ? 4096
                                      : 65536,
                            action: {
                                type: 'field',
                                field: key
                            }
                        },
                        extra || {}
                    )
                )
            );
        };
        const renderFieldGrid = (list, startY, cardPad) => {
            const innerW = Math.max(1, formWidth - cardPad * 2),
                columns = innerW > 580 ? 2 : 1,
                cell = (innerW - (columns - 1) * 12) / columns;
            list.forEach(([key, text, iconName, placeholder], index) =>
                field(
                    key,
                    text,
                    cardPad + (index % columns) * (cell + 12),
                    startY + Math.floor(index / columns) * 77,
                    cell,
                    {
                        inputMode: key === 'hourly_wage' ? 'decimal' : 'text',
                        placeholder: placeholder ? tr(placeholder) : ''
                    },
                    iconName
                )
            );
            return Math.ceil(list.length / columns) * 77;
        };
        if (ui.page === 'profile') {
            help(
                'These details are shown in profiles, messages and user pickers.',
                'id-card'
            );
            const cardPad = formWidth < 360 ? 10 : 14;
            const identityList = profileIdentityFields.filter(([key]) =>
                Object.prototype.hasOwnProperty.call(model.draft, key)
            );
            const columns = Math.max(1, formWidth - cardPad * 2) > 580 ? 2 : 1;
            const identityRows = Math.ceil(identityList.length / columns);
            const identityCardH = 52 + 77 + identityRows * 77 + 8;
            fields.push(
                node(
                    'Box',
                    'adminUserProfileIdentityCard',
                    box(0, y, formWidth, identityCardH),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 10
                    }
                )
            );
            sectionHeader(
                'adminUserProfileIdentityHeader',
                'Identity & name',
                'id-card',
                y
            );
            let cy = y + 52;
            field(
                'login',
                'Login',
                cardPad,
                cy,
                Math.max(1, formWidth - cardPad * 2),
                {
                    readOnly: !!model.identity,
                    placeholder: tr('Unique login, without spaces')
                },
                'at'
            );
            cy += 77;
            cy += renderFieldGrid(identityList, cy, cardPad);
            y += identityCardH + 12;

            const contactList = profileContactFields.filter(([key]) =>
                Object.prototype.hasOwnProperty.call(model.draft, key)
            );
            if (contactList.length) {
                const contactRows = Math.ceil(contactList.length / columns);
                const contactCardH = 52 + contactRows * 77 + 8;
                fields.push(
                    node(
                        'Box',
                        'adminUserProfileContactCard',
                        box(0, y, formWidth, contactCardH),
                        {
                            background: 'surfaceContainer',
                            border: 'outlineVariant',
                            radius: 10
                        }
                    )
                );
                sectionHeader(
                    'adminUserProfileContactHeader',
                    'Contact information',
                    'envelope',
                    y
                );
                renderFieldGrid(contactList, y + 52, cardPad);
                y += contactCardH + 8;
            }
        }
        if (ui.page === 'account') {
            const cardPad = formWidth < 360 ? 10 : 14,
                innerW = Math.max(1, formWidth - cardPad * 2),
                columns = innerW > 580 ? 2 : 1,
                cell = (innerW - (columns - 1) * 12) / columns;
            const introH = formWidth < 460 ? 58 : 42;
            fields.push(
                node(
                    'Box',
                    'adminUserAccountIntroCard',
                    box(0, y, formWidth, introH),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 8
                    }
                ),
                node(
                    'Icon',
                    'adminUserAccountIntroIcon',
                    box(12, y + Math.floor((introH - 18) / 2), 18, 18),
                    {
                        icon: 'security',
                        color: 'action'
                    }
                ),
                label(
                    'adminUserAccountIntroText',
                    box(38, y + 4, Math.max(0, formWidth - 50), introH - 8),
                    tr(
                        'Configure password credentials, directory identity (SSO), default project, billing rate and account status.'
                    ),
                    Object.assign({ wrap: true }, muted)
                )
            );
            y += introH + 12;

            // 1. Password & authentication card
            const pwdValue = String(model.draft.password || ''),
                confirmValue = String(ui.passwordConfirm || ''),
                pwdRows = columns === 2 ? 1 : 2,
                pwdToolbarStacked = innerW < 540,
                pwdStatusH = pwdToolbarStacked ? 76 : 38,
                pwdCardH = 52 + pwdRows * 77 + pwdStatusH + 14;
            fields.push(
                node(
                    'Box',
                    'adminUserAccountSecurityCard',
                    box(0, y, formWidth, pwdCardH),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 10
                    }
                )
            );
            sectionHeader(
                'adminUserAccountSecurityHeader',
                'Password & authentication',
                'key',
                y
            );
            if (formWidth >= 420) {
                const pwdBadgeText = pwdValue
                    ? tr(
                          pwdValue.length < 8
                              ? 'Short password'
                              : pwdValue.length < 12
                                ? 'Good password'
                                : 'Strong password'
                      ) +
                      ' · ' +
                      pwdValue.length
                    : tr(
                          model.identity
                              ? 'Server password kept'
                              : 'Initial password'
                      );
                const pwdBadgeW = Math.min(
                    Math.max(120, pwdBadgeText.length * 7 + 34),
                    Math.max(120, Math.floor(formWidth * 0.46))
                );
                fields.push(
                    node(
                        'Box',
                        'adminUserPasswordBadge',
                        box(
                            formWidth - cardPad - pwdBadgeW,
                            y + 8,
                            pwdBadgeW,
                            26
                        ),
                        {
                            background: 'surfaceContainerHigh',
                            border: 'outlineVariant',
                            radius: 13,
                            children: [
                                node(
                                    'Icon',
                                    'adminUserPasswordBadgeIcon',
                                    box(10, 5, 15, 15),
                                    {
                                        icon: pwdValue
                                            ? pwdValue.length < 8
                                                ? 'warning'
                                                : 'verified'
                                            : model.identity
                                              ? 'check-circle'
                                              : 'key',
                                        color:
                                            pwdValue && pwdValue.length < 8
                                                ? 'red'
                                                : 'action'
                                    }
                                ),
                                label(
                                    'adminUserPasswordBadgeText',
                                    box(30, 3, Math.max(0, pwdBadgeW - 38), 20),
                                    pwdBadgeText,
                                    {
                                        fontRole: 'secondary',
                                        weight: 600
                                    }
                                )
                            ]
                        }
                    )
                );
            }
            let sy = y + 52;
            const pwdFieldW = Math.max(1, (columns === 2 ? cell : innerW) - 44);
            field(
                'password',
                'Password',
                cardPad,
                sy,
                pwdFieldW,
                {
                    password: !ui.showPassword,
                    placeholder: tr(
                        model.identity
                            ? 'Leave empty to keep the current password'
                            : 'Enter initial password'
                    )
                },
                'key'
            );
            fields.push(
                node(
                    'Button',
                    'adminUserPasswordToggle',
                    box(cardPad + pwdFieldW + 6, sy + 27, 38, 38),
                    {
                        text: tr(
                            ui.showPassword ? 'Hide password' : 'Show password'
                        ),
                        icon: ui.showPassword ? 'visibility-off' : 'visibility',
                        iconOnly: true,
                        round: false,
                        enabled: !model.busy,
                        action: {
                            type: 'togglePasswordVisibility'
                        }
                    }
                )
            );
            const confirmX = columns === 2 ? cardPad + cell + 12 : cardPad,
                confirmY = columns === 2 ? sy : sy + 77,
                confirmW = columns === 2 ? cell : innerW;
            fields.push(
                node(
                    'Icon',
                    'adminUserFieldIcon_password_confirm',
                    box(confirmX, confirmY + 3, 16, 16),
                    {
                        icon: 'lock',
                        color: 'action'
                    }
                ),
                label(
                    'adminUserLabel_password_confirm',
                    box(
                        confirmX + 22,
                        confirmY,
                        Math.max(0, confirmW - 22),
                        22
                    ),
                    tr('Confirm password'),
                    {
                        weight: 600
                    }
                ),
                node(
                    'Field',
                    'adminUserPasswordConfirm',
                    box(confirmX, confirmY + 27, confirmW, 38),
                    {
                        text: confirmValue,
                        label: tr('Confirm password'),
                        enabled: allow.editable,
                        password: !ui.showPassword,
                        maxLength: 4096,
                        placeholder: tr('Re-enter new password to verify'),
                        action: {
                            type: 'passwordConfirm'
                        }
                    }
                )
            );
            sy += pwdRows * 77;
            const genBtnW = Math.min(
                    language === 'ru' ? 196 : 168,
                    Math.max(110, Math.floor((innerW - 8) * 0.62))
                ),
                clearBtnW = Math.min(
                    language === 'ru' ? 112 : 104,
                    Math.max(72, innerW - genBtnW - 8)
                );
            fields.push(
                node(
                    'Button',
                    'adminUserPasswordGenerate',
                    box(cardPad, sy, genBtnW, 34),
                    {
                        text: tr('Generate password'),
                        icon: 'refresh',
                        enabled: allow.editable,
                        action: {
                            type: 'generatePassword'
                        }
                    }
                ),
                node(
                    'Button',
                    'adminUserPasswordClear',
                    box(cardPad + genBtnW + 8, sy, clearBtnW, 34),
                    {
                        text: tr('Clear password'),
                        icon: 'close',
                        enabled: allow.editable && !!(pwdValue || confirmValue),
                        action: {
                            type: 'clearPassword'
                        }
                    }
                )
            );
            const pwdMismatch =
                    Boolean(confirmValue) && confirmValue !== pwdValue,
                pwdMatched = Boolean(confirmValue) && confirmValue === pwdValue,
                hintIcon = pwdMismatch
                    ? 'warning'
                    : pwdMatched
                      ? 'check-circle'
                      : pwdValue
                        ? 'key'
                        : 'lock',
                hintColor = pwdMismatch
                    ? 'red'
                    : pwdMatched || pwdValue
                      ? 'action'
                      : 'secondaryText',
                hintText = tr(
                    pwdMismatch
                        ? 'Passwords do not match'
                        : pwdMatched
                          ? 'Passwords match — ready to save'
                          : pwdValue
                            ? 'New password will be applied when you save'
                            : 'Password hashes never leave the server. Enter or generate a new password to reset it.'
                ),
                hintX = pwdToolbarStacked
                    ? cardPad
                    : cardPad + genBtnW + clearBtnW + 18,
                hintY = pwdToolbarStacked ? sy + 40 : sy + 2,
                hintW = pwdToolbarStacked
                    ? innerW
                    : Math.max(0, innerW - genBtnW - clearBtnW - 18);
            fields.push(
                node(
                    'Icon',
                    'adminUserPasswordHintIcon',
                    box(hintX, hintY + 7, 16, 16),
                    {
                        icon: hintIcon,
                        color: hintColor
                    }
                ),
                label(
                    'adminUserPasswordHintText',
                    box(
                        hintX + 22,
                        hintY,
                        Math.max(0, hintW - 22),
                        pwdToolbarStacked ? 34 : 30
                    ),
                    hintText,
                    Object.assign(
                        {
                            wrap: true
                        },
                        pwdMismatch
                            ? {
                                  fontRole: 'secondary',
                                  color: 'red',
                                  weight: 600
                              }
                            : muted
                    )
                )
            );
            y += pwdCardH + 12;

            // 2. Directory, project & billing card
            const workspaceFields = accountFields.filter(([key]) =>
                Object.prototype.hasOwnProperty.call(model.draft, key)
            );
            if (workspaceFields.length) {
                const wsRows = Math.ceil(workspaceFields.length / columns),
                    accountCardH = 52 + wsRows * 77 + 8;
                fields.push(
                    node(
                        'Box',
                        'adminUserAccountWorkspaceCard',
                        box(0, y, formWidth, accountCardH),
                        {
                            background: 'surfaceContainer',
                            border: 'outlineVariant',
                            radius: 10
                        }
                    )
                );
                sectionHeader(
                    'adminUserAccountWorkspaceHeader',
                    'Directory, project & billing',
                    'tune',
                    y
                );
                renderFieldGrid(workspaceFields, y + 52, cardPad);
                if (
                    Object.prototype.hasOwnProperty.call(model.draft, 'upn') &&
                    String(model.draft.login || '').trim() &&
                    cell >= 210
                ) {
                    const upnBtnW = language === 'ru' ? 96 : 86;
                    fields.push(
                        node(
                            'Button',
                            'adminUserUpnFromLogin',
                            box(cardPad + cell - upnBtnW, y + 50, upnBtnW, 24),
                            {
                                text: tr('Use login'),
                                enabled:
                                    allow.editable &&
                                    String(model.draft.upn || '') !==
                                        String(model.draft.login || '').trim(),
                                action: {
                                    type: 'upnFromLogin'
                                }
                            }
                        )
                    );
                }
                y += accountCardH + 12;
            }

            // 3. Account status & lifecycle card (kept at the bottom of the Account form)
            const retireHelpH = formWidth < 360 ? 58 : 42,
                statusCardH = 52 + 38 + 40 + retireHelpH + 14,
                isRetired = model.draft.s_status === 'retired';
            fields.push(
                node(
                    'Box',
                    'adminUserAccountStatusCard',
                    box(0, y, formWidth, statusCardH),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 10
                    }
                )
            );
            sectionHeader(
                'adminUserAccountStatusHeader',
                'Account status & lifecycle',
                isRetired ? 'archive' : 'verified',
                y
            );
            let sty = y + 52;
            const statusChipW = Math.max(80, (innerW - 8) / 2);
            fields.push(
                node(
                    'Button',
                    'adminUserStatusActive',
                    box(cardPad, sty, statusChipW, 32),
                    {
                        text: tr('Active account'),
                        icon: 'verified',
                        radio: true,
                        selected: !isRetired,
                        enabled: allow.editable,
                        action: {
                            type: 'retired',
                            value: false
                        }
                    }
                ),
                node(
                    'Button',
                    'adminUserStatusRetired',
                    box(cardPad + statusChipW + 8, sty, statusChipW, 32),
                    {
                        text: tr('Retired account'),
                        icon: 'archive',
                        radio: true,
                        selected: isRetired,
                        enabled: allow.editable,
                        action: {
                            type: 'retired',
                            value: true
                        }
                    }
                )
            );
            sty += 38;
            fields.push(
                node(
                    'CheckBox',
                    'adminUserRetired',
                    box(cardPad, sty, innerW, 32),
                    {
                        text: tr('Retired'),
                        checked: isRetired,
                        enabled: allow.editable,
                        children: [
                            node(
                                'Icon',
                                'adminUserRetiredCheckIcon',
                                box(28, 8, 16, 16),
                                {
                                    icon: 'archive',
                                    color: isRetired
                                        ? 'action'
                                        : 'secondaryText'
                                }
                            ),
                            label(
                                'adminUserRetiredLabel',
                                box(50, 0, Math.max(0, innerW - 50), 32),
                                tr('Retired'),
                                {
                                    weight: 600
                                }
                            )
                        ],
                        action: {
                            type: 'retired'
                        }
                    }
                )
            );
            sty += 40;
            fields.push(
                label(
                    'adminUserHelp_' + ui.page,
                    box(cardPad, sty, innerW, retireHelpH),
                    tr(
                        "Retiring keeps this user's history. Clear this option to reactivate the account, then save."
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += statusCardH + 8;
        }
        if (ui.page === 'groups') {
            help(
                "Group membership changes affect this user's permissions.",
                'groups'
            );
            fields.push(
                node(
                    'List',
                    'adminUserGroupsList',
                    box(0, y, inner, Math.max(1, docHeight - 136 - pad - y)),
                    {
                        source: 'groups',
                        keyField: 'name',
                        fields: [
                            'name',
                            'description',
                            'projectCode',
                            'isDefault'
                        ],
                        rowHeight: 64,
                        scrollbarId: 'adminUserGroupsScrollBar',
                        label: tr('Groups')
                    }
                )
            );
            if (!model.groupCount)
                fields.push(
                    label(
                        'adminUserGroupsEmpty',
                        box(0, y, formWidth, 50),
                        tr('No user groups yet'),
                        {
                            wrap: true,
                            color: 'secondaryText'
                        }
                    )
                );
            y = Math.max(1, docHeight - 136 - pad);
        }
        content.push(
            node(
                'Scroll',
                'adminUserForm',
                box(pad, 136, inner, docHeight - 136 - pad),
                {
                    contentHeight: y,
                    scrollbarId: 'adminUserFormScrollBar',
                    children: fields,
                    resetKey: ui.page
                }
            )
        );
    }
    nodes.push(
        node('Box', 'adminUserDetails', box(docX, docY, docWidth, docHeight), {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children: content
        })
    );
    return {
        nodes
    };
}

export function row(list, record, model, ui, language) {
    const tr = (text, values) => translate(text, language, values),
        width = list.width - 16,
        height = list.rowHeight - 4,
        allow = permissions(model);
    if (list.source === 'users') {
        const selected = model.identity === record.login,
            children = identity(
                record,
                10,
                (height - 40) / 2,
                width - 20,
                40,
                'directoryIdentity'
            );
        if (record.retired)
            children.push(
                node(
                    'Icon',
                    'adminUserRetiredIcon_' + record.login,
                    box(width - 24, height - 20, 16, 16),
                    {
                        icon: 'archive',
                        text: tr('Retired user'),
                        color: 'secondaryText'
                    }
                )
            );
        return {
            nodes: [
                node(
                    'Action',
                    'adminUser_' + record.login,
                    box(0, 0, width, height),
                    {
                        text:
                            (record.displayName || record.login) +
                            ' ' +
                            record.login,
                        description: record.retired ? tr('Retired user') : '',
                        enabled: allow.select,
                        selected,
                        rail: selected,
                        normalColor: 'transparent',
                        selectedColor: 'selected',
                        children,
                        action: {
                            type: 'select',
                            login: record.login
                        }
                    }
                )
            ]
        };
    }
    const info = record.projectCode
        ? tr('Project: {project}', {
              project: record.projectCode
          })
        : record.isDefault
          ? tr('Default group')
          : '';
    const checked = (model.draft.groups || []).indexOf(record.name) >= 0;
    return {
        nodes: [
            node(
                'CheckBox',
                'userGroupMembership_' + record.name,
                box(0, 0, width, height),
                {
                    text: record.name,
                    checked,
                    enabled: allow.editable,
                    indicatorX: 10,
                    normalColor: 'transparent',
                    selectedColor: 'transparent',
                    children: [
                        node(
                            'Icon',
                            'userGroupIcon_' + record.name,
                            box(36, info ? 6 : 12, 16, 16),
                            {
                                icon: record.isDefault ? 'security' : 'groups',
                                color: checked ? 'action' : 'secondaryText'
                            }
                        ),
                        label(
                            'userGroupTitle_' + record.name,
                            box(58, info ? 3 : 9, Math.max(0, width - 68), 22),
                            record.name,
                            {
                                weight: 600
                            }
                        ),
                        label(
                            'userGroupDescription_' + record.name,
                            box(
                                58,
                                info ? 24 : 31,
                                Math.max(0, width - 68),
                                18
                            ),
                            record.description || '',
                            muted
                        ),
                        label(
                            'userGroupScope_' + record.name,
                            box(58, 41, Math.max(0, width - 68), 16),
                            info,
                            muted
                        )
                    ],
                    action: {
                        type: 'member',
                        name: record.name
                    }
                }
            )
        ]
    };
}
