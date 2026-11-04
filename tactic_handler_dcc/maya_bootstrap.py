"""Small Python 3 Maya entry point installed by Handler Configuration."""

import json
import os
import subprocess
import sys
from pathlib import Path

_launch_process = None

def _root():
    receipt = Path(__file__).resolve().parents[1] / "integration.json"
    root = Path(json.loads(receipt.read_text(encoding="utf-8"))["handler_root"]).resolve()
    if not (root / "launch.pyw").is_file():
        raise FileNotFoundError("Handler moved. Reinstall the Maya integration from Configuration.")
    return root


def _maya(root):
    for name, module in list(sys.modules.items()):
        if name.split(".")[0] not in {
            "handler_server", "tactic_handler_dcc", "tactic_handler_api", "thlib", "custom_scripts"
        }:
            continue
        origin = getattr(module, "__file__", None)
        locations = [origin] if origin else list(getattr(module, "__path__", []))
        if any(not Path(location).resolve().is_relative_to(root) for location in locations):
            raise RuntimeError("Another Handler integration is loaded. Save work and restart Maya to switch.")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tactic_handler_dcc import maya
    return maya


def _shelf():
    from maya import cmds, mel

    name = "TACTIC_Stream"
    command = "import tactic_stream_maya; tactic_stream_maya.connect(show=True)"
    icon = _root() / "thlib/ui/gliph/maya_shelf/tactic_logo.png"
    if not icon.is_file():
        raise FileNotFoundError("The Handler Maya shelf icon is unavailable")
    appearance = dict(
        image1=icon.as_posix(), imageOverlayLabel="", useAlpha=True,
        overlayLabelColor=(0.9, 0.9, 0.9), overlayLabelBackColor=(0.08, 0.08, 0.08, 0.85),
        width=35, height=34,
    )
    if cmds.shelfLayout(name, exists=True):
        for button in cmds.shelfLayout(name, query=True, childArray=True) or []:
            if cmds.objectTypeUI(button) != "shelfButton":
                continue
            if (cmds.shelfButton(button, query=True, docTag=True) == "tactic_stream/integration"
                    and cmds.shelfButton(button, query=True, command=True) == command):
                cmds.shelfButton(button, edit=True, **appearance)
        return
    parent = mel.eval("$tsShelfTop = $gShelfTopLevel")
    shelf = cmds.shelfLayout(name, parent=parent)
    cmds.shelfButton(
        parent=shelf, label="TACTIC Handler", annotation="Open TACTIC Handler",
        sourceType="python", command=command, docTag="tactic_stream/integration", **appearance,
    )


def connect(show=False):
    global _launch_process
    from maya import cmds

    try:
        root = _root()
        maya = _maya(root)
        runtime = maya.runtime()
        if runtime is not None and runtime.state not in {"stopped", "failed"}:
            client_root = getattr(runtime.client, "handler_root", "")
            if not client_root or Path(client_root).resolve() != root:
                raise RuntimeError("Another Handler connection is active. Save work and restart Maya to switch.")
        if runtime is None or runtime.state in {"stopped", "failed"}:
            runtime = maya.startup(root, autostart_handler=False,
                                   show_on_connect=bool(show), pin_handler=True)
        if show:
            runtime._show_on_connect = True
            if runtime.connected or (
                hasattr(runtime, "wait_until_connected")
                and runtime.wait_until_connected(0.2)
            ):
                runtime.show_handler()
            else:
                if _launch_process is not None and _launch_process.poll() is None:
                    return runtime
                launcher = root.parent / "TACTIC Handler.exe"
                if not launcher.is_file():
                    raise FileNotFoundError("Start Handler manually; this installation has no TACTIC Handler.exe")
                if os.name != "nt":
                    raise OSError("The portable Handler launcher requires Windows")
                _launch_process = subprocess.Popen(
                    [str(launcher)], cwd=str(root.parent),
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
        return runtime
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        cmds.warning("TACTIC Stream integration: " + str(error))
        return None


def autostart():
    from maya import cmds

    try:
        _shelf()
        return connect()
    except (OSError, RuntimeError) as error:
        cmds.warning("TACTIC Stream integration: " + str(error))
        return None
