# Maya and studio tools

**The scene lives in Maya. Its production context lives in Handler.**

[TACTIC Handler](../../README.md) · [Русский](maya.ru.md) · [Full feature tour](product-tour.en.md)

The Maya plugin connects a selected Maya session to standalone Handler through the local Handler Server. Open a published scene, import a file, create a reference or prepare a scene for publication from the production workspace. A native shelf provides Handler launch and project tools.

![Maya 2023: demonstration blockout and native Orbit Studio shelf created by the TH connector](../assets/product-tour/maya-shelf.png)

*Fresh capture of installed Maya 2023 with a separate profile. The actual connector created the shelf; the geometry is a demonstration blockout. This capture demonstrates shelf creation, not a complete Maya scene-publication acceptance run.*

## From a project version to an open scene

Select the object, process and required publication in standard Item View or Snapshot Browser. Handler resolves the file through the local repository and routes the action to the selected Maya session.

| Action | Result |
| --- | --- |
| **Open** | Opens the scene; an option sets its directory as the Maya workspace. |
| **Import** | Imports a file into the current scene, with the supported action's options. |
| **Reference** | Creates a file reference in the current scene. |
| **Save / check-in preparation** | Maya prepares the scene; Handler continues publication through Commit Queue. |

When several sessions are connected, select the intended client. Each command targets a particular Maya session rather than whichever process happens to be nearby.

## From a working scene to a publication

1. Select the object and publication context in Handler.
2. Prepare the scene through connected Maya; choose ASCII or Binary where needed.
3. Review the description, version, file roles and resolved paths in Commit Queue.
4. Submit check-in and return to the result through the object's snapshots.

Maya owns its native scene operations. TACTIC authentication, naming, repository work, transfers and publication records remain with Handler and the server. Maya Scene settings control the format, project-directory creation, playblast preparation where supported, and focus after native actions.

[Publishing and files](product-tour.en.md#from-working-file-to-traceable-publication) · [Maya Scene Help](../../thlib/ui/help_articles/configuration.maya.en.md)

## Shelf: turn a script into an everyday tool

The shelf sits beside Search. A familiar button runs in the context of the project and selection; its editor retains the saved-script reference, label, tooltip, icon and order.

![Standard Item View and the project's shared shelf](../assets/product-tour/item-view-shelf.png)

A **personal shelf** belongs to the signed-in user. A **shared shelf** provides team tools and requires the appropriate authoring permissions. Either owner can have a common set or a shelf assigned to a specific sidebar tab. Editing a personal shelf does not rewrite the shared definition.

![Shared shelf editor: three saved read-only project scripts](../assets/product-tour/shelf-editor.png)

Create a tool in Script Editor, save it and add it to the shelf. A short label helps people find it; the tooltip explains its purpose. The saved script determines its runtime: local Python, the server and a selected DCC session have different data and capabilities. Named script access rules also apply to its shelf button.

### The same shelf in Maya

When a connected Maya client advertises `create_script_shelf`, the editor can create or update a native shelf. Enter its name and confirm replacement when it already exists. The first button starts or reveals Handler. The remaining buttons preserve order, labels, tooltips, rendered icons and project-script references. Maya persists the tab through its native shelf mechanism.

![Native Maya buttons: Handler and Assets, Tasks, Versions tools](../assets/product-tour/maya-shelf-strip.png)

A Maya shelf is a saved export. Update it through the editor after changing buttons or access; saving a Handler shelf does not continuously synchronize every Maya session.

[Complete Script Shelf Help](../../thlib/ui/help_articles/script_shelf.en.md) · [Script Editor](../../thlib/ui/help_articles/script_editor.en.md)

## Connect installed Maya

1. Enable the Maya plugin in **Configuration → DCC plugins**. Restart Handler if the plugin selection changed.
2. Open **Configuration → Maya Scene → Maya integration** and select **Find Maya**.
3. Choose the version/profile and select **Integrate into Maya**.
4. Restart Maya. Its **TACTIC_Stream** shelf provides the Handler button; the connector waits for this exact application installation.

Managed integration supports Windows and Python 3 Maya, starting with Maya 2022. It adds its own module and separate shelf while preserving existing user startup scripts and shelves. Register again after moving Handler. Use **Remove integration** with Maya closed; modified and foreign files are protected.

[Installation and legacy drag-and-drop installer](../../installer/README.md) · [DCC API](../dcc_api.md) · [Connection protocol](../thin_client_protocol.md)

These are Handler desktop capabilities. Stream's browser uses the same server objects and publications; native Handler supplies local Maya access. The product remains a prototype: validate your open, save and check-in workflow on a scene copy before production use.
