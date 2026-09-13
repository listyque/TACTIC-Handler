import QtQuick
import "controls" as Controls

Controls.Button {
    id: root

    property bool sending: false
    property bool hasContent: false
    property real compactBreakpoint: 620

    text: sending ? qsTr("Sending") : qsTr("Send")
    icon.name: "send"
    compact: parent && parent.width < compactBreakpoint
    highlighted: true
    enabled: hasContent && !sending
}
