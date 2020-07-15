import importlib
from . import version

module_name = "QtWidgets"
if version in ["PySide", "PyQt4"]:
    module_name = "QtGui"

module = importlib.import_module(version + "." + module_name)

globals().update({k: getattr(module, k) for k in dir(module) if not k.startswith("_")})
