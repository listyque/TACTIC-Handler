import time


def sizes(size, precision=2):
    suffixes = [' b', ' Kb', ' Mb', ' Gb', ' Tb']
    suffix_index = 0

    while size > 1024 and suffix_index < 4:
        suffix_index += 1
        size = size / 1024.0

    return "%.*f%s" % (precision, size, suffixes[suffix_index])


query = [{
    'is_synced': True, 'code': 'SNAPSHOT00000108', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 108, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000108', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000264',
        '__search_type__': 'sthpw/file', 'file_name': 'verts_Modeling_v002.ma',
        'snapshot_code': 'SNAPSHOT00000108', 'project_code': 'exam', 'id': 264,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000264', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Modeling/versions',
        'timestamp': '2015-12-19 12:13:56', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Modeling/versions',
        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
        'source_path': 'verts.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'VERTICES', 'timestamp': '2015-12-19 12:13:56',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 15:13:56 2015" context="Modeling" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000264" name="verts_Modeling_v002.ma" type="main"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000107', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 107, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000107', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000266', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_verts_Modeling.ma',
        'snapshot_code': 'SNAPSHOT00000107', 'project_code': '', 'id': 266,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000266', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Modeling',
        'timestamp': '2015-12-19 12:13:56', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Modeling',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-19 12:13:08',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000108">\n  <file file_code="FILE00000266" '
                'name="Oculus_verts_Modeling.ma" type="main"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000106', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 106, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000106', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000261',
        '__search_type__': 'sthpw/file', 'file_name': 'mesh_Modeling_v001.ma',
        'snapshot_code': 'SNAPSHOT00000106', 'project_code': 'exam', 'id': 261,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000261', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Modeling/versions',
        'timestamp': '2015-12-19 12:13:07', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Modeling/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'mesh.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'MESHING', 'timestamp': '2015-12-19 12:13:07',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 15:13:07 2015" context="Modeling" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000261" name="mesh_Modeling_v001.ma" type="main"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000072', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 72, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 6,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000072', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000207',
        '__search_type__': 'sthpw/file', 'file_name': 'flower_Refs_v006.ma',
        'snapshot_code': 'SNAPSHOT00000072', 'project_code': 'exam', 'id': 207,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000207', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs',
        'timestamp': '2015-12-19 10:46:47', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'sd', 'timestamp': '2015-12-19 10:46:47', 'repo': '',
    'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 13:46:47 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000207" name="flower_Refs_v006.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000057', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 57, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 5,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000057', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000184',
        '__search_type__': 'sthpw/file', 'file_name': 'oculus_Refs_v005.ma',
        'snapshot_code': 'SNAPSHOT00000057', 'project_code': 'exam', 'id': 184,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000184', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs/versions',
        'timestamp': '2015-12-19 09:58:12', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'oculus.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'oculus', 'timestamp': '2015-12-19 09:58:12',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 12:58:12 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000184" name="oculus_Refs_v005.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000056', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 56, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 4,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000056', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000181',
        '__search_type__': 'sthpw/file', 'file_name': 'Oculus_nhair_Refs_v004.ma',
        'snapshot_code': 'SNAPSHOT00000056', 'project_code': 'exam', 'id': 181,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000181', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs/versions',
        'timestamp': '2015-12-19 09:55:39', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'nhair.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'das', 'timestamp': '2015-12-19 09:55:39', 'repo': '',
    'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 12:55:39 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000181" name="Oculus_nhair_Refs_v004.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000055', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 55, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 3,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000055', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000178',
        '__search_type__': 'sthpw/file', 'file_name': 'Oculus_shave_Refs_v003.ma',
        'snapshot_code': 'SNAPSHOT00000055', 'project_code': 'exam', 'id': 178,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000178', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs/versions',
        'timestamp': '2015-12-19 09:08:11', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
        'source_path': 'shave.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'nhair an shave', 'timestamp': '2015-12-19 09:08:11',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 12:08:11 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000178" name="Oculus_shave_Refs_v003.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000054', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 54, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000054', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000175',
        '__search_type__': 'sthpw/file', 'file_name': 'Oculus_nhair_Refs_v002.ma',
        'snapshot_code': 'SNAPSHOT00000054', 'project_code': 'exam', 'id': 175,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000175', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs/versions',
        'timestamp': '2015-12-19 09:08:09', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'nhair.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'nhair an shave', 'timestamp': '2015-12-19 09:08:09',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 12:08:09 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000175" name="Oculus_nhair_Refs_v002.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000052', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 52, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000052', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000172',
        '__search_type__': 'sthpw/file', 'file_name': 'Oculus_shave_Refs_v001.ma',
        'snapshot_code': 'SNAPSHOT00000052', 'project_code': 'exam', 'id': 172,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000172', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs/versions',
        'timestamp': '2015-12-19 09:07:23', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
        'source_path': 'shave.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'nhair va', 'timestamp': '2015-12-19 09:07:23',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 12:07:23 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000172" name="Oculus_shave_Refs_v001.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000053', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 53, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000053', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000186', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_oculus_Refs.ma', 'snapshot_code': 'SNAPSHOT00000053',
        'project_code': '', 'id': 186, 'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000186', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Refs',
        'timestamp': '2015-12-19 09:58:12', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-19 09:07:23',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000057">\n  <file file_code="FILE00000186" '
                'name="Oculus_oculus_Refs.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000051', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 51, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 4,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000051', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000169',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_nhair_Sculpt_v004.ma',
        'snapshot_code': 'SNAPSHOT00000051', 'project_code': 'exam', 'id': 169,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000169', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
        'timestamp': '2015-12-19 08:01:45', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'nhair.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'Back to nhair', 'timestamp': '2015-12-19 08:01:45',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 11:01:45 2015" context="Sculpt" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000169" name="Oculus_nhair_Sculpt_v004.ma" type="main"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000050', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 50, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 3,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000050', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000166',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_shave_Sculpt_v003.ma',
        'snapshot_code': 'SNAPSHOT00000050', 'project_code': 'exam', 'id': 166,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000166', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
        'timestamp': '2015-12-19 07:45:05', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
        'source_path': 'shave.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'Shave Var', 'timestamp': '2015-12-19 07:45:05',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 10:45:05 2015" context="Sculpt" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000166" name="Oculus_shave_Sculpt_v003.ma" type="main"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000049', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 49, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000049', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000163',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_nhair_Sculpt_v002.ma',
        'snapshot_code': 'SNAPSHOT00000049', 'project_code': 'exam', 'id': 163,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000163', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
        'timestamp': '2015-12-18 21:36:02', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'nhair.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'Another ver', 'timestamp': '2015-12-18 21:36:02',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 00:36:02 2015" context="Sculpt" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000163" name="Oculus_nhair_Sculpt_v002.ma" type="main"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000048', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 48, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000048', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000162', '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_nhair_Texturing.ma',
        'snapshot_code': 'SNAPSHOT00000048', 'project_code': '', 'id': 162,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000162', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/Texturing',
        'timestamp': '2015-12-18 21:30:58', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-18 21:30:58',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000047">\n  <file file_code="FILE00000162" '
                'name="Mushroom_nhair_Texturing.ma" type="main"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000047', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 47, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 3,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000047', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000160',
        '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_nhair_Texturing_v003.ma',
        'snapshot_code': 'SNAPSHOT00000047', 'project_code': 'exam', 'id': 160,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000160', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
        'timestamp': '2015-12-18 21:30:57', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'nhair.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'main version', 'timestamp': '2015-12-18 21:30:57',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 19 00:30:57 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000160" name="Mushroom_nhair_Texturing_v003.ma" type="main"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000045', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 45, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000045', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000157',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_nhair_Sculpt_v001.ma',
        'snapshot_code': 'SNAPSHOT00000045', 'project_code': 'exam', 'id': 157,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000157', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
        'timestamp': '2015-12-18 20:58:16', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'nhair.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'nHai Hairs version',
    'timestamp': '2015-12-18 20:58:16', 'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {},
    'snapshot_type': 'file', 'server': '', 'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Fri Dec 18 23:58:16 2015" context="Sculpt" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000157" name="Oculus_nhair_Sculpt_v001.ma" type="main"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000046', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 46, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000046', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000171', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_nhair_Sculpt.ma', 'snapshot_code': 'SNAPSHOT00000046',
        'project_code': '', 'id': 171, 'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000171', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Sculpt',
        'timestamp': '2015-12-19 08:01:45', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-18 20:58:16',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000051">\n  <file file_code="FILE00000171" '
                'name="Oculus_nhair_Sculpt.ma" type="main"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000044', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 44, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000044', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000156', '__search_type__': 'sthpw/file',
        'file_name': u'Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling.ma',
        'snapshot_code': 'SNAPSHOT00000044', 'project_code': '', 'id': 156,
        'base_type': 'file', 'st_size': 117919,
        '__search_key__': 'sthpw/file?code=FILE00000156', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/Modeling',
        'timestamp': '2015-12-15 19:07:49', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Modeling',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-15 19:07:49',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000043">\n  <file file_code="FILE00000156" '
                u'name="Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling.ma" type="main"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000043', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 43, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000043', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000154',
        '__search_type__': 'sthpw/file',
        'file_name': u'Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling_v001.ma',
        'snapshot_code': 'SNAPSHOT00000043', 'project_code': 'exam', 'id': 154,
        'base_type': 'file', 'st_size': 117919,
        '__search_key__': 'sthpw/file?code=FILE00000154', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/Modeling/versions',
        'timestamp': '2015-12-15 19:07:47', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Modeling/versions',
        'md5': '', 'base_dir_alias': '',
        'source_path': u'\u0431\u0438\u043b\u0435\u04422.ma',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }],
    'description': u'\t\tIntensity 100 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\tfromIntensity '
                   u'1\n\t\ttoIntensity  100000 - \u043a\u043e\u0440\u043e\u0447\u0435, '
                   u'\u0434\u0430\u043b\u0435\u043a\u043e\n\t\tdecayRate 1.6\n\t\tfromLightColor, toLightColor  - '
                   u'\u044d\u0442\u0438 \u0434\u0432\u0430 \u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u0430 '
                   u'\u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c \u0432 \u043e\u0434\u0438\u043d - '
                   u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\tconeAngle 300 - '
                   u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\tpenumbraAngle '
                   u'10-100 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\tdropOff 3 - '
                   u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\temitDiffuse '
                   u'\n\t\temitSpecular \n\t\t\n\t\t\u042d\u0442\u0438 '
                   u'\u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b \u043d\u0430\u0434\u043e '
                   u'\u0441\u0434\u0435\u043b\u0430\u0442\u044c \u043c\u0435\u043d\u0435\u0435 '
                   u'\u0447\u0443\u0432\u0441\u0442\u0432\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u043c\u0438, '
                   u'\u0441\u0435\u0439\u0447\u0430\u0441 \u043e\u043d\u0438 \u0432\u0441\u0435 '
                   u'\u043a\u0440\u0443\u0442\u044f\u0442\u0441\u044f \u0432 '
                   u'\u0442\u044b\u0441\u044f\u0447\u043d\u044b\u0445 '
                   u'\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f\u0445:\n\t\t\ttrace_bias 0.001 - '
                   u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\ttrace_blur 0.001 '
                   u'- \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\ttrace_samples 8 '
                   u'- \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\ttrace_subset - '
                   u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                   u'\ttrace_excludesubset - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t\n\t\t'
                   u'\tdmapFilterSize - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\tdmapFilter - '
                   u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t\n\t\t'
                   u'\tbarnDoors  - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                   u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t',
    'timestamp': '2015-12-15 19:07:47', 'repo': '', 'is_current': False, 'is_latest': True, 'metadata': {},
    'snapshot_type': 'file', 'server': '', 'search_type': 'exam/props?project=exam',
    'snapshot': u'<snapshot timestamp="Tue Dec 15 22:07:47 2015" context="Modeling" '
                u'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n  '
                u'<file file_code="FILE00000154" name="Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling_v001.ma" '
                u'type="main"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000041', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 41, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000041', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000142',
        '__search_type__': 'sthpw/file', 'file_name': 'Oculus_transfer_v001.ma',
        'snapshot_code': 'SNAPSHOT00000041', 'project_code': 'exam', 'id': 142,
        'base_type': 'file', 'st_size': 4314,
        '__search_key__': 'sthpw/file?code=FILE00000142', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Texturing/versions',
        'timestamp': '2015-12-15 13:51:26', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing/versions',
        'md5': '3bd526ccf7cfd215d0aed8573fae14f6', 'base_dir_alias': '',
        'source_path': 'transfer.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000146',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_98736900_korol21_icon_v001_icon.png',
        'snapshot_code': 'SNAPSHOT00000041', 'project_code': 'exam', 'id': 146,
        'base_type': 'file', 'st_size': 23929,
        '__search_key__': 'sthpw/file?code=FILE00000146', 'type': 'icon',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Texturing/versions',
        'timestamp': '2015-12-15 15:20:43', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing/versions',
        'md5': 'a7d0700a49c43e089d3b079f545d36ee', 'base_dir_alias': '',
        'source_path': '98736900_korol21.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'transfer', 'timestamp': '2015-12-15 13:51:26',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Tue Dec 15 18:20:43 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000142" name="Oculus_transfer_v001.ma" type="main"/>\n  <file '
                'file_code="FILE00000146" name="Oculus_98736900_korol21_icon_v001_icon.png" '
                'type="icon"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000042', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 42, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000042', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000147', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_transfer.ma', 'snapshot_code': 'SNAPSHOT00000042',
        'project_code': '', 'id': 147, 'base_type': 'file', 'st_size': 4314,
        '__search_key__': 'sthpw/file?code=FILE00000147', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Texturing',
        'timestamp': '2015-12-15 15:20:44', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000148', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_98736900_korol21_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000042', 'project_code': '', 'id': 148,
        'base_type': 'file', 'st_size': 23929,
        '__search_key__': 'sthpw/file?code=FILE00000148', 'type': 'icon',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Texturing',
        'timestamp': '2015-12-15 15:20:44', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000149',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_98736900_korol21_icon_icon.png',
        'snapshot_code': 'SNAPSHOT00000042', 'project_code': 'exam', 'id': 149,
        'base_type': 'file', 'st_size': 23929,
        '__search_key__': 'sthpw/file?code=FILE00000149', 'type': 'icon',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/Texturing',
        'timestamp': '2015-12-15 15:20:51', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
        'md5': 'a7d0700a49c43e089d3b079f545d36ee', 'base_dir_alias': '',
        'source_path': '98736900_korol21.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-15 13:51:26',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000041" timestamp="Tue Dec 15 18:20:51 2015" '
                'context="Texturing" search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" '
                'checkin_type="strict">\n  <file file_code="FILE00000147" name="Oculus_transfer.ma" type="main"/>\n  '
                '<file file_code="FILE00000148" name="Oculus_98736900_korol21_icon.jpg" type="icon"/>\n  <file '
                'file_code="FILE00000149" name="Oculus_98736900_korol21_icon_icon.png" type="icon"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000038', '__search_type__': 'sthpw/snapshot', 'process': 'icon',
    's_status': '', 'id': 38, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000038', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000130', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_oculus.jpg', 'snapshot_code': 'SNAPSHOT00000038',
        'project_code': '', 'id': 130, 'base_type': 'file', 'st_size': 168148,
        '__search_key__': 'sthpw/file?code=FILE00000130', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/icon',
        'timestamp': '2015-12-15 13:50:04', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000131', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_oculus_web_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000038', 'project_code': '', 'id': 131,
        'base_type': 'file', 'st_size': 27040,
        '__search_key__': 'sthpw/file?code=FILE00000131', 'type': 'icon',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/icon',
        'timestamp': '2015-12-15 13:50:04', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000132', '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_oculus_icon_web.png',
        'snapshot_code': 'SNAPSHOT00000038', 'project_code': '', 'id': 132,
        'base_type': 'file', 'st_size': 18486,
        '__search_key__': 'sthpw/file?code=FILE00000132', 'type': 'web',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/icon',
        'timestamp': '2015-12-15 13:50:04', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-15 13:50:04',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000037">\n  <file file_code="FILE00000130" '
                'name="Oculus_oculus.jpg" type="main"/>\n  <file file_code="FILE00000131" '
                'name="Oculus_oculus_web_icon.jpg" type="icon"/>\n  <file file_code="FILE00000132" '
                'name="Oculus_oculus_icon_web.png" type="web"/>\n</snapshot>\n',
    'context': 'icon', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000037', '__search_type__': 'sthpw/snapshot', 'process': 'icon',
    's_status': '', 'id': 37, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00001',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000037', 'level_type': '', 'search_id': 1, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000124',
        '__search_type__': 'sthpw/file', 'file_name': 'Oculus_oculus_v001.jpg',
        'snapshot_code': 'SNAPSHOT00000037', 'project_code': 'exam', 'id': 124,
        'base_type': 'file', 'st_size': 168148,
        '__search_key__': 'sthpw/file?code=FILE00000124', 'type': 'main',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/icon/versions',
        'timestamp': '2015-12-15 13:50:03', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
        'md5': 'f4846ef8bce3ddca60091884ae0c93b6', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000125',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_oculus_web_v001_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000037', 'project_code': 'exam', 'id': 125,
        'base_type': 'file', 'st_size': 27040,
        '__search_key__': 'sthpw/file?code=FILE00000125', 'type': 'icon',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/icon/versions',
        'timestamp': '2015-12-15 13:50:03', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
        'md5': 'af338f9a79b107f7fb1fff078561e02c', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus_web.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000126',
        '__search_type__': 'sthpw/file',
        'file_name': 'Oculus_oculus_icon_v001_web.png',
        'snapshot_code': 'SNAPSHOT00000037', 'project_code': 'exam', 'id': 126,
        'base_type': 'file', 'st_size': 18486,
        '__search_key__': 'sthpw/file?code=FILE00000126', 'type': 'web',
        'search_id': 1, 'metadata': {},
        'relative_dir': 'exam/props/Oculus/work/icon/versions',
        'timestamp': '2015-12-15 13:50:03', 'file_range': '',
        'search_code': 'PROPS00001',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
        'md5': 'bc348db0751c0018d81440811de46b28', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus_icon.png',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Initial insert', 'timestamp': '2015-12-15 13:50:03',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Tue Dec 15 16:50:03 2015" context="icon" '
                'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000124" name="Oculus_oculus_v001.jpg" type="main"/>\n  <file '
                'file_code="FILE00000125" name="Oculus_oculus_web_v001_icon.jpg" type="icon"/>\n  <file '
                'file_code="FILE00000126" name="Oculus_oculus_icon_v001_web.png" type="web"/>\n</snapshot>\n',
    'context': 'icon', 'login': 'admin', 'column_name': 'preview'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000036', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 36, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 3,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000036', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000115',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_roundflower_v003.jpg',
        'snapshot_code': 'SNAPSHOT00000036', 'project_code': 'exam', 'id': 115,
        'base_type': 'file', 'st_size': 28028,
        '__search_key__': 'sthpw/file?code=FILE00000115', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing/versions',
        'timestamp': '2015-12-15 13:37:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
        'md5': 'af9206b7d4ae8ac80a749934aad01fe9', 'base_dir_alias': '',
        'source_path': 'roundflower.jpg', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000116',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_roundflower_web_v003_web.jpg',
        'snapshot_code': 'SNAPSHOT00000036', 'project_code': 'exam', 'id': 116,
        'base_type': 'file', 'st_size': 11524,
        '__search_key__': 'sthpw/file?code=FILE00000116', 'type': 'web',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing/versions',
        'timestamp': '2015-12-15 13:37:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
        'md5': '0b341d7fe7f61fb57f9ae6880a110f65', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/f4b72552d33c2f2c416250afd4aecbc1/roundflower_web.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000117',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_roundflower_icon_v003_icon.png',
        'snapshot_code': 'SNAPSHOT00000036', 'project_code': 'exam', 'id': 117,
        'base_type': 'file', 'st_size': 11841,
        '__search_key__': 'sthpw/file?code=FILE00000117', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing/versions',
        'timestamp': '2015-12-15 13:37:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
        'md5': '096ead5ab10efa815f73efa45ea5811d', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/f4b72552d33c2f2c416250afd4aecbc1/roundflower_icon.png',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'No comment', 'timestamp': '2015-12-15 13:37:29',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Tue Dec 15 16:37:29 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000115" name="Flower_roundflower_v003.jpg" type="main"/>\n  <file '
                'file_code="FILE00000116" name="Flower_roundflower_web_v003_web.jpg" type="web"/>\n  <file '
                'file_code="FILE00000117" name="Flower_roundflower_icon_v003_icon.png" type="icon"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000035', '__search_type__': 'sthpw/snapshot', 'process': 'icon',
    's_status': '', 'id': 35, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000035', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000112', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_floweer.jpg', 'snapshot_code': 'SNAPSHOT00000035',
        'project_code': '', 'id': 112, 'base_type': 'file', 'st_size': 11251065,
        '__search_key__': 'sthpw/file?code=FILE00000112', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/icon',
        'timestamp': '2015-12-15 12:39:49', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000113', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_floweer_web_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000035', 'project_code': '', 'id': 113,
        'base_type': 'file', 'st_size': 51042,
        '__search_key__': 'sthpw/file?code=FILE00000113', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/icon',
        'timestamp': '2015-12-15 12:39:49', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000114', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_floweer_icon_web.png',
        'snapshot_code': 'SNAPSHOT00000035', 'project_code': '', 'id': 114,
        'base_type': 'file', 'st_size': 23357,
        '__search_key__': 'sthpw/file?code=FILE00000114', 'type': 'web',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/icon',
        'timestamp': '2015-12-15 12:39:49', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-15 12:39:49',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000034">\n  <file file_code="FILE00000112" '
                'name="Flower_floweer.jpg" type="main"/>\n  <file file_code="FILE00000113" '
                'name="Flower_floweer_web_icon.jpg" type="icon"/>\n  <file file_code="FILE00000114" '
                'name="Flower_floweer_icon_web.png" type="web"/>\n</snapshot>\n',
    'context': 'icon', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000034', '__search_type__': 'sthpw/snapshot', 'process': 'icon',
    's_status': '', 'id': 34, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000034', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000106',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_floweer_v001.jpg',
        'snapshot_code': 'SNAPSHOT00000034', 'project_code': 'exam', 'id': 106,
        'base_type': 'file', 'st_size': 11251065,
        '__search_key__': 'sthpw/file?code=FILE00000106', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/icon/versions',
        'timestamp': '2015-12-15 12:39:47', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon/versions',
        'md5': '5b89b22b0ac37f2b3803d7d00a59d778', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/floweer.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000107',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_floweer_web_v001_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000034', 'project_code': 'exam', 'id': 107,
        'base_type': 'file', 'st_size': 51042,
        '__search_key__': 'sthpw/file?code=FILE00000107', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/icon/versions',
        'timestamp': '2015-12-15 12:39:47', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon/versions',
        'md5': '7f5fe4888a6bee2224ca45a1f8a33f36', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/floweer_web.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000108',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_floweer_icon_v001_web.png',
        'snapshot_code': 'SNAPSHOT00000034', 'project_code': 'exam', 'id': 108,
        'base_type': 'file', 'st_size': 23357,
        '__search_key__': 'sthpw/file?code=FILE00000108', 'type': 'web',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/icon/versions',
        'timestamp': '2015-12-15 12:39:47', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon/versions',
        'md5': 'e427ffc50e5e64b8966f1ffbef5a3cc0', 'base_dir_alias': '',
        'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                       'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/floweer_icon.png',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Initial insert', 'timestamp': '2015-12-15 12:39:47',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Tue Dec 15 15:39:47 2015" context="icon" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000106" name="Flower_floweer_v001.jpg" type="main"/>\n  <file '
                'file_code="FILE00000107" name="Flower_floweer_web_v001_icon.jpg" type="icon"/>\n  <file '
                'file_code="FILE00000108" name="Flower_floweer_icon_v001_web.png" type="web"/>\n</snapshot>\n',
    'context': 'icon', 'login': 'admin', 'column_name': 'preview'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000033', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 33, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000033', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000097',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_flowers_v002.jpg',
        'snapshot_code': 'SNAPSHOT00000033', 'project_code': 'exam', 'id': 97,
        'base_type': 'file', 'st_size': 27582,
        '__search_key__': 'sthpw/file?code=FILE00000097', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs/versions',
        'timestamp': '2015-12-12 11:11:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
        'md5': '3dee2494e17171a904769aa91b47462e', 'base_dir_alias': '',
        'source_path': 'flowers.jpg', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000098',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_flowers_web_v002_web.jpg',
        'snapshot_code': 'SNAPSHOT00000033', 'project_code': 'exam', 'id': 98,
        'base_type': 'file', 'st_size': 16440,
        '__search_key__': 'sthpw/file?code=FILE00000098', 'type': 'web',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs/versions',
        'timestamp': '2015-12-12 11:11:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
        'md5': '2a23a73df00e7c05fe24148faaa9ee8b', 'base_dir_alias': '',
        'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                       'title)\\root/temp/upload/46b4d74b3cc052d2474865dcc660485a/flowers_web.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000099',
        '__search_type__': 'sthpw/file',
        'file_name': 'Flower_flowers_icon_v002_icon.png',
        'snapshot_code': 'SNAPSHOT00000033', 'project_code': 'exam', 'id': 99,
        'base_type': 'file', 'st_size': 14738,
        '__search_key__': 'sthpw/file?code=FILE00000099', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs/versions',
        'timestamp': '2015-12-12 11:11:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
        'md5': '34f64bd4dfe3d8f2c14e5a55ea941d8b', 'base_dir_alias': '',
        'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                       'title)\\root/temp/upload/46b4d74b3cc052d2474865dcc660485a/flowers_icon.png',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'No comment', 'timestamp': '2015-12-12 11:11:29',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 12 14:11:29 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000097" name="Flower_flowers_v002.jpg" type="main"/>\n  <file '
                'file_code="FILE00000098" name="Flower_flowers_web_v002_web.jpg" type="web"/>\n  <file '
                'file_code="FILE00000099" name="Flower_flowers_icon_v002_icon.png" type="icon"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000032', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 32, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000032', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000094',
        '__search_type__': 'sthpw/file', 'file_name': 'Mushroom_mushroom_v002.ma',
        'snapshot_code': 'SNAPSHOT00000032', 'project_code': 'exam', 'id': 94,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000094', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
        'timestamp': '2015-12-12 10:48:25', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing/versions',
        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
        'source_path': 'mushroom.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'Fix some overlapping uvs',
    'timestamp': '2015-12-12 10:48:25', 'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {},
    'snapshot_type': 'file', 'server': '', 'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 12 13:48:25 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000094" name="Mushroom_mushroom_v002.ma" type="main"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000030', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 30, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000030', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000091',
        '__search_type__': 'sthpw/file', 'file_name': 'Mushroom_mushroom_v001.ma',
        'snapshot_code': 'SNAPSHOT00000030', 'project_code': 'exam', 'id': 91,
        'base_type': 'file', 'st_size': 897549,
        '__search_key__': 'sthpw/file?code=FILE00000091', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
        'timestamp': '2015-12-12 10:48:09', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing/versions',
        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
        'source_path': 'mushroom.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'First tex', 'timestamp': '2015-12-12 10:48:09',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 12 13:48:09 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000091" name="Mushroom_mushroom_v001.ma" type="main"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000029', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 29, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000029', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000088',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_flower_v002.ma',
        'snapshot_code': 'SNAPSHOT00000029', 'project_code': 'exam', 'id': 88,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000088', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing/versions',
        'timestamp': '2015-12-12 10:47:50', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'More tex', 'timestamp': '2015-12-12 10:47:50',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 12 13:47:50 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000088" name="Flower_flower_v002.ma" type="main"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000027', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 27, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000027', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000085',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_flower_v001.ma',
        'snapshot_code': 'SNAPSHOT00000027', 'project_code': 'exam', 'id': 85,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000085', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing/versions',
        'timestamp': '2015-12-12 10:47:14', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'FloWer Tex', 'timestamp': '2015-12-12 10:47:14',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 12 13:47:14 2015" context="Texturing" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000085" name="Flower_flower_v001.ma" type="main"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000028', '__search_type__': 'sthpw/snapshot', 'process': 'Texturing',
    's_status': '', 'id': 28, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000028', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000121', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_roundflower.jpg', 'snapshot_code': 'SNAPSHOT00000028',
        'project_code': '', 'id': 121, 'base_type': 'file', 'st_size': 28028,
        '__search_key__': 'sthpw/file?code=FILE00000121', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing',
        'timestamp': '2015-12-15 13:37:30', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000122', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_roundflower_web_web.jpg',
        'snapshot_code': 'SNAPSHOT00000028', 'project_code': '', 'id': 122,
        'base_type': 'file', 'st_size': 11524,
        '__search_key__': 'sthpw/file?code=FILE00000122', 'type': 'web',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing',
        'timestamp': '2015-12-15 13:37:30', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000123', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_roundflower_icon_icon.png',
        'snapshot_code': 'SNAPSHOT00000028', 'project_code': '', 'id': 123,
        'base_type': 'file', 'st_size': 11841,
        '__search_key__': 'sthpw/file?code=FILE00000123', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Texturing',
        'timestamp': '2015-12-15 13:37:30', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-12 10:47:14',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000036">\n  <file file_code="FILE00000121" '
                'name="Flower_roundflower.jpg" type="main"/>\n  <file file_code="FILE00000122" '
                'name="Flower_roundflower_web_web.jpg" type="web"/>\n  <file file_code="FILE00000123" '
                'name="Flower_roundflower_icon_icon.png" type="icon"/>\n</snapshot>\n',
    'context': 'Texturing', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000025', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 25, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000025', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000082',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_flower_v001.ma',
        'snapshot_code': 'SNAPSHOT00000025', 'project_code': 'exam', 'id': 82,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000082', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Modeling/versions',
        'timestamp': '2015-12-12 10:46:59', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000473',
        '__search_type__': 'sthpw/file',
        'file_name': '98736900_korol21_icon_Modeling_v001.png',
        'snapshot_code': 'SNAPSHOT00000025', 'project_code': 'exam', 'id': 473,
        'base_type': 'file', 'st_size': 23929,
        '__search_key__': 'sthpw/file?code=FILE00000473', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Modeling/versions',
        'timestamp': '2015-12-23 09:48:07', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling/versions',
        'md5': 'a7d0700a49c43e089d3b079f545d36ee', 'base_dir_alias': '',
        'source_path': '98736900_korol21.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Flower MOD', 'timestamp': '2015-12-12 10:46:59',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Wed Dec 23 12:48:07 2015" context="Modeling" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000082" name="Flower_flower_v001.ma" type="main"/>\n  <file '
                'file_code="FILE00000473" name="98736900_korol21_icon_Modeling_v001.png" type="icon"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000026', '__search_type__': 'sthpw/snapshot', 'process': 'Modeling',
    's_status': '', 'id': 26, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000026', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000474', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_Modeling.ma', 'snapshot_code': 'SNAPSHOT00000026',
        'project_code': '', 'id': 474, 'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000474', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Modeling',
        'timestamp': '2015-12-23 09:48:07', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000475', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_Modeling_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000026', 'project_code': '', 'id': 475,
        'base_type': 'file', 'st_size': 23929,
        '__search_key__': 'sthpw/file?code=FILE00000475', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Modeling',
        'timestamp': '2015-12-23 09:48:08', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-12 10:46:59',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000025">\n  <file file_code="FILE00000474" '
                'name="Flower_Modeling.ma" type="main"/>\n  <file file_code="FILE00000475" '
                'name="Flower_Modeling_icon.jpg" type="icon"/>\n</snapshot>\n',
    'context': 'Modeling', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000023', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 23, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000023', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000079',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_flower_v001.ma',
        'snapshot_code': 'SNAPSHOT00000023', 'project_code': 'exam', 'id': 79,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000079', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Sculpt/versions',
        'timestamp': '2015-12-12 10:46:43', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000476',
        '__search_type__': 'sthpw/file',
        'file_name': 'ep15Set_masterscene_light_sc01_icon_Sculpt_v001.png',
        'snapshot_code': 'SNAPSHOT00000023', 'project_code': 'exam', 'id': 476,
        'base_type': 'file', 'st_size': 16355,
        '__search_key__': 'sthpw/file?code=FILE00000476', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Sculpt/versions',
        'timestamp': '2015-12-23 09:59:02', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt/versions',
        'md5': '5ca9bcbddd74d8b6345afa8b95eb82fa', 'base_dir_alias': '',
        'source_path': 'ep15Set_masterscene_light_sc01.png',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Flower Sculpt', 'timestamp': '2015-12-12 10:46:43',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Wed Dec 23 12:59:02 2015" context="Sculpt" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000079" name="Flower_flower_v001.ma" type="main"/>\n  <file '
                'file_code="FILE00000476" name="ep15Set_masterscene_light_sc01_icon_Sculpt_v001.png" '
                'type="icon"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000024', '__search_type__': 'sthpw/snapshot', 'process': 'Sculpt',
    's_status': '', 'id': 24, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000024', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000477', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_Sculpt.ma', 'snapshot_code': 'SNAPSHOT00000024',
        'project_code': '', 'id': 477, 'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000477', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Sculpt',
        'timestamp': '2015-12-23 09:59:02', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000478', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_Sculpt_icon.png', 'snapshot_code': 'SNAPSHOT00000024',
        'project_code': '', 'id': 478, 'base_type': 'file', 'st_size': 16355,
        '__search_key__': 'sthpw/file?code=FILE00000478', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Sculpt',
        'timestamp': '2015-12-23 09:59:02', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-12 10:46:43',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000023">\n  <file file_code="FILE00000477" '
                'name="Flower_Sculpt.ma" type="main"/>\n  <file file_code="FILE00000478" '
                'name="Flower_Sculpt_icon.png" type="icon"/>\n</snapshot>\n',
    'context': 'Sculpt', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000022', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 22, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000022', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000103', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_flowers.jpg', 'snapshot_code': 'SNAPSHOT00000022',
        'project_code': '', 'id': 103, 'base_type': 'file', 'st_size': 27582,
        '__search_key__': 'sthpw/file?code=FILE00000103', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs',
        'timestamp': '2015-12-12 11:11:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000104', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_flowers_web_web.jpg',
        'snapshot_code': 'SNAPSHOT00000022', 'project_code': '', 'id': 104,
        'base_type': 'file', 'st_size': 16440,
        '__search_key__': 'sthpw/file?code=FILE00000104', 'type': 'web',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs',
        'timestamp': '2015-12-12 11:11:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000105', '__search_type__': 'sthpw/file',
        'file_name': 'Flower_flowers_icon_icon.png',
        'snapshot_code': 'SNAPSHOT00000022', 'project_code': '', 'id': 105,
        'base_type': 'file', 'st_size': 14738,
        '__search_key__': 'sthpw/file?code=FILE00000105', 'type': 'icon',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs',
        'timestamp': '2015-12-12 11:11:29', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-12-12 10:46:22',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000033">\n  <file file_code="FILE00000103" '
                'name="Flower_flowers.jpg" type="main"/>\n  <file file_code="FILE00000104" '
                'name="Flower_flowers_web_web.jpg" type="web"/>\n  <file file_code="FILE00000105" '
                'name="Flower_flowers_icon_icon.png" type="icon"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000021', '__search_type__': 'sthpw/snapshot', 'process': 'Refs',
    's_status': '', 'id': 21, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00003',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000021', 'level_type': '', 'search_id': 3, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000076',
        '__search_type__': 'sthpw/file', 'file_name': 'Flower_flower_v001.ma',
        'snapshot_code': 'SNAPSHOT00000021', 'project_code': 'exam', 'id': 76,
        'base_type': 'file', 'st_size': 255075,
        '__search_key__': 'sthpw/file?code=FILE00000076', 'type': 'main',
        'search_id': 3, 'metadata': {},
        'relative_dir': 'exam/props/Flower/work/Refs/versions',
        'timestamp': '2015-12-12 10:46:20', 'file_range': '',
        'search_code': 'PROPS00003',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
        'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
        'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
        'metadata_search': ''
    }], 'description': 'Flower REF', 'timestamp': '2015-12-12 10:46:20',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sat Dec 12 13:46:20 2015" context="Refs" '
                'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000076" name="Flower_flower_v001.ma" type="main"/>\n</snapshot>\n',
    'context': 'Refs', 'login': 'admin', 'column_name': 'snapshot'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000015', '__search_type__': 'sthpw/snapshot', 'process': 'icon',
    's_status': '', 'id': 15, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000015', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': 'tactic', 'code': 'FILE00000052',
        '__search_type__': 'sthpw/file', 'file_name': 'Mushroom_mushroom_v002.jpg',
        'snapshot_code': 'SNAPSHOT00000015', 'project_code': 'exam', 'id': 52,
        'base_type': 'file', 'st_size': 278007,
        '__search_key__': 'sthpw/file?code=FILE00000052', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/icon/versions',
        'timestamp': '2015-11-29 19:03:36', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon/versions',
        'md5': '0e51bc2a8d2e0cfa6c47067747233a39', 'base_dir_alias': '',
        'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                       'title)\\root/temp/upload/80a542b57944b77ac72ba95ddbdbfbc6/mushroom.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000053',
        '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_mushroom_web_v002_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000015', 'project_code': 'exam', 'id': 53,
        'base_type': 'file', 'st_size': 45539,
        '__search_key__': 'sthpw/file?code=FILE00000053', 'type': 'icon',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/icon/versions',
        'timestamp': '2015-11-29 19:03:36', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon/versions',
        'md5': '8ca4c3d336d02af56b22264c72ed9331', 'base_dir_alias': '',
        'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                       'title)\\root/temp/upload/80a542b57944b77ac72ba95ddbdbfbc6/mushroom_web.jpg',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': 'tactic', 'code': 'FILE00000054',
        '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_mushroom_icon_v002_web.png',
        'snapshot_code': 'SNAPSHOT00000015', 'project_code': 'exam', 'id': 54,
        'base_type': 'file', 'st_size': 25475,
        '__search_key__': 'sthpw/file?code=FILE00000054', 'type': 'web',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/icon/versions',
        'timestamp': '2015-11-29 19:03:36', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon/versions',
        'md5': '85ff96759c1bff8a0ba7bad1b054d9d9', 'base_dir_alias': '',
        'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                       'title)\\root/temp/upload/80a542b57944b77ac72ba95ddbdbfbc6/mushroom_icon.png',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'No comment', 'timestamp': '2015-11-29 19:03:36',
    'repo': '', 'is_current': True, 'is_latest': True, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot timestamp="Sun Nov 29 22:03:36 2015" context="icon" '
                'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n  '
                '<file file_code="FILE00000052" name="Mushroom_mushroom_v002.jpg" type="main"/>\n  <file '
                'file_code="FILE00000053" name="Mushroom_mushroom_web_v002_icon.jpg" type="icon"/>\n  <file '
                'file_code="FILE00000054" name="Mushroom_mushroom_icon_v002_web.png" type="web"/>\n</snapshot>\n',
    'context': 'icon', 'login': 'admin', 'column_name': 'preview'
}, {
    'is_synced': True, 'code': 'SNAPSHOT00000014', '__search_type__': 'sthpw/snapshot', 'process': 'icon',
    's_status': '', 'id': 14, 'project_code': 'exam', 'lock_date': '', 'search_code': 'PROPS00002',
    'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
    '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000014', 'level_type': '', 'search_id': 2, 'revision': 0,
    'status': '', '__files__': [{
        'repo_type': '', 'code': 'FILE00000058', '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_mushroom.jpg', 'snapshot_code': 'SNAPSHOT00000014',
        'project_code': '', 'id': 58, 'base_type': 'file', 'st_size': 278007,
        '__search_key__': 'sthpw/file?code=FILE00000058', 'type': 'main',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/icon',
        'timestamp': '2015-11-29 19:03:37', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000059', '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_mushroom_web_icon.jpg',
        'snapshot_code': 'SNAPSHOT00000014', 'project_code': '', 'id': 59,
        'base_type': 'file', 'st_size': 45539,
        '__search_key__': 'sthpw/file?code=FILE00000059', 'type': 'icon',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/icon',
        'timestamp': '2015-11-29 19:03:37', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }, {
        'repo_type': '', 'code': 'FILE00000060', '__search_type__': 'sthpw/file',
        'file_name': 'Mushroom_mushroom_icon_web.png',
        'snapshot_code': 'SNAPSHOT00000014', 'project_code': '', 'id': 60,
        'base_type': 'file', 'st_size': 25475,
        '__search_key__': 'sthpw/file?code=FILE00000060', 'type': 'web',
        'search_id': 2, 'metadata': {},
        'relative_dir': 'exam/props/Mushroom/work/icon',
        'timestamp': '2015-11-29 19:03:37', 'file_range': '',
        'search_code': 'PROPS00002',
        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon',
        'md5': '', 'base_dir_alias': '', 'source_path': '',
        'search_type': 'exam/props?project=exam', 'metadata_search': ''
    }], 'description': 'Versionless', 'timestamp': '2015-11-29 19:01:28',
    'repo': '', 'is_current': False, 'is_latest': False, 'metadata': {}, 'snapshot_type': 'file', 'server': '',
    'search_type': 'exam/props?project=exam',
    'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000015">\n  <file file_code="FILE00000058" '
                'name="Mushroom_mushroom.jpg" type="main"/>\n  <file file_code="FILE00000059" '
                'name="Mushroom_mushroom_web_icon.jpg" type="icon"/>\n  <file file_code="FILE00000060" '
                'name="Mushroom_mushroom_icon_web.png" type="web"/>\n</snapshot>\n',
    'context': 'icon', 'login': 'admin', 'column_name': 'snapshot'
}]
result_dict = {}
time1 = time.time()

for q in query:
    # print(q)
    for a in q.iteritems():
        # print([a])
        for key, value in [a]:
            # print(value)
            result_dict.setdefault(key, []).append(value)
# print(time.time()-time1)
# print(result_dict)


time2 = time.time()


def snapshots_query(process=None, code=None, snapshots=None):
    """
    Query for snapshonts belongs to asset
    :return:
    """
    # TODO: Refactor all the crazy and redundant logic
    process_codes = list(process)
    process_codes.append('icon')

    def get_snapshot_dict(sn_code, in_dict):
        """
        Getting info from each snapshot, and return as structured dictionary
        :param sn_code: individual snapshot code
        :param in_dict: query for current snapshot from base
        :return: structured dictionary tree
        """

        snapshots_list = []
        for dic in in_dict:
            if sn_code in dic['code']:
                sn_dict_get = dic.get

                snapshots_list.extend([dict(
                    code=sn_code,
                    snapshot=get_snapshot_file_codes(
                        sn_dict_get('__files__'),
                        sn_dict_get('context'),
                        sn_dict_get('description'),
                        sn_dict_get('login'),
                        sn_dict_get('column_name'),
                        sn_dict_get('search_code'),
                        sn_dict_get('is_current'),
                        sn_dict_get('is_latest'),
                        sn_dict_get('revision'),
                        sn_dict_get('version'),
                        sn_dict_get('process')),
                )])

        return snapshots_list

    def get_snapshot_file_codes(in_dict, context, description,
                                login, column_name, search_code,
                                is_current, is_latest, revision,
                                version, process):
        """
        Getting all file info from __files__
        :param in_dict:
        :param context:
        :param description:
        :param login:
        :param column_name:
        :param search_code:
        :param is_current:
        :param is_latest:
        :param revision:
        :param version:
        :param process:
        :return:
        """
        files_list = []

        for dic in in_dict:
            fl_get = dic.get
            files_list.extend([dict(
                context=context,
                code=fl_get('code'),
                file_name=fl_get('file_name'),
                type=fl_get('type'),
                st_size=sizes(fl_get('st_size')),
                timestamp=fl_get('timestamp'),
                relative_dir=fl_get('relative_dir'),
                description=description,
                column_name=column_name,
                search_code=search_code,
                is_current=is_current,
                is_latest=is_latest,
                revision=revision,
                version=version,
                process=process,
                login=login,
            )])

        return files_list

    dict_result = {}
    dict_final = {}

    # Walking through asset codes list
    for prop_code in code:
        dict_result[prop_code] = dict(code=[], process=[])
        # Iterating snapshots
        for iter_dict in snapshots:

            if iter_dict.get('search_code') == prop_code:
                dict_result[prop_code]['process'].append(iter_dict.get('process'))
                dict_result[prop_code]['code'].append(iter_dict.get('code'))

        dict_final[prop_code] = {}
        process_codes_pairs = zip(dict_result[prop_code]['process'], dict_result[prop_code]['code'])

        for process in process_codes:
            # walking through process, per asset
            process_result = {process: []}

            # TODO: this require more optimizations
            for process_single, dict_single in process_codes_pairs:
                if process_single == process:
                    process_result[process].extend(get_snapshot_dict(dict_single, snapshots))
            dict_final[prop_code][process] = process_result[process]

    return dict_final


asdf = snapshots_query(['Modeling', 'Refs', 'Texturing', 'Sculpt', 'icon'], ['PROPS00001', 'PROPS00002', 'PROPS00003'],
                       query)

# print(asdf)
print(time.time() - time2)

result_needed = {
    u'PROPS00001': {
        'Modeling': [
            {
                'files': [
                    {
                        'repo_type': 'tactic', 'code': 'FILE00000264', '__search_type__': 'sthpw/file',
                        'file_name': 'verts_Modeling_v002.ma', 'snapshot_code': 'SNAPSHOT00000108',
                        'project_code': 'exam', 'id': 264, 'base_type': 'file', 'st_size': 897549,
                        '__search_key__': 'sthpw/file?code=FILE00000264', 'type': 'main', 'search_id': 1,
                        'metadata': {}, 'relative_dir': 'exam/props/Oculus/work/Modeling/versions',
                        'timestamp': '2015-12-19 12:13:56', 'file_range': '',
                        'search_code': 'PROPS00001',
                        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                       'title)\\root/exam/props/Oculus/work/Modeling/versions',
                        'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
                        'source_path': 'verts.ma', 'search_type': 'exam/props?project=exam',
                        'metadata_search': ''
                    }
                ],
                'code': 'SNAPSHOT00000108', 'search_code': 'PROPS00001',
                'description': 'VERTICES', 'process': 'Modeling', 'column_name': 'snapshot', 'version': 2,
                'is_current': True, 'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Modeling/versions',
                'code': 'FILE00000264',
                'description': 'VERTICES',
                'timestamp': '2015-12-19 12:13:56',
                'st_size': '876.51 Kb',
                'context': 'Modeling',
                'file_name': 'verts_Modeling_v002.ma',
                'login': 'admin', 'type': 'main'
            }
            ],
                'login': 'admin',
                'is_latest': True, 'revision': 0
            },
            {
                'files': [
                    {
                        'repo_type': '', 'code': 'FILE00000266', '__search_type__': 'sthpw/file',
                        'file_name': 'Oculus_verts_Modeling.ma', 'snapshot_code': 'SNAPSHOT00000107',
                        'project_code': '', 'id': 266, 'base_type': 'file', 'st_size': 897549,
                        '__search_key__': 'sthpw/file?code=FILE00000266', 'type': 'main', 'search_id': 1,
                        'metadata': {}, 'relative_dir': 'exam/props/Oculus/work/Modeling',
                        'timestamp': '2015-12-19 12:13:56', 'file_range': '',
                        'search_code': 'PROPS00001',
                        'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Modeling',
                        'md5': '', 'base_dir_alias': '', 'source_path': '',
                        'search_type': 'exam/props?project=exam', 'metadata_search': ''
                    }
                ],
                'code': 'SNAPSHOT00000107', 'search_code': 'PROPS00001',
                'description': 'Versionless', 'process': 'Modeling', 'column_name': 'snapshot', 'version': -1,
                'is_current': False, 'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Modeling',
                'code': 'FILE00000266',
                'description': 'Versionless',
                'timestamp': '2015-12-19 12:13:56',
                'st_size': '876.51 Kb',
                'context': 'Modeling',
                'file_name': 'Oculus_verts_Modeling.ma',
                'login': 'admin', 'type': 'main'
            }
            ],
                'login': 'admin',
                'is_latest': False, 'revision': 0
            },
            {
                'files': [{
                    'repo_type': 'tactic', 'code': 'FILE00000261', '__search_type__': 'sthpw/file',
                    'file_name': 'mesh_Modeling_v001.ma', 'snapshot_code': 'SNAPSHOT00000106',
                    'project_code': 'exam', 'id': 261, 'base_type': 'file', 'st_size': 255075,
                    '__search_key__': 'sthpw/file?code=FILE00000261', 'type': 'main', 'search_id': 1,
                    'metadata': {}, 'relative_dir': 'exam/props/Oculus/work/Modeling/versions',
                    'timestamp': '2015-12-19 12:13:07', 'file_range': '',
                    'search_code': 'PROPS00001',
                    'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                   'title)\\root/exam/props/Oculus/work/Modeling/versions',
                    'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                    'source_path': 'mesh.ma', 'search_type': 'exam/props?project=exam',
                    'metadata_search': ''
                }], 'code': 'SNAPSHOT00000106', 'search_code': 'PROPS00001',
                'description': 'MESHING', 'process': 'Modeling', 'column_name': 'snapshot', 'version': 1,
                'is_current': False, 'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Modeling/versions',
                'code': 'FILE00000261',
                'description': 'MESHING',
                'timestamp': '2015-12-19 12:13:07',
                'st_size': '249.10 Kb',
                'context': 'Modeling',
                'file_name': 'mesh_Modeling_v001.ma',
                'login': 'admin', 'type': 'main'
            }], 'login': 'admin',
                'is_latest': False, 'revision': 0
            }], 'Refs': [{
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000207',
                '__search_type__': 'sthpw/file',
                'file_name': 'flower_Refs_v006.ma',
                'snapshot_code': 'SNAPSHOT00000072', 'project_code': 'exam',
                'id': 207, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000207',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs',
                'timestamp': '2015-12-19 10:46:47', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                'source_path': 'flower.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000072', 'search_code': 'PROPS00001',
            'description': 'sd', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 6, 'is_current': True, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs',
                'code': 'FILE00000207',
                'description': 'sd',
                'timestamp': '2015-12-19 10:46:47',
                'st_size': '249.10 Kb',
                'context': 'Refs',
                'file_name': 'flower_Refs_v006.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': True, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000184',
                '__search_type__': 'sthpw/file',
                'file_name': 'oculus_Refs_v005.ma',
                'snapshot_code': 'SNAPSHOT00000057', 'project_code': 'exam',
                'id': 184, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000184',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'timestamp': '2015-12-19 09:58:12', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                'source_path': 'oculus.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000057', 'search_code': 'PROPS00001',
            'description': 'oculus', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 5, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'code': 'FILE00000184',
                'description': 'oculus',
                'timestamp': '2015-12-19 09:58:12',
                'st_size': '249.10 Kb',
                'context': 'Refs',
                'file_name': 'oculus_Refs_v005.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000181',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_nhair_Refs_v004.ma',
                'snapshot_code': 'SNAPSHOT00000056', 'project_code': 'exam',
                'id': 181, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000181',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'timestamp': '2015-12-19 09:55:39', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                'source_path': 'nhair.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000056', 'search_code': 'PROPS00001',
            'description': 'das', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 4, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'code': 'FILE00000181',
                'description': 'das',
                'timestamp': '2015-12-19 09:55:39',
                'st_size': '249.10 Kb',
                'context': 'Refs',
                'file_name': 'Oculus_nhair_Refs_v004.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000178',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_shave_Refs_v003.ma',
                'snapshot_code': 'SNAPSHOT00000055', 'project_code': 'exam',
                'id': 178, 'base_type': 'file', 'st_size': 897549,
                '__search_key__': 'sthpw/file?code=FILE00000178',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'timestamp': '2015-12-19 09:08:11', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
                'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
                'source_path': 'shave.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000055', 'search_code': 'PROPS00001',
            'description': 'nhair an shave', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 3, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'code': 'FILE00000178',
                'description': 'nhair an shave',
                'timestamp': '2015-12-19 09:08:11',
                'st_size': '876.51 Kb',
                'context': 'Refs',
                'file_name': 'Oculus_shave_Refs_v003.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000175',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_nhair_Refs_v002.ma',
                'snapshot_code': 'SNAPSHOT00000054', 'project_code': 'exam',
                'id': 175, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000175',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'timestamp': '2015-12-19 09:08:09', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                'source_path': 'nhair.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000054', 'search_code': 'PROPS00001',
            'description': 'nhair an shave', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 2, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'code': 'FILE00000175',
                'description': 'nhair an shave',
                'timestamp': '2015-12-19 09:08:09',
                'st_size': '249.10 Kb',
                'context': 'Refs',
                'file_name': 'Oculus_nhair_Refs_v002.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000172',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_shave_Refs_v001.ma',
                'snapshot_code': 'SNAPSHOT00000052', 'project_code': 'exam',
                'id': 172, 'base_type': 'file', 'st_size': 897549,
                '__search_key__': 'sthpw/file?code=FILE00000172',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'timestamp': '2015-12-19 09:07:23', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs/versions',
                'md5': '8357016cee16691cf2ca43bf863c32fb', 'base_dir_alias': '',
                'source_path': 'shave.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000052', 'search_code': 'PROPS00001',
            'description': 'nhair va', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 1, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs/versions',
                'code': 'FILE00000172',
                'description': 'nhair va',
                'timestamp': '2015-12-19 09:07:23',
                'st_size': '876.51 Kb',
                'context': 'Refs',
                'file_name': 'Oculus_shave_Refs_v001.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': '', 'code': 'FILE00000186',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus_Refs.ma',
                'snapshot_code': 'SNAPSHOT00000053', 'project_code': '',
                'id': 186, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000186',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Refs',
                'timestamp': '2015-12-19 09:58:12', 'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Refs',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000053', 'search_code': 'PROPS00001',
            'description': 'Versionless', 'process': 'Refs', 'column_name': 'snapshot',
            'version': -1, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Refs',
                'code': 'FILE00000186',
                'description': 'Versionless',
                'timestamp': '2015-12-19 09:58:12',
                'st_size': '249.10 Kb',
                'context': 'Refs',
                'file_name': 'Oculus_oculus_Refs.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }], 'icon': [{
            'files': [{
                'repo_type': '', 'code': 'FILE00000130',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus.jpg',
                'snapshot_code': 'SNAPSHOT00000038',
                'project_code': '', 'id': 130,
                'base_type': 'file', 'st_size': 168148,
                '__search_key__': 'sthpw/file?code=FILE00000130',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/icon',
                'timestamp': '2015-12-15 13:50:04',
                'file_range': '', 'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon',
                'md5': '', 'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000131',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus_web_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000038',
                'project_code': '', 'id': 131,
                'base_type': 'file', 'st_size': 27040,
                '__search_key__': 'sthpw/file?code=FILE00000131',
                'type': 'icon', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/icon',
                'timestamp': '2015-12-15 13:50:04',
                'file_range': '', 'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon',
                'md5': '', 'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000132',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus_icon_web.png',
                'snapshot_code': 'SNAPSHOT00000038',
                'project_code': '', 'id': 132,
                'base_type': 'file', 'st_size': 18486,
                '__search_key__': 'sthpw/file?code=FILE00000132',
                'type': 'web', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/icon',
                'timestamp': '2015-12-15 13:50:04',
                'file_range': '', 'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon',
                'md5': '', 'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000038',
            'search_code': 'PROPS00001', 'description': 'Versionless',
            'process': 'icon', 'column_name': 'snapshot', 'version': -1,
            'is_current': False, 'context': 'icon', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/icon',
                'code': 'FILE00000130',
                'description': 'Versionless',
                'timestamp': '2015-12-15 13:50:04',
                'st_size': '164.21 Kb',
                'context': 'icon',
                'file_name': 'Oculus_oculus.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Oculus/work/icon',
                'code': 'FILE00000131',
                'description': 'Versionless',
                'timestamp': '2015-12-15 13:50:04',
                'st_size': '26.41 Kb',
                'context': 'icon',
                'file_name': 'Oculus_oculus_web_icon.jpg',
                'login': 'admin',
                'type': 'icon'
            }, {
                'relative_dir': 'exam/props/Oculus/work/icon',
                'code': 'FILE00000132',
                'description': 'Versionless',
                'timestamp': '2015-12-15 13:50:04',
                'st_size': '18.05 Kb',
                'context': 'icon',
                'file_name': 'Oculus_oculus_icon_web.png',
                'login': 'admin',
                'type': 'web'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000124',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus_v001.jpg',
                'snapshot_code': 'SNAPSHOT00000037',
                'project_code': 'exam', 'id': 124,
                'base_type': 'file', 'st_size': 168148,
                '__search_key__': 'sthpw/file?code=FILE00000124',
                'type': 'main', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/icon/versions',
                'timestamp': '2015-12-15 13:50:03',
                'file_range': '', 'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
                'md5': 'f4846ef8bce3ddca60091884ae0c93b6',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000125',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus_web_v001_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000037',
                'project_code': 'exam', 'id': 125,
                'base_type': 'file', 'st_size': 27040,
                '__search_key__': 'sthpw/file?code=FILE00000125',
                'type': 'icon', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/icon/versions',
                'timestamp': '2015-12-15 13:50:03',
                'file_range': '', 'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
                'md5': 'af338f9a79b107f7fb1fff078561e02c',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus_web.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000126',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_oculus_icon_v001_web.png',
                'snapshot_code': 'SNAPSHOT00000037',
                'project_code': 'exam', 'id': 126,
                'base_type': 'file', 'st_size': 18486,
                '__search_key__': 'sthpw/file?code=FILE00000126',
                'type': 'web', 'search_id': 1, 'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/icon/versions',
                'timestamp': '2015-12-15 13:50:03',
                'file_range': '', 'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
                'md5': 'bc348db0751c0018d81440811de46b28',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus_icon.png',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000037',
            'search_code': 'PROPS00001', 'description': 'Initial insert',
            'process': 'icon', 'column_name': 'preview', 'version': 1,
            'is_current': True, 'context': 'icon', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/icon/versions',
                'code': 'FILE00000124',
                'description': 'Initial insert',
                'timestamp': '2015-12-15 13:50:03',
                'st_size': '164.21 Kb',
                'context': 'icon',
                'file_name': 'Oculus_oculus_v001.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Oculus/work/icon/versions',
                'code': 'FILE00000125',
                'description': 'Initial insert',
                'timestamp': '2015-12-15 13:50:03',
                'st_size': '26.41 Kb',
                'context': 'icon',
                'file_name': 'Oculus_oculus_web_v001_icon.jpg',
                'login': 'admin',
                'type': 'icon'
            }, {
                'relative_dir': 'exam/props/Oculus/work/icon/versions',
                'code': 'FILE00000126',
                'description': 'Initial insert',
                'timestamp': '2015-12-15 13:50:03',
                'st_size': '18.05 Kb',
                'context': 'icon',
                'file_name': 'Oculus_oculus_icon_v001_web.png',
                'login': 'admin',
                'type': 'web'
            }],
            'login': 'admin', 'is_latest': True, 'revision': 0
        }], 'Texturing': [{
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000142',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_transfer_v001.ma',
                'snapshot_code': 'SNAPSHOT00000041',
                'project_code': 'exam',
                'id': 142,
                'base_type': 'file',
                'st_size': 4314,
                '__search_key__': 'sthpw/file?code=FILE00000142',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Texturing/versions',
                'timestamp': '2015-12-15 13:51:26',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/exam/props/Oculus/work/Texturing/versions',
                'md5': '3bd526ccf7cfd215d0aed8573fae14f6',
                'base_dir_alias': '',
                'source_path': 'transfer.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic',
                'code': 'FILE00000146',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_98736900_korol21_icon_v001_icon.png',
                'snapshot_code': 'SNAPSHOT00000041',
                'project_code': 'exam',
                'id': 146,
                'base_type': 'file',
                'st_size': 23929,
                '__search_key__': 'sthpw/file?code=FILE00000146',
                'type': 'icon',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Texturing/versions',
                'timestamp': '2015-12-15 15:20:43',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/exam/props/Oculus/work/Texturing/versions',
                'md5': 'a7d0700a49c43e089d3b079f545d36ee',
                'base_dir_alias': '',
                'source_path': '98736900_korol21.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000041',
            'search_code': 'PROPS00001',
            'description': 'transfer',
            'process': 'Texturing',
            'column_name': 'snapshot',
            'version': 1, 'is_current': True,
            'context': 'Texturing', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Texturing/versions',
                'code': 'FILE00000142',
                'description': 'transfer',
                'timestamp': '2015-12-15 13:51:26',
                'st_size': '4.21 Kb',
                'context': 'Texturing',
                'file_name': 'Oculus_transfer_v001.ma',
                'login': 'admin',
                'type': 'main'
            },
                {
                    'relative_dir': 'exam/props/Oculus/work/Texturing/versions',
                    'code': 'FILE00000146',
                    'description': 'transfer',
                    'timestamp': '2015-12-15 15:20:43',
                    'st_size': '23.37 Kb',
                    'context': 'Texturing',
                    'file_name': 'Oculus_98736900_korol21_icon_v001_icon.png',
                    'login': 'admin',
                    'type': 'icon'
                }],
            'login': 'admin', 'is_latest': True,
            'revision': 0
        }, {
            'files': [{
                'repo_type': '',
                'code': 'FILE00000147',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_transfer.ma',
                'snapshot_code': 'SNAPSHOT00000042',
                'project_code': '',
                'id': 147,
                'base_type': 'file',
                'st_size': 4314,
                '__search_key__': 'sthpw/file?code=FILE00000147',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Texturing',
                'timestamp': '2015-12-15 15:20:44',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '',
                'code': 'FILE00000148',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_98736900_korol21_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000042',
                'project_code': '',
                'id': 148,
                'base_type': 'file',
                'st_size': 23929,
                '__search_key__': 'sthpw/file?code=FILE00000148',
                'type': 'icon',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Texturing',
                'timestamp': '2015-12-15 15:20:44',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic',
                'code': 'FILE00000149',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_98736900_korol21_icon_icon.png',
                'snapshot_code': 'SNAPSHOT00000042',
                'project_code': 'exam',
                'id': 149,
                'base_type': 'file',
                'st_size': 23929,
                '__search_key__': 'sthpw/file?code=FILE00000149',
                'type': 'icon',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Texturing',
                'timestamp': '2015-12-15 15:20:51',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
                'md5': 'a7d0700a49c43e089d3b079f545d36ee',
                'base_dir_alias': '',
                'source_path': '98736900_korol21.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000042',
            'search_code': 'PROPS00001',
            'description': 'Versionless',
            'process': 'Texturing',
            'column_name': 'snapshot',
            'version': -1, 'is_current': False,
            'context': 'Texturing', 'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Texturing',
                'code': 'FILE00000147',
                'description': 'Versionless',
                'timestamp': '2015-12-15 15:20:44',
                'st_size': '4.21 Kb',
                'context': 'Texturing',
                'file_name': 'Oculus_transfer.ma',
                'login': 'admin',
                'type': 'main'
            },
                {
                    'relative_dir': 'exam/props/Oculus/work/Texturing',
                    'code': 'FILE00000148',
                    'description': 'Versionless',
                    'timestamp': '2015-12-15 15:20:44',
                    'st_size': '23.37 Kb',
                    'context': 'Texturing',
                    'file_name': 'Oculus_98736900_korol21_icon.jpg',
                    'login': 'admin',
                    'type': 'icon'
                },
                {
                    'relative_dir': 'exam/props/Oculus/work/Texturing',
                    'code': 'FILE00000149',
                    'description': 'Versionless',
                    'timestamp': '2015-12-15 15:20:51',
                    'st_size': '23.37 Kb',
                    'context': 'Texturing',
                    'file_name': 'Oculus_98736900_korol21_icon_icon.png',
                    'login': 'admin',
                    'type': 'icon'
                }],
            'login': 'admin', 'is_latest': False,
            'revision': 0
        }], 'Sculpt': [{
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000169',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_nhair_Sculpt_v004.ma',
                'snapshot_code': 'SNAPSHOT00000051',
                'project_code': 'exam',
                'id': 169,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000169',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'timestamp': '2015-12-19 08:01:45',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'nhair.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000051',
            'search_code': 'PROPS00001',
            'description': 'Back to nhair',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': 4,
            'is_current': True,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'code': 'FILE00000169',
                'description': 'Back to nhair',
                'timestamp': '2015-12-19 08:01:45',
                'st_size': '249.10 Kb',
                'context': 'Sculpt',
                'file_name': 'Oculus_nhair_Sculpt_v004.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin',
            'is_latest': True,
            'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000166',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_shave_Sculpt_v003.ma',
                'snapshot_code': 'SNAPSHOT00000050',
                'project_code': 'exam',
                'id': 166,
                'base_type': 'file',
                'st_size': 897549,
                '__search_key__': 'sthpw/file?code=FILE00000166',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'timestamp': '2015-12-19 07:45:05',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
                'md5': '8357016cee16691cf2ca43bf863c32fb',
                'base_dir_alias': '',
                'source_path': 'shave.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000050',
            'search_code': 'PROPS00001',
            'description': 'Shave Var',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': 3,
            'is_current': False,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'code': 'FILE00000166',
                'description': 'Shave Var',
                'timestamp': '2015-12-19 07:45:05',
                'st_size': '876.51 Kb',
                'context': 'Sculpt',
                'file_name': 'Oculus_shave_Sculpt_v003.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin',
            'is_latest': False,
            'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000163',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_nhair_Sculpt_v002.ma',
                'snapshot_code': 'SNAPSHOT00000049',
                'project_code': 'exam',
                'id': 163,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000163',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'timestamp': '2015-12-18 21:36:02',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'nhair.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000049',
            'search_code': 'PROPS00001',
            'description': 'Another ver',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': 2,
            'is_current': False,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'code': 'FILE00000163',
                'description': 'Another ver',
                'timestamp': '2015-12-18 21:36:02',
                'st_size': '249.10 Kb',
                'context': 'Sculpt',
                'file_name': 'Oculus_nhair_Sculpt_v002.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin',
            'is_latest': False,
            'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000157',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_nhair_Sculpt_v001.ma',
                'snapshot_code': 'SNAPSHOT00000045',
                'project_code': 'exam',
                'id': 157,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000157',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'timestamp': '2015-12-18 20:58:16',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'nhair.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000045',
            'search_code': 'PROPS00001',
            'description': 'nHai Hairs version',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': 1,
            'is_current': False,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Sculpt/versions',
                'code': 'FILE00000157',
                'description': 'nHai Hairs version',
                'timestamp': '2015-12-18 20:58:16',
                'st_size': '249.10 Kb',
                'context': 'Sculpt',
                'file_name': 'Oculus_nhair_Sculpt_v001.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin',
            'is_latest': False,
            'revision': 0
        }, {
            'files': [{
                'repo_type': '',
                'code': 'FILE00000171',
                '__search_type__': 'sthpw/file',
                'file_name': 'Oculus_nhair_Sculpt.ma',
                'snapshot_code': 'SNAPSHOT00000046',
                'project_code': '',
                'id': 171,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000171',
                'type': 'main',
                'search_id': 1,
                'metadata': {},
                'relative_dir': 'exam/props/Oculus/work/Sculpt',
                'timestamp': '2015-12-19 08:01:45',
                'file_range': '',
                'search_code': 'PROPS00001',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/Sculpt',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000046',
            'search_code': 'PROPS00001',
            'description': 'Versionless',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': -1,
            'is_current': False,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Oculus/work/Sculpt',
                'code': 'FILE00000171',
                'description': 'Versionless',
                'timestamp': '2015-12-19 08:01:45',
                'st_size': '249.10 Kb',
                'context': 'Sculpt',
                'file_name': 'Oculus_nhair_Sculpt.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin',
            'is_latest': False,
            'revision': 0
        }]
    }, u'PROPS00002': {
        'Modeling': [{
            'files': [{
                'repo_type': '', 'code': 'FILE00000156', '__search_type__': 'sthpw/file',
                'file_name': u'Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling.ma',
                'snapshot_code': 'SNAPSHOT00000044', 'project_code': '', 'id': 156,
                'base_type': 'file', 'st_size': 117919,
                '__search_key__': 'sthpw/file?code=FILE00000156', 'type': 'main', 'search_id': 2,
                'metadata': {}, 'relative_dir': 'exam/props/Mushroom/work/Modeling',
                'timestamp': '2015-12-15 19:07:49', 'file_range': '',
                'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Modeling',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000044', 'search_code': 'PROPS00002',
            'description': 'Versionless', 'process': 'Modeling', 'column_name': 'snapshot', 'version': -1,
            'is_current': False, 'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/Modeling',
                'code': 'FILE00000156',
                'description': 'Versionless',
                'timestamp': '2015-12-15 19:07:49',
                'st_size': '115.16 Kb',
                'context': 'Modeling',
                'file_name': u'Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling.ma',
                'login': 'admin', 'type': 'main'
            }], 'login': 'admin',
            'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000154', '__search_type__': 'sthpw/file',
                'file_name': u'Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling_v001.ma',
                'snapshot_code': 'SNAPSHOT00000043', 'project_code': 'exam', 'id': 154,
                'base_type': 'file', 'st_size': 117919,
                '__search_key__': 'sthpw/file?code=FILE00000154', 'type': 'main', 'search_id': 2,
                'metadata': {}, 'relative_dir': 'exam/props/Mushroom/work/Modeling/versions',
                'timestamp': '2015-12-15 19:07:47', 'file_range': '',
                'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Modeling/versions',
                'md5': '', 'base_dir_alias': '',
                'source_path': u'\u0431\u0438\u043b\u0435\u04422.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000043', 'search_code': 'PROPS00002',
            'description': u'\t\tIntensity 100 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                           u'\tfromIntensity 1\n\t\ttoIntensity  100000 - \u043a\u043e\u0440\u043e\u0447\u0435, '
                           u'\u0434\u0430\u043b\u0435\u043a\u043e\n\t\tdecayRate 1.6\n\t\tfromLightColor, '
                           u'toLightColor  - \u044d\u0442\u0438 \u0434\u0432\u0430 '
                           u'\u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u0430 '
                           u'\u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c \u0432 \u043e\u0434\u0438\u043d - '
                           u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\tconeAngle '
                           u'300 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                           u'\tpenumbraAngle 10-100 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\tdropOff 3 '
                           u'- \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                           u'\temitDiffuse \n\t\temitSpecular \n\t\t\n\t\t\u042d\u0442\u0438 '
                           u'\u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b \u043d\u0430\u0434\u043e '
                           u'\u0441\u0434\u0435\u043b\u0430\u0442\u044c \u043c\u0435\u043d\u0435\u0435 '
                           u'\u0447\u0443\u0432\u0441\u0442\u0432\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u043c'
                           u'\u0438, \u0441\u0435\u0439\u0447\u0430\u0441 \u043e\u043d\u0438 \u0432\u0441\u0435 '
                           u'\u043a\u0440\u0443\u0442\u044f\u0442\u0441\u044f \u0432 '
                           u'\u0442\u044b\u0441\u044f\u0447\u043d\u044b\u0445 '
                           u'\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f\u0445:\n\t\t\ttrace_bias 0.001 - '
                           u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                           u'\ttrace_blur 0.001 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                           u'\ttrace_samples 8 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                           u'\ttrace_subset - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                           u'\ttrace_excludesubset - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t\n\t\t'
                           u'\tdmapFilterSize - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                           u'\tdmapFilter - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t\n\t\t'
                           u'\tbarnDoors  - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                           u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t',
            'process': 'Modeling', 'column_name': 'snapshot', 'version': 1, 'is_current': False,
            'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/Modeling/versions',
                'code': 'FILE00000154',
                'description': u'\t\tIntensity 100 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                               u'\tfromIntensity 1\n\t\ttoIntensity  100000 - \u043a\u043e\u0440\u043e\u0447\u0435, '
                               u'\u0434\u0430\u043b\u0435\u043a\u043e\n\t\tdecayRate 1.6\n\t\tfromLightColor, '
                               u'toLightColor  - \u044d\u0442\u0438 \u0434\u0432\u0430 '
                               u'\u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u0430 '
                               u'\u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c \u0432 '
                               u'\u043e\u0434\u0438\u043d - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 '
                               u'\u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                               u'\tconeAngle 300 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                               u'\tpenumbraAngle 10-100 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 '
                               u'\u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                               u'\tdropOff 3 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t'
                               u'\temitDiffuse \n\t\temitSpecular \n\t\t\n\t\t\u042d\u0442\u0438 '
                               u'\u043f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b \u043d\u0430\u0434\u043e '
                               u'\u0441\u0434\u0435\u043b\u0430\u0442\u044c \u043c\u0435\u043d\u0435\u0435 '
                               u'\u0447\u0443\u0432\u0441\u0442\u0432\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u043c'
                               u'\u0438, \u0441\u0435\u0439\u0447\u0430\u0441 \u043e\u043d\u0438 \u0432\u0441\u0435 '
                               u'\u043a\u0440\u0443\u0442\u044f\u0442\u0441\u044f \u0432 '
                               u'\u0442\u044b\u0441\u044f\u0447\u043d\u044b\u0445 '
                               u'\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f\u0445:\n\t\t\ttrace_bias 0.001 - '
                               u'\u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                               u'\ttrace_blur 0.001 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                               u'\ttrace_samples 8 - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                               u'\ttrace_subset - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                               u'\ttrace_excludesubset - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 '
                               u'\u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t\n\t'
                               u'\t\tdmapFilterSize - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t'
                               u'\tdmapFilter - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t\n\t'
                               u'\t\tbarnDoors  - \u0432\u044b\u043d\u0435\u0441\u0442\u0438 \u043a\u0430\u043a '
                               u'\u0440\u0435\u0433\u0443\u043b\u0438\u0440\u0443\u0435\u043c\u044b\u0435\n\t\t\t',
                'timestamp': '2015-12-15 19:07:47',
                'st_size': '115.16 Kb', 'context': 'Modeling',
                'file_name': u'Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling_v001.ma',
                'login': 'admin', 'type': 'main'
            }], 'login': 'admin', 'is_latest': True, 'revision': 0
        }], 'Refs': [], 'icon': [{
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000052',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_v002.jpg',
                'snapshot_code': 'SNAPSHOT00000015',
                'project_code': 'exam', 'id': 52,
                'base_type': 'file', 'st_size': 278007,
                '__search_key__': 'sthpw/file?code=FILE00000052',
                'type': 'main', 'search_id': 2, 'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/icon/versions',
                'timestamp': '2015-11-29 19:03:36',
                'file_range': '', 'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon/versions',
                'md5': '0e51bc2a8d2e0cfa6c47067747233a39',
                'base_dir_alias': '',
                'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                               'title)\\root/temp/upload/80a542b57944b77ac72ba95ddbdbfbc6/mushroom.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000053',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_web_v002_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000015',
                'project_code': 'exam', 'id': 53,
                'base_type': 'file', 'st_size': 45539,
                '__search_key__': 'sthpw/file?code=FILE00000053',
                'type': 'icon', 'search_id': 2, 'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/icon/versions',
                'timestamp': '2015-11-29 19:03:36',
                'file_range': '', 'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon/versions',
                'md5': '8ca4c3d336d02af56b22264c72ed9331',
                'base_dir_alias': '',
                'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                               'title)\\root/temp/upload/80a542b57944b77ac72ba95ddbdbfbc6/mushroom_web.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000054',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_icon_v002_web.png',
                'snapshot_code': 'SNAPSHOT00000015',
                'project_code': 'exam', 'id': 54,
                'base_type': 'file', 'st_size': 25475,
                '__search_key__': 'sthpw/file?code=FILE00000054',
                'type': 'web', 'search_id': 2, 'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/icon/versions',
                'timestamp': '2015-11-29 19:03:36',
                'file_range': '', 'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon/versions',
                'md5': '85ff96759c1bff8a0ba7bad1b054d9d9',
                'base_dir_alias': '',
                'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                               'title)\\root/temp/upload/80a542b57944b77ac72ba95ddbdbfbc6/mushroom_icon.png',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000015',
            'search_code': 'PROPS00002', 'description': 'No comment',
            'process': 'icon', 'column_name': 'preview', 'version': 2,
            'is_current': True, 'context': 'icon', 'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/icon/versions',
                'code': 'FILE00000052',
                'description': 'No comment',
                'timestamp': '2015-11-29 19:03:36',
                'st_size': '271.49 Kb',
                'context': 'icon',
                'file_name': 'Mushroom_mushroom_v002.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Mushroom/work/icon/versions',
                'code': 'FILE00000053',
                'description': 'No comment',
                'timestamp': '2015-11-29 19:03:36',
                'st_size': '44.47 Kb',
                'context': 'icon',
                'file_name': 'Mushroom_mushroom_web_v002_icon.jpg',
                'login': 'admin',
                'type': 'icon'
            }, {
                'relative_dir': 'exam/props/Mushroom/work/icon/versions',
                'code': 'FILE00000054',
                'description': 'No comment',
                'timestamp': '2015-11-29 19:03:36',
                'st_size': '24.88 Kb',
                'context': 'icon',
                'file_name': 'Mushroom_mushroom_icon_v002_web.png',
                'login': 'admin',
                'type': 'web'
            }],
            'login': 'admin', 'is_latest': True, 'revision': 0
        }, {
            'files': [{
                'repo_type': '', 'code': 'FILE00000058',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom.jpg',
                'snapshot_code': 'SNAPSHOT00000014',
                'project_code': '', 'id': 58, 'base_type': 'file',
                'st_size': 278007,
                '__search_key__': 'sthpw/file?code=FILE00000058',
                'type': 'main', 'search_id': 2, 'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/icon',
                'timestamp': '2015-11-29 19:03:37',
                'file_range': '', 'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000059',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_web_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000014',
                'project_code': '', 'id': 59, 'base_type': 'file',
                'st_size': 45539,
                '__search_key__': 'sthpw/file?code=FILE00000059',
                'type': 'icon', 'search_id': 2, 'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/icon',
                'timestamp': '2015-11-29 19:03:37',
                'file_range': '', 'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000060',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_icon_web.png',
                'snapshot_code': 'SNAPSHOT00000014',
                'project_code': '', 'id': 60, 'base_type': 'file',
                'st_size': 25475,
                '__search_key__': 'sthpw/file?code=FILE00000060',
                'type': 'web', 'search_id': 2, 'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/icon',
                'timestamp': '2015-11-29 19:03:37',
                'file_range': '', 'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/icon',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000014',
            'search_code': 'PROPS00002', 'description': 'Versionless',
            'process': 'icon', 'column_name': 'snapshot', 'version': -1,
            'is_current': False, 'context': 'icon', 'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/icon',
                'code': 'FILE00000058',
                'description': 'Versionless',
                'timestamp': '2015-11-29 19:03:37',
                'st_size': '271.49 Kb',
                'context': 'icon',
                'file_name': 'Mushroom_mushroom.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Mushroom/work/icon',
                'code': 'FILE00000059',
                'description': 'Versionless',
                'timestamp': '2015-11-29 19:03:37',
                'st_size': '44.47 Kb',
                'context': 'icon',
                'file_name': 'Mushroom_mushroom_web_icon.jpg',
                'login': 'admin',
                'type': 'icon'
            }, {
                'relative_dir': 'exam/props/Mushroom/work/icon',
                'code': 'FILE00000060',
                'description': 'Versionless',
                'timestamp': '2015-11-29 19:03:37',
                'st_size': '24.88 Kb',
                'context': 'icon',
                'file_name': 'Mushroom_mushroom_icon_web.png',
                'login': 'admin',
                'type': 'web'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }], 'Texturing': [{
            'files': [{
                'repo_type': '',
                'code': 'FILE00000162',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_nhair_Texturing.ma',
                'snapshot_code': 'SNAPSHOT00000048',
                'project_code': '', 'id': 162,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000162',
                'type': 'main',
                'search_id': 2,
                'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/Texturing',
                'timestamp': '2015-12-18 21:30:58',
                'file_range': '',
                'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000048',
            'search_code': 'PROPS00002',
            'description': 'Versionless',
            'process': 'Texturing',
            'column_name': 'snapshot', 'version': -1,
            'is_current': False, 'context': 'Texturing',
            'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/Texturing',
                'code': 'FILE00000162',
                'description': 'Versionless',
                'timestamp': '2015-12-18 21:30:58',
                'st_size': '249.10 Kb',
                'context': 'Texturing',
                'file_name': 'Mushroom_nhair_Texturing.ma',
                'login': 'admin',
                'type': 'main'
            }], 'login': 'admin',
            'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000160',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_nhair_Texturing_v003.ma',
                'snapshot_code': 'SNAPSHOT00000047',
                'project_code': 'exam',
                'id': 160,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000160',
                'type': 'main',
                'search_id': 2,
                'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
                'timestamp': '2015-12-18 21:30:57',
                'file_range': '',
                'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'nhair.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000047',
            'search_code': 'PROPS00002',
            'description': 'main version',
            'process': 'Texturing',
            'column_name': 'snapshot', 'version': 3,
            'is_current': True, 'context': 'Texturing',
            'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
                'code': 'FILE00000160',
                'description': 'main version',
                'timestamp': '2015-12-18 21:30:57',
                'st_size': '249.10 Kb',
                'context': 'Texturing',
                'file_name': 'Mushroom_nhair_Texturing_v003.ma',
                'login': 'admin',
                'type': 'main'
            }], 'login': 'admin',
            'is_latest': True, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000094',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_v002.ma',
                'snapshot_code': 'SNAPSHOT00000032',
                'project_code': 'exam',
                'id': 94, 'base_type': 'file',
                'st_size': 897549,
                '__search_key__': 'sthpw/file?code=FILE00000094',
                'type': 'main',
                'search_id': 2,
                'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
                'timestamp': '2015-12-12 10:48:25',
                'file_range': '',
                'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing/versions',
                'md5': '8357016cee16691cf2ca43bf863c32fb',
                'base_dir_alias': '',
                'source_path': 'mushroom.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000032',
            'search_code': 'PROPS00002',
            'description': 'Fix some overlapping uvs',
            'process': 'Texturing',
            'column_name': 'snapshot', 'version': 2,
            'is_current': False, 'context': 'Texturing',
            'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
                'code': 'FILE00000094',
                'description': 'Fix some overlapping uvs',
                'timestamp': '2015-12-12 10:48:25',
                'st_size': '876.51 Kb',
                'context': 'Texturing',
                'file_name': 'Mushroom_mushroom_v002.ma',
                'login': 'admin',
                'type': 'main'
            }], 'login': 'admin',
            'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000091',
                '__search_type__': 'sthpw/file',
                'file_name': 'Mushroom_mushroom_v001.ma',
                'snapshot_code': 'SNAPSHOT00000030',
                'project_code': 'exam',
                'id': 91, 'base_type': 'file',
                'st_size': 897549,
                '__search_key__': 'sthpw/file?code=FILE00000091',
                'type': 'main',
                'search_id': 2,
                'metadata': {},
                'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
                'timestamp': '2015-12-12 10:48:09',
                'file_range': '',
                'search_code': 'PROPS00002',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Mushroom/work/Texturing/versions',
                'md5': '8357016cee16691cf2ca43bf863c32fb',
                'base_dir_alias': '',
                'source_path': 'mushroom.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000030',
            'search_code': 'PROPS00002',
            'description': 'First tex',
            'process': 'Texturing',
            'column_name': 'snapshot', 'version': 1,
            'is_current': False, 'context': 'Texturing',
            'snapshot': [{
                'relative_dir': 'exam/props/Mushroom/work/Texturing/versions',
                'code': 'FILE00000091',
                'description': 'First tex',
                'timestamp': '2015-12-12 10:48:09',
                'st_size': '876.51 Kb',
                'context': 'Texturing',
                'file_name': 'Mushroom_mushroom_v001.ma',
                'login': 'admin',
                'type': 'main'
            }], 'login': 'admin',
            'is_latest': False, 'revision': 0
        }], 'Sculpt': []
    }, u'PROPS00003': {
        'Modeling': [{
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000082', '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flower_v001.ma', 'snapshot_code': 'SNAPSHOT00000025',
                'project_code': 'exam', 'id': 82, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000082', 'type': 'main', 'search_id': 3,
                'metadata': {}, 'relative_dir': 'exam/props/Flower/work/Modeling/versions',
                'timestamp': '2015-12-12 10:46:59', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                'source_path': 'flower.ma', 'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000473', '__search_type__': 'sthpw/file',
                'file_name': '98736900_korol21_icon_Modeling_v001.png',
                'snapshot_code': 'SNAPSHOT00000025', 'project_code': 'exam', 'id': 473,
                'base_type': 'file', 'st_size': 23929,
                '__search_key__': 'sthpw/file?code=FILE00000473', 'type': 'icon', 'search_id': 3,
                'metadata': {}, 'relative_dir': 'exam/props/Flower/work/Modeling/versions',
                'timestamp': '2015-12-23 09:48:07', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling/versions',
                'md5': 'a7d0700a49c43e089d3b079f545d36ee', 'base_dir_alias': '',
                'source_path': '98736900_korol21.jpg', 'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000025', 'search_code': 'PROPS00003',
            'description': 'Flower MOD', 'process': 'Modeling', 'column_name': 'snapshot', 'version': 1,
            'is_current': True, 'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Modeling/versions',
                'code': 'FILE00000082',
                'description': 'Flower MOD',
                'timestamp': '2015-12-12 10:46:59',
                'st_size': '249.10 Kb',
                'context': 'Modeling',
                'file_name': 'Flower_flower_v001.ma',
                'login': 'admin', 'type': 'main'
            }, {
                'relative_dir': 'exam/props/Flower/work/Modeling/versions',
                'code': 'FILE00000473',
                'description': 'Flower MOD',
                'timestamp': '2015-12-23 09:48:07',
                'st_size': '23.37 Kb',
                'context': 'Modeling',
                'file_name': '98736900_korol21_icon_Modeling_v001.png',
                'login': 'admin', 'type': 'icon'
            }], 'login': 'admin',
            'is_latest': True, 'revision': 0
        }, {
            'files': [{
                'repo_type': '', 'code': 'FILE00000474', '__search_type__': 'sthpw/file',
                'file_name': 'Flower_Modeling.ma', 'snapshot_code': 'SNAPSHOT00000026',
                'project_code': '', 'id': 474, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000474', 'type': 'main', 'search_id': 3,
                'metadata': {}, 'relative_dir': 'exam/props/Flower/work/Modeling',
                'timestamp': '2015-12-23 09:48:07', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000475', '__search_type__': 'sthpw/file',
                'file_name': 'Flower_Modeling_icon.jpg', 'snapshot_code': 'SNAPSHOT00000026',
                'project_code': '', 'id': 475, 'base_type': 'file', 'st_size': 23929,
                '__search_key__': 'sthpw/file?code=FILE00000475', 'type': 'icon', 'search_id': 3,
                'metadata': {}, 'relative_dir': 'exam/props/Flower/work/Modeling',
                'timestamp': '2015-12-23 09:48:08', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Modeling',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000026', 'search_code': 'PROPS00003',
            'description': 'Versionless', 'process': 'Modeling', 'column_name': 'snapshot', 'version': -1,
            'is_current': False, 'context': 'Modeling', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Modeling',
                'code': 'FILE00000474',
                'description': 'Versionless',
                'timestamp': '2015-12-23 09:48:07',
                'st_size': '249.10 Kb',
                'context': 'Modeling',
                'file_name': 'Flower_Modeling.ma',
                'login': 'admin', 'type': 'main'
            }, {
                'relative_dir': 'exam/props/Flower/work/Modeling',
                'code': 'FILE00000475',
                'description': 'Versionless',
                'timestamp': '2015-12-23 09:48:08',
                'st_size': '23.37 Kb',
                'context': 'Modeling',
                'file_name': 'Flower_Modeling_icon.jpg',
                'login': 'admin', 'type': 'icon'
            }], 'login': 'admin',
            'is_latest': False, 'revision': 0
        }], 'Refs': [{
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000097',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flowers_v002.jpg',
                'snapshot_code': 'SNAPSHOT00000033', 'project_code': 'exam',
                'id': 97, 'base_type': 'file', 'st_size': 27582,
                '__search_key__': 'sthpw/file?code=FILE00000097',
                'type': 'main', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'timestamp': '2015-12-12 11:11:29', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
                'md5': '3dee2494e17171a904769aa91b47462e', 'base_dir_alias': '',
                'source_path': 'flowers.jpg',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000098',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flowers_web_v002_web.jpg',
                'snapshot_code': 'SNAPSHOT00000033', 'project_code': 'exam',
                'id': 98, 'base_type': 'file', 'st_size': 16440,
                '__search_key__': 'sthpw/file?code=FILE00000098', 'type': 'web',
                'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'timestamp': '2015-12-12 11:11:29', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
                'md5': '2a23a73df00e7c05fe24148faaa9ee8b', 'base_dir_alias': '',
                'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                               'title)\\root/temp/upload/46b4d74b3cc052d2474865dcc660485a/flowers_web.jpg',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000099',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flowers_icon_v002_icon.png',
                'snapshot_code': 'SNAPSHOT00000033', 'project_code': 'exam',
                'id': 99, 'base_type': 'file', 'st_size': 14738,
                '__search_key__': 'sthpw/file?code=FILE00000099',
                'type': 'icon', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'timestamp': '2015-12-12 11:11:29', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
                'md5': '34f64bd4dfe3d8f2c14e5a55ea941d8b', 'base_dir_alias': '',
                'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                               'title)\\root/temp/upload/46b4d74b3cc052d2474865dcc660485a/flowers_icon.png',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000033', 'search_code': 'PROPS00003',
            'description': 'No comment', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 2, 'is_current': True, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'code': 'FILE00000097',
                'description': 'No comment',
                'timestamp': '2015-12-12 11:11:29',
                'st_size': '26.94 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flowers_v002.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'code': 'FILE00000098',
                'description': 'No comment',
                'timestamp': '2015-12-12 11:11:29',
                'st_size': '16.05 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flowers_web_v002_web.jpg',
                'login': 'admin',
                'type': 'web'
            }, {
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'code': 'FILE00000099',
                'description': 'No comment',
                'timestamp': '2015-12-12 11:11:29',
                'st_size': '14.39 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flowers_icon_v002_icon.png',
                'login': 'admin',
                'type': 'icon'
            }],
            'login': 'admin', 'is_latest': True, 'revision': 0
        }, {
            'files': [{
                'repo_type': '', 'code': 'FILE00000103',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flowers.jpg',
                'snapshot_code': 'SNAPSHOT00000022', 'project_code': '',
                'id': 103, 'base_type': 'file', 'st_size': 27582,
                '__search_key__': 'sthpw/file?code=FILE00000103',
                'type': 'main', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs',
                'timestamp': '2015-12-12 11:11:29', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000104',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flowers_web_web.jpg',
                'snapshot_code': 'SNAPSHOT00000022', 'project_code': '',
                'id': 104, 'base_type': 'file', 'st_size': 16440,
                '__search_key__': 'sthpw/file?code=FILE00000104', 'type': 'web',
                'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs',
                'timestamp': '2015-12-12 11:11:29', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000105',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flowers_icon_icon.png',
                'snapshot_code': 'SNAPSHOT00000022', 'project_code': '',
                'id': 105, 'base_type': 'file', 'st_size': 14738,
                '__search_key__': 'sthpw/file?code=FILE00000105',
                'type': 'icon', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs',
                'timestamp': '2015-12-12 11:11:29', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs',
                'md5': '', 'base_dir_alias': '', 'source_path': '',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000022', 'search_code': 'PROPS00003',
            'description': 'Versionless', 'process': 'Refs', 'column_name': 'snapshot',
            'version': -1, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Refs',
                'code': 'FILE00000103',
                'description': 'Versionless',
                'timestamp': '2015-12-12 11:11:29',
                'st_size': '26.94 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flowers.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Flower/work/Refs',
                'code': 'FILE00000104',
                'description': 'Versionless',
                'timestamp': '2015-12-12 11:11:29',
                'st_size': '16.05 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flowers_web_web.jpg',
                'login': 'admin',
                'type': 'web'
            }, {
                'relative_dir': 'exam/props/Flower/work/Refs',
                'code': 'FILE00000105',
                'description': 'Versionless',
                'timestamp': '2015-12-12 11:11:29',
                'st_size': '14.39 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flowers_icon_icon.png',
                'login': 'admin',
                'type': 'icon'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000076',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flower_v001.ma',
                'snapshot_code': 'SNAPSHOT00000021', 'project_code': 'exam',
                'id': 76, 'base_type': 'file', 'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000076',
                'type': 'main', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'timestamp': '2015-12-12 10:46:20', 'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Refs/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e', 'base_dir_alias': '',
                'source_path': 'flower.ma',
                'search_type': 'exam/props?project=exam', 'metadata_search': ''
            }], 'code': 'SNAPSHOT00000021', 'search_code': 'PROPS00003',
            'description': 'Flower REF', 'process': 'Refs', 'column_name': 'snapshot',
            'version': 1, 'is_current': False, 'context': 'Refs', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Refs/versions',
                'code': 'FILE00000076',
                'description': 'Flower REF',
                'timestamp': '2015-12-12 10:46:20',
                'st_size': '249.10 Kb',
                'context': 'Refs',
                'file_name': 'Flower_flower_v001.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }], 'icon': [{
            'files': [{
                'repo_type': '', 'code': 'FILE00000112',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_floweer.jpg',
                'snapshot_code': 'SNAPSHOT00000035',
                'project_code': '', 'id': 112,
                'base_type': 'file', 'st_size': 11251065,
                '__search_key__': 'sthpw/file?code=FILE00000112',
                'type': 'main', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/icon',
                'timestamp': '2015-12-15 12:39:49',
                'file_range': '', 'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon',
                'md5': '', 'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000113',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_floweer_web_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000035',
                'project_code': '', 'id': 113,
                'base_type': 'file', 'st_size': 51042,
                '__search_key__': 'sthpw/file?code=FILE00000113',
                'type': 'icon', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/icon',
                'timestamp': '2015-12-15 12:39:49',
                'file_range': '', 'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon',
                'md5': '', 'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '', 'code': 'FILE00000114',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_floweer_icon_web.png',
                'snapshot_code': 'SNAPSHOT00000035',
                'project_code': '', 'id': 114,
                'base_type': 'file', 'st_size': 23357,
                '__search_key__': 'sthpw/file?code=FILE00000114',
                'type': 'web', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/icon',
                'timestamp': '2015-12-15 12:39:49',
                'file_range': '', 'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon',
                'md5': '', 'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000035',
            'search_code': 'PROPS00003', 'description': 'Versionless',
            'process': 'icon', 'column_name': 'snapshot', 'version': -1,
            'is_current': False, 'context': 'icon', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/icon',
                'code': 'FILE00000112',
                'description': 'Versionless',
                'timestamp': '2015-12-15 12:39:49',
                'st_size': '10.73 Mb',
                'context': 'icon',
                'file_name': 'Flower_floweer.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Flower/work/icon',
                'code': 'FILE00000113',
                'description': 'Versionless',
                'timestamp': '2015-12-15 12:39:49',
                'st_size': '49.85 Kb',
                'context': 'icon',
                'file_name': 'Flower_floweer_web_icon.jpg',
                'login': 'admin',
                'type': 'icon'
            }, {
                'relative_dir': 'exam/props/Flower/work/icon',
                'code': 'FILE00000114',
                'description': 'Versionless',
                'timestamp': '2015-12-15 12:39:49',
                'st_size': '22.81 Kb',
                'context': 'icon',
                'file_name': 'Flower_floweer_icon_web.png',
                'login': 'admin',
                'type': 'web'
            }],
            'login': 'admin', 'is_latest': False, 'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic', 'code': 'FILE00000106',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_floweer_v001.jpg',
                'snapshot_code': 'SNAPSHOT00000034',
                'project_code': 'exam', 'id': 106,
                'base_type': 'file', 'st_size': 11251065,
                '__search_key__': 'sthpw/file?code=FILE00000106',
                'type': 'main', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/icon/versions',
                'timestamp': '2015-12-15 12:39:47',
                'file_range': '', 'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon/versions',
                'md5': '5b89b22b0ac37f2b3803d7d00a59d778',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/floweer.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000107',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_floweer_web_v001_icon.jpg',
                'snapshot_code': 'SNAPSHOT00000034',
                'project_code': 'exam', 'id': 107,
                'base_type': 'file', 'st_size': 51042,
                '__search_key__': 'sthpw/file?code=FILE00000107',
                'type': 'icon', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/icon/versions',
                'timestamp': '2015-12-15 12:39:47',
                'file_range': '', 'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon/versions',
                'md5': '7f5fe4888a6bee2224ca45a1f8a33f36',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/floweer_web.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic', 'code': 'FILE00000108',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_floweer_icon_v001_web.png',
                'snapshot_code': 'SNAPSHOT00000034',
                'project_code': 'exam', 'id': 108,
                'base_type': 'file', 'st_size': 23357,
                '__search_key__': 'sthpw/file?code=FILE00000108',
                'type': 'web', 'search_id': 3, 'metadata': {},
                'relative_dir': 'exam/props/Flower/work/icon/versions',
                'timestamp': '2015-12-15 12:39:47',
                'file_range': '', 'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/icon/versions',
                'md5': 'e427ffc50e5e64b8966f1ffbef5a3cc0',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/floweer_icon.png',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }], 'code': 'SNAPSHOT00000034',
            'search_code': 'PROPS00003', 'description': 'Initial insert',
            'process': 'icon', 'column_name': 'preview', 'version': 1,
            'is_current': True, 'context': 'icon', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/icon/versions',
                'code': 'FILE00000106',
                'description': 'Initial insert',
                'timestamp': '2015-12-15 12:39:47',
                'st_size': '10.73 Mb',
                'context': 'icon',
                'file_name': 'Flower_floweer_v001.jpg',
                'login': 'admin',
                'type': 'main'
            }, {
                'relative_dir': 'exam/props/Flower/work/icon/versions',
                'code': 'FILE00000107',
                'description': 'Initial insert',
                'timestamp': '2015-12-15 12:39:47',
                'st_size': '49.85 Kb',
                'context': 'icon',
                'file_name': 'Flower_floweer_web_v001_icon.jpg',
                'login': 'admin',
                'type': 'icon'
            }, {
                'relative_dir': 'exam/props/Flower/work/icon/versions',
                'code': 'FILE00000108',
                'description': 'Initial insert',
                'timestamp': '2015-12-15 12:39:47',
                'st_size': '22.81 Kb',
                'context': 'icon',
                'file_name': 'Flower_floweer_icon_v001_web.png',
                'login': 'admin',
                'type': 'web'
            }],
            'login': 'admin', 'is_latest': True, 'revision': 0
        }], 'Texturing': [{
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000115',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_roundflower_v003.jpg',
                'snapshot_code': 'SNAPSHOT00000036',
                'project_code': 'exam',
                'id': 115,
                'base_type': 'file',
                'st_size': 28028,
                '__search_key__': 'sthpw/file?code=FILE00000115',
                'type': 'main',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'timestamp': '2015-12-15 13:37:29',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/exam/props/Flower/work/Texturing/versions',
                'md5': 'af9206b7d4ae8ac80a749934aad01fe9',
                'base_dir_alias': '',
                'source_path': 'roundflower.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic',
                'code': 'FILE00000116',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_roundflower_web_v003_web.jpg',
                'snapshot_code': 'SNAPSHOT00000036',
                'project_code': 'exam',
                'id': 116,
                'base_type': 'file',
                'st_size': 11524,
                '__search_key__': 'sthpw/file?code=FILE00000116',
                'type': 'web',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'timestamp': '2015-12-15 13:37:29',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/exam/props/Flower/work/Texturing/versions',
                'md5': '0b341d7fe7f61fb57f9ae6880a110f65',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/f4b72552d33c2f2c416250afd4aecbc1/roundflower_web.jpg',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic',
                'code': 'FILE00000117',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_roundflower_icon_v003_icon.png',
                'snapshot_code': 'SNAPSHOT00000036',
                'project_code': 'exam',
                'id': 117,
                'base_type': 'file',
                'st_size': 11841,
                '__search_key__': 'sthpw/file?code=FILE00000117',
                'type': 'icon',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'timestamp': '2015-12-15 13:37:29',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/exam/props/Flower/work/Texturing/versions',
                'md5': '096ead5ab10efa815f73efa45ea5811d',
                'base_dir_alias': '',
                'source_path': 'D:\\Alexey\\onedrive\\Exam_(work '
                               'title)\\root/temp/upload/f4b72552d33c2f2c416250afd4aecbc1/roundflower_icon.png',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000036',
            'search_code': 'PROPS00003',
            'description': 'No comment',
            'process': 'Texturing',
            'column_name': 'snapshot',
            'version': 3, 'is_current': True,
            'context': 'Texturing', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'code': 'FILE00000115',
                'description': 'No comment',
                'timestamp': '2015-12-15 13:37:29',
                'st_size': '27.37 Kb',
                'context': 'Texturing',
                'file_name': 'Flower_roundflower_v003.jpg',
                'login': 'admin',
                'type': 'main'
            },
                {
                    'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                    'code': 'FILE00000116',
                    'description': 'No comment',
                    'timestamp': '2015-12-15 13:37:29',
                    'st_size': '11.25 Kb',
                    'context': 'Texturing',
                    'file_name': 'Flower_roundflower_web_v003_web.jpg',
                    'login': 'admin',
                    'type': 'web'
                },
                {
                    'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                    'code': 'FILE00000117',
                    'description': 'No comment',
                    'timestamp': '2015-12-15 13:37:29',
                    'st_size': '11.56 Kb',
                    'context': 'Texturing',
                    'file_name': 'Flower_roundflower_icon_v003_icon.png',
                    'login': 'admin',
                    'type': 'icon'
                }],
            'login': 'admin', 'is_latest': True,
            'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000088',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flower_v002.ma',
                'snapshot_code': 'SNAPSHOT00000029',
                'project_code': 'exam',
                'id': 88,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000088',
                'type': 'main',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'timestamp': '2015-12-12 10:47:50',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'flower.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000029',
            'search_code': 'PROPS00003',
            'description': 'More tex',
            'process': 'Texturing',
            'column_name': 'snapshot',
            'version': 2, 'is_current': False,
            'context': 'Texturing', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'code': 'FILE00000088',
                'description': 'More tex',
                'timestamp': '2015-12-12 10:47:50',
                'st_size': '249.10 Kb',
                'context': 'Texturing',
                'file_name': 'Flower_flower_v002.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False,
            'revision': 0
        }, {
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000085',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flower_v001.ma',
                'snapshot_code': 'SNAPSHOT00000027',
                'project_code': 'exam',
                'id': 85,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000085',
                'type': 'main',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'timestamp': '2015-12-12 10:47:14',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'flower.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000027',
            'search_code': 'PROPS00003',
            'description': 'FloWer Tex',
            'process': 'Texturing',
            'column_name': 'snapshot',
            'version': 1, 'is_current': False,
            'context': 'Texturing', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Texturing/versions',
                'code': 'FILE00000085',
                'description': 'FloWer Tex',
                'timestamp': '2015-12-12 10:47:14',
                'st_size': '249.10 Kb',
                'context': 'Texturing',
                'file_name': 'Flower_flower_v001.ma',
                'login': 'admin',
                'type': 'main'
            }],
            'login': 'admin', 'is_latest': False,
            'revision': 0
        }, {
            'files': [{
                'repo_type': '',
                'code': 'FILE00000121',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_roundflower.jpg',
                'snapshot_code': 'SNAPSHOT00000028',
                'project_code': '',
                'id': 121,
                'base_type': 'file',
                'st_size': 28028,
                '__search_key__': 'sthpw/file?code=FILE00000121',
                'type': 'main',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing',
                'timestamp': '2015-12-15 13:37:30',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '',
                'code': 'FILE00000122',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_roundflower_web_web.jpg',
                'snapshot_code': 'SNAPSHOT00000028',
                'project_code': '',
                'id': 122,
                'base_type': 'file',
                'st_size': 11524,
                '__search_key__': 'sthpw/file?code=FILE00000122',
                'type': 'web',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing',
                'timestamp': '2015-12-15 13:37:30',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '',
                'code': 'FILE00000123',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_roundflower_icon_icon.png',
                'snapshot_code': 'SNAPSHOT00000028',
                'project_code': '',
                'id': 123,
                'base_type': 'file',
                'st_size': 11841,
                '__search_key__': 'sthpw/file?code=FILE00000123',
                'type': 'icon',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Texturing',
                'timestamp': '2015-12-15 13:37:30',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Texturing',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000028',
            'search_code': 'PROPS00003',
            'description': 'Versionless',
            'process': 'Texturing',
            'column_name': 'snapshot',
            'version': -1, 'is_current': False,
            'context': 'Texturing', 'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Texturing',
                'code': 'FILE00000121',
                'description': 'Versionless',
                'timestamp': '2015-12-15 13:37:30',
                'st_size': '27.37 Kb',
                'context': 'Texturing',
                'file_name': 'Flower_roundflower.jpg',
                'login': 'admin',
                'type': 'main'
            },
                {
                    'relative_dir': 'exam/props/Flower/work/Texturing',
                    'code': 'FILE00000122',
                    'description': 'Versionless',
                    'timestamp': '2015-12-15 13:37:30',
                    'st_size': '11.25 Kb',
                    'context': 'Texturing',
                    'file_name': 'Flower_roundflower_web_web.jpg',
                    'login': 'admin',
                    'type': 'web'
                },
                {
                    'relative_dir': 'exam/props/Flower/work/Texturing',
                    'code': 'FILE00000123',
                    'description': 'Versionless',
                    'timestamp': '2015-12-15 13:37:30',
                    'st_size': '11.56 Kb',
                    'context': 'Texturing',
                    'file_name': 'Flower_roundflower_icon_icon.png',
                    'login': 'admin',
                    'type': 'icon'
                }],
            'login': 'admin', 'is_latest': False,
            'revision': 0
        }], 'Sculpt': [{
            'files': [{
                'repo_type': 'tactic',
                'code': 'FILE00000079',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_flower_v001.ma',
                'snapshot_code': 'SNAPSHOT00000023',
                'project_code': 'exam',
                'id': 79,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000079',
                'type': 'main',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Sculpt/versions',
                'timestamp': '2015-12-12 10:46:43',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt/versions',
                'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                'base_dir_alias': '',
                'source_path': 'flower.ma',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': 'tactic',
                'code': 'FILE00000476',
                '__search_type__': 'sthpw/file',
                'file_name': 'ep15Set_masterscene_light_sc01_icon_Sculpt_v001.png',
                'snapshot_code': 'SNAPSHOT00000023',
                'project_code': 'exam',
                'id': 476,
                'base_type': 'file',
                'st_size': 16355,
                '__search_key__': 'sthpw/file?code=FILE00000476',
                'type': 'icon',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Sculpt/versions',
                'timestamp': '2015-12-23 09:59:02',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt/versions',
                'md5': '5ca9bcbddd74d8b6345afa8b95eb82fa',
                'base_dir_alias': '',
                'source_path': 'ep15Set_masterscene_light_sc01.png',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000023',
            'search_code': 'PROPS00003',
            'description': 'Flower Sculpt',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': 1,
            'is_current': True,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Sculpt/versions',
                'code': 'FILE00000079',
                'description': 'Flower Sculpt',
                'timestamp': '2015-12-12 10:46:43',
                'st_size': '249.10 Kb',
                'context': 'Sculpt',
                'file_name': 'Flower_flower_v001.ma',
                'login': 'admin',
                'type': 'main'
            },
                {
                    'relative_dir': 'exam/props/Flower/work/Sculpt/versions',
                    'code': 'FILE00000476',
                    'description': 'Flower Sculpt',
                    'timestamp': '2015-12-23 09:59:02',
                    'st_size': '15.97 Kb',
                    'context': 'Sculpt',
                    'file_name': 'ep15Set_masterscene_light_sc01_icon_Sculpt_v001.png',
                    'login': 'admin',
                    'type': 'icon'
                }],
            'login': 'admin',
            'is_latest': True,
            'revision': 0
        }, {
            'files': [{
                'repo_type': '',
                'code': 'FILE00000477',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_Sculpt.ma',
                'snapshot_code': 'SNAPSHOT00000024',
                'project_code': '',
                'id': 477,
                'base_type': 'file',
                'st_size': 255075,
                '__search_key__': 'sthpw/file?code=FILE00000477',
                'type': 'main',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Sculpt',
                'timestamp': '2015-12-23 09:59:02',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }, {
                'repo_type': '',
                'code': 'FILE00000478',
                '__search_type__': 'sthpw/file',
                'file_name': 'Flower_Sculpt_icon.png',
                'snapshot_code': 'SNAPSHOT00000024',
                'project_code': '',
                'id': 478,
                'base_type': 'file',
                'st_size': 16355,
                '__search_key__': 'sthpw/file?code=FILE00000478',
                'type': 'icon',
                'search_id': 3,
                'metadata': {},
                'relative_dir': 'exam/props/Flower/work/Sculpt',
                'timestamp': '2015-12-23 09:59:02',
                'file_range': '',
                'search_code': 'PROPS00003',
                'checkin_dir': 'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Flower/work/Sculpt',
                'md5': '',
                'base_dir_alias': '',
                'source_path': '',
                'search_type': 'exam/props?project=exam',
                'metadata_search': ''
            }],
            'code': 'SNAPSHOT00000024',
            'search_code': 'PROPS00003',
            'description': 'Versionless',
            'process': 'Sculpt',
            'column_name': 'snapshot',
            'version': -1,
            'is_current': False,
            'context': 'Sculpt',
            'snapshot': [{
                'relative_dir': 'exam/props/Flower/work/Sculpt',
                'code': 'FILE00000477',
                'description': 'Versionless',
                'timestamp': '2015-12-23 09:59:02',
                'st_size': '249.10 Kb',
                'context': 'Sculpt',
                'file_name': 'Flower_Sculpt.ma',
                'login': 'admin',
                'type': 'main'
            },
                {
                    'relative_dir': 'exam/props/Flower/work/Sculpt',
                    'code': 'FILE00000478',
                    'description': 'Versionless',
                    'timestamp': '2015-12-23 09:59:02',
                    'st_size': '15.97 Kb',
                    'context': 'Sculpt',
                    'file_name': 'Flower_Sculpt_icon.png',
                    'login': 'admin',
                    'type': 'icon'
                }],
            'login': 'admin',
            'is_latest': False,
            'revision': 0
        }]
    }
}
