pragma Singleton

import QtQuick

QtObject {
    id: root

    property var pendingOwner: null

    function schedule(owner, delay) {
        if (!owner)
            return
        if (pendingOwner && pendingOwner !== owner)
            pendingOwner.releaseControlHover()
        pendingOwner = owner
        releaseTimer.interval = Math.max(0, Number(delay || 0))
        releaseTimer.restart()
    }

    function cancel(owner) {
        if (pendingOwner !== owner)
            return
        releaseTimer.stop()
        pendingOwner = null
    }

    property Timer releaseTimer: Timer {
        onTriggered: {
            const owner = root.pendingOwner
            root.pendingOwner = null
            if (owner)
                owner.releaseControlHover()
        }
    }
}
