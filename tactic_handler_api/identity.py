"""Validated TACTIC identities, independent of transport and presentation."""

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode


@dataclass(frozen=True)
class SearchKey:
    search_type: str
    project_code: str
    column: str
    value: str

    def __post_init__(self):
        if (
            len(self.search_type.split("/")) != 2
            or any(
                not part or part in (".", "..") for part in self.search_type.split("/")
            )
            or any(char in self.search_type for char in "?&#\\")
        ):
            raise ValueError("Expected a TACTIC Search Type: namespace/table")
        if not self.project_code:
            raise ValueError(
                "A project code is required (the namespace is not a project)"
            )
        if self.column not in ("code", "id") or not self.value:
            raise ValueError("A nonempty code or id is required")

    @classmethod
    def parse(cls, value: str) -> "SearchKey":
        if not isinstance(value, str):
            raise TypeError("Expected a complete TACTIC search key")
        value = value.removeprefix("skey://")
        search_type, separator, query = value.partition("?")
        pairs = parse_qsl(query, keep_blank_values=True)
        parameters = dict(pairs)
        if not separator or len(pairs) != len(parameters):
            raise ValueError("Invalid or ambiguous TACTIC search key")
        if set(parameters) - {"project", "code", "id", "context"}:
            raise ValueError("Unsupported TACTIC search-key parameters")
        columns = [name for name in ("code", "id") if name in parameters]
        if len(columns) != 1:
            raise ValueError("A search key must contain exactly one code or id")
        project = parameters.get("project") or (
            "sthpw" if search_type.startswith("sthpw/") else ""
        )
        return cls(search_type, project, columns[0], parameters[columns[0]])

    def __str__(self):
        return (
            self.search_type
            + "?"
            + urlencode(
                {
                    "project": self.project_code,
                    self.column: self.value,
                }
            )
        )
