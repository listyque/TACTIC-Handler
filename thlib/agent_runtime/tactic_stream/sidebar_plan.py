"""Small semantic edits to existing native sidebar definitions."""
from pydantic import BaseModel,ConfigDict,Field
from typing import Literal


class SidebarGroup(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    name: str=Field(pattern=r'^[a-z][a-z0-9_]{0,63}$')
    title: str=Field(min_length=1,max_length=256)
    icon: str|None=Field(default=None,max_length=128)
    color: str|None=Field(default=None,pattern=r'^(#[0-9A-Fa-f]{6})?$')
    items: list[str]=Field(default_factory=list,max_length=128)


class SidebarUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    item: str=Field(min_length=1,max_length=4096)
    title: str|None=Field(default=None,max_length=256)
    icon: str|None=Field(default=None,max_length=128)
    color: str|None=Field(default=None,pattern=r'^(#[0-9A-Fa-f]{6})?$')
    visible: bool|None=None


class SidebarDocument(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    source: Literal['handler','tactic']='handler'
    groups: list[SidebarGroup]=Field(default_factory=list,max_length=32)
    updates: list[SidebarUpdate]=Field(default_factory=list,max_length=128)
    hidden: list[str]=Field(default_factory=list,max_length=128)
