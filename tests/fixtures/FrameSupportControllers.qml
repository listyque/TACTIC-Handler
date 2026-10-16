import QtQuick

Item {
    QtObject {
        objectName: "userController"
        signal stateChanged()
        signal profileSaved()
        property bool directoryVisible: true
        property bool canManageUsers: true
        property bool editingBusy: false
        property bool busy: false
        property bool tasksBusy: false
        property bool canEdit: true
        property string editingError: ""
        property string error: ""
        property string activityError: ""
        property string login: "artist"
        property bool canViewWorkHours: true
        property var profile: ({login:"artist",displayName:"Alice Artist",initials:"AA",avatarColor:"#ad4242",avatarUrl:"",current:true,
            firstName:"Alice",lastName:"Artist",phoneNumber:"100",address:"Studio 4",department:"Art",email:"alice@example.test",
            project:"CG",server:"tactic.example.test",groups:[{code:"artists",label:"Artists"}],roles:["artist"],presenceKnown:true,online:true})
        property var taskSummary: ({total:14,incomplete:8,overdue:2,dueThisWeek:5})
        property var workHourSummary: ({loggedHours:12.5,approvedHours:8,pendingHours:4.5})
        property var taskStatusSummary: [{value:"in_progress",label:"In progress",count:5,color:"#447fa4"}]
        property var taskProcessSummary: [{value:"model",label:"Model",count:8,color:"#ad4242"}]
        property var lastCommand: ({})
        function select_profile(value) { lastCommand={type:"select",login:value} }
        function refresh() { lastCommand={type:"refresh"} }
        function logout() { lastCommand={type:"logout"} }
        function open_activity(key) { lastCommand={type:"activity",key} }
        function open_activity_target(key) { lastCommand={type:"target",key} }
        function open_full_activity() { lastCommand={type:"activity"} }
        function open_task_activity(key,task,process) { lastCommand={type:"taskActivity",key,task,process} }
        function create_user(values,groups) { lastCommand={type:"create",values,groups}; return true }
        function queue_avatar(path) { lastCommand={type:"avatar",path:String(path)};return true }
        function save_group_settings(groups,access) { lastCommand={type:"groups",groups,access};return true }
        function save_profile(values,groups,access) { lastCommand={type:"save",values,groups,access};return true }
    }
    QtObject {
        objectName: "appController"
        property string server_state: "online"
        property bool authentication_dialog_visible: true
        property bool authentication_busy: false
        property string authentication_error: ""
        property string login_name: "artist"
        property string server_url: "https://tactic.example.test"
        property var lastCommand: ({})
        function authenticate(login,password) {lastCommand={type:"authenticate",login,password}}
        function cancel_authentication() {authentication_dialog_visible=false;lastCommand={type:"cancel"}}
    }
    QtObject {
        objectName: "messagesController"
        property bool busy: false
        property string selectedLogin: ""
        function open_direct_conversation(login) {selectedLogin=login}
    }
    QtObject {
        objectName: "tasksController"
        property var lastCommand: ({})
        function open_for_user(login) {lastCommand={login}}
        function open_for_user_filter(login,key,value) {lastCommand={login,key,value}}
    }
    QtObject {
        objectName: "windowModel"
        property string lastHelp: ""
        property string closed: ""
        property string shown: ""
        function open_help(topic) {lastHelp=topic}
        function close_window(name) {closed=name}
        function show_window(name) {shown=name}
    }
    QtObject {
        objectName: "configurationController"
        property int sessions: 0
        function begin_session() {sessions++}
    }
    QtObject {
        objectName: "serverPresetsController"
        signal stateChanged()
        signal sessionStarted()
        property string selected_name: "default"
        property var selected_values: ({serverUrl:"https://tactic.example.test",rpcTransport:"xmlrpc",storedUser:"artist",hasTicket:true,
            teamLocalRepository:false,siteEnabled:false,siteName:"default",proxyEnabled:false,proxyServer:"",proxyLogin:"",proxyPassword:"",hasProxyPassword:true})
        property string error: ""
        property var lastCommand: ({})
        function begin_session() {sessionStarted()}
        function update_selected(values) {lastCommand={type:"update",values}}
        function add(name) {lastCommand={type:"add",name};return !!name}
        function remove(index) {lastCommand={type:"remove",index}}
        function select(index) {lastCommand={type:"select",index}}
        function save() {lastCommand={type:"save"};return true}
        function cancel() {lastCommand={type:"cancel"}}
    }
    QtObject {
        objectName: "updateController"
        signal stateChanged()
        signal updateAvailable(string version)
        property string currentVersion: "0.6.0.107"
        property string changelog: "# Release notes\n\nA complete, native update shell."
        property string currentChanges: "Preserve all existing files and settings."
        property string sourceSearchKey: "sthpw/asset?code=fixture"
        property bool busy: false
        property bool portable: true
        property bool cancelable: false
        property bool canInstall: true
        property string error: ""
        property string stage: ""
        property real progress: 0
        property var lastCommand: ({})
        function load() {lastCommand={type:"load"}}
        function select(index) {lastCommand={type:"select",index}}
        function cancel() {lastCommand={type:"cancel"}}
        function install_selected() {lastCommand={type:"install"}}
        function create_update(major,minor,build,revision,changes,misc) {lastCommand={type:"create",major,minor,build,revision,changes,misc}}
        function open_generator() {lastCommand={type:"generator"}}
    }
}
