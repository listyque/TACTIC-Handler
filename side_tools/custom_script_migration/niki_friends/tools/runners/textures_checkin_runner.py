from importlib import import_module, reload


module = reload(import_module(
    "custom_scripts.niki_friends.tools.modules.checkin_textures_module"
))

RESULT = module.begin_process_textures()
