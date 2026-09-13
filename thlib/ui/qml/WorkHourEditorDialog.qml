import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id: root

    required property var controller
    property bool editing: false
    property string entryCode: ""
    property string category: "regular"
    property bool awaitingSave: false
    property bool approvingSave: false

    title: editing ? qsTr("Edit work hours") : qsTr("Log work hours")
    width: 430
    height: 390
    x: Math.round((parent.width - width) / 2)
    y: Math.round((parent.height - height) / 2)
    closePolicy: Popup.CloseOnEscape

    function todayText() {
        const now = new Date()
        const month = String(now.getMonth() + 1).padStart(2, "0")
        const day = String(now.getDate()).padStart(2, "0")
        return now.getFullYear() + "-" + month + "-" + day
    }

    function loginIndex(login) {
        for (let index = 0; index < userListModel.count(); ++index) {
            const value = userListModel.get(index)
            if (String(value.login || "") === String(login || ""))
                return index
        }
        return -1
    }

    function prepare(record) {
        const value = record || {}
        editing = String(value.entryCode || "").length > 0
        entryCode = String(value.entryCode || "")
        dayField.text = editing ? String(value.day || "") : todayText()
        durationField.text = editing ? String(value.totalHours || "") : ""
        descriptionField.text = String(value.description || "")
        category = String(value.category || "regular")
        const login = editing
            ? String(value.login || "") : controller.selectedLogin
        loginField.currentIndex = loginIndex(login)
        awaitingSave = false
        approvingSave = false
    }

    function save(approve) {
        const login = controller.canManage && loginField.currentIndex >= 0
            ? loginField.currentValue : controller.selectedLogin
        approvingSave = approve
        awaitingSave = editing
            ? controller.update_time(
                entryCode, dayField.text, category,
                Number(durationField.text), descriptionField.text,
                String(login || ""), approve)
            : controller.log_time(
                dayField.text, category, Number(durationField.text),
                descriptionField.text, String(login || ""), approve)
    }

    function openForCreate() {
        prepare({})
        open()
        durationField.forceActiveFocus()
    }

    function openForEdit(record) {
        prepare(record)
        open()
        durationField.forceActiveFocus()
    }

    Connections {
        target: root.controller
        function onEntrySaved() {
            if (root.awaitingSave) {
                root.awaitingSave = false
                root.close()
            }
        }
    }

    contentItem: ColumnLayout {
        spacing: 12

        Label {
            Layout.fillWidth: true
            text: root.editing
                ? qsTr("Update the selected time entry.")
                : qsTr("Record actual effort for the selected task.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Controls.DateField {
                id: dayField
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Work date")
            }
            Controls.TextField {
                id: durationField
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Duration, hours")
                validator: DoubleValidator {
                    bottom: 0.01
                    top: 24
                    decimals: 2
                    notation: DoubleValidator.StandardNotation
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Controls.Button {
                theme: root.theme
                text: qsTr("Regular")
                icon.name: "schedule"
                highlighted: root.category === "regular"
                onClicked: root.category = "regular"
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Overtime")
                icon.name: "more_time"
                highlighted: root.category === "overtime"
                onClicked: root.category = "overtime"
            }
            Item { Layout.fillWidth: true }
        }

        UserComboBox {
            id: loginField
            visible: root.controller.canManage
            theme: root.theme
            Layout.fillWidth: true
            userModel: userListModel
            model: userListModel
            textRole: "displayName"
            valueRole: "login"
            displayText: currentIndex >= 0
                ? currentText : qsTr("Select user")
        }

        Controls.TextField {
            id: descriptionField
            theme: root.theme
            Layout.fillWidth: true
            placeholderText: qsTr("Description")
        }

        Label {
            visible: root.controller.error.length > 0
            Layout.fillWidth: true
            text: root.controller.error
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                enabled: !root.awaitingSave
                onClicked: root.close()
            }
            Controls.Button {
                theme: root.theme
                text: root.awaitingSave ? qsTr("Saving...") : qsTr("Save")
                icon.name: root.editing ? "save" : "add_alarm"
                highlighted: !root.controller.canManage
                enabled: !root.controller.busy
                    && !root.awaitingSave
                    && dayField.text.length >= 10
                    && Number(durationField.text) > 0
                onClicked: root.save(false)
            }
            Controls.Button {
                visible: root.controller.canManage
                theme: root.theme
                text: root.awaitingSave && root.approvingSave
                    ? qsTr("Approving...") : qsTr("Save & Approve")
                icon.name: "approval"
                highlighted: true
                enabled: !root.controller.busy
                    && !root.awaitingSave
                    && dayField.text.length >= 10
                    && Number(durationField.text) > 0
                onClicked: root.save(true)
            }
        }
    }
}
