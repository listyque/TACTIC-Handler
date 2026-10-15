# Paste into TACTIC Handler Script Editor and run as Server Python.
# This creates a shell script on the Linux server; it does NOT run the upgrade.
import os
import pwd
import shlex
import shutil
import sys
import tempfile

from pyasm.common import Environment

if os.name != "posix":
    raise RuntimeError("This script must run on the Linux TACTIC server")
if not Environment.get_security().is_admin():
    raise PermissionError("TACTIC administrator access is required")
install_dir = os.path.realpath(Environment.get_install_dir())
upgrade_py = os.path.join(install_dir, "src", "bin", "upgrade_db.py")
if not os.path.isfile(upgrade_py):
    raise FileNotFoundError(upgrade_py)

if os.path.basename(sys.executable).startswith("python"):
    python_cmd = [sys.executable]
else:
    python_cmd = shlex.split(Environment.get_python_exec() or "")
    if not python_cmd:
        raise RuntimeError("TACTIC has no configured Python interpreter")
    python_cmd[0] = shutil.which(python_cmd[0]) or ""
if not python_cmd[0] or not os.access(python_cmd[0], os.X_OK):
    raise RuntimeError("Cannot find the server's Python interpreter")

run_dir = tempfile.mkdtemp(prefix="tactic-upgrade-", dir=Environment.get_tmp_dir())
script_path = os.path.join(run_dir, "upgrade_all.sh")
log_path = os.path.join(run_dir, "upgrade.log")
quote = shlex.quote
lines = [
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    'if [ "$(id -u)" -eq 0 ]; then echo "Run as the TACTIC service user, not root"; exit 1; fi',
    'read -r -p "Backups ready and TACTIC stopped? Type UPGRADE: " answer',
    '[ "$answer" = UPGRADE ] || exit 1',
]
environment = {
    "TACTIC_INSTALL_DIR": install_dir,
    "TACTIC_DATA_DIR": Environment.get_data_dir(),
    "TACTIC_SITE_DIR": os.environ.get("TACTIC_SITE_DIR"),
    "TACTIC_CONFIG_PATH": os.environ.get("TACTIC_CONFIG_PATH"),
}
for name, value in environment.items():
    if value:
        lines.append("export %s=%s" % (name, quote(value)))
lines += [
    "cd %s" % quote(install_dir),
    "%s %s -y 2>&1 | tee %s" % (
        " ".join(quote(arg) for arg in python_cmd), quote(upgrade_py), quote(log_path)
    ),
    'echo "Review every project upgrade_output.txt; exit status alone is not proof of success."',
]
with open(script_path, "x", encoding="utf-8", newline="\n") as script:
    script.write("\n".join(lines) + "\n")
os.chmod(script_path, 0o700)

return {
    "server_script": script_path,
    "run_as": pwd.getpwuid(os.getuid()).pw_name,
    "command": "bash %s" % quote(script_path),
    "console_log": log_path,
}
