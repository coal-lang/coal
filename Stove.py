#!/usr/bin/env python3
#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # author William "10c8" F.
 # version 0.3
 # copyright MIT
##

# Imports
import sys
import collections
import ply.yacc as yacc

import lexer
from CoalObject import Object, CoalBuiltin, Void, Bool, Int, Float, String, List

Builtins = CoalBuiltin()


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

    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
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
         | var_assign
         | func_def
         | func_ret
         | func_end
         | type_def
         | method_call
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
    var_obj = createObject(var_type, var_value, var_value_type)
    # var_obj_id = id(var_obj)

    if var_obj:
        p.lexer.local_scope[p.lexer.current_scope]['names'][var_name] = var_obj
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
    if var_type in p.lexer.local_scope[p.lexer.current_scope]['types']\
       or var_type == 'Any':
        p.lexer.local_scope[p.lexer.current_scope]['names'][var_name] = Void(obj_type=var_type)
    else:
        throwError(p, 4, 'TypeError: Unknown type "{}"'.format(var_type))


def p_var_assign(p):
    '''
    var_assign : NAME EQUALS value
    '''

    var_name = p[1]
    var_value = p[3]

    scope = p.lexer.local_scope[p.lexer.current_scope]

    if var_name not in scope['names']:
        throwError(p, 1, 'NameError: Unknown name "{}"'.format(var_name))

    if isinstance(scope['names'][var_name], Void):
        var_type = scope['names'][var_name].value

        if var_type != 'Any'\
           and var_type != var_value.object_type:
            throwError(p, 3, 'TypeError: Wrong value type for Void({}): {}'
                             .format(var_type,
                                     var_value.object_type))

    scope['names'][var_name] = var_value


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
    p[3] = [p[3]] + list(flatten(p[4]))
    p[3] = [p[3][i:i + 3] for i in range(0, len(p[3]), 3)]

    for item in p[3]:
        del item[1]

    p[4] = None

    if not isinstance(p[2], Object):
        call_args = [v for v in list(flatten(p[3]))[:] if v != ':']
        selectors = '{}_'.format(p[2])
        args = [call_args[0]]

        if len(call_args) > 2:
            for i in range(1, len(call_args), 2):
                selectors += '{}_'.format(call_args[i])
                args.append(call_args[i+1])

        if selectors in Builtins.methods:
            p[0] = Builtins.call(selectors, args)
        elif selectors in p.lexer.local_scope[p.lexer.current_scope]['methods']:
            current_scope = p.lexer.current_scope
            func = p.lexer.local_scope[current_scope]['methods'][selectors]
            func_code = func['code']
            func_args = func['args']

            p.lexer.current_scope += 1
            p.lexer.local_scope.append({
                'types': Builtins.types,
                'methods': {},
                'names': Builtins.names
            })

            if len(args) != len(func_args):
                throwError(p, 0, 'Wrong argument count for {}'
                                 .format(selectors))
            else:
                for i in range(len(args)):
                    p.lexer.local_scope[p.lexer.current_scope]['names'][func_args[i]] = args[i]

            for line in func_code:
                if p.lexer.returned:
                    p.lexer.returned = False
                    break

                if line.lstrip(' ').lstrip('\t').startswith('//')\
                   or line.rstrip('\n') == '':
                    continue

                if not lexer.def_in or line.rstrip('\n') == 'end':
                    parser.parse(line)
                else:
                    lexer.def_list[lexer.def_depth]['code']\
                         .append(line.lstrip(' ')
                                     .lstrip('\t'))

            p[0] = p.lexer.ret_value
            p.lexer.ret_value = Void(obj_type='Void')
    else:
        call_args = list(flatten(p[3]))
        selectors = ''
        args = []

        for i in range(0, len(call_args), 2):
            selectors += '{}_'.format(call_args[i])
            args.append(call_args[i+1])

        p[0] = p[2].call(selectors, args)


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
    func_def : DEF func_argdefs AS TYPE_NAME
    '''

    # TODO
    # It's still a work in progress.

    selectors = p[2]
    selector_names = [s[0] for s in selectors]
    selector_types = [s[1] for s in selectors]

    method_name = ''
    for selector in selector_names:
        method_name += '{}_'.format(selector)

    return_type = p[4]

    # Apply selector aliases
    selector_names = [s[2] if len(s) > 2 else s[0] for s in selectors]

    p.lexer.def_depth += 1
    p.lexer.def_in = True
    p.lexer.def_list.append({
        'name': method_name,
        'args': selector_names,
        'types': selector_types,
        'return': return_type,
        'code': []
    })


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


def p_func_end(p):
    '''
    func_end : END
    '''

    if p.lexer.def_in:
        func = p.lexer.def_list[p.lexer.def_depth]
        name = func['name']
        p.lexer.local_scope[p.lexer.current_scope]['methods'][name] = func

        del p.lexer.def_list[p.lexer.def_depth]
        p.lexer.def_depth -= 1
        p.lexer.def_in = False
    else:
        throwError(p, 0, 'Unmatched END')


def p_func_ret(p):
    '''
    func_ret : FUNC_RET value
             | FUNC_RET
    '''

    if len(p) > 2:
        p.lexer.ret_value = p[2]
    else:
        pass


# Values
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
    '''
    p[0] = List(p[1:][1])


def p_value_list_items(p):
    '''
    list_items : list_items COMMA value
               | value
    '''
    p[0] = list(flatten(filter(lambda a: a != ',', p[1:])))


def p_value_name(p):
    '''
    value : NAME
    '''
    p[0] = p.lexer.local_scope[p.lexer.current_scope]['names'][p[1]]


def p_value_get_item(p):
    '''
    value : value LBRACE value COMMA value RBRACE
          | value LBRACE value RBRACE
    '''

    if callable(p[1].iter):
        if len(p) == 5:
            item = p[1].iter(p[3].value)
        else:
            item = p[1].iter(p[3].value, p[5].value)

        if isinstance(item, Void):
            throwError(p, 3, 'IndexError: Index out of range ({})'
                             .format(p[3].value))
    else:
        throwError(p, 1, 'TypeError: "{}" object is not iterable'
                         .format(p[1].object_type))

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

lexer.ignore_line = False

lexer.def_depth = -1
lexer.def_in = False
lexer.def_list = []

lexer.returned = False
lexer.ret_value = Void(obj_type='Void')

lexer.local_scope = []
lexer.current_scope = 0

lexer.local_scope.append({
    'types': Builtins.types,
    'methods': {},
    'names': Builtins.names
})

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

for line in code:
    if line.lstrip(' ').lstrip('\t').startswith('//')\
       or line.rstrip('\n') == '':
        continue

    if not lexer.def_in or line.rstrip('\n') == 'end':
        parser.parse(line)
    else:
        lexer.def_list[lexer.def_depth]['code'].append(line.lstrip(' ')
                                                           .lstrip('\t'))
