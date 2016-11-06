import json
import PySide.QtCore as QtCore
from environment import env_mode, env_server


def singleton(cls):
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls
        return instances[cls]

    return get_instance()


@singleton
class Controls(object):
    def __init__(self):
        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/pages_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)
        self.server = None
        self.project = None
        self.checkin = None
        self.checkout = None
        self.checkin_out = None
        self.checkin_out_projects = None
        self.checkin = None
        self.maya_scene = None

    def get_server(self):
        if self.server:
            return self.server
        else:
            self.settings.beginGroup('config')
            self.server = json.loads(self.settings.value('server', 'null'))
            self.settings.endGroup()
            return self.server

    def set_server(self, server):
        self.server = server
        self.settings.beginGroup('config')
        self.settings.setValue('server', json.dumps(server, separators=(',', ':')))
        self.settings.endGroup()

    def get_project(self):
        if self.project:
            return self.project
        else:
            self.settings.beginGroup('config')
            self.project = self.settings.value('project', None)
            self.settings.endGroup()
            return self.project

    def set_project(self, project):
        self.project = project
        self.settings.beginGroup('config')
        self.settings.setValue('project', project)
        self.settings.endGroup()

    def get_checkout(self):
        if self.checkout:
            return self.checkout
        else:
            self.settings.beginGroup('config')
            self.checkout = json.loads(self.settings.value('checkout', 'null'))
            self.settings.endGroup()
            return self.checkout

    def set_checkout(self, checkout):
        self.checkout = checkout
        self.settings.beginGroup('config')
        self.settings.setValue('checkout', json.dumps(checkout, separators=(',', ':')))
        self.settings.endGroup()

    def get_checkin(self):
        if self.checkin:
            return self.checkin
        else:
            self.settings.beginGroup('config')
            self.checkin = json.loads(self.settings.value('checkin', 'null'))
            self.settings.endGroup()
            return self.checkin

    def set_checkin(self, checkin):
        self.checkin = checkin
        self.settings.beginGroup('config')
        self.settings.setValue('checkin', json.dumps(checkin, separators=(',', ':')))
        self.settings.endGroup()

    def get_checkin_out(self):
        if self.checkin_out:
            return self.checkin_out
        else:
            self.settings.beginGroup('config')
            self.checkin_out = json.loads(self.settings.value('checkin_out', 'null'))
            self.settings.endGroup()
            return self.checkin_out

    def set_checkin_out(self, checkin_out):
        self.checkin_out = checkin_out
        self.settings.beginGroup('config')
        self.settings.setValue('checkin_out', json.dumps(checkin_out, separators=(',', ':')))
        self.settings.endGroup()

    def get_checkin_out_projects(self):
        if self.checkin_out_projects:
            return self.checkin_out_projects
        else:
            self.settings.beginGroup('config')
            self.checkin_out_projects = json.loads(self.settings.value('checkin_out_projects', 'null'))
            self.settings.endGroup()
            return self.checkin_out_projects

    def set_checkin_out_projects(self, checkin_out_projects):
        self.checkin_out_projects = checkin_out_projects
        self.settings.beginGroup('config')
        self.settings.setValue('checkin_out_projects', json.dumps(checkin_out_projects, separators=(',', ':')))
        self.settings.endGroup()

    def get_maya_scene(self):
        self.settings.beginGroup('config')
        self.maya_scene = self.settings.value('maya_scene', None)
        self.settings.endGroup()
        return self.maya_scene

    def set_maya_scene(self, maya_scene):
        self.maya_scene = maya_scene
        self.settings.beginGroup('config')
        self.settings.setValue('maya_scene', maya_scene)
        self.settings.endGroup()

cfg_controls = Controls()