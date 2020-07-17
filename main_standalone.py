# main_standalone.py
# Start here to run app standalone

import sys
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui

from thlib.environment import env_mode, env_inst

import thlib.global_functions as gf

import thlib.tactic_classes as tc

import thlib.ui_classes.ui_main_classes as ui_main_classes

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
    'Foreground:Active': 4290493371, 'Text:Disabled': 4285098345, 'WindowText:Normal': 4290493371,
    'Window:Active': 4282664004, 'AlternateBase:Inactive': 4281216558, 'BrightText:Inactive': 4280624421,
    'Base:Disabled': 4281019179, 'BrightText:Normal': 4280624421, 'Background:Inactive': 4282664004,
    'AlternateBase:Disabled': 4281216558, 'Button:Inactive': 4284308829, 'AlternateBase:Active': 4281216558,
    'ToolTipBase:Disabled': 4294967260, 'Base:Active': 4281019179, 'Text:Inactive': 4291348680,
    'Button:Disabled': 4283124555, 'BrightText:Disabled': 4294967295, 'ToolTipBase:Active': 4294967260,
    'ButtonText:Normal': 4293848814, 'ToolTipBase:Inactive': 4294967260, 'Button:Active': 4284308829,
    'ButtonText:Disabled': 4286611584, 'Base:Inactive': 4281019179, 'BrightText:Active': 4280624421,
    'AlternateBase:Normal': 4281216558, 'Window:Disabled': 4282664004, 'Window:Inactive': 4282664004,
    'Window:Normal': 4282664004, 'Foreground:Disabled': 4286611584, 'Text:Normal': 4291348680,
    'WindowText:Inactive': 4290493371, 'ToolTipBase:Normal': 4294967260, 'WindowText:Disabled': 4286611584,
    'ButtonText:Active': 4293848814, 'ToolTipText:Normal': 4278190080, 'Text:Active': 4291348680,
    'WindowText:Active': 4290493371, 'Base:Normal': 4281019179, 'Background:Normal': 4282664004,
    'Background:Disabled': 4282664004, 'Button:Normal': 4284308829, 'ButtonText:Inactive': 4293848814,
    'Background:Active': 4282664004, 'ToolTipText:Inactive': 4278190080, 'ToolTipText:Disabled': 4278190080,
    'Foreground:Normal': 4290493371, 'ToolTipText:Active': 4278190080, 'Foreground:Inactive': 4290493371
}


def create_ui(error_tuple=None):

    if error_tuple:
        env_mode.set_offline()
        if not env_inst.ui_main:
            window = ui_main_classes.Ui_Main(parent=None)
            window.statusBar()
            window.show()
        gf.error_handle(error_tuple)
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

    env_inst.ui_super = QtGui.QApplication(sys.argv)
    env_inst.ui_super.setApplicationName('TacticHandler_Client')
    env_inst.ui_super.setStyle('fusion')
    setPaletteFromDct(palette)

    def server_ping_agent():
        return tc.server_ping()

    ping_worker, thread_pool = gf.get_thread_worker(
        server_ping_agent,
        finished_func=create_ui,
        error_func=create_ui
    )
    thread_pool.start(ping_worker)

    sys.exit(env_inst.ui_super.exec_())


if __name__ == '__main__':
    startup()
