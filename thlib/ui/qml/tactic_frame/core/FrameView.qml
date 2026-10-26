pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
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
    signal event(var action, var source)
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
            letterSpacing: definition.letterSpacing || 0,
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
    function send(action, value, source) {
        if (!action || !interactive)
            return;
        root.event(Object.assign({}, action, value === undefined ? {} : {
            value: value
        }), source || null);
    }
    function keyboard(key, definition) {
        const keys = {};
        keys[Qt.Key_Return] = "Enter";
        keys[Qt.Key_Enter] = "Enter";
        keys[Qt.Key_F2] = "F2";
        keys[Qt.Key_Backtab] = "Backtab";
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
    function focusListRow(id, row, controlId) {
        for (let index = 0; index < repeater.count; index++) {
            const wrapper = root.wrapperAt(index), control = wrapper ? wrapper.control : null;
            if (control && control.focusListRow && control.focusListRow(id, row, controlId))
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
            scale: node.scale === undefined ? 1 : node.scale
            transformOrigin: Item.TopLeft
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
                    keys: wrapper.node.dropAction && wrapper.node.dropAction.name === "file-ingest" ? [] : ["application/x-tactic-frame"]
                    onDropped: drop => {
                        if (wrapper.node.dropAction && wrapper.node.dropAction.name === "file-ingest" && drop.hasUrls) {
                            root.send(wrapper.node.dropAction, Array.from(drop.urls, url => String(url)));
                            drop.acceptProposedAction();
                        } else if (root.dragValue(drop.source) !== undefined) {
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
                        return wrapper.node.tab ? tabBrick : wrapper.node.filledAction ? filledActionBrick : wrapper.node.iconAction ? iconActionBrick : buttonBrick;
                    case "Action":
                        return actionBrick;
                    case "CheckBox":
                        return checkBrick;
                    case "Field":
                        return fieldBrick;
                    case "Area":
                        return areaBrick;
                    case "SummaryChip":
                        return summaryChipBrick;
                    case "Segmented":
                        return segmentedBrick;
                    case "StatusChip":
                        return statusChipBrick;
                    case "Preview":
                        return previewBrick;
                    case "List":
                        // JS/QVariant arrays have snapshots, not native model-role lifetimes.
                        const rows = root.models[wrapper.node.source];
                        return wrapper.node.fields.length && !(rows && typeof rows.length === "number") ? listBrick : arrayListBrick;
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
                        radius: wrapper.node.radiusRole ? root.effectiveTheme[wrapper.node.radiusRole] : wrapper.node.radius === undefined ? root.effectiveTheme.surfaceRadius : wrapper.node.radius
                        bottomRightRadius: wrapper.node.bottomRightRadius === undefined ? radius : wrapper.node.bottomRightRadius
                        clip: true
                        TapHandler {
                            acceptedButtons: Qt.RightButton
                            enabled: !!wrapper.node.contextAction && root.interactive
                            onTapped: point => root.send(wrapper.node.contextAction, {
                                    x: point.position.x,
                                    y: point.position.y
                                }, parent)
                        }
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
                            onEvent: (action, source) => root.event(action, source)
                        }
                        function focusControl(name) {
                            return boxContent.focusControl(name);
                        }
                        function focusListRow(id, row, controlId) {
                            return boxContent.focusListRow(id, row, controlId);
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
                        id: labelControl
                        property bool tipDismissed: false
                        activeFocusOnTab: !!wrapper.node.focusable
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
                        horizontalAlignment: wrapper.node.align === "center" ? Text.AlignHCenter : wrapper.node.align === "right" ? Text.AlignRight : Text.AlignLeft
                        wrapMode: wrapper.node.wrapAnywhere ? Text.WrapAnywhere : wrapper.node.wrap ? Text.WordWrap : Text.NoWrap
                        maximumLineCount: wrapper.node.maxLines || 2147483647
                        elide: wrapper.node.elide === false ? Text.ElideNone : wrapper.node.elideMiddle ? Text.ElideMiddle : wrapper.node.maxLines ? Text.ElideRight : wrapper.node.wrap ? Text.ElideNone : Text.ElideRight

                        onActiveFocusChanged: tipDismissed = false
                        Keys.onEscapePressed: event => {
                            if (infoTip.item && infoTip.item.visible) {
                                tipDismissed = true;
                                event.accepted = true;
                            } else
                                event.accepted = false;
                        }
                        HoverHandler {
                            id: infoHover
                            enabled: !!(wrapper.node.toolTip)
                            onHoveredChanged: if (hovered)
                                labelControl.tipDismissed = false
                        }
                        Loader {
                            id: infoTip
                            active: !!(wrapper.node.toolTip) && (infoHover.hovered || labelControl.activeFocus) && !labelControl.tipDismissed
                            sourceComponent: Controls.ToolTip {
                                theme: root.effectiveTheme
                                parent: labelControl
                                text: wrapper.node.toolTip || ""
                                visible: true
                            }
                        }
                    }
                }
                Component {
                    id: codeBrick
                    FrameCodeBranch {
                        theme: root.effectiveTheme
                        node: wrapper.node
                        controller: root.models[wrapper.node.service || "sourceEditor"]
                        onEvent: action => root.event(action, null)
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
                        sourceComponent: root.views[wrapper.node.view] ? (root.views[wrapper.node.view].component || root.views[wrapper.node.view]) : null
                        onLoaded: {
                            if (root.views[wrapper.node.view] && root.views[wrapper.node.view].nodeProps)
                                item.frameNode = Qt.binding(() => wrapper.node);
                        }
                    }
                }
                Component {
                    id: graphBrick
                    FrameGraphBranch {
                        theme: root.effectiveTheme
                        node: wrapper.node
                        onEvent: action => root.event(action, null)
                    }
                }
                Component {
                    id: iconBrick
                    Controls.MaterialIcon {
                        id: iconControl
                        property bool tipDismissed: false
                        activeFocusOnTab: !!wrapper.node.focusable
                        objectName: wrapper.node.id
                        name: wrapper.node.icon || ""
                        size: wrapper.node.width
                        color: root.color(wrapper.node.color)
                        Accessible.name: wrapper.node.text

                        onActiveFocusChanged: tipDismissed = false
                        Keys.onEscapePressed: event => {
                            if (infoTip.item && infoTip.item.visible) {
                                tipDismissed = true;
                                event.accepted = true;
                            } else
                                event.accepted = false;
                        }
                        HoverHandler {
                            id: infoHover
                            enabled: !!(wrapper.node.toolTip || wrapper.node.text)
                            onHoveredChanged: if (hovered)
                                iconControl.tipDismissed = false
                        }
                        Loader {
                            id: infoTip
                            active: !!(wrapper.node.toolTip || wrapper.node.text) && (infoHover.hovered || iconControl.activeFocus) && !iconControl.tipDismissed
                            sourceComponent: Controls.ToolTip {
                                theme: root.effectiveTheme
                                parent: iconControl
                                text: wrapper.node.toolTip || wrapper.node.text || ""
                                visible: true
                            }
                        }
                    }
                }
                Component {
                    id: filledActionBrick
                    Controls.FilledActionButton {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        iconName: wrapper.node.icon || ""
                        compact: !!wrapper.node.iconOnly
                        text: wrapper.node.text
                        toolTip: wrapper.node.label || wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        Accessible.name: wrapper.node.label || wrapper.node.text
                        onPressed: root.send(wrapper.node.pressAction, undefined, this)
                        onClicked: root.send(wrapper.node.action, undefined, this)
                    }
                }
                Component {
                    id: iconActionBrick
                    Controls.CompactIconButton {
                        id: iconActionControl
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        iconName: wrapper.node.icon || ""
                        iconSize: wrapper.node.iconSize || 17
                        iconColor: root.color(wrapper.node.iconColor || (wrapper.node.highlighted ? "selectedText" : "primaryText"))
                        backgroundColor: wrapper.node.highlighted ? (enabled ? root.effectiveTheme.action : root.effectiveTheme.surfaceContainerHigh) : "transparent"
                        badgeCount: wrapper.node.badgeCount || 0
                        toolTip: wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        Accessible.name: wrapper.node.label || wrapper.node.text
                        round: !!wrapper.node.round
                        onPressed: root.send(wrapper.node.pressAction, undefined, iconActionControl)
                        onClicked: root.send(wrapper.node.action, undefined, iconActionControl)
                    }
                }
                Component {
                    id: segmentedBrick
                    Controls.SegmentedButton {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        model: wrapper.node.options || []
                        currentValue: wrapper.node.value || ""
                        segmentObjectNamePrefix: wrapper.node.id + "_"
                        iconOnly: !!wrapper.node.iconOnly
                        enabled: !!wrapper.node.enabled
                        Accessible.name: wrapper.node.label || ""
                        onActivated: value => root.send(wrapper.node.action, value)
                    }
                }
                Component {
                    id: tabBrick
                    Controls.TabButton {
                        id: tabControl
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        checked: !!wrapper.node.selected
                        enabled: !!wrapper.node.enabled
                        font: root.controlFont(wrapper.node)
                        Accessible.name: wrapper.node.label || wrapper.node.text
                        onClicked: root.send(wrapper.node.action, undefined, tabControl)
                    }
                }
                Component {
                    id: buttonBrick
                    Controls.Button {
                        id: buttonControl
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        highlighted: !!wrapper.node.highlighted
                        destructive: !!wrapper.node.destructive
                        tonal: !!wrapper.node.tonal
                        compact: !!wrapper.node.iconOnly
                        icon.name: wrapper.node.icon || ""
                        iconSize: wrapper.node.iconSize || 0
                        toolTip: wrapper.node.text
                        font: root.controlFont(wrapper.node)
                        Accessible.name: wrapper.node.label || wrapper.node.text
                        Accessible.role: wrapper.node.radio ? Accessible.RadioButton : Accessible.Button
                        Accessible.checkable: !!wrapper.node.radio
                        Accessible.checked: !!wrapper.node.selected
                        readonly property bool radio: !!wrapper.node.radio
                        checkable: radio
                        checked: !!wrapper.node.selected
                        segmented: radio
                        focusPolicy: wrapper.node.retainFocus ? Qt.TabFocus : radio && !checked ? Qt.ClickFocus : Qt.StrongFocus
                        Keys.priority: Keys.BeforeItem
                        Keys.onPressed: event => {
                            if (root.keyboard(event.key, wrapper.node))
                                event.accepted = true;
                            else
                                event.accepted = false;
                        }
                        onPressed: root.send(wrapper.node.pressAction, undefined, buttonControl)
                        onClicked: root.send(wrapper.node.action, undefined, buttonControl)
                    }
                }
                Component {
                    id: actionBrick
                    Controls.PopupAction {
                        id: actionControl
                        property bool tipDismissed: false
                        objectName: wrapper.node.id
                        text: wrapper.node.text
                        enabled: !!wrapper.node.enabled
                        padding: 0
                        property bool selected: !!wrapper.node.selected
                        property string description: wrapper.node.description || ""
                        Accessible.name: text
                        Accessible.description: description
                        Accessible.role: wrapper.node.role === "treeitem" ? Accessible.TreeItem : wrapper.node.role === "checkbox" ? Accessible.CheckBox : wrapper.node.role === "option" ? Accessible.ListItem : Accessible.Button
                        Accessible.selectable: wrapper.node.role === "treeitem" || wrapper.node.role === "option"
                        Accessible.selected: !!wrapper.node.selected
                        checked: wrapper.node.checked || false
                        Accessible.checkable: wrapper.node.role === "checkbox"
                        Accessible.checked: !!wrapper.node.checked
                        keyHandler: key => root.keyboard(key, wrapper.node)
                        background: Controls.ItemSurface {
                            theme: root.effectiveTheme
                            selected: actionControl.selected
                            accent: root.color(wrapper.node.accent || "action")
                            hovered: actionControl.hovered || actionControl.visualFocus
                            pressed: actionControl.down
                            normalColor: root.color(wrapper.node.normalColor)
                            selectedColor: root.color(wrapper.node.selectedColor)
                            railVisible: !!wrapper.node.rail
                            separatorVisible: false
                            cornerRadius: wrapper.node.radius === undefined ? 10 : wrapper.node.radius
                            inset: 0
                        }
                        contentItem: FrameBranch {
                            theme: root.effectiveTheme
                            scene: ({
                                    nodes: wrapper.node.children
                                })
                            interactive: false
                            models: root.models
                            views: root.views
                            describeRow: root.describeRow
                            describeCell: root.describeCell
                            enabled: false
                        }
                        onPressed: root.send(wrapper.node.pressAction, undefined, actionControl)
                        onClicked: root.send(wrapper.node.action, undefined, actionControl)
                        onDoubleClicked: root.send(wrapper.node.doubleAction)

                        onActiveFocusChanged: tipDismissed = false
                        Keys.onEscapePressed: event => {
                            if (infoTip.item && infoTip.item.visible) {
                                tipDismissed = true;
                                event.accepted = true;
                            } else
                                event.accepted = false;
                        }
                        HoverHandler {
                            id: infoHover
                            enabled: !!(wrapper.node.toolTip)
                            onHoveredChanged: if (hovered)
                                actionControl.tipDismissed = false
                        }
                        Loader {
                            id: infoTip
                            active: !!(wrapper.node.toolTip) && (infoHover.hovered || actionControl.activeFocus) && !actionControl.tipDismissed
                            sourceComponent: Controls.ToolTip {
                                theme: root.effectiveTheme
                                parent: actionControl
                                text: wrapper.node.toolTip || ""
                                visible: true
                            }
                        }
                    }
                }
                Component {
                    id: checkBrick
                    Controls.CheckBox {
                        id: checkControl
                        onActiveFocusChanged: if (activeFocus)
                            root.reveal(checkControl)
                        compact: !!wrapper.node.compact
                        prominent: !!wrapper.node.prominent
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
                        Accessible.name: wrapper.node.label || text || ""
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
                        contentItem: Item {
                            Label {
                                objectName: "frameCheckBoxCaption_" + checkControl.objectName
                                anchors.fill: parent
                                visible: !wrapper.node.children || !wrapper.node.children.length
                                leftPadding: checkControl.indicatorOffset + checkControl.indicator.width + checkControl.spacing
                                text: checkControl.text
                                font: checkControl.font
                                color: checkControl.enabled ? root.effectiveTheme.primaryText : root.effectiveTheme.disabledText
                                verticalAlignment: Text.AlignVCenter
                                elide: wrapper.node.wrapText ? Text.ElideNone : Text.ElideRight
                                wrapMode: wrapper.node.wrapText ? Text.Wrap : Text.NoWrap
                            }
                            FrameBranch {
                                anchors.fill: parent
                                theme: root.effectiveTheme
                                scene: ({
                                        nodes: wrapper.node.children
                                    })
                                interactive: false
                                enabled: false
                            }
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
                        Binding {
                            target: fieldControl
                            property: "leftPadding"
                            value: Number(wrapper.node.paddingLeft || 0)
                            when: wrapper.node.paddingLeft !== undefined
                            restoreMode: Binding.RestoreBindingOrValue
                        }
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
                        onActiveFocusChanged: if (activeFocus) {
                            root.reveal(this);
                            if (wrapper.node.selectOnFocus)
                                Qt.callLater(function () {
                                    if (fieldControl.activeFocus)
                                        fieldControl.selectAll();
                                });
                        }
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
                        contentWidth: wrapper.node.wrap === false ? Math.max(availableWidth - 12, editor.contentWidth + editor.leftPadding + editor.rightPadding) : availableWidth - 12
                        contentHeight: editor.height
                        property alias text: editor.text
                        property alias readOnly: editor.readOnly
                        property alias color: editor.color
                        function focusEditor() {
                            editor.forceActiveFocus();
                        }
                        background: Rectangle {
                            color: wrapper.node.flat ? "transparent" : root.effectiveTheme.surfaceContainerHigh
                            radius: root.effectiveTheme.surfaceRadius
                            border.width: wrapper.node.flat || wrapper.node.notice ? 0 : editor.activeFocus ? 2 : 1
                            border.color: wrapper.node.error ? root.effectiveTheme.error : editor.activeFocus ? root.effectiveTheme.action : root.effectiveTheme.outline
                        }
                        Item {
                            width: area.contentWidth
                            height: editor.height
                            Controls.TextArea {
                                id: editor
                                width: parent.width
                                height: Math.max(area.height, implicitHeight)
                                theme: root.effectiveTheme
                                readOnly: !!wrapper.node.readOnly
                                wrapMode: wrapper.node.wrap === false ? TextEdit.NoWrap : TextEdit.Wrap
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
                                Keys.priority: Keys.BeforeItem
                                Keys.onPressed: event => {
                                    if (wrapper.node.sendOnEnter && (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) && event.modifiers === Qt.NoModifier && !inputMethodComposing && !event.isAutoRepeat) {
                                        root.send(wrapper.node.action, text);
                                        root.send(wrapper.node.sendAction);
                                        event.accepted = true;
                                    }
                                }
                            }
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            objectName: wrapper.node.id + "ScrollBar"
                            theme: root.effectiveTheme
                            flickableTarget: area.contentItem
                        }
                        ScrollBar.horizontal: Controls.ScrollBar {
                            theme: root.effectiveTheme
                            policy: wrapper.node.wrap === false ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
                            flickableTarget: area.contentItem
                        }
                    }
                }
                Component {
                    id: statusChipBrick
                    Controls.StatusChip {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        text: wrapper.node.text
                        iconName: wrapper.node.icon || ""
                        accentColor: root.color(wrapper.node.accent || "secondaryText")
                        dense: !!wrapper.node.dense
                        interactive: !!wrapper.node.action
                        enabled: !!wrapper.node.enabled
                        onClicked: root.send(wrapper.node.action)
                    }
                }
                Component {
                    id: summaryChipBrick
                    Controls.SummaryChip {
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        label: wrapper.node.text
                        count: wrapper.node.count || 0
                        accent: root.color(wrapper.node.accent || "action")
                        iconName: wrapper.node.icon || ""
                        compact: !!wrapper.node.compact
                        clickable: !!wrapper.node.action
                        enabled: !!wrapper.node.enabled
                        showCount: wrapper.node.showCount !== false
                        showDot: wrapper.node.showDot !== false
                        onClicked: root.send(wrapper.node.action)
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
                        selected: !!wrapper.node.selected
                        loading: !!wrapper.node.loading
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
                        monthOnly: !!wrapper.node.monthOnly
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
                        id: choice
                        objectName: wrapper.node.id
                        theme: root.effectiveTheme
                        // Replacing an unchanged model makes Qt reset an in-progress edit.
                        property string optionsJson: JSON.stringify(wrapper.node.options || [])
                        model: JSON.parse(optionsJson)
                        textRole: "label"
                        valueRole: "value"
                        iconRole: "icon"
                        editable: !!wrapper.node.editable
                        editText: String(wrapper.node.value ?? "")
                        placeholderText: wrapper.node.placeholder || ""
                        onTextEdited: value => root.send(wrapper.node.action, value)
                        onAccepted: root.send(wrapper.node.commitAction, editText)
                        translateDisplayText: false
                        enabled: !!wrapper.node.enabled
                        Binding {
                            target: choice
                            property: "currentIndex"
                            delayed: true
                            value: choice.editable ? -1 : (wrapper.node.options || []).findIndex(item => item.value === wrapper.node.value)
                        }
                        displayText: currentIndex < 0 ? String(wrapper.node.value ?? "") : (wrapper.node.displayPrefix || "") + currentText
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
                        Controls.ToolTip {
                            theme: root.effectiveTheme
                            visible: parent.hovered && !!wrapper.node.toolTip && !root.effectiveTheme.suppressToolTips
                            text: wrapper.node.toolTip || ""
                        }
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
                        readonly property var ownerWindow: splitter.Window.window
                        objectName: wrapper.node.id
                        enabled: !!wrapper.node.enabled
                        activeFocusOnTab: enabled
                        Accessible.role: Accessible.Separator
                        Accessible.name: wrapper.node.text
                        function set(value, commit) {
                            const action = commit && wrapper.node.commitAction ? wrapper.node.commitAction : wrapper.node.action;
                            root.send(action, Math.max(wrapper.node.min, Math.min(wrapper.node.max, value)));
                        }
                        Keys.onPressed: event => {
                            if ((wrapper.node.horizontal ? event.key === Qt.Key_Up || event.key === Qt.Key_Down : event.key === Qt.Key_Left || event.key === Qt.Key_Right) || event.key === Qt.Key_Home || event.key === Qt.Key_End) {
                                set(event.key === Qt.Key_Home ? wrapper.node.min : event.key === Qt.Key_End ? wrapper.node.max : wrapper.node.value + (event.key === Qt.Key_Left || event.key === Qt.Key_Up ? -10 : 10) * (wrapper.node.reverse ? -1 : 1), true);
                                event.accepted = true;
                            }
                        }
                        Controls.ResizeGripVisual {
                            theme: root.effectiveTheme
                            vertical: !wrapper.node.horizontal
                            hovered: splitterMouse.containsMouse
                            pressed: splitterMouse.pressed
                        }
                        Connections {
                            id: splitterWindow
                            target: splitter.ownerWindow
                            function onVisibleChanged() {
                                if (splitter.ownerWindow && !splitter.ownerWindow.visible)
                                    splitterMouse.cancelResize();
                            }
                            function onActiveChanged() {
                                if (splitter.ownerWindow && !splitter.ownerWindow.active)
                                    splitterMouse.cancelResize();
                            }
                        }
                        MouseArea {
                            id: splitterMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: wrapper.node.horizontal ? Qt.SplitVCursor : Qt.SplitHCursor
                            property real start: 0
                            property real value: 0
                            property bool resizing: false
                            function cancelResize() {
                                if (!resizing)
                                    return;
                                resizing = false;
                                if (root && wrapper && wrapper.node.cancelAction)
                                    root.send(wrapper.node.cancelAction, value);
                            }
                            onPressed: mouse => {
                                resizing = true;
                                start = wrapper.node.horizontal ? mapToItem(root, mouse.x, mouse.y).y : mapToItem(root, mouse.x, mouse.y).x;
                                value = wrapper.node.value;
                                splitter.forceActiveFocus();
                            }
                            function positionValue(mouse) {
                                return value + ((wrapper.node.horizontal ? mapToItem(root, mouse.x, mouse.y).y : mapToItem(root, mouse.x, mouse.y).x) - start) * (wrapper.node.reverse ? -1 : 1);
                            }
                            onPositionChanged: mouse => {
                                if (pressed && resizing)
                                    splitter.set(positionValue(mouse), false);
                            }
                            onReleased: mouse => {
                                if (resizing && wrapper.node.commitAction)
                                    splitter.set(positionValue(mouse), true);
                                resizing = false;
                            }
                            onCanceled: cancelResize()
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
                        onEvent: action => root.event(action, null)
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
                        onEvent: (action, source) => root.event(action, source)
                    }
                }
                Component {
                    id: listBrick
                    ListView {
                        id: list
                        property var sourceRows: root.models[wrapper.node.source]
                        Accessible.name: wrapper.node.label || ""
                        objectName: wrapper.node.id
                        model: sourceRows
                        function focusControl(name) {
                            for (const item of contentItem.children)
                                if (item.focusControl && item.focusControl(name))
                                    return true;
                            return false;
                        }
                        function focusListRow(id, row, controlId) {
                            if (id !== wrapper.node.id || row < 0 || row >= count)
                                return false;
                            contentY = Contract.revealListOffset(contentY, row, height, count, wrapper.node.rowHeight, wrapper.node.rowGap === undefined ? 4 : wrapper.node.rowGap);
                            forceLayout();
                            Qt.callLater(() => root.focusControl(controlId));
                            return true;
                        }
                        clip: true
                        spacing: wrapper.node.rowGap === undefined ? 4 : wrapper.node.rowGap
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
                            scene: record ? root.describeRow(wrapper.node, record, index) : ({
                                    nodes: []
                                })
                            interactive: root.interactive
                            onEvent: (action, source) => root.event(action, source)
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
                        contentWidth: Math.max(width, wrapper.node.contentWidth || width)
                        contentHeight: wrapper.node.contentHeight
                        property var resetKey: wrapper.node.resetKey
                        onResetKeyChanged: contentY = 0
                        boundsBehavior: Flickable.StopAtBounds
                        FrameBranch {
                            id: scrollContent
                            width: scrollView.contentWidth
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
                            onEvent: (action, source) => root.event(action, source)
                        }
                        ScrollBar.horizontal: Controls.ScrollBar {
                            theme: root.effectiveTheme
                            flickableTarget: scrollView
                        }
                        function focusControl(name) {
                            return scrollContent.focusControl(name);
                        }
                        function focusListRow(id, row, controlId) {
                            return scrollContent.focusListRow(id, row, controlId);
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
