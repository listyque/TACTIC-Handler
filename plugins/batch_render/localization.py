"""Plugin-owned UI messages; project names and statuses stay server data."""
import json
import re
from pathlib import Path
from string import Formatter
from PySide6.QtCore import Property, Slot


class LocalizationMixin:
    def _init_localization(self):
        self._language = 'en'
        self._translations = json.loads((Path(__file__).parent / 'strings.ru.json').read_text(encoding='utf-8'))
        self._english_messages = {target:source for source,target in self._translations.items()}
        self._message_patterns = []
        templates=sorted(self._translations.items(),key=lambda item:sum(len(literal) for literal,field,spec,conversion in Formatter().parse(item[0])),reverse=True)
        for source,target in templates:
            fields = [field for literal,field,spec,conversion in Formatter().parse(source) if field]
            if not fields:
                continue
            patterns=[]
            for template in (source,target):
                pattern=re.escape(template)
                for field in fields:
                    pattern=pattern.replace(re.escape('{'+field+'}'),'(?P<'+field+'>.*?)')
                patterns.append(re.compile(pattern))
            self._message_patterns.append((patterns,source,target))

    @Property('QVariantMap', constant=True)
    def translations(self):
        return self._translations

    @Slot(str, str, result=str)
    def translate(self, value, language):
        if value in self._translations:
            return self._translations[value] if language=='ru' else value
        if value in self._english_messages:
            return value if language=='ru' else self._english_messages[value]
        for patterns,source,target in self._message_patterns:
            for pattern in patterns:
                match=pattern.fullmatch(value)
                if match:
                    return (target if language=='ru' else source).format(**match.groupdict())
        return value

    def _text(self, value):
        return '\n'.join(self.translate(line,self._language) for line in str(value or '').split('\n'))

    @Slot(str)
    def setLanguage(self, language):
        language='ru' if language=='ru' else 'en'
        if self._language != language:
            self._language=language
            self._replace_episode_filters(self.episode_filters.records())
            self._publish_queue()
            self.stateChanged.emit()
