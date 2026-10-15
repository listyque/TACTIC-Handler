import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { filtered } from './help.state.mjs';
import { metrics as themeMetrics } from '../../../core/foundation.mjs';

export const metrics = {
    margin: 12,
    gap: 10,
    topicRow: 61,
    phoneWidth: 760,
    topicMin: 236,
    topicMax: 292,
    header: 72,
    phoneHeader: 104
};

export function topicRow(model, record, width, language) {
    const keys = {};
    for (const key of ['ArrowDown', 'ArrowUp', 'Home', 'End'])
        keys[key] = { type: 'topicKey', id: record.id, key };
    return {
        nodes: [
            node('Action', 'helpTopic_' + record.id, rect(0, 0, width, 58), {
                text: record.title,
                selected: model.selected === record.id,
                rail: true,
                normalColor: 'row',
                selectedColor: 'contentSelection',
                role: 'button',
                action: { type: 'select', id: record.id },
                keys,
                children: [
                    node('Icon', 'topicIcon', rect(11, 20, 17, 17), {
                        icon: record.icon || 'help',
                        color:
                            model.selected === record.id
                                ? 'action'
                                : 'secondaryText'
                    }),
                    label(
                        'topicTitle',
                        rect(37, 11, Math.max(0, width - 46), 21),
                        record.title,
                        {
                            weight: model.selected === record.id ? 600 : 400
                        }
                    ),
                    label(
                        'topicGroup',
                        rect(37, 33, Math.max(0, width - 46), 16),
                        translate(record.group, language),
                        { fontRole: 'caption', color: 'secondaryText' }
                    )
                ]
            })
        ]
    };
}

export function describe(model, data, width, height, language) {
    const compact = width < metrics.phoneWidth;
    const margin = compact ? 8 : metrics.margin;
    const innerWidth = Math.max(0, width - margin * 2);
    const innerHeight = Math.max(0, height - margin * 2);
    const topicsWidth = compact
        ? innerWidth
        : Math.min(metrics.topicMax, Math.max(metrics.topicMin, width * 0.29));
    const articleX = compact ? margin : margin + topicsWidth + metrics.gap;
    const articleWidth = Math.max(0, width - margin - articleX);
    const showTopics = !compact || model.topicsVisible;
    const current =
        data.articles.find((article) => article.id === model.selected) || {};
    const hasFile = !!(current.file || data.currentFile);
    const radius = themeMetrics(data.style || 'md3').surfaceRadius;
    const rows = filtered(data.articles, model.query);
    const header = compact ? metrics.phoneHeader : metrics.header;
    const text = (key) => translate(key, language);
    const actions = [
        [
            'helpReloadButton',
            'Reload help articles',
            'refresh',
            'reload',
            !data.busy
        ],
        [
            'helpOpenArticleFileButton',
            'Open article file',
            'folder-open',
            'openFile',
            hasFile
        ],
        ...(data.canDownload
            ? [
                  [
                      'helpDownloadButton',
                      'Download article',
                      'download',
                      'download',
                      hasFile
                  ]
              ]
            : [])
    ];
    const actionsWidth = actions.length * 36;
    const headerChildren = [
        node(
            'View',
            'helpLoading',
            rect(
                compact ? 12 : articleWidth - actionsWidth - 38,
                compact ? 66 : 22,
                24,
                24
            ),
            { view: 'busy', visible: !!data.busy }
        ),
        ...(compact
            ? [
                  button(
                      'helpShowTopics',
                      rect(8, 8, 32, 32),
                      text('Help topics'),
                      'menu',
                      { type: 'topics', value: true },
                      true,
                      { iconOnly: true }
                  )
              ]
            : [
                  node('Icon', 'helpArticleIcon', rect(14, 19, 24, 24), {
                      icon: current.icon || 'help',
                      color: 'action'
                  })
              ]),
        label(
            'helpArticleTitle',
            rect(
                compact ? 46 : 48,
                compact ? 8 : 12,
                Math.max(0, articleWidth - (compact ? 58 : 60 + actionsWidth)),
                26
            ),
            current.title || text('Help'),
            { fontRole: 'title', weight: 600, role: 'heading', level: 1 }
        ),
        label(
            'helpArticleGroup',
            rect(
                compact ? 46 : 48,
                compact ? 35 : 40,
                Math.max(0, articleWidth - 60),
                18
            ),
            text(current.group || 'Guide'),
            { fontRole: 'secondary', color: 'secondaryText' }
        )
    ];
    actions.forEach(([id, title, icon, type, enabled], index) =>
        headerChildren.push(
            button(
                id,
                rect(
                    Math.max(4, articleWidth - actionsWidth - 10) + index * 36,
                    compact ? 62 : 18,
                    32,
                    32
                ),
                text(title),
                icon,
                { type },
                enabled,
                Object.assign(
                    { iconOnly: true },
                    type === 'openFile' && data.fileLinks && current.file
                        ? { href: current.file, target: '_blank' }
                        : {}
                )
            )
        )
    );
    return {
        width,
        height,
        compact,
        topicRows: rows,
        nodes: [
            node('Box', 'helpBackground', rect(0, 0, width, height), {
                background: 'workspace'
            }),
            node(
                'Box',
                'helpTopicsPanel',
                rect(margin, margin, topicsWidth, innerHeight),
                {
                    visible: showTopics,
                    background: 'panel',
                    border: 'outlineVariant',
                    radius,
                    children: [
                        node('Icon', 'helpTopicsIcon', rect(10, 10, 20, 20), {
                            icon: 'help',
                            color: 'action'
                        }),
                        label(
                            'helpTopicsTitle',
                            rect(38, 9, topicsWidth - (compact ? 84 : 48), 24),
                            text('Help topics'),
                            { fontRole: 'bodyLarge', weight: 600 }
                        ),
                        ...(compact
                            ? [
                                  button(
                                      'helpHideTopics',
                                      rect(topicsWidth - 42, 5, 32, 32),
                                      text('Close help topics'),
                                      'close',
                                      { type: 'topics', value: false },
                                      true,
                                      { iconOnly: true }
                                  )
                              ]
                            : []),
                        node(
                            'Field',
                            'helpTopicSearch',
                            rect(10, 42, Math.max(0, topicsWidth - 20), 36),
                            {
                                text: model.query,
                                label: text('Search help'),
                                placeholder: text('Search help'),
                                action: { type: 'query' }
                            }
                        ),
                        node(
                            'List',
                            'helpTopicList',
                            rect(
                                10,
                                86,
                                Math.max(0, topicsWidth - 20),
                                Math.max(0, innerHeight - 96)
                            ),
                            {
                                source: 'helpTopics',
                                keyField: 'id',
                                fields: [],
                                rowHeight: metrics.topicRow,
                                rowGap: 3,
                                label: text('Help topics'),
                                scrollbarId: 'helpTopicsScrollbar'
                            }
                        ),
                        ...(!rows.length && !data.busy
                            ? [
                                  label(
                                      'helpNoTopics',
                                      rect(10, 90, topicsWidth - 20, 60),
                                      text('No help topics match your search'),
                                      { wrap: true, color: 'secondaryText' }
                                  )
                              ]
                            : [])
                    ]
                }
            ),
            node(
                'Box',
                'helpContentPanel',
                rect(articleX, margin, articleWidth, innerHeight),
                {
                    visible: !compact || !model.topicsVisible,
                    background: 'panel',
                    border: 'outlineVariant',
                    radius,
                    children: [
                        ...headerChildren,
                        node(
                            'Box',
                            'helpArticleDivider',
                            rect(4, header, Math.max(0, articleWidth - 8), 1),
                            { background: 'outlineVariant' }
                        ),
                        node(
                            'View',
                            'helpDocument',
                            rect(
                                4,
                                header + 1,
                                Math.max(0, articleWidth - 8),
                                Math.max(0, innerHeight - header - 5)
                            ),
                            { view: 'document' }
                        )
                    ]
                }
            )
        ]
    };
}
