__all__ = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "QtNetwork"
]

import os
import sys
import site


module_data = []
cache = []
for path in sys.path + site.PREFIXES:
    path = path.replace("\\", "/").rstrip("/")
    if path in cache:
        continue

    cache.append(path)

    if not os.path.isdir(path):
        continue

    for name in os.listdir(path):
        if "." in name:
            name, ext = name.split(".", 1)
            if ext not in ["py", "pyw", "pyc", "pyd"]:
                continue

        if name in module_data:
            continue

        module_data.append(name)


available_versions = [name for name in ["PySide", "PyQt4", "PySide2", "PyQt5"] if name in module_data]
version = available_versions and available_versions[0] or "PySide2"
