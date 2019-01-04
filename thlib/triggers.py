input = {'id': 7,
 'is_insert': True,
 'mode': 'insert',
 'prev_data': {'applications_list_code': None,
               'description': None,
               'keywords': None,
               'name': None,
               'pipeline_code': None,
               'props_code': None,
               'timestamp': None},
 'search_code': u'TEXTURES00007',
 'search_key': u'cgshort/textures?project=the_pirate&code=TEXTURES00007',
 'search_type': 'cgshort/textures?project=the_pirate',
 'sobject': {'__search_key__': u'cgshort/textures?project=the_pirate&code=TEXTURES00007',
             u'applications_list_code': '',
             u'code': u'TEXTURES00007',
             u'description': '',
             u'id': 7,
             u'keywords': '',
             u'login': '',
             u'name': u'TEXTURES00003',
             u'pipeline_code': u'PIPELINE00052',
             u'props_code': '',
             u's_status': '',
             u'timestamp': '2016-10-26 09:49:39'},
 'trigger_sobject': {'__search_key__': u'config/trigger?project=the_pirate&code=SPT_TRIGGER00002',
                     u'class_name': '',
                     u'code': u'SPT_TRIGGER00002',
                     u'data': '',
                     u'description': '',
                     u'event': u'insert|cgshort/textures',
                     u'id': 2,
                     u'listen_process': '',
                     u'mode': u'same process,same transaction',
                     u'process': '',
                     u's_status': '',
                     u'script_path': u'triggers/SPT_TRIGGER00002',
                     u'search_type': u'cgshort/textures',
                     u'timestamp': '2016-10-26 09:00:19',
                     u'title': u'Added new item',
                     u'trigger_type': ''},
 'update_data': {'applications_list_code': None,
                 'description': None,
                 'keywords': None,
                 'name': u'TEXTURES00003',
                 'pipeline_code': u'PIPELINE00052',
                 'props_code': None,
                 'timestamp': '2016-10-26 09:49:39'}}


# Custom naming trigger
def get_complex_name():
    # get applications_list
    applications_list_name = ''
    applications_list_code = input['sobject']['applications_list_code']
    if applications_list_code:
        filters = [('code', applications_list_code)]
        applications_list_dict = server.query('cgshort/applications_list', filters, single=True, columns=['name'])
        if applications_list_dict:
            applications_list_name = applications_list_dict['name']

    # # get props
    props_name = 'Texture_{0:05d}'.format(int(input['id']))  # if no name, and no code, it will be named CODE
    props_code = input['sobject']['props_code']
    if props_code:
        filters = [('code', props_code)]
        props_dict = server.query('cgshort/props', filters, single=True, columns=['name'])
        if props_dict:
            props_name = props_dict['name']

    data = {
        'name': '{0}_{1}'.format(props_name, applications_list_name)
    }

    server.update(input['search_key'], data, triggers=False)

if not input['sobject']['name']:
    get_complex_name()

asd = {
    "trigger_sobject": {
        "code": "SPT_TRIGGER00001",
        "description": "",
        "title": "texture_insert",
        "class_name": "",
        "timestamp": "2016-11-22 15:03:01",
        "trigger_type": "",
        "s_status": "",
        "event": "insert|cgshort/textures",
        "search_type": "cgshort/textures",
        "process": "",
        "mode": "same process,same transaction",
        "__search_key__": "config/trigger?project=new&code=SPT_TRIGGER00001",
        "script_path": "stypes_triggers/textures_naming",
        "data": "",
        "id": 1,
        "listen_process": ""
    },
    "update_data": {
        "props_code": null,
        "description": null,
        "postfix": "bugr",
        "timestamp": "2016-11-22 15:25:44",
        "search_type": "cgshort/props?project=new",
        "characters_code": null,
        "keywords": null,
        "search_code": "PROPS00001",
        "sets_code": null
    },
    "search_key": "cgshort/textures?project=new&code=TEXTURES00032",
    "prev_data": {
        "description": null,
        "postfix": null,
        "timestamp": null,
        "sets_code": null,
        "search_type": null,
        "characters_code": null,
        "keywords": null,
        "search_code": null,
        "props_code": null
    },
    "search_type": "cgshort/textures?project=new",
    "is_insert": true,
    "mode": "insert",
    "search_code": "TEXTURES00032",
    "id": 32,
    "sobject": {
        "code": "TEXTURES00032",
        "description": "",
        "postfix": "bugr",
        "timestamp": "2016-11-22 15:25:44",
        "s_status": "",
        "sets_code": "",
        "search_type": "cgshort/props?project=new",
        "__search_key__": "cgshort/textures?project=new&code=TEXTURES00032",
        "characters_code": "",
        "keywords": "",
        "login": "",
        "search_code": "PROPS00001",
        "props_code": "",
        "id": 32,
        "name": ""
    }
}


def apply_texture_naming():
    # get postfix
    postfix = input['sobject'].get('postfix')
    if not postfix:
        postfix = 'texture_{0:05d}'.format(int(input['id']))  # if no postfix only id number

    # get parent name
    parent_code = input['sobject']['search_code']
    search_type = input['sobject']['search_type']
    search_code = input['sobject']['search_code']
    filters = [('code', parent_code)]
    parent_dict = server.query(search_type, filters, single=True, columns=['name'])
    parent_name = '{0}_texture'.format(search_code)
    if parent_dict:
        parent_name = parent_dict['name']

    data = {
        'name': '{0}_{1}'.format(parent_name, postfix)
    }

    server.update(input['search_key'], data, triggers=False)

if not input['sobject']['name']:
    apply_texture_naming()
