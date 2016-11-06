# main_standalone.py
# Start here to run app standalone

import sys
import PySide.QtGui as QtGui
from lib.environment import env_mode
import lib.tactic_classes as tc
import lib.ui_classes.ui_main_classes as ui_main_classes

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
    palette = QtGui.QPalette()
    for role in roles:
        for group in groups:
            color = QtGui.QColor(dct['%s:%s' % (role, group)])
            qGrp = getattr(QtGui.QPalette, group)
            qRl = getattr(QtGui.QPalette, role)
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


def create_ui(thread):
    thread = tc.treat_result(thread)
    if thread.result == QtGui.QMessageBox.ApplyRole:
        retry_startup(thread)
    else:
        if thread.isFailed():
            env_mode.set_offline()
            window = ui_main_classes.Ui_Main(parent=None)
        else:
            env_mode.set_online()
            window = ui_main_classes.Ui_Main(parent=None)
        window.statusBar()
        window.show()

        if thread.result == QtGui.QMessageBox.ActionRole:
            window.open_config_dialog()


def retry_startup(thread):
    thread.run()
    create_ui(thread)


def startup():
    app = QtGui.QApplication(sys.argv)
    app.setStyle("plastique")
    setPaletteFromDct(palette)
    ping_thread = tc.get_server_thread(dict(), tc.server_ping, lambda: create_ui(ping_thread), parent=app)
    ping_thread.start()
    sys.exit(app.exec_())

if __name__ == '__main__':
    startup()
