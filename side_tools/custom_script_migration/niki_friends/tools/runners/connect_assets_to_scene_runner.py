from importlib import import_module, reload


module = reload(import_module(
    "custom_scripts.niki_friends.tools.modules.connect_assets_to_scene_module"
))

RESULT = module.begin_process_assets()
