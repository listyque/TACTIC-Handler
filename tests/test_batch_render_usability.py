"""Regressions for the batch interaction and presentation contracts."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_BACKEND','software')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE','Basic')
import json
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtCore import QObject, QPointF, Qt, QEvent, QCoreApplication
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest
from batch_render_fixture import BatchCase, episode, Root
from plugins.batch_render import preparation, window as batch_ui
from plugins.batch_render.render import RenderProgress
from thlib.ui.icon_font import fontawesome_assets
import thlib.ui.source_editor

ROOT=Path(__file__).resolve().parents[1]


class BatchUsabilityTests(BatchCase):
    def queue(self,count=6):
        entry=episode('episode',count)
        self.controller._entries=[entry]
        self.controller._publish_queue()
        return entry

    def test_default_filter_excludes_verified_and_taskless_episodes(self):
        c=self.controller
        self.assertNotIn('',c.visibleEpisodeStatuses)
        self.assertNotIn(c._config['terminal_status'],c.visibleEpisodeStatuses)
        self.assertTrue(set(c._config['status_options'])-{c._config['terminal_status']} <= set(c.visibleEpisodeStatuses))
        self.assertIn(c._config['complete_status'],c.visibleEpisodeStatuses)

    def test_addition_is_read_only_on_the_server(self):
        c=self.controller
        api=Mock()
        with patch.object(preparation,'_query_shots',return_value=[{'title':'shot'}]),patch.object(preparation,'_set_episode_task_status') as write:
            records=preparation._discover_queue(api,'episode',c._config,False,'queued')
        self.assertEqual(records,[{'title':'shot'}])
        write.assert_not_called()

    def test_manual_add_does_not_render_even_when_scheduler_was_idle_running(self):
        c=self.controller
        c.episodes.replace([dict(searchKey='episode',title='Episode')])
        c._paused=False
        with patch.object(c,'_discover_entry'),patch.object(c,'_run_stage') as render:
            c._enqueue('episode',False)
            entry=c._entries[0]
            c._discovery_finished(entry,[dict(searchKey='shot',title='Shot',start=1,end=10,excluded=False,previewUrl='',scenePath='scene.ma')])
            render.assert_not_called()
            self.assertFalse(entry['startRequested'])
            c.startScheduler()
            self.assertTrue(entry['startRequested'])
            render.assert_called_once()

    def test_selecting_rows_does_not_reveal_or_rebuild_them(self):
        c=self.controller
        entry=self.queue(100)
        c.episodes.replace([dict(searchKey='episode',selected=False)])
        reveal=QSignalSpy(c.queueSelected)
        catalog_reveal=QSignalSpy(c.episodeSelected)
        with patch.object(c,'_shot_record',wraps=c._shot_record) as projection:
            c.selectQueue(entry['jobs'][40]['id'])
            c.selectQueue(entry['jobs'][41]['id'])
        self.assertEqual(reveal.count(),0)
        self.assertEqual(catalog_reveal.count(),0)
        projection.assert_not_called()
        self.assertTrue(c.queue.get(42)['selected'])

    def test_shift_control_and_plain_selection(self):
        c=self.controller;entry=self.queue()
        ids=[job['id'] for job in entry['jobs']]
        c.selectQueueRange(ids[1],0)
        c.selectQueueRange(ids[4],1)
        self.assertEqual(c._selected_shots,set(ids[1:5]))
        self.assertEqual(c.selectedShotCount,4)
        c.selectQueueRange(ids[2],2)
        self.assertEqual(c._selected_shots,{ids[1],ids[3],ids[4]})
        c.selectQueueRange(ids[0],0)
        self.assertEqual(c._selected_shots,{ids[0]})
        c.selectAllShots(entry['id'])
        self.assertEqual(c._selected_shots,set(ids))

    def test_selected_checkbox_changes_only_the_selected_range(self):
        c=self.controller;entry=self.queue()
        c.selectQueueRange(entry['jobs'][1]['id'],0)
        c.selectQueueRange(entry['jobs'][3]['id'],1)
        c.toggleIncluded(entry['jobs'][2]['id'])
        self.assertEqual([job['state'] for job in entry['jobs']],['waiting','skipped','skipped','skipped','waiting','waiting'])
        c.toggleIncluded(entry['jobs'][2]['id'])
        self.assertTrue(all(job['state']=='waiting' for job in entry['jobs']))

    def test_episode_checkbox_is_tristate_and_protects_finished_active_work(self):
        c=self.controller;entry=self.queue(5)
        entry['jobs'][0].update(state='completed',framesDone=5)
        entry['jobs'][1]['state']='rendering'
        entry['jobs'][2]['state']='skipped'
        entry['state']='rendering';c._active_entry=entry;c._active_job=entry['jobs'][1]
        self.assertEqual(c._episode_include_state(entry),1)
        with patch.object(c,'_pump'):
            c.setEpisodeIncluded(entry['id'],False)
            self.assertEqual([job['state'] for job in entry['jobs']],['completed','rendering','skipped','skipped','skipped'])
            self.assertEqual(c._episode_include_state(entry),0)
            c.setEpisodeIncluded(entry['id'],True)
        self.assertEqual([job['state'] for job in entry['jobs']],['completed','rendering','waiting','waiting','waiting'])
        self.assertEqual(c._episode_include_state(entry),2)
        self.assertEqual(entry['jobs'][0]['framesDone'],5)

    def test_excluded_shots_can_be_reordered_within_the_episode(self):
        c=self.controller;entry=self.queue(4)
        skipped=entry['jobs'][3];skipped['state']='skipped'
        self.assertIn('move',c._allowed_actions(entry,skipped))
        c.moveQueueTo(skipped['id'],entry['jobs'][0]['id'])
        self.assertIs(entry['jobs'][0],skipped)

    def test_render_progress_is_coalesced_and_updates_only_active_rows(self):
        c=self.controller;entry=self.queue(100)
        c._clock.stop();c._active_entry=entry;c._active_job=entry['jobs'][0]
        entry['state']='rendering';c._active_job['state']='rendering'
        with patch.object(c,'_shot_record',wraps=c._shot_record) as projection:
            for index in range(100):c._stage_progress(dict(framesDone=index,text=f'full log event {index}'))
            projection.assert_not_called()
            self.until(lambda:not c._progress_timer.isActive())
            self.assertEqual(projection.call_count,1)
        self.assertEqual(c._active_job['framesDone'],99)
        self.assertEqual(len(c._events),100)
        self.assertIn('full log event 99',c.logText)

    def test_previews_do_not_stat_files_on_the_ui_thread(self):
        c=self.controller;entry=self.queue(1)
        job=entry['jobs'][0];job['renderFiles']=['C:/render/frame.png'];job['renderFileVersions']={'C:/render/frame.png':2}
        c.selectQueue(job['id'])
        with patch.object(Path,'stat',side_effect=AssertionError('UI filesystem access')):
            previews=c.renderPreviews
        self.assertIn('changed=',previews[0]['url'])
        self.assertTrue(previews[0]['url'].endswith('-2'))
        self.assertEqual(c._web_state(job['id'])['previews'][0]['revision'],2)

    def test_rewritten_render_frame_invalidates_its_preview_without_stat(self):
        tracker = RenderProgress(1, 2)
        event = 'TH_BATCH_EVENT ' + json.dumps(dict(type='frame',frame=1,files=['frame.png']))
        first = tracker.feed(event)
        second = tracker.feed(event)
        self.assertEqual(first['renderFiles'], second['renderFiles'])
        self.assertGreater(second['renderFileVersions']['frame.png'], first['renderFileVersions']['frame.png'])

    def test_dynamic_messages_and_inspector_follow_language(self):
        c=self.controller;entry=self.queue(3)
        c.selectQueue(entry['jobs'][0]['id'])
        c.setLanguage('ru')
        self.assertEqual(c.queue.get(0)['subtitle'],'3 шотов · завершено 0')
        self.assertIn('попытка',c.queue.get(1)['subtitle'])
        self.assertEqual(c.selectedDetail['stateLabel'],'Ожидание')
        self.assertEqual(c._text('Frames: 1-5 · attempt 2'),'Кадры: 1-5 · попытка 2')
        c.setLanguage('en')
        self.assertEqual(c._text('Кадры: 1-5 · попытка 2'),'Frames: 1-5 · attempt 2')
        self.assertEqual(c.queue.get(0)['subtitle'],'3 shots · 0 completed')
        self.assertEqual(c.selectedDetail['stateLabel'],'Waiting')
        self.assertEqual(c._config['running_status'],'Рендерится')

    def test_web_selection_and_inclusion_use_the_same_owner(self):
        c=self.controller;entry=self.queue(4)
        c._web_action(dict(action='select',id=entry['jobs'][0]['id'],modifiers=0))
        c._web_action(dict(action='select',id=entry['jobs'][2]['id'],modifiers=1))
        state=c._web_state(entry['jobs'][2]['id'])
        self.assertEqual(state['selectionCount'],3)
        self.assertEqual(state['language'],'en')
        c._web_action(dict(action='include-selected',included=False))
        self.assertTrue(all(job['state']=='skipped' for job in entry['jobs'][:3]))
        c._web_action(dict(action='include-all',id=entry['id'],included=True))
        self.assertTrue(all(job['state']=='waiting' for job in entry['jobs']))

    def test_real_qml_shift_selection_and_checkboxes_preserve_scroll(self):
        c=self.controller
        entry=self.queue(60)
        c.episodes.replace([dict(searchKey=f'catalog-{i}',code=f'EP{i}',title=f'Episode {i}',subtitle='',renderStatus='Подготовлен',previewUrl='',statusColor='#ffffff',selected=False,queued=False,statusChoices=[]) for i in range(100)])
        engine=QQmlEngine();messages=[];engine.warnings.connect(lambda errors:messages.extend(error.toString() for error in errors))
        solid,family,regular,regular_family=fontawesome_assets(ROOT)
        for key,value in dict(fontAwesomeSolidGlyphs=solid,fontAwesomeSolidFontFamily=family,fontAwesomeRegularGlyphs=regular,fontAwesomeRegularFontFamily=regular_family).items():engine.rootContext().setContextProperty(key,value)
        parent=Root();component,window=batch_ui._create_window(engine,ROOT,parent,c)
        window.show();window.requestActivate()
        queue=window.findChild(QObject,'batchQueueList');catalog=window.findChild(QObject,'batchEpisodeList')
        try:
            QTest.qWait(50)
            queue.setProperty('contentY',800);catalog.setProperty('contentY',500)
            QTest.qWait(50)
            self.assertGreater(queue.property('contentY'),500)
            rows=[item for item in self.descendants(window.contentItem()) if item.objectName().startswith('batchQueueRow_') and item.property('depth') == 1 and item.mapToScene(QPointF(160,40)).y()>230 and item.mapToScene(QPointF(160,40)).y()<480]
            self.assertGreaterEqual(len(rows),2)
            rows.sort(key=lambda item:item.mapToScene(QPointF()).y())
            first,last=rows[0],rows[-1]
            before=(queue.property('contentY'),catalog.property('contentY'))
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=first.mapToScene(QPointF(210,30)).toPoint())
            QTest.qWait(200)
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.ShiftModifier,last.mapToScene(QPointF(210,30)).toPoint())
            self.until(lambda:c.selectedShotCount>=2)
            self.assertAlmostEqual(queue.property('contentY'),before[0],delta=1)
            self.assertAlmostEqual(catalog.property('contentY'),before[1],delta=1)
            include=self.visual(last,'batchInclude_'+str(last.property('index')))
            self.assertIsNotNone(include)
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=include.mapToScene(QPointF(include.width()/2,include.height()/2)).toPoint())
            self.until(lambda:all(job['state']=='skipped' for job in entry['jobs'] if job['id'] in c._selected_shots))
            self.assertFalse(messages,messages)
        finally:
            window.hide();window.deleteLater();component.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            engine.deleteLater();self.app.processEvents()

    def descendants(self,item):
        for child in item.childItems():
            yield child
            yield from self.descendants(child)
