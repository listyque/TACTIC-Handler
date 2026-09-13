import QtQuick

Item {
    id: root

    required property var theme
    property int depth: 0
    property real indentStep: 24
    property real baseX: 11
    property real elbowWidth: 13
    property real revealProgress: 1
    property real overlap: 3

    visible: depth > 0

    Repeater {
        model: root.depth

        delegate: Rectangle {
            required property int index

            x: Math.round(root.baseX + index * root.indentStep)
            y: -root.overlap
            width: 1
            height: root.height + root.overlap * 2
            color: root.theme.outlineVariant
            opacity: 0.34 * root.revealProgress
        }
    }

    Rectangle {
        x: Math.round(root.baseX + (root.depth - 1) * root.indentStep)
        y: Math.round(root.height / 2)
        width: root.elbowWidth * root.revealProgress
        height: 1
        color: root.theme.outlineVariant
        opacity: 0.48 * root.revealProgress
    }
}
