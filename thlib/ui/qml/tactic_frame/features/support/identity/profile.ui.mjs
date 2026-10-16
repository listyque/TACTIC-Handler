import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { format as formatNumber } from '../../../controls/forms/number.mjs';
import { controls } from '../../../core/foundation.mjs';

export const userFields = [
    'login',
    'displayName',
    'initials',
    'avatarUrl',
    'avatarColor',
    'primaryGroup',
    'current',
    'selected',
    'presenceKnown',
    'online'
];

export function matchesUser(record, query) {
    const groups = (record.groups || []).map((group) =>
        typeof group === 'string' ? group : group.label || group.code || ''
    );
    const terms = [
        record.login,
        record.displayName,
        record.email || '',
        groups.join(' ')
    ]
        .join(' ')
        .toLowerCase();
    return terms.includes(
        String(query || '')
            .trim()
            .toLowerCase()
    );
}

export function userRow(model, record, width, language) {
    return {
        nodes: [
            node(
                'Action',
                'userDirectoryRow_' + record.login,
                rect(0, 0, width, 58),
                {
                    text: record.displayName,
                    selected: model.profile.login === record.login,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    radius: 10,
                    action: { type: 'user', login: record.login },
                    children: [
                        node('Preview', 'userAvatar', rect(8, 10, 38, 38), {
                            source: record.avatarUrl,
                            initials: record.initials,
                            accent: record.avatarColor,
                            round: true,
                            outlined: true
                        }),
                        label(
                            'userName',
                            rect(56, 5, width - 78, 24),
                            record.displayName,
                            { weight: 600 }
                        ),
                        label(
                            'userLogin',
                            rect(56, 29, width - 78, 22),
                            record.login + ' · ' + (record.primaryGroup || ''),
                            muted
                        ),
                        node(
                            'Box',
                            'userPresence',
                            rect(width - 15, 25, 7, 7),
                            {
                                visible: !!record.presenceKnown,
                                background: record.online
                                    ? 'green'
                                    : 'secondaryText',
                                radius: 4
                            }
                        )
                    ]
                }
            )
        ]
    };
}

function chips(id, records, width, language, action) {
    const columns = Math.max(1, Math.floor((width + 6) / 160)),
        cell = (width - (columns - 1) * 6) / columns;
    const height = controls.summaryChip.height,
        step = height + 6;
    const nodes = records.map((record, index) =>
        node(
            'SummaryChip',
            id + '_' + index,
            rect(
                (index % columns) * (cell + 6),
                Math.floor(index / columns) * step,
                cell,
                height
            ),
            {
                text:
                    record.label ||
                    record.code ||
                    record.value ||
                    translate('Unspecified', language),
                fontRole: 'secondary',
                count: record.count || 0,
                showCount: record.count !== undefined,
                showDot: record.showDot !== false,
                accent: record.color || 'action',
                action: action
                    ? Object.assign({}, action, { value: record.value })
                    : null
            }
        )
    );
    return { nodes, height: Math.ceil(records.length / columns) * step };
}

export function summary(model, width, language) {
    const text = (key) => translate(key, language),
        profile = model.profile || {},
        compact = width < 620,
        groupsBeside = width >= 700;
    const avatar = compact ? 56 : 168,
        left = compact ? 82 : 195;
    const groupWidth = groupsBeside
        ? Math.min(240, Math.max(160, width * 0.26))
        : width - 26;
    const groupX = groupsBeside ? width - 13 - groupWidth : 13;
    const actions = [];
    if (!profile.current)
        actions.push(['profileMessage', 'Message', 'message', 'message']);
    if (model.canEdit)
        actions.push(['profileEdit', 'Edit user profile', 'edit', 'edit']);
    actions.push(['profileRefresh', 'Refresh profile', 'refresh', 'refresh']);
    if (profile.current)
        actions.push(['profileLogout', 'Sign out', 'logout', 'logout']);
    const nodes = [
        node('Preview', 'profileAvatar', rect(13, 13, avatar, avatar), {
            source: profile.avatarUrl,
            initials: profile.initials,
            accent: profile.avatarColor,
            round: true,
            outlined: true
        }),
        label(
            'profileName',
            rect(
                left,
                14,
                width - left - 13 - (compact ? 0 : actions.length * 40 + 8),
                28
            ),
            profile.displayName || profile.login || '',
            { fontRole: 'display', weight: 600 }
        ),
        label(
            'profilePresence',
            rect(left, 44, width - left - 13, 22),
            profile.login +
                ' · ' +
                text(
                    profile.presenceKnown
                        ? profile.online
                            ? 'Online'
                            : 'Offline'
                        : 'Status unavailable'
                ),
            muted
        )
    ];
    actions.forEach(([id, name, icon, type], index) =>
        nodes.push(
            button(
                id,
                rect(
                    (compact ? 13 : width - 13 - actions.length * 40) +
                        index * 40,
                    compact ? 80 : 14,
                    36,
                    36
                ),
                text(name),
                icon,
                { type },
                !model.saving && (type !== 'refresh' || !model.busy),
                { iconOnly: true, destructive: type === 'logout' }
            )
        )
    );
    const infoX = compact ? 13 : left,
        infoY = compact ? 130 : 82,
        infoWidth = (groupsBeside ? groupX - 14 : width - 13) - infoX;
    const columns = infoWidth >= 560 ? 3 : infoWidth >= 240 ? 2 : 1,
        rowHeight = 33;
    const values = [
        ['Project', profile.project, 'briefcase'],
        ['Email', profile.email, 'email'],
        [
            'Contact',
            profile.phone_number ?? profile.phoneNumber ?? profile.contact,
            'phone'
        ],
        ['Address', profile.address, 'address-book'],
        ['Department', profile.department, 'briefcase'],
        ['Server', model.server || profile.server, 'server']
    ];
    const cell = infoWidth / columns;
    values.forEach(([name, value, icon], index) => {
        const x = infoX + (index % columns) * cell,
            y = infoY + Math.floor(index / columns) * rowHeight;
        nodes.push(
            node('Icon', 'profileInfoIcon' + index, rect(x, y + 9, 15, 15), {
                icon,
                color: 'secondaryText'
            })
        );
        nodes.push(
            label(
                'profileInfoLabel' + index,
                rect(x + 23, y, cell - 31, 14),
                text(name),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
        nodes.push(
            label(
                'profileInfoValue' + index,
                rect(x + 23, y + 15, cell - 31, 18),
                String(value || '—')
            )
        );
    });
    const infoBottom = infoY + Math.ceil(values.length / columns) * rowHeight;
    const groupsY = groupsBeside ? 82 : Math.max(avatar + 26, infoBottom) + 12;
    if (groupsBeside)
        nodes.push(
            node(
                'Box',
                'profileGroupDivider',
                rect(
                    groupX - 10,
                    groupsY,
                    1,
                    Math.max(90, infoBottom - groupsY)
                ),
                { background: 'outlineVariant' }
            )
        );
    nodes.push(
        label(
            'profileGroupsHeading',
            rect(groupX, groupsY, groupWidth - 36, 24),
            text('GROUPS AND ROLES'),
            muted
        )
    );
    if (model.canManage && !model.restricted)
        nodes.push(
            button(
                'profileEditGroups',
                rect(groupX + groupWidth - 32, groupsY - 4, 32, 32),
                text('Edit group membership'),
                'group',
                { type: 'editGroups' },
                !model.saving,
                { iconOnly: true }
            )
        );
    const groups = (profile.groups || [])
        .map((group) => (typeof group === 'string' ? { label: group } : group))
        .concat(
            (profile.roles || []).map((role) => ({
                label: role,
                showDot: false
            }))
        );
    const packed = chips('profileGroup', groups, groupWidth, language);
    nodes.push(
        ...packed.nodes.map((item) =>
            Object.assign({}, item, {
                x: item.x + groupX,
                y: item.y + groupsY + 30
            })
        )
    );
    if (!groups.length)
        nodes.push(
            label(
                'profileNoGroups',
                rect(groupX, groupsY + 30, groupWidth, 42),
                text('No groups or roles returned by TACTIC'),
                Object.assign({}, muted, { wrap: true })
            )
        );
    const height = Math.max(
        avatar + 26,
        infoBottom + 13,
        groupsY + 30 + Math.max(packed.height, 42) + 13
    );
    return {
        nodes: [
            node('Box', 'profileSummaryCard', rect(0, 0, width, height), {
                background: 'surfaceContainerHigh',
                radius: 9,
                children: nodes
            })
        ],
        height
    };
}

export function work(model, width, language) {
    const text = (key) => translate(key, language),
        nodes = [],
        summary = model.taskSummary || {};
    nodes.push(
        label(
            'profileTasksHeading',
            rect(0, 0, width, 26),
            text('PROJECT TASKS'),
            muted
        )
    );
    const columns = width < 400 ? 2 : 3,
        cell = width / columns;
    const metrics = [
        ['total', 'Total'],
        ['completed', 'Completed tasks'],
        ['incomplete', 'Incomplete'],
        ['overdue', 'Overdue'],
        ['dueThisWeek', 'Due this week']
    ];
    metrics.forEach(([key, name], index) => {
        const y = 34 + Math.floor(index / columns) * 70,
            x = (index % columns) * cell;
        const value =
            key === 'completed'
                ? Math.max(0, (summary.total || 0) - (summary.incomplete || 0))
                : summary[key] || 0;
        nodes.push(
            label(
                'profileTaskMetric_' + key,
                rect(x, y, cell - 8, 32),
                model.tasksBusy ? '—' : String(value),
                {
                    fontRole: 'hero',
                    weight: 600,
                    color: key === 'overdue' && value ? 'red' : 'primaryText'
                }
            )
        );
        nodes.push(
            label(
                'profileTaskLabel_' + key,
                rect(x, y + 35, cell - 8, 32),
                text(name),
                Object.assign({}, muted, { wrap: true })
            )
        );
    });
    let y = 34 + Math.ceil(metrics.length / columns) * 70 + 12;
    for (const [key, name, filter] of [
        ['statusSummary', 'BY STATUS', 'status'],
        ['processSummary', 'BY PROCESS', 'process']
    ]) {
        nodes.push(
            label(
                'profileTaskSection_' + key,
                rect(0, y, width, 26),
                text(name),
                muted
            )
        );
        y += 32;
        const packed = chips(
            'profileTask_' + key,
            model[key] || [],
            width,
            language,
            { type: 'tasks', key: filter }
        );
        nodes.push(
            ...packed.nodes.map((item) =>
                Object.assign({}, item, { y: item.y + y })
            )
        );
        y += packed.height + 12;
    }
    if (model.viewWorkHours) {
        nodes.push(
            label(
                'profileHoursHeading',
                rect(0, y, width, 26),
                text('WORK HOURS') + ' · ' + text('THIS WEEK'),
                muted
            )
        );
        y += 32;
        const hours = model.workHourSummary || {};
        [
            ['loggedHours', 'Logged'],
            ['approvedHours', 'Approved'],
            ['pendingHours', 'Pending']
        ].forEach(([key, name], index) => {
            nodes.push(
                label(
                    'profileHours_' + key,
                    rect((index * width) / 3, y, width / 3 - 8, 32),
                    text('{hours} h').replace(
                        '{hours}',
                        formatNumber(Number(hours[key] || 0), 1, language)
                    ),
                    { fontRole: 'title', weight: 600 }
                )
            );
            nodes.push(
                label(
                    'profileHoursLabel_' + key,
                    rect((index * width) / 3, y + 34, width / 3 - 8, 24),
                    text(name),
                    muted
                )
            );
        });
        y += 72;
    }
    nodes.push(
        button(
            'profileOpenTasks',
            rect(0, y, width, 38),
            text('Open Task Manager'),
            'task',
            { type: 'tasks' },
            !!model.profile?.login,
            { highlighted: true }
        )
    );
    y += 48;
    if (!model.tasksBusy && !summary.total) {
        nodes.push(
            label(
                'profileNoTasks',
                rect(0, y, width, 42),
                text('No assigned tasks in the current project'),
                Object.assign({}, muted, { wrap: true })
            )
        );
        y += 48;
    }
    return { nodes, height: y };
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 760,
        margin = compact ? 8 : 12;
    const directoryWidth =
        !model.directory || compact
            ? 0
            : Math.min(360, Math.max(210, model.directoryWidth || 252));
    const x = margin + (directoryWidth ? directoryWidth + 8 : 0),
        paneWidth = width - margin - x;
    const nodes = [];
    if (model.directory && (!compact || model.directoryExpanded)) {
        const leftWidth = compact ? width - margin * 2 : directoryWidth;
        nodes.push(
            node(
                'Box',
                'profileDirectory',
                rect(margin, margin, leftWidth, height - margin * 2),
                {
                    background: 'panel',
                    border: 'outlineVariant',
                    radius: 12,
                    children: [
                        label(
                            'profileDirectoryHeading',
                            rect(12, 6, leftWidth - 64, 28),
                            text('USERS'),
                            { fontRole: 'section' }
                        ),
                        button(
                            'profileAddUser',
                            rect(leftWidth - 44, 4, 32, 32),
                            text('Add user'),
                            'person-add',
                            { type: 'create' },
                            model.canManage && !model.restricted,
                            {
                                iconOnly: true,
                                visible: model.canManage && !model.restricted
                            }
                        ),
                        node(
                            'Field',
                            'profileDirectorySearch',
                            rect(12, 44, leftWidth - 24, 38),
                            {
                                text: model.query || '',
                                label: text('Search users'),
                                placeholder: text('Search users'),
                                enabled: true,
                                action: { type: 'query' }
                            }
                        ),
                        node(
                            'List',
                            'userDirectoryList',
                            rect(
                                6,
                                90,
                                leftWidth - 12,
                                height - margin * 2 - 96
                            ),
                            {
                                source: 'users',
                                keyField: 'login',
                                fields: userFields,
                                rowHeight: 62,
                                rowGap: 4,
                                scrollbarId: 'userDirectoryScrollBar'
                            }
                        )
                    ]
                }
            )
        );
        if (!compact)
            nodes.push(
                node(
                    'Splitter',
                    'profileDirectorySplitter',
                    rect(
                        margin + directoryWidth,
                        margin,
                        8,
                        height - margin * 2
                    ),
                    {
                        value: directoryWidth,
                        min: 210,
                        max: 360,
                        text: text('Resize user directory'),
                        action: { type: 'directoryWidth' }
                    }
                )
            );
    }
    if (compact && model.directory && model.directoryExpanded) return { nodes };
    const content = [],
        bodyWidth = paneWidth - 24;
    let y = 12;
    if (compact && model.directory) {
        content.push(
            button(
                'profileShowDirectory',
                rect(12, y, bodyWidth, 36),
                text('Show users'),
                'group',
                { type: 'showDirectory' },
                true
            )
        );
        y += 46;
    }
    if (model.profile?.login) {
        const card = summary(model, bodyWidth, language);
        content.push(
            ...card.nodes.map((item) =>
                Object.assign({}, item, { x: item.x + 12, y: item.y + y })
            )
        );
        y += card.height + 24;
        const split = bodyWidth >= 860,
            workWidth = split ? Math.floor(bodyWidth * 0.61) - 24 : bodyWidth;
        const tasks = work(model, workWidth, language);
        content.push(
            node('Box', 'profileWork', rect(12, y, workWidth, tasks.height), {
                children: tasks.nodes
            })
        );
        const activityX = split ? 12 + Math.floor(bodyWidth * 0.61) + 24 : 12,
            activityY = split ? y : y + tasks.height + 24;
        const activityWidth = split
            ? bodyWidth - Math.floor(bodyWidth * 0.61) - 24
            : bodyWidth;
        content.push(
            label(
                'profileRecentHeading',
                rect(activityX, activityY, activityWidth - 40, 28),
                text('RECENT ACTIVITY'),
                muted
            )
        );
        content.push(
            button(
                'openFullUserActivityButton',
                rect(activityX + activityWidth - 34, activityY - 3, 32, 32),
                text('Open full activity'),
                'activity-feed',
                { type: 'activity' },
                true,
                { iconOnly: true }
            )
        );
        let activityHeight = model.activityHeight || 0;
        content.push(
            node(
                'View',
                'profileActivityCards',
                rect(activityX, activityY + 38, activityWidth, activityHeight),
                { view: 'activity' }
            )
        );
        if (model.activityCount > 6) {
            content.push(
                button(
                    'profileExpandActivity',
                    rect(
                        activityX,
                        activityY + 38 + activityHeight,
                        activityWidth,
                        36
                    ),
                    text(model.expanded ? 'Show less' : 'Show more'),
                    model.expanded ? 'expand-less' : 'expand-more',
                    { type: 'expand' },
                    true
                )
            );
            activityHeight += 44;
        }
        if (!model.activityCount && !model.relatedBusy) {
            content.push(
                label(
                    'profileNoActivity',
                    rect(activityX, activityY + 38, activityWidth, 48),
                    text(
                        model.activityError
                            ? 'Activity is unavailable'
                            : 'No recent activity'
                    ),
                    Object.assign({}, muted, { wrap: true })
                )
            );
            activityHeight = 48;
        }
        y = Math.max(y + tasks.height, activityY + 38 + activityHeight) + 16;
    } else if (model.busy) {
        content.push(
            label(
                'profileLoading',
                rect(12, y, bodyWidth, 56),
                text('Loading user profile…'),
                Object.assign({}, muted, { wrap: true })
            )
        );
        y += 64;
    }
    if (model.error || model.activityError) {
        content.push(
            label(
                'profileError',
                rect(12, y, bodyWidth, 72),
                text(model.error || model.activityError),
                { wrap: true, color: 'red', role: 'alert' }
            )
        );
        y += 80;
    }
    nodes.push(
        node(
            'Box',
            'profilePane',
            rect(x, margin, paneWidth, height - margin * 2),
            {
                background: 'panel',
                border: 'outlineVariant',
                radius: 12,
                children: [
                    node(
                        'Scroll',
                        'profileScroll',
                        rect(0, 0, paneWidth, height - margin * 2),
                        {
                            contentHeight: y,
                            children: content,
                            scrollbarId: 'profileScrollBar'
                        }
                    )
                ]
            }
        )
    );
    return { nodes };
}
