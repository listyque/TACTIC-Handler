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
    'License type': 'Тип лицензии',
    'Hourly wage': 'Почасовая ставка',
    Password: 'Пароль',
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
const profileFields = [
    ['first_name', 'First name'],
    ['last_name', 'Last name'],
    ['display_name', 'Display name'],
    ['department', 'Department'],
    ['email', 'Email'],
    ['phone_number', 'Phone number'],
    ['address', 'Address']
];
const accountFields = [
    ['upn', 'UPN'],
    ['namespace', 'Namespace'],
    ['project_code', 'Project code'],
    ['license_type', 'License type'],
    ['hourly_wage', 'Hourly wage']
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
        remaining = Math.max(1, height - top),
        catalogWidth = stacked ? width : width < 780 ? 220 : 290;
    const catalogHeight = stacked ? Math.min(240, remaining * 0.37) : remaining;
    const docX = stacked ? 0 : catalogWidth + 12,
        docY = stacked ? top + catalogHeight + 12 : top;
    const docWidth = stacked ? width : width - docX,
        docHeight = Math.max(1, height - docY),
        inner = Math.max(1, docWidth - pad * 2);
    const catalog = [
        node('Icon', 'adminUsersIcon', box(pad, 14, 20, 20), {
            icon: 'groups',
            color: 'action'
        }),
        label(
            'adminUsersTitle',
            box(44, 12, catalogWidth - 58, 24),
            tr('User directory'),
            {
                fontRole: 'section',
                weight: 600
            }
        ),
        node(
            'Field',
            'adminUserSearch',
            box(pad, 48, catalogWidth - pad * 2, 38),
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
            box(pad, 92, catalogWidth - pad * 2, 30),
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
            box(pad, 130, catalogWidth - pad * 2, catalogHeight - 130 - pad),
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
    ];
    if (!model.userCount && !model.busy)
        catalog.push(
            label(
                'adminUsersEmpty',
                box(pad, 130, catalogWidth - pad * 2 - 16, 50),
                tr('No users match the search'),
                {
                    wrap: true,
                    color: 'secondaryText'
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
        content.push(
            ...identity(profile, pad, pad, inner - 44, 60, 'userIdentity')
        );
        content.push(
            node(
                'Button',
                'adminUserManageGroups',
                box(docWidth - pad - 38, pad + 11, 38, 38),
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
        const help = (text) => {
            const h = formWidth < 320 ? 56 : 36;
            fields.push(
                label(
                    'adminUserHelp_' + ui.page,
                    box(0, y, formWidth, h),
                    tr(text),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += h + 8;
        };
        const field = (key, text, x, top, w, extra) => {
            fields.push(
                label('adminUserLabel_' + key, box(x, top, w, 22), tr(text), {
                    weight: 600
                })
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
        if (ui.page === 'profile') {
            help(
                'These details are shown in profiles, messages and user pickers.'
            );
            field('login', 'Login', 0, y, formWidth, {
                readOnly: !!model.identity,
                placeholder: tr('Unique login, without spaces')
            });
            y += 77;
        }
        if (ui.page !== 'groups') {
            const availableFields = (
                    ui.page === 'profile' ? profileFields : accountFields
                ).filter(([key]) =>
                    Object.prototype.hasOwnProperty.call(model.draft, key)
                ),
                columns = formWidth > 620 ? 2 : 1,
                cell = (formWidth - (columns - 1) * 12) / columns;
            availableFields.forEach(([key, text], index) =>
                field(
                    key,
                    text,
                    (index % columns) * (cell + 12),
                    y + Math.floor(index / columns) * 77,
                    cell,
                    {
                        inputMode: key === 'hourly_wage' ? 'decimal' : 'text'
                    }
                )
            );
            y += Math.ceil(availableFields.length / columns) * 77;
        }
        if (ui.page === 'account') {
            field('password', 'Password', 0, y, formWidth, {
                password: true,
                placeholder: tr('Leave empty to keep the current password')
            });
            y += 77;
            fields.push(
                node('CheckBox', 'adminUserRetired', box(0, y, formWidth, 32), {
                    text: tr('Retired'),
                    checked: model.draft.s_status === 'retired',
                    enabled: allow.editable,
                    children: [
                        label(
                            'adminUserRetiredLabel',
                            box(27, 0, formWidth - 27, 32),
                            tr('Retired')
                        )
                    ],
                    action: {
                        type: 'retired'
                    }
                })
            );
            y += 40;
            help(
                "Retiring keeps this user's history. Clear this option to reactivate the account, then save."
            );
        }
        if (ui.page === 'groups') {
            help("Group membership changes affect this user's permissions.");
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
                        label(
                            'userGroupTitle_' + record.name,
                            box(39, info ? 3 : 9, width - 49, 22),
                            record.name,
                            {
                                weight: 600
                            }
                        ),
                        label(
                            'userGroupDescription_' + record.name,
                            box(39, info ? 24 : 31, width - 49, 18),
                            record.description || '',
                            muted
                        ),
                        label(
                            'userGroupScope_' + record.name,
                            box(39, 41, width - 49, 16),
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
