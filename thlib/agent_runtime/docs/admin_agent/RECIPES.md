# TS project configuration recipes

Use these as decision patterns, not as permission to write. The Python example
is a host executor using Stream HTTP/RPC, not a Handler Script Editor example.
It creates two new projects and exports a package. Run it only in an authorized
test installation with unused project codes. There is no whole-recipe rollback.
See [template commands](../../src/tactic/command/project_template_cmd.py) and
[package examples and evidence](SOURCES.md#projects-templates-and-executable-evidence)
for the underlying formats and additional cases.

## From a description to a complete configuration

Example request: "Create a reusable review project. Review Items need an integer
priority, a review table, work/review stages and predictable EXR names. Add one
example item and prove that the configuration can be reused in another project."

Interpretation:

- A project/type definition, not a new application component.
- The custom `priority` field belongs to Review Item; work records remain native
  tasks attached to those items.
- Work/review are processes, not invented task status values.
- `agent_review` is a named table. This example does not change navigation or
  the default view; include those operations when the requested outcome does.
- The template carries configuration; the example business row is not implicitly
  part of the export. The second project's table is expected to start empty.

The host provides `auth` for an administrator, `rpc(method, args, kwargs=None)`
and `post(path, payload)`. Both helpers return the unwrapped HTTP `result` and
raise on server errors. They use the same selected server and private ticket.
`auth` never goes to the model provider. The literals below identify new test
projects; inspect the catalogue before running them.

```python
from xml.etree import ElementTree as ET

source_project = "agent_review_template"
copy_project = "agent_review_copy"
admin_auth = dict(auth, project="admin")

def command(context, name, **arguments):
    return rpc("execute_cmd", [context, name, arguments])["info"]

types_cmd = "tactic.ui.panel.search_types_cmd.SearchTypesCmd"
workflow_cmd = "tactic.ui.panel.workflow_cmd.WorkflowCmd"
naming_cmd = "tactic.ui.panel.naming_cmd.NamingCmd"
creator = "tactic.command.CreateProjectCmd"
installer = "tactic.command.ProjectTemplateInstallerCmd"

projects = post("/admin/project-catalog", {
    "ticket": admin_auth["ticket"], "project": "admin"
})
assert not {source_project, copy_project} & {p["code"] for p in projects}
command(admin_auth, creator, project_code=source_project,
        project_title="Review template", project_type=source_project,
        is_template=True)
context = dict(auth, project=source_project)
created = command(context, types_cmd, action="save", project_code=source_project,
                  document={"title": "Review Item", "hasPipeline": True,
                            "columns": [{"name": "priority", "type": "integer"}]})
search_type = created["identity"]
pipeline_code = created["metadata"]["pipelines"][0]["identity"]
flow = command(context, workflow_cmd, action="load",
               project_code=source_project, identity=pipeline_code)
assert not ET.fromstring(flow["document"]["xml"]).findall("process")
flow["document"].update(
    name="Review workflow",
    xml='<pipeline><process name="work" type="manual"/>'
        '<process name="review" type="manual"/>'
        '<connect from="work" to="review"/></pipeline>',
    processSettings={}, processDescriptions={})
command(context, workflow_cmd, action="save", project_code=source_project,
        identity=pipeline_code, document=flow["document"],
        expected_revision=flow["revision"])

target = {"ticket": context["ticket"], "project": source_project,
          "search_type": search_type, "view": "agent_review"}
baseline = post("/admin/widget-configuration/read", target)
assert not baseline["sources"]
xml = '<config><agent_review><element name="code"/><element name="name"/>' \
      '<element name="priority"/></agent_review></config>'
draft = dict(target, source_id=None, xml=xml, revision=baseline["revision"])
assert post("/admin/widget-configuration/check", draft)["valid"]
preview = post("/admin/widget-configuration/preview", draft)
assert all(e["cell"]["supported"] for e in preview["interface"]["table"]["elements"])
post("/admin/widget-configuration/save", draft)

item = rpc("insert", [context, search_type,
           {"code": "REV001", "name": "Vehicle", "priority": 2,
            "pipeline_code": pipeline_code}])
tasks = rpc("add_initial_tasks", [context, item["__search_key__"]])
assert {t["process"] for t in tasks} == {"work", "review"}
rule = {"search_type": search_type, "context": "review/*",
        "dir_naming": "{project.code}/{sobject.code}",
        "file_naming": "{sobject.code}_v{version}.{ext}", "checkin_type": "strict"}
naming = command(context, naming_cmd, action="load",
                 project_code=source_project, search_type=search_type)
sample = {"key": item["__search_key__"], "file": "image.exr", "version": 1,
          "process": "review", "context": "review/main",
          "fileType": "main", "snapshotType": "file"}
paths = command(context, naming_cmd, action="preview", project_code=source_project,
                search_type=search_type, document=rule, sample=sample,
                allow_execution=False)
assert paths["results"][0]["file"] == "REV001_v001.exr"
command(context, naming_cmd, action="save", project_code=source_project,
        search_type=search_type, document=rule, expected_revision=naming["revision"])

command(admin_auth, "tactic.command.ProjectTemplateCreatorCmd",
        project_code=source_project)
available = post("/admin/project-creation", {
    "ticket": admin_auth["ticket"], "project": "admin"})
package = next(p for p in available["installedTemplates"]
               if p["code"] == source_project)
command(admin_auth, installer, project_code=copy_project,
        project_title="Review copy", template_code=source_project,
        path=package["path"], new_project=True, is_template=False)
copied_context = dict(auth, project=copy_project)
copied_type = command(copied_context, types_cmd, action="load",
                      project_code=copy_project, identity=search_type)
assert "priority" in copied_type["metadata"]["columns"]
assert rpc("query", [copied_context, search_type], {"limit": 1}) == []
copied_view = post("/admin/widget-configuration/read", dict(target, project=copy_project))
assert any('name="priority"' in s["xml"] for s in copied_view["sources"])
assert copied_type["metadata"]["pipelines"]
copied_pipeline = copied_type["metadata"]["pipelines"][0]["identity"]
assert copied_pipeline != pipeline_code
copied_flow = command(copied_context, workflow_cmd, action="load",
                      project_code=copy_project, identity=copied_pipeline)
copied_nodes = ET.fromstring(copied_flow["document"]["xml"]).findall("process")
assert {p.get("name") for p in copied_nodes} == {"work", "review"}
copied_naming = command(copied_context, naming_cmd, action="load",
                        project_code=copy_project, search_type=search_type)
assert any(r["document"]["context"] == "review/*" for r in copied_naming["rules"])
```

Expected evidence: one configured template project, one separate installed
project, a shared base SearchType namespace with separate row data, a copied
integer field and view, remapped project pipeline, copied naming and two tasks
on the original demo item. API checks do not prove visual rendering in both
clients. Open the named view, inspect/edit a row and task parent, and inspect
the forms before claiming full UI acceptance. No EXR is uploaded by this recipe.
The installer consumes the exported directory discovered in the catalogue;
this example does not test transferring or extracting the ZIP on another host.

The Python block was executed unchanged through real HTTP against temporary
SQLite data on 2026-10-24, including all assertions and the second installation.
That check does not cover PostgreSQL or rendered desktop/browser interaction.

## Modify an existing project

Read the target type, relation metadata, view sources and relevant forms. For
"add priority to shots", first check whether the field exists and what type it
has. Add it once through SearchTypesCmd, using the loaded document and revision.
Then modify the actual table and relevant edit/insert views, preserving other
elements. Validate/preview and save each view against its own source/revision.
Read back both stored field values and rendered cell descriptions. A field that
exists only in the database does not finish a request to expose it in the UI.

For "show a sequence's shots", inspect the real schema relationship, configured
parent scope and nested `search_view`/`edit_view`/`insert_view`. Keep the parent
filter even when adding another search condition. Test two different parents,
an empty parent and related-object creation; otherwise a plausible child table
may be showing unrelated records.

## Extend a supplied template

Read `/admin/project-creation` and select the actual returned template reference.
Instantiate it into the requested project; inspect its effective type catalogue,
views and pipelines. Preserve the original namespace and default layout unless
the native installer or the requested change says otherwise. Check each added
field/widget against actual support. An unsupported Maya/applet action is an
explicit excluded capability, not grounds to rewrite the remaining template.

## Stop at the right boundary

If asked for an unfamiliar widget or custom plugin, obtain its authorized
configuration and input/output contract. A known class path is insufficient.
If the needed behavior requires missing implementation, explain that gap and
return the relevant proposed configuration separately from implementation work.
Do not silently replace it with another widget or claim a successful migration.

If asked for automation, establish its event, inputs, outputs, side effects and
execution context. Drafting a script does not authorize running or binding it.
Current editor execution is ordinary server execution; isolated test/activation
tools must actually exist before describing such a test as sandboxed.
