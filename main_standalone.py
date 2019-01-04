# main_standalone.py
# Start here to run app standalone

import sys

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui

from thlib.environment import env_mode, env_inst
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.ui_classes.ui_main_classes as ui_main_classes


def reload_modules():
    reload(ui_main_classes)


groups = ['Disabled', 'Active', 'Inactive', 'Normal']
roles = ['Window',
         'Background',
         'WindowText',
         'Foreground',
         'Base',
         'AlternateBase',
         'ToolTipBase',
         'ToolTipText',
         'Text',
         'Button',
         'ButtonText',
         'BrightText']


def getPaletteInfo():
    palette = QtGui.QApplication.palette()
    # build a dict with all the colors
    result = {}
    for role in roles:
        for group in groups:
            qGrp = getattr(QtGui.QPalette, group)
            qRl = getattr(QtGui.QPalette, role)
            result['%s:%s' % (role, group)] = palette.color(qGrp, qRl).rgba()
    return result


def setPaletteFromDct(dct):
    palette = Qt4Gui.QPalette()
    for role in roles:
        for group in groups:
            color = Qt4Gui.QColor(dct['%s:%s' % (role, group)])
            qGrp = getattr(Qt4Gui.QPalette, group)
            qRl = getattr(Qt4Gui.QPalette, role)
            palette.setColor(qGrp, qRl, color)

    QtGui.QApplication.setPalette(palette)


palette = {
    'Foreground:Active': 4290493371L, 'Text:Disabled': 4285098345L, 'WindowText:Normal': 4290493371L,
    'Window:Active': 4282664004L, 'AlternateBase:Inactive': 4281216558L, 'BrightText:Inactive': 4280624421L,
    'Base:Disabled': 4281019179L, 'BrightText:Normal': 4280624421L, 'Background:Inactive': 4282664004L,
    'AlternateBase:Disabled': 4281216558L, 'Button:Inactive': 4284308829L, 'AlternateBase:Active': 4281216558L,
    'ToolTipBase:Disabled': 4294967260L, 'Base:Active': 4281019179L, 'Text:Inactive': 4291348680L,
    'Button:Disabled': 4283124555L, 'BrightText:Disabled': 4294967295L, 'ToolTipBase:Active': 4294967260L,
    'ButtonText:Normal': 4293848814L, 'ToolTipBase:Inactive': 4294967260L, 'Button:Active': 4284308829L,
    'ButtonText:Disabled': 4286611584L, 'Base:Inactive': 4281019179L, 'BrightText:Active': 4280624421L,
    'AlternateBase:Normal': 4281216558L, 'Window:Disabled': 4282664004L, 'Window:Inactive': 4282664004L,
    'Window:Normal': 4282664004L, 'Foreground:Disabled': 4286611584L, 'Text:Normal': 4291348680L,
    'WindowText:Inactive': 4290493371L, 'ToolTipBase:Normal': 4294967260L, 'WindowText:Disabled': 4286611584L,
    'ButtonText:Active': 4293848814L, 'ToolTipText:Normal': 4278190080L, 'Text:Active': 4291348680L,
    'WindowText:Active': 4290493371L, 'Base:Normal': 4281019179L, 'Background:Normal': 4282664004L,
    'Background:Disabled': 4282664004L, 'Button:Normal': 4284308829L, 'ButtonText:Inactive': 4293848814L,
    'Background:Active': 4282664004L, 'ToolTipText:Inactive': 4278190080L, 'ToolTipText:Disabled': 4278190080L,
    'Foreground:Normal': 4290493371L, 'ToolTipText:Active': 4278190080L, 'Foreground:Inactive': 4290493371L
}


@gf.catch_error
def create_ui(ping_worker):
    if ping_worker.is_failed():
        env_mode.set_offline()
        if not env_inst.ui_main:
            window = ui_main_classes.Ui_Main(parent=None)
            window.statusBar()
            window.show()
        gf.error_handle(ping_worker.get_error_tuple())
    else:
        env_mode.set_online()
        offline_ui = None
        if env_inst.ui_main:
            offline_ui = env_inst.ui_main
        window = ui_main_classes.Ui_Main(parent=None)
        if offline_ui:
            offline_ui.close()
        window.statusBar()
        window.show()


@gf.catch_error
def startup():
    app = QtGui.QApplication(sys.argv)
    env_inst.ui_super = app
    app.setStyle("plastique")
    setPaletteFromDct(palette)

    def server_ping_agent():
        return tc.server_ping()

    ping_worker = gf.get_thread_worker(server_ping_agent, finished_func=lambda: create_ui(ping_worker))
    ping_worker.try_start()
    sys.exit(app.exec_())


if __name__ == '__main__':
    startup()
