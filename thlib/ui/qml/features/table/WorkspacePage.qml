import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/page.ui.mjs" as Page

Item {
    id: root
    required property var theme
    required property var services
    required property var controller
    required property var columnsController
    required property var users
    required property var administration
    readonly property var owner: services.workspaceLayout
    readonly property var document: owner.document
    readonly property var scene: Page.describe({
        title: document.title || "",
        busy: !!document.layoutBusy,
        error: document.layoutError || ""
    }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        onEvent: root.owner.refresh()
    }
    Loader {
        x: root.scene.bodyBounds.x
        y: root.scene.bodyBounds.y
        width: root.scene.bodyBounds.width
        height: root.scene.bodyBounds.height
        active: !root.document.layoutBusy && !root.document.layoutError && root.document.layoutNodes !== undefined
        sourceComponent: CustomLayoutView {
            theme: root.theme
            owner: root.owner
            services: root.services
            controller: root.controller
            columnsController: root.columnsController
            users: root.users
            administration: root.administration
        }
    }
}
