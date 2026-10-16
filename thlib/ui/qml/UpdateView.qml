import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/support/connection/updates.ui.mjs" as UI
import "tactic_frame/controls/feedback/confirmation.ui.mjs" as Confirmation

Item {
    id: root
    required property var theme
    required property bool createMode
    property bool versionInitialized: false
    property string currentPage: "updates"
    property var draft: ({
            major: "0",
            minor: "0",
            build: "0",
            revision: "0",
            changes: "",
            misc: ""
        })
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            createMode,
            page: currentPage,
            draft,
            busy: updateController.busy,
            error: qsTr(updateController.error),
            stage: qsTr(updateController.stage),
            progress: updateController.progress,
            cancelable: updateController.cancelable,
            portable: updateController.portable,
            canInstall: updateController.canInstall,
            count: updateModel.count(),
            configured: !!updateController.sourceSearchKey
        })
    function syncVersion() {
        if (!createMode || versionInitialized || !updateController.currentVersion)
            return;
        const values = updateController.currentVersion.split(".");
        if (values.length === 4) {
            draft = ({
                    major: values[0],
                    minor: values[1],
                    build: values[2],
                    revision: values[3],
                    changes: updateController.currentChanges,
                    misc: ""
                });
            versionInitialized = true;
        }
    }
    function dispatch(action) {
        if (action.type === "refresh")
            updateController.load();
        else if (action.type === "page")
            currentPage = action.value;
        else if (action.type === "field") {
            const next = Object.assign({}, draft);
            next[action.key] = action.value;
            draft = next;
        } else if (action.type === "versionStep")
            draft = UI.stepVersion(draft, action.key, action.delta);
        else if (action.type === "cancel")
            updateController.cancel();
        else if (action.type === "select") {
            for (let index = 0; index < updateModel.count(); index++) {
                const record = updateModel.get(index);
                if (record.archive === action.archive && record.version === action.version) {
                    updateController.select(index);
                    break;
                }
            }
        } else if (action.type === "install" && updateController.canInstall)
            updateConfirmation.open();
        else if (action.type === "create" && !updateController.busy) {
            const values = UI.versionValues(draft);
            if (values)
                updateController.create_update(values[0], values[1], values[2], values[3], draft.changes, draft.misc);
        }
    }
    Component.onCompleted: syncVersion()
    onVisibleChanged: if (visible)
        updateController.load()
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        models: ({
                releases: updateModel
            })
        views: ({
                version: versionComponent,
                changelog: changelogComponent
            })
        describeRow: (list, record) => UI.row(record, list.width - 16)
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: versionComponent
        Label {
            objectName: "currentVersionLabel"
            text: qsTr("Current version  ") + (updateController.currentVersion || "—")
            color: root.theme.secondaryText
            font.pixelSize: 12
            font.family: root.theme.fontFamily
            elide: Text.ElideRight
            MouseArea {
                anchors.fill: parent
                onDoubleClicked: mouse => {
                    if (mouse.modifiers & Qt.ControlModifier)
                        updateController.open_generator();
                }
            }
        }
    }
    Component {
        id: changelogComponent
        Controls.DocumentPane {
            objectName: "updateChangelogScroll"
            theme: root.theme
            documentKey: "changelog"
            text: updateController.changelog
            presented: root.visible && root.currentPage === "changelog"
        }
    }
    Controls.Dialog {
        id: updateConfirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(440, root.width - 24)
        height: 340
        title: qsTr("Install selected version?")
        contentItem: Frame.FrameView {
            implicitHeight: 240
            theme: root.theme
            scene: Confirmation.describe({
                message: qsTr("TACTIC-Handler will close, install this version, then reopen. Your saved workspace and settings are preserved. The previous version remains available for rollback."),
                accept: "Install and restart",
                busy: updateController.busy
            }, width, height, root.language)
            onEvent: action => {
                updateConfirmation.close();
                if (action.type === "accept" && updateController.canInstall)
                    updateController.install_selected();
            }
        }
    }
    Connections {
        target: updateController
        function onStateChanged() {
            root.syncVersion();
        }
    }
}
