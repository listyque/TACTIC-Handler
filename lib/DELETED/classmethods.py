import tactic_classes as tc
import collections
from pprint import pprint


# SObject class
class SObject(object):
    """
    Main class for all types of sobjects
    creates structured tree of objects
    to see all output:

    sobjects = get_sobjects(sobjects_list, snapshots_list)

    # test particular output example, outputs versioned and versionless snapshots
    for c, v in sobjects['PROPS00001'].process['Modeling'].contexts.iteritems():
        pprint(c)
        pprint(v.versionless)
        pprint(v.versions)

    # Test full output example, outputs all versioned and versionless snapshots
    for read in sobjects.iterkeys():
        print('____________________________________________:'+read+'____________________________________________')
        for key, value in sobjects[read].process.iteritems():
            for key2, val2 in value.contexts.iteritems():
                print('Process: {0},\n\nContext: {1}, \n\nSnapshot versionless: {2},\n\nSnapshot versions: {
                3}'.format(key, key2, value.contexts[key2].versionless, value.contexts[key2].versions))

    # Usage variants:
    # .get_snapshots()
    # .process['sculpt'].snapshots['maya']()  # gets all versionless snapshots per context typed 'maya'
    # .process['sculpt'].snapshots['context'].versions() # gets all dependent to context versions
    # .process['sculpt'].snapshots['context'].preview['web']()  # give all playblast, or icons 'web',
    # 'icon', 'playblast', 'main'
    # .process['sculpt'].snapshots['maya'].getTasks()

    # .get_icons()
    # .icons['web']()  # all sobject icons 'web', 'icon', 'main'

    # .get_tasks()
    # .process['sculpt'].task() # return all tasks per context belongs to 'sculpt'
    # .process['sculpt'].task['context'].get_notes() # gets notes per task context
    # .process['sculpt'].task['context'].notes() # return all notes per task context

    # .get_notes()
    # .process['sculpt'].notes()
    """

    def __init__(self, in_sobj=None, in_process=None):
        """
        :param in_sobj: input list with info on particular sobject
        :param in_process: list of current sobject possible process, need to query tasks per process
        :return:
        """

        # INPUT VARS
        self.sobj = in_sobj
        self.all_process = in_process

        # OUTPUT VARS
        self.process = {}
        self.tasks = {}
        self.notes = {}

    # Tasks by search code
    @staticmethod
    def query_tasks(s_code, process=None, user=None):
        """
        Query for Task
        :param s_code: Code of asset related to task
        :param process: Process code
        :param user: Optional users names
        :return:
        """
        search_type = 'sthpw/task'
        if process:
            filters = [('search_code', s_code), ('process', process)]
        else:
            filters = [('search_code', s_code)]

        return tc.server_query(search_type, filters)

    # Notes by search code
    @staticmethod
    def query_notes(s_code, process=None):
        """
        Query for Notes
        :param s_code: Code of asset related to note
        :param process: Process code
        :return:
        """
        search_type = 'sthpw/note'
        if process:
            filters = [('search_code', s_code), ('process', process)]
        else:
            filters = [('search_code', s_code)]

        return tc.server_query(search_type, filters)

    # Snapshots by process
    def get_snapshots(self, snapshot_dict):
        process_set = set(snapshot['process'] for snapshot in snapshot_dict)

        for process in process_set:
            self.process[process] = Process(snapshot_dict, process)


class Process(object):
    def __init__(self, snapshot_dict, process):
        # Contexts
        self.contexts = {}
        versions = collections.defaultdict(list)
        versionless = collections.defaultdict(list)
        contexts = set()

        for snapshot in snapshot_dict:
            if snapshot['process'] == process and snapshot['version'] == -1:
                versionless[snapshot['context']].append(snapshot)
            elif snapshot['process'] == process and snapshot['version'] != -1:
                versions[snapshot['context']].append(snapshot)
            if snapshot['process'] == process:
                contexts.add(snapshot['context'])

        for context in contexts:
            self.contexts[context] = Contexts(versionless[context], versions[context])


class Contexts(object):
    def __init__(self, versionless, versions):
        self.versions = {sn['code']: Snapshot(sn) for sn in versions}
        self.versionless = {sn['code']: Snapshot(sn) for sn in versionless}


class Snapshot(SObject, object):
    def __init__(self, snapshot):
        super(self.__class__, self).__init__()

        self.files = collections.defaultdict(list)
        for fl in snapshot['__files__']:
            self.files[fl['type']].append(fl)

        self.snapshot = snapshot
        # delete unused big entries
        del self.snapshot['__files__'], self.snapshot['snapshot']

    def get_tasks(self):
        print(self.query_tasks(self.snapshot['code']))

    def get_notes(self):
        print(self.query_notes(self.snapshot['code']))


class Notes(object):
    def __init__(self):
        pass


class Tasks(object):
    def __init__(self):
        pass


process_codes = ['Modeling', 'Sculpt', 'Final', 'Texturing', 'Refs']
code = ['PROPS00001', 'PROPS00002', 'PROPS00003', 'PROPS00004']
process_codes.extend(['icon', 'attachment'])

filters_snapshots = [
    ('process', process_codes),
    ('project_code', 'exam'),
    ('search_code', code),
]

snapshots_list = tc.server_start().query_snapshots(filters=filters_snapshots, include_files=True)

sobjects_list = [{
    '__search_key__': u'exam/props?project=exam&code=PROPS00001',
    'code': u'PROPS00001',
    'description': u'testing purposes',
    'id': 4,
    'keywords': None,
    'login': None,
    'name': u'Test',
    'pipeline_code': u'exam/props',
    's_status': None,
    'timestamp': '2015-12-19 12:18:40'
},
    {
        '__search_key__': u'exam/props?project=exam&code=PROPS00002',
        'code': u'PROPS00002',
        'description': u'testing purposes',
        'id': 4,
        'keywords': None,
        'login': None,
        'name': u'Test',
        'pipeline_code': u'exam/props',
        's_status': None,
        'timestamp': '2015-12-19 12:18:40'
    },
    {
        '__search_key__': u'exam/props?project=exam&code=PROPS00003',
        'code': u'PROPS00003',
        'description': u'testing purposes',
        'id': 4,
        'keywords': None,
        'login': None,
        'name': u'Test',
        'pipeline_code': u'exam/props',
        's_status': None,
        'timestamp': '2015-12-19 12:18:40'
    },
    {
        '__search_key__': u'exam/props?project=exam&code=PROPS00004',
        'code': u'PROPS00004',
        'description': u'testing purposes',
        'id': 4,
        'keywords': None,
        'login': None,
        'name': u'Test',
        'pipeline_code': u'exam/props',
        's_status': None,
        'timestamp': '2015-12-19 12:18:40'
    }]


def get_sobjects(sobjects_list, snapshots_list):
    """
    Filters snapshot by search codes, and sobjects codes
    :param sobjects_list: full list of stypes
    :param snapshots_list: full list of related snapshots
    :return: dict of sObjects objects
    """
    snapshots = collections.defaultdict(list)
    sobjects = {}

    # filter snapshots by search_code
    for snapshot in snapshots_list:
        snapshots[snapshot['search_code']].append(snapshot)

    # append sObject info to the end of each search_code filtered list
    for sobject in sobjects_list:
        snapshots[sobject['code']].append(sobject)

    # creating dict or ready SObjects
    for k, v in snapshots.iteritems():
        sobjects[k] = SObject(v[-1], process_codes)
        sobjects[k].get_snapshots(v[:-1])

    return sobjects


sobjects = get_sobjects(sobjects_list, snapshots_list)

# test output
"""
for c, v in sobjects['PROPS00001'].process['Modeling'].contexts.iteritems():
    pprint(c)
    pprint(v.versionless)
    pprint(v.versions)
"""
# Test full output
# """
for read in sobjects.iterkeys():
    print('____________________________________________:' + read + '____________________________________________')
    for key, value in sobjects[read].process.iteritems():
        for key2, val2 in value.contexts.iteritems():
            print(
            'Process: {0},\n\nContext: {1}, \n\nSnapshot versionless: {2},\n\nSnapshot versions: {3}'.format(key, key2,
                                                                                                             value.contexts[
                                                                                                                 key2].versionless,
                                                                                                             value.contexts[
                                                                                                                 key2].versions))
# """
