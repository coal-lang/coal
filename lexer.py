#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # Module: Lexer
 # version 0.31
##

# Imports
import ply.lex as lex

# Reserved names
reserved = {
    # Quit!
    'exit': 'EXIT',

    # Imports
    'import': 'IMP_CALL',
    'from': 'IMP_FROM',

    # Variables and functions
    'let': 'VAR_DEF',
    'def': 'DEF',
    'end': 'END',
    'return': 'FUNC_RET',

    # Classes
    'type': 'CLASS',
    'extends': 'EXTENDS',
    'init': 'INIT',
    'private': 'PRIVATE',
    'public': 'PUBLIC',
    'repr': 'REPR',

    # Loops
    'for': 'FOR',
    'each': 'EACH',
    'while': 'WHILE',
    'break': 'BREAK',
    'next': 'NEXT',

    # Conditionals
    'elif': 'ELIF',
    'if': 'IF',
    'else': 'ELSE',
    'try': 'TRY',
    'except': 'EXCEPT',
    'do': 'DO',

    # Booleans
    'true': 'TRUE',
    'false': 'FALSE'
}

# Tokens
tokens = (
    'WITH', 'AS', 'ASK', 'NEWLINE',
    'SPACE', 'COMMA', 'EQUALS', 'BAR', 'PERCENT', 'AMPERSAND',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'AND', 'OR', 'XOR', 'RSHIFT', 'LSHIFT', 'NOT',
    'EQEQUAL', 'NOT_EQUAL', 'GREATER', 'LESS', 'EQGREATER', 'EQLESS',
    'PLUSEQ', 'MINUSEQ', 'TIMESEQ', 'DIVEQ',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LSQB', 'RSQB',
    'TYPE_NAME',
)

complex = (
    'VOID',
    'INT',
    'FLOAT',
    'STRING',
    'LIST',
    'OBJECT',
    'NAME', 'LETTER_NAME',
    'INDENT', 'DEDENT',
)

tokens += tuple(reserved.values())
tokens += complex

t_LETTER_NAME = r'[a-z_]'

# For tests
t_EQEQUAL = r'\=\='
t_GREATER = r'\>'
t_LESS = r'\<'
t_EQGREATER = r'\>\='
t_EQLESS = r'\<\='

# Simple tokens
t_WITH = r':'
t_AS = r'\-\>'
t_ASK = r'\?'
t_COMMA = r','
t_EQUALS = r'\='
t_BAR = r'\|'
t_NOT_EQUAL = r'\!\='
t_PERCENT = r'\%'
t_AMPERSAND = r'\&'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_TYPE_NAME = r'\b[A-Z][a-zA-Z]+'

# For expressions
t_PLUSEQ = r'\+\='
t_MINUSEQ = r'\-\='
t_TIMESEQ = r'\*\='
t_DIVEQ = r'\/\='
t_PLUS = r'\+'
t_MINUS = r'\-'
t_TIMES = r'\*'
t_DIVIDE = r'\/'
t_AND = r'\&'
t_OR = r'\|'
t_XOR = r'\^'
t_RSHIFT = r'\>\>'
t_LSHIFT = r'\<\<'
t_NOT = r'\~'


def t_LPAREN(t):
    r'\('

    # t.lexer.paren_count += 1
    return t


def t_RPAREN(t):
    r'\)'

    # t.lexer.paren_count -= 1
    return t


def t_LSQB(t):
    r'\['

    # t.lexer.bracket_count += 1
    return t


def t_RSQB(t):
    r'\]'

    # t.lexer.bracket_count -= 1
    return t


# Complex tokens
# Read in a float
def t_FLOAT(t):
    r'-?\d+\.\d*(e-?\d+)?'

    t.value = float(t.value)
    return t


# Read in an int
def t_INT(t):
    r'-?\d+'

    t.value = int(t.value)
    return t


# Read in a string
def t_STRING(t):  # HACK
    # r'([\'"]).+?\1'
    # r'\"([^\\"]|(\\.))*\"'
    r'"([^\\"]+|\\"|\\n|\\\\)*"'

    t.value = bytes(t.value[1:-1], 'utf-8').decode('unicode-escape')
    return t


def t_NAME(t):
    r'[a-z_][a-zA-Z_]+'

    if t.value in reserved:
        t.type = reserved[t.value]
    else:
        t.type = 'NAME'

    return t


# Ignore comments
def t_comment(t):
    r'[ ]*//[^\n]*'
    pass


# Significant whitespace (indent)
# def t_SPACE(t):
    # r' [ ]+ '

    # if t.lexer.at_line_start and t.lexer.paren_count == 0:
    #     return t


# Track line numbers
def t_newline(t):
    r'\n+'

    t.lexer.lineno += len(t.value)
    # t.type = 'NEWLINE'

    # return t

    # if t.lexer.paren_count == 0:
    #     return t


# Ignore spaces and tabs
t_ignore = ' \t'


# Error handling rule
def t_error(t):
    print('Illegal character "{}".'.format(t.value[0]))
    t.lexer.skip(1)


lexer = lex.lex()

# Indentation (WIP)
NO_INDENT = 0
MAY_INDENT = 1
MUST_INDENT = 2


def filtr(lexer):
    token = None
    tokens = iter(lexer.token, None)
    tokens = track_tokens_filter(lexer, tokens)

    for token in indentation_filter(tokens):
        yield token


class IndentLexer(object):
    def __init__(self, debug=0, optimize=0, lextab='lextab', reflags=0):
        self.lexer = lex.lex(debug=debug,
                             optimize=optimize,
                             lextab=lextab,
                             reflags=reflags)
        self.token_stream = None

    def input(self, s):
        self.lexer.paren_count = 0
        self.lexer.input(s)
        self.token_stream = filtr(self.lexer)

    def token(self):
        try:
            return self.token_stream.__next__()
        except StopIteration:
            return None


# only care about whitespace at the start of a line
def track_tokens_filter(lexer, tokens):
    lexer.at_line_start = at_line_start = True
    indent = NO_INDENT

    # for token in tokens:
    tokens = list(tokens)
    print(tokens)

    for i, token in enumerate(tokens):
        token.at_line_start = at_line_start
        print(token, token.at_line_start)

        if token.type == "AS":
            if tokens[i+1].type == "NAME_TYPE"\
               or tokens[i+1].type == "NAME":
                at_line_start = False
                indent = MUST_INDENT
                token.must_indent = False
        elif token.type == "DO":
            at_line_start = False
            indent = MUST_INDENT
            token.must_indent = False
        elif token.type == "NEWLINE":
            at_line_start = True

            if indent == MAY_INDENT:
                indent = MUST_INDENT

            token.must_indent = False
        elif token.type == "SPACE":
            assert token.at_line_start is True

            at_line_start = True
            token.must_indent = False
        else:
            # A real token
            if indent == MUST_INDENT:
                token.must_indent = True
            else:
                token.must_indent = False

            at_line_start = False
            indent = NO_INDENT

        yield token
        lexer.at_line_start = at_line_start


def _new_token(type, lineno):
    tok = lex.LexToken()
    tok.type = type
    tok.value = None
    tok.lineno = lineno

    return tok


# Synthesize a DEDENT tag
def DEDENT(lineno):
    return _new_token("DEDENT", lineno)


# Synthesize an INDENT tag
def INDENT(lineno):
    return _new_token("INDENT", lineno)


# Track the indentation level and emit the right INDENT / DEDENT events.
def indentation_filter(tokens):
    # A stack of indentation levels; will never pop item 0
    levels = [0]
    token = None
    depth = 0
    prev_was_SPACE = False

    for token in tokens:
        # SPACE only occurs at the start of the line
        # There may be SPACE followed by NEWLINE so
        # only track the depth here.  Don't indent/dedent
        # until there's something real.

        if token.type == "SPACE":
            assert depth == 0

            depth = len(token.value)
            prev_was_SPACE = True

            # SPACE tokens are never passed to the parser
            continue

        if token.type == "NEWLINE":
            depth = 0

            if prev_was_SPACE or token.at_line_start:
                # ignore blank lines
                continue

            # pass the other cases on through
            yield token
            continue

        # then it must be a real token (not SPACE, not NEWLINE)
        # which can affect the indentation levels

        prev_was_SPACE = False
        if token.must_indent:
            # The current depth must be larger than the previous level
            if not (depth > levels[-1]):
                raise IndentationError("expected an indented block")

            levels.append(depth)
            yield INDENT(token.lineno)
        elif token.at_line_start:
            # Must be on the same level or one of the previous levels
            if depth == levels[-1]:
                # At the same level
                pass
            elif depth > levels[-1]:
                raise IndentationError("indentation increase but not in new"
                                       " block")
            else:
                # Back up; but only if it matches a previous level
                try:
                    i = levels.index(depth)
                except ValueError:
                    raise IndentationError("inconsistent indentation")

                for _ in range(i+1, len(levels)):
                    yield DEDENT(token.lineno)
                    levels.pop()

        yield token

    # Finished processing!
    # Must dedent any remaining levels
    if len(levels) > 1:
        assert token is not None

        for _ in range(1, len(levels)):
            yield DEDENT(token.lineno)
