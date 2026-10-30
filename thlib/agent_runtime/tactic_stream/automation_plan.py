"""Non-executing draft schemas for native Handler scripts and bindings."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AutomationPlan(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    title: Annotated[str, Field(min_length=1, max_length=100)]
    source: Annotated[str, Field(min_length=1, max_length=128 * 1024)]
    kind: Literal['hook', 'shelf']
    phase: Literal['before', 'after'] = 'before'
    search_type: Annotated[str, Field(max_length=256)] = ''
    process: Annotated[str, Field(max_length=256)] = ''
    context: Annotated[str, Field(max_length=256)] = ''
    entry_key: Annotated[str, Field(max_length=1024)] = ''
    icon: Annotated[str, Field(max_length=128)] = 'play-arrow'
    description: Annotated[str, Field(max_length=4096)] = ''

    @model_validator(mode='after')
    def validate_source(self):
        if not self.title.strip() or '\x00' in self.source:
            raise ValueError('A title and valid Python source are required')
        try:
            compile(self.source, '<Handler automation draft>', 'exec')
        except SyntaxError as error:
            raise ValueError(f'Invalid Python at line {error.lineno}: {error.msg}') from None
        if self.kind == 'shelf' and (not self.entry_key.rpartition('@')[0] or not self.entry_key.rpartition('@')[2]):
            raise ValueError('A shelf button requires an explicit native sidebar entry key')
        if self.kind == 'hook' and self.entry_key:
            raise ValueError('Hook drafts do not have a sidebar assignment')
        if self.kind == 'shelf' and (self.search_type or self.process or self.context or self.phase != 'before'):
            raise ValueError('Shelf drafts use an entry key; hook filters and phases do not apply')
        return self
