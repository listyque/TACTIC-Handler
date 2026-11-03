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
    readonly property var pageTitles: [qsTr("Connect to your server"), qsTr("Choose your repository"), qsTr("Connect your tools"), qsTr("Review your workspace"), qsTr("Your workspace is ready")]
    readonly property var descriptions: [qsTr("Sign in with your own account to load the projects and tools available to you."), qsTr("Choose a project and the folder where this computer will keep its working files."), qsTr("Choose your DCC integrations and a shelf. Your groups determine which tools are available."), qsTr("Check the details below. Your settings will be saved when you apply them."), qsTr("Your connection, files and tools are configured. You can start working.")]
    readonly property real formWidth: 680
    readonly property bool compactLayout: width < formWidth + Foundation.spacing.major * 2
    width: 960
    height: 760
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
    Component.onCompleted: {
        if (typeof windowAppearanceController !== "undefined")
            windowAppearanceController.apply(root, wizardTheme.dark, wizardTheme.workspace, wizardTheme.primaryText);
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.compactLayout ? Foundation.spacing.section : Foundation.spacing.major
        spacing: Foundation.spacing.major
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(parent.width, root.formWidth)
                spacing: Foundation.spacing.section
                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: heroText.implicitHeight + Foundation.spacing.section
                    Controls.SectionLabel {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        theme: wizardTheme
                        text: "0" + (root.state.step + 1)
                        font.pixelSize: Foundation.textStyles.headline * 3
                        font.weight: Font.Light
                        color: wizardTheme.action
                        opacity: 0.12
                        Accessible.ignored: true
                    }
                    ColumnLayout {
                        id: heroText
                        width: parent.width
                        spacing: Foundation.spacing.compact
                        Controls.SectionLabel {
                            Layout.fillWidth: true
                            theme: wizardTheme
                            text: root.pageTitles[root.state.step]
                            color: wizardTheme.primaryText
                            font.pixelSize: root.compactLayout ? Foundation.textStyles.hero : Foundation.textStyles.headline
                            font.letterSpacing: 0
                            wrapMode: Text.Wrap
                        }
                        Controls.SectionLabel {
                            Layout.fillWidth: true
                            theme: wizardTheme
                            text: root.descriptions[root.state.step]
                            font.pixelSize: Foundation.textStyles.bodyLarge
                            font.weight: Font.Normal
                            font.letterSpacing: 0
                            wrapMode: Text.Wrap
                        }
                    }
                }
                Controls.EditorPanel {
                    objectName: "setupContentPanel"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 0
                    theme: wizardTheme
                    padding: 0
                    color: "transparent"
                    border.width: 0
                    QtControls.ScrollView {
                        id: formScroll
                        objectName: "setupFormScroll"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 0
                        clip: true
                        contentWidth: availableWidth
                        QtControls.ScrollBar.vertical: Controls.ScrollBar {
                            objectName: "setupFormScrollBar"
                            theme: wizardTheme
                        }
                        ColumnLayout {
                            width: Math.max(0, formScroll.availableWidth - Foundation.controls.scrollBar.extent - Foundation.spacing.compact)
                            spacing: Foundation.spacing.compact
                            enabled: !root.state.busy
                            ColumnLayout {
                                visible: root.state.step === 0
                                Layout.fillWidth: true
                                spacing: Foundation.spacing.compact
                                Controls.SectionLabel {
                                    theme: wizardTheme
                                    text: qsTr("TACTIC server URL")
                                }
                                Controls.TextField {
                                    objectName: "setupServer"
                                    theme: wizardTheme
                                    Layout.fillWidth: true
                                    text: root.state.server
                                    placeholderText: qsTr("Enter your server address")
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
                                Controls.FilledActionButton {
                                    id: signIn
                                    iconName: "login"
                                    Layout.fillWidth: true
                                    objectName: "setupSignIn"
                                    theme: wizardTheme
                                    text: qsTr("Sign in")
                                    enabled: !!root.state.server && !!root.state.login && !!password.text
                                    onClicked: {
                                        root.controller.sign_in(password.text);
                                    }
                                }
                                Controls.SectionLabel {
                                    theme: wizardTheme
                                    text: qsTr("Your password stays in this window only. It is never saved to disk.")
                                    font.weight: Font.Normal
                                    font.pixelSize: Foundation.textStyles.secondary
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
                                Flow {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: childrenRect.height
                                    spacing: Foundation.spacing.section
                                    Repeater {
                                        model: (root.state.shelves.find(row => row.id === root.state.shelf) || {
                                                buttons: []
                                            }).buttons
                                        delegate: Row {
                                            required property var modelData
                                            spacing: Foundation.spacing.compact
                                            height: wizardTheme.controlHeight
                                            Controls.MaterialIcon {
                                                anchors.verticalCenter: parent.verticalCenter
                                                name: modelData.icon === "box" ? "package-variant" : modelData.icon || "play-arrow"
                                                size: Foundation.textStyles.display
                                                color: wizardTheme.action
                                            }
                                            Controls.SectionLabel {
                                                anchors.verticalCenter: parent.verticalCenter
                                                theme: wizardTheme
                                                text: modelData.title
                                                color: wizardTheme.primaryText
                                                font.weight: Font.Normal
                                            }
                                        }
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
                                Repeater {
                                    model: [
                                        {
                                            icon: "server",
                                            label: qsTr("TACTIC server URL"),
                                            value: root.state.server
                                        },
                                        {
                                            icon: "user",
                                            label: qsTr("Login"),
                                            value: root.state.login
                                        },
                                        {
                                            icon: "folder",
                                            label: qsTr("Project"),
                                            value: (root.state.projects.find(row => row.code === root.state.project) || {
                                                    title: root.state.project
                                                }).title
                                        },
                                        {
                                            icon: "database",
                                            label: qsTr("Repository folder"),
                                            value: root.state.repository
                                        },
                                        {
                                            icon: "hub",
                                            label: qsTr("DCC plugins"),
                                            value: root.state.pluginCatalog.filter(row => root.state.plugins.indexOf(row.id) >= 0).map(row => row.title).join(", ") || qsTr("None")
                                        },
                                        {
                                            icon: "link",
                                            label: qsTr("Maya versions to integrate"),
                                            value: root.state.maya.filter(row => root.state.mayaProfiles.indexOf(row.id) >= 0).map(row => row.version).join(", ") || qsTr("None")
                                        },
                                        {
                                            icon: "layers",
                                            label: qsTr("Shelf for the signed-in user"),
                                            value: (root.state.shelves.find(row => row.id === root.state.shelf) || {
                                                    title: qsTr("Launcher only")
                                                }).title
                                        }
                                    ]
                                    delegate: RowLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        spacing: Foundation.spacing.section
                                        Controls.MaterialIcon {
                                            name: modelData.icon
                                            size: Foundation.textStyles.statistic
                                            color: wizardTheme.action
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: Foundation.spacing.tight
                                            Controls.SectionLabel {
                                                theme: wizardTheme
                                                text: modelData.label
                                                font.pixelSize: Foundation.textStyles.secondary
                                                font.weight: Font.Normal
                                            }
                                            Controls.SelectableText {
                                                theme: wizardTheme
                                                Layout.fillWidth: true
                                                text: modelData.value
                                            }
                                        }
                                    }
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
                            ColumnLayout {
                                visible: root.state.step === 4
                                Layout.fillWidth: true
                                spacing: Foundation.spacing.major
                                Rectangle {
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.preferredWidth: 88
                                    Layout.preferredHeight: 88
                                    radius: width / 2
                                    color: wizardTheme.blend(wizardTheme.surfaceContainerLow, wizardTheme.green, 0.12)
                                    Controls.MaterialIcon {
                                        anchors.centerIn: parent
                                        name: "check-circle"
                                        size: 48
                                        color: wizardTheme.green
                                    }
                                }
                                Controls.SectionLabel {
                                    theme: wizardTheme
                                    Layout.fillWidth: true
                                    text: qsTr("Ready to go")
                                    font.pixelSize: Foundation.textStyles.hero
                                    color: wizardTheme.primaryText
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Controls.SectionLabel {
                                    theme: wizardTheme
                                    Layout.fillWidth: true
                                    wrapMode: Text.Wrap
                                    font.weight: Font.Normal
                                    horizontalAlignment: Text.AlignHCenter
                                    text: qsTr("You can start TACTIC Handler now. Run Setup again to change the server, account, repository or integrations.")
                                }
                            }
                        }
                    }
                }
                Controls.EditorPanel {
                    objectName: "setupErrorPanel"
                    Layout.fillWidth: true
                    theme: wizardTheme
                    visible: !!root.state.error
                    fillContentHeight: false
                    color: wizardTheme.blend(wizardTheme.surfaceContainerLow, wizardTheme.error, 0.08)
                    border.color: wizardTheme.error
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Foundation.spacing.content
                        Controls.MaterialIcon {
                            name: "alert"
                            size: Foundation.textStyles.statistic
                            color: wizardTheme.error
                        }
                        Controls.SelectableText {
                            objectName: "setupError"
                            theme: wizardTheme
                            color: wizardTheme.primaryText
                            Layout.fillWidth: true
                            Layout.maximumHeight: 110
                            text: root.state.error
                        }
                    }
                }
                RowLayout {
                    visible: root.state.busy
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.compact
                    Controls.BusyIndicator {
                        uiTheme: wizardTheme
                        running: root.state.busy
                    }
                    Controls.SectionLabel {
                        Layout.fillWidth: true
                        theme: wizardTheme
                        text: root.state.step === 0 ? qsTr("Signing in…") : root.state.step === 1 ? qsTr("Loading project…") : qsTr("Applying configuration…")
                        font.weight: Font.Normal
                        wrapMode: Text.Wrap
                    }
                }
                RowLayout {
                    objectName: "setupProgress"
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.content
                    Controls.SectionLabel {
                        theme: wizardTheme
                        text: qsTr("STEP %1 OF %2").arg(root.state.step + 1).arg(root.headings.length)
                        font.pixelSize: Foundation.textStyles.caption
                        color: wizardTheme.secondaryText
                    }
                    Repeater {
                        model: root.headings.length
                        delegate: Rectangle {
                            required property int index
                            Layout.fillWidth: true
                            height: Foundation.spacing.text
                            color: index <= root.state.step ? wizardTheme.action : wizardTheme.outlineVariant
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Foundation.spacing.compact
                    Controls.Button {
                        objectName: "setupBack"
                        theme: wizardTheme
                        text: qsTr("Back")
                        icon.name: "arrow-left"
                        visible: root.state.step > 0 && root.state.step < 4
                        enabled: !root.state.busy
                        onClicked: root.controller.back()
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Controls.Button {
                        theme: wizardTheme
                        text: qsTr("Cancel")
                        visible: root.state.step < 4
                        enabled: !root.state.busy
                        onClicked: root.close()
                    }
                    Controls.FilledActionButton {
                        objectName: "setupFinish"
                        theme: wizardTheme
                        text: qsTr("Finish")
                        iconName: "check"
                        visible: root.state.step === 4
                        onClicked: root.close()
                    }
                    Controls.FilledActionButton {
                        objectName: "setupNext"
                        theme: wizardTheme
                        iconName: root.state.step === 3 ? "check" : "arrow-right"
                        text: root.state.step === 3 ? qsTr("Apply") : qsTr("Next")
                        visible: root.state.step > 0 && root.state.step < 4
                        enabled: !root.state.busy
                        onClicked: root.controller.next()
                    }
                }
            }
        }
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            if (root.controller.state.step === 4)
                password.clear();
        }
    }
}
