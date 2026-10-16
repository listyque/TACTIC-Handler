pragma ComponentBehavior: Bound
import QtQuick
import ".."
import "../controls/forms" as Forms
import "frame.mjs" as Contract
import QtQuick.Controls
import "../../controls" as Controls
import "../.." as TH

Item {
    id: root
    required property var theme
    property var scene: ({
            nodes: []
        })
    property var models: ({})
    property var views: ({})
    property var describeRow: null
    property var describeCell: null
    property bool interactive: true
    signal event(var action)
    property bool ready: false
    property var effectiveTheme: theme
    onThemeChanged: if (theme)
        effectiveTheme = theme

    // Replace the inherited font as a whole, including its size unit.
    function controlFont(definition): font {
        return Qt.font({
            family: definition.monospace ? "Consolas" : effectiveTheme.fontFamily,
            pixelSize: definition.fontSize,
            weight: definition.weight,
            hintingPreference: Font.PreferVerticalHinting,
            strikeout: !!definition.strike
        });
    }
    function color(role): color {
        if (!role)
            return "transparent";
        if (role.mix)
            return effectiveTheme.blend(root.color(role.mix[0]), root.color(role.mix[1]), role.mix[2]);
        if (role === "transparent" || String(role).charAt(0) === "#")
            return Qt.darker(role, 1.0);
        return effectiveTheme[role];
    }
    function reveal(item) {
        for (let parent = item.parent; parent; parent = parent.parent) {
            if (!(parent instanceof Flickable))
                continue;
            const point = item.mapToItem(parent.contentItem, 0, 0);
            if (item.height > parent.height)
                continue;
            const nearest = Math.min(point.y, Math.max(parent.contentY, point.y + item.height - parent.height));
            parent.contentY = Math.max(parent.originY, Math.min(parent.originY + Math.max(0, parent.contentHeight - parent.height), nearest));
        }
    }
    function send(action, value) {
        if (!action || !interactive)
            return;
        root.event(Object.assign({}, action, value === undefined ? {} : {
            value: value
        }));
    }
    function keyboard(key, definition) {
        const keys = {};
        keys[Qt.Key_Return] = "Enter";
        keys[Qt.Key_Enter] = "Enter";
        keys[Qt.Key_F2] = "F2";
        keys[Qt.Key_Left] = "ArrowLeft";
        keys[Qt.Key_Up] = "ArrowUp";
        keys[Qt.Key_Down] = "ArrowDown";
        keys[Qt.Key_Right] = "ArrowRight";
        keys[Qt.Key_Home] = "Home";
        keys[Qt.Key_End] = "End";
        if (!definition.keys || !definition.keys[key]) {
            if (!definition.keys || !definition.keys[keys[key]])
                return false;
            root.send(definition.keys[keys[key]]);
        } else
            root.send(definition.keys[key]);
        return true;
    }
    function sync() {
        if (!ready)
            return;
        const nodes = Contract.validateScene(scene, models, views);
        for (let index = 0; index < nodes.length; index++) {
            const definition = nodes[index];
            let existing = index;
            while (existing < items.count && items.get(existing).key !== definition.id)
                existing++;
            if (existing === items.count)
                items.insert(index, {
                    key: definition.id,
                    definition: definition
                });
            else if (existing !== index)
                items.move(existing, index, 1);
            items.setProperty(index, "definition", definition);
        }
        if (items.count > nodes.length)
            items.remove(nodes.length, items.count - nodes.length);
    }
    function dragValue(source): var {
        return source ? source.frameDragValue : undefined;
    }
    function wrapperAt(index): var {
        return repeater.itemAt(index);
    }
    function focusControl(name) {
        for (let index = 0; index < repeater.count; index++) {
            const wrapper = root.wrapperAt(index);
            if (wrapper && wrapper.focusControl(name))
                return true;
        }
        return false;
    }
    function focusGrid(id, row, column, name) {
        for (let index = 0; index < repeater.count; index++) {
            const control = root.wrapperAt(index).control;
            if (control && control.focusGrid && control.focusGrid(id, row, column, name))
                return true;
        }
        return false;
    }
    function graphCommand(id, command) {
        for (let index = 0; index < repeater.count; index++) {
            const wrapper = root.wrapperAt(index), control = wrapper.control;
            if (!control)
                continue;
            if (wrapper.node.kind === "Graph") {
                if (wrapper.node.id === id)
                    return control.graphCommand(command);
                continue;
            }
            if (control.graphCommand) {
                const result = control.graphCommand(id, command);
                if (result)
                    return result;
            }
        }
        return null;
    }
    onSceneChanged: sync()
    Component.onCompleted: {
        ready = true;
        sync();
    }
    onModelsChanged: if (ready)
        Contract.validateScene(scene, models, views)
    onViewsChanged: if (ready)
        Contract.validateScene(scene, models, views)
    ListModel {
        id: items
        dynamicRoles: true
    }
    Repeater {
        id: repeater
        model: items
        delegate: Item {
            id: wrapper
            required property var definition
            readonly property var node: definition
            readonly property var frameRecordKey: node.recordKey
            readonly property var control: loader.item
            function duration(property): int {
                return node.motion && node.motion[property] && !root.effectiveTheme.suppressTransientMotion ? root.effectiveTheme[node.motion[property]] : 0;
            }
            Behavior on x {
                enabled: wrapper.duration('x') > 0
                NumberAnimation {
                    duration: wrapper.duration('x')
                    easing.type: Easing.OutCubic
                }
            }
            Behavior on width {
                enabled: wrapper.duration('width') > 0
                NumberAnimation {
                    duration: wrapper.duration('width')
                    easing.type: Easing.OutCubic
                }
            }
            x: node.x
            y: node.y
            width: node.width
            height: node.height
            visible: node.visible !== false
            function activeBrick(): var {
                return loader.item;
            }
            function focusControl(name) {
                const control = activeBrick();
                if (!control)
                    return false;
                if (node.id === name) {
                    if (control.focusEditor)
                        control.focusEditor();
                    else
                        control.forceActiveFocus();
                    return true;
                }
                return control.focusControl ? control.focusControl(name) : false;
            }
            Loader {
                anchors.fill: parent
                z: 4
                active: !!wrapper.node.dropAction && root.interactive
                enabled: !!wrapper.node.enabled
                sourceComponent: DropArea {
                    keys: ["application/x-tactic-frame"]
                    onDropped: drop => {
                        if (root.dragValue(drop.source) !== undefined) {
                            root.send(wrapper.node.dropAction, root.dragValue(drop.source));
                            drop.acceptProposedAction();
                        }
                    }
                }
            }
            Loader {
                anchors.fill: parent
                z: 5
                active: root.interactive && !!wrapper.node.enabled && wrapper.node.dragValue !== undefined && wrapper.node.dragValue !== null
                sourceComponent: FrameDragScope {
                    value: wrapper.node.dragValue
                    onStarted: root.send(wrapper.node.dragStartAction)
                }
            }
            Loader {
                id: loader
                anchors.fill: parent
                opacity: wrapper.node.opacity
                Behavior on opacity {
                    enabled: wrapper.duration('opacity') > 0
                    NumberAnimation {
                        duration: wrapper.duration('opacity')
                        easing.type: Easing.OutCubic
                    }
                }
                function brick(kind) {
                    switch (kind) {
                    case "Box":
                        return boxBrick;
                    case "Label":
                        return labelBrick;
                    case "Icon":
                        return iconBrick;
                    case "Button":
                        return buttonBrick;
                    case "Action":
                        return actionBrick;
                    case "CheckBox":
                        return checkBrick;
                    case "Field":
                        return fieldBrick;
                    case "Area":
                        return areaBrick;
                    case "Preview":
                        return previewBrick;
                    case "List":
                        return wrapper.node.fields.length ? listBrick : arrayListBrick;
                    case "Scroll":
                        return scrollBrick;
                    case "Choice":
                        return choiceBrick;
                    case "DateChoice":
                        return dateChoiceBrick;
                    case "UserChoice":
                        return userChoiceBrick;
                    case "Grid":
                        return gridBrick;
                    case "Graph":
                        return graphBrick;
                    case "Code":
                        return codeBrick;
                    case "View":
                        return viewBrick;
                    case "IconChoice":
                        return iconChoiceBrick;
                    case "ColorChoice":
                        return colorChoiceBrick;
                    case "Splitter":
                        return splitterBrick;
                    case "Switch":
                        return switchBrick;
                    default:
                        throw Error("Unsupported Tactic Frame control: " + kind);
                    }
                }
                sourceComponent: brick(wrapper.node.kind)
                Component {
                    id: boxBrick
                    Rectangle {
                        // Virtual row wrappers are private and may repeat across lists.
                        objectName: wrapper.node.recordKey === undefined ? wrapper.node.id : ""
                        color: root.color(wrapper.node.background)
                        border.width: wrapper.node.border ? wrapper.node.borderWidth || 1 : 0
                        border.color: root.color(wrapper.node.border)
                        radius: wrapper.node.radius === undefined ? root.effectiveTheme.surfaceRadius : wrapper.node.radius
                        bottomRightRadius: wrapper.node.bottomRightRadius === undefined ? radius : wrapper.node.bottomRightRadius
                        clip: true
                        FrameBranch {
                            id: boxContent
                            anchors.fill: parent
                            theme: root.effectiveTheme
                            scene: ({
                                    nodes: wrapper.node.children
                                })
                            models: root.models
                            views: root.views
                            describeRow: root.describeRow
                            describeCell: root.describeCell
                            interactive: root.interactive
                            onEvent: action => root.event(action)
                        }
                        function focusControl(name) {
                            return boxContent.focusControl(name);
                        }
                        function focusGrid(id, row, column, name) {
                            return boxContent.focusGrid(id, row, column, name);
                        }
                        function graphCommand(id, command) {
                            return boxContent.graphCommand(id, command);
                        }
                    }
                }
                Component {
                    id: labelBrick
                    Label {
                        Accessible.role: wrapper.node.role === "alert" ? Accessible.AlertMessage : wrapper.node.role === "heading" ? Accessible.Heading : Accessible.StaticText
                        objectName: wrapper.node.id
                        text: wrapper.node.text
                        textFormat: Text.PlainText
                        color: root.color(wrapper.node.color)
                        Behavior on color {
                            enabled: wrapper.duration('color') > 0
                            ColorAnimation {
                                duration: wrapper.duration('color')
                            }
                        }
                        font: root.controlFont(wrapper.node)
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: wrapper.node.align === "center" ? Text.AlignHCenter : Text.AlignLeft
                        wrapMode: wrapper.node.wrap ? Text.WordWrap : Text.NoWrap
                        maximumLineCount: wrapper.node.maxLines || 2147483647
                        elide: wrapper.node.elide === false ? Text.ElideNone : wrapper.node.maxLines ? Text.ElideRight : wrapper.node.wrap ? Text.ElideNone : Text.ElideRight
                    }
                }
                Component {
                    id: codeBrick
                    FrameCodeBranch {
                        theme: root.effectiveTheme
                        node: wrapper.node
                        controller: root.models[wrapper.node.service || "sourceEditor"]
                        onEvent: action => root.event(action)
                    }
                }
                Component {
                    id: colorChoiceBrick
                    Controls.ColorField {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        enabled: !!wrapper.node.enabled
                        value: wrapper.node.value || ""
                        onColorChosen: value => root.send(wrapper.node.action, value)
                    }
                }
                Component {
                    id: viewBrick
                    Loader {
                        objectName: wrapper.node.id
                        sourceComponent: root.views[wrapper.node.view] || null
                    }
                }
                Component {
                    id: graphBrick
                    FrameGraphBranch {
                        theme: root.effectiveTheme
                        node: wrapper.node
                        onEvent: action => root.event(action)
                    }
                }
                Component {
                    id: iconBrick
                    Controls.MaterialIcon {
                        objectName: wrapper.node.id
                        name: wrapper.node.icon || ""
                        size: wrapper.node.width
                        color: root.color(wrapper.node.color)
                        Accessible.name: wrapper.node.text
                    }
                }
                Component {
                    id: buttonBrick
                    Controls.Button {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        highlighted: !!wrapper.node.highlighted
                        destructive: !!wrapper.node.destructive
                        compact: !!wrapper.node.iconOnly
                        icon.name: wrapper.node.icon || ""
                        toolTip: wrapper.node.text
                        font: root.controlFont(wrapper.node)
                        Accessible.role: wrapper.node.radio ? Accessible.RadioButton : Accessible.Button
                        Accessible.checkable: !!wrapper.node.radio
                        Accessible.checked: !!wrapper.node.selected
                        readonly property bool radio: !!wrapper.node.radio
                        checkable: radio
                        checked: !!wrapper.node.selected
                        segmented: radio
                        focusPolicy: radio && !checked ? Qt.ClickFocus : Qt.StrongFocus
                        Keys.priority: Keys.BeforeItem
                        Keys.onPressed: event => {
                            if (root.keyboard(event.key, wrapper.node))
                                event.accepted = true;
                            else
                                event.accepted = false;
                        }
                        onClicked: root.send(wrapper.node.action)
                    }
                }
                Component {
                    id: actionBrick
                    Controls.PopupAction {
                        id: actionControl
                        objectName: wrapper.node.id
                        text: wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        padding: 0
                        property bool selected: !!wrapper.node.selected
                        property string description: wrapper.node.description || ""
                        Accessible.name: text
                        Accessible.description: description
                        Accessible.role: wrapper.node.role === "treeitem" ? Accessible.TreeItem : wrapper.node.role === "checkbox" ? Accessible.CheckBox : Accessible.Button
                        Accessible.selectable: wrapper.node.role === "treeitem"
                        Accessible.selected: !!wrapper.node.selected
                        checked: wrapper.node.checked || false
                        Accessible.checkable: wrapper.node.role === "checkbox"
                        Accessible.checked: !!wrapper.node.checked
                        keyHandler: key => root.keyboard(key, wrapper.node)
                        background: Controls.ItemSurface {
                            theme: root.effectiveTheme
                            selected: actionControl.selected
                            hovered: actionControl.hovered || actionControl.visualFocus
                            pressed: actionControl.down
                            normalColor: root.color(wrapper.node.normalColor)
                            selectedColor: root.color(wrapper.node.selectedColor)
                            railVisible: !!wrapper.node.rail
                            separatorVisible: false
                            cornerRadius: 10
                            inset: 0
                        }
                        contentItem: FrameBranch {
                            theme: root.effectiveTheme
                            scene: ({
                                    nodes: wrapper.node.children
                                })
                            interactive: false
                            enabled: false
                        }
                        onClicked: root.send(wrapper.node.action)
                    }
                }
                Component {
                    id: checkBrick
                    Controls.CheckBox {
                        id: checkControl
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        checkState: wrapper.node.mixed ? Qt.PartiallyChecked : wrapper.node.checked ? Qt.Checked : Qt.Unchecked
                        enabled: !!wrapper.node.enabled
                        padding: 0
                        topPadding: 0
                        bottomPadding: 0
                        leftPadding: 0
                        rightPadding: 0
                        indicatorOffset: wrapper.node.indicatorX || 0
                        Accessible.name: text
                        Accessible.description: wrapper.node.description || ""
                        Accessible.ignored: !root.interactive
                        Keys.onLeftPressed: event => {
                            event.accepted = root.keyboard(Qt.Key_Left, wrapper.node);
                        }
                        Keys.onRightPressed: event => {
                            event.accepted = root.keyboard(Qt.Key_Right, wrapper.node);
                        }
                        Keys.onUpPressed: event => {
                            event.accepted = root.keyboard(Qt.Key_Up, wrapper.node);
                        }
                        Keys.onDownPressed: event => {
                            event.accepted = root.keyboard(Qt.Key_Down, wrapper.node);
                        }
                        background: Controls.ItemSurface {
                            theme: root.effectiveTheme
                            selected: checkControl.checked
                            hovered: checkControl.hovered
                            pressed: checkControl.down
                            normalColor: root.color(wrapper.node.normalColor)
                            selectedColor: root.color(wrapper.node.selectedColor)
                            railVisible: false
                            separatorVisible: false
                            cornerRadius: 10
                            inset: 0
                        }
                        contentItem: FrameBranch {
                            theme: root.effectiveTheme
                            scene: ({
                                    nodes: wrapper.node.children
                                })
                            interactive: false
                            enabled: false
                        }
                        onToggled: root.send(wrapper.node.action, checked)
                    }
                }
                Component {
                    id: fieldBrick
                    Controls.TextField {
                        id: fieldControl
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        readOnly: !!wrapper.node.readOnly
                        horizontalAlignment: wrapper.node.align === "center" ? TextInput.AlignHCenter : TextInput.AlignLeft
                        tableCell: !!wrapper.node.tableCell
                        errorState: !!wrapper.node.error
                        Keys.priority: Keys.BeforeItem
                        Keys.onPressed: event => {
                            event.accepted = !fieldControl.inputMethodComposing && event.modifiers === Qt.NoModifier && root.keyboard(event.key, wrapper.node);
                        }
                        TapHandler {
                            enabled: !!wrapper.node.activateAction
                            acceptedButtons: Qt.LeftButton
                            onTapped: root.send(wrapper.node.activateAction)
                        }
                        echoMode: wrapper.node.password ? TextInput.Password : TextInput.Normal
                        placeholderText: wrapper.node.placeholder || ""
                        maximumLength: wrapper.node.maxLength || 32767
                        Accessible.name: wrapper.node.label || ""
                        font: root.controlFont(wrapper.node)
                        onActiveFocusChanged: if (activeFocus)
                            root.reveal(this)
                        onEditingFinished: root.send(wrapper.node.commitAction, text)
                        onTextEdited: root.send(wrapper.node.action, text)
                    }
                }
                Component {
                    id: areaBrick
                    ScrollView {
                        id: area
                        objectName: wrapper.node.id
                        enabled: !!wrapper.node.enabled
                        padding: 0
                        font: root.controlFont(wrapper.node)
                        contentWidth: availableWidth - 12
                        contentHeight: editor.height
                        property alias text: editor.text
                        property alias readOnly: editor.readOnly
                        property alias color: editor.color
                        function focusEditor() {
                            editor.forceActiveFocus();
                        }
                        background: Rectangle {
                            color: root.effectiveTheme.surfaceContainerHigh
                            radius: root.effectiveTheme.surfaceRadius
                            border.width: wrapper.node.notice ? 0 : editor.activeFocus ? 2 : 1
                            border.color: wrapper.node.error ? root.effectiveTheme.error : editor.activeFocus ? root.effectiveTheme.action : root.effectiveTheme.outline
                        }
                        Item {
                            width: area.availableWidth - 12
                            height: editor.height
                            Controls.TextArea {
                                id: editor
                                width: parent.width
                                height: Math.max(area.height, implicitHeight)
                                theme: root.effectiveTheme
                                readOnly: !!wrapper.node.readOnly
                                textFormat: TextEdit.PlainText
                                property string modelText: wrapper.node.text
                                onModelTextChanged: if (text !== modelText)
                                    text = modelText
                                Component.onCompleted: text = modelText
                                placeholderText: wrapper.node.placeholder || ""
                                errorState: !!wrapper.node.error
                                color: root.color(wrapper.node.color)
                                font: root.controlFont(wrapper.node)
                                Accessible.name: wrapper.node.label || ""
                                background: null
                                onActiveFocusChanged: if (activeFocus)
                                    root.reveal(area)
                                onTextChanged: if (activeFocus && !readOnly && text !== wrapper.node.text) {
                                    if (wrapper.node.maxLength && text.length > wrapper.node.maxLength)
                                        text = text.slice(0, wrapper.node.maxLength);
                                    Qt.callLater(root.send, wrapper.node.action, text);
                                }
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            objectName: wrapper.node.id + "ScrollBar"
                            theme: root.effectiveTheme
                            flickableTarget: area.contentItem
                        }
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    }
                }
                Component {
                    id: previewBrick
                    Controls.ItemPreview {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        source: wrapper.node.source || ""
                        fallbackText: wrapper.node.initials || ""
                        fallbackIcon: wrapper.node.icon || "person"
                        accent: root.color(wrapper.node.accent || "action")
                        round: wrapper.node.round !== false
                        cornerRadius: wrapper.node.radius === undefined ? (round ? width / 2 : 4) : wrapper.node.radius
                        outlined: wrapper.node.outlined !== false
                        animateAppearance: false
                        previewSize: wrapper.node.width
                        fillMode: wrapper.node.fit === "contain" ? Image.PreserveAspectFit : Image.PreserveAspectCrop
                    }
                }
                Component {
                    id: dateChoiceBrick
                    Controls.DateField {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        font: root.controlFont(wrapper.node)
                        language: wrapper.node.language || (typeof localizationController !== "undefined" ? localizationController.current_language : "en")
                        property bool textWasEdited: false
                        includeTime: !!wrapper.node.includeTime
                        allowClear: wrapper.node.allowClear !== false
                        readOnly: !!wrapper.node.readOnly
                        enabled: !!wrapper.node.enabled
                        Accessible.name: wrapper.node.label || ""
                        onTextEdited: value => {
                            textWasEdited = true;
                            root.send(wrapper.node.action, value);
                        }
                        onEditingFinished: {
                            if (textWasEdited)
                                root.send(wrapper.node.commitAction, text);
                            textWasEdited = false;
                        }
                        onAccepted: value => {
                            textWasEdited = false;
                            const canonical = includeTime ? value.replace(" ", "T").slice(0, 16) : value;
                            root.send(wrapper.node.action, canonical);
                            root.send(wrapper.node.commitAction, canonical);
                        }
                    }
                }
                Component {
                    id: userChoiceBrick
                    Forms.FrameUserChoice {
                        node: wrapper.node
                        theme: root.effectiveTheme
                        font: root.controlFont(wrapper.node)
                        enabled: !!wrapper.node.enabled
                        onEvent: action => root.send(action)
                    }
                }
                Component {
                    id: choiceBrick
                    Controls.ComboBox {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        model: wrapper.node.options || []
                        textRole: "label"
                        valueRole: "value"
                        translateDisplayText: false
                        enabled: !!wrapper.node.enabled
                        currentIndex: (wrapper.node.options || []).findIndex(item => item.value === wrapper.node.value)
                        displayText: currentIndex < 0 ? String(wrapper.node.value ?? "") : currentText
                        Accessible.name: wrapper.node.label || ""
                        font: root.controlFont(wrapper.node)
                        onActiveFocusChanged: if (activeFocus)
                            root.reveal(this)
                        onActivated: root.send(wrapper.node.action, currentValue)
                    }
                }
                Component {
                    id: switchBrick
                    Controls.Switch {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        checked: !!wrapper.node.checked
                        enabled: !!wrapper.node.enabled
                        padding: 0
                        topPadding: 0
                        bottomPadding: 0
                        leftPadding: 0
                        rightPadding: 0
                        Accessible.name: wrapper.node.text
                        onToggled: root.send(wrapper.node.action, checked)
                    }
                }
                Component {
                    id: iconChoiceBrick
                    TH.IconPickerButton {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        iconName: wrapper.node.value || ""
                        enabled: !!wrapper.node.enabled
                        tacticCompatibleOnly: !!wrapper.node.tacticCompatibleOnly
                        onIconSelected: value => root.send(wrapper.node.action, value)
                    }
                }
                Component {
                    id: splitterBrick
                    Item {
                        id: splitter
                        objectName: wrapper.node.id
                        enabled: !!wrapper.node.enabled
                        activeFocusOnTab: enabled
                        Accessible.role: Accessible.Separator
                        Accessible.name: wrapper.node.text
                        function set(value) {
                            root.send(wrapper.node.action, Math.max(wrapper.node.min, Math.min(wrapper.node.max, value)));
                        }
                        Keys.onPressed: event => {
                            if ((wrapper.node.horizontal ? event.key === Qt.Key_Up || event.key === Qt.Key_Down : event.key === Qt.Key_Left || event.key === Qt.Key_Right) || event.key === Qt.Key_Home || event.key === Qt.Key_End) {
                                set(event.key === Qt.Key_Home ? wrapper.node.min : event.key === Qt.Key_End ? wrapper.node.max : wrapper.node.value + (event.key === Qt.Key_Left || event.key === Qt.Key_Up ? -10 : 10) * (wrapper.node.reverse ? -1 : 1));
                                event.accepted = true;
                            }
                        }
                        Controls.ResizeGripVisual {
                            theme: root.effectiveTheme
                            vertical: !wrapper.node.horizontal
                            hovered: splitterMouse.containsMouse
                            pressed: splitterMouse.pressed
                        }
                        MouseArea {
                            id: splitterMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: wrapper.node.horizontal ? Qt.SplitVCursor : Qt.SplitHCursor
                            property real start: 0
                            property real value: 0
                            onPressed: mouse => {
                                start = wrapper.node.horizontal ? mapToItem(root, mouse.x, mouse.y).y : mapToItem(root, mouse.x, mouse.y).x;
                                value = wrapper.node.value;
                                splitter.forceActiveFocus();
                            }
                            onPositionChanged: mouse => {
                                if (pressed)
                                    splitter.set(value + ((wrapper.node.horizontal ? mapToItem(root, mouse.x, mouse.y).y : mapToItem(root, mouse.x, mouse.y).x) - start) * (wrapper.node.reverse ? -1 : 1));
                            }
                        }
                    }
                }
                Component {
                    id: gridBrick
                    FrameGridBranch {
                        theme: root.effectiveTheme
                        node: wrapper.node
                        sourceModel: root.models[wrapper.node.source]
                        describeCell: root.describeCell
                        onEvent: action => root.event(action)
                    }
                }
                Component {
                    id: arrayListBrick
                    FrameArrayList {
                        theme: root.effectiveTheme
                        node: wrapper.node
                        sourceRows: root.models[wrapper.node.source]
                        models: root.models
                        views: root.views
                        describeRow: root.describeRow
                        describeCell: root.describeCell
                        interactiveContent: root.interactive
                        onEvent: action => root.event(action)
                    }
                }
                Component {
                    id: listBrick
                    ListView {
                        id: list
                        property var sourceRows: root.models[wrapper.node.source]
                        objectName: wrapper.node.id
                        model: sourceRows
                        clip: true
                        spacing: 4
                        reuseItems: true
                        boundsBehavior: Flickable.StopAtBounds
                        delegate: FrameBranch {
                            required property var model
                            required property int index
                            readonly property var record: {
                                const value = {};
                                for (const field of wrapper.node.fields)
                                    value[field] = model[field];
                                return value[wrapper.node.keyField] === undefined || value[wrapper.node.keyField] === null ? null : value;
                            }
                            width: list.width - 16
                            height: Contract.listRowHeight(wrapper.node)
                            theme: root.effectiveTheme
                            models: root.models
                            views: root.views
                            describeRow: root.describeRow
                            describeCell: root.describeCell
                            scene: record ? root.describeRow(wrapper.node, record) : ({
                                    nodes: []
                                })
                            interactive: root.interactive
                            onEvent: action => root.event(action)
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            objectName: wrapper.node.scrollbarId || ""
                            theme: root.effectiveTheme
                            flickableTarget: list
                        }
                    }
                }
                Component {
                    id: scrollBrick
                    Flickable {
                        id: scrollView
                        objectName: wrapper.node.id
                        clip: true
                        contentWidth: width
                        contentHeight: wrapper.node.contentHeight
                        property var resetKey: wrapper.node.resetKey
                        onResetKeyChanged: contentY = 0
                        boundsBehavior: Flickable.StopAtBounds
                        FrameBranch {
                            id: scrollContent
                            width: scrollView.width
                            height: scrollView.contentHeight
                            theme: root.effectiveTheme
                            scene: ({
                                    nodes: wrapper.node.children
                                })
                            models: root.models
                            views: root.views
                            describeRow: root.describeRow
                            describeCell: root.describeCell
                            interactive: root.interactive
                            onEvent: action => root.event(action)
                        }
                        function focusControl(name) {
                            return scrollContent.focusControl(name);
                        }
                        function focusGrid(id, row, column, name) {
                            return scrollContent.focusGrid(id, row, column, name);
                        }
                        function graphCommand(id, command) {
                            return scrollContent.graphCommand(id, command);
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            objectName: wrapper.node.scrollbarId || ""
                            theme: root.effectiveTheme
                            flickableTarget: scrollView
                        }
                    }
                }
            }
        }
    }
}
