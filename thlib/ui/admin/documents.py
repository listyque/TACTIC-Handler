"""Lossless native XML editing: graph identities and access-rule attributes."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET


def parse_xml(text: str, root_tag: str) -> ET.Element:
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('Document types and XML entities are not supported')
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
    root = ET.fromstring(text, parser=parser)
    if root.tag != root_tag:
        raise ValueError('Expected <%s> as the document root' % root_tag)
    return root


class GraphDocument:
    """Edit only known nodes/edges; preserve other XML, attributes and ordering."""

    def __init__(self, mode: str, xml: str) -> None:
        self.mode = mode
        self.tag = 'search_type' if mode == 'schema' else 'process'
        self.root = parse_xml(xml, 'schema' if mode == 'schema' else 'pipeline')
        self.validate()

    def validate(self) -> None:
        names = set()
        for node in self.root.findall(self.tag):
            name = node.get('name', '').strip()
            if not name or name in names:
                raise ValueError('Node names must be non-empty and unique')
            names.add(name)
            for axis in ('xpos', 'ypos'):
                if not math.isfinite(float(node.get(axis, '0'))):
                    raise ValueError('Node positions must be finite')
        for edge in self.root.findall('connect'):
            if not edge.get('from') or not edge.get('to'):
                raise ValueError('Every connection must name its source and destination')

    def xml(self) -> str:
        return ET.tostring(self.root, encoding='unicode')

    def nodes(self) -> list[dict]:
        result = []
        for index, node in enumerate(self.root.findall(self.tag)):
            result.append({'identity': node.get('name'), 'attributes': dict(node.attrib),
                           'nodeX': float(node.get('xpos', str(40 + index % 3 * 240))),
                           'nodeY': float(node.get('ypos', str(40 + index // 3 * 130))),
                           'kind': node.get('type') or self.tag,
                           'color': node.get('color') or '', 'referenceOnly': False})
        # Existing documents may contain dangling links. Keep them inspectable
        # and repairable without silently creating processes or dropping XML.
        names = {row['identity'] for row in result}
        for edge in self.root.findall('connect'):
            for key in ('from', 'to'):
                name = edge.get(key)
                if name not in names:
                    index = len(result)
                    result.append({'identity': name, 'attributes': {'name': name},
                                   'nodeX': 40 + index % 3 * 240, 'nodeY': 40 + index // 3 * 130,
                                   'kind': 'reference' if self.mode == 'schema' else 'missing',
                                   'color': '', 'referenceOnly': True})
                    names.add(name)
        return result

    def edges(self) -> list[dict]:
        return [dict(edge.attrib, edgeIndex=index)
                for index, edge in enumerate(self.root.findall('connect'))]

    def node(self, name: str) -> ET.Element:
        node = next((node for node in self.root.findall(self.tag)
                     if node.get('name') == name), None)
        if node is None:
            raise ValueError('The selected node no longer exists')
        return node

    def add_node(self, name: str, kind: str = '') -> None:
        name = name.strip()
        if not name or any(node.get('name') == name for node in self.root.findall(self.tag)):
            raise ValueError('Enter a unique node name')
        index = len(self.nodes())
        attrs = {'name': name, 'xpos': str(40 + index % 3 * 240),
                 'ypos': str(40 + index // 3 * 130)}
        if kind:
            attrs['type'] = kind
        ET.SubElement(self.root, self.tag, attrs)

    def connect(self, source: str, target: str) -> None:
        self.node(source)
        self.node(target)
        if source == target:
            raise ValueError('Choose two different nodes')
        if any(edge.get('from') == source and edge.get('to') == target for edge in self.edges()):
            raise ValueError('This connection already exists')
        attrs = {'from': source, 'to': target}
        if self.mode == 'schema':
            attrs.update(relationship='code', type='hierarchy')
        ET.SubElement(self.root, 'connect', attrs)

    def remove_node(self, name: str) -> None:
        self.root.remove(self.node(name))
        for edge in list(self.root.findall('connect')):
            if name in (edge.get('from'), edge.get('to')):
                self.root.remove(edge)

    def remove_edge(self, index: int) -> None:
        edges = self.root.findall('connect')
        if not 0 <= index < len(edges):
            raise ValueError('Select a connection')
        self.root.remove(edges[index])

    def set_attributes(self, name: str, attributes: dict[str, str]) -> None:
        node = self.node(name)
        replacement = attributes.get('name', name).strip()
        if replacement != name:
            if any(row['identity'] == replacement for row in self.nodes()) or not replacement:
                raise ValueError('Enter a unique node name')
            for edge in self.root.findall('connect'):
                for key in ('from', 'to'):
                    if edge.get(key) == name:
                        edge.set(key, replacement)
        node.attrib.clear()
        node.attrib.update(attributes)


class RulesDocument:
    def __init__(self, xml: str) -> None:
        self.root = parse_xml(xml, 'rules')

    def xml(self) -> str:
        return ET.tostring(self.root, encoding='unicode')

    def records(self) -> list[dict]:
        return [dict(rule.attrib, ruleIndex=index)
                for index, rule in enumerate(self.root.findall('rule'))]

    def set_rule(self, index: int, attributes: dict[str, str]) -> None:
        if not (attributes.get('group') or attributes.get('category')):
            raise ValueError('Enter a security scope')
        scope = attributes.get('group') or attributes.get('category')
        if not (scope == 'search_filter' and 'access' not in attributes) and attributes.get('access') not in {
                'deny', 'allow', 'view', 'edit', 'insert', 'retire', 'delete', 'true', 'false'}:
            raise ValueError('Select a valid access level')
        rules = self.root.findall('rule')
        if index == -1:
            rule = ET.SubElement(self.root, 'rule')
        elif 0 <= index < len(rules):
            rule = rules[index]
        else:
            raise ValueError('Select an access rule')
        rule.attrib.clear()
        rule.attrib.update(attributes)

    def remove(self, index: int) -> None:
        rules = self.root.findall('rule')
        if not 0 <= index < len(rules):
            raise ValueError('Select an access rule')
        self.root.remove(rules[index])
