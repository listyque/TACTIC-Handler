pragma ComponentBehavior: Bound
import QtQuick
import "." as Controls

Item {
    id: root

    required property var theme
    property var items: []
    property int maximumItems: 0
    signal completionRequested(string searchType)

    implicitWidth: content.implicitWidth
    implicitHeight: 24
    width: implicitWidth
    height: implicitHeight

    Row {
        id: content
        height: parent.height
        spacing: 4

        Repeater {
            model: root.maximumItems > 0
                ? (root.items || []).slice(0, root.maximumItems)
                : root.items || []

            delegate: Controls.StatusChip {
                id: completionChip
                required property int index
                required property var modelData
                readonly property string searchType:
                    String(modelData.searchType || "")
                readonly property string description:
                    [modelData.name || qsTr("Completion"), modelData.label || ""]
                        .filter(Boolean).join(": ")

                objectName: "completionChip_" + index
                height: root.height
                theme: root.theme
                text: description
                iconName: "donut-small"
                accentColor: String(modelData.color || root.theme.action)
                interactive: searchType.length > 0
                activeFocusOnTab: interactive
                Accessible.role: Accessible.Button
                Accessible.name: description
                Accessible.onPressAction: {
                    if (interactive)
                        clicked()
                }
                border.width: activeFocus ? 1 : 0
                border.color: root.theme.action
                Keys.enabled: interactive

                Keys.onPressed: event => {
                    if (event.key !== Qt.Key_Return
                            && event.key !== Qt.Key_Enter
                            && event.key !== Qt.Key_Space)
                        return
                    clicked()
                    event.accepted = true
                }
                onClicked: root.completionRequested(searchType)

                HoverHandler {
                    id: completionHover
                    enabled: completionChip.interactive
                    cursorShape: Qt.PointingHandCursor
                }
                Controls.ToolTip {
                    theme: root.theme
                    visible: completionHover.hovered
                        && !root.theme.suppressToolTips
                    text: completionChip.description + "\n"
                        + qsTr(
                            "Approved objects are shown first; all tracked objects are shown second."
                        ) + "\n"
                        + qsTr("Open tracked objects")
                }
            }
        }
    }
}
