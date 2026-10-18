// Presentation and input rules only. Requests, drafts, receipts and writes stay with their owners.
import { metrics } from '../../core/foundation.mjs';
export function formatFileSize(bytes) {
    const value = Math.max(0, Number(bytes) || 0);
    if (!value) return '';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'],
        unit = Math.min(4, Math.floor(Math.log(value) / Math.log(1024))),
        scaled = value / 1024 ** unit;
    return (unit ? scaled.toFixed(1) : Math.round(scaled)) + ' ' + units[unit];
}

// MessageTimelineFrame.qml: one closed contour includes the curved group tail.
export function bubbleContour(width, height, corner, last, tail = 6) {
    const l = (last ? tail : 0) + 2,
        t = 2,
        r = l + width,
        b = t + height,
        radius = Math.min(corner, height / 2, width / 2);
    const arc = ` A ${radius} ${radius} 0 0 1 `;
    let path = `M ${l + radius} ${t} H ${r - radius}${arc}${r} ${t + radius} V ${b - radius}${arc}${r - radius} ${b} H ${l + radius}`;
    path += last
        ? ` C ${l} ${b} ${l - tail} ${b} ${l - tail} ${b - 2} C ${l - tail} ${b - 4} ${l} ${b - 4} ${l} ${b - radius}`
        : arc + `${l} ${b - radius}`;
    return path + ` V ${t + radius}${arc}${l + radius} ${t} Z`;
}

// MessageBodyText.qml's sticker rule; keep its ranges and cluster/count semantics.
export function emojiCount(value) {
    const points = Array.from(String(value || '').trim(), (char) =>
        char.codePointAt(0)
    );
    let count = 0,
        clusterOpen = false,
        afterJoiner = false,
        pendingRegional = false;
    const base = (point) =>
        (point >= 0x1f000 && point <= 0x1faff) ||
        (point >= 0x2600 && point <= 0x27bf) ||
        (point >= 0x2190 && point <= 0x21ff) ||
        (point >= 0x2300 && point <= 0x23ff) ||
        (point >= 0x25a0 && point <= 0x25ff) ||
        [
            0xa9, 0xae, 0x203c, 0x2049, 0x2122, 0x2139, 0x2b50, 0x2b55, 0x3030,
            0x303d, 0x3297, 0x3299
        ].includes(point);
    for (let index = 0; index < points.length; index++) {
        const point = points[index];
        if ([0x20, 0x09, 0x0a, 0x0d].includes(point)) {
            if (afterJoiner) return 0;
            clusterOpen = false;
            pendingRegional = false;
            continue;
        }
        if (
            (point >= 0x30 && point <= 0x39) ||
            point === 0x23 ||
            point === 0x2a
        ) {
            let next = index + 1;
            if (points[next] === 0xfe0f) next++;
            if (points[next] !== 0x20e3) return 0;
            count++;
            index = next;
            clusterOpen = true;
            continue;
        }
        if (point === 0x200d) {
            if (!clusterOpen) return 0;
            afterJoiner = true;
            continue;
        }
        if (
            point === 0xfe0e ||
            point === 0xfe0f ||
            point === 0x20e3 ||
            (point >= 0x1f3fb && point <= 0x1f3ff)
        ) {
            if (!clusterOpen) return 0;
            continue;
        }
        if (point >= 0x1f1e6 && point <= 0x1f1ff) {
            if (!pendingRegional) count++;
            pendingRegional = !pendingRegional;
            clusterOpen = true;
            afterJoiner = false;
            continue;
        }
        pendingRegional = false;
        if (!base(point)) return 0;
        if (!afterJoiner) count++;
        clusterOpen = true;
        afterJoiner = false;
        if (count > 3) return 0;
    }
    return !afterJoiner && count <= 3 ? count : 0;
}

export function composerKey(
    event,
    phone = false,
    mentioning = false,
    matches = false
) {
    if (event.composing || event.keyCode === 229) return 'pass';
    if (event.disabled || event.sending)
        return event.key === 'Enter' ? 'consume' : 'pass';
    if (event.key === 'Escape' && mentioning) return 'dismiss';
    if (
        mentioning &&
        matches &&
        !event.control &&
        !event.meta &&
        ['ArrowDown', 'ArrowUp', 'Enter'].includes(event.key)
    )
        return event.key === 'Enter'
            ? event.repeat
                ? 'consume'
                : 'mention'
            : event.key === 'ArrowDown'
              ? 'next'
              : 'previous';
    if (event.key !== 'Enter' || phone) return 'pass';
    if (event.repeat || event.disabled || event.sending) return 'consume';
    return event.control || event.meta ? 'newline' : 'send';
}
export function mentionQuery(text, cursor) {
    const found = String(text || '')
        .slice(0, cursor)
        .match(/(?:^|\s)@([A-Za-z0-9_.-]*)$/);
    return found ? found[1] : null;
}
export function insertion(text, start, end, value, replace = 0) {
    const at = Math.max(0, start - replace);
    return {
        text: text.slice(0, at) + value + text.slice(end),
        cursor: at + value.length
    };
}
export function bubbleGeometry(
    width,
    natural,
    contentHeight,
    model = {},
    style = 'md3'
) {
    const theme = metrics(style),
        small = width < 380,
        avatar = small ? 34 : 40,
        margin = small ? 8 : 12,
        padding = theme.communicationBubblePadding + (small ? 0 : 3),
        maximum = Math.max(
            0,
            Math.min(
                model.media ? width : 520,
                width * 0.7,
                width - avatar - theme.communicationAvatarSpacing - margin * 2
            )
        ),
        bubbleWidth = Math.min(
            maximum,
            model.media
                ? maximum
                : Math.max(small ? 104 : 116, natural + padding * 2)
        ),
        bubbleHeight = contentHeight + padding * 2,
        height = Math.max(model.last ? avatar : 0, bubbleHeight),
        avatarX = model.own ? width - avatar - margin : margin,
        x = model.own
            ? avatarX - theme.communicationAvatarSpacing - bubbleWidth
            : avatarX + avatar + theme.communicationAvatarSpacing;
    return {
        width: bubbleWidth,
        height: bubbleHeight,
        rowHeight: height,
        x,
        y: height - bubbleHeight,
        avatarX,
        avatarY: height - avatar,
        avatar,
        padding,
        gap: theme.communicationContentSpacing,
        corner: theme.communicationBubbleRadius,
        margin,
        maximum,
        tail: Math.min(
            theme.communicationGroupTailSize,
            theme.communicationAvatarSpacing - 2
        )
    };
}
export const bodyOrder = [
    'reply',
    'forward',
    'previews',
    'attachments',
    'text',
    'reactions'
];
export function popup(mode) {
    return {
        spacing: mode === 'history' || mode === 'pin-history' ? 10 : 12,
        height: {
            create: 536,
            members: 536,
            'view-members': 366,
            files: 406,
            history: 336,
            forward: 540,
            'pin-history': 336
        }[mode],
        anchored: !['create', 'members', 'rename'].includes(mode),
        width:
            {
                create: 436,
                members: 436,
                'view-members': 306,
                files: 356,
                rename: 366,
                history: 396,
                'pin-history': 396,
                forward: 460,
                search: 336
            }[mode] || 420
    };
}
