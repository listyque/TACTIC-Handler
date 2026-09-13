import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property var symbols: []
    readonly property int symbolCount: symbols ? symbols.length : 0
    signal navigateRequested(int line)

    function filteredSymbols() {
        const query = outlineFilter.text.trim().toLowerCase()
        if (!query)
            return symbols || []
        const result = []
        for (let index = 0; index < symbols.length; ++index) {
            const symbol = symbols[index]
            if (String(symbol.qualifiedName || symbol.name)
                    .toLowerCase().indexOf(query) >= 0)
                result.push(symbol)
        }
        return result
    }

    function focusFilter() {
        outlineFilter.forceActiveFocus()
        outlineFilter.selectAll()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 4

        Controls.TextField {
            id: outlineFilter
            objectName: "scriptEditorOutlineFilter"
            theme: root.theme
            Layout.fillWidth: true
            Layout.leftMargin: 3
            Layout.rightMargin: 3
            placeholderText: qsTr("Filter classes and methods")
            Keys.onReturnPressed: event => {
                const values = root.filteredSymbols()
                if (values.length)
                    root.navigateRequested(Number(values[0].line))
                event.accepted = true
            }
        }

        ListView {
            id: outlineList
            objectName: "scriptEditorOutlineList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.filteredSymbols()
            visible: count > 0
            clip: true
            spacing: 1
            boundsBehavior: Flickable.StopAtBounds
            currentIndex: count > 0 ? 0 : -1
            activeFocusOnTab: true
            Keys.onReturnPressed: event => {
                if (currentItem) {
                    root.navigateRequested(Number(currentItem.symbolLine))
                    event.accepted = true
                }
            }
            Keys.onEnterPressed: event => {
                if (currentItem) {
                    root.navigateRequested(Number(currentItem.symbolLine))
                    event.accepted = true
                }
            }
            delegate: Controls.PopupAction {
                id: symbolAction
                required property int index
                required property var modelData
                readonly property int symbolLine: Number(modelData.line || 1)
                width: outlineList.width
                height: 34
                leftPadding: 7 + Number(modelData.depth || 0) * 14
                rightPadding: 7
                hoverEnabled: true
                Accessible.name: String(modelData.qualifiedName || modelData.name)
                    + qsTr(", line ") + String(symbolLine)
                background: Rectangle {
                    radius: root.theme.itemRadius
                    color: symbolAction.down
                        || outlineList.currentIndex === symbolAction.index
                        ? root.theme.secondaryContainer
                        : symbolAction.hovered ? root.theme.rowHover : "transparent"
                }
                contentItem: RowLayout {
                    spacing: 6
                    Controls.MaterialIcon {
                        name: symbolAction.modelData.kind === "class"
                            ? "type" : "code"
                        size: 14
                        color: root.theme.action
                    }
                    Label {
                        Layout.fillWidth: true
                        text: symbolAction.modelData.name
                        color: root.theme.primaryText
                        font.family: "Consolas"
                        font.pointSize: Controls.Typography.body
                        elide: Text.ElideRight
                    }
                    Label {
                        text: String(symbolAction.symbolLine)
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                    }
                }
                onHoveredChanged: if (hovered)
                    outlineList.currentIndex = index
                onClicked: root.navigateRequested(symbolLine)
            }
            Controls.ScrollBar.vertical: Controls.ScrollBar {
                objectName: "scriptEditorOutlineScrollBar"
                theme: root.theme
                flickableTarget: outlineList
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 8
            visible: root.symbolCount === 0
            text: qsTr("No classes or methods")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
        }
    }
}
