import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/related.ui.mjs" as UI
import "../table" as Tables
import "../.." as Shell

Item {
    id: root
    required property var theme
    property var relatedController: relatedObjectsController
    readonly property var users: userModel
    readonly property string language: localizationController.current_language
    readonly property var toolbar: UI.toolbar(root.relatedController.model, width, root.language)
    Frame.FrameView {
        id: header
        width: parent.width
        height: root.toolbar.height
        theme: root.theme
        scene: root.toolbar
        onEvent: (action, value) => root.relatedController.activate(action, value)
    }
    Tables.NestedTableView {
        anchors {
            left: parent.left
            right: parent.right
            top: message.bottom
            bottom: parent.bottom
        }
        theme: root.theme
        visible: !!root.relatedController.scope
        controller: appController
        columnsController: columnsEditorController
        userModel: root.users
        services: tableServicesController
        administration: administrationController
        scope: root.relatedController.scope
        nestedTableFactory: nestedFactory
        onClosed: root.relatedController.close()
        onMenuRequested: (nodeId, anchor) => {
            rowMenu.nodeId = nodeId;
            rowMenu.actions = appController.item_menu_actions(nodeId);
            rowMenu.openBelow(anchor);
        }
    }
    Shell.ActionMenu {
        id: rowMenu
        objectName: "relatedObjectsRowMenu"
        property string nodeId: ""
        theme: root.theme
        frameComposition: true
        onTriggered: command => appController.invoke_item_action(command, nodeId)
    }
    Component {
        id: nestedFactory
        Tables.NestedTableView {
            theme: root.theme
            controller: appController
            columnsController: columnsEditorController
            userModel: root.users
            services: tableServicesController
            administration: administrationController
            nestedTableFactory: nestedFactory
            onClosed: scope.request_close()
        }
    }
    Frame.FrameView {
        id: message
        anchors {
            left: parent.left
            right: parent.right
            top: header.bottom
        }
        height: root.relatedController.model.error ? 56 : 0
        theme: root.theme
        visible: height > 0
        scene: UI.message(root.relatedController.model.error || "", width, root.language)
    }
}
