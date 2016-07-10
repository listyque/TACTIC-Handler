# main.py
# Start here

import os
import sys

DATA_DIR = os.environ['TACTIC_DATA_DIR'] + '/TACTIC-handler'
if DATA_DIR not in sys.path:
    sys.path.append(DATA_DIR)
import lib.environment as env
env.Mode.set_mode('maya')
import lib.ui_classes.ui_maya_dock as main

reload(main)

# Set 0 to open first tab at start, set 1 to second. etc...
# To restart set restart=True; default False;
# example: main.startup(0, True): run app, open checkout tab and restart if app already started.
# main.startup(0): just raise and set active tab to checkout

main.startup()
