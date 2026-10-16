pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/shell/projects.ui.mjs" as Projects

// QML counterpart of Ui_projectsChooserWidget + Ui_projectItemWidget:
// categorized, three-column project cards with Ui_projectLinkWidget previews.
Controls.Popup {
    id: root
    required property var model
    objectName: "projectChooser"
    surfaceRadius: theme.dialogRadius
    property double lastClosedAt: 0
    property string selectedCode: ""
    readonly property var popupSize: Projects.popup(parent.width, parent.height)
    readonly property var heading: Projects.header(width, model.visibleCount, model.totalCount, (text, values) => {
        if (text === "{visible} of {total} projects shown")
            return qsTr("%1 of %2 projects shown").arg(values.visible).arg(values.total);
        return qsTranslate("ProjectChooser", text);
    })
    readonly property var headerChrome: ({
            width: width,
            height: heading.height,
            nodes: heading.nodes.filter(item => item.kind !== "View")
        })
    signal projectSelected(string code)

    parent: Overlay.overlay
    width: popupSize.width
    height: popupSize.height
    modal: false
    dim: true
    focus: true
    padding: 0
    settledClosePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onClosed: lastClosedAt = Date.now()

    function moveProject(code, key) {
        const groups = Array.from(root.model.groups);
        const target = Projects.keyTarget(groups.reduce((codes, group) => codes.concat(Array.from(group.projects).map(project => project.code)), []), code, key, 3);
        if (!target)
            return false;
        const index = groups.findIndex(group => group.projects.some(project => project.code === target));
        categories.positionViewAtIndex(index, ListView.Contain);
        categories.forceLayout();
        const group = categories.itemAtIndex(index) as ProjectCategory;
        if (group)
            group.focusProject(target);
        return true;
    }

    function toggle(sourceItem) {
        root.protectOpeningFrom(sourceItem);
        if (root.openingInputGuardActive) {
            root.sourceWasOpen = false;
            return;
        }
        if (root.sourceWasOpen || root.opened) {
            root.close();
        } else {
            root.openCenteredIn(root.parent);
        }
        root.sourceWasOpen = false;
    }

    enter: Transition {
        enabled: root.animationsEnabled
        NumberAnimation {
            property: "opacity"
            from: 0
            to: 1
            duration: root.theme.popupMotionMedium
        }
        NumberAnimation {
            property: "scale"
            from: 0.97
            to: 1
            duration: root.theme.popupMotionSlow
            easing.type: Easing.OutCubic
        }
    }
    exit: Transition {
        enabled: root.animationsEnabled
        NumberAnimation {
            property: "opacity"
            from: 1
            to: 0
            duration: root.theme.popupMotionFast
        }
        NumberAnimation {
            property: "scale"
            from: 1
            to: 0.985
            duration: root.theme.popupMotionFast
        }
    }
    contentItem: ColumnLayout {
        spacing: 0
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: root.heading.height - 1
            Frame.FrameView {
                anchors.fill: parent
                theme: root.theme
                scene: root.headerChrome
                interactive: false
            }
            Controls.ProjectFilterToggles {
                id: filtersRow
                anchors.left: parent.left
                anchors.leftMargin: 20
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 8
                theme: root.theme
                model: root.model
            }
            Controls.CompactIconButton {
                id: closeButton
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.top: parent.top
                anchors.topMargin: 8
                width: 44
                height: 44
                theme: root.theme
                iconName: "close"
                iconSize: 20
                iconColor: root.theme.primaryText
                round: true
                toolTip: qsTr("Close")
                onClicked: root.close()
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.separator
        }
        ListView {
            id: categories
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 12
            Layout.rightMargin: 12
            Layout.bottomMargin: 12
            clip: true
            spacing: 4
            model: root.model.groups
            rightMargin: Projects.dimensions.gutter
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }

            delegate: ProjectCategory {}
            Label {
                anchors.centerIn: parent
                visible: categories.count === 0
                text: qsTr("No projects match the current filters")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
            }
        }
    }
    component ProjectCategory: Item {
        id: categoryDelegate
        required property var modelData
        function focusProject(code) {
            const index = modelData.projects.findIndex(project => project.code === code);
            const item = cards.itemAt(index);
            if (item)
                item.forceActiveFocus();
        }
        width: categories.width - categories.rightMargin
        height: categoryColumn.implicitHeight

        Column {
            id: categoryColumn
            width: parent.width
            spacing: 6
            Frame.FrameView {
                width: parent.width
                height: 42
                theme: root.theme
                interactive: false
                scene: Projects.categoryHeader(width, categoryDelegate.modelData.title, categoryDelegate.modelData.projects.length, text => qsTranslate("ProjectChooser", text))
            }
            Flow {
                width: parent.width
                spacing: 8
                Repeater {
                    id: cards
                    model: categoryDelegate.modelData.projects
                    delegate: Controls.ProjectCard {
                        id: projectCard
                        required property var modelData
                        width: Projects.category(categoryColumn.width, categoryDelegate.modelData.projects.length).cardWidth
                        selected: modelData.code === root.selectedCode
                        details: modelData
                        theme: root.theme
                        compact: false
                        Keys.onPressed: event => {
                            const keys = {
                                [Qt.Key_Left]: "ArrowLeft",
                                [Qt.Key_Right]: "ArrowRight",
                                [Qt.Key_Up]: "ArrowUp",
                                [Qt.Key_Down]: "ArrowDown",
                                [Qt.Key_Home]: "Home",
                                [Qt.Key_End]: "End"
                            };
                            if (keys[event.key])
                                event.accepted = root.moveProject(projectCard.modelData.code, keys[event.key]);
                        }
                        onClicked: {
                            root.projectSelected(modelData.code);
                            root.close();
                        }
                    }
                }
            }
        }
    }
}
