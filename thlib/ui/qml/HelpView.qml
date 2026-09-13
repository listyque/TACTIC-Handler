import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    objectName: "applicationHelpView"
    required property var theme

    readonly property var selectedTopic: helpController.article || ({})
    readonly property string selectedTopicId: helpController.selected_topic_id

    function filteredTopics() {
        const query = helpSearch.text.trim().toLowerCase()
        if (!query.length)
            return helpController.topics
        return helpController.topics.filter(function(topic) {
            return (topic.title + " " + topic.group + " "
                    + topic.searchText).toLowerCase().indexOf(query) >= 0
        })
    }

    function selectTopic(topicId) {
        helpController.select(topicId || "overview")
        if (articleScroll.contentItem)
            articleScroll.contentItem.contentY = 0
        topicReveal.restart()
    }

    function currentTopicIndex() {
        const topics = filteredTopics()
        return topics.findIndex(function(topic) {
            return topic.id === root.selectedTopicId
        })
    }

    function revealSelectedTopic() {
        let index = currentTopicIndex()
        if (index < 0 && helpSearch.text.length) {
            helpSearch.text = ""
            index = currentTopicIndex()
        }
        if (index >= 0)
            topicList.positionViewAtIndex(index, ListView.Contain)
    }

    Component.onCompleted: selectTopic(windowModel.helpTopic)

    Connections {
        target: windowModel
        function onHelpTopicChanged() {
            root.selectTopic(windowModel.helpTopic)
        }
    }

    Connections {
        target: helpController
        function onArticleChanged() {
            if (articleScroll.contentItem)
                articleScroll.contentItem.contentY = 0
            topicReveal.restart()
        }
    }

    Timer {
        id: topicReveal
        interval: 1
        onTriggered: root.revealSelectedTopic()
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Rectangle {
            Layout.preferredWidth: Math.min(292, Math.max(236, root.width * 0.29))
            Layout.fillHeight: true
            radius: root.theme.surfaceRadius
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Controls.MaterialIcon {
                        name: "help"
                        size: 20
                        color: root.theme.action
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Help topics")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }
                }

                Controls.TextField {
                    id: helpSearch
                    objectName: "helpTopicSearch"
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("Search help")
                }

                Controls.SmoothListView {
                    id: topicList
                    objectName: "helpTopicList"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    clip: true
                    spacing: 3
                    model: root.filteredTopics()
                    currentIndex: root.currentTopicIndex()
                    rightMargin: 8
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                    }

                    delegate: Item {
                        id: topicRow
                        required property var modelData
                        width: ListView.view.width - ListView.view.rightMargin
                        height: 58
                        readonly property bool selected:
                            root.selectedTopicId === modelData.id

                        Controls.ItemSurface {
                            anchors.fill: parent
                            theme: root.theme
                            selected: topicRow.selected
                            hovered: topicMouse.containsMouse
                            pressed: topicMouse.pressed
                            accent: root.theme.action
                            cornerRadius: root.theme.itemRadius
                            separatorVisible: false
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 11
                            anchors.rightMargin: 9
                            spacing: 9

                            Controls.MaterialIcon {
                                name: topicRow.modelData.icon
                                size: 17
                                color: topicRow.selected
                                    ? root.theme.action
                                    : root.theme.secondaryText
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1

                                Label {
                                    Layout.fillWidth: true
                                    text: topicRow.modelData.title
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: topicRow.selected
                                        ? Font.DemiBold : Font.Normal
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: topicRow.modelData.group
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        MouseArea {
                            id: topicMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.selectTopic(topicRow.modelData.id)
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: topicList.count === 0
                        text: qsTr("No help topics match your search")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: root.theme.surfaceRadius
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 0

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 14
                    Layout.rightMargin: 10
                    Layout.topMargin: 10
                    Layout.bottomMargin: 10
                    spacing: 10

                    Controls.MaterialIcon {
                        name: root.selectedTopic.icon || "help"
                        size: 24
                        color: root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            Layout.fillWidth: true
                            text: root.selectedTopic.title || ""
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.title
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Label {
                            text: root.selectedTopic.group || ""
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                    }
                    Controls.CompactIconButton {
                        objectName: "helpReloadButton"
                        theme: root.theme
                        iconName: "refresh"
                        toolTip: qsTr("Reload help articles")
                        onClicked: helpController.reload()
                    }
                    Controls.CompactIconButton {
                        objectName: "helpOpenArticleFileButton"
                        theme: root.theme
                        iconName: "folder-open"
                        toolTip: qsTr("Open article file")
                        enabled: Boolean(root.selectedTopic.filePath)
                        onClicked: helpController.open_current_file()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.theme.outlineVariant
                }

                ScrollView {
                    id: articleScroll
                    objectName: "helpArticleScroll"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: articleContent.y
                        + articleContent.height + 14
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: articleScroll
                    }

                    Column {
                        id: articleContent
                        width: Math.max(0, articleScroll.width - 40)
                        x: 14
                        y: 14
                        height: implicitHeight
                        spacing: 14

                        Rectangle {
                            objectName: "helpArticleSummary"
                            width: articleContent.width
                            height: summaryLayout.implicitHeight + 24
                            visible: !helpController.error.length
                                && Boolean(root.selectedTopic.summary)
                            radius: root.theme.itemRadius
                            color: root.theme.surfaceContainerHigh
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            RowLayout {
                                id: summaryLayout
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10

                                Controls.MaterialIcon {
                                    Layout.alignment: Qt.AlignTop
                                    name: "info"
                                    size: 18
                                    color: root.theme.action
                                }
                                Controls.SelectableText {
                                    objectName: "helpArticleSummaryText"
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: contentHeight
                                    theme: root.theme
                                    baseUrl: root.selectedTopic.fileUrl || ""
                                    text: root.selectedTopic.summary || ""
                                    textFormat: TextEdit.MarkdownText
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    wrapMode: TextEdit.WordWrap
                                    onLinkActivated: link =>
                                        Qt.openUrlExternally(link)
                                }
                            }
                        }

                        Controls.SelectableText {
                            id: articleBody
                            objectName: "helpArticleBody"
                            property string spacedText: ""
                            width: articleContent.width
                            height: contentHeight
                            theme: root.theme
                            baseUrl: root.selectedTopic.fileUrl || ""
                            text: helpController.error.length
                                ? helpController.error
                                : (root.selectedTopic.body || "")
                            textFormat: TextEdit.MarkdownText
                            color: helpController.error.length
                                ? root.theme.error : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            wrapMode: TextEdit.WordWrap
                            onLinkActivated: link =>
                                Qt.openUrlExternally(link)
                            onTextChanged: {
                                if (spacedText === text)
                                    return
                                spacedText = text
                                helpController.format_document(textDocument)
                            }
                        }
                    }
                }
            }
        }
    }
}
