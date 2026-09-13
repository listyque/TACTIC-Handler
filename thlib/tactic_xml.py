"""Small soup-compatible view over TACTIC XML definitions."""

from __future__ import annotations

from html.parser import HTMLParser
import re
from xml.etree import ElementTree


class TacticXmlNode:
    def __init__(self, element: ElementTree.Element):
        self._element = element

    def __bool__(self) -> bool:
        return True

    def __getitem__(self, name: str) -> str:
        return self._element.attrib[name]

    def __contains__(self, name: str) -> bool:
        return name in self._element.attrib

    @property
    def name(self) -> str:
        return self._element.tag

    @property
    def attrs(self) -> dict[str, str]:
        return self._element.attrib

    @property
    def text(self) -> str:
        return "".join(self._element.itertext())

    @property
    def string(self) -> str | None:
        children = list(self._element)
        if not children:
            return self._element.text
        if (
            len(children) == 1
            and not (self._element.text or "").strip()
            and not (children[0].tail or "").strip()
        ):
            return TacticXmlNode(children[0]).string
        return None

    def get(self, name: str, default=None):
        value = self._element.get(name)
        if value is None:
            return default
        return value.split() if name == "class" else value

    def get_text(self, strip: bool = False) -> str:
        value = self.text
        return " ".join(value.split()) if strip else value

    def find(self, name: str | None = None, **kwargs):
        name = kwargs.get("name", name)
        for element in self._element.iter():
            if element is not self._element and (name is None or element.tag == name):
                return TacticXmlNode(element)
        return None

    def find_all(self, name: str | None = None, **kwargs) -> list["TacticXmlNode"]:
        name = kwargs.get("name", name)
        return [
            TacticXmlNode(element)
            for element in self._element.iter()
            if element is not self._element and (name is None or element.tag == name)
        ]

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return self.find(name)


class _ForgivingXmlParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = ElementTree.Element("tactic_document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        element = ElementTree.SubElement(self.stack[-1], tag, dict(attrs))
        self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        ElementTree.SubElement(self.stack[-1], tag, dict(attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        current = self.stack[-1]
        if len(current):
            current[-1].tail = (current[-1].tail or "") + data
        else:
            current.text = (current.text or "") + data


def parse_tactic_xml(value, _parser: str | None = None) -> TacticXmlNode:
    """Parse XML and tolerate malformed fragments emitted by legacy TACTIC."""
    text = str(value or "")
    document = ElementTree.Element("tactic_document")
    try:
        cleaned = re.sub(r"^\s*<\?xml[^>]*\?>", "", text, count=1)
        document.append(ElementTree.fromstring(cleaned))
    except ElementTree.ParseError:
        parser = _ForgivingXmlParser()
        parser.feed(text)
        parser.close()
        document = parser.root
    return TacticXmlNode(document)
