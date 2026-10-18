import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/support/collaboration/initialization.ui.mjs" as UI

Frame.FrameView {
    id: root
    property bool canInitialize: false
    property bool busy: false
    property string error: ""
    property string featureTitle: ""
    property string featureMessage: ""
    property string featureIcon: "database"
    property string projectCode: ""
    onProjectCodeChanged: confirmation.close()
    property int epoch: 0
    readonly property string language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
    readonly property var presentation: ({
            canInitialize: root.canInitialize,
            busy: root.busy,
            error: root.error,
            title: root.featureTitle,
            message: root.featureMessage,
            icon: root.featureIcon,
            project: root.projectCode,
            epoch: root.epoch
        })
    signal initializeRequested
    scene: UI.state(presentation, width, height, language)
    onEvent: action => confirmation.open()
    Controls.Dialog {
        id: confirmation
        objectName: "collaborationInitializationConfirmation"
        anchors.centerIn: parent
        width: UI.dialogSize(root.width, root.height).width
        height: UI.dialogSize(root.width, root.height).height
        theme: root.theme
        modal: true
        title: qsTr("Initialize server features?")
        standardButtons: Dialog.NoButton
        focus: true
        onOpened: {
            root.epoch++;
            Qt.callLater(() => content.focusControl("collaborationInitializationCancel"));
        }
        onAccepted: root.initializeRequested()
        contentItem: Frame.FrameView {
            id: content
            theme: root.theme
            scene: UI.confirmation(root.presentation, width, height, root.language)
            onEvent: action => action.type === "initialize" ? confirmation.accept() : confirmation.reject()
        }
    }
}
