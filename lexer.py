#!/usr/env/bin python
#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # Module: Lexer
 # version 0.2
##

# Imports
import ply.lex as lex

# Reserved names
reserved = {
    # Imports
    'import': 'IMP_CALL',
    'from': 'IMP_FROM',

    # Variables and functions
    'let': 'VAR_DEF',
    'def': 'FUNC_DEF',
    'return': 'FUNC_RET',

    # Classes
    'class': 'TYPE_DEF',
    'extends': 'TYPE_EXT',
    'init': 'TYPE_INIT',
    'private': 'TYPE_PRIVATE',
    'public': 'TYPE_PUBLIC',
    'repr': 'TYPE_REPR',

    # Loops
    'for': 'LOOP_FOR',
    'foreach': 'LOOP_FOREACH',
    'while': 'LOOP_WHILE',

    # Conditionals
    'if': 'COND_IF',
    'elif': 'COND_ELIF',
    'else': 'COND_ELSE',
    'try': 'COND_TRY',
    'except': 'COND_EXC'
}

# Tokens
tokens = (
    'WITH', 'AS', 'ASK',
    'COMMA', 'EQUALS', 'NOT_EQUAL',
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LSBRACKET', 'RSBRACKET',
    'TYPE_NAME',
)

complex = (
    'INT',
    'FLOAT',
    'STRING',
    'LIST',
    'OBJECT',
    'NAME',
)

tokens += tuple(reserved.values())
tokens += complex

# Simple tokens
t_WITH = r':'
t_AS = r'->'
t_ASK = r'\?'
t_COMMA = r','
t_EQUALS = r'\='
t_NOT_EQUAL = r'\!\='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\{'
t_RBRACKET = r'\}'
t_LSBRACKET = r'\['
t_RSBRACKET = r'\]'
t_TYPE_NAME = r'\b[A-Z][a-zA-Z]+'


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
def t_STRING(t):
    # r'([\'"]).+?\1'
    r'\"([^\\"]|(\\.))*\"'

    escaped = 0
    str = t.value[1:-1]
    new_str = ""

    for i in range(0, len(str)):
        c = str[i]

        if escaped:
            if c == "n":
                c = "\n"
            elif c == "t":
                c = "\t"

            new_str += c
            escaped = 0
        else:
            if c == "\\":
                escaped = 1
            else:
                new_str += c

    t.value = new_str
    return t


def t_NAME(t):
    r'[a-z_][a-zA-Z_]+'

    if t.value in reserved:
        t.type = reserved.get(t.value, 'ID')
    else:
        t.type = 'NAME'

    return t


# Track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# Ignore comments
def t_comment(t):
    r'//[^\n]*'
    pass


# Ignore spaces and tabs
t_ignore = ' \t'


# Error handling rule
def t_error(t):
    print('Illegal character "{}".'.format(t.value[0]))
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()
