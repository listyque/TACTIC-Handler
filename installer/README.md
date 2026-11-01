# Maya installer

For an existing Windows portable Handler installation, use **Configuration →
Maya Scene → Maya integration**. Find installed/running Maya versions and choose
**Integrate into Maya** or **Remove integration**. This offline path preserves
legacy shelves and user startup scripts, adds a separate TACTIC_Stream shelf,
and pins its connector to this installation. Restart Maya after changes. Do not
use the legacy download presets below to register an already installed build.
Close Maya before removing its registration, to prevent its running UI from
saving the shelf again. Enable/disable the complete integration through
**Configuration → DCC plugins**, effective after restarting Handler.

The integration receipt records only its application root and exact owned file
hashes, not credentials or tickets. Module payloads are outside the modules
search directory. Modified files are protected from overwrite/removal. The
startup bootstrap refuses an SDK already loaded from another root; it never
reloads Qt or clears another integration's Python modules. Existing clients and
discovery records without the optional handler_root field retain their previous
behavior; installation pinning is opt-in for the new managed connector.

The browser application has no local Maya installation counterpart.

## Legacy drag-and-drop installer

Drag `drop_install.mel` into a Maya viewport. Choose the install parent and one
of the presets, then select **Install**. The installer downloads that
preset's ZIP outside Maya's UI thread, validates it, installs it as
`TACTIC-handler`, and creates the `Niki_And_Friends` shelf.

Available button sets:

- **Animation:** Handler, scene save, create/save cache, render setup.
- **Modelling/Rig:** Handler, scene save, texture check-in, attach references.
- **Full:** every action above plus unpack/apply cache.

Each custom action starts the same thin connector and dispatches its existing
`custom_scripts/niki_friends/tools/runners` module. TACTIC credentials,
repositories, and check-in remain owned by the standalone application.
Maya PNG icons live under `thlib/ui/gliph/maya_shelf` and are used
by the matching buttons.

The shelf is created before the download starts. If the package server is
unavailable, copy the application manually into `<Install Path>/TACTIC-handler`;
the installed shelf commands already point there.

Only Python 3 Maya versions are supported.
