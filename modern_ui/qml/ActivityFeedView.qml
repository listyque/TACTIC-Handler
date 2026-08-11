import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme

    Component.onCompleted: {
        activityFeedController.set_visible(true)
        activityFeedController.refresh()
    }
    Component.onDestruction: activityFeedController.set_visible(false)
    onVisibleChanged: activityFeedController.set_visible(visible)
    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("ACTIVITY FEED")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
            RefreshIconButton {
                theme: root.theme
                enabled: !activityFeedController.busy
                toolTip: qsTr("Refresh activity")
                onClicked: activityFeedController.refresh()
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [
                    {"key": "all", "title": "All"},
                    {"key": "my_tasks", "title": "My tasks"},
                    {"key": "my_objects", "title": "My objects"},
                    {"key": "messages", "title": "Messages"},
                    {"key": "publications", "title": "Publications"}
                ]
                delegate: Md3Button {
                    required property var modelData
                    theme: root.theme
                    text: qsTr(String(modelData.title))
                    highlighted: activityFeedController.currentFilter === modelData.key
                    onClicked: activityFeedController.set_filter(modelData.key)
                }
            }
        }

        Label {
            visible: activityFeedController.error.length > 0
            Layout.fillWidth: true
            text: activityFeedController.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }

        ListView {
            id: feed
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: activityFeedModel
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
            footer: Md3Button {
                visible: activityFeedController.hasMore
                anchors.horizontalCenter: parent.horizontalCenter
                theme: root.theme
                text: qsTr("Load more")
                enabled: !activityFeedController.busy
                onClicked: activityFeedController.load_more()
            }
            delegate: Item {
                id: eventRow
                required property int index
                required property string kind
                required property string title
                required property string detail
                required property string actor
                required property string timestamp
                required property string searchKey
                required property string targetSearchKey
                required property string targetTitle
                required property string targetType
                required property string project
                required property string process
                required property string context
                required property string version
                required property bool canOpen
                width: feed.width
                height: eventCard.implicitHeight

                ActivityEventCard {
                    id: eventCard
                    anchors.fill: parent
                    theme: root.theme
                    kind: eventRow.kind
                    eventTitle: eventRow.title
                    detail: eventRow.detail
                    actor: eventRow.actor
                    timestamp: eventRow.timestamp
                    targetSearchKey: eventRow.targetSearchKey
                    targetTitle: eventRow.targetTitle
                    targetType: eventRow.targetType
                    process: eventRow.process
                    context: eventRow.context
                    version: eventRow.version
                    canOpenActivity: eventRow.canOpen
                        && eventRow.searchKey.length > 0
                    canOpenTarget: eventRow.targetSearchKey.length > 0
                    onActivityRequested:
                        activityFeedController.open_item(eventRow.index)
                    onTargetRequested:
                        activityFeedController.open_target(eventRow.index)
                }
            }

            Label {
                anchors.centerIn: parent
                visible: feed.count === 0 && !activityFeedController.busy
                text: qsTr("No activity for this filter")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 11
            }
        }

    }

    ContentLoadingOverlay {
        anchors.fill: parent
        anchors.margins: 12
        z: 20
        theme: root.theme
        visible: activityFeedController.busy && feed.count === 0
        message: qsTr("Loading activity...")
    }
}
