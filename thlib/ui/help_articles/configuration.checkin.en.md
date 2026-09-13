---
group: Configuration
icon: publish
order: 33
---
# Check-in Options configuration

> Check-in Options defines result presentation, snapshot defaults, file transfer, Repository Sync,
> Drop Plate completion, and automatic file matching. These are defaults; an operation may expose an
> explicit override in Commit Queue.

## Search results

| Setting | What it controls |
| --- | --- |
| **Preview delivery** | Loads previews through the TACTIC HTTP endpoint instead of requiring direct access to the repository path. |
| **Built-in processes** | Includes TACTIC built-in processes alongside project-defined processes in result items. |
| **Result limit** | Requests 20–5000 sObjects per result page. A larger page reduces paging but costs more time and memory per request. |
| **Loading mode** | **Pages** uses explicit previous/next navigation; **Continuous** requests the next page when scrolling reaches the end. |
| **Default result view** | Opens **Continuous** rows or **Cards** when the Search Tab has no saved view state. |

## Item interactions

**Double-click to save** downloads or saves the selected snapshot with the configured check-out
method. **Shift + double-click to open** opens the selected file with its associated application.
Disable either gesture when double-click should only select an item.

## Versions and descriptions

| Setting | What it controls |
| --- | --- |
| **Separate versions** | Places snapshot versions in their own area instead of mixing them with the main item. |
| **Versions position** | Puts that separate area on the **Right** or **Bottom**; it is available only when versions are separated. |
| **Description length** | When enabled, clips descriptions to 20–50000 characters. Disable it to show complete text. |

## Snapshot Browser defaults

| Setting | Choices and effect |
| --- | --- |
| **Show every snapshot** | Includes snapshots from every process instead of only the selected process. |
| **Show more metadata** | Starts with the additional metadata section expanded. |
| **Initial content** | Shows **Preview and files**, **Preview only**, or **Files only**. |
| **Initial orientation** | Places preview and files side by side (**Horizontal**) or top to bottom (**Vertical**). |

## File transfer

**Check-in method** chooses the TACTIC transfer contract: **Preallocate** prepares the final
repository path before registration; **In-Place** registers a file already at its repository path;
**Copy** copies the source to repository storage; **Move** moves it; **Upload** transfers it through
the server endpoint. Copy and In-Place preserve the source, while Move deliberately relocates it.

**Check-out method** uses **Local** for direct repository-path access or **HTTP** to download through
TACTIC. Use HTTP when the workstation cannot see repository paths directly.

## Snapshot creation

| Setting | What it controls |
| --- | --- |
| **Update versionless snapshot** | Refreshes `latest`/versionless output when a numbered version succeeds. |
| **Generate previews** | Creates supported thumbnails and preview files during preparation. |
| **Clean completed Commit Queue items** | Removes successful queue operations automatically. Failed and cancelled rows remain. |
| **Confirm saving** | Asks before saving a prepared check-in operation. |
| **Confirm revision saving** | Adds a separate confirmation before saving a revision rather than a new version. |
| **Sequence padding** | Enables fixed 1–9 digit frame numbers for generated sequence names. The number is editable only while the switch is on. |

## Repository synchronization

| Setting | What it controls |
| --- | --- |
| **Verify files with MD5** | Compares checksums to detect changed local files. It is stronger than metadata checks but spends additional CPU and disk I/O. |
| **Clean completed downloads** | Removes successful Repository Sync rows after each download batch. |
| **Discovery mode** | **Full scope** discovers the whole requested tree before transfer; **Partial scope** overlaps discovery and transfer in chunks. |
| **Partial scope chunk size** | Uses 1–250 repository records per discovery chunk and is active only in Partial scope. |

## Drop Plate completion

| Setting | What it controls |
| --- | --- |
| **Share Drop Plate across tabs** | Uses one compatible file selection across Search Tabs instead of a selection owned by each tab. |
| **Uncheck submitted files** | Keeps successful files in Drop Plate but clears their check marks. |
| **Clear submitted files** | Removes successful files from Drop Plate. Unsuccessful files remain available for review. |

## File matching and naming

| Setting or action | What it controls |
| --- | --- |
| **Group selected files** | Prepares one multi-file snapshot instead of one snapshot per selected file. |
| **Keep original filename** | Preserves source names instead of applying the active naming template. |
| **Include subfolders** | Recursively scans nested directories added to Drop Plate. |
| **Allow a single UDIM or UV tile** | Recognizes one matching tile as a valid set instead of requiring multiple tiles. |
| **Allow a single-frame sequence** | Recognizes one numbered file as a sequence when its padding matches the rules. |
| **Minimum frame padding** | Accepts automatic sequences only when their frame number has at least 1–9 configured digits. |
| **Matching templates — Open** | Opens the templates that associate dropped files with check-in contexts. |
