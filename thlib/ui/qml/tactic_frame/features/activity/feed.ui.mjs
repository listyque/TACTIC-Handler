import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const filters = [
    ['all', 'All', 'select-all'],
    ['my_tasks', 'My tasks', 'task'],
    ['my_objects', 'My objects', 'inventory-2'],
    ['notes', 'Notes', 'notes'],
    ['publications', 'Publications', 'snapshot']
];
export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language),
        phone = !!model.phone,
        expanded = !phone || !!model.optionsVisible,
        narrow = width < 716,
        icons = width < 956,
        calendarCompact = width < 1076,
        userCompact = width < 1276,
        nodes = [];
    const check = (id, y, x, w, text, value, type) =>
        nodes.push(
            node('CheckBox', id, rect(x, y, w, 28), {
                text: tr(text),
                checked: !!value,
                compact: true,
                action: { type }
            })
        );
    if (!phone)
        nodes.push(
            label(
                'activityFeedTitle',
                rect(
                    10,
                    16,
                    narrow ? width - 20 : Math.max(0, width - 460),
                    18
                ),
                tr('ACTIVITY FEED'),
                { fontRole: 'body', weight: 600, color: 'secondaryText' }
            )
        );
    if (expanded)
        check(
            'activityFeedNotificationsEnabled',
            phone ? 54 : narrow ? 36 : 10,
            narrow ? 10 : width - 450,
            narrow ? width - 20 : 220,
            'Activity notifications',
            model.notifications,
            'notifications'
        );
    if (expanded)
        check(
            'activityFeedExcludeOwnActivity',
            phone ? 86 : narrow ? 68 : 10,
            narrow ? 10 : width - 222,
            narrow ? width - 20 : 212,
            'Exclude my activity',
            model.excludeOwn,
            'exclude'
        );
    const searchY = phone ? 6 : narrow ? 104 : 48,
        searchWidth = phone ? width - 68 : narrow ? width - 20 : 220;
    nodes.push(
        node(
            'Field',
            'activityFeedSearchField',
            rect(10, searchY, searchWidth, 38),
            {
                label: tr('Search activity'),
                placeholder: tr('Search activity'),
                text: model.search || '',
                paddingLeft: 38,
                paddingRight: model.search ? 36 : 12,
                action: { type: 'search' }
            }
        )
    );
    nodes.push(
        node('Icon', 'activityFeedSearchIcon', rect(22, searchY + 10, 18, 18), {
            icon: 'search',
            color: 'secondaryText'
        })
    );
    if (model.search)
        nodes.push(
            button(
                'activityFeedClearSearch',
                rect(10 + searchWidth - 32, searchY + 6, 26, 26),
                '',
                'close',
                { type: 'search', value: '' },
                true,
                { label: tr('Clear search'), iconOnly: true, iconAction: true }
            )
        );
    if (phone)
        nodes.push(
            button(
                'activityFeedOptions',
                rect(width - 48, 6, 38, 38),
                '',
                'tune',
                { type: 'options' },
                true,
                {
                    label: tr('Activity options'),
                    iconOnly: true,
                    iconAction: true,
                    selected: !!model.optionsVisible
                }
            )
        );
    if (!expanded) return { height: 50, nodes };
    const actionsY = phone ? 178 : narrow ? 194 : 48,
        userWidth = userCompact ? 38 : 160,
        calendarWidth = calendarCompact ? 38 : 160,
        actionsWidth = userWidth + calendarWidth + 54,
        actionsX = Math.max(10, width - 10 - actionsWidth),
        filterY = phone ? 132 : narrow ? 150 : 48,
        filterX = narrow ? 10 : 240,
        filterWidth = narrow ? width - 20 : Math.max(0, actionsX - 8 - filterX);
    nodes.push(
        node(
            phone ? 'Choice' : 'Segmented',
            'activityFeedFilterSegments',
            rect(filterX, filterY, filterWidth, 38),
            {
                label: tr('Activity filters'),
                options: filters.map(([value, text, icon]) => ({
                    value,
                    label: tr(text),
                    icon
                })),
                value: model.filter || 'all',
                iconOnly: icons,
                action: { type: 'filter' }
            }
        )
    );
    nodes.push(
        button(
            userCompact
                ? 'activityFeedCompactUserFilterButton'
                : 'activityFeedUserFilterButton',
            rect(actionsX, actionsY, userWidth, 38),
            userCompact ? '' : model.userTitle || tr('All users'),
            'groups',
            { type: 'users' },
            true,
            {
                label: model.userTitle || tr('Filter by users'),
                iconOnly: userCompact,
                badgeCount: model.userCount || 0,
                highlighted: model.userCount > 0,
                pressAction: { type: 'users-press' }
            }
        )
    );
    nodes.push(
        button(
            'activityFeedCalendarButton',
            rect(actionsX + userWidth + 8, actionsY, calendarWidth, 38),
            calendarCompact ? '' : model.dayLabel || tr('All history'),
            'calendar-month',
            { type: 'calendar' },
            true,
            {
                label: model.dayLabel || tr('All history'),
                iconOnly: calendarCompact,
                highlighted: !!model.day,
                pressAction: { type: 'calendar-press' }
            }
        )
    );
    nodes.push(
        button(
            'activityFeedRefreshButton',
            rect(width - 48, actionsY, 38, 38),
            '',
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { label: tr('Refresh activity'), iconOnly: true, iconAction: true }
        )
    );
    const height = phone ? 226 : narrow ? 242 : 96;
    nodes.unshift(
        node('Box', 'activityFeedToolbarSurface', rect(0, 0, width, height), {
            background: 'surfaceContainerHigh',
            radius: 9
        })
    );
    return { height, nodes };
}
export function day(title, width) {
    const w = Math.min(width * 0.75, Math.max(60, String(title).length * 6));
    return {
        height: 34,
        nodes: [
            label('activityDayTitle', rect(4, 9, w, 16), title, {
                fontRole: 'secondary',
                weight: 600,
                color: 'secondaryText'
            }),
            node(
                'Box',
                'activityDaySeparator',
                rect(w + 14, 17, Math.max(0, width - w - 20), 1),
                { background: 'separator' }
            )
        ]
    };
}
export function peoplePopup(width, height) {
    return {
        width: Math.max(0, Math.min(396, width - 24)),
        height: Math.max(0, Math.min(516, height - 48))
    };
}
export function people(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values),
        footer = Math.max(160, height - 38),
        nodes = [
            node('Icon', 'activityUserFilterIcon', rect(0, 4, 22, 22), {
                icon: 'groups',
                color: 'action'
            }),
            label(
                'activityUserFilterTitle',
                rect(32, 0, Math.max(0, width - 32), 20),
                tr('Filter by users'),
                { fontRole: 'bodyLarge', weight: 600 }
            ),
            label(
                'activityUserFilterDescription',
                rect(32, 24, Math.max(0, width - 32), 32),
                tr('Show activity created by selected users'),
                { fontRole: 'secondary', color: 'secondaryText', wrap: true }
            ),
            node('Box', 'activityUserFilterSeparator', rect(0, 64, width, 1), {
                background: 'separator'
            }),
            node(
                'View',
                'activityUserPickerPort',
                rect(0, 77, width, Math.max(0, footer - 89)),
                { view: 'people' }
            ),
            label(
                'activityUserFilterCount',
                rect(0, footer + 10, Math.max(0, width - 250), 16),
                model.count
                    ? tr('{count} users', { count: model.count })
                    : tr('All users'),
                { fontRole: 'secondary', color: 'secondaryText' }
            ),
            button(
                'activityFeedClearUserFilterButton',
                rect(Math.max(0, width - 244), footer, 76, 38),
                tr('Clear'),
                '',
                { type: 'clear' },
                !!model.count
            ),
            button(
                'activityFeedCancelUserFilterButton',
                rect(Math.max(0, width - 160), footer, 76, 38),
                tr('Cancel'),
                '',
                { type: 'cancel' },
                true
            ),
            button(
                'activityFeedApplyUserFilterButton',
                rect(Math.max(0, width - 76), footer, 76, 38),
                tr('Apply'),
                '',
                { type: 'apply' },
                true,
                { highlighted: true }
            )
        ];
    return { nodes };
}
