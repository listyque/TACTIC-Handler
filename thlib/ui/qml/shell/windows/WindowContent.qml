import QtQuick

Item {
    id: root

    required property var theme
    required property string contentSource
    property var contentProperties: ({})
    property bool componentReady: false

    function loadContent() {
        if (!componentReady)
            return;
        const properties = {
            "theme": root.theme
        };
        const supplied = root.contentProperties || {};
        for (const name in supplied)
            properties[name] = supplied[name];
        const source = root.contentSource;
        const absolute = /^(?:[a-z][a-z0-9+.-]*:|\/)/i.test(source);
        const url = source ? Qt.resolvedUrl(absolute ? source : "../../" + source) : Qt.resolvedUrl("UnregisteredWindow.qml");
        contentLoader.setSource(url, properties);
    }

    Component.onCompleted: {
        componentReady = true;
        loadContent();
    }
    onContentSourceChanged: loadContent()
    onContentPropertiesChanged: loadContent()

    Loader {
        id: contentLoader
        anchors.fill: parent
    }
}
