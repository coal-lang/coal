#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # Module: Abstract syntax-tree
 # version 0.2
##

import sys
from CoalObject import *

Builtins = CoalBuiltin()

# Globals
returned = False
ret_value = CoalVoid(obj_type='Void')

local_scope = []
current_scope = 0

local_scope.append({
    'types': dict(Builtins.types),
    'methods': {},
    'names': dict(Builtins.names)
})


class Globals(object):
    scope_depth = 0

g = Globals()


# Utils
def throwError(p, pos, message):
    '''
    Throw an error. (Do I need to explain more?)
    '''

    print('{}.'.format(message))
    sys.exit(1)


# Parse a statement
def ExecuteCoal(stmt, scope=local_scope[current_scope]):
    # Call
    if isinstance(stmt, LocalMethodCall):
        selectors = stmt.selectors
        selector_args = stmt.selector_args

        for i in range(len(selector_args)):
            selector_args[i] = ExecuteCoal(selector_args[i], scope)

        if selectors in Builtins.methods:
            return Builtins.call(selectors, selector_args)
        elif selectors in scope['methods']:
            if g.scope_depth == 0:
                n_scope = {
                    'types': dict(Builtins.types),
                    'methods': {},
                    'names': dict(Builtins.names)
                }
            else:
                n_scope = scope

            g.scope_depth += 1

            defs = scope['methods'][selectors](n_scope,
                                               selector_args)
            suite, n_scope, rtype = defs

            for st in suite:
                result = ExecuteCoal(st, n_scope)

                if isinstance(st, FuncRet):
                    if result.object_type != rtype:
                        throwError(0, 0,
                                   'TypeError: Invalid return type for "{}": '
                                   '"{}"'
                                   .format(rtype, result.object_type))

                    g.scope_depth -= 1
                    return result
    elif isinstance(stmt, ObjectMethodCall):
        obj = ExecuteCoal(stmt.object, scope)
        selectors = stmt.selectors
        selector_args = stmt.selector_args

        for i in range(len(selector_args)):
            selector_args[i] = ExecuteCoal(selector_args[i], scope)

        return obj.call(selectors, selector_args)

    # Name
    elif isinstance(stmt, NameDef):
        stmt.value = ExecuteCoal(stmt.value, scope)
        local_types = scope['types']

        if stmt.type in local_types:
            scope['names'][stmt.name] =\
                local_types[stmt.type]['init'](stmt.value.value, stmt.value.object_type)
    elif isinstance(stmt, NameDefEmpty):
        if stmt.type in scope['types']\
           or stmt.type == 'Any':
            scope['names'][stmt.name] = CoalVoid(obj_type=stmt.type)
        else:
            throwError(0, 4, 'TypeError: Unknown type "{}"'.format(stmt.type))

    # Assignment
    elif isinstance(stmt, NameAssign):
        stmt.value = ExecuteCoal(stmt.value, scope)

        if stmt.name not in scope['names']:
            throwError(0, 1, 'NameError: Unknown name "{}"'.format(stmt.name))

        if isinstance(scope['names'][stmt.name], CoalVoid):
            var_type = scope['names'][stmt.name].value

            if var_type != 'Any'\
               and var_type != stmt.value.object_type:
                throwError(0, 3, 'TypeError: Wrong value type for Void({}): {}'
                                 .format(var_type,
                                         stmt.value.object_type))

        scope['names'][stmt.name] = stmt.value
    elif isinstance(stmt, IterableItemAssign):
        stmt.index = ExecuteCoal(stmt.index, scope)
        stmt.value = ExecuteCoal(stmt.value, scope)

        if stmt.name not in scope['names']:
            throwError(0, 0,
                       'NameError: Unknown name "{}"'
                       .format(stmt.name))

        stmt.name = scope['names'][stmt.name]

        if not isinstance(stmt.name, CoalIterableObject):
            throwError(0, 0, 'Exception: "{}" object is not a writable iterable'
                       .format(stmt.name.object_type))

        stmt.name.assign(stmt.index, stmt.value)

    # Function
    elif isinstance(stmt, FuncDef):
        scope['methods'][stmt.selectors] = CoalFunction(
            stmt.selectors,
            stmt.selector_names,
            stmt.selector_types,
            stmt.selector_aliases,
            stmt.return_type,
            stmt.suite,
            stmt.simple
        )
    elif isinstance(stmt, FuncRet):
        return ExecuteCoal(stmt.value, scope)

    # Conditional
    elif isinstance(stmt, IfBlock):
        stmt.test = ExecuteCoal(stmt.test, scope)

        if stmt.test.value and not isinstance(stmt.test.value, CoalVoid):
            for st in stmt.suite:
                ExecuteCoal(st, scope)

            return

        if stmt.elif_blocks is not None:
            for block in stmt.elif_blocks:
                test = ExecuteCoal(block[0], scope)

                if test.value and not isinstance(test.value, CoalVoid):
                    for st in block[1]:
                        ExecuteCoal(st, scope)

                    return


        if stmt.else_suite is not None:
            for st in stmt.else_suite:
                ExecuteCoal(st, scope)

    # Expression
    elif type(stmt).__name__ in ['ExprAddition',
                                 'ExprSubtraction',
                                 'ExprMultiplication',
                                 'ExprDivision',
                                 'ExprModulo',
                                 'ExprBitAnd',
                                 'ExprBitOr',
                                 'ExprBitXor',
                                 'ExprBitShiftR',
                                 'ExprBitShiftL',
                                 'ExprEqual',
                                 'ExprGreater',
                                 'ExprLess']:
        stmt.a = ExecuteCoal(stmt.a, scope)
        stmt.b = ExecuteCoal(stmt.b, scope)

        a_type = stmt.a.object_type
        b_type = stmt.b.object_type

        # if all(a_type != t for t in ('Int', 'Float'))\
        #    or all(b_type != t for t in ('Int', 'Float')):
        #     throwError(0, 0, 'TypeError: Invalid types for "+": {}, {}'
        #                      .format(a_type, b_type))

        expr_type = type(stmt).__name__

        if expr_type == 'ExprAddition':
            result = stmt.a.value + stmt.b.value
        elif expr_type == 'ExprSubtraction':
            result = stmt.a.value - stmt.b.value
        elif expr_type == 'ExprMultiplication':
            result = stmt.a.value * stmt.b.value
        elif expr_type == 'ExprDivision':
            result = stmt.a.value / stmt.b.value
        elif expr_type == 'ExprModulo':
            result = stmt.a.value % stmt.b.value
        elif expr_type == 'ExprBitAnd':
            result = stmt.a.value & stmt.b.value
        elif expr_type == 'ExprBitOr':
            result = stmt.a.value | stmt.b.value
        elif expr_type == 'ExprBitXor':
            result = stmt.a.value ^ stmt.b.value
        elif expr_type == 'ExprBitShiftR':
            result = stmt.a.value >> stmt.b.value
        elif expr_type == 'ExprBitShiftL':
            result = stmt.a.value << stmt.b.value
        elif expr_type == 'ExprEqual':
            result = 'true' if stmt.a.value == stmt.b.value else 'false'
        elif expr_type == 'ExprGreater':
            result = 'true' if stmt.a.value > stmt.b.value else 'false'
        elif expr_type == 'ExprLess':
            result = 'true' if stmt.a.value < stmt.b.value else 'false'

        if type(result) == int:
            return CoalInt(result)
        elif type(result) == float:
            return CoalFloat(result)
        else:
            return CoalBool(result)

    # Value
    elif isinstance(stmt, Value):
        if isinstance(stmt, Name):
            if stmt.name not in scope['names']:
                throwError(0, 0,
                           'NameError: Unknown name "{}"'
                           .format(stmt.name))

            return scope['names'][stmt.name]
        elif isinstance(stmt, ItemFromIterable):
            iter_name = ExecuteCoal(stmt.name, scope)
            iter_start = ExecuteCoal(stmt.index, scope)

            if stmt.end is None:
                iter_end = None
            else:
                iter_end = ExecuteCoal(stmt.end, scope)

            return iter_name.iter(iter_start, iter_end)
        elif isinstance(stmt, Void):
            return CoalVoid(stmt.value)
        elif isinstance(stmt, Bool):
            return CoalBool(stmt.value)
        elif isinstance(stmt, Int):
            return CoalInt(stmt.value)
        elif isinstance(stmt, Float):
            return CoalFloat(stmt.value)
        elif isinstance(stmt, String):
            return CoalString(stmt.value)
        elif isinstance(stmt, List):
            for i in range(len(stmt.value)):
                stmt.value[i] = ExecuteCoal(stmt.value[i], scope)

            return CoalList(stmt.value)

    # Empty return
    return CoalVoid()


# For organization sake
class CoalAST(object):
    pass


# Call
class LocalMethodCall(CoalAST):
    def __init__(self,
                 selectors,
                 selector_args):
        self.selectors = selectors
        self.selector_args = selector_args


class ObjectMethodCall(CoalAST):
    def __init__(self,
                 _object,
                 selectors,
                 selector_args):
        self.object = _object
        self.selectors = selectors
        self.selector_args = selector_args


class ObjectPropertyCall(CoalAST):
    def __init__(self,
                 _object,
                 _property):
        self.object = _object
        self.property = _property


# Name
class NameDef(CoalAST):
    def __init__(self,
                 name,
                 _type,
                 value):
        self.name = name
        self.type = _type
        self.value = value


class NameDefEmpty(CoalAST):
    def __init__(self,
                 name,
                 _type):
        self.name = name
        self.type = _type


class NameAssign(CoalAST):
    def __init__(self,
                 name,
                 value):
        self.name = name
        self.value = value


class IterableItemAssign(CoalAST):
    def __init__(self,
                 name,
                 index,
                 value):
        self.name = name
        self.index = index
        self.value = value


# Function
class FuncDef(CoalAST):
    def __init__(self,
                 selector_names,
                 selector_types,
                 selector_aliases,
                 return_type,
                 suite,
                 simple=False):
        self.selectors = ''
        self.selector_names = selector_names
        self.selector_types = selector_types
        self.selector_aliases = selector_aliases
        self.return_type = return_type
        self.suite = suite
        self.simple = simple

        for selector in selector_names:
            self.selectors += '{}_'.format(selector)


class FuncRet(CoalAST):
    def __init__(self,
                 value):
        self.value = value


# Type (TODO)
class TypeDef(CoalAST):
    def __init__(self,
                 name,
                 suite):
        self.name = name
        self.suite = suite


class TypeDefExt(CoalAST):
    def __init__(self,
                 name,
                 ext_name,
                 suite):
        self.name = name
        self.ext_name = ext_name
        self.suite = suite


# Conditional
class IfBlock(CoalAST):
    def __init__(self,
                 test,
                 suite,
                 elif_blocks=None,
                 else_suite=None):
        self.test = test
        self.suite = suite
        self.elif_blocks = elif_blocks
        self.else_suite = else_suite


# Expression
class ExprAddition(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprSubtraction(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprMultiplication(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprDivision(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprModulo(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprEqual(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprExact(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprNotEqual(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprGreater(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprGreaterEqual(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprLess(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


class ExprLessEqual(CoalAST):
    def __init__(self,
                 a,
                 b):
        self.a = a
        self.b = b


# Value
class Value(CoalAST):
    pass


class Name(Value):
    def __init__(self,
                 name):
        self.name = name


class ItemFromIterable(Value):
    def __init__(self,
                 name,
                 index,
                 end=None):
        self.name = name
        self.index = index
        self.end = end


class Void(Value):
    def __init__(self,
                 value):
        self.value = value


class Bool(Value):
    def __init__(self,
                 value):
        self.value = value


class Int(Value):
    def __init__(self,
                 value):
        self.value = int(value)


class Float(Value):
    def __init__(self,
                 value):
        self.value = float(value)


class String(Value):
    def __init__(self,
                 value):
        self.value = str(value)


class List(Value):
    def __init__(self,
                 value):
        self.value = list(value)
