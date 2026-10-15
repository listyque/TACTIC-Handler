import QtQuick
import "controls" as Controls

Item {
    id: root
    required property var theme
    property url currentUrl: ""
    property url currentQualityUrl: ""
    property bool currentQualityRequested: false
    property string currentToken: ""
    property url outgoingUrl: ""
    property int transitionDirection: 1
    property string viewMode: "fit"
    property real devicePixelRatio: Screen.devicePixelRatio
    readonly property url activeUrl: {
        const quality = String(currentQualityUrl || "")
        return quality.length > 0
                && quality.indexOf("pending-preview:") !== 0
            ? currentQualityUrl : currentUrl
    }
    signal qualityRequested(string token)

    function requestQualityIfNeeded() {
        if (currentQualityRequested || !currentToken
                || incomingPreview.sourcePixelWidth <= 0
                || incomingPreview.sourcePixelHeight <= 0)
            return
        const horizontalScale = width * devicePixelRatio
            / incomingPreview.sourcePixelWidth
        const verticalScale = height * devicePixelRatio
            / incomingPreview.sourcePixelHeight
        const scale = viewMode === "fill"
            ? Math.max(horizontalScale, verticalScale)
            : Math.min(horizontalScale, verticalScale)
        if (scale > 1)
            qualityRequested(currentToken)
    }

    function settle() {
        carouselTransition.stop()
        incomingLayer.x = 0
        incomingLayer.opacity = 1
        outgoingLayer.x = 0
        outgoingLayer.opacity = 0
    }

    function startTransition() {
        incomingLayer.x = root.transitionDirection
            * Math.max(36, root.width * 0.18)
        incomingLayer.opacity = 0
        outgoingLayer.x = 0
        outgoingLayer.opacity = 1
        carouselTransition.restart()
    }

    onWidthChanged: requestQualityIfNeeded()
    onHeightChanged: requestQualityIfNeeded()
    onDevicePixelRatioChanged: requestQualityIfNeeded()
    onViewModeChanged: requestQualityIfNeeded()
    onCurrentUrlChanged: Qt.callLater(requestQualityIfNeeded)
    onCurrentTokenChanged: Qt.callLater(requestQualityIfNeeded)

    Item {
        id: outgoingLayer
        objectName: "snapshotOutgoingPreviewLayer"
        anchors.fill: parent
        opacity: 0
        Controls.ItemPreview {
            objectName: "snapshotOutgoingPreview"
            anchors.fill: parent
            theme: root.theme
            source: root.outgoingUrl
            fallbackIcon: "movie"
            accent: root.theme.surfaceContainerHigh
            fillMode: root.viewMode === "fill"
                ? Image.PreserveAspectCrop : Image.PreserveAspectFit
            round: false
            cornerRadius: root.theme.itemRadius
            animateAppearance: false
            effectsEnabled: false
            readyBorderEnabled: false
            decodeAtItemSize: false
        }
    }
    Item {
        id: incomingLayer
        objectName: "snapshotIncomingPreviewLayer"
        anchors.fill: parent
        Controls.ItemPreview {
            id: incomingPreview
            objectName: "snapshotIncomingPreview"
            anchors.fill: parent
            theme: root.theme
            source: root.activeUrl
            fallbackIcon: "movie"
            accent: root.theme.surfaceContainerHigh
            fillMode: root.viewMode === "fill"
                ? Image.PreserveAspectCrop : Image.PreserveAspectFit
            round: false
            cornerRadius: root.theme.itemRadius
            animateAppearance: false
            effectsEnabled: false
            readyBorderEnabled: false
            decodeAtItemSize: false
            onImageReady: root.requestQualityIfNeeded()
        }
    }

    ParallelAnimation {
        id: carouselTransition
        objectName: "snapshotCarouselTransition"
        NumberAnimation {
            target: incomingLayer
            property: "x"
            to: 0
            duration: root.theme.motionExtended
            easing.type: Easing.OutExpo
        }
        NumberAnimation {
            target: incomingLayer
            property: "opacity"
            to: 1
            duration: root.theme.motionSlow
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: outgoingLayer
            property: "x"
            to: -root.transitionDirection * Math.max(36, root.width * 0.18)
            duration: root.theme.motionExtended
            easing.type: Easing.OutExpo
        }
        NumberAnimation {
            target: outgoingLayer
            property: "opacity"
            to: 0
            duration: root.theme.motionSlow
            easing.type: Easing.OutCubic
        }
    }
}
