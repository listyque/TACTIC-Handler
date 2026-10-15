// UI transitions are shared; the existing client controller owns server data.
export function initial() {
    return {
        page: 'members',
        query: '',
        confirmation: ''
    };
}

export function permissions(model) {
    const editable =
        !!model.ready && !!model.canWrite && !model.busy && !model.uncertain;
    return {
        editable,
        create: editable && !model.dirty,
        reload: !model.busy && !!model.canLoad,
        save: editable && !!model.draft && !!model.dirty,
        discard: !model.busy && !!(model.dirty || model.uncertain),
        select:
            !!model.ready && !model.busy && !model.dirty && !model.uncertain,
        search: !!model.draft && !model.busy
    };
}

export function transition(ui, model, event) {
    const next = Object.assign({}, ui);
    const commands = [];
    const allow = permissions(model);
    switch (event.type) {
        case 'page':
            if (
                !model.busy &&
                ['members', 'details'].indexOf(event.value) >= 0
            ) {
                next.page = event.value;
                commands.push({
                    type: 'focus',
                    id: 'segmentedButtonSegment_' + next.page
                });
            }
            break;
        case 'query':
            if (allow.search) {
                next.query = String(event.value);
                commands.push({
                    type: 'query',
                    value: next.query
                });
            }
            break;
        case 'create':
            if (allow.create) {
                next.page = 'details';
                next.query = '';
                next.confirmation = '';
                commands.push(
                    {
                        type: 'create'
                    },
                    {
                        type: 'query',
                        value: ''
                    },
                    {
                        type: 'focus',
                        id: 'securityGroupName'
                    }
                );
            }
            break;
        case 'select':
            if (allow.select)
                commands.push({
                    type: 'select',
                    code: event.code
                });
            break;
        case 'field':
            if (
                allow.editable &&
                model.draft &&
                ['name', 'description'].indexOf(event.field) >= 0 &&
                !(event.field === 'name' && model.draft.code)
            ) {
                commands.push({
                    type: 'field',
                    field: event.field,
                    value: String(event.value)
                });
            }
            break;
        case 'member':
            if (allow.editable && model.draft)
                commands.push({
                    type: 'member',
                    login: event.login,
                    value: !!event.value
                });
            break;
        case 'save':
            if (allow.save)
                commands.push(
                    model.draft.name.trim()
                        ? {
                              type: 'save'
                          }
                        : {
                              type: 'error',
                              text: 'Enter a group identifier'
                          }
                );
            break;
        case 'reload':
            if (allow.reload) {
                if (model.dirty || model.uncertain)
                    next.confirmation = 'reload';
                else
                    commands.push({
                        type: 'reload',
                        force: false
                    });
            }
            break;
        case 'discard':
            if (allow.discard) next.confirmation = 'discard';
            break;
        case 'close':
            if (!model.busy) {
                if (model.dirty || model.uncertain) next.confirmation = 'close';
                else
                    commands.push({
                        type: 'close'
                    });
            }
            break;
        case 'keep':
            next.confirmation = '';
            break;
        case 'confirm':
            if (!model.busy && next.confirmation) {
                const action = next.confirmation;
                next.confirmation = '';
                if (action === 'close')
                    commands.push({
                        type: 'close'
                    });
                else if (action === 'reload' || model.uncertain)
                    commands.push({
                        type: 'reload',
                        force: true
                    });
                else
                    commands.push({
                        type: 'discard'
                    });
            }
            break;
        default:
            throw Error('Unknown Groups action: ' + event.type);
    }
    return {
        ui: next,
        commands
    };
}
