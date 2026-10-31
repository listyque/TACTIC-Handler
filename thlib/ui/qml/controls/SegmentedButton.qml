import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import "../tactic_frame/controls/forms/segmented.mjs" as Segments
import QtQuick.Controls.Basic as Basic
import "." as Controls

Item {
    id: root

    required property var theme
    property var model: []
    property string currentValue: ""
    property real segmentWidth: 84
    property real minimumSegmentWidth: 62
    property real contentPadding: 3
    property bool outlined: false
    property bool iconOnly: false
    property string segmentObjectNamePrefix: "segmentedButtonSegment_"
    signal activated(string value)

    readonly property int segmentCount: model && model.length ? model.length : 0

    implicitWidth: Math.max(minimumSegmentWidth * segmentCount + contentPadding * 2, segmentWidth * segmentCount + contentPadding * 2)
    implicitHeight: theme.controlHeight

    function choose(index) {
        const option = root.model[index];
        if (!root.enabled || !option || !Segments.selectable(option))
            return;
        if (String(option.value || "") !== root.currentValue || option.reselectable === true)
            root.activated(String(option.value || ""));
    }
    function move(key) {
        const index = Segments.target(root.model, root.currentValue, key);
        if (index < 0 || !root.enabled)
            return false;
        root.choose(index);
        segments.itemAt(index).forceActiveFocus(Qt.TabFocusReason);
        return true;
    }

    Rectangle {
        anchors.fill: parent
        radius: root.theme.buttonRadius
        color: root.outlined ? "transparent" : root.theme.surfaceContainerHigh
        border.width: root.outlined ? 0 : 1
        border.color: root.theme.outlineVariant
    }

    Row {
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: 0

        Repeater {
            id: segments
            model: root.model

            delegate: Basic.Button {
                id: segment

                required property var modelData
                required property int index
                objectName: root.segmentObjectNamePrefix + modelData.value
                readonly property bool selected: String(modelData.value || "") === root.currentValue

                width: Math.max(0, (root.width - root.contentPadding * 2) / Math.max(1, root.segmentCount))
                height: Math.max(0, root.height - root.contentPadding * 2)
                enabled: Segments.selectable(modelData)
                activeFocusOnTab: index === Segments.entry(root.model, root.currentValue)
                padding: 0
                focusPolicy: Qt.TabFocus
                Accessible.role: Accessible.RadioButton
                Accessible.checkable: true
                Accessible.checked: selected
                Accessible.name: qsTr(String(modelData.label || ""))
                Basic.ToolTip.visible: root.iconOnly && hovered
                Basic.ToolTip.text: Accessible.name

                contentItem: Item {
                    clip: true

                    Row {
                        id: segmentContent
                        anchors.centerIn: parent
                        anchors.alignWhenCentered: false
                        spacing: 6

                        Controls.MaterialIcon {
                            id: segmentIcon
                            visible: String(segment.modelData.icon || "").length > 0
                            name: String(segment.modelData.icon || "")
                            size: 15
                            color: !segment.enabled ? root.theme.disabledText : segment.selected ? (root.outlined ? root.theme.action : root.theme.selectedText) : root.theme.secondaryText
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Basic.Label {
                            visible: !root.iconOnly
                            text: segment.modelData.translate === false ? String(segment.modelData.label || "") : qsTr(String(segment.modelData.label || ""))
                            width: Math.min(implicitWidth, Math.max(0, segment.width - (segmentIcon.visible ? segmentIcon.width + parent.spacing : 0) - 16))
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            color: !segment.enabled ? root.theme.disabledText : segment.selected ? (root.outlined ? root.theme.action : root.theme.selectedText) : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.hintingPreference: Font.PreferVerticalHinting
                            font.pixelSize: Foundation.textStyles.body
                            font.weight: segment.selected ? Font.DemiBold : Font.Normal
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                background: Rectangle {
                    radius: Math.max(3, root.theme.itemRadius - 2)
                    border.width: root.outlined && segment.selected ? 1 : 0
                    border.color: root.theme.action
                    color: !segment.enabled ? "transparent" : root.outlined && segment.selected ? root.theme.surfaceContainerHigh : segment.down ? root.theme.surfaceContainerHighest : segment.selected ? root.theme.selected : segment.hovered ? root.theme.rowHover : "transparent"
                }

                HoverHandler {
                    cursorShape: Qt.PointingHandCursor
                }

                Keys.onPressed: event => {
                    if (event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier))
                        return;
                    const keys = {};
                    keys[Qt.Key_Left] = "ArrowLeft";
                    keys[Qt.Key_Right] = "ArrowRight";
                    keys[Qt.Key_Home] = "Home";
                    keys[Qt.Key_End] = "End";
                    if (keys[event.key])
                        event.accepted = root.move(keys[event.key]);
                }
                onClicked: root.choose(index)
            }
        }
    }
}
