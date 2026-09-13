import QtQuick
import "controls" as Controls

TextEdit {
    id: root

    required property var theme
    property string sourceHtml: ""
    property string rawText: ""
    readonly property int emojiOnlyCount: emojiCount(rawText)
    readonly property bool stickerMode: emojiOnlyCount > 0

    function isEmojiBase(codePoint) {
        return (codePoint >= 0x1F000 && codePoint <= 0x1FAFF)
            || (codePoint >= 0x2600 && codePoint <= 0x27BF)
            || (codePoint >= 0x2190 && codePoint <= 0x21FF)
            || (codePoint >= 0x2300 && codePoint <= 0x23FF)
            || (codePoint >= 0x25A0 && codePoint <= 0x25FF)
            || codePoint === 0x00A9 || codePoint === 0x00AE
            || codePoint === 0x203C || codePoint === 0x2049
            || codePoint === 0x2122 || codePoint === 0x2139
            || codePoint === 0x2B50 || codePoint === 0x2B55
            || codePoint === 0x3030 || codePoint === 0x303D
            || codePoint === 0x3297 || codePoint === 0x3299
    }

    function emojiCount(value) {
        const source = String(value || "").trim()
        if (!source.length)
            return 0

        const codePoints = []
        for (let offset = 0; offset < source.length; ++offset) {
            const first = source.charCodeAt(offset)
            if (first >= 0xD800 && first <= 0xDBFF
                    && offset + 1 < source.length) {
                const second = source.charCodeAt(offset + 1)
                if (second >= 0xDC00 && second <= 0xDFFF) {
                    codePoints.push(
                        0x10000 + ((first - 0xD800) << 10)
                        + second - 0xDC00)
                    ++offset
                    continue
                }
            }
            codePoints.push(first)
        }

        let count = 0
        let clusterOpen = false
        let afterJoiner = false
        let pendingRegional = false
        for (let index = 0; index < codePoints.length; ++index) {
            const codePoint = codePoints[index]
            if (codePoint === 0x20 || codePoint === 0x09
                    || codePoint === 0x0A || codePoint === 0x0D) {
                if (afterJoiner)
                    return 0
                clusterOpen = false
                pendingRegional = false
                continue
            }
            if ((codePoint >= 0x30 && codePoint <= 0x39)
                    || codePoint === 0x23 || codePoint === 0x2A) {
                let next = index + 1
                if (codePoints[next] === 0xFE0F)
                    ++next
                if (codePoints[next] !== 0x20E3)
                    return 0
                ++count
                index = next
                clusterOpen = true
                continue
            }
            if (codePoint === 0x200D) {
                if (!clusterOpen)
                    return 0
                afterJoiner = true
                continue
            }
            if (codePoint === 0xFE0E || codePoint === 0xFE0F
                    || codePoint === 0x20E3
                    || (codePoint >= 0x1F3FB && codePoint <= 0x1F3FF)) {
                if (!clusterOpen)
                    return 0
                continue
            }
            if (codePoint >= 0x1F1E6 && codePoint <= 0x1F1FF) {
                if (!pendingRegional)
                    ++count
                pendingRegional = !pendingRegional
                clusterOpen = true
                afterJoiner = false
                continue
            }
            pendingRegional = false
            if (!isEmojiBase(codePoint))
                return 0
            if (!afterJoiner)
                ++count
            clusterOpen = true
            afterJoiner = false
            if (count > 3)
                return 0
        }
        return !afterJoiner && count <= 3 ? count : 0
    }

    text: sourceHtml.replace(
        /<a /g, "<a style=\"color:" + theme.action + ";\" "
    )
    textFormat: TextEdit.RichText
    color: theme.primaryText
    font.family: stickerMode ? theme.emojiFontFamily : theme.fontFamily
    font.pointSize: stickerMode
        ? (emojiOnlyCount === 1 ? 42 : emojiOnlyCount === 2 ? 36 : 31.5)
        : Controls.Typography.body
    wrapMode: TextEdit.Wrap
    topPadding: stickerMode ? 5 : 0
    bottomPadding: stickerMode ? 5 : 0
    readOnly: true
    selectByMouse: true
    activeFocusOnTab: true
}
