import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/document.ui.mjs" as Document

Item {
    id: root
    required property var theme
    property int selected: 0
    Connections {
        target: tableServicesController
        function onDocumentChanged() {
            root.selected = 0;
        }
    }
    Loader {
        anchors.fill: parent
        anchors.margins: 12
        active: !!tableServicesController.document.layoutNodes
        sourceComponent: ServiceCell {
            theme: root.theme
            controller: appController
            nodeId: tableServicesController.document.nodeId || ""
            cell: tableServicesController.document
            services: tableServicesController
            administration: administrationController
        }
    }
    Loader {
        anchors.fill: parent
        anchors.margins: 12
        active: tableServicesController.document.kind === "dependencies"
        sourceComponent: DependenciesView {
            theme: root.theme
            owner: tableServicesController.dependencyViewer
            model: tableServicesController.document
            onCloseRequested: windowModel.close_window("table_document")
        }
    }
    Frame.FrameView {
        visible: !tableServicesController.document.layoutNodes && tableServicesController.document.kind !== "dependencies"
        anchors.fill: parent
        anchors.margins: 12
        theme: root.theme
        models: ({
                sourceEditor: tableServicesController.sourceEditor
            })
        scene: Document.describe(tableServicesController.document, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language, root.selected)
        onEvent: action => {
            if (action.type === "help")
                windowModel.open_help(action.topic);
            else if (action.type === "section")
                root.selected = Number(action.value) || 0;
            else if (action.type === "close")
                windowModel.close_window("table_document");
        }
    }
}
