import importlib
from . import version

module_name = "QtCore"
module = importlib.import_module(version + "." + module_name)

globals().update({k: getattr(module, k) for k in dir(module) if not k.startswith("_")})

if version in ["PyQt4", "PyQt5"]:
    globals().update({"Signal": getattr(module, "pyqtSignal")})
    globals().update({"Slot": getattr(module, "pyqtSlot")})
    globals().update({"Property": getattr(module, "pyqtProperty")})
