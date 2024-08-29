import os
import sys

from PySide2.QtWidgets import QCompleter
from PySide2.QtCore import Qt, QObject, QXmlStreamReader, QFile, QIODevice, QStringListModel, QRegularExpression
from PySide2.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor, QTextFormat, QTextBlockUserData


class Language(QObject):
    FormatType = 1

    @staticmethod
    def available():
        result = []
        directory = os.path.dirname(os.path.abspath(__file__))
        for name in os.listdir(directory):
            if not name.endswith('.xml'):
                continue

            result.append(name)

        return result

    def __init__(self, device='default', parent=None):
        super(Language, self).__init__(parent)
        self._loaded = False

        self._style = None
        self._data = {}

        self._completer = QCompleter()
        self._completer.setCompletionColumn(0)
        self._completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self._completer.setCaseSensitivity(Qt.CaseSensitive)
        self._completer.setWrapAround(True)

        self.load(device)

    def load(self, device='default'):
        self._loaded = False

        self._style = LanguageStyle(device, self)
        if not self._style.device:
            return False

        self._style.device.seek(0)
        reader = QXmlStreamReader(self._style.device)

        valid_string = lambda s: s.replace('&apos;', r'\'').replace('&quot;', r'\"').replace('&lt;', '<').replace('&gt;', '>')
        name = ''
        data = []
        read_block = None
        while not reader.atEnd() and not reader.hasError():
            read_type = reader.readNext()
            if read_type == QXmlStreamReader.TokenType.StartElement:
                if reader.name() == 'language':
                    if data:
                        if name in self._data:
                            self._data[name].extend(data)

                        else:
                            self._data[name] = data

                        data = []

                    name = str(reader.attributes().value('name'))

                elif reader.name() == 'name':
                    read_block = reader.attributes()

            elif read_type == QXmlStreamReader.TokenType.Characters and read_block is not None:
                keyword = str(reader.text()).strip('\n ')
                begin_pattern = ''
                end_pattern = ''

                if read_block.hasAttribute('begin_pattern'):
                    begin_pattern = valid_string(str(read_block.value('begin_pattern')))

                if read_block.hasAttribute('end_pattern'):
                    end_pattern = valid_string(str(read_block.value('end_pattern')))

                data.append((keyword, begin_pattern, end_pattern))
                read_block = None

        if data:
            if name in self._data:
                self._data[name].extend(data)

            else:
                self._data[name] = data

        completer_data = []
        for key in self._data:
            for value in self._data[key]:
                if not value[0]:
                    continue

                completer_data.append(value[0])

        self._completer.setModel(QStringListModel(completer_data, self))
        self._loaded = not reader.hasError()
        return self._loaded

    def completer(self):
        return self._completer

    def style(self):
        return self._style

    def keys(self):
        return self._data.keys()

    def values(self, key):
        return self._data[key]

    def loaded(self):
        return self._loaded


class LanguageStyle(QObject):
    def __init__(self, device='default', parent=None):
        super(LanguageStyle, self).__init__(parent)
        self.device = None
        self._name = None
        self._data = {}
        self._loaded = False
        self.load(device)

    def prop(self):
        return QTextFormat.UserProperty + Language.FormatType

    def type(self):
        return QTextFormat.UserFormat + Language.FormatType

    def load(self, device='default'):
        self._data.clear()

        self._data['Unknown'] = QTextCharFormat()
        self._data['Unknown'].setObjectType(self.type())
        self._data['Unknown'].setProperty(self.prop(), 'Unknown')

        self._loaded = False
        if not isinstance(device, QIODevice):
            device_name = device
            if not device_name:
                return False

            device_name = '{}.xml'.format(device_name.split('.', 1)[0])
            directory = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(directory, device_name)
            if not os.path.exists(path):
                return False

            device = QFile(path)
            if not device.open(QIODevice.ReadOnly):
                return False

        self.device = device
        self.device.seek(0)
        reader = QXmlStreamReader(self.device)
        while not reader.atEnd() and not reader.hasError():
            token = reader.readNext()

            if token == QXmlStreamReader.StartElement:
                if reader.name() == "style-scheme":
                    if reader.attributes().hasAttribute("name"):
                        self._name = str(reader.attributes().value("name"))

                elif reader.name() == "style":
                    attrs = reader.attributes()
                    name = attrs.value("name")
                    fmt = QTextCharFormat()
                    fmt.setObjectType(self.type())

                    if attrs.hasAttribute("background"):
                        fmt.setBackground(QColor(str(attrs.value("background"))))

                    if attrs.hasAttribute("foreground"):
                        fmt.setForeground(QColor(str(attrs.value("foreground"))))

                    if attrs.hasAttribute("bold") and attrs.value("bold") == "true":
                        fmt.setFontWeight(QFont.Weight.Bold)

                    if attrs.hasAttribute("italic") and attrs.value("italic") == "true":
                        fmt.setFontItalic(True)

                    if attrs.hasAttribute("underlineStyle"):
                        underline = attrs.value("underlineStyle")
                        s = QTextCharFormat.UnderlineStyle.NoUnderline

                        if underline == "SingleUnderline":
                            s = QTextCharFormat.UnderlineStyle.SingleUnderline

                        elif underline == "DashUnderline":
                            s = QTextCharFormat.UnderlineStyle.DashUnderline

                        elif underline == "DotLine":
                            s = QTextCharFormat.UnderlineStyle.DotLine

                        elif underline == "DashDotLine":
                            s = QTextCharFormat.DashDotLine

                        elif underline == "DashDotDotLine":
                            s = QTextCharFormat.DashDotDotLine

                        elif underline == "WaveUnderline":
                            s = QTextCharFormat.WaveUnderline

                        elif underline == "SpellCheckUnderline":
                            s = QTextCharFormat.SpellCheckUnderline

                        else:
                            sys.stderr.write('unknown underline value {}'.format(underline))
                            sys.stderr.flush()

                        fmt.setUnderlineStyle(s)

                    fmt.setProperty(self.prop(), name)
                    self._data[str(name)] = fmt

        self._loaded = not reader.hasError()

        return self._loaded

    def name(self):
        return self._name

    def loaded(self):
        return self._loaded

    def getFormat(self, name):
        result = self._data.get(name)
        if not result:
            result = self._data.get('Unknown')

        return result


class LanguageHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language='default'):
        super(LanguageHighlighter, self).__init__(document)
        self._language = Language('default', self)

        self._highlight_rules = []
        self._highlight_block_rules = []
        self._highlight_parentheses_rules = []
        self._highlight_include_pattern = None
        self._highlight_function_pattern = None
        self._highlight_define_type_pattern = None

        self._loaded = False
        self.load(language)

    def language(self):
        return self._language

    def style(self):
        return self._language.style()

    def completer(self):
        return self._language.completer()

    def load(self, device='default'):
        if not self._language.load(device):
            return False

        language = self.language()
        keys = self.language().keys()
        for key in keys:
            if key == 'Parentheses':
                value = language.values(key)
                for block in value:
                    begin_pattern = block[1]
                    end_pattern = block[2]
                    rule = [key]
                    if begin_pattern and end_pattern:
                        rule.append(QRegularExpression(r'{}'.format(begin_pattern)))
                        rule.append(QRegularExpression(r'{}'.format(end_pattern)))

                    elif begin_pattern:
                        rule.append(QRegularExpression(r'{}'.format(begin_pattern)))

                    self._highlight_parentheses_rules.append(rule)

            else:
                value = language.values(key)
                for block in value:
                    name = block[0]
                    begin_pattern = block[1]
                    end_pattern = block[2]
                    rule = [key]
                    is_block_rule = False
                    if begin_pattern and end_pattern:
                        rule.append(QRegularExpression(r'{}'.format(begin_pattern)))
                        rule.append(QRegularExpression(r'{}'.format(end_pattern)))
                        is_block_rule = True

                    elif begin_pattern:
                        rule.append(QRegularExpression(r'{}'.format(begin_pattern)))

                    elif name:
                        rule.append(QRegularExpression(r'(\b{}\b)'.format(name)))

                    if is_block_rule:
                        self._highlight_block_rules.append(rule)

                    else:
                        self._highlight_rules.append(rule)

        self._loaded = language.loaded()

        document = self.document()
        self.setDocument(None)
        self.setDocument(document)
        return self._loaded

    def get_single_comment(self):
        language = self.language()
        value = language.values('Comment')
        for block in value:
            if block[0]:
                return block[0]

    def get_parentheses(self, text):
        if text:
            for i in range(len(self._highlight_parentheses_rules)):
                rules = self._highlight_parentheses_rules[i]
                if len(rules) > 2:
                    match = rules[1].match(text)
                    start_index = match.capturedStart()
                    if start_index < 0:
                        match = rules[2].match(text)
                        start_index = match.capturedStart()
                        if start_index < 0:
                            continue

                    return rules[1].pattern().replace('\\', ''), rules[2].pattern().replace('\\', '')

                else:
                    match = rules[1].match(text)
                    start_index = match.capturedStart()
                    if start_index >= 0:
                        return rules[1].pattern().replace('\\', ''), ''

        return None

    def is_parentheses(self, begin_text, end_text):
        begin_text = begin_text if begin_text else ''
        end_text = end_text if end_text else ''
        for i in range(len(self._highlight_parentheses_rules)):
            rules = self._highlight_parentheses_rules[i]
            match = rules[1].match(begin_text)
            start_index = match.capturedStart()
            if start_index >= 0:
                if len(rules) > 2:
                    match = rules[2].match(end_text)
                    start_index = match.capturedStart()
                    if start_index >= 0:
                        return True

                else:
                    return True

        return False

    def highlightBlock(self, text):
        user_data = []
        user_multiline_data = []

        previous_match_start = None
        previous_match_length = None

        self.setFormat(
            0,
            len(text),
            self.style().getFormat('Text')
        )

        # TODO: analyze block data

        # highlight multiline block
        self.setCurrentBlockState(0)
        if self._highlight_block_rules:
            start_index = 0
            match_length = 0

            # check multiline block begin
            highlight_rule_id = self.previousBlockState()
            if highlight_rule_id < 1 or highlight_rule_id > len(self._highlight_block_rules):
                for i in range(len(self._highlight_block_rules)):
                    block_rules = self._highlight_block_rules[i]
                    match = block_rules[1].match(text)
                    start_index = match.capturedStart()
                    match_length = match.capturedEnd() - start_index

                    if start_index >= 0:
                        # begin multiline block match
                        highlight_rule_id = i + 1
                        if self.currentBlockState() == 0:
                            self.setCurrentBlockState(highlight_rule_id)

                        else:
                            self.setCurrentBlockState(0)

                        break

            if highlight_rule_id:
                self.setCurrentBlockState(highlight_rule_id)
                previous_start_index = None
                while start_index >= 0:
                    block_rules = self._highlight_block_rules[highlight_rule_id - 1]
                    match = block_rules[2].match(text, start_index + match_length)

                    end_index = match.capturedEnd()
                    if end_index == -1:
                        # skip part of multiline block
                        match_length = len(text) - start_index
                        self.setCurrentBlockState(highlight_rule_id)

                    else:
                        # begin multiline block match
                        if self.currentBlockState() == 0:
                            start_index = match.capturedStart()
                            self.setCurrentBlockState(highlight_rule_id)

                        # end multiline block match
                        else:
                            self.setCurrentBlockState(0)
                            start_index = previous_start_index if previous_start_index is not None else start_index

                        match_length = end_index - start_index

                    # format text
                    self.setFormat(
                        start_index,
                        match_length,
                        self.style().getFormat(block_rules[0])
                    )

                    user_multiline_data.append((start_index, match_length, block_rules[0]))

                    # continue to next multiline block
                    match = block_rules[1].match(text, start_index + match_length)
                    previous_start_index = start_index
                    start_index = match.capturedStart()

                    match_length = 0

                # last block match
                if self.currentBlockState() and previous_start_index is not None:
                    block_rules = self._highlight_block_rules[highlight_rule_id - 1]
                    match_length = len(text) - previous_start_index
                    self.setFormat(
                        previous_start_index,
                        match_length,
                        self.style().getFormat(block_rules[0])
                    )
                    user_multiline_data.append((previous_start_index, match_length, block_rules[0]))

        # highlight single word
        for rule in self._highlight_rules:
            match_start = 0
            match_length = 0
            while match_start >= 0:
                match_length = len(self.get_single_comment()) if rule[0] == 'Comment' and match_length else match_length  # check comment block end
                match = rule[1].match(text, match_start + match_length)
                match_start = match.capturedStart()
                match_length = match.capturedLength()
                if match_start < 0:
                    break

                # check if text is already matched
                if previous_match_start is not None and previous_match_length is not None:
                    if match_start >= previous_match_start and match_start + match_length <= previous_match_start + previous_match_length:
                        continue

                # check if line is uncommented multiline block
                is_match_multiline_block = False
                user_multiline_size = len(user_multiline_data)
                for i in reversed(range(user_multiline_size)):
                    user_multiline_item = user_multiline_data[i]
                    if (
                        user_multiline_item[0] < match_start < user_multiline_item[0] + user_multiline_item[1]
                        or user_multiline_item[0] < match_start + match_length < user_multiline_item[0] + user_multiline_item[1]
                    ):
                        is_match_multiline_block = True
                        break

                if is_match_multiline_block:
                    continue

                elif rule[0] == 'Comment':
                    self.setCurrentBlockState(0)

                # format text
                if match.lastCapturedIndex() == 1:
                    self.setFormat(
                        match_start,
                        match_length,
                        self.style().getFormat(rule[0])
                    )
                    user_data.append((match_start, match_length, rule[0]))

                else:
                    self.setFormat(
                        match_start,
                        match_length,
                        self.style().getFormat(rule[0])
                    )

                    if rule[0] in ('Include', 'Definition', 'Type'):
                        match_start = match.capturedStart(2)
                        match_length = match.capturedLength(2)
                        self.setFormat(
                            match_start,
                            match_length,
                            self.style().getFormat(rule[0])
                        )
                        user_data.append((match_start, match_length, rule[0]))

                    else:
                        fmt = self.style().getFormat(rule[0])
                        fmt = self.style().getFormat('Text') if not isinstance(fmt, QTextCharFormat) else fmt

                        self.setFormat(
                            match_start,
                            match_length,
                            fmt
                        )
                        user_data.append((match_start, match_length, rule[0]))

                # continue to next match
                previous_match_start = match_start
                previous_match_length = match_length

        block_user_data = QTextBlockUserData()
        block_user_data.value = user_data + user_multiline_data
        self.setCurrentBlockUserData(block_user_data)
