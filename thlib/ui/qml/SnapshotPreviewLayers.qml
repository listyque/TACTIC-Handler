import QtQuick
import "controls" as Controls

Item {
    id: root
    required property var theme
    property url currentUrl: ""
    property url outgoingUrl: ""
    property int transitionDirection: 1

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
            fillMode: Image.PreserveAspectFit
            round: false
            cornerRadius: root.theme.itemRadius
            animateAppearance: false
            effectsEnabled: false
            decodeAtItemSize: false
        }
    }
    Item {
        id: incomingLayer
        objectName: "snapshotIncomingPreviewLayer"
        anchors.fill: parent
        Controls.ItemPreview {
            objectName: "snapshotIncomingPreview"
            anchors.fill: parent
            theme: root.theme
            source: root.currentUrl
            fallbackIcon: "movie"
            accent: root.theme.surfaceContainerHigh
            fillMode: Image.PreserveAspectFit
            round: false
            cornerRadius: root.theme.itemRadius
            animateAppearance: false
            effectsEnabled: false
            decodeAtItemSize: false
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
