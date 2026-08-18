import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    required property var theme
    required property string title
    required property string emptyText
    required property var sourceModel
    property bool loading: false
    property bool canLoadMore: false
    property int totalCount: sourceModel ? sourceModel.count : 0
    signal rowSelected(int row, bool additive)
    signal loadMoreRequested()

    radius: root.theme.surfaceRadius
    color: root.theme.panel
    border.width: 1
    border.color: root.theme.outlineVariant
    clip: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            color: root.theme.panelRaised

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    text: root.title
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }

                Label {
                    text: {
                        const visibleCount = root.sourceModel
                            ? root.sourceModel.count : 0
                        if (root.totalCount > visibleCount)
                            return visibleCount + " / " + root.totalCount
                        return String(visibleCount)
                    }
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    font.weight: Font.DemiBold
                }

                Md3BusyIndicator {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    uiTheme: root.theme
                    visible: root.loading
                    running: visible
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            SmoothListView {
                id: objectList
                anchors.fill: parent
                anchors.rightMargin: verticalBar.visible ? 6 : 0
                model: root.sourceModel
                clip: true
                spacing: 4
                topMargin: 6
                bottomMargin: 6
                leftMargin: 6
                rightMargin: 6

                ScrollBar.vertical: Md3ScrollBar {
                    id: verticalBar
                    theme: root.theme
                    policy: objectList.contentHeight > objectList.height
                        ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
                }

                delegate: Item {
                    id: row

                    required property int index
                    required property string searchKey
                    required property string title
                    required property string subtitle
                    required property string previewUrl
                    required property string fallbackText
                    required property color accent
                    required property bool selected

                    width: objectList.width
                        - objectList.leftMargin - objectList.rightMargin
                    height: 64

                    ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        selected: row.selected
                        hovered: rowPointer.containsMouse
                        pressed: rowPointer.pressed
                        accent: row.accent
                        railVisible: true
                        railX: 0
                        railWidth: 3
                        inset: 0
                        cornerRadius: root.theme.itemRadius
                        separatorVisible: false
                        normalColor: root.theme.row
                        selectedColor: root.theme.selected
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 10

                        ItemPreview {
                            Layout.preferredWidth: 44
                            Layout.preferredHeight: 44
                            theme: root.theme
                            previewSize: 44
                            source: row.previewUrl
                            fallbackIcon: "sobject"
                            fallbackText: row.fallbackText
                            accent: row.accent
                            selected: row.selected
                            outlined: true
                            cornerRadius: root.theme.itemRadius
                            animateAppearance: false
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Label {
                                Layout.fillWidth: true
                                text: row.title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.bodyLarge
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Label {
                                Layout.fillWidth: true
                                visible: row.subtitle.length > 0
                                text: row.subtitle
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                elide: Text.ElideRight
                            }
                        }

                        MaterialIcon {
                            visible: row.selected
                            name: "check-circle"
                            size: 16
                            color: root.theme.action
                        }
                    }

                    MouseArea {
                        id: rowPointer
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton
                        cursorShape: Qt.PointingHandCursor
                        onClicked: function(mouse) {
                            root.rowSelected(
                                row.index,
                                (mouse.modifiers & Qt.ControlModifier) !== 0
                            )
                        }
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                width: Math.min(280, parent.width - 36)
                visible: objectList.count === 0 && !root.loading
                text: root.emptyText
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.body
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }

            ContentLoadingOverlay {
                anchors.fill: parent
                z: 3
                theme: root.theme
                visible: root.loading && objectList.count === 0
                message: qsTr("Loading objects...")
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 48 : 0
            visible: root.canLoadMore
                || (root.loading && root.sourceModel && root.sourceModel.count > 0)
            color: root.theme.panelRaised

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: root.theme.separator
            }

            RowLayout {
                anchors.centerIn: parent
                spacing: 8

                Md3BusyIndicator {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    uiTheme: root.theme
                    visible: root.loading
                    running: visible
                }

                Md3Button {
                    theme: root.theme
                    visible: root.canLoadMore
                    enabled: !root.loading
                    tonal: true
                    icon.name: "expand-more"
                    text: qsTr("Load more")
                    onClicked: root.loadMoreRequested()
                }
            }
        }
    }
}
