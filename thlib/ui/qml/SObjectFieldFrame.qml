import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/objects/fields.ui.mjs" as UI

Item {
    id: root
    objectName: "sobjectFieldFrame_" + fieldName
    required property var theme
    required property string title
    required property string fieldName
    required property string description
    required property string iconName
    required property string errorText
    required property bool requiredField
    required property bool readOnlyField
    default property alias editorData: editorHost.data
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var fieldModel: ({
            name: fieldName,
            title: title,
            description: description,
            icon: iconName,
            error: errorText,
            required: requiredField,
            readOnly: readOnlyField,
            minimumHeight: theme.controlHeight
        })
    readonly property var columns: UI.columns(fieldModel, width)
    readonly property var scene: UI.field(fieldModel, width, editorHost.childrenRect.height, language)
    readonly property bool compact: scene.compact
    implicitHeight: scene.height
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
    }
    Item {
        id: editorHost
        objectName: "sobjectFieldEditorHost_" + root.fieldName
        x: root.columns.inputX
        y: root.columns.inputY
        width: root.columns.inputWidth
        height: Math.max(root.theme.controlHeight, childrenRect.height)
    }
}
