pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string pageId
    property bool managed: false
    property var schema: ({})
    property var values: ({})
    property bool loadingValues: true

    function syncValues() {
        root.loadingValues = true
        root.schema = configurationController.page_schema(root.pageId)
        root.values = configurationController.page_values(root.pageId)
        root.loadingValues = false
    }

    function setValue(key, value) {
        const updated = Object.assign({}, root.values)
        updated[key] = value
        root.values = updated
        if (root.managed && !root.loadingValues)
            configurationController.update_page(root.pageId, updated)
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController

        function onSessionStarted() {
            root.syncValues()
        }

        function onPageReset(pageId) {
            if (pageId === root.pageId)
                root.syncValues()
        }
    }

    ScrollView {
        id: dccScroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: dccContent.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: dccScroll
        }

        ColumnLayout {
            id: dccContent
            x: 22
            y: 20
            width: Math.max(0, dccScroll.availableWidth - 44)
            spacing: 14

            Repeater {
                objectName: "dccConfigurationSections"
                model: root.schema.sections || []

                ConfigurationSection {
                    id: sectionDelegate
                    objectName: "dccConfigurationSection"
                    required property var modelData
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr(String(
                        sectionDelegate.modelData.title || ""
                    ))
                    description: qsTr(String(
                        sectionDelegate.modelData.description || ""
                    ))
                    iconName: String(
                        sectionDelegate.modelData.icon || "deployed_code"
                    )

                    Repeater {
                        objectName: "dccConfigurationFields"
                        model: sectionDelegate.modelData.fields || []

                        DccSettingField {
                            id: settingDelegate
                            required property var modelData
                            Layout.fillWidth: true
                            theme: root.theme
                            field: settingDelegate.modelData
                            value: root.values[settingDelegate.modelData.key]
                                ?? settingDelegate.modelData.default
                            onValueEdited: value => root.setValue(
                                settingDelegate.modelData.key, value
                            )
                        }
                    }
                }
            }

            Item { Layout.preferredHeight: 8 }
        }
    }
}
