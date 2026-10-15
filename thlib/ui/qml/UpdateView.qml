import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    required property bool createMode
    property bool versionInitialized: false
    property string currentPage: "updates"

    function syncVersion() {
        if (!createMode || versionInitialized
                || !updateController.currentVersion)
            return
        const parts = updateController.currentVersion.split(".")
        if (parts.length === 4) {
            major.value = Number(parts[0])
            minor.value = Number(parts[1])
            build.value = Number(parts[2])
            revision.value = Number(parts[3])
            changes.text = updateController.currentChanges
            versionInitialized = true
        }
    }

    Component.onCompleted: root.syncVersion()
    onVisibleChanged: if (visible) updateController.load()
    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            Rectangle {
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                radius: 14
                color: root.theme.secondaryContainer
                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: root.createMode ? "inventory_2" : "system_update"
                    size: 21
                    color: root.theme.action
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    text: root.createMode
                        ? qsTr("Create update") : qsTr("Application updates")
                    color: root.theme.primaryText
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    id: currentVersionLabel
                    objectName: "currentVersionLabel"
                    text: qsTr("Current version  ") + (updateController.currentVersion || "—")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton
                        onDoubleClicked: mouse => {
                            if (mouse.modifiers & Qt.ControlModifier)
                                updateController.open_generator()
                        }
                    }
                }
            }
            RefreshIconButton {
                theme: root.theme
                visible: root.createMode || root.currentPage === "updates"
                toolTip: qsTr("Check TACTIC update snapshots")
                enabled: !updateController.busy
                onClicked: updateController.load()
            }
        }

        Controls.SegmentedButton {
            objectName: "updatePages"
            visible: !root.createMode
            Layout.fillWidth: true
            theme: root.theme
            currentValue: root.currentPage
            segmentObjectNamePrefix: "updatePage_"
            model: [
                {"value": "updates", "label": qsTr("Available updates"),
                 "icon": "system_update"},
                {"value": "changelog", "label": qsTr("Changelog"),
                 "icon": "history"}
            ]
            onActivated: value => root.currentPage = value
        }

        GridLayout {
            visible: root.createMode
            Layout.fillWidth: true
            columns: 4
            rowSpacing: 5
            columnSpacing: 8
            Label { text: qsTr("Major"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Label { text: qsTr("Minor"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Label { text: qsTr("Build"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Label { text: qsTr("Revision"); color: root.theme.secondaryText; font.pointSize: Controls.Typography.label }
            Controls.SpinBox { id: major; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
            Controls.SpinBox { id: minor; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
            Controls.SpinBox { id: build; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
            Controls.SpinBox { id: revision; objectName: "updateRevision"; theme: root.theme; Layout.fillWidth: true; from: 0; to: 999 }
        }
        ScrollView {
            id: changesScroll
            objectName: "updateChangesScroll"
            visible: root.createMode
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            clip: true
            rightPadding: 14
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: "updateChangesScrollbar"
                theme: root.theme
                flickableTarget: changesScroll
            }
            Controls.TextArea {
                id: changes
                objectName: "updateChanges"
                theme: root.theme
                width: changesScroll.availableWidth
                placeholderText: qsTr("Changes")
            }
        }
        Controls.TextArea {
            id: misc
            theme: root.theme
            visible: root.createMode
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            placeholderText: qsTr("Additional information")
        }

        ListView {
            id: versions
            visible: root.createMode || root.currentPage === "updates"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: updateModel
            clip: true
            spacing: 5
            rightMargin: 14
            delegate: Rectangle {
                required property int index
                required property string version
                required property string date
                required property string changes
                required property string misc
                required property bool selected
                width: Math.max(0, versions.width - versions.rightMargin)
                height: 72
                radius: 13
                color: selected ? root.theme.secondaryContainer
                    : root.theme.surfaceContainerLow
                border.width: 1
                border.color: selected ? root.theme.action
                    : root.theme.outlineVariant
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    spacing: 2
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: version
                            color: root.theme.primaryText
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Item { Layout.fillWidth: true }
                        Label { text: date; color: root.theme.secondaryText; font.pointSize: Controls.Typography.caption }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: changes || misc || qsTr("No release notes")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: updateController.select(parent.index)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: versions
            }
            Label {
                anchors.centerIn: parent
                visible: versions.count === 0 && !updateController.busy
                text: updateController.sourceSearchKey.length
                    ? qsTr("No release ZIP snapshots found")
                    : qsTr("Configure an update sObject in Server configuration")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.body
            }
        }

        ScrollView {
            id: changelogScroll
            objectName: "updateChangelogScroll"
            visible: !root.createMode && root.currentPage === "changelog"
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            clip: true
            rightPadding: 14
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: "updateChangelogScrollbar"
                theme: root.theme
                flickableTarget: changelogScroll
            }
            Controls.SelectableText {
                objectName: "updateChangelogText"
                theme: root.theme
                width: changelogScroll.availableWidth
                height: contentHeight
                text: updateController.changelog
                textFormat: TextEdit.MarkdownText
                wrapMode: TextEdit.WordWrap
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            visible: (root.createMode || root.currentPage === "updates")
                && (updateController.busy || updateController.error.length > 0
                    || updateController.stage.length > 0)
            ProgressBar {
                Layout.fillWidth: true
                visible: updateController.busy
                from: 0
                to: 1
                value: updateController.progress
                indeterminate: updateController.busy
                    && updateController.progress <= 0
            }
            Label {
                Layout.fillWidth: true
                text: updateController.error || updateController.stage
                color: updateController.error ? root.theme.red
                    : root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }
        }
        Label {
            Layout.fillWidth: true
            visible: !root.createMode && root.currentPage === "updates"
                && !updateController.portable
            text: qsTr("Automatic installation requires a portable build")
            color: root.theme.secondaryText
            wrapMode: Text.WordWrap
        }
        RowLayout {
            Layout.fillWidth: true
            Controls.Button {
                theme: root.theme
                visible: updateController.cancelable
                text: qsTr("Cancel")
                icon.name: "stop"
                onClicked: updateController.cancel()
            }
            Item { Layout.fillWidth: true }
            Controls.Button {
                objectName: "createUpdateArchiveButton"
                theme: root.theme
                visible: root.createMode
                text: qsTr("Create archive")
                icon.name: "archive"
                highlighted: true
                enabled: !updateController.busy
                onClicked: updateController.create_update(
                    major.value, minor.value, build.value, revision.value,
                    changes.text, misc.text)
            }
            Controls.Button {
                theme: root.theme
                visible: !root.createMode && root.currentPage === "updates"
                text: qsTr("Install selected version")
                icon.name: "restart_alt"
                highlighted: true
                enabled: updateController.canInstall
                onClicked: updateConfirmation.open()
            }
        }
    }

    Controls.Dialog {
        id: updateConfirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(410, root.width - 24)
        title: qsTr("Install selected version?")
        contentItem: Label {
            width: Math.max(0, updateConfirmation.width - 48)
            text: qsTr("TACTIC-Handler will close, install this version, then reopen. Your saved workspace and settings are preserved. The previous version remains available for rollback.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Install and restart")
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: updateController.install_selected()
    }
    Connections {
        target: updateController
        function onStateChanged() { root.syncVersion() }
    }
}
