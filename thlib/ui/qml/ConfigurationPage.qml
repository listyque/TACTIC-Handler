import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: page

    required property var theme
    required property string pageId
    property bool managed: false
    readonly property var dccSchema: configurationController.page_schema(pageId)

    Loader {
        anchors.fill: parent
        sourceComponent: page.pageId === "server" ? serverForm
            : page.pageId === "repository" ? repositoryForm
            : page.pageId === "project" ? projectForm
            : page.pageId === "checkin_preferences" ? checkinOptionsPageForm
            : page.pageId === "global_preferences" ? globalPreferencesForm
            : page.pageId === "appearance" ? appearanceForm
            : page.pageId === "cache" ? cacheForm
            : page.pageId === "tasks_preferences" ? taskPreferencesForm
            : Object.keys(page.dccSchema).length ? dccPreferencesForm
            : null
    }

    Component {
        id: checkinOptionsPageForm
        CheckinOptionsPage { theme: page.theme; managed: page.managed }
    }

    Component {
        id: serverForm
        ConfigurationServerPage {
            theme: page.theme
            managed: page.managed
        }
    }
    Component {
        id: repositoryForm
        ConfigurationRepositoryPage { theme: page.theme }
    }
    Component {
        id: projectForm
        ConfigurationProjectPage {
            theme: page.theme
        }
    }

    Component {
        id: globalPreferencesForm
        ConfigurationGlobalPreferencesPage {
            theme: page.theme
            managed: page.managed
        }
    }

    Component {
        id: taskPreferencesForm
        ConfigurationTaskPreferencesPage {
            theme: page.theme
            managed: page.managed
        }
    }

    Component {
        id: cacheForm
        ConfigurationCachePage {
            theme: page.theme
            managed: page.managed
        }
    }

    Component {
        id: appearanceForm
        ConfigurationAppearancePage {
            theme: page.theme
            managed: page.managed
        }
    }

    Component {
        id: dccPreferencesForm
        ConfigurationDccPage {
            theme: page.theme
            managed: page.managed
            pageId: page.pageId
        }
    }
}
