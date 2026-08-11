import QtQuick

Item {
    id: root

    required property var theme
    required property string contentSource
    property var contentProperties: ({})

    function loadContent() {
        const properties = {"theme": root.theme}
        const supplied = root.contentProperties || {}
        for (const name in supplied)
            properties[name] = supplied[name]
        contentLoader.setSource(
            Qt.resolvedUrl(root.contentSource || "UnregisteredWindow.qml"),
            properties
        )
    }

    Component.onCompleted: loadContent()
    onContentSourceChanged: loadContent()
    onContentPropertiesChanged: loadContent()

    Loader {
        id: contentLoader
        anchors.fill: parent
    }
}
