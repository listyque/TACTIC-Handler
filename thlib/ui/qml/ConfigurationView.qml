import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/configuration/configuration.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property string windowId
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    property int pageRevision: 0
    readonly property var entries: {
        root.pageRevision;
        const result = UI.pages.slice();
        for (let index = 0; index < configPageModel.count(); index++) {
            const record = configPageModel.get(index);
            if (!result.some(page => (page.nativeId || page.id) === record.target))
                result.push({
                    id: record.target,
                    title: record.title,
                    icon: record.icon,
                    description: record.description || "",
                    help: record.helpTopic || "configuration"
                });
        }
        return result;
    }
    readonly property var current: entries.find(page => (page.nativeId || page.id) === configurationController.current_page) || entries[0]
    readonly property var frameModel: ({
            product: "TACTIC HANDLER",
            pages: entries,
            page: current.id,
            dirty: configurationController.dirty,
            currentDirty: configurationController.current_page_dirty,
            dirtyPages: configurationController.dirty_pages.map(id => {
                const entry = root.entries.find(page => (page.nativeId || page.id) === id);
                return entry ? entry.id : id;
            }),
            canReset: configurationController.can_reset_current_page,
            busy: false
        })
    function dispatch(action) {
        if (action.type === "page") {
            const entry = entries.find(page => page.id === action.value);
            configurationController.select_page(entry.nativeId || entry.id);
        } else if (action.type === "reset")
            configurationController.reset_current();
        else if (action.type === "apply")
            configurationController.apply_current();
        else if (action.type === "save")
            configurationController.save_all();
        else if (action.type === "close")
            configurationController.request_close();
        else if (action.type === "help")
            windowModel.open_help(current.help);
    }
    readonly property var scene: UI.describe(root.frameModel, width, height, root.language)
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        onEvent: action => root.dispatch(action)
    }
    ConfigurationPage {
        x: root.scene.pageBounds.x
        y: root.scene.pageBounds.y
        width: root.scene.pageBounds.width
        height: root.scene.pageBounds.height
        theme: root.theme
        pageId: configurationController.current_page
        managed: true
    }
    Connections {
        target: configPageModel
        function onDataChanged() {
            root.pageRevision++;
        }
        function onContentReplaced() {
            root.pageRevision++;
        }
    }
    Controls.Dialog {
        id: unsavedDialog
        theme: root.theme
        anchors.centerIn: parent
        width: Math.min(430, root.width - 32)
        modal: true
        title: qsTr("Unsaved changes")
        padding: 0
        headerPadding: 20
        closePolicy: Popup.NoAutoClose
        contentItem: Frame.FrameView {
            implicitHeight: 248
            theme: root.theme
            scene: UI.confirmation({
                kind: "close"
            }, width, height, root.language)
            onEvent: action => {
                unsavedDialog.close();
                if (action.type === "save")
                    configurationController.save_and_close();
                else if (action.type === "discard")
                    configurationController.discard_and_close();
            }
        }
    }

    Connections {
        target: configurationController

        function onConfirmationRequested() {
            unsavedDialog.open();
        }
    }
}
