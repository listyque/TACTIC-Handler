pragma Singleton

import QtQuick

QtObject {
    property var activeMenu: null

    function activate(menu) {
        if (activeMenu && activeMenu !== menu && activeMenu.opened)
            activeMenu.close()
        activeMenu = menu
    }

    function release(menu) {
        if (activeMenu === menu)
            activeMenu = null
    }
}
