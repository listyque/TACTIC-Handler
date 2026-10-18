import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function rowHeight(record, query) {
    return (
        record.kind === 'section' ? record.description : query && record.excerpt
    )
        ? 49
        : 32;
}

export function row(record, selected, query, width, language) {
    const section = record.kind === 'section';
    const left = 2 + Math.max(0, record.depth || 0) * 18;
    const height = rowHeight(record, query);
    const detail = section ? record.description : query ? record.excerpt : '';
    const draft = record.localDraft
        ? 'Local draft'
        : record.draft
          ? 'Draft'
          : '';
    const draftWidth = draft ? 78 : 0;
    const nodes = [];
    nodes.push(
        node(
            'Icon',
            'knowledgeNavigationIcon-' + record.identity,
            rect(left + 28, 7, 17, 17),
            {
                icon: section
                    ? record.expanded
                        ? 'folder-open'
                        : 'folder'
                    : 'file',
                color: section ? 'tertiary' : 'action'
            }
        )
    );
    nodes.push(
        label(
            'knowledgeNavigationTitle-' + record.identity,
            rect(left + 49, 3, Math.max(0, width - left - 55 - draftWidth), 24),
            record.title || '',
            { weight: section ? 600 : 400 }
        )
    );
    if (detail)
        nodes.push(
            label(
                (section
                    ? 'knowledgeSectionDescription-'
                    : 'knowledgeArticleExcerpt-') + record.identity,
                rect(left + 49, 27, Math.max(0, width - left - 55), 18),
                detail,
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    if (draft)
        nodes.push(
            label(
                'knowledgeNavigationDraft-' + record.identity,
                rect(Math.max(0, width - draftWidth), 5, draftWidth, 20),
                translate(draft, language),
                { fontRole: 'caption', color: 'tertiary', weight: 600 }
            )
        );
    return {
        nodes: [
            node(
                'Action',
                'knowledgePageLink-' + record.identity,
                rect(0, 0, width, height),
                {
                    text: record.title || '',
                    selected: !!selected,
                    normalColor: 'transparent',
                    selectedColor: 'surfaceContainerHigh',
                    radius: 8,
                    action: { type: 'select', id: record.identity },
                    children: nodes
                }
            )
        ].concat(
            section && record.hasChildren
                ? [
                      button(
                          'knowledgeSectionDisclosure-' + record.identity,
                          rect(left, 4, 24, 24),
                          translate(
                              record.expanded
                                  ? 'Collapse section'
                                  : 'Expand section',
                              language
                          ),
                          record.expanded ? 'chevron-down' : 'chevron-right',
                          { type: 'disclose', id: record.identity },
                          true,
                          { iconOnly: true }
                      )
                  ]
                : []
        )
    };
}

export function outline(entries, width, height, title, language) {
    return {
        nodes: [
            node('Box', 'knowledgeOutlineSurface', rect(0, 0, width, height), {
                background: 'surfaceContainerLow',
                radius: 12,
                border: 'outlineVariant'
            }),
            node('Icon', 'knowledgeOutlineIcon', rect(8, 12, 15, 15), {
                icon: 'list-ul',
                color: 'action'
            }),
            label(
                'knowledgeTableOfContentsTitle',
                rect(29, 8, Math.max(0, width - 37), 24),
                title || translate('On this page', language),
                { weight: 600 }
            ),
            node(
                'List',
                'knowledgeTableOfContents',
                rect(8, 38, Math.max(0, width - 16), Math.max(0, height - 46)),
                {
                    source: 'headings',
                    keyField: 'frameKey',
                    rowHeight: 30,
                    rowGap: 1
                }
            )
        ]
    };
}

export function outlineEntries(entries) {
    return (entries || []).map((record, index) =>
        Object.assign({}, record, {
            frameKey: String(
                record.id || record.identity || record.position || index
            )
        })
    );
}

export function heading(record, index, width) {
    const left = 7 + Math.max(0, (record.level || 1) - 1) * 11;
    return {
        nodes: [
            node(
                'Action',
                'knowledgeTocEntry-' + index,
                rect(0, 0, width, 29),
                {
                    text: record.title || '',
                    action: { type: 'heading', index },
                    normalColor: 'transparent',
                    children: [
                        label(
                            'knowledgeHeadingTitle',
                            rect(left, 0, Math.max(0, width - left - 6), 29),
                            record.title || '',
                            {
                                fontRole: 'caption',
                                color: 'secondaryText',
                                weight: record.level === 1 ? 600 : 400
                            }
                        )
                    ]
                }
            )
        ]
    };
}
