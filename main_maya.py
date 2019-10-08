# main.py
# Start here

CURRENT_PATH = '/home/krivospickiy_a/MEGA/Work/CGProjects/tacticbase_dev/TACTIC-handler'

import sys
if CURRENT_PATH not in sys.path:
    sys.path.append(CURRENT_PATH)
import thlib.environment as thenv
thenv.env_mode.set_current_path(CURRENT_PATH)
thenv.env_mode.set_mode('maya')
import thlib.ui_classes.ui_maya_dock as main

reload(main)

# To restart set restart=True; default False;
# hotkeys = {
#     'project': 'complex_testing_phase_two',
#     'control_tab': 'checkout'
# }
# example: main.startup(restart=True, hotkeys=hotkeys): run app, open complex_testing_phase_two project, checkout tab and restart if app already started.
# main.startup(hotkeys={'control_tab': 'checkin'}): just raise and set active tab to checkin, tab with current project

hotkeys = None

main.startup(hotkeys=hotkeys)
