"""Maya drag-and-drop installer based on the legacy Niki shelf installer."""

import os
import posixpath
import shutil
import stat
import tempfile
import threading
import traceback
import urllib.parse
import urllib.request
import zipfile

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtWidgets


SHELF_NAME = "Niki_And_Friends"
INSTALL_DIR_NAME = "TACTIC-handler"
TACTIC_URL = "akaleich.fvds.ru"
INSTALL_PRESETS = {
    "Animation": "http://{}/assets/niki_friends/assets/pipeline/"
    "Tactic-Handler_animators.zip".format(TACTIC_URL),
    "Modelling/Rig": "http://{}/assets/niki_friends/assets/pipeline/"
    "Tactic-Handler_modellers.zip".format(TACTIC_URL),
    "Full": "http://{}/assets/niki_friends/assets/pipeline/"
    "Tactic-Handler_full.zip".format(TACTIC_URL),
}
BUTTONS = {
    "save": (
        "Append Save Current Scene",
        "Click to Save Current Scene As a new Version",
        "save",
        "content-save-edit.png",
        "tools/runners/save_similar_runner",
    ),
    "create_cache": (
        "Create nCache",
        "Click to Create nCache for all Objects",
        "CC",
        "animation.png",
        "tools/runners/cache_create_runner",
    ),
    "save_cache": (
        "Save nCache and Current Scene",
        "Click to Save Created nCache and Current Scene",
        "SC",
        "content-save-all.png",
        "tools/runners/cache_checkin_runner",
    ),
    "textures": (
        "Checkin / Check Textures",
        "Click Checkin / Check all Textures in Current Scene",
        "TEX",
        "buffer.png",
        "tools/runners/textures_checkin_runner",
    ),
    "references": (
        "Attach References",
        "Connect all Referenced Assets to Current Scene",
        "REF",
        "buffer.png",
        "tools/runners/connect_assets_to_scene_runner",
    ),
    "unpack_cache": (
        "Unpack All Caches",
        "Click to Unpack all Caches for Current Episode",
        "GET",
        "download.png",
        "tools/runners/cache_fetcher_runner",
    ),
    "apply_cache": (
        "Apply All Caches",
        "Click to Apply all Caches to Current Episode",
        "APL",
        "run.png",
        "tools/runners/cache_apply_runner",
    ),
    "render_setup": (
        "Render Setup for Episodes",
        "Click to Open Render Setup Dialog",
        "RS",
        "tune.png",
        "tools/runners/render_setup_runner",
    ),
}
PRESET_BUTTONS = {
    "Animation": ("save", "create_cache", "save_cache", "render_setup"),
    "Modelling/Rig": ("save", "textures", "references"),
    "Full": (
        "save",
        "create_cache",
        "save_cache",
        "textures",
        "references",
        "unpack_cache",
        "apply_cache",
        "render_setup",
    ),
}
MAX_EXTRACTED_SIZE = 4 * 1024 * 1024 * 1024

_dialog = None


def _maya_modules():
    from maya import cmds, mel
    return cmds, mel


def _maya_main_window():
    try:
        from maya import OpenMayaUI
        try:
            from shiboken6 import wrapInstance
        except ImportError:
            from shiboken2 import wrapInstance
    except ImportError:
        return None
    pointer = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget) if pointer else None


def _remove(path):
    if os.path.islink(path) or os.path.isfile(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def _extract(archive_path, destination):
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if sum(member.file_size for member in members) > MAX_EXTRACTED_SIZE:
            raise ValueError("Package expands beyond the 4 GiB safety limit")
        for member in members:
            name = posixpath.normpath(member.filename.replace("\\", "/"))
            first = name.split("/", 1)[0]
            if (
                not name
                or "\x00" in name
                or name.startswith("/")
                or name == ".."
                or name.startswith("../")
                or ":" in first
                or stat.S_ISLNK(member.external_attr >> 16)
            ):
                raise ValueError("Unsafe package entry: {!r}".format(member.filename))
        archive.extractall(destination)


def _handler_root(extracted):
    matches = []
    for root, _directories, files in os.walk(extracted):
        if (
            "launch.pyw" in files
            and os.path.isfile(os.path.join(root, "tactic_handler_dcc", "maya.py"))
        ):
            matches.append(root)
    if len(matches) != 1:
        raise ValueError(
            "Package must contain exactly one TACTIC Handler application root"
        )
    return matches[0]


def install_archive(archive_path, install_parent):
    install_parent = os.path.abspath(os.path.expanduser(install_parent))
    os.makedirs(install_parent, exist_ok=True)
    target = os.path.join(install_parent, INSTALL_DIR_NAME)
    staging = tempfile.mkdtemp(prefix=".tactic-handler-install-", dir=install_parent)
    backup = None
    try:
        extracted = os.path.join(staging, "extracted")
        _extract(archive_path, extracted)
        payload = os.path.join(staging, "payload")
        os.replace(_handler_root(extracted), payload)

        if os.path.lexists(target):
            backup = tempfile.mkdtemp(
                prefix=".tactic-handler-backup-", dir=install_parent
            )
            os.rmdir(backup)
            os.replace(target, backup)
        try:
            os.replace(payload, target)
        except Exception:
            if backup and os.path.lexists(backup):
                _remove(target)
                os.replace(backup, target)
            raise
        if backup:
            _remove(backup)
        return target
    finally:
        _remove(staging)


def _valid_url(url):
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def download_and_install(url, install_parent):
    if not _valid_url(url):
        raise ValueError("Package URL must use HTTP or HTTPS")
    install_parent = os.path.abspath(os.path.expanduser(install_parent))
    os.makedirs(install_parent, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".tactic-handler-download-", dir=install_parent
    ) as download_dir:
        archive_path = os.path.join(download_dir, "TACTIC-handler.zip")
        request = urllib.request.Request(
            url,
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": "TACTIC-Handler-Maya-Installer",
            },
        )
        with urllib.request.urlopen(request, timeout=120) as response, open(
            archive_path, "wb"
        ) as output:
            shutil.copyfileobj(response, output)
        return install_archive(archive_path, install_parent)


def shelf_command(handler_root):
    handler_root = os.path.normpath(handler_root).replace("\\", "/")
    return "\n".join(
        (
            "import importlib",
            "import sys",
            "CURRENT_PATH = {!r}".format(handler_root),
            "if CURRENT_PATH not in sys.path:",
            "    sys.path.insert(0, CURRENT_PATH)",
            "from tactic_handler_dcc import maya as tactic_handler_maya",
            "tactic_handler_maya = importlib.reload(tactic_handler_maya)",
            "tactic_handler_maya.startup(CURRENT_PATH)",
        )
    )


def custom_script_command(handler_root, script_path):
    return "{}\ntactic_handler_maya.execute_custom_script({!r}, project={!r})".format(
        shelf_command(handler_root), script_path, "niki_friends"
    )


def create_shelf(handler_root, preset, cmds=None, mel=None):
    if preset not in PRESET_BUTTONS:
        raise ValueError("Unknown shelf preset: {}".format(preset))
    if cmds is None or mel is None:
        cmds, mel = _maya_modules()

    shelf_top = mel.eval("$tmp = $gShelfTopLevel")
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.deleteUI(SHELF_NAME)
    shelf = cmds.shelfLayout(SHELF_NAME, parent=shelf_top)
    icon_dir = os.path.join(handler_root, "thlib", "ui", "gliph", "maya_shelf")
    logo = os.path.join(icon_dir, "tactic_logo.png")
    cmds.shelfButton(
        parent=shelf,
        label="Tactic Handler",
        annotation="This will Start Main Window of Tactic Handler",
        image1=logo if os.path.isfile(logo) else "pythonFamily.png",
        imageOverlayLabel="" if os.path.isfile(logo) else "TH",
        command=shelf_command(handler_root),
        sourceType="python",
    )
    for button_code in PRESET_BUTTONS[preset]:
        label, annotation, overlay, image_name, script_path = BUTTONS[button_code]
        image = os.path.join(icon_dir, image_name)
        cmds.shelfButton(
            parent=shelf,
            label=label,
            annotation=annotation,
            image1=image if os.path.isfile(image) else "pythonFamily.png",
            imageOverlayLabel=overlay,
            command=custom_script_command(handler_root, script_path),
            sourceType="python",
        )
    mel.eval("saveAllShelves $gShelfTopLevel;")
    return shelf


def remove_shelf():
    cmds, mel = _maya_modules()
    if not cmds.shelfLayout(SHELF_NAME, exists=True):
        return False
    cmds.deleteUI(SHELF_NAME)
    mel.eval("saveAllShelves $gShelfTopLevel;")
    return True


class InstallerDialog(QtWidgets.QDialog):
    installed = QtCore.Signal(str)
    failed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Drag and Drop Installation")
        self.resize(550, 80)
        self._busy = False
        self._installing_preset = ""
        self._installing_root = ""

        self.path_edit = QtWidgets.QLineEdit(os.path.dirname(__file__))
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItems(list(INSTALL_PRESETS))
        self.preset_combo.setCurrentText("Modelling/Rig")
        self.install_button = QtWidgets.QPushButton("Install / Reinstall")
        self.uninstall_button = QtWidgets.QPushButton("Uninstall")
        self.status_label = QtWidgets.QLabel("Ready")

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(QtWidgets.QLabel("Install Path:"), 0, 0)
        layout.addWidget(self.path_edit, 0, 1)
        layout.addWidget(QtWidgets.QLabel("Shelf preset:"), 1, 0)
        layout.addWidget(self.preset_combo, 1, 1)
        layout.addWidget(self.install_button, 2, 0)
        layout.addWidget(self.uninstall_button, 2, 1)
        layout.addWidget(self.status_label, 3, 0, 1, 2)

        self.installed.connect(self._installed)
        self.failed.connect(self._failed)
        self.install_button.clicked.connect(self._install)
        self.uninstall_button.clicked.connect(self._uninstall)

    def _set_busy(self, busy):
        self._busy = busy
        self.path_edit.setEnabled(not busy)
        self.preset_combo.setEnabled(not busy)
        self.install_button.setEnabled(not busy)
        self.uninstall_button.setEnabled(not busy)

    def closeEvent(self, event):
        if self._busy:
            event.ignore()
        else:
            super().closeEvent(event)

    def _install(self):
        install_parent = self.path_edit.text().strip()
        if not install_parent:
            QtWidgets.QMessageBox.warning(
                self, "TACTIC Handler", "Choose an install directory."
            )
            return
        self._installing_preset = self.preset_combo.currentText()
        self._installing_root = os.path.join(
            os.path.abspath(os.path.expanduser(install_parent)),
            INSTALL_DIR_NAME,
        )
        try:
            create_shelf(self._installing_root, self._installing_preset)
        except Exception:
            self.status_label.setText("Shelf creation failed")
            self._show_error("The shelf could not be created.", traceback.format_exc())
            return

        url = INSTALL_PRESETS[self._installing_preset]
        self._set_busy(True)
        self.status_label.setText(
            "Shelf ready. Downloading {}...".format(self._installing_preset)
        )

        def run():
            try:
                self.installed.emit(download_and_install(url, install_parent))
            except Exception:
                self.failed.emit(traceback.format_exc())

        threading.Thread(target=run, name="tactic-handler-install", daemon=True).start()

    def _installed(self, handler_root):
        self._set_busy(False)
        self.status_label.setText("Installed: {}".format(handler_root))
        QtWidgets.QMessageBox.information(
            self, "TACTIC Handler", "The {} shelf is ready.".format(SHELF_NAME)
        )

    def _failed(self, details):
        self._set_busy(False)
        self.status_label.setText("Shelf ready; download failed")
        self._show_error(
            "The shelf was created, but the package could not be installed.",
            details,
            "Copy TACTIC Handler files to {}.".format(self._installing_root),
        )

    def _show_error(self, text, details, information=""):
        message = QtWidgets.QMessageBox(self)
        message.setIcon(QtWidgets.QMessageBox.Critical)
        message.setWindowTitle("TACTIC Handler installation failed")
        message.setText(text)
        if information:
            message.setInformativeText(information)
        message.setDetailedText(details)
        (getattr(message, "exec", None) or message.exec_)()

    def _uninstall(self):
        self.status_label.setText(
            "Shelf removed" if remove_shelf() else "Shelf is not installed"
        )


def begin_shelf_install():
    global _dialog
    if _dialog is not None and _dialog._busy:
        _dialog.raise_()
        _dialog.activateWindow()
        return _dialog
    if _dialog is not None:
        _dialog.close()
        _dialog.deleteLater()
    _dialog = InstallerDialog(_maya_main_window())
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
    return _dialog
