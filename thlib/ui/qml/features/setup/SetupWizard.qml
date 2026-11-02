import QtQuick
import QtQuick.Window
import QtQuick.Controls as QtControls
import QtQuick.Layouts
import "../.." as App
import "../../controls" as Controls
import "../../tactic_frame/core/foundation.mjs" as Foundation

Window {
    id: root
    required property var controller
    readonly property var state: controller.state
    readonly property var headings: [qsTr("Server and sign-in"), qsTr("Project and repository"), qsTr("DCC plugins and shelf"), qsTr("Ready to apply"), qsTr("Setup complete")]
    width: 720
    height: 650
    minimumWidth: 500
    minimumHeight: 500
    visible: true
    title: qsTr("TACTIC Handler Setup")
    color: wizardTheme.workspace
    onClosing: event => event.accepted = !root.state.busy
    App.Theme {
        id: wizardTheme
        dark: true
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Foundation.spacing.section
        spacing: Foundation.spacing.section
        Controls.SectionLabel {
            Layout.fillWidth: true
            theme: wizardTheme
            text: (root.state.step + 1) + " / 5 · " + root.headings[root.state.step]
            font.pixelSize: 22
            wrapMode: Text.Wrap
        }
        QtControls.ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            QtControls.ScrollBar.vertical: Controls.ScrollBar {
                theme: wizardTheme
            }
            ColumnLayout {
                width: parent.width - Foundation.controls.scrollBar.extent - Foundation.spacing.compact
                spacing: Foundation.spacing.compact
                enabled: !root.state.busy
                ColumnLayout {
                    visible: root.state.step === 0
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.compact
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Configure a new or existing workstation. Changes are saved only after Apply.")
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("TACTIC server URL")
                    }
                    Controls.TextField {
                        objectName: "setupServer"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        text: root.state.server
                        placeholderText: "https://tactic.example.com"
                        onTextEdited: root.controller.edit("server", text)
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Login")
                    }
                    Controls.TextField {
                        objectName: "setupLogin"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        text: root.state.login
                        onTextEdited: root.controller.edit("login", text)
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Password")
                    }
                    Controls.TextField {
                        id: password
                        objectName: "setupPassword"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        echoMode: TextInput.Password
                        onAccepted: signIn.clicked()
                    }
                    Controls.Button {
                        id: signIn
                        objectName: "setupSignIn"
                        theme: wizardTheme
                        text: qsTr("Sign in")
                        enabled: !!root.state.server && !!root.state.login && !!password.text
                        onClicked: {
                            root.controller.sign_in(password.text);
                            password.clear();
                        }
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Your password is not saved. The client stores the server-issued session ticket.")
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    visible: root.state.step === 1
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.compact
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Project")
                    }
                    Controls.ComboBox {
                        objectName: "setupProject"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        model: root.state.projects
                        textRole: "title"
                        valueRole: "code"
                        translateDisplayText: false
                        currentIndex: root.state.projects.findIndex(row => row.code === root.state.project)
                        onActivated: root.controller.edit("project", currentValue)
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Repository alias")
                    }
                    Controls.ComboBox {
                        objectName: "setupRepositoryAlias"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        model: ["base", "client", "local", "sandbox"]
                        currentIndex: model.indexOf(root.state.repositoryAlias)
                        onActivated: root.controller.edit("repositoryAlias", currentText)
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Repository folder on this computer")
                    }
                    Controls.TextField {
                        objectName: "setupRepository"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        text: root.state.repository
                        onTextEdited: root.controller.edit("repository", text)
                    }
                    Controls.Button {
                        theme: wizardTheme
                        text: qsTr("Browse…")
                        onClicked: root.controller.browse()
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Use a local folder or a network share. This maps the selected repository on this PC; server paths stay unchanged.")
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    visible: root.state.step === 2
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.compact
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Enable DCC plugins in TACTIC Handler")
                    }
                    Repeater {
                        model: root.state.pluginCatalog
                        delegate: Controls.CheckBox {
                            required property var modelData
                            theme: wizardTheme
                            text: modelData.title
                            checked: root.state.plugins.indexOf(modelData.id) >= 0
                            onToggled: root.controller.toggle("plugins", modelData.id, checked)
                        }
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Maya versions to integrate")
                        visible: root.state.plugins.indexOf("maya") >= 0
                    }
                    Repeater {
                        model: root.state.plugins.indexOf("maya") >= 0 ? root.state.maya : []
                        delegate: Controls.CheckBox {
                            required property var modelData
                            objectName: "setupMaya_" + modelData.version
                            theme: wizardTheme
                            Layout.fillWidth: true
                            wrapText: true
                            text: "Maya " + modelData.version + " · " + modelData.profile + (modelData.pids.length ? " · " + qsTr("Close Maya first") : "")
                            enabled: modelData.supported && !modelData.pids.length
                            checked: root.state.mayaProfiles.indexOf(modelData.id) >= 0
                            onToggled: root.controller.toggle("mayaProfiles", modelData.id, checked)
                        }
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        visible: root.state.maya.length === 0
                        text: qsTr("No Maya profiles found. You can run Setup again after installing Maya.")
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Shelf for the signed-in user")
                    }
                    Controls.ComboBox {
                        objectName: "setupShelf"
                        theme: wizardTheme
                        Layout.fillWidth: true
                        model: [
                            {
                                id: "",
                                title: qsTr("Launcher only"),
                                buttons: []
                            }
                        ].concat(root.state.shelves)
                        textRole: "title"
                        valueRole: "id"
                        translateDisplayText: false
                        currentIndex: root.state.shelf ? root.state.shelves.findIndex(row => row.id === root.state.shelf) + 1 : 0
                        onActivated: root.controller.edit("shelf", currentValue)
                    }
                    Repeater {
                        model: (root.state.shelves.find(row => row.id === root.state.shelf) || {
                                buttons: []
                            }).buttons
                        delegate: Controls.SectionLabel {
                            required property var modelData
                            theme: wizardTheme
                            text: modelData.title
                            Layout.fillWidth: true
                        }
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Only buttons allowed by your groups are installed. Access is checked again when a script runs. Restart Maya after setup.")
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
                ColumnLayout {
                    visible: root.state.step === 3
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.compact
                    Controls.SelectableText {
                        theme: wizardTheme
                        Layout.fillWidth: true
                        text: root.state.server + "\n" + root.state.login + " · " + root.state.project + "\n" + root.state.repositoryAlias + ": " + root.state.repository + "\n" + root.state.plugins.join(", ")
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("Selected Maya profiles: %1").arg(root.state.mayaProfiles.length)
                    }
                    Controls.CheckBox {
                        objectName: "setupShortcuts"
                        theme: wizardTheme
                        text: qsTr("Create desktop shortcuts for TH and Setup")
                        checked: root.state.shortcuts
                        onToggled: root.controller.toggle("shortcuts", "", checked)
                    }
                    Controls.SectionLabel {
                        theme: wizardTheme
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        text: qsTr("Apply will save this workstation's connection and repository, configure selected plugins and install Maya's connector and shelf.")
                    }
                }
                Controls.SectionLabel {
                    visible: root.state.step === 4
                    theme: wizardTheme
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: qsTr("You can start TACTIC Handler now. Run Setup again to change the server, account, repository or integrations.")
                }
            }
        }
        Controls.SelectableText {
            objectName: "setupError"
            theme: wizardTheme
            Layout.fillWidth: true
            visible: !!text
            text: root.state.error
            Layout.maximumHeight: 110
        }
        Controls.SectionLabel {
            theme: wizardTheme
            text: qsTr("Working…")
            visible: root.state.busy
        }
        RowLayout {
            Layout.fillWidth: true
            Controls.Button {
                objectName: "setupBack"
                theme: wizardTheme
                text: qsTr("Back")
                visible: root.state.step > 0 && root.state.step < 4
                enabled: !root.state.busy
                onClicked: root.controller.back()
            }
            Item {
                Layout.fillWidth: true
            }
            Controls.Button {
                theme: wizardTheme
                text: root.state.step === 4 ? qsTr("Finish") : qsTr("Cancel")
                enabled: !root.state.busy
                onClicked: root.close()
            }
            Controls.Button {
                objectName: "setupNext"
                theme: wizardTheme
                text: root.state.step === 3 ? qsTr("Apply") : qsTr("Next")
                visible: root.state.step > 0 && root.state.step < 4
                enabled: !root.state.busy
                onClicked: root.controller.next()
            }
        }
    }
}
