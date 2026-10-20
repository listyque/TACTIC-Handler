import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { link } from './cells.ui.mjs';

export function describe(
    cell,
    width,
    height,
    language,
    editable = true,
    server = ''
) {
    const children = [];
    let top = 0;
    for (const [index, item] of (cell.layoutNodes || []).entries()) {
        const id = 'customLayout_' + index,
            inner = Math.max(0, width - 24);
        const text = item.translate
            ? translate(item.text, language)
            : item.text;
        if (item.kind === 'text') {
            const extent = Math.max(
                28,
                Math.ceil(
                    String(text).length / Math.max(1, Math.floor(inner / 8))
                ) * 22
            );
            children.push(
                label(id, rect(0, top, inner, extent), text, { wrap: true })
            );
            top += extent + 6;
        } else if (item.kind === 'preview') {
            children.push(
                node('Preview', id, rect(0, top, 64, 64), {
                    source: link(item.value?.image, server) || '',
                    initials: String(text)
                        .split(/\s+/)
                        .map((part) => part[0])
                        .slice(0, 2)
                        .join(''),
                    round: false,
                    action: {
                        type: 'service',
                        name: item.javascript ? 'script' : 'sobject_detail',
                        javascript: item.javascript || '',
                        targetSearchKey: cell.targetSearchKey
                    },
                    enabled: !item.javascript || editable
                })
            );
            top += 70;
        } else {
            children.push(
                button(
                    id,
                    rect(0, top, inner, 36),
                    text,
                    item.kind === 'link' ? 'open-in-new' : 'edit',
                    {
                        type: 'service',
                        name: item.kind === 'link' ? 'layout-link' : 'script',
                        href: item.href,
                        javascript: item.javascript
                    },
                    item.kind === 'link' || editable,
                    { outlined: true }
                )
            );
            top += 42;
        }
    }
    return {
        nodes: [
            node('Scroll', 'customLayoutScroll', rect(0, 0, width, height), {
                contentHeight: top,
                scrollbarId: 'customLayoutScrollBar',
                children
            })
        ]
    };
}
