import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import * as Confirmation from '../../../controls/feedback/confirmation.ui.mjs';

const icon = (id, bounds, name, extra = {}) =>
    node('Icon', id, bounds, Object.assign({ icon: name }, extra));

export const profileFields = [
    ['first_name', 'First name'],
    ['last_name', 'Last name'],
    ['display_name', 'Display name'],
    ['department', 'Department'],
    ['email', 'Email'],
    ['phone_number', 'Phone number'],
    ['address', 'Address']
];
export const accountFields = [
    ['upn', 'UPN'],
    ['namespace', 'Namespace'],
    ['s_status', 'Account status'],
    ['project_code', 'Project code'],
    ['hourly_wage', 'Hourly wage']
];
const FIELD_ICONS = {
    login: 'at',
    first_name: 'person',
    last_name: 'person',
    display_name: 'id-card',
    department: 'building',
    email: 'envelope',
    phone_number: 'phone',
    address: 'map-marker',
    upn: 'account-circle',
    namespace: 'layers',
    s_status: 'verified',
    project_code: 'folder-open',
    hourly_wage: 'payments',
    password: 'key'
};
export const groupFields = ['code', 'label', 'description', 'accessLevel'];
export const accessLevels = [
    ['', 'Server default (Low)'],
    ['high', 'High'],
    ['medium', 'Medium'],
    ['low', 'Low'],
    ['min', 'Minimum'],
    ['none', 'None']
];

export function groupRow(model, record, width, language) {
    const draft = model.draft || {};
    const text = (key) => translate(key, language),
        compact = width < 500,
        enabled = !model.saving && !model.uncertain && model.canManage;
    const nodes = [
        node(
            'CheckBox',
            'profileGroup_' + record.code,
            rect(8, 6, compact ? width - 16 : width - 178, 32),
            {
                text: record.label,
                checked: (draft.groups || []).includes(record.code),
                enabled,
                action: { type: 'group', code: record.code }
            }
        ),
        label(
            'profileGroupDescription',
            rect(12, 42, compact ? width - 24 : width - 186, 36),
            record.description || '',
            Object.assign({}, muted, { wrap: true })
        )
    ];
    if (!model.creating)
        nodes.push(
            node(
                'Choice',
                'profileAccess_' + record.code,
                rect(
                    compact ? 12 : width - 166,
                    compact ? 80 : 14,
                    compact ? width - 24 : 154,
                    36
                ),
                {
                    value: draft.accessLevels?.[record.code] || '',
                    label: text('Access level'),
                    enabled,
                    options: accessLevels.map(([value, name]) => ({
                        value,
                        label: text(name)
                    })),
                    action: { type: 'access', code: record.code }
                }
            )
        );
    return {
        nodes: [
            node(
                'Box',
                'profileMembership',
                rect(0, 0, width, compact && !model.creating ? 124 : 84),
                {
                    background: 'surfaceContainerHigh',
                    radius: 10,
                    children: nodes
                }
            )
        ]
    };
}

export function describe(model, width, viewportHeight, language) {
    const height = Math.max(540, viewportHeight);
    const text = (key) => translate(key, language),
        margin = width < 500 ? 12 : 20,
        inner = width - margin * 2;
    const nodes = [],
        draft = model.draft || {},
        enabled = !model.saving && !model.uncertain,
        compact = width < 520;
    nodes.push(
        node('View', 'profileEditorAvatar', rect(margin, 14, 54, 54), {
            view: 'avatar'
        })
    );
    const changeWidth =
        model.mode === 'profile'
            ? Math.min(inner - 72, language === 'ru' ? 160 : 140)
            : 0;
    nodes.push(
        label(
            'profileEditorName',
            rect(margin + 66, 16, inner - 74 - changeWidth, 24),
            model.creating ? text('New user') : model.displayName,
            { weight: 600 }
        )
    );
    nodes.push(
        label(
            'profileEditorLogin',
            rect(margin + 66, 42, inner - 74 - changeWidth, 20),
            draft.login || '',
            muted
        )
    );
    if (model.mode === 'profile')
        nodes.push(
            button(
                'profileAvatarChange',
                rect(width - margin - changeWidth, 22, changeWidth, 36),
                text('Change avatar'),
                'image',
                { type: 'avatar' },
                enabled
            )
        );
    let top = 82;
    if (model.avatarName) {
        nodes.push(
            label(
                'profileAvatarPending',
                rect(margin, top, inner, 24),
                model.avatarName,
                muted
            )
        );
        top += 30;
    }
    if (model.canManage && !model.restricted) {
        for (const [index, mode] of ['profile', 'groups'].entries())
            nodes.push(
                button(
                    'profileEditorTab_' + mode,
                    rect(
                        margin + (index * (inner + 6)) / 2,
                        top,
                        (inner - 6) / 2,
                        36
                    ),
                    text(mode === 'profile' ? 'Profile' : 'Groups'),
                    mode === 'profile' ? 'person' : 'group',
                    { type: 'mode', value: mode },
                    !model.saving,
                    { radio: true, selected: model.mode === mode }
                )
            );
        top += 46;
    }
    let footer = height - 58,
        noticeHeight =
            (model.error ? 64 : 0) +
            (model.uncertain ? 44 : 0) +
            (model.confirmClose ? (inner < 380 ? 168 : 122) : 0);
    const bodyHeight = Math.max(80, footer - top - noticeHeight - 10);
    if (model.mode === 'groups') {
        const intro =
            text("Group membership changes affect this user's permissions.") +
            (model.creating
                ? ''
                : ' ' +
                  text(
                      "Access level is shared by every member of the group. Empty uses TACTIC's Low default."
                  ));
        nodes.push(
            label(
                'profileMembershipExplanation',
                rect(margin, top, inner, compact ? 88 : 56),
                intro,
                Object.assign({}, muted, { wrap: true })
            )
        );
        const offset = compact ? 96 : 64;
        nodes.push(
            node(
                'List',
                'profileMemberships',
                rect(
                    margin,
                    top + offset,
                    inner,
                    Math.max(0, bodyHeight - offset)
                ),
                {
                    source: 'groups',
                    fields: groupFields,
                    keyField: 'code',
                    rowHeight: inner - 16 < 500 && !model.creating ? 132 : 92,
                    rowGap: 8,
                    scrollbarId: 'userProfileEditorScrollBar'
                }
            )
        );
    } else {
        const fields = [],
            columnWidth = compact ? inner - 16 : (inner - 28) / 2;
        let y = 0,
            column = 0;
        const field = (key, name, wide = false) => {
            if (!Object.prototype.hasOwnProperty.call(draft, key)) return;
            if (wide && column) {
                y += 64;
                column = 0;
            }
            const x = compact ? 0 : column * (columnWidth + 12),
                fieldWidth = wide ? inner - 16 : columnWidth,
                fieldIcon = FIELD_ICONS[key] || '';
            if (fieldIcon)
                fields.push(
                    icon(
                        'profileFieldIcon_' + key,
                        rect(x + 2, y + 3, 14, 14),
                        fieldIcon,
                        muted
                    )
                );
            fields.push(
                label(
                    'profileLabel_' + key,
                    rect(
                        fieldIcon ? x + 20 : x,
                        y,
                        Math.max(0, fieldWidth - (fieldIcon ? 20 : 0)),
                        20
                    ),
                    text(name),
                    muted
                )
            );
            fields.push(
                node(
                    'Field',
                    'profileField_' + key,
                    rect(x, y + 23, fieldWidth, 36),
                    {
                        text: draft[key] || '',
                        label: text(name),
                        placeholder: text(name),
                        enabled,
                        password: key === 'password',
                        action: { type: 'field', key }
                    }
                )
            );
            if (compact || wide || column) {
                y += 68;
                column = 0;
            } else column = 1;
        };
        if (model.creating) field('login', 'Login', true);
        for (const [key, name] of profileFields)
            field(key, name, key === 'address');
        field('password', 'New password — leave empty to keep current', true);
        if (model.canManage && !model.restricted) {
            if (column) {
                y += 68;
                column = 0;
            }
            fields.push(
                label(
                    'profileAccountHeading',
                    rect(0, y, inner - 16, 24),
                    text('ACCOUNT SETTINGS'),
                    muted
                )
            );
            y += 30;
            for (const [key, name] of accountFields) field(key, name);
        }
        nodes.push(
            node(
                'Scroll',
                'profileEditorFields',
                rect(margin, top, inner, bodyHeight),
                {
                    contentHeight: y + (column ? 68 : 0),
                    scrollbarId: 'userProfileEditorScrollBar',
                    children: fields
                }
            )
        );
    }
    let noticeY = top + bodyHeight + 6;
    if (model.error) {
        nodes.push(
            label(
                'profileEditorError',
                rect(margin, noticeY, inner, 60),
                text(model.error),
                { wrap: true, color: 'red', role: 'alert' }
            )
        );
        noticeY += 64;
    }
    if (model.uncertain) {
        nodes.push(
            button(
                'profileEditorReload',
                rect(margin, noticeY, inner, 36),
                text('Reload from server'),
                'refresh',
                { type: 'reload' },
                !model.saving
            )
        );
        noticeY += 44;
    }
    if (model.confirmClose) {
        const confirmation = Confirmation.describe(
            {
                message: text('Discard unsaved user changes?'),
                accept: 'Discard changes',
                reject: 'Keep editing',
                acceptId: 'profileDiscard',
                rejectId: 'profileKeepEditing',
                destructive: true
            },
            inner,
            inner < 380 ? 168 : 122,
            language
        );
        for (const item of confirmation.nodes) {
            if (item.action)
                item.action.type =
                    item.action.type === 'accept' ? 'discard' : 'keep';
        }
        nodes.push(
            node(
                'Box',
                'profileDiscardConfirmation',
                rect(margin, noticeY, inner, inner < 380 ? 168 : 122),
                { children: confirmation.nodes }
            )
        );
    }
    const actionWidth = (inner - 8) / 2;
    nodes.push(
        button(
            'userProfileEditorCancel',
            rect(margin, footer, actionWidth, 38),
            text('Cancel'),
            '',
            { type: 'close' },
            !model.saving
        )
    );
    nodes.push(
        button(
            'userProfileEditorSave',
            rect(margin + actionWidth + 8, footer, actionWidth, 38),
            text(model.creating ? 'Create' : 'Save'),
            'save',
            { type: 'save' },
            enabled,
            { highlighted: true }
        )
    );
    return {
        nodes: [
            node(
                'Scroll',
                'profileEditorBody',
                rect(0, 0, width, viewportHeight),
                { contentHeight: height, children: nodes }
            )
        ]
    };
}
