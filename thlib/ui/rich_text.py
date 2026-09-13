"""Safe rich-text storage and link presentation for native Qt views."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import urlparse


LINK_PATTERN = re.compile(
    r"(?:skey|tactic-search|https?|ftp)://[^\s<>\"]+",
    re.IGNORECASE,
)

_TRAILING_PUNCTUATION = ".,;:!?)]}"
_HEADING_TAGS = {f"h{level}" for level in range(1, 7)}
_ALLOWED_TAGS = _HEADING_TAGS | {
    "a", "b", "blockquote", "br", "code", "div", "em", "hr", "i",
    "img", "li", "ol", "p", "pre", "s",
    "small", "span", "strike", "strong", "table", "tbody", "td", "th", "thead",
    "tr", "u", "ul",
}
_VOID_TAGS = {"br", "hr", "img"}
_DROPPED_CONTENT_TAGS = {"iframe", "object", "script", "style"}
_ALLOWED_SCHEMES = {
    "ftp", "http", "https", "skey", "tactic-search",
}
_ALLOWED_IMAGE_SCHEMES = {"http", "https"}
_SAFE_STYLE_PROPERTIES = {
    "background-color", "border-collapse", "color", "font-family", "font-size", "font-style",
    "font-weight", "margin-left", "max-width", "text-align", "text-decoration",
    "vertical-align", "white-space",
}


def _safe_url(value: str, *, image: bool = False) -> str:
    candidate = html.unescape(str(value or "")).strip()
    if not candidate or any(character in candidate for character in "\r\n\x00"):
        return ""
    parsed = urlparse(candidate)
    schemes = _ALLOWED_IMAGE_SCHEMES if image else _ALLOWED_SCHEMES
    if parsed.scheme.casefold() not in schemes:
        return ""
    return candidate


def _safe_style(value: str) -> str:
    declarations = []
    for declaration in str(value or "").split(";"):
        name, separator, raw_value = declaration.partition(":")
        name = name.strip().casefold()
        raw_value = raw_value.strip()
        if not separator or name not in _SAFE_STYLE_PROPERTIES or not raw_value:
            continue
        folded = raw_value.casefold()
        if any(token in folded for token in ("url(", "expression", "javascript:")):
            continue
        if name == "max-width" and folded != "100%":
            continue
        declarations.append(f"{name}: {raw_value}")
    return "; ".join(declarations)


def _linked_fragment(value: str) -> str:
    result = []
    offset = 0
    for match in LINK_PATTERN.finditer(str(value or "")):
        raw = match.group(0)
        target = raw.rstrip(_TRAILING_PUNCTUATION)
        suffix = raw[len(target):]
        if not target:
            continue
        result.append(html.escape(value[offset:match.start()]))
        escaped = html.escape(target, quote=True)
        result.append(f'<a href="{escaped}">{html.escape(target)}</a>')
        result.append(html.escape(suffix))
        offset = match.end()
    result.append(html.escape(value[offset:]))
    return "".join(result)


def linkify_plain_text(value: str) -> str:
    """Escape plain text and expose supported links to a Qt rich-text view."""
    return _linked_fragment(str(value or "")).replace("\n", "<br>")


def _numeric_dimension(value: object) -> float:
    match = re.fullmatch(
        r"\s*([0-9]+(?:\.[0-9]+)?)\s*(?:px)?\s*",
        str(value or ""),
        flags=re.IGNORECASE,
    )
    return float(match.group(1)) if match else 0.0


def _dimension_text(value: float) -> str:
    rounded = round(float(value), 2)
    return str(int(rounded)) if rounded.is_integer() else str(rounded)


def _image_uses_content_width(attributes) -> bool:
    for raw_name, raw_value in attributes:
        if str(raw_name or "").casefold() != "style":
            continue
        for declaration in str(raw_value or "").split(";"):
            name, separator, value = declaration.partition(":")
            if (
                separator
                and name.strip().casefold() == "max-width"
                and value.strip().casefold() == "100%"
            ):
                return True
    return False


class _RichTextSanitizer(HTMLParser):
    def __init__(
        self,
        *,
        linkify: bool,
        image_maximum_width: float = 0.0,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self._linkify = linkify
        self._image_maximum_width = max(0.0, float(image_maximum_width))
        self._parts: list[str] = []
        self._open_tags: list[str] = []
        self._drop_depth = 0
        self._anchor_depth = 0

    def _attributes(self, tag: str, attributes) -> str:
        attributes = list(attributes)
        dimension_overrides: dict[str, str] = {}
        if tag == "img" and self._image_maximum_width > 0.0:
            content_width = _image_uses_content_width(attributes)
            dimensions = {
                str(name or "").casefold(): _numeric_dimension(value)
                for name, value in attributes
                if str(name or "").casefold() in {"height", "width"}
            }
            width = dimensions.get("width", 0.0)
            height = dimensions.get("height", 0.0)
            if content_width and width > 0.0:
                scale = self._image_maximum_width / width
                dimension_overrides["width"] = _dimension_text(
                    self._image_maximum_width
                )
                if height > 0.0:
                    dimension_overrides["height"] = _dimension_text(
                        height * scale
                    )
            elif width > self._image_maximum_width:
                scale = self._image_maximum_width / width
                dimension_overrides["width"] = _dimension_text(
                    self._image_maximum_width
                )
                if height > 0.0:
                    dimension_overrides["height"] = _dimension_text(
                        height * scale
                    )
        result = []
        for raw_name, raw_value in attributes:
            name = str(raw_name or "").casefold()
            value = dimension_overrides.get(name, str(raw_value or ""))
            if name.startswith("on"):
                continue
            if name == "style":
                value = _safe_style(value)
                if not value:
                    continue
            elif tag == "a" and name == "href":
                value = _safe_url(value)
                if not value:
                    continue
            elif tag == "img" and name == "src":
                value = _safe_url(value, image=True)
                if not value:
                    continue
            elif (
                (tag == "ol" and name == "start")
                or (tag == "li" and name == "value")
            ):
                try:
                    value = str(int(value))
                except (TypeError, ValueError):
                    continue
            elif tag == "li" and name == "class":
                value = value.casefold()
                if value not in {"checked", "unchecked"}:
                    continue
            elif tag == "table" and name in {"border", "cellpadding"}:
                try:
                    value = str(max(0, min(24, int(float(value)))))
                except (TypeError, ValueError):
                    continue
            elif name not in {
                "align", "alt", "height", "href", "src", "style", "title",
                "width",
            }:
                continue
            if name in {"href", "src"} and (
                (tag != "a" or name != "href")
                and (tag != "img" or name != "src")
            ):
                continue
            result.append(
                f' {name}="{html.escape(value, quote=True)}"'
            )
        return "".join(result)

    def handle_starttag(self, tag: str, attributes) -> None:
        tag = tag.casefold()
        if tag in _DROPPED_CONTENT_TAGS:
            self._drop_depth += 1
            return
        if self._drop_depth or tag not in _ALLOWED_TAGS:
            return
        self._parts.append(f"<{tag}{self._attributes(tag, attributes)}>")
        if tag == "a":
            self._anchor_depth += 1
        if tag not in _VOID_TAGS:
            self._open_tags.append(tag)

    def handle_startendtag(self, tag: str, attributes) -> None:
        tag = tag.casefold()
        if not self._drop_depth and tag in _ALLOWED_TAGS:
            self._parts.append(
                f"<{tag}{self._attributes(tag, attributes)}>"
            )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in _DROPPED_CONTENT_TAGS:
            self._drop_depth = max(0, self._drop_depth - 1)
            return
        if self._drop_depth or tag not in self._open_tags:
            return
        while self._open_tags:
            current = self._open_tags.pop()
            self._parts.append(f"</{current}>")
            if current == "a":
                self._anchor_depth = max(0, self._anchor_depth - 1)
            if current == tag:
                break

    def handle_data(self, data: str) -> None:
        if self._drop_depth:
            return
        if self._linkify and not self._anchor_depth:
            self._parts.append(_linked_fragment(data))
        else:
            self._parts.append(html.escape(data))

    def result(self) -> str:
        while self._open_tags:
            self._parts.append(f"</{self._open_tags.pop()}>")
        return "".join(self._parts).strip()


def sanitize_rich_html(value: str, *, linkify: bool = True) -> str:
    """Keep Qt-supported formatting while removing executable markup."""
    parser = _RichTextSanitizer(linkify=linkify)
    parser.feed(str(value or ""))
    parser.close()
    return parser.result()


def fit_rich_html_images(
    value: str,
    maximum_width: float,
    *,
    linkify: bool = True,
) -> str:
    """Sanitize rich text and shrink only images wider than the viewport."""
    parser = _RichTextSanitizer(
        linkify=linkify,
        image_maximum_width=max(1.0, float(maximum_width or 1.0)),
    )
    parser.feed(str(value or ""))
    parser.close()
    return parser.result()


class _RichTextListParser(HTMLParser):
    """Flatten an HTML list into cheap independently wrapping item blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._lists: list[dict] = []
        self._items: list[dict] = []
        self.items: list[dict] = []

    @staticmethod
    def _integer_attribute(attributes, name: str, default: int) -> int:
        for raw_name, raw_value in attributes:
            if str(raw_name or "").casefold() != name:
                continue
            try:
                return int(raw_value)
            except (TypeError, ValueError):
                return default
        return default

    def handle_starttag(self, tag: str, attributes) -> None:
        tag = tag.casefold()
        if tag in {"ol", "ul"}:
            self._lists.append({
                "ordered": tag == "ol",
                "next": self._integer_attribute(attributes, "start", 1),
            })
            return
        if tag == "li" and self._lists:
            owner = self._lists[-1]
            number = self._integer_attribute(
                attributes, "value", int(owner["next"])
            )
            owner["next"] = number + 1
            item = {
                "kind": "list-item",
                "listOrdered": bool(owner["ordered"]),
                "listIndex": number,
                "listLevel": max(0, len(self._lists) - 1),
                "listCheckState": next((
                    1 if str(value or "").casefold() == "checked" else 0
                    for name, value in attributes
                    if str(name or "").casefold() == "class"
                    and str(value or "").casefold() in {"checked", "unchecked"}
                ), -1),
                "parts": [],
            }
            self.items.append(item)
            self._items.append(item)
            return
        if self._items:
            self._items[-1]["parts"].append(
                str(self.get_starttag_text() or f"<{tag}>")
            )

    def handle_startendtag(self, tag: str, attributes) -> None:
        if self._items:
            self._items[-1]["parts"].append(
                str(self.get_starttag_text() or f"<{tag}/>")
            )

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag == "li" and self._items:
            item = self._items.pop()
            fragment = sanitize_rich_html(
                "".join(item.pop("parts", [])), linkify=False
            )
            item["html"] = fragment
            item["plainText"] = plain_text_from_html(fragment).strip()
            item["lightweight"] = not bool(re.search(
                r"<\s*[a-zA-Z][^>]*>", fragment
            ))
            return
        if tag in {"ol", "ul"}:
            if self._lists:
                self._lists.pop()
            return
        if self._items:
            self._items[-1]["parts"].append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._items:
            self._items[-1]["parts"].append(data)

    def handle_entityref(self, name: str) -> None:
        if self._items:
            self._items[-1]["parts"].append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._items:
            self._items[-1]["parts"].append(f"&#{name};")

    def finish(self) -> list[dict]:
        while self._items:
            self.handle_endtag("li")
        return [
            dict(item)
            for item in self.items
            if item.get("plainText") or item.get("html")
        ]


def _rich_text_list_items(value: str) -> list[dict]:
    parser = _RichTextListParser()
    parser.feed(value)
    parser.close()
    return parser.finish()


class _RichTextBlockParser(HTMLParser):
    """Split safe article markup into text and native image blocks."""

    _SPLIT_TAGS = _HEADING_TAGS | {
        "blockquote", "div", "hr", "ol",
        "p", "pre", "table", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._parts: list[str] = []
        self._open_tags: list[tuple[str, str]] = []
        self.blocks: list[dict] = []

    def _flush_text(self) -> None:
        if not self._parts:
            return
        closing = [
            f"</{tag}>" for tag, _start in reversed(self._open_tags)
        ]
        value = sanitize_rich_html(
            "".join(self._parts + closing), linkify=False
        )
        self._parts = []
        if value and (
            plain_text_from_html(value)
            or any(marker in value for marker in ("<hr", "<table", "<br"))
        ):
            if re.match(r"^\s*<(?:ol|ul)(?:\s[^>]*)?>", value, re.I):
                list_items = _rich_text_list_items(value)
                if list_items:
                    self.blocks.extend(list_items)
                    return
            plain_text = plain_text_from_html(value)
            heading_match = re.match(r"^\s*<h([1-6])(?:\s[^>]*)?>", value)
            outer_match = re.match(
                r"^\s*<(p|div|h[1-6])(?:\s[^>]*)?>(.*)</\1>\s*$",
                value,
                flags=re.DOTALL | re.IGNORECASE,
            )
            inner = outer_match.group(2) if outer_match else value
            if heading_match:
                # QTextDocument serializes the heading's own size and weight
                # into one redundant span.  QML applies those semantics from
                # headingLevel, so this span must not force a rich-text layout.
                inner = re.sub(
                    r"<span\s+style=\"\s*(?:(?:font-size|font-weight)"
                    r"\s*:[^;\"]+;?\s*)+\">|</span>",
                    "",
                    inner,
                    flags=re.IGNORECASE,
                )
            lightweight = bool(outer_match) and not re.search(
                r"<\s*[a-zA-Z][^>]*>", inner
            )
            alignment_match = re.search(
                r"(?:align=\"(left|center|right|justify)\"|"
                r"text-align\s*:\s*(left|center|right|justify))",
                outer_match.group(0) if outer_match else "",
                flags=re.IGNORECASE,
            )
            self.blocks.append({
                "kind": "html",
                "html": value,
                "plainText": plain_text,
                "lightweight": lightweight,
                "headingLevel": (
                    int(heading_match.group(1)) if heading_match else 0
                ),
                "alignment": (
                    next((
                        part.casefold()
                        for part in alignment_match.groups()
                        if part
                    ), "left")
                    if alignment_match else "left"
                ),
            })

    def _append_image(self, attributes) -> None:
        attributes = list(attributes)
        values = {
            str(name or "").casefold(): str(value or "")
            for name, value in attributes
        }
        source = _safe_url(values.get("src", ""), image=True)
        if not source:
            return
        self._flush_text()
        self.blocks.append({
            "kind": "image",
            "source": source,
            "width": _numeric_dimension(values.get("width")),
            "height": _numeric_dimension(values.get("height")),
            "contentWidth": _image_uses_content_width(attributes),
            "title": values.get("title", ""),
            "alt": values.get("alt", ""),
        })
        self._parts = [start for _tag, start in self._open_tags]

    def handle_starttag(self, tag: str, attributes) -> None:
        tag = tag.casefold()
        if tag == "img":
            self._append_image(attributes)
            return
        if tag in self._SPLIT_TAGS and not self._open_tags and self._parts:
            self._flush_text()
        start = str(self.get_starttag_text() or f"<{tag}>")
        self._parts.append(start)
        if tag not in _VOID_TAGS:
            self._open_tags.append((tag, start))
        elif tag in self._SPLIT_TAGS and not self._open_tags:
            self._flush_text()

    def handle_startendtag(self, tag: str, attributes) -> None:
        if tag.casefold() == "img":
            self._append_image(attributes)
        else:
            self._parts.append(str(self.get_starttag_text() or ""))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        self._parts.append(f"</{tag}>")
        for index in range(len(self._open_tags) - 1, -1, -1):
            if self._open_tags[index][0] == tag:
                del self._open_tags[index:]
                break
        if tag in self._SPLIT_TAGS and not self._open_tags:
            self._flush_text()

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._parts.append(f"&#{name};")

    def finish(self) -> list[dict]:
        self._flush_text()
        return [dict(block) for block in self.blocks]


def rich_text_blocks(
    value: str,
    maximum_width: float | None = None,
) -> list[dict]:
    """Return safe ordered blocks for responsive native article rendering.

    Width-independent blocks preserve the stored image dimensions so a QML
    viewer can resize existing delegates without reparsing the article.  The
    explicit-width form remains available for non-QML presentation paths.
    """
    fitted = (
        fit_rich_html_images(value, maximum_width, linkify=True)
        if maximum_width is not None
        else sanitize_rich_html(value, linkify=True)
    )
    parser = _RichTextBlockParser()
    parser.feed(fitted)
    parser.close()
    return parser.finish()


class _PlainTextExtractor(HTMLParser):
    _BLOCK_TAGS = _HEADING_TAGS | {
        "blockquote", "br", "div", "li",
        "p", "pre", "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, _attributes) -> None:
        if tag.casefold() in self._BLOCK_TAGS and self.parts:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_text_from_html(value: str) -> str:
    parser = _PlainTextExtractor()
    parser.feed(str(value or ""))
    parser.close()
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line).strip()


class _HeadingExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._level = 0
        self._parts: list[str] = []
        self._occurrences: dict[str, int] = {}
        self.headings: list[dict] = []

    def handle_starttag(self, tag: str, _attributes) -> None:
        folded = tag.casefold()
        if folded in _HEADING_TAGS:
            self._level = int(folded[1])
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._level:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != f"h{self._level}" or not self._level:
            return
        title = " ".join("".join(self._parts).split())
        if title:
            occurrence = self._occurrences.get(title, 0)
            self.headings.append({
                "title": title,
                "level": self._level,
                "occurrence": occurrence,
            })
            self._occurrences[title] = occurrence + 1
        self._level = 0
        self._parts = []


def headings_from_html(value: str) -> list[dict]:
    """Return the semantic H1-H6 outline used by the native article view."""
    parser = _HeadingExtractor()
    parser.feed(str(value or ""))
    parser.close()
    return parser.headings


class _MarkdownTreeParser(HTMLParser):
    """Build the tiny safe tree needed to serialize editor HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = {"tag": "", "attrs": {}, "children": []}
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attributes) -> None:
        node = {
            "tag": tag.casefold(),
            "attrs": {
                str(name or "").casefold(): str(value or "")
                for name, value in attributes
            },
            "children": [],
        }
        self._stack[-1]["children"].append(node)
        if node["tag"] not in _VOID_TAGS:
            self._stack.append(node)

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index]["tag"] == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1]["children"].append(str(data or ""))


def _markdown_escape(value: str) -> str:
    return re.sub(r"([\\`*_[\]])", r"\\\1", str(value or ""))


def _markdown_style_flags(node: dict) -> tuple[bool, bool, bool, bool, bool]:
    tag = node["tag"]
    style = node["attrs"].get("style", "").casefold()
    weight = re.search(r"font-weight\s*:\s*([^;]+)", style)
    bold = tag in {"b", "strong"} or bool(
        weight and (
            weight.group(1).strip() in {"bold", "bolder"}
            or weight.group(1).strip().isdigit()
            and int(weight.group(1).strip()) >= 600
        )
    )
    italic = tag in {"em", "i"} or "font-style: italic" in style
    decoration = re.search(r"text-decoration\s*:\s*([^;]+)", style)
    decoration = decoration.group(1) if decoration else ""
    underline = tag == "u" or "underline" in decoration
    strike = tag in {"s", "strike"} or "line-through" in decoration
    code = tag == "code" or "font-family: 'monospace'" in style
    return bold, italic, underline, strike, code


def _markdown_inline(node, *, heading: bool = False, preformatted: bool = False) -> str:
    if isinstance(node, str):
        return node if preformatted else _markdown_escape(node)
    tag = node["tag"]
    if tag == "br":
        return "  \n"
    if tag == "img":
        source = _safe_url(node["attrs"].get("src", ""), image=True)
        if not source:
            return ""
        title = node["attrs"].get("title", "").replace('"', r'\"')
        alt = (node["attrs"].get("alt") or title or "Image").replace(
            "]", r"\]"
        )
        result = f"![{alt}]({source}"
        if title:
            result += f' "{title}"'
        result += ")"
        attributes = []
        for name in ("width", "height"):
            dimension = _numeric_dimension(node["attrs"].get(name))
            if dimension > 0:
                attributes.append(f"{name}={_dimension_text(dimension)}")
        if _image_uses_content_width(node["attrs"].items()):
            attributes.append("fit=content")
        return result + ("{" + " ".join(attributes) + "}" if attributes else "")
    content = "".join(
        _markdown_inline(
            child,
            heading=heading,
            preformatted=preformatted or tag == "pre",
        )
        for child in node["children"]
    )
    if tag == "a":
        target = _safe_url(node["attrs"].get("href", ""))
        return f"[{content}]({target})" if target else content
    bold, italic, underline, strike, code = _markdown_style_flags(node)
    style = node["attrs"].get("style", "").casefold()
    small = tag == "small" or bool(re.search(
        r"font-size\s*:\s*(?:small|9(?:\.0+)?pt)(?:\s*;|$)", style
    ))
    if code and not preformatted and content:
        fence = "``" if "`" in content else "`"
        content = f"{fence}{content}{fence}"
    if strike and content:
        content = f"~~{content}~~"
    if underline and content:
        content = f"<u>{content}</u>"
    if italic and content:
        content = f"*{content}*"
    if bold and content and not heading:
        content = f"**{content}**"
    if small and content:
        content = f"<small>{content}</small>"
    return content


def _markdown_alignment(node: dict) -> str:
    attributes = node["attrs"]
    value = attributes.get("align", "").casefold()
    if not value:
        match = re.search(
            r"text-align\s*:\s*(left|center|right|justify)",
            attributes.get("style", ""),
            flags=re.IGNORECASE,
        )
        value = match.group(1).casefold() if match else ""
    return value if value in {"center", "right", "justify"} else ""


def _markdown_table(node: dict) -> str:
    rows = []
    for row in node["children"]:
        if not isinstance(row, dict) or row["tag"] not in {"thead", "tbody", "tr"}:
            continue
        candidates = row["children"] if row["tag"] != "tr" else [row]
        for candidate in candidates:
            if not isinstance(candidate, dict) or candidate["tag"] != "tr":
                continue
            cells = [
                " ".join(_markdown_inline(cell).split()).replace("|", r"\|")
                for cell in candidate["children"]
                if isinstance(cell, dict) and cell["tag"] in {"td", "th"}
            ]
            if cells:
                rows.append(cells)
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    lines = ["| " + " | ".join(row) + " |" for row in rows]
    lines.insert(1, "| " + " | ".join("---" for _ in range(width)) + " |")
    return "\n".join(lines)


def _markdown_table_cells(node: dict) -> list[dict]:
    cells = []
    pending = list(node["children"])
    while pending:
        child = pending.pop(0)
        if not isinstance(child, dict):
            continue
        if child["tag"] in {"td", "th"}:
            cells.append(child)
        elif child["tag"] in {"tbody", "thead", "tr"}:
            pending[0:0] = child["children"]
    return cells


def _markdown_list(node: dict, level: int = 0) -> str:
    ordered = node["tag"] == "ol"
    try:
        number = int(node["attrs"].get("start") or 1)
    except ValueError:
        number = 1
    lines = []
    for child in node["children"]:
        if not isinstance(child, dict) or child["tag"] != "li":
            continue
        inline_children = []
        nested_lists = []
        for part in child["children"]:
            if isinstance(part, dict) and part["tag"] in {"ol", "ul"}:
                nested_lists.append(part)
            else:
                inline_children.append(part)
        label = "".join(_markdown_inline(part) for part in inline_children).strip()
        classes = set(child["attrs"].get("class", "").casefold().split())
        marker = (
            "- [x]" if "checked" in classes
            else "- [ ]" if "unchecked" in classes
            else f"{number}." if ordered else "-"
        )
        lines.append("    " * level + marker + " " + label)
        for nested in nested_lists:
            lines.append(_markdown_list(nested, level + 1))
        number += 1
    return "\n".join(filter(None, lines))


def _markdown_block(node: dict) -> str:
    tag = node["tag"]
    if tag == "img":
        return _markdown_inline(node)
    if tag in {"ol", "ul"}:
        return _markdown_list(node)
    if tag == "table":
        cells = _markdown_table_cells(node)
        if len(cells) == 1:
            return "\n\n".join(filter(None, (
                _markdown_block(child)
                if isinstance(child, dict) else _markdown_escape(child.strip())
                for child in cells[0]["children"]
            )))
        return _markdown_table(node)
    content = "".join(
        _markdown_inline(
            child,
            heading=tag in _HEADING_TAGS,
            preformatted=tag == "pre",
        )
        for child in node["children"]
    ).strip()
    if not content and tag != "hr":
        return ""
    if tag in _HEADING_TAGS:
        content = "#" * int(tag[1]) + " " + content
    elif tag == "blockquote":
        content = "\n".join("> " + line for line in content.splitlines())
    elif tag == "pre":
        content = "```\n" + content + "\n```"
    elif tag == "hr":
        content = "---"
    elif tag == "p" and re.search(
        r"margin-(?:left|right)\s*:\s*40px",
        node["attrs"].get("style", ""),
        flags=re.IGNORECASE,
    ):
        content = "\n".join("> " + line for line in content.splitlines())
    alignment = _markdown_alignment(node)
    if alignment:
        content += f" {{align={alignment}}}"
    return content


def markdown_from_rich_html(value: str) -> str:
    """Serialize the visual editor's safe HTML as editable Markdown."""
    parser = _MarkdownTreeParser()
    parser.feed(sanitize_rich_html(value, linkify=True))
    parser.close()
    blocks = []
    for child in parser.root["children"]:
        if isinstance(child, str):
            text = child.strip()
            if text:
                blocks.append(_markdown_escape(text))
            continue
        rendered = _markdown_block(child)
        if rendered:
            blocks.append(rendered)
    return "\n\n".join(blocks).strip()
