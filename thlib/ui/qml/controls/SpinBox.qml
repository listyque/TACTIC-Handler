import "../tactic_frame/controls/forms/number.mjs" as Numbers
import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.SpinBox {
    id: control

    required property var theme
    property int decimals: 0
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : Qt.locale().name.indexOf("ru") === 0 ? "ru" : "en"
    readonly property bool errorState: !spinInput.acceptableInput
    property bool readOnly: false
    readonly property int valueScale: Math.pow(10, Math.max(0, decimals))
    readonly property real realValue: value / valueScale
    readonly property string formattedValue: displayText
    locale: Qt.locale(language === "ru" ? "ru_RU" : "en_US")
    signal realValueEdited(real value)

    function scaledValue(realValue) {
        return Math.round(Number(realValue || 0) * valueScale);
    }

    onValueModified: realValueEdited(realValue)
    function restoreFormattedText() {
        spinInput.text = Qt.binding(function () {
            return control.displayText;
        });
    }
    function commitTextValue() {
        if (!enabled || readOnly || !editable)
            return;
        spinInput.editingFinished();
    }

    textFromValue: function (value, locale) {
        return Numbers.format(value / control.valueScale, control.decimals, control.language);
    }
    valueFromText: function (text, locale) {
        const number = Numbers.parse(text, control.decimals, control.language);
        return number === null ? control.value : Math.round(number * control.valueScale);
    }

    implicitHeight: theme.controlHeight
    editable: true
    leftPadding: Foundation.controls.number.indicatorWidth
    rightPadding: Foundation.controls.number.indicatorWidth
    font: Qt.font({
        family: theme.fontFamily,
        hintingPreference: Font.PreferVerticalHinting,
        pixelSize: Foundation.textStyles.body
    })

    RegularExpressionValidator {
        id: numberValidator
        regularExpression: new RegExp(Numbers.pattern(control.decimals, control.language))
    }

    contentItem: TextInput {
        id: spinInput
        objectName: "spinBoxTextInput"
        text: control.displayText
        color: control.enabled ? control.theme.primaryText : control.theme.disabledText
        selectionColor: control.theme.action
        selectedTextColor: control.theme.selectedText
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        readOnly: !control.editable || control.readOnly
        selectByMouse: true
        validator: numberValidator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
        onEditingFinished: Qt.callLater(control.restoreFormattedText)
        Keys.onEscapePressed: event => {
            control.restoreFormattedText();
            event.accepted = true;
        }

        HoverHandler {
            objectName: "spinBoxCursorHandler"
            cursorShape: control.enabled && control.editable ? Qt.IBeamCursor : Qt.ArrowCursor
        }
    }

    up.indicator: Controls.CompactIconButton {
        x: control.width - width
        height: control.height
        width: Foundation.controls.number.indicatorWidth
        theme: control.theme
        toolTip: qsTr("Increase value")
        iconName: "chevron-up"
        iconSize: Foundation.controls.number.iconSize
        round: false
        enabled: control.enabled && !control.readOnly && control.value < control.to
        onClicked: {
            control.increase();
            control.realValueEdited(control.realValue);
        }
    }
    down.indicator: Controls.CompactIconButton {
        height: control.height
        width: Foundation.controls.number.indicatorWidth
        theme: control.theme
        toolTip: qsTr("Decrease value")
        iconName: "chevron-down"
        iconSize: Foundation.controls.number.iconSize
        round: false
        enabled: control.enabled && !control.readOnly && control.value > control.from
        onClicked: {
            control.decrease();
            control.realValueEdited(control.realValue);
        }
    }

    Keys.onPressed: event => {
        if (readOnly && (event.key === Qt.Key_Up || event.key === Qt.Key_Down))
            event.accepted = true;
    }

    background: Rectangle {
        radius: control.theme.fieldRadius
        color: control.theme.surfaceContainerHigh
        border.width: control.activeFocus ? 2 : 1
        border.color: control.errorState ? control.theme.error : control.activeFocus ? control.theme.action : control.theme.outline
    }
}
