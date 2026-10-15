from importlib import import_module, reload


module = reload(import_module(
    "custom_scripts.niki_friends.tools.modules.save_current_scene_module"
))

RESULT = module.save_current_scene_as_new_version()
