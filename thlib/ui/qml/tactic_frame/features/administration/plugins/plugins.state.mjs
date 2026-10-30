import { themeSource } from './plugins.resources.mjs';

export function initial() {
    return {
        query: '',
        activeOnly: false,
        tab: 'info',
        operation: '',
        value: '',
        url: '',
        checksum: '',
        collapsed: false,
        source: 'zip',
        notice: '',
        resourceAdd: false,
        resourceKind: 'widget',
        resourceName: '',
        resourceType: '',
        resourceCode: '',
        resourceSchema: false,
        resourceMode: 'source'
    };
}
export const destructive = {
    run_resource:
        'Run this trusted server Python action? It may modify project data.',
    activate:
        'Activate this package in the selected project? Its manifest can create or update project data and run server code.',
    replace_file: 'Replace the selected file with a local upload?',
    reload_catalog: 'Discard unsaved changes and reload the plugin catalogue?',
    reload: 'Reload removes and reinstalls the plugin in this project. Its data may be replaced.',
    deactivate:
        'Remove this plugin and its manifest-defined data from the current project?',
    clean: 'Clean all project entries described by this plugin manifest?',
    delete: 'Delete this package from the server? It must be inactive in every project.',
    delete_file: 'Delete the selected plugin file or folder and its contents?',
    clear_spt: 'Delete all generated .spt files in this package?'
};
export function catalog(model, ui) {
    const query = ui.query.trim().toLowerCase();
    return (model.catalog || []).filter(
        (row) =>
            (!ui.activeOnly || row.active) &&
            (!query ||
                [row.code, row.title, row.path]
                    .join(' ')
                    .toLowerCase()
                    .includes(query))
    );
}
const parent = (path) => path.split('/').slice(0, -1).join('/');
export function transition(ui, model, event) {
    if (event.type === 'reset') return { ui: initial(), commands: [] };
    const next = Object.assign({}, ui),
        commands = [],
        request = (action, values = {}) =>
            commands.push({ type: 'request', action, values }),
        blocked = model.busy || model.uncertain,
        clean = () => {
            if (model.dirty || model.uncertain) {
                commands.push({
                    type: 'error',
                    value: 'Apply or discard unsaved changes first'
                });
                return false;
            }
            return !model.busy;
        };
    if (event.type === 'completed') {
        const messages = {
            add_resource: 'Resource added to this project and package.',
            apply_theme:
                'Project theme applied. Personal appearance settings are preserved.',
            reset_theme: 'Personal appearance restored.',
            install:
                'Package added. Review its contents, then activate it in this project.',
            download_url:
                'Package added. Review its contents, then activate it in this project.',
            create: model.metadata?.active
                ? 'Plugin created and active in this project. Add files and configure its manifest.'
                : model.identity
                  ? 'Package added. Review its contents, then activate it in this project.'
                  : 'Package exported. Check your downloads.',
            activate: 'Plugin is now active in this project.',
            deactivate:
                'Plugin removed from this project. The package remains on the server.',
            save:
                model.metadata?.active &&
                !model.document?.file &&
                !model.document?.resource
                    ? 'Changes saved. Reload the plugin to apply manifest changes to this project.'
                    : 'Changes saved.',
            export: 'Package exported. Check your downloads.',
            publish:
                'Version published. Review the new release before activating it.'
        };
        next.notice = messages[event.action] || '';
        if (event.action === 'add_resource') next.resourceAdd = false;
        if (
            [
                'list',
                'new',
                'install',
                'download_url',
                'create',
                'publish',
                'delete'
            ].includes(event.action)
        ) {
            next.operation = '';
            next.tab = 'info';
        }
    } else if (event.type === 'help')
        commands.push({ type: 'help', topic: 'plugins' });
    else if (event.type === 'query') next.query = event.value;
    else if (event.type === 'activeOnly') next.activeOnly = event.value;
    else if (event.type === 'collapse') next.collapsed = !ui.collapsed;
    else if (event.type === 'input') next[event.field] = event.value;
    else if (event.type === 'resource-add' && clean()) {
        next.resourceAdd = true;
        next.resourceName = '';
    } else if (event.type === 'resource-cancel' && !model.busy)
        next.resourceAdd = false;
    else if (event.type === 'resource-create' && clean())
        request('add_resource', {
            values: {
                kind: ui.resourceKind,
                name: ui.resourceName,
                searchType: ui.resourceType,
                code: ui.resourceCode,
                schema: ui.resourceSchema
            }
        });
    else if (event.type === 'resource' && clean()) {
        next.resourceMode = 'source';
        request('open_resource', { resource: event.key });
    } else if (
        event.type === 'resource-theme' &&
        !blocked &&
        model.canWrite &&
        model.document?.resource?.kind === 'theme' &&
        model.document.resource.palette
    ) {
        const resource = model.document.resource,
            palette = JSON.parse(JSON.stringify(resource.palette));
        if (event.field === 'style') palette.style = event.value;
        else {
            const parts = event.field.split('_');
            palette[parts[0]][parts[1]] = event.value;
        }
        commands.push(
            {
                type: 'field',
                field: 'resource_source',
                value: themeSource(resource.source, event.field, event.value)
            },
            { type: 'field', field: 'resource_palette', value: palette }
        );
    } else if (event.type === 'field' && !blocked && model.canWrite)
        commands.push(event);
    else if (event.type === 'select' && clean()) {
        next.operation = '';
        next.notice = '';
        next.tab = 'info';
        commands.push(event);
    } else if (event.type === 'tab' && clean()) {
        next.tab = event.value;
        next.operation = '';
        next.notice = '';
        if (event.value === 'resources') {
            const first = model.metadata?.resources?.find((item) => item.field);
            if (first) {
                next.resourceMode = 'preview';
                request('open_resource', { resource: first.key });
            }
        } else if (event.value === 'docs') {
            if (model.metadata.docsExist)
                request('open_file', { file: model.metadata.docs });
        } else if (model.document?.file || model.document?.resource)
            request('load');
    } else if (event.type === 'reload' && !model.busy) {
        if (model.dirty) next.operation = 'reload_catalog';
        else {
            commands.push({ type: 'discard' });
            request('list');
        }
    } else if (event.type === 'discard' && !model.busy) commands.push(event);
    else if (
        event.type === 'save' &&
        !blocked &&
        (!model.metadata?.new || canCreate(model))
    )
        commands.push(event);
    else if (event.type === 'new' && clean()) {
        next.operation = '';
        next.notice = '';
        next.tab = 'info';
        request('new');
    } else if (event.type === 'install' && clean()) {
        next.operation = 'install';
        next.notice = '';
        next.source = 'zip';
        next.url = '';
        next.checksum = '';
    } else if (event.type === 'file' && clean()) {
        next.tab = 'files';
        next.operation = '';
        next.notice = '';
        request(
            event.directory ? 'browse' : 'open_file',
            event.directory
                ? { folder: event.path }
                : { file: event.path, folder: model.metadata.folder || '' }
        );
    } else if (event.type === 'docs_create' && clean()) {
        next.tab = 'docs';
        request('new_file', { path: model.metadata.docs });
    } else if (event.type === 'upload' && clean()) commands.push(event);
    else if (event.type === 'operation' && clean()) {
        next.operation = event.action;
        next.notice = '';
        next.value =
            event.action === 'rename'
                ? model.document?.file?.path || model.metadata.folder || ''
                : '';
    } else if (event.type === 'cancel' && !model.busy) {
        next.operation = '';
        if (model.metadata?.new) commands.push({ type: 'discard' });
    } else if (
        event.type === 'confirm' &&
        ui.operation === 'reload_catalog' &&
        !model.busy
    ) {
        commands.push({ type: 'discard' });
        request('list');
        next.operation = '';
    } else if (event.type === 'confirm' && clean()) {
        const action = ui.operation,
            values = { confirmation: true };
        if (action === 'replace_file') {
            commands.push({ type: 'upload', package: false, replace: true });
        } else if (action === 'install') {
            values.url = ui.url;
            values.checksum = ui.checksum;
            request('download_url', values);
        } else {
            const selected =
                model.document?.file?.path || model.metadata.folder || '';
            if (['new_file', 'new_folder'].includes(action))
                values.path = [model.metadata.folder, ui.value]
                    .filter(Boolean)
                    .join('/');
            if (action === 'publish') values.version = ui.value;
            if (action === 'run_resource') {
                values.resource = model.document?.resource?.key;
                values.inputs = ui.resourceArguments || '{}';
            }
            if (action === 'rename') {
                values.path = selected;
                values.destination = ui.value;
            }
            if (action === 'delete_file') values.path = selected;
            if (action === 'delete_file' || action === 'rename')
                values.folder = parent(selected);
            request(action, values);
        }
        if (action !== 'install') next.operation = '';
    } else if (event.type === 'run' && clean())
        request(event.action, event.values || {});
    return { ui: next, commands };
}

export function canCreate(model) {
    const doc = model.document || {};
    return doc.type === 'project' || !!(doc.title?.trim() && doc.code?.trim());
}
