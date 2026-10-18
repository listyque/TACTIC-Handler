import QtQuick
import "controls" as Controls

Controls.Button {
    id: root
    objectName: "messageComposerSendButton"

    property bool sending: false
    property bool hasContent: false
    property real compactBreakpoint: 620

    text: sending ? qsTr("Sending") : qsTr("Send")
    icon.name: "send"
    compact: parent && parent.width < compactBreakpoint
    highlighted: true
    enabled: hasContent && !sending
}
