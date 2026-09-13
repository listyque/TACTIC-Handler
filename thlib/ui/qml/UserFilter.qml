import QtQuick
import QtQml.Models
import "UserSearch.js" as UserSearch

SortFilterProxyModel {
    id: root

    property string searchText: ""
    property var excludedLogins: []

    onSearchTextChanged: invalidate()
    onExcludedLoginsChanged: invalidate()
    filters: FunctionFilter {
        column: 0
        component RoleData: QtObject {
            property string login
            property string displayName
            property var groups
        }
        function filter(data: RoleData): bool {
            if (root.excludedLogins.indexOf(data.login) >= 0)
                return false
            return UserSearch.matches(data.login, data.displayName, data.groups, root.searchText)
        }
    }
}
