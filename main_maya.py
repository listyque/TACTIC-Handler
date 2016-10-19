# main.py
# Start here

CURRENT_PATH = 'D:/APS/OneDrive/Dropbox/Work/CGProjects/tacticbase_dev/TACTIC-Handler'

import sys
if CURRENT_PATH not in sys.path:
    sys.path.append(CURRENT_PATH)
from lib.environment import env_mode
env_mode.set_current_path(CURRENT_PATH)
env_mode.set_mode('maya')
import lib.ui_classes.ui_maya_dock as main

reload(main)

# Set 0 to open first tab at start, set 1 to second. etc...
# To restart set restart=True; default False;
# example: main.startup(0, True): run app, open checkout tab and restart if app already started.
# main.startup(0): just raise and set active tab to checkout

main.startup()
