import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.SpinBox {
    id: control

    required property var theme
    property int decimals: 0
    readonly property int valueScale: Math.pow(10, Math.max(0, decimals))
    readonly property real realValue: value / valueScale
    readonly property string formattedValue: textFromValue(value, locale)
    signal realValueEdited(real value)

    function scaledValue(realValue) {
        return Math.round(Number(realValue || 0) * valueScale)
    }

    function commitTextValue() {
        const parsed = valueFromText(spinInput.text, locale)
        value = Math.max(from, Math.min(to, parsed))
        spinInput.text = formattedValue
        realValueEdited(realValue)
    }

    textFromValue: function(value, locale) {
        if (control.decimals <= 0)
            return Number(value).toLocaleString(locale, "f", 0)
        let text = Number(value / control.valueScale).toLocaleString(
            locale, "f", control.decimals
        )
        return text.replace(/([,.]\d*?)0+$/, "$1").replace(/[,.]$/, "")
    }
    valueFromText: function(text, locale) {
        const number = Number.fromLocaleString(locale, text)
        return Math.round((isNaN(number) ? 0 : number) * control.valueScale)
    }

    implicitHeight: theme.controlHeight
    editable: true
    leftPadding: 34
    rightPadding: 34
    font.family: theme.fontFamily
    font.pointSize: Typography.body

    DoubleValidator {
        id: decimalValidator
        bottom: control.from / control.valueScale
        top: control.to / control.valueScale
        decimals: control.decimals
        notation: DoubleValidator.StandardNotation
    }

    contentItem: TextInput {
        id: spinInput
        objectName: "spinBoxTextInput"
        text: control.formattedValue
        color: control.enabled
            ? control.theme.primaryText : control.theme.disabledText
        selectionColor: control.theme.action
        selectedTextColor: control.theme.selectedText
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        readOnly: !control.editable
        selectByMouse: true
        validator: control.decimals > 0
            ? decimalValidator : control.validator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
        onEditingFinished: control.commitTextValue()

        HoverHandler {
            objectName: "spinBoxCursorHandler"
            cursorShape: control.enabled && control.editable
                ? Qt.IBeamCursor : Qt.ArrowCursor
        }
    }

    up.indicator: Controls.CompactIconButton {
        x: control.width - width
        height: control.height
        width: 34
        theme: control.theme
        iconName: "chevron-up"
        iconSize: 14
        round: true
        enabled: control.enabled && control.value < control.to
        onClicked: {
            control.value = Math.min(
                control.to,
                control.value + control.stepSize
            )
            control.realValueEdited(control.realValue)
        }
    }
    down.indicator: Controls.CompactIconButton {
        height: control.height
        width: 34
        theme: control.theme
        iconName: "chevron-down"
        iconSize: 14
        round: true
        enabled: control.enabled && control.value > control.from
        onClicked: {
            control.value = Math.max(
                control.from,
                control.value - control.stepSize
            )
            control.realValueEdited(control.realValue)
        }
    }

    background: Rectangle {
        radius: control.theme.fieldRadius
        color: control.theme.surfaceContainerHigh
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus
            ? control.theme.action : control.theme.outline
    }
}
