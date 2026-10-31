import QtQuick
import "tactic_frame/features/table/cells.ui.mjs" as Cells
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    required property string kind
    required property var cell
    property string alignment: "center"
    signal clicked

    readonly property var presentation: Cells.action(kind, root.language) || ({
            icon: "info",
            label: ""
        })

    Controls.CompactIconButton {
        objectName: root.kind === "checkin" ? "tableCellCheckin" : root.kind === "sobject_detail" ? "tableCellSObjectDetail" : "tableCellAction_" + root.kind
        anchors.verticalCenter: parent.verticalCenter
        x: Cells.contentX(parent.width, width, root.alignment, 6)
        theme: root.theme
        round: false
        iconName: root.presentation.icon
        iconColor: root.kind === "delete" ? root.theme.error : root.theme.action
        enabled: root.cell.available !== false
        toolTip: root.presentation.label
        onClicked: root.clicked()
    }
}
