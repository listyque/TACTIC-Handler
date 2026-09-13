import QtQuick

Item {
    id: root
    required property var theme

    AdminSearchTypesView {
        anchors.fill: parent
        anchors.margins: 14
        theme: root.theme
        controller: administrationController.schemaTypeEditor
        projectCode: administrationController.project
        creationOnly: true
        onCreateWorkflowRequested: administrationController.create_type_workflow(controller)
        title: qsTr("New Search Type")
        description: qsTr("Create a table and add its node to the project schema. Your current connections and canvas edits will be kept.")
        confirmationMessage: qsTr("TACTIC will create the Search Type, its table and a schema node on the server. Other unsaved canvas changes remain in your draft; save the schema separately to apply them.")
    }
}
