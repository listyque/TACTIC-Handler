pragma ComponentBehavior: Bound
import QtQuick
import "../../../thlib/ui/qml/features/table" as Table

Item {
    id: root
    required property var theme
    required property var controller
    required property var columnsController
    required property var services
    required property var scope
    Component {
        id: factory
        Table.NestedTableView {
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            userModel: null
            administration: null
            services: root.services
            onClosed: root.services.close_nested(scope)
        }
    }
    Component.onCompleted: factory.createObject(root, {
        scope: scope,
        width: Qt.binding(() => root.width),
        height: Qt.binding(() => root.height)
    })
}
