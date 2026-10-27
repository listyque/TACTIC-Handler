import QtQuick
import QtQuick.Window
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/administration/layouts/layout.preview.mjs" as Composition

Frame.FrameView {
    id: root
    required property var layout
    required property var record
    required property var controller
    required property string nodeId
    property bool editing: false
    property bool readOnly: false
    property string selectedElement: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var composition: Composition.describe(layout, record, width, selectedElement, language, root.Window.window ? root.Window.window.width : width, "", "itemComposition", 0, editing || readOnly)
    signal elementSelected(string name)
    signal menuRequested(bool relations, var anchor)
    implicitHeight: composition.height
    scene: composition
    onEvent: (event, source) => {
        if (event.type === "select") {
            if (editing)
                elementSelected(event.name);
            return;
        }
        if (editing || readOnly || event.type !== "itemAction")
            return;
        if (event.href) {
            if (/^(https?:\/\/|\/(?!\/))/i.test(event.href) && !/[\u0000-\u0020\u007f\\]/.test(event.href))
                controller.open_rich_link(event.href);
            return;
        }
        if (event.urlOnly || !Composition.actionAvailable(event.action, record))
            return;
        if (event.action === "operate" || event.action === "relations") {
            menuRequested(event.action === "relations", source);
            return;
        }
        const command = {
            inspect: "sobject_info",
            upload: "save",
            create: "add_related",
            link: "link_related"
        }[event.action] || (event.action === "quickaction" ? event.command : event.action);
        controller.invoke_item_action(command, nodeId);
    }
}
