import QtQuick

Md3Button {
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
