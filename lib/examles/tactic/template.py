import xml.etree.ElementTree as Et

full_dict = [
    {
        'is_synced': True, 'code': u'SNAPSHOT00000044', 'process': u'Modeling', 's_status': None, 'id': 44,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': -1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000044', 'level_type': None,
        'search_id': 2, 'metadata': None, 'status': None, 'description': u'Versionless',
        'timestamp': '2015-12-15 19:07:49', 'repo': None, 'is_current': False, 'search_code': u'PROPS00002',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000043">\n  <file file_code="FILE00000156" '
                    u'name="Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling.ma" type="main"/>\n</snapshot>\n',
        'context': u'Modeling', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000043', 'process': u'Modeling', 's_status': None, 'id': 43,
        'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000043', 'level_type': None, 'search_id': 2,
        'metadata': None, 'status': None, 'description': u'\u0411\u0438\u043b\u0435\u0442\u0435\u0433 =)',
        'timestamp': '2015-12-15 19:07:47', 'repo': None, 'is_current': True, 'search_code': u'PROPS00002',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Tue Dec 15 22:07:47 2015" context="Modeling" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000154" '
                    u'name="Mushroom_\u0431\u0438\u043b\u0435\u04422_Modeling_v001.ma" type="main"/>\n</snapshot>\n',
        'context': u'Modeling', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000041', 'process': u'Texturing', 's_status': None, 'id': 41,
        'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000041', 'level_type': None, 'search_id': 1,
        'metadata': None, 'status': None, 'description': u'transfer', 'timestamp': '2015-12-15 13:51:26', 'repo': None,
        'is_current': True, 'search_code': u'PROPS00001', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Tue Dec 15 18:20:43 2015" context="Texturing" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000142" name="Oculus_transfer_v001.ma" type="main"/>\n  <file '
                    u'file_code="FILE00000146" name="Oculus_98736900_korol21_icon_v001_icon.png" '
                    u'type="icon"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000042', 'process': u'Texturing', 's_status': None, 'id': 42,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': -1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000042', 'level_type': None,
        'search_id': 1, 'metadata': None, 'status': None, 'description': u'Versionless',
        'timestamp': '2015-12-15 13:51:26', 'repo': None, 'is_current': False, 'search_code': u'PROPS00001',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000041" timestamp="Tue Dec 15 18:20:51 2015" '
                    u'context="Texturing" search_key="exam/props?project=exam&amp;code=PROPS00001" login="admin" '
                    u'checkin_type="strict">\n  <file file_code="FILE00000147" name="Oculus_transfer.ma" '
                    u'type="main"/>\n  <file file_code="FILE00000148" name="Oculus_98736900_korol21_icon.jpg" '
                    u'type="icon"/>\n  <file file_code="FILE00000149" name="Oculus_98736900_korol21_icon_icon.png" '
                    u'type="icon"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000036', 'process': u'Texturing', 's_status': None, 'id': 36,
        'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 3, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000036', 'level_type': None, 'search_id': 3,
        'metadata': None, 'status': None, 'description': u'No comment', 'timestamp': '2015-12-15 13:37:29',
        'repo': None,
        'is_current': True, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Tue Dec 15 16:37:29 2015" context="Texturing" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000115" name="Flower_roundflower_v003.jpg" type="main"/>\n  <file '
                    u'file_code="FILE00000116" name="Flower_roundflower_web_v003_web.jpg" type="web"/>\n  <file '
                    u'file_code="FILE00000117" name="Flower_roundflower_icon_v003_icon.png" '
                    u'type="icon"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000033', 'process': u'Refs', 's_status': None, 'id': 33, 'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 2, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000033', 'level_type': None, 'search_id': 3,
        'metadata': None, 'status': None, 'description': u'No comment', 'timestamp': '2015-12-12 11:11:29',
        'repo': None,
        'is_current': True, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 14:11:29 2015" context="Refs" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000097" name="Flower_flowers_v002.jpg" type="main"/>\n  <file '
                    u'file_code="FILE00000098" name="Flower_flowers_web_v002_web.jpg" type="web"/>\n  <file '
                    u'file_code="FILE00000099" name="Flower_flowers_icon_v002_icon.png" type="icon"/>\n</snapshot>\n',
        'context': u'Refs', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000032', 'process': u'Texturing', 's_status': None, 'id': 32,
        'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 2, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000032', 'level_type': None, 'search_id': 2,
        'metadata': None, 'status': None, 'description': u'Fix some overlapping uvs',
        'timestamp': '2015-12-12 10:48:25',
        'repo': None, 'is_current': True, 'search_code': u'PROPS00002', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:48:25 2015" context="Texturing" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000094" name="Mushroom_mushroom_v002.ma" type="main"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000030', 'process': u'Texturing', 's_status': None, 'id': 30,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000030', 'level_type': None,
        'search_id': 2, 'metadata': None, 'status': None, 'description': u'First tex',
        'timestamp': '2015-12-12 10:48:09',
        'repo': None, 'is_current': False, 'search_code': u'PROPS00002', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:48:09 2015" context="Texturing" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00002" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000091" name="Mushroom_mushroom_v001.ma" type="main"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000029', 'process': u'Texturing', 's_status': None, 'id': 29,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': 2, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000029', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'More tex',
        'timestamp': '2015-12-12 10:47:50',
        'repo': None, 'is_current': False, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:47:50 2015" context="Texturing" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000088" name="Flower_flower_v002.ma" type="main"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000027', 'process': u'Texturing', 's_status': None, 'id': 27,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000027', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'FloWer Tex',
        'timestamp': '2015-12-12 10:47:14',
        'repo': None, 'is_current': False, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:47:14 2015" context="Texturing" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000085" name="Flower_flower_v001.ma" type="main"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000028', 'process': u'Texturing', 's_status': None, 'id': 28,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': -1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000028', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'Versionless',
        'timestamp': '2015-12-12 10:47:14', 'repo': None, 'is_current': False, 'search_code': u'PROPS00003',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000036">\n  <file file_code="FILE00000121" '
                    u'name="Flower_roundflower.jpg" type="main"/>\n  <file file_code="FILE00000122" '
                    u'name="Flower_roundflower_web_web.jpg" type="web"/>\n  <file file_code="FILE00000123" '
                    u'name="Flower_roundflower_icon_icon.png" type="icon"/>\n</snapshot>\n',
        'context': u'Texturing', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000025', 'process': u'Modeling', 's_status': None, 'id': 25,
        'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000025', 'level_type': None, 'search_id': 3,
        'metadata': None, 'status': None, 'description': u'Flower MOD', 'timestamp': '2015-12-12 10:46:59',
        'repo': None,
        'is_current': True, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:46:59 2015" context="Modeling" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000082" name="Flower_flower_v001.ma" type="main"/>\n</snapshot>\n',
        'context': u'Modeling', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000026', 'process': u'Modeling', 's_status': None, 'id': 26,
        'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': -1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000026', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'Versionless',
        'timestamp': '2015-12-12 10:46:59', 'repo': None, 'is_current': False, 'search_code': u'PROPS00003',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000025">\n  <file file_code="FILE00000084" '
                    u'name="Flower_flower.ma" type="main"/>\n</snapshot>\n',
        'context': u'Modeling', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000023', 'process': u'Sculpt', 's_status': None, 'id': 23, 'label': None,
        'project_code': u'exam', 'is_latest': True, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None,
        'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000023', 'level_type': None, 'search_id': 3,
        'metadata': None, 'status': None, 'description': u'Flower Sculpt', 'timestamp': '2015-12-12 10:46:43',
        'repo': None, 'is_current': True, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:46:43 2015" context="Sculpt" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000079" name="Flower_flower_v001.ma" type="main"/>\n</snapshot>\n',
        'context': u'Sculpt', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000024', 'process': u'Sculpt', 's_status': None, 'id': 24, 'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': -1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000024', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'Versionless',
        'timestamp': '2015-12-12 10:46:43', 'repo': None, 'is_current': False, 'search_code': u'PROPS00003',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000023">\n  <file file_code="FILE00000081" '
                    u'name="Flower_flower.ma" type="main"/>\n</snapshot>\n',
        'context': u'Sculpt', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000022', 'process': u'Refs', 's_status': None, 'id': 22, 'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': -1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000022', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'Versionless',
        'timestamp': '2015-12-12 10:46:22', 'repo': None, 'is_current': False, 'search_code': u'PROPS00003',
        'snapshot_type': u'file', 'server': None, 'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot ref_snapshot_code="SNAPSHOT00000033">\n  <file file_code="FILE00000103" '
                    u'name="Flower_flowers.jpg" type="main"/>\n  <file file_code="FILE00000104" '
                    u'name="Flower_flowers_web_web.jpg" type="web"/>\n  <file file_code="FILE00000105" '
                    u'name="Flower_flowers_icon_icon.png" type="icon"/>\n</snapshot>\n',
        'context': u'Refs', 'login': u'admin', 'column_name': u'snapshot'
    },
    {
        'is_synced': True, 'code': u'SNAPSHOT00000021', 'process': u'Refs', 's_status': None, 'id': 21, 'label': None,
        'project_code': u'exam', 'is_latest': False, 'revision': 0, 'level_id': None, 'lock_login': None,
        'lock_date': None, 'version': 1, '__search_key__': u'sthpw/snapshot?code=SNAPSHOT00000021', 'level_type': None,
        'search_id': 3, 'metadata': None, 'status': None, 'description': u'Flower REF',
        'timestamp': '2015-12-12 10:46:20',
        'repo': None, 'is_current': False, 'search_code': u'PROPS00003', 'snapshot_type': u'file', 'server': None,
        'search_type': u'exam/props?project=exam',
        'snapshot': u'<snapshot timestamp="Sat Dec 12 13:46:20 2015" context="Refs" '
                    u'search_key="exam/props?project=exam&amp;code=PROPS00003" login="admin" checkin_type="strict">\n '
                    u' <file file_code="FILE00000076" name="Flower_flower_v001.ma" type="main"/>\n</snapshot>\n',
        'context': u'Refs', 'login': u'admin', 'column_name': u'snapshot'
    }]

files = [
    {
        'repo_type': u'tactic', 'code': u'FILE00000046', 'file_name': u'Oculus_oculus_v001.mb',
        'snapshot_code': u'SNAPSHOT00000011', 'id': 46, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 1312480, '__search_key__': u'sthpw/file?code=FILE00000046', 'type': u'main', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/modeling/versions',
        'timestamp': '2015-11-23 21:40:13', 'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\APS\\OneDrive\\Exam_(work title)\\root/exam/props/Oculus/work/modeling/versions',
        'md5': u'948c1e62811c305f0c41540ddca2bc58', 'base_dir_alias': None, 'source_path': u'oculus.mb',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000124', 'file_name': u'Oculus_oculus_v001.jpg',
        'snapshot_code': u'SNAPSHOT00000037', 'id': 124, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 168148, '__search_key__': u'sthpw/file?code=FILE00000124', 'type': u'main', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/icon/versions',
        'timestamp': '2015-12-15 13:50:03', 'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
        'md5': u'f4846ef8bce3ddca60091884ae0c93b6', 'base_dir_alias': None,
        'source_path': u'D:\\Alexey\\onedrive\\Exam_(work '
                       u'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus.jpg',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000125', 'file_name': u'Oculus_oculus_web_v001_icon.jpg',
        'snapshot_code': u'SNAPSHOT00000037', 'id': 125, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 27040, '__search_key__': u'sthpw/file?code=FILE00000125', 'type': u'icon', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/icon/versions',
        'timestamp': '2015-12-15 13:50:03', 'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
        'md5': u'af338f9a79b107f7fb1fff078561e02c', 'base_dir_alias': None,
        'source_path': u'D:\\Alexey\\onedrive\\Exam_(work '
                       u'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus_web.jpg',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000126', 'file_name': u'Oculus_oculus_icon_v001_web.png',
        'snapshot_code': u'SNAPSHOT00000037', 'id': 126, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 18486, '__search_key__': u'sthpw/file?code=FILE00000126', 'type': u'web', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/icon/versions',
        'timestamp': '2015-12-15 13:50:03', 'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/icon/versions',
        'md5': u'bc348db0751c0018d81440811de46b28', 'base_dir_alias': None,
        'source_path': u'D:\\Alexey\\onedrive\\Exam_(work '
                       u'title)\\root/temp/upload/aa041d63de28418a828d904b83727750/oculus_icon.png',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000142', 'file_name': u'Oculus_transfer_v001.ma',
        'snapshot_code': u'SNAPSHOT00000041', 'id': 142, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 4314, '__search_key__': u'sthpw/file?code=FILE00000142', 'type': u'main', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/Texturing/versions',
        'timestamp': '2015-12-15 13:51:26', 'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing/versions',
        'md5': u'3bd526ccf7cfd215d0aed8573fae14f6', 'base_dir_alias': None, 'source_path': u'transfer.ma',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000146',
        'file_name': u'Oculus_98736900_korol21_icon_v001_icon.png', 'snapshot_code': u'SNAPSHOT00000041',
        'id': 146, 'project_code': u'exam', 'base_type': u'file', 'st_size': 23929,
        '__search_key__': u'sthpw/file?code=FILE00000146', 'type': u'icon', 'search_id': 1, 'metadata': None,
        'relative_dir': u'exam/props/Oculus/work/Texturing/versions', 'timestamp': '2015-12-15 15:20:43',
        'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing/versions',
        'md5': u'a7d0700a49c43e089d3b079f545d36ee', 'base_dir_alias': None, 'source_path': u'98736900_korol21.jpg',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000149', 'file_name': u'Oculus_98736900_korol21_icon_icon.png',
        'snapshot_code': u'SNAPSHOT00000042', 'id': 149, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 23929, '__search_key__': u'sthpw/file?code=FILE00000149', 'type': u'icon', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/Texturing', 'timestamp': '2015-12-15 15:20:51',
        'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/Texturing',
        'md5': u'a7d0700a49c43e089d3b079f545d36ee', 'base_dir_alias': None, 'source_path': u'98736900_korol21.jpg',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000150',
        'file_name': u'Oculus_tolotoys_9493864_icon_v001_icon.png', 'snapshot_code': u'SNAPSHOT00000011',
        'id': 150, 'project_code': u'exam', 'base_type': u'file', 'st_size': 9617,
        '__search_key__': u'sthpw/file?code=FILE00000150', 'type': u'icon', 'search_id': 1, 'metadata': None,
        'relative_dir': u'exam/props/Oculus/work/modeling/versions', 'timestamp': '2015-12-15 15:37:16',
        'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/modeling/versions',
        'md5': u'512a476e0e8096dd971a721a0e350693', 'base_dir_alias': None, 'source_path': u'tolotoys_9493864.jpg',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    },
    {
        'repo_type': u'tactic', 'code': u'FILE00000153', 'file_name': u'Oculus_tolotoys_9493864_icon_icon.png',
        'snapshot_code': u'SNAPSHOT00000012', 'id': 153, 'project_code': u'exam', 'base_type': u'file',
        'st_size': 9617, '__search_key__': u'sthpw/file?code=FILE00000153', 'type': u'icon', 'search_id': 1,
        'metadata': None, 'relative_dir': u'exam/props/Oculus/work/modeling', 'timestamp': '2015-12-15 15:37:29',
        'file_range': None, 'search_code': u'PROPS00001',
        'checkin_dir': u'D:\\Alexey\\onedrive\\Exam_(work title)\\root/exam/props/Oculus/work/modeling',
        'md5': u'512a476e0e8096dd971a721a0e350693', 'base_dir_alias': None, 'source_path': u'tolotoys_9493864.jpg',
        'search_type': u'exam/props?project=exam', 'metadata_search': None
    }
]

props_codes = ['PROPS00001', 'PROPS00002', 'PROPS00003']
process_codes = ['Texturing', 'Modeling', 'Refs', 'Sculpt']
dict_result = {}
dict_final = {}


def get_snapshot_file_codes(in_dict):

    fl_dict = {}
    root = Et.fromstring(in_dict.encode('utf-8'))

    for i in range(len(root)):

        for fl in root[i].iter('file'):
            fl_dict[fl.attrib['file_code']] = dict(
                name=fl.attrib['name'],
                type=fl.attrib['type'],
                relative_dir=[],
                st_size=[],
                timestamp=[],
            )

    return fl_dict


print get_snapshot_file_codes(full_dict[4])


def get_snapshot_file_info():
    pass


def get_snapshot_dict(sn_code, in_dict):
    """
    Getting info from each snapshot, and return in as structured dictionary
    :param sn_code: individual snapshot code
    :param in_dict: query for current snapshot from base
    :return: structured dictionary tree
    """
    sn_dict = {
        sn_code: {
            'login': [],  # snapshot
            'process': [],  # snapshot
            'context': [],  # snapshot
            'version': [],  # snapshot
            'revision': [],  # snapshot
            'is_latest': [],  # snapshot
            'is_current': [],  # snapshot
            'description': [],  # snapshot
            'search_code': [],  # snapshot
        }
    }
    for dic in in_dict:

        if dic.get('code') == sn_code:
            sn_dict_get = dic.get
            sn_dict[sn_code]['login'].append(sn_dict_get('login'))
            sn_dict[sn_code]['process'].append(sn_dict_get('process'))
            sn_dict[sn_code]['context'].append(sn_dict_get('context'))
            sn_dict[sn_code]['version'].append(sn_dict_get('version'))
            sn_dict[sn_code]['revision'].append(sn_dict_get('revision'))
            sn_dict[sn_code]['is_latest'].append(sn_dict_get('is_latest'))
            sn_dict[sn_code]['is_current'].append(sn_dict_get('is_current'))
            sn_dict[sn_code]['description'].append(sn_dict_get('description'))
            sn_dict[sn_code]['search_code'].append(sn_dict_get('search_code'))

    return sn_dict


for prop_code in props_codes:
    dict_result[prop_code] = dict(code=[], process=[])

    for iter_dict in full_dict:
        if iter_dict.get('search_code') == prop_code:
            dict_result[prop_code]['process'].append(iter_dict.get('process'))
            dict_result[prop_code]['code'].append(iter_dict.get('code'))

    dict_final[prop_code] = {}
    process_codes_pairs = zip(dict_result[prop_code]['process'], dict_result[prop_code]['code'])
    for process in process_codes:
        process_result = {process: []}

        for process_single, dict_single in process_codes_pairs:

            if process_single == process:
                process_result[process].append(get_snapshot_dict(dict_single, full_dict))
        dict_final[prop_code][process] = process_result[process]

# print(dict_final)
