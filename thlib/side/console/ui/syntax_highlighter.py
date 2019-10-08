from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore


def get_char_format(color, style=""):

    _color = Qt4Gui.QColor()
    _color.setNamedColor(color)
    _format = Qt4Gui.QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in style:
        _format.setFontWeight(Qt4Gui.QFont.Bold)

    if "italic" in style:
        _format.setFontItalic(True)

    return _format


class SyntaxHighlighter(Qt4Gui.QSyntaxHighlighter):

    STYLES = {
        'keyword': get_char_format('#21CF4C'),
        'operator': get_char_format('#BABABA'),
        'brace': get_char_format('#BABABA'),
        'defclass': get_char_format('#72DB8C', 'bold'),
        'string': get_char_format('yellow'),
        'string2': get_char_format('orange'),
        'comment': get_char_format('gray', 'italic'),
        'self': get_char_format('#70C1CC', 'italic'),
        'numbers': get_char_format('#D4D4D4'),
    }

    KEYWORDS = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    OPERATORS = [
        '=',
        '==', '!=', '<', '<=', '>', '>=',
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        '\+=', '-=', '\*=', '/=', '\%=',
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    BRACES = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, *args, **kwargs):

        """
        Initialize default settings.
        """

        super(SyntaxHighlighter, self).__init__(*args, **kwargs)
        self.tri_single = (QtCore.QRegExp("'''"), 1, self.STYLES['string2'])
        self.tri_double = (QtCore.QRegExp('"""'), 2, self.STYLES['string2'])

        rules = []
        rules += [(r'\b%s\b' % w, 0, self.STYLES['keyword']) for w in SyntaxHighlighter.KEYWORDS]
        rules += [(r'%s' % o, 0, self.STYLES['operator']) for o in SyntaxHighlighter.OPERATORS]
        rules += [(r'%s' % b, 0, self.STYLES['brace']) for b in SyntaxHighlighter.BRACES]

        rules += [
            (r'\bself\b', 0, self.STYLES['self']),
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, self.STYLES['string']),
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, self.STYLES['string']),
            (r'\bdef\b\s*(\w+)', 1, self.STYLES['defclass']),
            (r'\bclass\b\s*(\w+)', 1, self.STYLES['defclass']),
            (r'#[^\n]*', 0, self.STYLES['comment']),
            (r'\b[+-]?[0-9]+[lL]?\b', 0, self.STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, self.STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, self.STYLES['numbers']),
        ]

        self.rules = [(QtCore.QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):

        """
        Highlight text block.
        """

        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):

        """
        Match multiline block.
        """

        if self.previousBlockState() == in_state:
            start = 0
            add = 0

        else:
            start = delimiter.indexIn(text)
            add = delimiter.matchedLength()

        while start >= 0:
            end = delimiter.indexIn(text, start + add)

            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)

            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add

            self.setFormat(start, length, style)
            start = delimiter.indexIn(text, start + length)

        if self.currentBlockState() == in_state:
            return True

        else:
            return False