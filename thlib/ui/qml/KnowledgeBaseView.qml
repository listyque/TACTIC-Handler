import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    readonly property bool narrow: width < 720
    property bool navigationPage: true
    property bool navigationExpanded: true
    property bool dockResizeActive: false

    function consumeOpenArticleRequest() {
        if (!knowledgeController.openArticlePending)
            return;
        root.navigationPage = false;
        knowledgeController.acknowledge_article_open();
    }

    Component.onCompleted: root.consumeOpenArticleRequest()

    Controls.DockWorkspaceFooter {
        objectName: "knowledgeDockSurface"
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    Connections {
        target: knowledgeController
        function onStateChanged() {
            root.consumeOpenArticleRequest();
            if (root.narrow && (knowledgeController.identity.length > 0 || knowledgeController.creating))
                root.navigationPage = false;
        }
    }

    ColumnLayout {
        objectName: "knowledgeBaseLayout"
        anchors.fill: parent
        anchors.margins: 8
        spacing: 7

        RowLayout {
            Layout.fillWidth: true
            spacing: 7
            Controls.MaterialIcon {
                name: "book-open"
                size: 20
                color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: qsTr("Knowledge Base")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.title
                font.weight: Font.DemiBold
            }
            Controls.CompactIconButton {
                id: navigationToggle
                objectName: "knowledgeToggleNavigation"
                visible: knowledgeController.initialized && !root.narrow
                activeFocusOnTab: visible
                theme: root.theme
                iconName: root.navigationExpanded
                    ? "chevron-left" : "chevron-right"
                iconColor: root.navigationExpanded
                    ? root.theme.secondaryText : root.theme.action
                backgroundColor: root.navigationExpanded
                    && !navigationToggle.activeFocus
                    ? "transparent" : root.theme.surfaceContainerHigh
                toolTip: root.navigationExpanded
                    ? qsTr("Hide article navigation")
                    : qsTr("Show article navigation")
                Accessible.role: Accessible.Button
                Accessible.name: toolTip
                Accessible.onPressAction:
                    root.navigationExpanded = !root.navigationExpanded
                Keys.onPressed: event => {
                    if (event.key !== Qt.Key_Return
                            && event.key !== Qt.Key_Enter
                            && event.key !== Qt.Key_Space)
                        return
                    root.navigationExpanded = !root.navigationExpanded
                    event.accepted = true
                }
                onClicked: root.navigationExpanded = !root.navigationExpanded
            }
            Controls.Button {
                objectName: "knowledgeSaveOrganization"
                visible: knowledgeController.organizationDirty
                theme: root.theme
                compact: root.width < 720
                text: qsTr("Save order")
                toolTip: text
                icon.name: "save"
                highlighted: true
                enabled: !knowledgeController.busy
                onClicked: knowledgeController.save_organization()
            }
            Controls.CompactIconButton {
                objectName: "knowledgeDiscardOrganization"
                visible: knowledgeController.organizationDirty
                theme: root.theme
                iconName: "undo"
                toolTip: qsTr("Discard order changes")
                enabled: !knowledgeController.busy
                onClicked: knowledgeController.discard_organization()
            }
            Controls.CompactIconButton {
                objectName: "knowledgeCreateArticle"
                visible: knowledgeController.initialized && knowledgeController.canEdit
                theme: root.theme
                iconName: "create-article"
                iconColor: root.theme.action
                toolTip: qsTr("Create article")
                onClicked: knowledgeController.create("article", knowledgeController.document.kind === "section" ? knowledgeController.identity : String(knowledgeController.document.parentCode || ""))
            }
            Controls.CompactIconButton {
                objectName: "knowledgeCreateSection"
                visible: knowledgeController.initialized && knowledgeController.canEdit
                theme: root.theme
                iconName: "folder-plus"
                iconColor: root.theme.action
                toolTip: qsTr("Create section")
                onClicked: knowledgeController.create("section", knowledgeController.document.kind === "section" ? knowledgeController.identity : String(knowledgeController.document.parentCode || ""))
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "refresh"
                toolTip: qsTr("Reload articles")
                enabled: !knowledgeController.busy && !knowledgeController.organizationDirty
                onClicked: knowledgeController.reload()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: errorRow.implicitHeight + 14
            visible: knowledgeController.error.length > 0
            radius: root.theme.itemRadius
            color: root.theme.blend(root.theme.error, root.theme.surfaceContainerLow, 0.14)
            border.width: 1
            border.color: root.theme.error
            RowLayout {
                id: errorRow
                anchors.fill: parent
                anchors.margins: 7
                spacing: 7
                Controls.MaterialIcon {
                    name: "exclamation-circle"
                    size: 16
                    color: root.theme.error
                }
                Label {
                    id: errorText
                    objectName: "knowledgeErrorText"
                    Layout.fillWidth: true
                    text: knowledgeController.error
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    wrapMode: Text.Wrap
                }
                Controls.CompactIconButton {
                    objectName: "knowledgeErrorDismiss"
                    theme: root.theme
                    iconName: "times"
                    toolTip: qsTr("Dismiss error")
                    onClicked: knowledgeController.dismiss_error()
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: knowledgeController.initialized

            KnowledgeNavigation {
                id: navigation
                objectName: "knowledgeNavigation"
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: root.narrow ? parent.width : Math.min(310, parent.width * 0.34)
                visible: root.narrow
                    ? root.navigationPage : root.navigationExpanded
                theme: root.theme
                controller: knowledgeController
                onArticleRequested: root.navigationPage = false
            }

            Rectangle {
                visible: !root.narrow && root.navigationExpanded
                anchors.left: navigation.right
                anchors.leftMargin: 8
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 1
                color: root.theme.outlineVariant
            }

            Loader {
                id: articleLoader
                objectName: "knowledgeArticleLoader"
                anchors.left: root.narrow || !root.navigationExpanded
                    ? parent.left : navigation.right
                anchors.leftMargin: root.narrow || !root.navigationExpanded
                    ? 0 : 17
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                visible: !root.narrow || !root.navigationPage
                active: knowledgeController.identity.length > 0 || knowledgeController.creating
                sourceComponent: knowledgeController.editing ? editorComponent : viewerComponent
            }

            Controls.EmptyState {
                anchors.left: root.narrow || !root.navigationExpanded
                    ? parent.left : navigation.right
                anchors.leftMargin: root.narrow || !root.navigationExpanded
                    ? 0 : 17
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                visible: (!root.narrow || !root.navigationPage) && knowledgeController.identity.length === 0 && !knowledgeController.creating && !knowledgeController.busy
                theme: root.theme
                iconName: "file"
                title: qsTr("Choose an article")
                message: qsTr("Sections, full-text search, files, and object links stay together here.")
            }
        }

        CollaborationInitializationState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !knowledgeController.initialized
            theme: root.theme
            canInitialize: knowledgeController.canInitialize
            busy: knowledgeController.busy
            // The persistent error card above already owns this surface.
            error: ""
            featureIcon: "file"
            featureTitle: qsTr("Knowledge Base is not initialized")
            featureMessage: qsTr("Initialize the collaboration schema before writing project documentation.")
            projectCode: knowledgeController.projectCode
            onInitializeRequested: knowledgeController.initialize()
        }

        Controls.BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            visible: knowledgeController.busy && knowledgeController.initialized
            running: visible
            uiTheme: root.theme
        }
    }

    Component {
        id: viewerComponent
        KnowledgeArticleViewer {
            theme: root.theme
            controller: knowledgeController
            resizeActive: root.dockResizeActive
            backNavigationAvailable: root.narrow && !navigation.visible
            onBackRequested: root.navigationPage = true
        }
    }
    Component {
        id: editorComponent
        KnowledgeArticleEditor {
            theme: root.theme
            controller: knowledgeController
            resizeActive: root.dockResizeActive
            backNavigationAvailable: root.narrow && !navigation.visible
            onBackRequested: root.navigationPage = true
        }
    }
}
