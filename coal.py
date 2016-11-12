#!/usr/bin/env python3
#: vim set encoding=utf-8 :
##
 # Coal
 # Python implementation of the Coal language
 #
 # author William F. de Araújo
 # version 0.34
 # copyright MIT
##

# Imports
import sys
import re
import collections
import ply.yacc as yacc

import lexer

from ast import *

# Options
DEBUGGING = False


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
         | method_call
         | forblock
         | eachblock
         | whileblock
         | break
         | next
         | conditional
    '''
    p[0] = p[1]


# Variable definition
def p_var_def(p):
    '''
    var_def : VAR_DEF name WITH TYPE_NAME EQUALS value
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
    var_def : VAR_DEF name WITH TYPE_NAME ASK
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
    var_assign : name EQUALS value
               | name PLUSEQ value
               | name MINUSEQ value
               | name TIMESEQ value
               | name DIVEQ value
    '''

    var_name = p[1]
    var_mode = p[2]
    var_value = p[3]

    p[0] = NameAssign(
        var_name,
        var_mode,
        var_value
    )


def p_iterable_item_assign(p):
    '''
    iter_assign : name LBRACE value RBRACE EQUALS value
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
    type_def : CLASS TYPE_NAME AS TYPE_NAME stmts END
    '''

    # TODO: A nice list.
    # [ ] Make the process less confusing.
    # [ ] Add support for extending classes other than "Object".

    name = p[2]
    extends = p[4]

    if isinstance(p[5], list):
        suite = list(flatten(p[5]))
    else:
        suite = [p[5]]

    p[0] = TypeDef(
        name,
        extends,
        suite
    )


def p_type_init_def(p):
    '''
    type_init_def : INIT func_argdefs stmts END
    '''

    selectors = p[2]
    selector_names = [s[0] for s in selectors]
    selector_types = [s[1] for s in selectors]
    selector_aliases = [s[2] if len(s) > 2 else None for s in selectors]

    if isinstance(p[3], list):
        suite = list(flatten(p[3]))
    else:
        suite = [p[3]]

    p[0] = TypeInitDef(
        selector_names,
        selector_types,
        selector_aliases,
        suite
    )


# Method call
def p_method_call(p):
    '''
    method_call : LSQB value name call_arglist RSQB
                | LSQB value name RSQB
                | LSQB name call_arglist RSQB
                | LSQB name RSQB
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
        selectors = '{}:'.format(p[2])

        if len(p[3]):
            call_args = [v for v in list(flatten(p[3]))[:] if v != ':']
            selector_args = [call_args[0]]

            if len(call_args) > 2:
                for i in range(1, len(call_args), 2):
                    selectors += '{}:'.format(call_args[i])
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
            selectors += '{}:'.format(call_args[i])

            if len(call_args) > 1:
                selector_args.append(call_args[i+1])

        if isinstance(p[2], Name):
            if p[2].name == 'self':
                p[0] = SelfAssign(
                    selectors,
                    selector_args
                )

                return

        p[0] = ObjectMethodCall(
            p[2],
            selectors,
            selector_args
        )


def p_type_call(p):
    '''
    type_call : LSQB TYPE_NAME name call_arglist RSQB
              | LSQB TYPE_NAME RSQB
    '''

    if len(p) == 4:
        p[0] = TypeCall(
            p[2]
        )
    else:
        call_args = [v for v in list(flatten(p[4]))[:] if v != ':']
        selectors = '{}:'.format(p[3])
        selector_args = [call_args[0]]

        for i in range(1, len(call_args), 2):
            selectors += '{}:'.format(call_args[i])

            if len(call_args) > 1:
                selector_args.append(call_args[i+1])

        p[0] = TypeCall(
            p[2],
            selectors,
            selector_args
        )


def p_call_arglist(p):
    '''
    call_arglist : WITH special_value name call_arglist
                 | WITH special_value
    '''
    p[0] = p[1:]

    # This doesn't seem to work when we're dealing with Object instances:
    # if isinstance(p[len(p)-1], Object):
    #     p[0] = p[1:]
    # else:
    #     p[0] = p[1:len(p)-1] + p[len(p)-1]


def p_special_value(p):
    '''
    special_value : value
                  | AMPERSAND name
    '''

    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = NameAsSelector(p[2])


# Function definition
def p_func_def_simple(p):
    '''
    func_def : DEF name AS TYPE_NAME stmts END
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

    # Version history:
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
    func_argdef : name WITH LPAREN TYPE_NAME name RPAREN
                | name WITH LPAREN TYPE_NAME RPAREN
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


# Loop
def p_for(p):
    '''
    forblock : FOR value COMMA value COMMA value AS name stmts END
             | FOR value COMMA value AS name stmts END
    '''

    start = p[2]
    end = p[4]

    if len(p) == 10:
        interval = p[6]
        name = p[8]

        if isinstance(p[9], list):
            suite = list(flatten(p[9]))
        else:
            suite = [p[9]]
    else:
        interval = None
        name = p[6]

        if isinstance(p[7], list):
            suite = list(flatten(p[7]))
        else:
            suite = [p[7]]

    p[0] = ForBlock(
        start,
        end,
        interval,
        name,
        suite
    )


def p_each(p):
    '''
    eachblock : EACH value AS name stmts END
    '''

    p[0] = EachBlock(
        p[2],
        p[4],
        list(flatten(p[5]))
    )


def p_while(p):
    '''
    whileblock : WHILE value DO stmts END
    '''

    p[0] = WhileBlock(
        p[2],
        list(flatten(p[4]))
    )


def p_break(p):
    '''
    break : BREAK
    '''
    p[0] = FlowBreak()


def p_next(p):
    '''
    next : NEXT
    '''
    p[0] = FlowNext()


# Conditional
def p_conditional(p):
    '''
    conditional : ifblock END
                | ifblock elseblock END
                | ifblock elifblocks END
                | ifblock elifblocks elseblock END
    '''

    if len(p) == 3:  # IF test DO stmts END
        p[0] = IfBlock(
            p[1][0],
            list(flatten(p[1][1]))
        )
    elif len(p) == 4:  # (IfBlock ELSE stmts END)
        if p[2][0] is None:
            for i in range(1, len(p[2])):
                p[2][i] = (p[2][i][0], list(flatten(p[2][i][1])))

            p[0] = IfBlock(
                p[1][0],
                list(flatten(p[1][1])),
                p[2][1:]
            )
        else:
            p[0] = IfBlock(
                p[1][0],
                list(flatten(p[1][1])),
                else_suite=list(flatten(p[2]))
            )
    else:
        if len(p) > 3:
            else_suite = list(flatten(p[3]))
        else:
            else_suite = None

        for i in range(1, len(p[2])):
            p[2][i] = (p[2][i][0], list(flatten(p[2][i][1])))

        p[0] = IfBlock(
            p[1][0],
            list(flatten(p[1][1])),
            p[2][1:],
            else_suite
        )


def p_if_elif_block(p):
    '''
    ifblock : IF value DO stmts
    elifblock : ELIF value DO stmts
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
          | value NOT_EQUAL value
          | value GREATER value
          | value LESS value
          | value EQGREATER value
          | value EQLESS value
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
    elif p[2] == '!=':
        p[0] = ExprNotEqual(p[1], p[3])
    elif p[2] == '>':
        p[0] = ExprGreater(p[1], p[3])
    elif p[2] == '<':
        p[0] = ExprLess(p[1], p[3])
    elif p[2] == '>=':
        p[0] = ExprEqualGreater(p[1], p[3])
    elif p[2] == '<=':
        p[0] = ExprEqualLess(p[1], p[3])


def p_value_uminus(p):
    '''
    value : MINUS value %prec UMINUS
    '''
    p[0] = type(p[2]).__class__(-p[2].value)


def p_value_list(p):
    '''
    value : LPAREN list_items RPAREN
          | LPAREN RPAREN
    '''

    if len(p) == 4:
        p[0] = List(p[2])
    else:
        p[0] = List([])


def p_value_group(p):
    '''
    value : LPAREN value RPAREN
    '''
    p[0] = p[2]


def p_value(p):
    '''
    value : OBJECT
          | method_call
          | type_call
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


def p_value_list_items(p):
    '''
    list_items : list_items COMMA value
               | list_items COMMA
               | value
    '''

    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = list(flatten(filter(lambda a: a != ',', p[1:])))


def p_value_name(p):
    '''
    value : name
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


def p_name(p):
    '''
    name : NAME
         | LETTER_NAME
    '''
    p[0] = p[1]


# Error rule for syntax errors
def p_error(p):
    throwError(p, 0, 'Syntax error: {}'.format(p.value))


# HACK: A simple REPL
if len(sys.argv) < 2:
    # We'll use readline to enable command history
    import readline
    readline.parse_and_bind('set editing-mode vi')

    # And tab completion
    keywords = ['let', 'def', 'if', 'elif', 'else', 'for', 'each', 'while',
                'break', 'next', 'return', 'type', 'end', 'help', 'copyright',
                'credits', 'license', 'quit']

    def completer(text, state):
        options = [i for i in keywords if i.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None

    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)

    # Build our parser
    lexer = lexer.lexer
    lexer.ast = []

    parser = yacc.yacc(optimize=True)

    # Greet the user, of course.
    print('Coal 0.34 (nightly, Nov 12 2016)')
    print('Type "help", "copyright", "credits" or "license" for more'
          ' information.')

    # REPL
    while True:
        try:
            code = input('>>> ')

            # Skip empty lines
            if code == '':
                continue

            # Keywords
            elif code == 'help':
                print('You can access the command history with the UP and'
                      ' DOWN arrows.')
                print('Use TAB to auto-complete keywords. Press TAB twice'
                      ' on an empty line to list all the available keywords.')
                print('You can check the online documentation at'
                      ' http://coal-lang.github.io/coal.')
                continue
            elif code == 'copyright':
                print('Copyright (c) 2016 William F.')
                print('All rights reserved.')
                continue
            elif code == 'credits':
                print('Thanks to @dgelessus and everyone in the Pythonista'
                      'community for supporting Coal development. See'
                      ' coal-lang.github.io/coal for more information.')
                continue
            elif code == 'license':
                print('Type [license] to see the full license text.')
                continue
            elif code == 'quit':
                print('Use [quit] or Ctrl-D (i.e. EOF) to exit.')
                continue

            # Check if we're entering a complex block
            elif any(code.lstrip().startswith(n) for n in ['def', 'if', 'for',
                                                           'each', 'while']):
                depth = 4

                while True:
                    # Automatic indentation (fancy!)
                    readline.set_startup_hook(
                        lambda: readline.insert_text(' ' * depth)
                    )

                    try:
                        line = input('... ')
                    finally:
                        readline.set_startup_hook()

                    # Skip empty lines
                    if line.lstrip() == '':
                        continue

                    # Handle multiple blocks
                    elif any(line.lstrip().startswith(n) for n in ['def',
                                                                   'if',
                                                                   'for',
                                                                   'each',
                                                                   'while']):
                        depth += 4
                    elif any(line.lstrip().startswith(n) for n in ['elif',
                                                                   'else']):
                        pass
                    else:
                        depth = len(line) - len(line.lstrip())

                    # Restore newline
                    line += '\n'

                    # Insert the line on the block
                    code += line

                    if line.lstrip().startswith('end'):
                        if depth == 0:
                            parser.parse(code)
                            break
                        else:
                            depth -= 4
            else:
                parser.parse(code)

            # Execute the block
            for stmt in lexer.ast:
                ExecuteCoal(stmt)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            continue
        except EOFError:
            # Exit on CTRL-D
            sys.exit()

# Build the parser
test_file = open(sys.argv[1], 'r', encoding='utf-8')
src = test_file.read()
test_file.close()

# lexer = lexer.IndentLexer()
lexer = lexer.lexer
lexer.ast = []

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

for stmt in lexer.ast:
    ExecuteCoal(stmt)
