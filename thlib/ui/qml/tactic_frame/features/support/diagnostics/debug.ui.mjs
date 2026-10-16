import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export const eventFields = [
    'eventId',
    'timestamp',
    'level',
    'message',
    'module',
    'functionName',
    'line',
    'group',
    'source',
    'command',
    'stacktrace',
    'duration',
    'sizeKb',
    'thread',
    'details',
    'selected'
];
export const groupFields = [
    'identity',
    'key',
    'label',
    'depth',
    'count',
    'selected'
];

export function levelColor(level) {
    if (['ERROR', 'CRITICAL', 'EXCEPTION'].includes(level)) return 'red';
    if (['WARNING', 'MISSING'].includes(level)) return 'yellow';
    return level === 'INFO'
        ? 'green'
        : level === 'API'
          ? 'action'
          : 'secondaryText';
}

export function row(model, list, record, width, language) {
    const text = (key) => translate(key, language);
    if (list.source === 'groups') {
        const x = 10 + Number(record.depth || 0) * 13;
        return {
            nodes: [
                node(
                    'Action',
                    'debugGroup_' + record.depth + '_' + record.key,
                    rect(0, 0, width, 36),
                    {
                        text: record.key ? record.label : text('FULL LOG'),
                        selected: model.group === record.key,
                        radius: 8,
                        normalColor: 'transparent',
                        selectedColor: 'contentSelection',
                        action: { type: 'group', value: record.key },
                        children: [
                            node('Icon', 'groupIcon', rect(x, 11, 14, 14), {
                                icon: record.depth
                                    ? 'subdirectory-arrow-right'
                                    : 'folder',
                                color: 'secondaryText'
                            }),
                            label(
                                'groupName',
                                rect(x + 22, 4, width - x - 70, 28),
                                record.key ? record.label : text('FULL LOG')
                            ),
                            label(
                                'groupCount',
                                rect(width - 42, 4, 36, 28),
                                String(record.count),
                                Object.assign({}, muted, { align: 'right' })
                            )
                        ]
                    }
                )
            ]
        };
    }
    const compact = width < 550,
        metricWidth = compact ? 0 : 112;
    const accent = levelColor(record.level),
        textX = compact ? 88 : 120;
    const keys = {};
    for (const key of ['ArrowUp', 'ArrowDown', 'Home', 'End'])
        keys[key] = { type: 'eventKey', id: record.eventId, key };
    const children = [
        node('Box', 'eventRail', rect(0, 12, 3, 36), {
            background: accent,
            radius: 2
        }),
        node('Box', 'eventLevel', rect(10, 18, compact ? 66 : 76, 24), {
            background: { mix: [accent, 'panel', 0.86] },
            radius: 7,
            children: [
                label(
                    'eventLevelText',
                    rect(2, 0, compact ? 62 : 72, 24),
                    record.level,
                    {
                        fontRole: 'caption',
                        color: accent,
                        weight: 600,
                        align: 'center'
                    }
                )
            ]
        }),
        label(
            'eventMessage',
            rect(textX, 8, width - textX - metricWidth - 10, 23),
            String(record.message).replace(/\s+/g, ' ')
        ),
        label(
            'eventSource',
            rect(textX, 33, width - textX - metricWidth - 10, 18),
            [record.group, record.module, record.functionName]
                .filter(Boolean)
                .join(' · '),
            muted
        )
    ];
    if (!compact) {
        children.push(
            node('Icon', 'eventCommandIcon', rect(94, 21, 16, 16), {
                icon: record.command ? 'terminal' : 'info',
                color: 'action'
            })
        );
        children.push(
            label(
                'eventTime',
                rect(width - 116, 9, 106, 20),
                String(record.timestamp).slice(11, 23),
                Object.assign({}, muted, {
                    monospace: true,
                    wrap: false,
                    align: 'right'
                })
            )
        );
        children.push(
            label(
                'eventMetrics',
                rect(width - 116, 31, 106, 20),
                (record.duration > 0
                    ? Number(record.duration).toFixed(3) + ' s '
                    : '') +
                    (record.sizeKb > 0
                        ? Number(record.sizeKb).toFixed(1) + ' KB'
                        : ''),
                Object.assign({}, muted, {
                    monospace: true,
                    wrap: false,
                    align: 'right'
                })
            )
        );
    }
    return {
        nodes: [
            node(
                'Action',
                'debugEvent_' + record.eventId,
                rect(0, 0, width, 60),
                {
                    text: record.message,
                    selected: model.selectedId === record.eventId,
                    normalColor: 'panel',
                    selectedColor: 'contentSelection',
                    radius: 8,
                    role: 'option',
                    keys,
                    action: { type: 'event', id: record.eventId },
                    children
                }
            )
        ]
    };
}

export function detail(entry, width, height, language) {
    const text = (key) => translate(key, language),
        nodes = [];
    let y = 8;
    const section = (id, title, value, code = false) => {
        if (!value) return;
        if (title) {
            nodes.push(
                label(
                    id + 'Title',
                    rect(8, y, width - 32, 22),
                    text(title),
                    muted
                )
            );
            y += 26;
        }
        const size = Math.min(
            260,
            Math.max(60, (String(value).split('\n').length + 1) * 18)
        );
        nodes.push(
            node('Area', id, rect(8, y, width - 32, size), {
                text: String(value),
                label: text(title || 'Event details'),
                readOnly: true,
                enabled: true,
                monospace: true,
                wrap: false,
                syntax: 'python',
                language
            })
        );
        y += size + 12;
    };
    if (!entry || !entry.eventId)
        nodes.push(
            label(
                'debugDetailEmpty',
                rect(8, 8, width - 32, 54),
                text(
                    'Select an event to inspect its message, runtime command and stacktrace.'
                ),
                Object.assign({}, muted, { wrap: true })
            )
        );
    else {
        section('debugMessage', '', entry.message);
        section('debugDetails', 'Details', entry.details);
        section('debugCommand', 'Runtime command', entry.command, true);
        section('debugStacktrace', 'Stacktrace', entry.stacktrace);
    }
    return node(
        'Scroll',
        'debugDetailContent',
        rect(0, 38, width, height - 38),
        { contentHeight: Math.max(height - 38, y), children: nodes }
    );
}

export function describe(model, width, height, language) {
    const text = (key) => translate(key, language),
        compact = width < 760,
        margin = compact ? 8 : 12;
    const inner = width - margin * 2,
        toolbarHeight = compact ? 246 : 104;
    const contentHeight = Math.max(height, compact ? 650 : 430),
        bodyY = margin + toolbarHeight + 10;
    const bodyHeight = contentHeight - bodyY - margin;
    const sourceWidth = compact
        ? 0
        : Math.min(
              Math.max(170, model.groupWidth || 230),
              Math.max(170, inner - 360)
          );
    const eventX = compact ? margin : margin + sourceWidth + 8,
        eventWidth = width - margin - eventX;
    const detailHeight = Math.min(
        Math.max(110, model.detailHeight || 220),
        bodyHeight * 0.55
    );
    const eventHeight = bodyHeight - detailHeight - 8;
    const controls = [];
    const actions = [
        ['debugOpen', 'Open saved debug session', 'folder-open', 'open']
    ];
    if (model.historyId)
        actions.push([
            'debugLive',
            'Return to live session',
            'activity',
            'live'
        ]);
    actions.push([
        'debugExport',
        model.canDownload ? 'Download debug session' : 'Copy session path',
        model.canDownload ? 'download' : 'content-copy',
        model.canDownload ? 'download' : 'path'
    ]);
    actions.push(['debugClear', 'Clear session', 'delete', 'clear']);
    const actionsWidth = actions.length * 38;
    const choiceWidth = compact ? inner - 28 - actionsWidth : 190;
    const searchWidth = compact
        ? inner - 20
        : Math.max(100, inner - 36 - choiceWidth - actionsWidth);
    controls.push(
        node('Field', 'debugSearch', rect(10, 10, searchWidth, 40), {
            text: model.search || '',
            label: text('Search debug log'),
            placeholder: text('Search log…'),
            enabled: true,
            action: { type: 'search' }
        })
    );
    const choiceX = compact ? 10 : searchWidth + 18,
        choiceY = compact ? 58 : 12;
    controls.push(
        node(
            'Choice',
            'debugSession',
            rect(choiceX, choiceY, choiceWidth, 36),
            {
                label: text('Debug session'),
                value: model.historyId || '',
                options: (model.sessions || []).map((option) => ({
                    value: option.value,
                    label: option.value ? option.label : text('Live session')
                })),
                enabled: !model.loading,
                action: { type: 'session' }
            }
        )
    );
    let x = choiceX + choiceWidth + 8;
    for (const [id, name, icon, type] of actions) {
        controls.push(
            button(
                id,
                rect(x, choiceY, 34, 36),
                text(name),
                icon,
                { type },
                !model.loading,
                { iconOnly: true }
            )
        );
        x += 38;
    }
    const levelsY = compact ? 102 : 58,
        chipColumns = compact ? 3 : 8;
    const chipWidth = Math.floor(
        (inner - 20 - (chipColumns - 1) * 6) / chipColumns
    );
    (model.levels || []).forEach((level, index) => {
        const active = (model.enabled || []).includes(level),
            color = levelColor(level);
        const bounds = rect(
            10 + (index % chipColumns) * (chipWidth + 6),
            levelsY + Math.floor(index / chipColumns) * 32,
            chipWidth,
            28
        );
        controls.push(
            node('Action', 'debugLevel_' + level, bounds, {
                text: level,
                checked: active,
                role: 'checkbox',
                normalColor: active
                    ? { mix: [color, 'panel', 0.86] }
                    : 'transparent',
                selectedColor: 'contentSelection',
                action: { type: 'level', level },
                children: [
                    node('Box', 'levelOutline', rect(0, 0, chipWidth, 28), {
                        background: 'transparent',
                        border: active ? color : undefined,
                        radius: 10
                    }),
                    node('Icon', 'levelCheck', rect(6, 7, 14, 14), {
                        icon: active ? 'check' : 'close',
                        color: active ? color : 'secondaryText'
                    }),
                    label(
                        'levelCaption',
                        rect(24, 0, chipWidth - 28, 28),
                        level,
                        {
                            fontRole: 'caption',
                            weight: 600,
                            color: active ? color : 'secondaryText'
                        }
                    )
                ]
            })
        );
    });
    if (compact)
        controls.push(
            node(
                'Choice',
                'debugMobileSources',
                rect(10, 204, inner - 20, 36),
                {
                    label: text('Sources'),
                    value: model.group || '',
                    options: (model.groups || []).map((option) => ({
                        value: option.value,
                        label:
                            (option.value ? option.label : text('FULL LOG')) +
                            ' · ' +
                            option.count
                    })),
                    enabled: true,
                    action: { type: 'group' }
                }
            )
        );
    const nodes = [
        node(
            'Box',
            'debugToolbar',
            rect(margin, margin, inner, toolbarHeight),
            {
                background: 'panel',
                border: 'outlineVariant',
                radius: 14,
                children: controls
            }
        )
    ];
    if (model.error || model.message) {
        const notice = String(model.error || model.message);
        nodes.push(
            label(
                'debugStatus',
                rect(eventX, bodyY, eventWidth, 48),
                text(notice),
                {
                    color: model.error ? 'red' : 'secondaryText',
                    wrap: true,
                    role: model.error ? 'alert' : 'status'
                }
            )
        );
    }
    if (!compact) {
        nodes.push(
            node(
                'Box',
                'debugSourcesPanel',
                rect(margin, bodyY, sourceWidth, bodyHeight),
                {
                    role: 'navigation',
                    label: text('Sources'),
                    background: 'panel',
                    border: 'outlineVariant',
                    radius: 12,
                    children: [
                        label(
                            'debugSourcesTitle',
                            rect(12, 4, sourceWidth - 24, 30),
                            text('Sources'),
                            { fontRole: 'section' }
                        ),
                        node(
                            'List',
                            'debugSources',
                            rect(6, 40, sourceWidth - 12, bodyHeight - 46),
                            {
                                source: 'groups',
                                keyField: 'identity',
                                fields: groupFields,
                                rowHeight: 40,
                                scrollbarId: 'debugSourcesScrollBar'
                            }
                        )
                    ]
                }
            )
        );
        nodes.push(
            node(
                'Splitter',
                'debugSourceSplitter',
                rect(margin + sourceWidth, bodyY, 8, bodyHeight),
                {
                    text: text('Sources panel width'),
                    value: sourceWidth,
                    min: 170,
                    max: Math.max(170, inner - 360),
                    action: { type: 'sourceWidth' }
                }
            )
        );
    }
    const noticeHeight = model.error || model.message ? 52 : 0;
    nodes.push(
        node(
            'Box',
            'debugEventsPanel',
            rect(
                eventX,
                bodyY + noticeHeight,
                eventWidth,
                eventHeight - noticeHeight
            ),
            {
                background: 'panel',
                border: 'outlineVariant',
                radius: 12,
                children: [
                    label(
                        'debugActivityTitle',
                        rect(12, 4, eventWidth - 24, 30),
                        text('Activity') +
                            ' · ' +
                            text('{count} events').replace(
                                '{count}',
                                model.count || 0
                            ),
                        { fontRole: 'section' }
                    ),
                    node(
                        'List',
                        'debugEvents',
                        rect(
                            6,
                            40,
                            eventWidth - 12,
                            eventHeight - noticeHeight - 46
                        ),
                        {
                            source: 'events',
                            role: 'listbox',
                            label: text('Debug events'),
                            keyField: 'eventId',
                            fields: eventFields,
                            rowHeight: 62,
                            rowGap: 2,
                            scrollbarId: 'debugEventsScrollBar'
                        }
                    )
                ]
            }
        )
    );
    if (!model.visibleCount)
        nodes.push(
            label(
                'debugEmpty',
                rect(
                    eventX + 18,
                    bodyY + noticeHeight + 46,
                    eventWidth - 36,
                    40
                ),
                text('No matching events'),
                muted
            )
        );
    nodes.push(
        node(
            'Splitter',
            'debugDetailSplitter',
            rect(eventX, bodyY + eventHeight, eventWidth, 8),
            {
                horizontal: true,
                reverse: true,
                text: text('Event details height'),
                value: detailHeight,
                min: 110,
                max: Math.max(110, bodyHeight * 0.55),
                action: { type: 'detailHeight' }
            }
        )
    );
    const entry = model.entry || {};
    nodes.push(
        node(
            'Box',
            'debugDetailPanel',
            rect(eventX, bodyY + eventHeight + 8, eventWidth, detailHeight),
            {
                background: 'panel',
                border: 'outlineVariant',
                radius: 12,
                children: [
                    label(
                        'debugDetailTitle',
                        rect(12, 4, eventWidth - 138, 30),
                        entry.eventId
                            ? text('Event #{id}').replace(
                                  '{id}',
                                  entry.eventId
                              ) +
                                  ' · ' +
                                  entry.level
                            : text('Event details'),
                        { fontRole: 'section' }
                    ),
                    button(
                        'debugInspect',
                        rect(eventWidth - 118, 2, 34, 34),
                        text('Open event details'),
                        'open-in-new',
                        { type: 'inspect' },
                        !!entry.eventId,
                        { iconOnly: true }
                    ),
                    button(
                        'debugCopyEvent',
                        rect(eventWidth - 80, 2, 34, 34),
                        text('Copy event'),
                        'content-copy',
                        { type: 'copy' },
                        !!entry.eventId,
                        { iconOnly: true }
                    ),
                    button(
                        'debugCopyCommand',
                        rect(eventWidth - 42, 2, 34, 34),
                        text('Copy runtime command'),
                        'terminal',
                        { type: 'copyCommand' },
                        !!entry.command,
                        { iconOnly: true }
                    ),
                    detail(entry, eventWidth, detailHeight, language)
                ]
            }
        )
    );
    return {
        nodes: [
            node('Scroll', 'debugBody', rect(0, 0, width, height), {
                contentHeight,
                children: nodes
            })
        ]
    };
}
