.pragma library

function matches(login, label, groups, query) {
    query = String(query || "").trim().toLowerCase()
    return !query || (login + " " + label + " " + (groups || []).join(" "))
        .toLowerCase().indexOf(query) >= 0
}
