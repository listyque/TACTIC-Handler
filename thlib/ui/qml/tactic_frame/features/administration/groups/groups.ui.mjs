import { node } from '../../../core/frame.mjs';
import { permissions } from './groups.state.mjs';

export const metrics = {
    gap: 12,
    toolbarGap: 8,
    padding: 14,
    control: 38,
    groupRow: 64,
    memberRow: 58,
    scrollbar: 12
};

const russian = {
    Groups: 'Группы',
    Group: 'Группа',
    'New group': 'Новая группа',
    'Server error': 'Ошибка сервера',
    Status: 'Состояние',
    'Create group': 'Создать группу',
    'Reload from server': 'Обновить с сервера',
    Discard: 'Сбросить',
    'Save to server': 'Сохранить на сервере',
    Close: 'Закрыть',
    Members: 'Участники',
    'Group details': 'Сведения о группе',
    'Search users': 'Поиск пользователей',
    'Members: {count}': 'Участников: {count}',
    'Group identifier': 'Идентификатор группы',
    'Unique identifier': 'Уникальный идентификатор',
    Description: 'Описание',
    'What is this group responsible for?': 'За что отвечает эта группа?',
    'The identifier is used in access rules and cannot be changed after creation.':
        'Идентификатор используется в правилах доступа и не меняется после создания.',
    'Membership changes apply on the server. Sidebar visibility rules are configured separately for each sidebar item.':
        'Состав группы меняется на сервере. Видимость пунктов навигации настраивается отдельно для каждого пункта.',
    'Check the people who belong to this group':
        'Отметьте пользователей, входящих в группу',
    'No users match the search': 'Нет пользователей, соответствующих поиску',
    'No user groups yet': 'Групп пользователей пока нет',
    'Select a group or create a new one': 'Выберите группу или создайте новую',
    'Discard unsaved group changes?':
        'Сбросить несохранённые изменения группы?',
    'Keep editing': 'Продолжить',
    'Discard changes': 'Сбросить изменения',
    'Working on the server…': 'Выполняется операция на сервере…',
    'Unsaved changes': 'Есть несохранённые изменения',
    'Read-only': 'Только чтение',
    'Group saved on server': 'Группа сохранена на сервере',
    'Enter a group identifier': 'Введите идентификатор группы',
    Retired: 'Архивный',
    'The save result is unknown. Reload groups before trying again.':
        'Результат сохранения неизвестен. Обновите группы перед повторной попыткой.',
    'Group details changed. Reload before saving.':
        'Сведения о группе изменились. Обновите данные перед сохранением.'
};

export function translate(text, language, values) {
    let result =
        language === 'ru' && russian[text] ? russian[text] : String(text || '');
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
const label = (id, rect, text, properties) =>
    node(
        'Label',
        id,
        rect,
        Object.assign(
            {
                text
            },
            properties || {}
        )
    );
const muted = {
    color: 'secondaryText',
    fontRole: 'secondary'
};

export function toolbarWidth(hostWidth) {
    return hostWidth < 1080 ? 420 : 620;
}

export function toolbar(model, ui, width, language, closable) {
    const tr = (text) => translate(text, language);
    const allow = permissions(model),
        compact = width < (closable ? (language === 'ru' ? 650 : 600) : 550);
    const nodes = [];
    const button = (id, text, icon, x, size, action, enabled, highlighted) =>
        node('Button', id, box(x, 0, size, 38), {
            text: tr(text),
            icon,
            iconOnly: compact,
            action: {
                type: action
            },
            enabled,
            highlighted: !!highlighted
        });
    const createWidth = compact ? 38 : 148;
    nodes.push(
        button(
            'createSecurityGroup',
            'Create group',
            'person-add',
            0,
            createWidth,
            'create',
            allow.create
        )
    );
    nodes.push(
        node('Button', 'adminReloadDocument', box(createWidth + 6, 0, 38, 38), {
            text: tr('Reload from server'),
            icon: 'refresh',
            iconOnly: true,
            action: {
                type: 'reload'
            },
            enabled: allow.reload
        })
    );
    const closeWidth = closable ? (compact ? 44 : 102) : 0;
    const saveWidth = compact ? 38 : language === 'ru' ? 200 : 166,
        discardWidth = compact ? 38 : 118;
    const saveX = Math.max(createWidth + 58, width - closeWidth - saveWidth);
    const discardX = saveX - discardWidth - 8;
    nodes.push(
        button(
            'adminDiscardDocument',
            'Discard',
            'undo',
            discardX,
            discardWidth,
            'discard',
            allow.discard
        )
    );
    nodes.push(
        button(
            'saveSecurityGroup',
            'Save to server',
            'save',
            saveX,
            saveWidth,
            'save',
            allow.save,
            true
        )
    );
    if (closable)
        nodes.push(
            button(
                'closeSecurityGroups',
                'Close',
                'close',
                width - closeWidth + 6,
                closeWidth - 6,
                'close',
                !model.busy
            )
        );
    if (!compact && discardX > createWidth + 62) {
        const status = model.busy
            ? 'Working on the server…'
            : model.dirty
              ? 'Unsaved changes'
              : !model.canWrite
                ? 'Read-only'
                : '';
        nodes.push(
            label(
                'securityGroupStatus',
                box(createWidth + 58, 0, discardX - createWidth - 66, 38),
                tr(status),
                muted
            )
        );
    }
    return {
        nodes
    };
}

export function describe(model, ui, width, height, language) {
    const tr = (text, values) => translate(text, language, values);
    const allow = permissions(model),
        nodes = [],
        pad = metrics.padding;
    let top = 0;
    if (model.error || model.message) {
        nodes.push(
            node('Area', 'securityGroupNotice', box(0, top, width, 66), {
                text: tr(model.error || model.message),
                readOnly: true,
                color: model.error ? 'error' : 'secondaryText',
                label: tr(model.error ? 'Server error' : 'Status'),
                notice: true
            })
        );
        top += 74;
    }
    if (ui.confirmation) {
        const compact = width < 520,
            noticeHeight = compact ? 106 : 78;
        const controls = [
            label(
                'groupDiscardQuestion',
                box(12, 5, width - 24, 30),
                tr('Discard unsaved group changes?'),
                {
                    wrap: true
                }
            )
        ];
        controls.push(
            node(
                'Button',
                'keepSecurityGroup',
                box(12, compact ? 59 : 35, compact ? 128 : 164, 36),
                {
                    text: tr('Keep editing'),
                    action: {
                        type: 'keep'
                    }
                }
            )
        );
        controls.push(
            node(
                'Button',
                'confirmDiscardSecurityGroup',
                box(
                    compact ? 146 : 184,
                    compact ? 59 : 35,
                    compact ? width - 158 : 184,
                    36
                ),
                {
                    text: tr('Discard changes'),
                    destructive: true,
                    action: {
                        type: 'confirm'
                    },
                    enabled: !model.busy
                }
            )
        );
        nodes.push(
            node(
                'Box',
                'groupDiscardNotice',
                box(0, top, width, noticeHeight),
                {
                    background: 'surfaceContainerHigh',
                    children: controls
                }
            )
        );
        top += noticeHeight + 8;
    }
    const stacked = width < 600,
        available = Math.max(1, height - top);
    const catalogWidth = stacked ? width : width < 780 ? 190 : 250;
    const catalogHeight = stacked ? Math.min(146, available * 0.3) : available;
    const docX = stacked ? 0 : catalogWidth + 12,
        docY = stacked ? top + catalogHeight + 12 : top;
    const docWidth = stacked ? width : Math.max(1, width - docX),
        docHeight = Math.max(1, height - docY);
    const list = node(
        'List',
        'securityGroupsList',
        box(pad, 50, catalogWidth - pad * 2, catalogHeight - 50 - pad),
        {
            source: 'groups',
            keyField: 'code',
            fields: ['code', 'name', 'description', 'memberCount'],
            rowHeight: metrics.groupRow,
            scrollbarId: 'securityGroupsScrollBar',
            label: tr('Groups')
        }
    );
    const catalog = [
        node('Icon', 'securityGroupCatalogIcon', box(14, 14, 20, 20), {
            icon: 'groups',
            color: 'action'
        }),
        label(
            'securityGroupCatalogTitle',
            box(44, 12, catalogWidth - 58, 24),
            tr('Groups'),
            {
                fontRole: 'section',
                weight: 600
            }
        ),
        list
    ];
    if (!model.groupCount && !model.busy)
        catalog.push(
            label(
                'securityGroupsEmpty',
                box(pad, 54, catalogWidth - pad * 2, 58),
                tr('No user groups yet'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    nodes.push(
        node(
            'Box',
            'securityGroupsPanel',
            box(0, top, catalogWidth, catalogHeight),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children: catalog
            }
        )
    );
    const content = [
        node('Icon', 'securityGroupDocumentIcon', box(14, 14, 20, 20), {
            icon: 'groups',
            color: 'action'
        }),
        label(
            'securityGroupDocumentTitle',
            box(44, 10, docWidth - 58, 24),
            model.draft ? model.draft.name || tr('New group') : tr('Group'),
            {
                fontRole: 'section',
                weight: 600
            }
        )
    ];
    if (!model.draft)
        content.push(
            label(
                'securityGroupEmpty',
                box(pad, 58, docWidth - pad * 2, 70),
                tr('Select a group or create a new one'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    else {
        content.push(
            label(
                'securityGroupMemberCount',
                box(44, 34, docWidth - 58, 18),
                tr('Members: {count}', {
                    count: model.memberCount
                }),
                muted
            )
        );
        const inner = Math.max(1, docWidth - pad * 2),
            tabWidth = inner / 2;
        const keys = {
            ArrowLeft: {
                type: 'page',
                value: 'members'
            },
            ArrowRight: {
                type: 'page',
                value: 'details'
            },
            Home: {
                type: 'page',
                value: 'members'
            },
            End: {
                type: 'page',
                value: 'details'
            }
        };
        content.push(
            node('Box', 'securityGroupEditorTabs', box(pad, 62, inner, 38), {
                role: 'radiogroup',
                background: 'surfaceContainerHigh',
                border: 'outlineVariant',
                radius: 9,
                children: [
                    node(
                        'Button',
                        'segmentedButtonSegment_members',
                        box(3, 3, tabWidth - 3, 32),
                        {
                            text: tr('Members'),
                            icon: 'person',
                            radio: true,
                            selected: ui.page === 'members',
                            keys,
                            action: {
                                type: 'page',
                                value: 'members'
                            },
                            enabled: !model.busy
                        }
                    ),
                    node(
                        'Button',
                        'segmentedButtonSegment_details',
                        box(tabWidth, 3, tabWidth - 3, 32),
                        {
                            text: tr('Group details'),
                            icon: 'edit',
                            radio: true,
                            selected: ui.page === 'details',
                            keys,
                            action: {
                                type: 'page',
                                value: 'details'
                            },
                            enabled: !model.busy
                        }
                    )
                ]
            })
        );
        if (ui.page === 'members') {
            content.push(
                node(
                    'Field',
                    'securityMemberSearch',
                    box(pad, 110, inner, 38),
                    {
                        text: ui.query,
                        label: tr('Search users'),
                        placeholder: tr('Search users'),
                        enabled: allow.search,
                        action: {
                            type: 'query'
                        }
                    }
                )
            );
            const helpHeight = inner < 320 ? 42 : 26;
            content.push(
                label(
                    'securityMembersHelp',
                    box(pad, 154, inner, helpHeight),
                    tr('Check the people who belong to this group'),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            const listY = 154 + helpHeight + 4;
            content.push(
                node(
                    'List',
                    'securityMembersList',
                    box(pad, listY, inner, docHeight - listY - pad),
                    {
                        source: 'members',
                        keyField: 'login',
                        fields: [
                            'login',
                            'displayName',
                            'initials',
                            'avatarUrl',
                            'avatarColor',
                            'retired',
                            'member'
                        ],
                        rowHeight: metrics.memberRow,
                        scrollbarId: 'securityMembersScrollBar',
                        label: tr('Members')
                    }
                )
            );
            if (!model.userCount && !model.busy)
                content.push(
                    label(
                        'securityMembersEmpty',
                        box(pad + 12, listY + 16, inner - 24, 56),
                        tr('No users match the search'),
                        {
                            wrap: true,
                            color: 'secondaryText'
                        }
                    )
                );
        } else {
            const areaHeight = 120,
                helpHeight = inner < 320 ? 64 : 40;
            const fields = [
                label(
                    'securityGroupNameLabel',
                    box(0, 0, inner - 16, 22),
                    tr('Group identifier'),
                    {
                        weight: 600
                    }
                ),
                node('Field', 'securityGroupName', box(0, 28, inner - 16, 38), {
                    text: model.draft.name,
                    label: tr('Group identifier'),
                    placeholder: tr('Unique identifier'),
                    readOnly: !!model.draft.code,
                    enabled: allow.editable,
                    maxLength: 100,
                    action: {
                        type: 'field',
                        field: 'name'
                    }
                }),
                label(
                    'securityGroupNameHelp',
                    box(0, 74, inner - 16, helpHeight),
                    tr(
                        'The identifier is used in access rules and cannot be changed after creation.'
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                ),
                label(
                    'securityGroupDescriptionLabel',
                    box(0, 82 + helpHeight, inner - 16, 22),
                    tr('Description'),
                    {
                        weight: 600
                    }
                ),
                node(
                    'Area',
                    'securityGroupDescription',
                    box(0, 110 + helpHeight, inner - 16, areaHeight),
                    {
                        text: model.draft.description || '',
                        label: tr('Description'),
                        placeholder: tr('What is this group responsible for?'),
                        enabled: allow.editable,
                        maxLength: 65536,
                        action: {
                            type: 'field',
                            field: 'description'
                        }
                    }
                ),
                label(
                    'securityGroupMembershipHelp',
                    box(0, 240 + helpHeight, inner - 16, helpHeight + 12),
                    tr(
                        'Membership changes apply on the server. Sidebar visibility rules are configured separately for each sidebar item.'
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            ];
            content.push(
                node(
                    'Scroll',
                    'securityGroupDetails',
                    box(pad, 112, inner, docHeight - 112 - pad),
                    {
                        contentHeight: 252 + helpHeight * 2,
                        scrollbarId: 'securityDetailsScrollBar',
                        children: fields
                    }
                )
            );
        }
    }
    nodes.push(
        node(
            'Box',
            'securityGroupDocument',
            box(docX, docY, docWidth, docHeight),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children: content
            }
        )
    );
    return {
        nodes
    };
}

export function row(list, record, model, ui, language) {
    const width = Math.max(1, list.width - metrics.scrollbar - 4),
        height = list.rowHeight - 4;
    const allow = permissions(model);
    if (list.source === 'groups') {
        const selected = !!model.draft && model.draft.code === record.code;
        const children = [
            label(
                'groupTitle_' + record.code,
                box(12, 8, width - 60, 20),
                record.name,
                {
                    weight: selected ? 600 : 500
                }
            ),
            label(
                'groupDescription_' + record.code,
                box(12, 30, width - 56, 26),
                record.description || '',
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            ),
            label(
                'groupCount_' + record.code,
                box(width - 40, 14, 32, 24),
                String(record.memberCount),
                {
                    align: 'center',
                    color: 'secondaryText'
                }
            )
        ];
        return {
            nodes: [
                node(
                    'Action',
                    'securityGroup_' + record.code,
                    box(0, 0, width, height),
                    {
                        text: record.name,
                        description: record.description || '',
                        enabled: allow.select,
                        selected,
                        action: {
                            type: 'select',
                            code: record.code
                        },
                        surface: true,
                        rail: true,
                        normalColor: 'transparent',
                        selectedColor: 'selected',
                        children
                    }
                )
            ]
        };
    }
    if (list.source !== 'members')
        throw Error('Unsupported Groups list: ' + list.source);
    const opacity = record.retired ? 0.5 : 1;
    const title = record.displayName || record.login;
    const children = [
        node(
            'Preview',
            'userIdentityAvatar_' + record.login,
            box(38, 7, 40, 40),
            {
                source: record.avatarUrl || '',
                initials: record.initials || title.slice(0, 1).toUpperCase(),
                accent: record.avatarColor || '',
                opacity
            }
        ),
        label(
            'memberTitle_' + record.login,
            box(
                90,
                title === record.login ? (height - 22) / 2 : 7,
                width - 122,
                22
            ),
            title,
            {
                weight: 600,
                opacity
            }
        ),
        label(
            'memberLogin_' + record.login,
            box(90, 29, width - 122, 18),
            title === record.login ? '' : record.login,
            Object.assign(
                {
                    opacity
                },
                muted
            )
        )
    ];
    if (record.retired)
        children.push(
            node(
                'Icon',
                'memberRetired_' + record.login,
                box(width - 27, 18, 18, 18),
                {
                    icon: 'inventory-2',
                    text: translate('Retired', language),
                    color: 'secondaryText'
                }
            )
        );
    return {
        nodes: [
            node(
                'CheckBox',
                'securityMember_' + record.login,
                box(0, 0, width, height),
                {
                    text: record.login,
                    description: title,
                    enabled: allow.editable,
                    checked: !!record.member,
                    action: {
                        type: 'member',
                        login: record.login
                    },
                    surface: true,
                    rail: false,
                    normalColor: 'surfaceContainerLow',
                    selectedColor: 'surfaceContainerHigh',
                    indicatorX: 10,
                    children
                }
            )
        ]
    };
}
