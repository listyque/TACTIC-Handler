# Maya installer

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
