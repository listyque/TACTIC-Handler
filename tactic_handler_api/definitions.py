"""Edit exact widget-config records; never overwrite a merged definition."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import xml.etree.ElementTree as ET

from .errors import NotFound


def _parse(xml: str):
    if not isinstance(xml, str) or not xml.strip():
        raise ValueError("Definition XML is required")
    return ET.fromstring(
        xml, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    )


@dataclass(frozen=True)
class ResolvedDefinition:
    search_type: str
    view: str
    xml: str


class DefinitionCatalog:
    def __init__(self, api, project_code: str, search_type: str | None = None):
        self._api = api
        self.project_code = project_code
        self.search_type = search_type

    def list(self, *, search_type=None, view=None, login=None, limit=100, offset=0):
        self._api._check()
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("Expected 1 <= limit <= 1000 and offset >= 0")
        filters = [
            (name, value)
            for name, value in (
                ("search_type", search_type or self.search_type),
                ("view", view),
                ("login", login),
            )
            if value is not None
        ]
        server = self._api._core.server_start(project=self.project_code)
        records = server.query(
            "config/widget_config",
            filters=filters,
            order_bys=["code"],
            limit=limit,
            offset=offset,
        )
        return [Definition(self, record) for record in records]

    def get(self, config_code: str):
        self._api._check()
        server = self._api._core.server_start(project=self.project_code)
        records = server.query(
            "config/widget_config", filters=[("code", config_code)], limit=2
        )
        if len(records) != 1:
            raise NotFound(f"Definition {config_code!r} is unavailable or ambiguous")
        if self.search_type and records[0].get("search_type") != self.search_type:
            raise ValueError("The definition belongs to another Search Type")
        return Definition(self, records[0])

    def new(self, view: str, xml: str, *, search_type=None, login=""):
        search_type = search_type or self.search_type
        if not search_type or not view:
            raise ValueError("Search Type and view are required")
        return Definition(
            self,
            {"search_type": search_type, "view": view, "login": login, "config": xml},
        )

    def resolve(self, view: str, *, search_type=None):
        self._api._check()
        search_type = search_type or self.search_type
        if not search_type:
            raise ValueError("Search Type is required")
        project = self._api.project(self.project_code)
        project.stypes()
        xml = project._native.get_config_views().get_view(
            search_type,
            view=view,
            processed=False,
        )
        if not xml:
            raise NotFound(f"Definition {search_type}:{view} is unavailable")
        return ResolvedDefinition(search_type, view, xml)


class Definition:
    def __init__(self, catalog, record):
        self._catalog = catalog
        self._record = deepcopy(record)
        self._xml = record.get("config") or "<config/>"
        _parse(self._xml)

    @property
    def code(self):
        return self._record.get("code")

    @property
    def search_type(self):
        return self._record["search_type"]

    @property
    def view(self):
        return self._record["view"]

    @property
    def login(self):
        return self._record.get("login") or ""

    @property
    def xml(self):
        return self._xml

    def set_xml(self, xml: str) -> None:
        _parse(xml)
        self._xml = xml

    def validate(self) -> None:
        root = _parse(self.xml)
        # Names are unique within a view, not across separate table/edit views.
        views = list(root) if root.tag == "config" else [root]
        for view in views:
            names = [node.get("name") for node in view.findall("element")]
            if any(not name for name in names) or len(set(names)) != len(names):
                raise ValueError(
                    "Definition elements need unique nonempty names per view"
                )

    def element(self, name: str):
        root = _parse(self.xml)
        matches = [
            element for element in root.iter("element") if element.get("name") == name
        ]
        if len(matches) != 1:
            raise NotFound(
                f"Element {name!r} is unavailable or ambiguous; edit XML explicitly"
            )
        return DefinitionElement(self, name)

    def commit(self):
        self._catalog._api._check()
        self.validate()
        server = self._catalog._api._core.server_start(
            project=self._catalog.project_code
        )
        key = self._record.get("__search_key__")
        if self.code:
            if not key:
                key = server.build_search_key(
                    "config/widget_config",
                    self.code,
                    project_code=self._catalog.project_code,
                )
            result = server.update(key, {"config": self.xml}, triggers=False)
        else:
            result = server.insert(
                "config/widget_config",
                {
                    "search_type": self.search_type,
                    "view": self.view,
                    "login": self.login,
                    "config": self.xml,
                },
                triggers=False,
            )
        if not isinstance(result, dict) or not result.get("code"):
            raise RuntimeError("TACTIC did not confirm the saved definition")
        self._record.update(result)
        self._catalog._api._invalidate(self._catalog.project_code, definitions=True)
        return self


class DefinitionElement:
    def __init__(self, definition, name):
        self._definition = definition
        self.name = name

    def _update(self, callback):
        root = _parse(self._definition.xml)
        matches = [
            node for node in root.iter("element") if node.get("name") == self.name
        ]
        if len(matches) != 1:
            raise NotFound(f"Element {self.name!r} no longer exists unambiguously")
        callback(matches[0])
        self._definition.set_xml(ET.tostring(root, encoding="unicode"))

    def set_attribute(self, name: str, value: str):
        if name == "name":
            raise ValueError("Rename elements explicitly in XML")
        self._update(lambda node: node.set(name, str(value)))

    def set_widget(self, section: str, class_name: str):
        def change(node):
            target = node.find(section)
            if target is None:
                target = ET.SubElement(node, section)
            target.set("class", class_name)

        if section not in ("display", "edit"):
            raise ValueError("Widget section must be display or edit")
        self._update(change)

    def set_option(self, section: str, name: str, value: str):
        if section not in ("display", "edit") or not name.isidentifier():
            raise ValueError("Expected a display/edit section and an option name")

        def change(node):
            target = node.find(section)
            if target is None:
                target = ET.SubElement(node, section)
            option = target.find(name)
            if option is None:
                option = ET.SubElement(target, name)
            option.text = str(value)

        self._update(change)
