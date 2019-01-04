# module General Ui
# file ui_maya_dock.py
# Main Dock Window interface

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_mode, env_read_config, env_write_config
import thlib.tactic_classes as tc
import thlib.global_functions as gf

import ui_main_classes

reload(ui_main_classes)


def init_env(current_path):
    env_mode.set_current_path(current_path)
    env_mode.set_mode('maya')


@gf.catch_error
def create_ui(ping_worker, hotkeys=None):

    if ping_worker.is_failed():
        env_mode.set_offline()
        main_tab = Ui_DockMain()
        gf.error_handle(ping_worker.get_error_tuple())
    else:
        env_mode.set_online()
        main_tab = Ui_DockMain(hotkeys=hotkeys)

    main_tab.show()
    main_tab.raise_()


@gf.catch_error
def startup(restart=False, hotkeys=None):
    if restart:
        close_all_instances()

    env_inst.ui_super = mf.get_maya_window()

    try:
        main_tab = mf.get_maya_dock_window()[0]
        main_tab.hotkeys_dict = hotkeys
        main_tab.handle_hotkeys()
        main_tab.show()
        main_tab.raise_()
    except:

        def server_ping_agent():
            return tc.server_ping()

        ping_worker = gf.get_thread_worker(server_ping_agent, finished_func=lambda: create_ui(ping_worker, hotkeys))
        ping_worker.try_start()
