import QtQuick
import "." as Controls

Controls.TextField {
    id: root

    property bool clearOnEscape: true
    property string searchIconObjectName: "searchFieldIcon"
    signal searchEdited(string query)
    signal cleared()

    leftPadding: 38
    rightPadding: 38
    placeholderText: qsTr("Search")
    Accessible.name: placeholderText
    onTextEdited: root.searchEdited(text)

    function clearSearch() {
        if (!enabled || readOnly || text.length === 0)
            return
        clear()
        searchEdited("")
        cleared()
        forceActiveFocus()
    }

    Keys.onEscapePressed: event => {
        event.accepted = root.clearOnEscape && !root.readOnly && root.text.length > 0
        if (event.accepted)
            root.clearSearch()
    }

    Controls.MaterialIcon {
        objectName: root.searchIconObjectName
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        name: "search"
        size: 18
        color: root.activeFocus ? root.theme.action : root.theme.secondaryText
    }

    Controls.CompactIconButton {
        objectName: "searchFieldClear"
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        width: 30
        height: 30
        theme: root.theme
        iconName: "close"
        toolTip: qsTr("Clear search")
        visible: root.text.length > 0
        enabled: root.enabled && !root.readOnly
        onClicked: root.clearSearch()
    }
}
