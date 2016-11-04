#!/usr/bin/env python3
#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # author William "10c8" F.
 # version 0.31
 # copyright MIT
##

# Imports
import sys
import collections
import ply.yacc as yacc

import lexer
from CoalAST import *


# Utils
def throwError(p, pos, message):
    '''
    Throw an error. (Do I need to explain more?)
    '''

    if pos > 0:
        line_num = p.lineno(pos)

        print('[{}:{}] {}.'.format(line_num, p.lexpos(pos) - 1, message))
    else:
        print('[{}:{}] {}.'.format(p.lineno, p.lexpos, message))

    sys.exit(1)


def createObject(obj_type, obj_value, obj_value_type):
    '''
    Create a new Object from a custom (or built-in) type
    '''

    local_types = lexer.local_scope[lexer.current_scope]['types']

    if obj_type in local_types:
        return local_types[obj_type]['init'](obj_value, obj_value_type)


def flatten(l):
    '''
    Flatten a x-dimensional list into a 1D list
    '''

    def dims(testlist, dim=0):
        if isinstance(testlist, list):
            if testlist == []:
                return dim
            dim = dim + 1
            dim = dims(testlist[0], dim)
            return dim
        else:
            if dim == 0:
                return -1
            else:
                return dim

    if dims(l) < 2:
        pass

    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes))\
           and not isinstance(el, CoalAST) and not isinstance(el, tuple):
            yield from flatten(el)
        else:
            yield el


# YACC parsing code down there
# Import the tokens from Lex to use with YACC
tokens = lexer.tokens


def p_program(p):
    '''
    program : stmts
    '''
    p.lexer.ast = list(flatten(p[1]))


# Statements
def p_stmts(p):
    '''
    stmts : stmts stmt
          | stmt
    '''

    if len(p) == 3:
        p[0] = p[1:]
    else:
        p[0] = [p[1]]


def p_stmt(p):
    '''
    stmt : var_def
         | var_assign
         | iter_assign
         | func_def
         | func_ret
         | type_def
         | method_call
         | conditional
    '''
    p[0] = p[1]


# Variable definition
def p_var_def(p):
    '''
    var_def : VAR_DEF NAME WITH TYPE_NAME EQUALS value
    '''

    # Make the important tokens easy to use
    var_name = p[2]
    var_type = p[4]
    var_value = p[6]

    it = NameDef(
        var_name,
        var_type,
        var_value
    )

    p[0] = it


def p_var_def_empty(p):
    '''
    var_def : VAR_DEF NAME WITH TYPE_NAME ASK
    '''

    var_name = p[2]
    var_type = p[4]

    p[0] = NameDefEmpty(
        var_name,
        var_type
    )


# Assignment
def p_var_assign(p):
    '''
    var_assign : NAME EQUALS value
    '''

    var_name = p[1]
    var_value = p[3]

    p[0] = NameAssign(
        var_name,
        var_value
    )


def p_iterable_item_assign(p):
    '''
    iter_assign : NAME LBRACE value RBRACE EQUALS value
    '''

    iter_name = p[1]
    iter_index = p[3]
    iter_value = p[6]

    p[0] = IterableItemAssign(
        iter_name,
        iter_index,
        iter_value
    )


# Class definition
def p_type_def(p):
    '''
    type_def : TYPE_DEF TYPE_NAME TYPE_EXT TYPE_NAME AS
             | TYPE_DEF TYPE_NAME AS
    '''
    # TODO


# Method call
def p_method_call(p):
    '''
    method_call : LSQB value NAME call_arglist RSQB
                | LSQB value NAME RSQB
                | LSQB NAME call_arglist RSQB
                | LSQB NAME RSQB
    '''

    # Flatten argument list
    if len(p) > 4:
        p[3] = [p[3]] + list(flatten(p[4]))
        p[3] = [p[3][i:i + 3] for i in range(0, len(p[3]), 3)]

        for item in p[3]:
            del item[1]
    else:
        p[3] = []

    if not isinstance(p[2], CoalAST):
        selectors = '{}_'.format(p[2])

        if len(p[3]):
            call_args = [v for v in list(flatten(p[3]))[:] if v != ':']
            selector_args = [call_args[0]]

            if len(call_args) > 2:
                for i in range(1, len(call_args), 2):
                    selectors += '{}_'.format(call_args[i])
                    selector_args.append(call_args[i+1])
        else:
            selector_args = []

        p[0] = LocalMethodCall(
            selectors,
            selector_args
        )
    else:
        call_args = list(flatten(p[3]))
        selectors = ''
        selector_args = []

        for i in range(0, len(call_args), 2):
            selectors += '{}_'.format(call_args[i])

            if len(call_args) > 1:
                selector_args.append(call_args[i+1])

        p[0] = ObjectMethodCall(
            p[2],
            selectors,
            selector_args
        )


def p_call_arglist(p):
    '''
    call_arglist : WITH value NAME call_arglist
                 | WITH value
    '''
    p[0] = p[1:]

    # This doesn't seem to work when we're dealing with Object instances:
    # if isinstance(p[len(p)-1], Object):
    #     p[0] = p[1:]
    # else:
    #     p[0] = p[1:len(p)-1] + p[len(p)-1]


# Function definition
def p_func_def_simple(p):
    '''
    func_def : DEF NAME AS TYPE_NAME stmts END
    '''

    selector = p[2]
    return_type = p[4]

    if isinstance(p[5], list):
        suite = list(flatten(p[5]))
    else:
        suite = [p[5]]

    p[0] = FuncDef(
        [selector],
        [],
        [],
        return_type,
        suite,
        True
    )


def p_func_def(p):
    '''
    func_def : DEF func_argdefs AS TYPE_NAME stmts END
    '''

    # TODO
    # 0.2 - It's still a work in progress.
    # 0.3 - It seems stable now.

    selectors = p[2]
    selector_names = [s[0] for s in selectors]
    selector_types = [s[1] for s in selectors]
    selector_aliases = [s[2] if len(s) > 2 else None for s in selectors]
    return_type = p[4]

    if isinstance(p[5], list):
        suite = list(flatten(p[5]))
    else:
        suite = [p[5]]

    p[0] = FuncDef(
        selector_names,
        selector_types,
        selector_aliases,
        return_type,
        suite
    )


def p_func_argdefs(p):
    '''
    func_argdefs : func_argdefs func_argdef
    '''
    p[0] = p[1] + [p[2]]


def p_func_argdef(p):
    '''
    func_argdefs : func_argdef
    '''
    p[0] = [p[1]]


def p_func_argdef_single(p):
    '''
    func_argdef : NAME WITH LPAREN TYPE_NAME NAME RPAREN
                | NAME WITH LPAREN TYPE_NAME RPAREN
    '''

    if len(p) == 6:
        p[0] = [p[1], p[4]]
    else:
        p[0] = [p[1], p[4], p[5]]


def p_func_ret(p):
    '''
    func_ret : FUNC_RET value
             | FUNC_RET
    '''

    if len(p) > 2:
        p[0] = FuncRet(p[2])
    else:
        p[0] = FuncRet(Void('Void'))


# Conditional
def p_conditional(p):
    '''
    conditional : ifblock END
                | ifblock elseblock END
                | ifblock elifblocks END
                | ifblock elifblocks elseblock END
    '''

    if len(p) == 3:  # IF test THEN stmts END
        p[0] = IfBlock(
            p[1][0],
            p[1][1]
        )
    elif len(p) == 4:  # (IfBlock ELSE stmts END)
        if p[2][0] is None:
            p[0] = IfBlock(
                p[1][0],
                p[1][1],
                p[2][1:]
            )
        else:
            p[0] = IfBlock(
                p[1][0],
                p[1][1],
                else_suite=p[2]
            )
    else:
        if len(p) > 3:
            else_suite = p[3]
        else:
            else_suite = None

        p[0] = IfBlock(
            p[1][0],
            p[1][1],
            p[2][1:],
            else_suite
        )


def p_if_elif_block(p):
    '''
    ifblock : IF value THEN stmts
    elifblock : ELIF value THEN stmts
    '''
    p[0] = (p[2], p[4])


def p_elif_blocks(p):
    '''
    EMPTY :

    elifblocks : elifblocks elifblock
               | EMPTY
    '''
    if len(p) == 3:
        p[0] = list(flatten(p[1:]))


def p_else_block(p):
    '''
    elseblock : ELSE stmts
    '''
    p[0] = p[2]


# Value
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)


def p_value_binop(p):
    '''
    value : value PLUS value
          | value MINUS value
          | value TIMES value
          | value DIVIDE value
          | value PERCENT value
          | value AND value
          | value OR value
          | value XOR value
          | value LSHIFT value
          | value RSHIFT value
          | value EQEQUAL value
          | value GREATER value
          | value LESS value
    '''

    if p[2] == '+':
        p[0] = ExprAddition(p[1], p[3])
    elif p[2] == '-':
        p[0] = ExprSubtraction(p[1], p[3])
    elif p[2] == '*':
        p[0] = ExprMultiplication(p[1], p[3])
    elif p[2] == '/':
        p[0] = ExprDivision(p[1], p[3])
    elif p[2] == '%':
        p[0] = ExprModulo(p[1], p[3])
    elif p[2] == '&':
        p[0] = ExprBitAnd(p[1], p[3])
    elif p[2] == '|':
        p[0] = ExprBitOr(p[1], p[3])
    elif p[2] == '^':
        p[0] = ExprBitXor(p[1], p[3])
    elif p[2] == '<<':
        p[0] = ExprBitShiftL(p[1], p[3])
    elif p[2] == '>>':
        p[0] = ExprBitShiftR(p[1], p[3])
    elif p[2] == '==':
        p[0] = ExprEqual(p[1], p[3])
    elif p[2] == '>':
        p[0] = ExprGreater(p[1], p[3])
    elif p[2] == '<':
        p[0] = ExprLess(p[1], p[3])


def p_value_uminus(p):
    '''
    value : MINUS value %prec UMINUS
    '''
    p[0] = type(p[2]).__class__(-p[2].value)


def p_value_group(p):
    '''
    value : LPAREN value RPAREN
    '''
    p[0] = p[2]


def p_value(p):
    '''
    value : OBJECT
          | method_call
    '''
    p[0] = p[1]


def p_value_bool(p):
    '''
    value : TRUE
          | FALSE
    '''
    p[0] = Bool(p[1])


def p_value_int(p):
    '''
    value : INT
    '''
    p[0] = Int(p[1])


def p_value_float(p):
    '''
    value : FLOAT
    '''
    p[0] = Float(p[1])


def p_value_string(p):
    '''
    value : STRING
    '''
    p[0] = String(p[1])


def p_value_list(p):
    '''
    value : LPAREN list_items RPAREN
          | LPAREN RPAREN
    '''

    if len(p) == 4:
        p[0] = List(p[1:][1])
    else:
        p[0] = List([])


def p_value_list_items(p):
    '''
    list_items : list_items COMMA value
               | value
    '''

    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = list(flatten(filter(lambda a: a != ',', p[1:])))


def p_value_name(p):
    '''
    value : NAME
    '''
    p[0] = Name(p[1])


def p_value_get_item(p):
    '''
    value : value LBRACE value COMMA value RBRACE
          | value LBRACE value RBRACE
    '''

    if len(p) == 5:
        item = ItemFromIterable(p[1], p[3])
    else:
        item = ItemFromIterable(p[1], p[3], p[5])

    p[0] = item


# Error rule for syntax errors
def p_error(p):
    throwError(p, 0, 'Syntax error: {}'.format(p.value))


# TESTING!
# Build the parser
test_file = open('test.coal')
code = test_file.readlines()
src = '\n'.join(code)

# lexer = lexer.IndentLexer()
lexer = lexer.lexer
lexer.ast = []

DEBUGGING = False

if not DEBUGGING:
    parser = yacc.yacc(optimize=True)
else:
    parser = yacc.yacc()
    lexer.input(src)

    while True:
        tok = lexer.token()

        if not tok:
            break

        print(tok)

parser.parse(src)


# TODO: Parse AST
for stmt in lexer.ast:
    ExecuteCoal(stmt)
