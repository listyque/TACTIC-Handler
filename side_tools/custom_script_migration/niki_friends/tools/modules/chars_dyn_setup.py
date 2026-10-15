import maya.cmds as cmds
import maya.OpenMaya as om
try:
    import PySide6.QtWidgets as QtWidgets
except ImportError:
    import PySide2.QtWidgets as QtWidgets
from functools import partial

from tactic_handler_dcc import maya as handler_maya


def select_maya_node(selection_list=False, transforms=False):
    if not selection_list:
        cmds.select(clear=True)
    else:
        if transforms:
            selection_transforms = cmds.listRelatives(selection_list, parent=True, fullPath=True)
        else:
            selection_transforms = selection_list

        cmds.select(selection_transforms, replace=True)


def sync_selected(proc, remove=False):
    if remove:
        om.MMessage.removeCallback(proc)
    else:
        return om.MEventMessage.addEventCallback("SelectionChanged", proc)


def handle_spinbox(node=None, spinbox=None, arg=None):
    spinbox.setValue(float(cmds.getAttr(node)))


def get_all_dyn_nodes():
    transform_nodes = cmds.ls(type='transform')
    found_nodes = {}
    
    for trans in transform_nodes:
        attrs = cmds.listAttr(trans, userDefined=True)
        if attrs:
            for attr in attrs:
                if attr.find('ynamic') != -1:
                    found_nodes[trans] = attr
    
    return found_nodes


def create_chars_setup_dialog():
    main_dialog = QtWidgets.QDialog(handler_maya.get_maya_window())
    main_dialog.setWindowTitle('Dolly 3D Characters Setup')

    # Setting Main Dialog Attributes
    main_dialog.setMinimumWidth(420)
    main_dialog.setMinimumHeight(140)

    main_layout = QtWidgets.QVBoxLayout()
    main_dialog.setLayout(main_layout)

    # Creating Render Setup Button
    # Creating Shot Attributes
    layouts_list = []
    dyn_nodes = get_all_dyn_nodes()

    for node, value in sorted(dyn_nodes.items()):
        full_node = '{0}.{1}'.format(node, value)
        char_label = QtWidgets.QLabel('{0} / {1}'.format(node.split(':')[0].replace('_', ' ').title(), node.split(':')[1].replace('DynamicCtrl01', '')))
        value_edit = QtWidgets.QDoubleSpinBox()
        value_edit.setDecimals(3)
        value_edit.setMaximum(1)
        value_edit.setSingleStep(0.05)
        value_edit.setValue(float(cmds.getAttr('{0}.{1}'.format(node, value))))
        value_edit.setMaximumWidth(60)
        proc = partial(handle_spinbox, full_node, value_edit)
        #sync_selected(proc)
        cmds.scriptJob(attributeChange=[full_node, proc] )
        select_node_button = QtWidgets.QPushButton('Select')
        select_node_button.setMaximumWidth(80)
        select_node_button.clicked.connect(partial(select_maya_node, node))
        add_key_button = QtWidgets.QPushButton('Key')
        add_key_button.setMaximumWidth(40)
        add_key_button.clicked.connect(partial(cmds.setKeyframe, full_node))

        #    create_tactic_episode_button.clicked.connect(lambda: create_tactic_episode(int(episode_edit.text()), int(shot_edit.text())))
        items_layout = QtWidgets.QHBoxLayout()
        items_layout.addWidget(char_label)
        items_layout.addWidget(value_edit)
        items_layout.addWidget(add_key_button)
        items_layout.addWidget(select_node_button)
        layouts_list.append(items_layout)

    # Adding all to Main Layout
    for lay in layouts_list:
        main_layout.addLayout(lay)

    main_dialog.show()

create_chars_setup_dialog()
