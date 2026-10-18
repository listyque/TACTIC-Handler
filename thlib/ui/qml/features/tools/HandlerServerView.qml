import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tools/server.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string payload: "{}"
    property string commandName: ""
    property int timeoutSeconds: 30
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    readonly property var capabilities: {
        handlerServerController.state;
        return handlerCapabilityModel.records();
    }
    readonly property var bounds: UI.layout(width, height, handlerServerController.error)
    onCapabilitiesChanged: if (!capabilities.some(row => row.name === commandName))
        commandName = capabilities.length ? capabilities[0].name : ""
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        views: ({
                timeout: timeoutComponent
            })
        scene: UI.describe({
            state: handlerServerController.state,
            endpoint: handlerServerController.endpoint,
            error: handlerServerController.error,
            selectedClient: handlerServerController.selectedClient,
            demo: handlerServerController.demoRunning,
            capabilities: root.capabilities,
            command: root.commandName,
            payload: root.payload
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "start")
                handlerServerController.start_server();
            else if (action.type === "stop")
                stopDialog.open();
            else if (action.type === "help")
                windowModel.open_help("dcc_clients");
            else if (action.type === "demo")
                handlerServerController.demoRunning ? handlerServerController.stop_demo() : handlerServerController.start_demo();
            else if (action.type === "disconnect")
                handlerServerController.disconnect_selected();
            else if (action.type === "clear")
                handlerServerController.clear_results();
            else if (action.type === "command")
                root.commandName = action.value;
            else if (action.type === "payload")
                root.payload = action.value;
            else if (action.type === "send")
                handlerServerController.send_command(root.commandName, root.payload, root.timeoutSeconds);
        }
    }
    Component {
        id: timeoutComponent
        Controls.SpinBox {
            objectName: "handlerTimeoutInput"
            theme: root.theme
            from: 1
            to: 300
            value: root.timeoutSeconds
            Accessible.name: qsTr("Timeout (seconds)")
            onValueModified: root.timeoutSeconds = value
        }
    }
    ListView {
        id: clients
        objectName: "handlerClients"
        x: root.bounds.clients.x
        y: root.bounds.clients.y
        width: root.bounds.clients.width
        height: root.bounds.clients.height
        clip: true
        spacing: 4
        model: handlerClientModel
        ScrollBar.vertical: Controls.ScrollBar {
            id: clientBar
            theme: root.theme
            flickableTarget: clients
        }
        delegate: Frame.FrameView {
            id: client
            required property int index
            required property string clientId
            required property string applicationType
            required property int processId
            required property string capabilityText
            required property bool selected
            width: Math.max(0, clients.width - (clientBar.visible ? clientBar.reservedExtent : 0))
            height: 70
            theme: root.theme
            scene: UI.clientRow({
                index: index,
                clientId: clientId,
                applicationType: applicationType,
                processId: processId,
                capabilityText: capabilityText,
                selected: selected
            }, width, root.language)
            onEvent: action => handlerServerController.select_client(action.index)
        }
        Label {
            anchors.centerIn: parent
            width: parent.width - 12
            visible: clients.count === 0
            text: qsTr("No DCC clients connected")
            wrapMode: Text.WordWrap
            color: root.theme.secondaryText
        }
    }
    ListView {
        id: results
        objectName: "handlerResults"
        x: root.bounds.results.x
        y: root.bounds.results.y
        width: root.bounds.results.width
        height: root.bounds.results.height
        clip: true
        spacing: 4
        model: handlerResultModel
        onCountChanged: if (count > 0)
            positionViewAtEnd()
        ScrollBar.vertical: Controls.ScrollBar {
            id: resultBar
            theme: root.theme
            flickableTarget: results
        }
        delegate: Frame.FrameView {
            required property string timestamp
            required property string target
            required property string action
            required property string status
            required property string summary
            required property string detail
            readonly property var record: ({
                    timestamp: timestamp,
                    target: target,
                    action: action,
                    status: status,
                    summary: summary,
                    detail: detail
                })
            width: Math.max(0, results.width - (resultBar.visible ? resultBar.reservedExtent : 0))
            height: UI.resultHeight(record, width)
            theme: root.theme
            scene: UI.resultRow(record, width, root.language)
        }
    }
    Controls.Dialog {
        id: stopDialog
        theme: root.theme
        anchors.centerIn: parent
        width: 410
        title: qsTr("Stop Handler Server?")
        modal: false
        dim: false
        contentItem: Label {
            width: 362
            text: qsTr("Connected DCC clients and pending requests will be disconnected.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Stop")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: handlerServerController.stop_server()
    }
}
