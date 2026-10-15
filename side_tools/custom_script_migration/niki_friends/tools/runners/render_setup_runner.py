from importlib import import_module, reload


module = reload(import_module(
    "custom_scripts.niki_friends.tools.modules.render_setup_module"
))

RESULT = module.create_render_setup_dialog()
