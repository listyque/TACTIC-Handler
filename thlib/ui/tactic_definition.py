"""Lossless XML helpers for TACTIC table and EditSObject definitions."""

from copy import deepcopy
from xml.etree import ElementTree


INPUT_ALIASES = {
    "TextWdg": "pyasm.widget.input_wdg.TextWdg",
    "TextAreaWdg": "pyasm.widget.input_wdg.TextAreaWdg",
    "SelectWdg": "pyasm.widget.input_wdg.SelectWdg",
    "CheckboxWdg": "pyasm.widget.input_wdg.CheckboxWdg",
    "CalendarInputWdg": "tactic.ui.widget.calendar_wdg.CalendarInputWdg",
    "PasswordWdg": "pyasm.widget.input_wdg.PasswordWdg",
    "ThumbInputWdg": "pyasm.widget.input_wdg.ThumbInputWdg",
    "text": "pyasm.widget.input_wdg.TextWdg",
    "textarea": "pyasm.widget.input_wdg.TextAreaWdg",
    "select": "pyasm.widget.input_wdg.SelectWdg",
    "checkbox": "pyasm.widget.input_wdg.CheckboxWdg",
    "calendar": "tactic.ui.widget.calendar_wdg.CalendarInputWdg",
    "password": "pyasm.widget.input_wdg.PasswordWdg",
    "thumb": "pyasm.widget.input_wdg.ThumbInputWdg",
}

INPUT_LABELS = {
    "SimpleUploadWdg": "Upload",
    "TextWdg": "Single-line text",
    "TextAreaWdg": "Multi-line text",
    "SelectWdg": "Select",
    "CheckboxWdg": "Checkbox",
    "CurrentCheckboxWdg": "Current user checkbox",
    "TaskSObjectInputWdg": "Task object",
    "CalendarInputWdg": "Date and time",
    "ProcessGroupSelectWdg": "User",
    "ProjectSelectWdg": "Project",
    "ProcessInputWdg": "Process",
    "SubContextInputWdg": "Subcontext",
    "TaskStatusSelectWdg": "Task status",
    "PipelineInputWdg": "Pipeline",
    "ThumbInputWdg": "Thumbnail",
    "PasswordWdg": "Password",
}

DISPLAY_WIDGETS = (
    ("", "Automatic"),
    ("format", "Format"),
    ("expression", "Expression"),
    ("link", "Link"),
    ("pyasm.widget.ThumbWdg", "Thumbnail"),
    ("tactic.ui.widget.DiscussionElementWdg", "Notes"),
    ("tactic.ui.table.SObjectDetailElementWdg", "SObject details"),
    ("tactic.ui.table.CheckinButtonElementWdg", "Check-in"),
    ("tactic.ui.table.TaskElementWdg", "Tasks"),
    ("tactic.ui.table.TaskCompletionWdg", "Task completion"),
    ("tactic.ui.table.ExploreElementWdg", "Explorer"),
    ("tactic.ui.table.SObjectFilesElementWdg", "Files"),
    ("tactic.ui.table.MetadataElementWdg", "Metadata"),
    ("tactic.ui.table.DeleteElementWdg", "Delete"),
)


def width(value) -> int:
    try:
        return max(48, min(640, int(value or 160)))
    except (TypeError, ValueError):
        return 160


def flag(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def input_widget(value) -> str:
    value = str(value or "").strip()
    return INPUT_ALIASES.get(value, value)


def edit_source(item: dict) -> dict | None:
    """Build the input payload used for inherited EditWdg defaults."""
    class_name = input_widget(item.get("editClass"))
    if not class_name:
        class_name = input_widget(item.get("editWidget"))
    if not class_name:
        return None
    options = dict(item.get("editOptions") or {})
    return {**options, "class_name": class_name, "kwargs": options}


def set_widget(
    display: ElementTree.Element, widget, *, is_input: bool = False
) -> None:
    display.attrib.pop("widget", None)
    display.attrib.pop("class", None)
    widget = str(widget or "").strip()
    if not widget:
        return
    attribute = (
        "class" if is_input or "." in widget or widget.endswith("Wdg")
        else "widget"
    )
    display.set(attribute, widget)


def set_option(
    display: ElementTree.Element,
    name: str,
    value,
    *,
    keep_empty: bool = False,
) -> None:
    node = display.find(name)
    text = str(value or "").strip()
    if not text and not keep_empty:
        if node is not None:
            display.remove(node)
        return
    if node is None:
        node = ElementTree.SubElement(display, name)
    node.text = text


def element_form(
    element: ElementTree.Element,
    record: dict,
    edit_source: dict,
    target: str,
) -> dict:
    display = element.find("display")
    effective = {}
    if target == "edit_definition":
        effective.update(dict(edit_source.get("kwargs") or {}))
        effective.update(edit_source)
        effective.update(record["editOptions"])
    else:
        effective.update(record["displayOptions"])

    def option(name, default=""):
        node = display.find(name) if display is not None else None
        if node is not None and node.text is not None:
            return node.text
        return effective.get(name, default)

    widget = ""
    if display is not None:
        widget = display.get("class") or display.get("widget") or ""
    if not widget:
        if target == "edit_definition":
            widget = (
                edit_source.get("class_name")
                or record["editClass"] or record["editWidget"]
            )
        else:
            widget = record["widgetClass"] or record["widgetKey"]
    if target == "edit_definition":
        widget = input_widget(widget)

    def option_text(value):
        if isinstance(value, (list, tuple)):
            return "|".join(str(item) for item in value)
        return "" if value is None else str(value)

    return {
        "name": record["name"],
        "title": str(element.get("title") or record["label"]),
        "width": width(element.get("width") or record["displayWidth"]),
        "widget": str(widget or ""),
        "included": bool(record["editVisible"]),
        "required": flag(option("required")),
        "readOnly": flag(option("read_only", option("readonly"))),
        "empty": flag(option("empty")),
        "description": option_text(option("description")),
        "defaultValue": option_text(option("default")),
        "values": option_text(option("values")),
        "labels": option_text(option("labels")),
    }


def update_element(
    element: ElementTree.Element, target: str, form: dict
) -> ElementTree.Element:
    if target != "edit_definition":
        title = str(form.get("title") or "").strip()
        if not title:
            raise ValueError("Column label cannot be empty.")
        element.set("title", title)
        element.set("width", str(width(form.get("width"))))
    display = element.find("display")
    if display is None:
        display = ElementTree.SubElement(element, "display")
    widget = form.get("widget")
    if target == "edit_definition":
        widget = input_widget(widget)
    set_widget(display, widget, is_input=target == "edit_definition")
    if target != "edit_definition":
        return element
    set_option(
        display, "required", "true" if flag(form.get("required")) else "false",
        keep_empty=True,
    )
    set_option(
        display, "read_only", "true" if flag(form.get("readOnly")) else "false",
        keep_empty=True,
    )
    if str(widget or "").endswith("SelectWdg"):
        set_option(
            display, "empty", "true" if flag(form.get("empty")) else "false",
            keep_empty=True,
        )
    for option_name, form_name in (
        ("description", "description"),
        ("default", "defaultValue"),
        ("values", "values"),
        ("labels", "labels"),
    ):
        set_option(display, option_name, form.get(form_name))
    return element


def edit_view_xml(
    source: str,
    records: list[dict],
    element_name: str,
    included: bool,
) -> str:
    root = (
        ElementTree.fromstring(source)
        if str(source or "").strip() else ElementTree.Element("config")
    )
    edit = root if root.tag == "edit" else root.find(".//edit")
    if edit is None:
        edit = ElementTree.SubElement(root, "edit")
    elements = list(edit.findall("element"))
    if not source or not elements:
        for record in records:
            if record["editVisible"]:
                ElementTree.SubElement(
                    edit, "element", {"name": record["name"]}
                )
        elements = list(edit.findall("element"))
    matching = [
        element for element in elements if element.get("name") == element_name
    ]
    if included and not matching:
        ElementTree.SubElement(edit, "element", {"name": element_name})
    elif not included:
        for element in matching:
            edit.remove(element)
    return ElementTree.tostring(root, encoding="unicode")


def definition_element(
    database_views: dict, record: dict, target: str
) -> ElementTree.Element:
    view_xml = str(dict(database_views.get(target) or {}).get("config") or "")
    if view_xml:
        root = ElementTree.fromstring(view_xml)
        view_node = root if root.tag == target else root.find(f".//{target}")
        if view_node is not None:
            for node in view_node.findall("element"):
                if node.get("name") == record["name"]:
                    return deepcopy(node)
    source = (
        record["editXml"]
        if target == "edit_definition" else record["displayXml"]
    )
    if source:
        node = ElementTree.fromstring(source)
        if node.tag == "element":
            return node
    return ElementTree.Element("element", {"name": record["name"]})
