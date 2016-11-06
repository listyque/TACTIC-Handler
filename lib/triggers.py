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

