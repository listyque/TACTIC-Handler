import "../../tactic_frame/core/foundation.mjs" as Foundation
import "../../tactic_frame/controls/forms/search.mjs" as SearchText
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".." as Controls

Controls.Popup {
    id: root
    required property var rows
    property string namePrefix: "searchSuggestion"
    property string errorText: ""
    property string highlightQuery: ""
    property bool openInNewTab: false
    property alias currentIndex: list.currentIndex
    readonly property int count: list.count
    readonly property bool hovered: hover.hovered
    signal acceptedSuggestion(int index, var record)
    signal openSuggestion(int index, var record)
    signal highlighted(int index)

    objectName: namePrefix + "sPopup"
    padding: Foundation.controls.search.popupPadding
    modal: false
    focus: false
    settledClosePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onClosed: currentIndex = -1

    function recordAt(index) {
        const item = list.itemAtIndex(index) as SuggestionRow;
        return item ? item.suggestion : null;
    }
    function choose(index, newTab) {
        const record = recordAt(index);
        if (!record)
            return false;
        close();
        if (newTab)
            openSuggestion(index, record);
        else
            acceptedSuggestion(index, record);
        return true;
    }
    function move(direction) {
        if (!count)
            return;
        currentIndex = direction > 0 ? Math.min(count - 1, currentIndex + 1) : currentIndex <= 0 ? count - 1 : currentIndex - 1;
        list.positionViewAtIndex(currentIndex, ListView.Contain);
        highlighted(currentIndex);
    }

    contentItem: Item {
        Label {
            anchors.fill: parent
            anchors.margins: 8
            visible: root.errorText.length > 0
            text: root.errorText
            wrapMode: Text.Wrap
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 13
        }
        ListView {
            id: list
            objectName: root.namePrefix + "List"
            anchors.fill: parent
            visible: !root.errorText.length
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: root.rows
            currentIndex: -1
            delegate: SuggestionRow {}
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
        }
    }
    component SuggestionRow: Controls.PopupAction {
        id: row
        required property int index
        required property var model
        readonly property var record: model.modelData === undefined ? model : model.modelData
        readonly property var suggestion: ({
                title: String(record.title || ""),
                description: String(record.description || ""),
                keyword: String(record.keyword || ""),
                code: String(record.code || ""),
                id: record.id
            })
        objectName: root.namePrefix + "Row_" + index
        width: list.width
        height: Foundation.controls.search.rowHeight
        hoverEnabled: true
        leftPadding: 8
        rightPadding: 10
        Accessible.name: suggestion.title
        background: Rectangle {
            color: row.index === list.currentIndex ? root.theme.selected : row.down ? root.theme.surfaceContainerHighest : row.hovered ? root.theme.rowHover : row.index % 2 ? root.theme.panelRaised : root.theme.row
        }
        contentItem: RowLayout {
            spacing: 9
            Controls.MaterialIcon {
                name: "search"
                size: 17
                color: root.theme.secondaryText
            }
            Label {
                Layout.preferredWidth: Math.min(190, Math.max(90, implicitWidth))
                Layout.minimumWidth: 0
                text: SearchText.highlight(row.suggestion.title, root.highlightQuery, root.theme.action)
                textFormat: Text.StyledText
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: SearchText.highlight(row.suggestion.description ? "– " + row.suggestion.description : "", root.highlightQuery, root.theme.action)
                textFormat: Text.StyledText
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                elide: Text.ElideRight
            }
            Label {
                visible: row.suggestion.keyword.length > 0
                text: "#" + row.suggestion.keyword
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Controls.CompactIconButton {
                visible: root.openInNewTab
                theme: root.theme
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                iconName: "MDI_OPEN_IN_NEW"
                iconSize: 15
                toolTip: qsTr("Open result in new tab")
                enabled: row.suggestion.code.length > 0 || row.suggestion.id !== undefined
                onClicked: root.choose(row.index, true)
            }
        }
        onHoveredChanged: if (hovered) {
            list.currentIndex = index;
            root.highlighted(index);
        }
        onClicked: root.choose(index, false)
        TapHandler {
            enabled: root.openInNewTab
            acceptedButtons: Qt.MiddleButton
            gesturePolicy: TapHandler.DragThreshold
            onTapped: root.choose(row.index, true)
        }
    }
    HoverHandler {
        id: hover
    }
}
