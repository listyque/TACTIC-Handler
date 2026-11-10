# Handler in Maya: scenes and studio tools

**From a published version in the project to a scene you can work on.**

[TACTIC Handler](../../README.md) · [Русский](maya.ru.md) · [Full feature tour](product-tour.en.md)

The job starts before opening a scene: you need the right object, process and version. Handler helps you find that publication and pass it to Maya. The plugin connects the selected session through the local Handler Server; its shelf provides Handler launch and project tools.

![Maya 2023: demonstration blockout and native Orbit Studio shelf created by the TH connector](../assets/product-tour/maya-shelf.png)

*Fresh capture of installed Maya 2023 with a separate profile. The actual connector created the shelf; the geometry is a demonstration blockout. This capture demonstrates shelf creation, not a complete Maya scene-publication acceptance run.*

## Open, import or reference the version you need

Find the object and publication in standard Item View or Snapshot Browser, then choose how to use the file: open the scene, import its contents or create a reference. Handler resolves the path through the local repository and sends the action to the selected Maya session.

| Action | Result |
| --- | --- |
| **Open** | Opens the scene; an option sets its directory as the Maya workspace. |
| **Import** | Imports a file into the current scene, with the supported action's options. |
| **Reference** | Creates a file reference in the current scene. |
| **Save / check-in preparation** | Maya prepares the scene; Handler continues publication through Commit Queue. |

When several Maya sessions are open, choose the intended one first. The command addresses that client, so you can work with several scenes while knowing where the action will go.

## Save the scene and hand it over through check-in

1. Select the object and publication context in Handler.
2. Prepare the scene through connected Maya; choose ASCII or Binary where needed.
3. Review the description, version, file roles and resolved paths in Commit Queue.
4. Submit check-in and return to the result through the object's snapshots.

Maya owns its native scene operations. TACTIC authentication, naming, repository work, transfers and publication records remain with Handler and the server. Maya Scene settings control the format, project-directory creation, playblast preparation where supported, and focus after native actions.

[Publishing and files](product-tour.en.md#check-in-and-check-out-hand-files-to-the-next-person) · [Maya Scene Help](../../thlib/ui/help_articles/configuration.maya.en.md)

## Script Shelf: make studio scripts easy to find

A small script becomes an everyday tool when people can find it and understand what it does. The shelf beside Search gives it a button, label, icon and tooltip. Behind the button is the saved script, working with the project and selection context.

![Standard Item View and the project's shared shelf](../assets/product-tour/item-view-shelf.png)

A **personal shelf** belongs to the signed-in user. A **shared shelf** provides team tools and requires the appropriate authoring permissions. Either owner can have a common set or a shelf assigned to a specific sidebar tab. Editing a personal shelf does not rewrite the shared definition.

![Shared shelf editor: three saved read-only project scripts](../assets/product-tour/shelf-editor.png)

Develop and save the tool in Script Editor, then add it to the shelf. Users need a clear label and tooltip; the author also chooses where it runs—local Python, the server or a selected DCC session. Those environments have different data and capabilities. The button retains the named script’s access rules.

### Bring the project shelf into Maya

When a connected Maya client advertises `create_script_shelf`, the editor can create or update a native shelf. Enter its name and confirm replacement when it already exists. The first button starts or reveals Handler. The remaining buttons preserve order, labels, tooltips, rendered icons and project-script references. Maya persists the tab through its native shelf mechanism.

![Native Maya buttons: Handler and Assets, Tasks, Versions tools](../assets/product-tour/maya-shelf-strip.png)

Once exported, the shelf is saved in Maya. Update it through the editor when its buttons or access change. Saving a shelf in Handler does not automatically refresh every connected Maya session.

[Complete Script Shelf Help](../../thlib/ui/help_articles/script_shelf.en.md) · [Script Editor](../../thlib/ui/help_articles/script_editor.en.md)

## Install the connector and connect Maya

1. Enable the Maya plugin in **Configuration → DCC plugins**. Restart Handler if the plugin selection changed.
2. Open **Configuration → Maya Scene → Maya integration** and select **Find Maya**.
3. Choose the version/profile and select **Integrate into Maya**.
4. Restart Maya. Its **TACTIC_Stream** shelf provides the Handler button; the connector waits for this exact application installation.

Managed integration supports Windows and Python 3 Maya, starting with Maya 2022. It adds its own module and separate shelf while preserving existing user startup scripts and shelves. Register again after moving Handler. Use **Remove integration** with Maya closed; modified and foreign files are protected.

[Installation and legacy drag-and-drop installer](../../installer/README.md) · [DCC API](../dcc_api.md) · [Connection protocol](../thin_client_protocol.md)

These are Handler desktop capabilities. Stream's browser uses the same server objects and publications; native Handler supplies local Maya access. The product remains a prototype: validate your open, save and check-in workflow on a scene copy before production use.
