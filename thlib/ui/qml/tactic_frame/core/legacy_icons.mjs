// Original IconWdg names and raster sources used by shipped legacy templates.
// Values pair a modern semantic icon with the original asset reference.
export const legacyIcons = {
    ADD: ['add', 'add.png'],
    ARROW_OUT: ['open-in-new', 'arrow_out.png'],
    BW_PHOTO: ['image', '/context/icons/common/bw_photo.png'],
    CALENDAR: ['calendar', 'calendar.png'],
    CAMERA: ['photo-camera', 'camera.png'],
    CONNECT: ['connection', 'connect.png'],
    CONTENTS: ['view-list', 'application_view_list.png'],
    DATE: ['calendar', 'date.png'],
    DATE_EDIT: ['calendar', 'date_edit.png'],
    DATE_GO: ['schedule', 'date_go.png'],
    DATE_MAGNIFY: ['search', 'date_magnify.png'],
    DELETE: ['delete', 'delete.png'],
    DETAILS: ['description', 'page_white_text.png'],
    DOWNLOAD: ['download', '_spt_download.png'],
    EDIT: ['edit', 'page_white_edit.png'],
    FILM: ['movie', 'film.png'],
    FILM_SUBMIT: ['publish', 'film_go.png'],
    FOLDER: ['folder', 'folder.png'],
    FOLDER_EDIT: ['folder', 'folder_edit.png'],
    FOLDER_EXPLORE: ['folder-open', 'folder_explore.png'],
    FOLDER_GO: ['folder-open', 'folder_go.png'],
    GROUP_LINK: ['group', 'group_link.png'],
    IMAGE: ['image', 'image.png'],
    JUMP: ['open-in-new', 'door_in.png'],
    LINK: ['link', 'link.png'],
    LOCK: ['lock', 'lock.png'],
    MOVIE_VIEW: ['movie', '/context/icons/common/view_movie.png'],
    NOTE_GO: ['notes', 'note_go.png'],
    PHOTOS: ['collections', 'photos.png'],
    PICTURE_EDIT: ['image-edit', 'picture_edit.png'],
    PLUGIN: ['extension', 'plugin.png'],
    PLUGIN_ADD: ['extension', 'plugin_add.png'],
    PROCESS: ['grid-view', 'application_view_tile.png'],
    SAVE: ['save', 'disk.png'],
    STAR: ['star', 'star.png'],
    USER: ['person', 'user.png'],
    USER_ADD: ['person-add', 'user_add.png'],
    WORK: ['workspaces', '/context/icons/custom/work.png']
};

const aliases = Object.create(null);
for (const key of Object.keys(legacyIcons)) {
    const [name, source] = legacyIcons[key];
    aliases[key] = name;
    aliases[source] = name;
    const file = source.slice(source.lastIndexOf('/') + 1);
    aliases[file] = name;
    aliases[file.replace(/\.[^.]+$/, '')] = name;
    if (!source.startsWith('/'))
        aliases['/context/icons/silk/' + source] = name;
}
aliases.Contents = aliases.CONTENTS;
aliases.contents = aliases.CONTENTS;
aliases.BS_LIST_ALT = 'view-list';
aliases.FAS_TELEVISION = 'fontawesome-solid:tv';
aliases.television = 'fontawesome-solid:tv';

export function legacyName(source) {
    return aliases[String(source || '').trim()] || '';
}
