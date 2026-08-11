import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ComboBox {
    id: control

    required property var theme
    property string colorRole: ""
    property bool actionField: false
    property bool showIndicator: !actionField
    property string leadingIcon: ""
    property color leadingIconColor: theme.secondaryText

    function optionValue(index, roleName) {
        if (!roleName || index < 0 || !control.model)
            return ""
        if (control.model.get)
            return control.model.get(index)[roleName] || ""
        const value = control.model[index]
        return value && value[roleName] !== undefined
            ? value[roleName] : ""
    }

    implicitWidth: 140
    implicitHeight: theme.compactControlHeight
    leftPadding: 11
    rightPadding: showIndicator ? 32 : 12
    topPadding: 0
    bottomPadding: 0
    font.family: theme.fontFamily
    font.pixelSize: 10

    contentItem: RowLayout {
        spacing: 7
        MaterialIcon {
            visible: control.leadingIcon.length > 0
            name: control.leadingIcon
            size: control.actionField ? 17 : 15
            color: control.enabled
                ? control.leadingIconColor : control.theme.disabledText
        }
        Rectangle {
            visible: !!control.colorRole
                && control.leadingIcon.length === 0
                && !!control.optionValue(control.currentIndex, control.colorRole)
            Layout.preferredWidth: 9
            Layout.preferredHeight: 9
            radius: 4.5
            color: control.optionValue(control.currentIndex, control.colorRole)
        }
        Label {
            Layout.fillWidth: true
            text: qsTr(control.displayText)
            color: control.enabled
                ? control.theme.primaryText : control.theme.disabledText
            font: control.font
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    indicator: MaterialIcon {
        visible: control.showIndicator
        x: control.width - width - 9
        y: (control.height - height) / 2
        name: control.popup.opened ? "expand_less" : "expand_more"
        size: 17
        color: control.enabled
            ? control.theme.secondaryText : control.theme.disabledText
    }

    background: Rectangle {
        radius: control.actionField
            ? Math.min(height / 2, control.theme.itemRadius)
            : control.theme.fieldRadius
        color: control.actionField
            ? !control.enabled
                ? control.theme.surfaceContainerLow
                : control.down
                    ? control.theme.surfaceContainer
                    : control.hovered
                        ? control.theme.surfaceContainerHigh
                        : control.theme.surfaceContainerLow
            : !control.enabled
                ? control.theme.surfaceContainerLow
            : control.theme.surfaceContainerLow
        border.width: control.actionField
            ? 0 : control.activeFocus ? 2 : 1
        border.color: control.activeFocus
            ? control.theme.action : control.theme.outlineVariant

        Behavior on color {
            ColorAnimation {
                duration: control.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    HoverHandler {
        objectName: "md3ComboBoxCursorHandler"
        cursorShape: control.enabled
            ? control.editable
                ? Qt.IBeamCursor : Qt.PointingHandCursor
            : Qt.ArrowCursor
    }

    delegate: ItemDelegate {
        id: option

        required property int index

        width: control.popup.width - 8
        height: 34
        leftPadding: 12
        rightPadding: 10
        highlighted: control.highlightedIndex === index

        contentItem: RowLayout {
            spacing: 8
            Rectangle {
                visible: !!control.colorRole
                    && !!control.optionValue(option.index, control.colorRole)
                Layout.preferredWidth: 9
                Layout.preferredHeight: 9
                radius: 4.5
                color: control.optionValue(option.index, control.colorRole)
            }
            Label {
                Layout.fillWidth: true
                text: qsTr(control.textAt(option.index))
                color: control.theme.primaryText
                font: control.font
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
        }
        background: Rectangle {
            radius: control.theme.itemRadius
            color: option.highlighted
                ? control.theme.secondaryContainer : "transparent"
        }
    }

    popup: Md3Popup {
        theme: control.theme
        y: control.height + 4
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 246)
        padding: 4

        contentItem: ListView {
            implicitHeight: contentHeight
            clip: true
            currentIndex: control.highlightedIndex
            model: control.delegateModel
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: Md3ScrollBar {
                theme: control.theme
                flickableTarget: parent
            }
        }

    }
}
