import QtQuick
import QtQuick.Window
import "tactic_frame" as Frame
import "tactic_frame/features/support/connection/sign_in.ui.mjs" as UI

Window {
    id: root
    required property var ownerWindow
    required property var theme
    property bool blocksMainWindow: false
    property string login: ""
    property string password: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            login,
            password,
            busy: appController.authentication_busy,
            ready: true,
            server: appController.server_url || qsTr("Configure a server before signing in"),
            error: qsTr(appController.authentication_error),
            nativeTicket: true,
            cancelable: true,
            canHelp: true
        })
    readonly property var preferredScene: UI.describe(root.frameModel, root.width, 0, root.language)
    transientParent: ownerWindow
    modality: blocksMainWindow ? Qt.ApplicationModal : Qt.NonModal
    flags: Qt.Dialog | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint
    color: root.theme.workspace
    visible: appController.authentication_dialog_visible
    width: 440
    height: preferredScene && preferredScene.contentHeight ? preferredScene.contentHeight : 376
    minimumWidth: 400
    minimumHeight: 350
    title: qsTr("Sign in to TACTIC")
    function syncNativeFrame() {
        windowAppearanceController.apply(root, root.theme.dark, root.theme.topBar, root.theme.primaryText);
    }
    Component.onCompleted: syncNativeFrame()
    Connections {
        target: root.theme
        function onDarkChanged() {
            root.syncNativeFrame();
        }
        function onTopBarChanged() {
            root.syncNativeFrame();
        }
    }
    x: ownerWindow ? ownerWindow.x + (ownerWindow.width - width) / 2 : 100
    y: ownerWindow ? ownerWindow.y + (ownerWindow.height - height) / 2 : 100
    onVisibleChanged: Qt.callLater(function () {
        password = "";
        if (visible) {
            login = appController.login_name;
            requestActivate();
            frame.focusControl(login.length ? "signIn_password" : "signIn_login");
        }
    })
    onClosing: close => {
        close.accepted = false;
        appController.cancel_authentication();
    }
    function dispatch(action) {
        if (action.type === "login")
            login = action.value;
        else if (action.type === "password")
            password = action.value;
        else if (action.type === "submit" && UI.canSubmit(frameModel))
            appController.authenticate(login, password);
        else if (action.type === "help")
            windowModel.open_help("getting_started");
        else if (action.type === "cancel" && !appController.authentication_busy)
            appController.cancel_authentication();
    }
    Shortcut {
        sequences: [StandardKey.Cancel]
        enabled: root.visible && !appController.authentication_busy
        onActivated: appController.cancel_authentication()
    }
    Frame.FrameView {
        id: frame
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        onEvent: action => root.dispatch(action)
    }
}
