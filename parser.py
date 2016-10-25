#!/usr/env/bin python
#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # author William "0x77" F.
 # version 0.2
 # copyright MIT
##

# Imports
import sys
import collections
import ply.yacc as yacc

import lexer

from CoalObject import Object, Void, Builtins, Int, Float, String, List


# Globals
local_scope = []
current_scope = 0

local_scope.append({
    'types': {
        'Int': {
            'init': Int
        },
        'Float': {
            'init': Float
        },
        'String': {
            'init': String
        },
        'List': {
            'init': List
        }
    },
    'names': {
        '_VERSION_': Float('0.1')
    }
})


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
    local_types = local_scope[current_scope]['types']

    if obj_type in local_types:
        return local_types[obj_type]['init'](obj_value, obj_value_type)


def flatten(l):
    '''
    Flatten a x-dimensional list into a 1D list
    '''
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


# YACC parsing code down there
# Import the tokens from Lex to use with YACC
tokens = lexer.tokens


# Statements
def p_program(p):
    '''
    program : stmts
    '''


def p_stmts(p):
    '''
    stmts : stmts stmt
          | stmt
    '''


def p_stmt(p):
    '''
    stmt : var_def
         | func_def
         | type_def
         | method_call
         | func_ret
    '''


# Variable definition
def p_var_def(p):
    '''
    var_def : VAR_DEF NAME WITH TYPE_NAME EQUALS value
    '''

    # Make the important tokens easy to use
    var_name = p[2]
    var_type = p[4]
    var_value = p[6].value
    var_value_type = p[6].object_type

    # Try to create a new variable and assign an Object to it
    new_object = createObject(var_type, var_value, var_value_type)

    if new_object:
        local_scope[current_scope]['names'][var_name] = new_object
    else:
        throwError(p, 2, 'TypeError: Unknown type "{}"'.format(var_type))


def p_var_def_empty(p):
    '''
    var_def : VAR_DEF NAME WITH TYPE_NAME ASK
    '''

    # Make the important tokens easy to use
    var_name = p[2]
    var_type = p[4]

    # Try to create an uninitialized variable
    if var_type in local_scope[current_scope]['types']:
        local_scope[current_scope]['names'][var_name] = Void(var_type)
    else:
        throwError(p, 4, 'TypeError: Unknown type "{}"'.format(var_type))


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
    method_call : LSBRACKET value NAME call_arglist RSBRACKET
                | LSBRACKET value NAME RSBRACKET
                | LSBRACKET NAME call_arglist RSBRACKET
                | LSBRACKET NAME RSBRACKET
    '''

    # Flatten argument list
    p[3] = [p[3]] + list(flatten(p[4]))
    p[3] = [p[3][i:i + 3] for i in xrange(0, len(p[3]), 3)]

    for item in p[3]:
        del item[1]

    p[4] = None

    # Debugging
    # debug = []

    # if isinstance(p[2], Object):
    #     debug.append(p[2].value)
    # else:
    #     debug.append(p[2])

    # for i, item in enumerate(list(flatten(p[3]))):
    #     if isinstance(item, Object):
    #         debug.append(item.value)
    #     else:
    #         debug.append(item)

    # print debug

    # Parse call
    if p[2] in Builtins.methods:  # Builtin
        method_name = p[2]

        call_args = list(flatten(p[3]))
        call_args = filter(lambda a: a != ':', call_args)

        call_arg = call_args[0]

        if len(call_args) == 1:
            p[0] = Builtins.call(method_name, call_arg)
        else:
            method_arg = call_args[0]
            method_kwargs = {}

            print call_args

            for i in range(1, len(call_args), 2):
                method_kwargs[call_args[i]] = call_args[i+1]

            p[0] = Builtins.call(method_name,
                                 method_arg,
                                 method_kwargs)
    else:
        call_args = list(flatten(p[3]))
        method_name = call_args[0]

        if len(call_args) == 1:  # [object method]
            p[0] = p[2].call(method_name)
        else:
            method_name = call_args[0]
            method_arg = call_args[1]

            if len(call_args) == 2:  # [object method: argument_value]
                p[0] = p[2].call(method_name, method_arg)
            else:  # [object method: argument_value {...}]
                method_kwargs = {}

                for i in range(2, len(call_args), 2):
                    method_kwargs[call_args[i]] = call_args[i+1]

                p[0] = p[2].call(method_name, method_arg, method_kwargs)


def p_call_arglist(p):
    '''
    call_arglist : WITH value NAME call_arglist
                 | WITH value
    '''
    p[0] = p[1:]

    # That doesn't seem to work when we're dealing with Object instances:
    # if isinstance(p[len(p)-1], Object):
    #     p[0] = p[1:]
    # else:
    #     p[0] = p[1:len(p)-1] + p[len(p)-1]


# Function definition
def p_func_def(p):
    '''
    func_def : FUNC_DEF func_argdefs AS TYPE_NAME
    '''
    # TODO


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
    # TODO


# Values
def p_value(p):
    '''
    value : OBJECT
          | method_call
    '''
    p[0] = p[1]


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
          | LIST
    '''
    p[0] = List(p[1:][1])


def p_value_list_items(p):
    '''
    list_items : list_items COMMA list_items
               | list_items COMMA list_item
    '''
    p[0] = list(flatten(filter(lambda a: a != ',', p[1:])))


def p_value_list_item_single(p):
    '''
    list_items : list_item
    '''
    p[0] = p[1]


def p_value_list_item(p):
    '''
    list_item : value
    '''
    p[0] = p[1]


def p_value_var(p):
    '''
    value : NAME
    '''
    p[0] = local_scope[current_scope]['names'][p[1]]


def p_value_get_list_item(p):
    '''
    value : value LBRACKET value RBRACKET
    '''
    if isinstance(p[1], List):
        item = p[1].getItem(p[3].value)

        if isinstance(item, Void):
            throwError(p, 3, 'IndexError: Index out of range ({})'
                             .format(p[3].value))
    else:
        throwError(p, 1, 'TypeError: "{}" object is not iterable'.format(p[1]))

    p[0] = item


# Error rule for syntax errors
def p_error(p):
    throwError(p, 0, 'Syntax error: {}'.format(p.value))

# Build the parser
yacc.yacc()


# TESTING!
PRINT_TOKENS = False

test_file = open('test.coal')
code = test_file.readlines()
src = '\n'.join(code)

if PRINT_TOKENS:
    lexer.lexer.input(src)

    while True:
        tok = lexer.lexer.token()

        if not tok:
            break

        print(tok)

yacc.parse(src)
