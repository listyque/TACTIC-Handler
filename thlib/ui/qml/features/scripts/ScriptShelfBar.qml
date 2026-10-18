import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/bar.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    readonly property var bounds: UI.layout(width, height, controller.canExportDccShelf)
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            mode: root.controller.activeMode,
            count: root.controller.model.count(),
            busy: root.controller.busy,
            running: root.controller.executionBusy,
            error: root.controller.error,
            dcc: root.controller.canExportDccShelf,
            exportBusy: root.controller.dccShelfBusy
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "mode")
                root.controller.set_active_mode(action.value);
            else if (action.type === "edit")
                root.controller.open_editor();
            else if (action.type === "export") {
                dccShelfName.text = root.controller.dccShelfName;
                exportDccShelfDialog.open();
            }
        }
    }
    ListView {
        id: shelfButtons
        objectName: "scriptShelfButtons"
        x: root.bounds.buttons.x
        y: root.bounds.buttons.y
        width: root.bounds.buttons.width
        height: root.bounds.buttons.height - (shelfScrollBar.visible ? shelfScrollBar.reservedExtent : 0)
        orientation: ListView.Horizontal
        model: root.controller.model
        spacing: 4
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        WheelHandler {
            target: null
            blocking: true
            enabled: shelfButtons.contentWidth > shelfButtons.width
            onWheel: event => {
                const pixel = Math.abs(event.pixelDelta.x) > Math.abs(event.pixelDelta.y) ? event.pixelDelta.x : event.pixelDelta.y;
                const angle = Math.abs(event.angleDelta.x) > Math.abs(event.angleDelta.y) ? event.angleDelta.x : event.angleDelta.y;
                shelfButtons.contentX = Math.max(shelfButtons.originX, Math.min(shelfButtons.originX + shelfButtons.contentWidth - shelfButtons.width, shelfButtons.contentX - (pixel || angle / 2)));
                event.accepted = true;
            }
        }
        delegate: Item {
            id: buttonDelegate
            required property string buttonId
            required property string title
            required property string description
            required property string iconName
            required property string script
            required property bool available
            required property bool running
            width: 40
            height: shelfButtons.height
            Frame.FrameView {
                anchors.centerIn: parent
                width: parent.width
                height: UI.actionHeight(root.controller.model.count(), shelfButtons.width)
                theme: root.theme
                scene: UI.action({
                    buttonId: buttonDelegate.buttonId,
                    title: buttonDelegate.title,
                    description: buttonDelegate.description,
                    iconName: buttonDelegate.iconName,
                    script: buttonDelegate.script,
                    available: buttonDelegate.available,
                    running: buttonDelegate.running
                }, root.controller.executionBusy, root.language, height)
                onEvent: action => root.controller.run(action.buttonId)
            }
        }
        ScrollBar.horizontal: Controls.ScrollBar {
            id: shelfScrollBar
            objectName: "scriptShelfScrollBar"
            theme: root.theme
            flickableTarget: shelfButtons
        }
    }
    Controls.Dialog {
        id: exportDccShelfDialog
        objectName: "exportDccShelfDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(390, parent.width - 24)
        theme: root.theme
        modal: true
        title: qsTr("Create or update DCC shelf")
        onOpened: {
            dccShelfName.forceActiveFocus();
            dccShelfName.selectAll();
        }
        onAccepted: root.controller.export_dcc_shelf(dccShelfName.text)

        contentItem: ColumnLayout {
            spacing: 8

            Controls.TextField {
                id: dccShelfName
                objectName: "dccShelfNameField"
                Layout.fillWidth: true
                theme: root.theme
                maximumLength: 64
                placeholderText: qsTr("DCC shelf name")
                Keys.onReturnPressed: {
                    if (text.trim().length > 0)
                        exportDccShelfDialog.accept();
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("A shelf with this name will be updated in the selected DCC.")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }
        }

        footer: DialogButtonBox {
            background: Item {}

            Controls.Button {
                objectName: "confirmExportDccShelfButton"
                theme: root.theme
                text: qsTr("Create or update")
                highlighted: true
                enabled: dccShelfName.text.trim().length > 0
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }

            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}
