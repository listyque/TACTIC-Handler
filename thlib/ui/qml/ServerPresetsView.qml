import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool loadingValues: true
    property bool hasProxyPassword: false
    property string loadedPresetName: ""

    function formValues() {
        return {
            "serverUrl": serverAddress.text,
            "siteEnabled": siteEnabled.checked,
            "siteName": siteName.text,
            "proxyEnabled": proxyEnabled.checked,
            "proxyLogin": proxyLogin.text,
            "proxyServer": proxyServer.text,
            "proxyPassword": proxyPassword.text
        }
    }

    function loadSelected() {
        loadingValues = true
        loadedPresetName = serverPresetsController.selected_name
        const values = serverPresetsController.selected_values
        serverAddress.text = values.serverUrl || ""
        storedUser.text = values.storedUser || qsTr("No account saved")
        storedTicket.text = values.hasTicket
            ? qsTr("Ticket stored") : qsTr("No ticket")
        storedTicket.iconName = values.hasTicket ? "check-circle" : "key"
        storedTicket.accentColor = values.hasTicket
            ? root.theme.green : root.theme.secondaryText
        siteEnabled.checked = Boolean(values.siteEnabled)
        siteName.text = values.siteName || ""
        proxyEnabled.checked = Boolean(values.proxyEnabled)
        proxyLogin.text = values.proxyLogin || ""
        proxyServer.text = values.proxyServer || ""
        proxyPassword.clear()
        hasProxyPassword = Boolean(values.hasProxyPassword)
        loadingValues = false
    }

    function pushValues() {
        if (!loadingValues && serverPresetsController.selected_name.length)
            serverPresetsController.update_selected(formValues())
    }

    Component.onCompleted: {
        if (serverPresetsController.selected_name.length > 0)
            root.loadSelected()
        else
            serverPresetsController.begin_session()
    }

    Connections {
        target: serverPresetsController

        function onStateChanged() {
            if (root.loadedPresetName
                    !== serverPresetsController.selected_name)
                root.loadSelected()
        }

        function onSessionStarted() {
            root.loadSelected()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: qsTr("Connection presets")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Choose a preset on the left and edit its connection and routing settings.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.WordWrap
                }
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "help"
                toolTip: qsTr("Server configuration help")
                onClicked: windowModel.open_help("server_configuration")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 220
                Layout.minimumWidth: 190
                Layout.fillHeight: true
                radius: 14
                color: root.theme.surfaceContainerLow

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Label {
                        text: qsTr("Presets")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        Controls.TextField {
                            id: presetName
                            theme: root.theme
                            Layout.fillWidth: true
                            Layout.preferredHeight: 38
                            placeholderText: qsTr("Preset name")
                            onAccepted: {
                                if (serverPresetsController.add(text))
                                    text = ""
                            }
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "add"
                            toolTip: qsTr("Add preset")
                            onClicked: {
                                if (serverPresetsController.add(presetName.text))
                                    presetName.text = ""
                            }
                        }
                    }
                    ListView {
                        id: presetList
                        objectName: "serverPresetsList"
                        readonly property real scrollBarGutter: 14
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: serverPresetsModel
                        clip: true
                        spacing: 3

                        delegate: Item {
                            id: presetRow
                            objectName: "serverPresetRow"
                            required property int index
                            required property string name
                            required property bool isProtected
                            required property bool isActive
                            required property bool selected
                            width: Math.max(
                                0,
                                presetList.width - presetList.scrollBarGutter
                            )
                            height: 44

                            Controls.ItemSurface {
                                anchors.fill: parent
                                theme: root.theme
                                selected: presetRow.selected
                                hovered: rowHover.hovered
                                pressed: rowTap.pressed
                                accent: root.theme.action
                                cornerRadius: 11
                                separatorVisible: false
                            }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 6
                                spacing: 7
                                Controls.MaterialIcon {
                                    name: presetRow.isProtected
                                        ? "lock" : "dns"
                                    size: 15
                                    color: presetRow.selected
                                        ? root.theme.action
                                        : root.theme.secondaryText
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: presetRow.name
                                    color: root.theme.primaryText
                                    font.pointSize: Controls.Typography.body
                                    elide: Text.ElideRight
                                }
                                Controls.StatusChip {
                                    objectName: presetRow.isActive
                                        ? "activeServerPresetChip" : ""
                                    visible: presetRow.isActive
                                    theme: root.theme
                                    text: qsTr("Active preset")
                                    iconName: "check-circle"
                                    accentColor: root.theme.green
                                }
                                Controls.CompactIconButton {
                                    theme: root.theme
                                    iconName: "delete"
                                    toolTip: qsTr("Delete preset")
                                    enabled: !presetRow.isProtected
                                        && !presetRow.isActive
                                    visible: enabled && (rowHover.hovered
                                        || presetRow.selected)
                                    onClicked:
                                        serverPresetsController.remove(
                                            presetRow.index
                                        )
                                }
                            }
                            HoverHandler { id: rowHover }
                            Controls.ActivationHandler {
                                id: rowTap
                                onActivated:
                                    serverPresetsController.select(
                                        presetRow.index
                                    )
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            theme: root.theme
                            flickableTarget: presetList
                        }
                    }
                }
            }

            Rectangle {
                objectName: "serverPresetDetailsPane"
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 14
                color: root.theme.surfaceContainerLow

                ScrollView {
                    id: detailsScroll
                    anchors.fill: parent
                    anchors.margins: 10
                    contentWidth: availableWidth
                    contentHeight: detailsContent.implicitHeight
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: detailsScroll
                    }

                    ColumnLayout {
                        id: detailsContent
                        width: detailsScroll.availableWidth
                        spacing: 10

                        ConfigurationSection {
                            Layout.fillWidth: true
                            theme: root.theme
                            title: serverPresetsController.selected_name
                                || qsTr("Preset details")
                            description: qsTr("Server endpoint and stored authentication state.")
                            iconName: "dns"

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 8

                                Label {
                                    text: qsTr("Server address")
                                    color: root.theme.secondaryText
                                    font.pointSize: Controls.Typography.body
                                }
                                Controls.TextField {
                                    id: serverAddress
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    enabled: serverPresetsController
                                        .selected_name.length > 0
                                    placeholderText: qsTr("http://server")
                                    onTextEdited: root.pushValues()
                                }

                                Label {
                                    text: qsTr("Stored account")
                                    color: root.theme.secondaryText
                                    font.pointSize: Controls.Typography.body
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        id: storedUser
                                        Layout.fillWidth: true
                                        color: root.theme.primaryText
                                        font.pointSize: Controls.Typography.bodyLarge
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Controls.StatusChip {
                                        id: storedTicket
                                        theme: root.theme
                                    }
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("Sign-in is changed only through Generate ticket; the preset editor never asks for a TACTIC password.")
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.caption
                                wrapMode: Text.WordWrap
                            }
                        }

                        ConfigurationSection {
                            Layout.fillWidth: true
                            theme: root.theme
                            title: qsTr("Routing")
                            description: qsTr("Optional portal site and proxy for this preset.")
                            iconName: "hub"

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 8

                                Controls.CheckBox {
                                    id: siteEnabled
                                    theme: root.theme
                                    text: qsTr("Use portal site")
                                    enabled: serverPresetsController
                                        .selected_name.length > 0
                                    onToggled: root.pushValues()
                                }
                                Controls.TextField {
                                    id: siteName
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    enabled: siteEnabled.checked
                                    placeholderText: qsTr("Site name")
                                    onTextEdited: root.pushValues()
                                }

                                Controls.CheckBox {
                                    id: proxyEnabled
                                    theme: root.theme
                                    text: qsTr("Use proxy")
                                    enabled: serverPresetsController
                                        .selected_name.length > 0
                                    onToggled: root.pushValues()
                                }
                                Controls.TextField {
                                    id: proxyServer
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    enabled: proxyEnabled.checked
                                    placeholderText: qsTr("Proxy server")
                                    onTextEdited: root.pushValues()
                                }

                                Label {
                                    text: qsTr("Proxy login")
                                    color: root.theme.secondaryText
                                    font.pointSize: Controls.Typography.body
                                }
                                Controls.TextField {
                                    id: proxyLogin
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    enabled: proxyEnabled.checked
                                    placeholderText: qsTr("Optional")
                                    onTextEdited: root.pushValues()
                                }

                                Label {
                                    text: qsTr("Proxy password")
                                    color: root.theme.secondaryText
                                    font.pointSize: Controls.Typography.body
                                }
                                Controls.TextField {
                                    id: proxyPassword
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    enabled: proxyEnabled.checked
                                    echoMode: TextInput.Password
                                    placeholderText: root.hasProxyPassword
                                        ? qsTr("Stored password — enter to replace")
                                        : qsTr("Proxy password")
                                    onTextEdited: root.pushValues()
                                }
                            }
                        }
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: serverPresetsController.error.length > 0
            text: qsTr(serverPresetsController.error)
            color: root.theme.red
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.fillWidth: true
            Controls.Button {
                theme: root.theme
                text: qsTr("Help")
                flat: true
                icon.name: "help"
                onClicked: windowModel.open_help("server_configuration")
            }
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: {
                    serverPresetsController.cancel()
                    windowModel.close_window("server_presets")
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Save")
                icon.name: "save"
                highlighted: true
                onClicked: {
                    root.pushValues()
                    if (serverPresetsController.save()) {
                        configurationController.begin_session()
                        windowModel.close_window("server_presets")
                    }
                }
            }
        }
    }
}
