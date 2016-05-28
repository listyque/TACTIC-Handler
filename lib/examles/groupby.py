from itertools import groupby
from json import dumps

my_big_dict = [{
                   'is_synced': True, 'code': 'SNAPSHOT00000176', '__search_type__': 'sthpw/snapshot',
                   'process': 'Blocking', 's_status': '', 'id': 176, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000176', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': '', 'code': 'FILE00000433',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Blocking_zal_43.43.jpg.jpg',
                                                                  'snapshot_code': 'SNAPSHOT00000176',
                                                                  'project_code': '', 'id': 433, 'base_type': 'file',
                                                                  'st_size': 82047,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000433',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Blocking',
                                                                  'timestamp': '2015-12-20 14:26:46', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Blocking',
                                                                  'md5': '', 'base_dir_alias': '', 'source_path': '',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }, {
                                                                  'repo_type': '', 'code': 'FILE00000434',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Blocking_zal_43.43.jpg_web.jpg',
                                                                  'snapshot_code': 'SNAPSHOT00000176',
                                                                  'project_code': '', 'id': 434, 'base_type': 'file',
                                                                  'st_size': 55529,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000434',
                                                                  'type': 'web', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Blocking',
                                                                  'timestamp': '2015-12-20 14:26:46', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Blocking',
                                                                  'md5': '', 'base_dir_alias': '', 'source_path': '',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }, {
                                                                  'repo_type': '', 'code': 'FILE00000435',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Blocking_zal_43.43.jpg_icon.png',
                                                                  'snapshot_code': 'SNAPSHOT00000176',
                                                                  'project_code': '', 'id': 435, 'base_type': 'file',
                                                                  'st_size': 17311,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000435',
                                                                  'type': 'icon', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Blocking',
                                                                  'timestamp': '2015-12-20 14:26:46', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Blocking',
                                                                  'md5': '', 'base_dir_alias': '', 'source_path': '',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'Versionless',
                   'timestamp': '2015-12-20 14:26:46', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000175">\n  <file file_code="FILE00000433" '
                               'name="Boy_Blocking_zal_43.43.jpg.jpg" type="main"/>\n  <file file_code="FILE00000434" '
                               'name="Boy_Blocking_zal_43.43.jpg_web.jpg" type="web"/>\n  <file '
                               'file_code="FILE00000435" name="Boy_Blocking_zal_43.43.jpg_icon.png" '
                               'type="icon"/>\n</snapshot>\n',
                   'context': 'Blocking/zal_43.43.jpg', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000175', '__search_type__': 'sthpw/snapshot',
                   'process': 'Blocking', 's_status': '', 'id': 175, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000175', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000427',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Blocking_zal_43.43.jpg_v001.jpg',
                                                                  'snapshot_code': 'SNAPSHOT00000175',
                                                                  'project_code': 'exam', 'id': 427,
                                                                  'base_type': 'file', 'st_size': 82047,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000427',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir':
                                                                      'exam/chars/Boy/work/Blocking/versions',
                                                                  'timestamp': '2015-12-20 14:26:45', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Blocking/versions',
                                                                  'md5': 'fe9e3a7037ab65029c020d385da8f97d',
                                                                  'base_dir_alias': '', 'source_path': 'zal_43.43.jpg',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }, {
                                                                  'repo_type': 'tactic', 'code': 'FILE00000428',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name':
                                                                      'Boy_Blocking_zal_43.43.jpg_v001_web.jpg',
                                                                  'snapshot_code': 'SNAPSHOT00000175',
                                                                  'project_code': 'exam', 'id': 428,
                                                                  'base_type': 'file', 'st_size': 55529,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000428',
                                                                  'type': 'web', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir':
                                                                      'exam/chars/Boy/work/Blocking/versions',
                                                                  'timestamp': '2015-12-20 14:26:45', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Blocking/versions',
                                                                  'md5': '6e63d07a38ba289dfecb24ac7a6a51a0',
                                                                  'base_dir_alias': '',
                                                                  'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/temp/upload/a93cf5094541e908e1862abe547ea13f/zal_43_web.43.jpg',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }, {
                                                                  'repo_type': 'tactic', 'code': 'FILE00000429',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name':
                                                                      'Boy_Blocking_zal_43.43.jpg_v001_icon.png',
                                                                  'snapshot_code': 'SNAPSHOT00000175',
                                                                  'project_code': 'exam', 'id': 429,
                                                                  'base_type': 'file', 'st_size': 17311,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000429',
                                                                  'type': 'icon', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir':
                                                                      'exam/chars/Boy/work/Blocking/versions',
                                                                  'timestamp': '2015-12-20 14:26:45', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Blocking/versions',
                                                                  'md5': 'b98172c618063df4ad8c63df1b519d92',
                                                                  'base_dir_alias': '',
                                                                  'source_path': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/temp/upload/a93cf5094541e908e1862abe547ea13f/zal_43_icon.43.png',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }],
                   'description': u'Bardak! \u041d\u0435\u0442, \u0411\u0430\u0440\u0434\u0430\u0447\u0451\u043a!',
                   'timestamp': '2015-12-20 14:26:45', 'repo': '', 'is_current': False, 'is_latest': True,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 17:26:45 2015" context="Blocking/zal_43.43.jpg" '
                               'search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" '
                               'checkin_type="auto">\n  <file file_code="FILE00000427" '
                               'name="Boy_Blocking_zal_43.43.jpg_v001.jpg" type="main"/>\n  <file '
                               'file_code="FILE00000428" name="Boy_Blocking_zal_43.43.jpg_v001_web.jpg" '
                               'type="web"/>\n  <file file_code="FILE00000429" '
                               'name="Boy_Blocking_zal_43.43.jpg_v001_icon.png" type="icon"/>\n</snapshot>\n',
                   'context': 'Blocking/zal_43.43.jpg', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000174', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 174, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 6,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000174', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000424',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower_v006.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000174',
                                                                  'project_code': 'exam', 'id': 424,
                                                                  'base_type': 'file', 'st_size': 141610930,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000424',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir':
                                                                      'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:58:13', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '45ea226368a103b02f0583d64d66b4b6',
                                                                  'base_dir_alias': '', 'source_path': 'zal_v02.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:58:13', 'repo': '', 'is_current': True, 'is_latest': True,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:58:13 2015" context="Concept/flower" '
                               'search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" '
                               'checkin_type="auto">\n  <file file_code="FILE00000424" '
                               'name="Boy_Concept_flower_v006.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000173', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 173, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 5,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000173', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000421',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower_v005.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000173',
                                                                  'project_code': 'exam', 'id': 421,
                                                                  'base_type': 'file', 'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000421',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir':
                                                                      'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:57:57', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                                                                  'base_dir_alias': '', 'source_path': 'abracadabra.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:57:57', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:57:57 2015" context="Concept/flower" '
                               'search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" '
                               'checkin_type="auto">\n  <file file_code="FILE00000421" '
                               'name="Boy_Concept_flower_v005.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000172', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 172, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 4,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000172', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000418',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower_v004.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000172',
                                                                  'project_code': 'exam', 'id': 418,
                                                                  'base_type': 'file', 'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000418',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir':
                                                                      'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:57:48', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work '
                                                                                 'title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                                                                  'base_dir_alias': '', 'source_path': 'flower.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:57:48', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:57:48 2015" context="Concept/flower" search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" checkin_type="auto">\n  <file file_code="FILE00000418" name="Boy_Concept_flower_v004.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000171', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 171, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 3,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000171', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000415',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower_v003.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000171',
                                                                  'project_code': 'exam', 'id': 415,
                                                                  'base_type': 'file', 'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000415',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:57:41', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                                                                  'base_dir_alias': '', 'source_path': 'oculus.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:57:41', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:57:41 2015" context="Concept/flower" search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" checkin_type="auto">\n  <file file_code="FILE00000415" name="Boy_Concept_flower_v003.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000170', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 170, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 2,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000170', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000412',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower_v002.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000170',
                                                                  'project_code': 'exam', 'id': 412,
                                                                  'base_type': 'file', 'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000412',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:57:34', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                                                                  'base_dir_alias': '', 'source_path': 'oculus.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:57:34', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:57:34 2015" context="Concept/flower" search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" checkin_type="auto">\n  <file file_code="FILE00000412" name="Boy_Concept_flower_v002.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000168', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 168, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000168', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000409',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower_v001.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000168',
                                                                  'project_code': 'exam', 'id': 409,
                                                                  'base_type': 'file', 'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000409',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:45:47', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                                                                  'base_dir_alias': '', 'source_path': 'oculus.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:45:47', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:45:47 2015" context="Concept/flower" search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" checkin_type="auto">\n  <file file_code="FILE00000409" name="Boy_Concept_flower_v001.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000169', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 169, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000169', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': '', 'code': 'FILE00000426',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_flower.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000169',
                                                                  'project_code': '', 'id': 426, 'base_type': 'file',
                                                                  'st_size': 141610930,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000426',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Concept',
                                                                  'timestamp': '2015-12-20 13:58:15', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/chars/Boy/work/Concept',
                                                                  'md5': '', 'base_dir_alias': '', 'source_path': '',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'Versionless',
                   'timestamp': '2015-12-20 13:45:47', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000174">\n  <file file_code="FILE00000426" name="Boy_Concept_flower.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept/flower', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000167', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 167, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': 1,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000167', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': 'tactic', 'code': 'FILE00000406',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept_v001.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000167',
                                                                  'project_code': 'exam', 'id': 406,
                                                                  'base_type': 'file', 'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000406',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Concept/versions',
                                                                  'timestamp': '2015-12-20 13:45:26', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/chars/Boy/work/Concept/versions',
                                                                  'md5': '4cc55ae0c8245eb9923b345ac9a7d10e',
                                                                  'base_dir_alias': '', 'source_path': 'oculus.ma',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'large file',
                   'timestamp': '2015-12-20 13:45:26', 'repo': '', 'is_current': True, 'is_latest': True,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot timestamp="Sun Dec 20 16:45:26 2015" context="Concept" search_key="exam/chars?project=exam&amp;code=CHARS00001" login="admin" checkin_type="auto">\n  <file file_code="FILE00000406" name="Boy_Concept_v001.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept', 'login': 'admin', 'column_name': 'snapshot'
                   }, {
                   'is_synced': True, 'code': 'SNAPSHOT00000166', '__search_type__': 'sthpw/snapshot',
                   'process': 'Concept', 's_status': '', 'id': 166, 'project_code': 'exam', 'lock_date': '',
                   'search_code': 'CHARS00001', 'level_id': 0, 'lock_login': '', 'label': '', 'version': -1,
                   '__search_key__': 'sthpw/snapshot?code=SNAPSHOT00000166', 'level_type': '', 'search_id': 1,
                   'revision': 0, 'status': '', '__files__': [{
                                                                  'repo_type': '', 'code': 'FILE00000408',
                                                                  '__search_type__': 'sthpw/file',
                                                                  'file_name': 'Boy_Concept.ma',
                                                                  'snapshot_code': 'SNAPSHOT00000166',
                                                                  'project_code': '', 'id': 408, 'base_type': 'file',
                                                                  'st_size': 255075,
                                                                  '__search_key__': 'sthpw/file?code=FILE00000408',
                                                                  'type': 'main', 'search_id': 1, 'metadata': {},
                                                                  'relative_dir': 'exam/chars/Boy/work/Concept',
                                                                  'timestamp': '2015-12-20 13:45:27', 'file_range': '',
                                                                  'search_code': 'CHARS00001',
                                                                  'checkin_dir': 'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/chars/Boy/work/Concept',
                                                                  'md5': '', 'base_dir_alias': '', 'source_path': '',
                                                                  'search_type': 'exam/chars?project=exam',
                                                                  'metadata_search': ''
                                                                  }], 'description': 'Versionless',
                   'timestamp': '2015-12-20 13:45:08', 'repo': '', 'is_current': False, 'is_latest': False,
                   'metadata': {}, 'snapshot_type': 'file', 'server': '', 'search_type': 'exam/chars?project=exam',
                   'snapshot': '<snapshot ref_snapshot_code="SNAPSHOT00000167">\n  <file file_code="FILE00000408" name="Boy_Concept.ma" type="main"/>\n</snapshot>\n',
                   'context': 'Concept', 'login': 'admin', 'column_name': 'snapshot'
                   }]
# print(dumps(my_big_dict, sort_keys=True, indent=4))

# for data in my_big_dict:
    # print(dumps(data, sort_keys=True, indent=4))
    # print(
    # '__________________________________________________________SEPARATOR__________________________________________________________')

from collections import defaultdict

grouped = defaultdict(list)

my_big_dict = [{"year": ["1999"], "director": ["Wachowski"], "film": ["The Matrix"], "price": ["19,00"]},
{"year": ["1994"], "director": ["Tarantino"], "film": ["Pulp Fiction"], "price": ["20,00"]},
{"year": ["2003"], "director": ["Tarantino"], "film": ["Kill Bill vol.1"], "price": ["10,00"]},
{"year": ["2003"], "director": ["Wachowski"], "film": ["The Matrix Reloaded"], "price": ["9,99"]},
{"year": ["1994"], "director": ["Tarantino"], "film": ["Pulp Fiction"], "price": ["15,00"]},
{"year": ["1994"], "director": ["E. de Souza"], "film": ["Street Fighter"], "price": ["2,00"]},
{"year": ["1999"], "director": ["Wachowski"], "film": ["The Matrix"], "price": ["20,00"]},
{"year": ["1982"], "director": ["Ridley Scott"], "film": ["Blade Runner"], "price": ["19,99"]}]

for data in my_big_dict:
    # print(data)
    grouped[data['film'][0]].append(data)

print(grouped)
from pprint import pprint
pprint(dict(grouped))

    # for key, group in groupby(data, lambda x: x[0]):
    #     for thing in group:
    #         print(thing)
            # print(key)
            # print "A %s is a %s." % (thing[1], key)
        # print "_____SEPARATOR_____"

        # things = [("animal", "bear"), ("animal", "duck"), ("plant", "cactus"), ("vehicle", "speed boat"), ("vehicle", "school bus")]
        #
        # for key, group in groupby(things, lambda x: x[0]):
        #     for thing in group:
        #         print "A %s is a %s." % (thing[1], key)
        #     print " "
