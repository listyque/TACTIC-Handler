from importlib import import_module, reload


module = reload(import_module(
    "custom_scripts.niki_friends.tools.modules.checkin_cache_module"
))

RESULT = module.create_cache_from_scene()
