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
    width: 900
    height: 820
    minimumWidth: 500
    minimumHeight: 540
    visible: true
    title: qsTr("TH Setup Builder")
    color: rootTheme.workspace
    onClosing: event => event.accepted = !root.state.busy
    App.Theme {
        id: rootTheme
        dark: true
    }
    Component.onCompleted: {
        if (typeof windowAppearanceController !== "undefined")
            windowAppearanceController.apply(root, rootTheme.dark, rootTheme.workspace, rootTheme.primaryText);
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Foundation.spacing.major
        spacing: Foundation.spacing.section
        Controls.SectionLabel {
            theme: rootTheme
            Layout.fillWidth: true
            text: qsTr("Build your team's setup")
            font.pixelSize: Foundation.textStyles.headline
            color: rootTheme.primaryText
            wrapMode: Text.Wrap
        }
        Controls.SectionLabel {
            theme: rootTheme
            Layout.fillWidth: true
            text: qsTr("Choose the build and its defaults. Each employee signs in with their own account.")
            font.weight: Font.Normal
            wrapMode: Text.Wrap
        }
        QtControls.ScrollView {
            id: form
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 0
            clip: true
            contentWidth: availableWidth
            QtControls.ScrollBar.vertical: Controls.ScrollBar {
                theme: rootTheme
            }
            ColumnLayout {
                width: Math.max(0, form.availableWidth - Foundation.controls.scrollBar.extent - Foundation.spacing.compact)
                spacing: Foundation.spacing.compact
                enabled: !root.state.busy
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Base TH installer")
                }
                RowLayout {
                    Layout.fillWidth: true
                    Controls.TextField {
                        theme: rootTheme
                        Layout.fillWidth: true
                        readOnly: true
                        text: root.state.template
                        placeholderText: qsTr("Choose a base installer or a previously generated EXE")
                    }
                    Controls.Button {
                        theme: rootTheme
                        text: qsTr("Browse…")
                        onClicked: root.controller.browse_template()
                    }
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    visible: !!root.state.version
                    text: qsTr("TH version: %1").arg(root.state.version)
                    color: rootTheme.action
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Default server (optional)")
                }
                Controls.TextField {
                    objectName: "builderServer"
                    theme: rootTheme
                    Layout.fillWidth: true
                    text: root.state.defaults.server
                    placeholderText: qsTr("Empty means the employee enters the server address")
                    onTextEdited: root.controller.edit("server", text)
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Project code (optional)")
                }
                Controls.TextField {
                    objectName: "builderProject"
                    theme: rootTheme
                    Layout.fillWidth: true
                    text: root.state.defaults.project
                    onTextEdited: root.controller.edit("project", text)
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Installation folder (optional)")
                }
                Controls.TextField {
                    objectName: "builderInstallFolder"
                    theme: rootTheme
                    Layout.fillWidth: true
                    text: root.state.defaults.install_folder
                    placeholderText: "%LOCALAPPDATA%/TACTIC Handler"
                    onTextEdited: root.controller.edit("install_folder", text)
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Repository folder name inside the TH installation")
                }
                Controls.TextField {
                    objectName: "builderRepository"
                    theme: rootTheme
                    Layout.fillWidth: true
                    text: root.state.defaults.repository_name
                    onTextEdited: root.controller.edit("repository_name", text)
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Default shelf name (optional)")
                }
                Controls.TextField {
                    objectName: "builderShelf"
                    theme: rootTheme
                    Layout.fillWidth: true
                    text: root.state.defaults.shelf
                    onTextEdited: root.controller.edit("shelf", text)
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("DCC plugins")
                }
                Flow {
                    Layout.fillWidth: true
                    Layout.preferredHeight: childrenRect.height
                    spacing: Foundation.spacing.section
                    Repeater {
                        model: root.state.plugins
                        delegate: Controls.CheckBox {
                            required property var modelData
                            theme: rootTheme
                            text: modelData.title
                            checked: (root.state.defaults.plugins || []).indexOf(modelData.id) >= 0
                            onToggled: root.controller.toggle_plugin(modelData.id, checked)
                        }
                    }
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Language")
                }
                Controls.ComboBox {
                    objectName: "builderLanguage"
                    theme: rootTheme
                    Layout.fillWidth: true
                    model: [
                        { id: "", title: qsTr("System default") },
                        { id: "ru", title: "Русский" },
                        { id: "en", title: "English" }
                    ]
                    textRole: "title"
                    valueRole: "id"
                    translateDisplayText: false
                    currentIndex: Math.max(0, model.findIndex(row => row.id === (root.state.defaults.language || "")))
                    onActivated: root.controller.edit("language", currentValue)
                }
                Controls.CheckBox {
                    objectName: "builderDarkTheme"
                    theme: rootTheme
                    text: qsTr("Dark theme by default")
                    checked: root.state.defaults.dark_theme !== false
                    onToggled: root.controller.edit("dark_theme", checked)
                }
                Controls.CheckBox {
                    objectName: "builderCloseToTray"
                    theme: rootTheme
                    text: qsTr("Keep in system tray when closing the window")
                    checked: root.state.defaults.close_to_tray !== false
                    onToggled: root.controller.edit("close_to_tray", checked)
                }
                Controls.CheckBox {
                    objectName: "builderShortcuts"
                    theme: rootTheme
                    text: qsTr("Create a desktop shortcut by default")
                    checked: root.state.defaults.shortcuts
                    onToggled: root.controller.edit("shortcuts", checked)
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    font.weight: Font.Normal
                    text: qsTr("The installer contains public defaults only. Passwords and tickets are never included. Group access is checked after employee sign-in.")
                }
                Controls.SectionLabel {
                    theme: rootTheme
                    text: qsTr("Output installer")
                }
                RowLayout {
                    Layout.fillWidth: true
                    Controls.TextField {
                        theme: rootTheme
                        Layout.fillWidth: true
                        readOnly: true
                        text: root.state.output
                    }
                    Controls.Button {
                        theme: rootTheme
                        text: qsTr("Save as…")
                        onClicked: root.controller.browse_output()
                    }
                }
            }
        }
        Controls.SelectableText {
            objectName: "builderError"
            theme: rootTheme
            Layout.fillWidth: true
            visible: !!text
            text: root.state.error
            color: rootTheme.error
        }
        Controls.SelectableText {
            objectName: "builderResult"
            theme: rootTheme
            Layout.fillWidth: true
            visible: !!text
            text: root.state.result
            color: rootTheme.green
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: Foundation.spacing.compact
            Controls.BusyIndicator {
                uiTheme: rootTheme
                running: root.state.busy
                visible: running
            }
            Controls.SectionLabel {
                theme: rootTheme
                text: qsTr("Creating installer…")
                visible: root.state.busy
                Layout.fillWidth: true
            }
            Controls.Button {
                theme: rootTheme
                text: qsTr("Open output folder")
                visible: !!root.state.result
                onClicked: root.controller.open_output()
            }
            Item {
                Layout.fillWidth: true
            }
            Controls.Button {
                theme: rootTheme
                text: qsTr("Close")
                enabled: !root.state.busy
                onClicked: root.close()
            }
            Controls.FilledActionButton {
                objectName: "builderBuild"
                theme: rootTheme
                text: qsTr("Create EXE")
                iconName: "package-variant"
                enabled: !!root.state.version && !root.state.busy
                onClicked: root.controller.build()
            }
        }
    }
}
