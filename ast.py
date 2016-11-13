#: vim set encoding=utf-8 :
##
 # Coal
 # Python implementation of the Coal language
 #
 # Module: Abstract syntax-tree
 # version 0.21
##

import sys
# import copy

from stdlib import *

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

    self_ = None

    scope = None

    flow = False
    flow_next = False
    flow_break = False

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
    # Import
    # TODO: Import user-created modules
    if isinstance(stmt, Import):
        name = ExecuteCoal(stmt.name, scope).value

        if stmt.alias is not None:
            alias = stmt.alias
        else:
            alias = name

        if name in Builtins.modules:
            scope['names'][alias] = Builtins.modules[name]()
        else:
            throwError(0, 0, 'ImportError: Can\'t find module "{}"'
                       .format(name))

    # Call
    elif isinstance(stmt, LocalMethodCall):
        selectors = stmt.selectors
        selector_args = list(stmt.selector_args)

        for i in range(len(selector_args)):
            selector_args[i] = ExecuteCoal(selector_args[i], scope)

        if selectors in Builtins.public:
            return Builtins.call(selectors, selector_args)
        elif selectors in scope['methods']:
            if g.scope_depth == 0:
                n_scope = {
                    'types': dict(Builtins.types),
                    'methods': dict(scope['methods']),
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

            g.scope_depth -= 1
    elif isinstance(stmt, ObjectMethodCall):
        obj = ExecuteCoal(stmt.object, scope)
        selectors = stmt.selectors
        selector_args = list(stmt.selector_args)

        for i in range(len(selector_args)):
            selector_args[i] = ExecuteCoal(selector_args[i], scope)

        return obj.call(selectors, selector_args)
    elif isinstance(stmt, TypeCall):
        _type = stmt.type
        selectors = stmt.selectors
        selector_args = []

        if stmt.selector_args is not None:
            selector_args = list(stmt.selector_args)

            for i in range(len(selector_args)):
                selector_args[i] = ExecuteCoal(selector_args[i], scope)

        n_scope = {
            'types': dict(Builtins.types),
            'methods': {},
            'names': dict(Builtins.names)
        }

        # TODO: Currently, an empty instance of "_type_{...}" is created to
        # call an internal CoalTypeInit and do the "add arguments to scope"
        # thing, then the "real" new CoalObject instance is created and the
        # suite is called. Perhaps that's not the right way to do it, as it
        # creates an extra, unneeded(?), object. I think I should change
        # the structure of user-created types (and instances).

        defs = scope['types'][_type](selectors, n_scope, selector_args)
        suite, nscope = defs

        if _type in scope['types']:
            new_obj = scope['types'][_type]

            for st in suite:
                g.self_ = new_obj

                if isinstance(st, SelfAssign):
                    new_obj.attributes[st.name] = ExecuteCoal(st.value, nscope)
                else:
                    ExecuteCoal(st, scope)

            g.self_ = None
            return new_obj

    elif isinstance(stmt, NameFromSelf):
        if g.self_ is None:
            throwError(0, 0, 'Call to "self" from outside a type constructor.')

        if stmt.name not in g.self_.public:
            throwError(0, 0,
                       'NameError: Unknown name "{}"'
                       .format(stmt.name))

        return g.self_.public[stmt.name]

    # Name
    elif isinstance(stmt, NameDef):
        value = ExecuteCoal(stmt.value, scope)
        builtin_types = Builtins.types

        if stmt.type in builtin_types:
            scope['names'][stmt.name] =\
                builtin_types[stmt.type]['init'](value.value,
                                                 value.object_type)
        elif stmt.type in scope['types']:
            if value.object_type != stmt.type:
                throwError(0, 0, 'TypeError: Unknown value type for "{}": {}'
                           .format(stmt.type, value.object_type))

            scope['names'][stmt.name] = value

    elif isinstance(stmt, NameDefEmpty):
        if stmt.type in scope['types']\
           or stmt.type == 'Any':
            scope['names'][stmt.name] = CoalVoid(obj_type=stmt.type)
        else:
            throwError(0, 4, 'TypeError: Unknown type "{}"'.format(stmt.type))

    # Assignment
    elif isinstance(stmt, NameAssign):
        value = ExecuteCoal(stmt.value, scope)

        if stmt.name not in scope['names']:
            throwError(0, 1, 'NameError: Unknown name "{}"'.format(stmt.name))

        if isinstance(scope['names'][stmt.name], CoalVoid):
            var_type = scope['names'][stmt.name].value

            if var_type != 'Any'\
               and var_type != value.object_type:
                throwError(0, 3, 'TypeError: Wrong value type for Void({}): {}'
                                 .format(var_type, stmt.value.object_type))
        else:
            var_type = scope['names'][stmt.name].object_type

            if var_type != value.object_type:
                throwError(0, 3, 'TypeError: Wrong value type for {}: {}'
                                 .format(var_type, value.object_type))

        if stmt.mode == '=':
            scope['names'][stmt.name] = value
        elif stmt.mode == '+=':
            scope['names'][stmt.name].value += value.value
        elif stmt.mode == '-=':
            scope['names'][stmt.name].value -= value.value
        elif stmt.mode == '*=':
            scope['names'][stmt.name].value *= value.value
        elif stmt.mode == '/=':
            scope['names'][stmt.name].value /= value.value
    elif isinstance(stmt, IterableItemAssign):
        index = ExecuteCoal(stmt.index, scope)
        value = ExecuteCoal(stmt.value, scope)

        if stmt.name not in scope['names']:
            throwError(0, 0,
                       'NameError: Unknown name "{}"'
                       .format(stmt.name))

        name = scope['names'][stmt.name]

        if not isinstance(name, CoalIterableObject):
            throwError(0, 0, 'Exception: "{}" object is not a writable'
                       ' iterable'.format(name.object_type))

        name.assign(index, value)

    # Type

    # TODO: Lists are fun!
    # [ ] Implement private properties.
    # [ ] Implement protected properties.

    elif isinstance(stmt, TypeDef):
        inits = {}
        public = {}
        protected = {}
        private = {}

        for st in stmt.suite:
            if isinstance(st, TypeInitDef):
                inits[st.selectors] = CoalTypeInit(
                    st.selectors,
                    st.selector_names,
                    st.selector_types,
                    st.selector_aliases,
                    st.suite
                )
            # elif isinstance(st, TypePublicDecl):
            #     for pst in st.suite:
            #         if isinstance(pst, NameDef):
            #             public[stmt.name] = ExecuteCoal(stmt.value, scope)
            #         elif isinstance(pst, FuncDef):
            #             public[stmt.selectors] = CoalFunction(
            #                 stmt.selectors,
            #                 stmt.selector_names,
            #                 stmt.selector_types,
            #                 stmt.selector_aliases,
            #                 stmt.return_type,
            #                 stmt.suite,
            #                 stmt.simple
            #             )
            #         else:
            #             throwError(0, 0, 'Exception: What are you trying to'
            #                        ' do inside a type definition besides...'
            #                        ' A type definition?')

        scope['types'][stmt.name] = CoalType(
            stmt.name,
            inits,
            public,
            protected,
            private
        )

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
        test = ExecuteCoal(stmt.test, scope)

        if test.value and not isinstance(test.value, CoalVoid):
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

    # Loop
    elif isinstance(stmt, ForBlock):
        g.flow = True

        start = ExecuteCoal(stmt.start, scope)
        end = ExecuteCoal(stmt.end, scope)

        if stmt.interval is not None:
            interval = ExecuteCoal(stmt.interval, scope)
        else:
            interval = CoalInt(1)

        if not isinstance(start, CoalInt)\
           or not isinstance(end, CoalInt)\
           or (stmt.interval is not None
               and not isinstance(interval, CoalInt)):
            throwError(0, 0, 'TypeError: The values for "start", '
                             '"end" and "interval" must be "Int".')

        if stmt.name in scope['names']:
            var_type = scope['names'][stmt.name].object_type

            if var_type != 'Void(Any)' and var_type != 'Int':
                throwError(0, 3, 'TypeError: Wrong value type for {}: Int'
                                 .format(var_type))
        else:
            i = CoalInt(start.value)
            scope['names'][stmt.name] = i

            while i.value <= end.value:
                scope['names'][stmt.name].value = i.value

                for st in stmt.suite:
                    if g.flow_next:
                        g.flow_next = False
                        break
                    elif g.flow_break:
                        g.flow_break = False
                        return

                    ExecuteCoal(st, scope)

                i.value += interval.value

            del scope['names'][stmt.name]

        g.flow = False
    elif isinstance(stmt, EachBlock):
        g.flow = True

        iterable = ExecuteCoal(stmt.iterable, scope)

        if not isinstance(iterable, CoalIterableObject):
            throwError(0, 0, 'TypeError: "{}" object is not iterable.'
                             .format(iterable.object_type))

        if stmt.name in scope['names']:
            var_type = scope['names'][stmt.name].object_type
        else:
            scope['names'][stmt.name] = CoalVoid(obj_type='Any')

            length = iterable.call('length:', []).value
            i = CoalInt(0)

            while i.value < length:
                scope['names'][stmt.name] = iterable.iter(i)

                for st in stmt.suite:
                    if g.flow_next:
                        g.flow_next = False
                        break
                    elif g.flow_break:
                        g.flow_break = False
                        return

                    ExecuteCoal(st, scope)

                i.value += 1

            del scope['names'][stmt.name]

        g.flow = False
    elif isinstance(stmt, WhileBlock):
        g.flow = True

        test = ExecuteCoal(stmt.test, scope)

        while test.value:
            for st in stmt.suite:
                if g.flow_next:
                    g.flow_next = False
                    break
                elif g.flow_break:
                    g.flow_break = False
                    return

                ExecuteCoal(st, scope)

            test = ExecuteCoal(stmt.test, scope)

        g.flow = False
    elif isinstance(stmt, FlowBreak):
        if not g.flow:
            throwError('SyntaxError: Invalid syntax: "break".')

        g.flow_break = True
    elif isinstance(stmt, FlowNext):
        if not g.flow:
            throwError('SyntaxError: Invalid syntax: "next".')

        g.flow_next = True

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
                                 'ExprNotEqual',
                                 'ExprGreater',
                                 'ExprLess',
                                 'ExprEqualGreater',
                                 'ExprEqualLess']:
        a = ExecuteCoal(stmt.a, scope)
        b = ExecuteCoal(stmt.b, scope)

        # a_type = a.object_type
        # b_type = b.object_type

        # if all(a_type != t for t in ('Int', 'Float'))\
        #    or all(b_type != t for t in ('Int', 'Float')):
        #     throwError(0, 0, 'TypeError: Invalid types for "+": {}, {}'
        #                      .format(a_type, b_type))

        expr_type = type(stmt).__name__

        if expr_type == 'ExprAddition':
            result = a.value + b.value
        elif expr_type == 'ExprSubtraction':
            result = a.value - b.value
        elif expr_type == 'ExprMultiplication':
            result = a.value * b.value
        elif expr_type == 'ExprDivision':
            result = a.value / b.value
        elif expr_type == 'ExprModulo':
            result = a.value % b.value
        elif expr_type == 'ExprBitAnd':
            result = a.value & b.value
        elif expr_type == 'ExprBitOr':
            result = a.value | b.value
        elif expr_type == 'ExprBitXor':
            result = a.value ^ b.value
        elif expr_type == 'ExprBitShiftR':
            result = a.value >> b.value
        elif expr_type == 'ExprBitShiftL':
            result = a.value << b.value
        elif expr_type == 'ExprEqual':
            result = 'true' if a.value == b.value else 'false'
        elif expr_type == 'ExprNotEqual':
            result = 'false' if a.value == b.value else 'true'
        elif expr_type == 'ExprGreater':
            result = 'true' if a.value > b.value else 'false'
        elif expr_type == 'ExprLess':
            result = 'true' if a.value < b.value else 'false'
        elif expr_type == 'ExprEqualGreater':
            result = 'true' if a.value >= b.value else 'false'
        elif expr_type == 'ExprEqualLess':
            result = 'true' if a.value <= b.value else 'false'

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
            value = []
            for i in range(len(stmt.value)):
                value.append(ExecuteCoal(stmt.value[i], scope))

            return CoalList(value)

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


class TypeCall(CoalAST):
    def __init__(self,
                 _type,
                 selectors=None,
                 selector_args=None):
        self.type = _type
        self.selectors = selectors
        self.selector_args = selector_args


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
                 mode,
                 value):
        self.name = name
        self.mode = mode
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
            self.selectors += '{}:'.format(selector)


class FuncRet(CoalAST):
    def __init__(self,
                 value):
        self.value = value


# Type (TODO)
class TypeDef(CoalAST):
    def __init__(self,
                 name,
                 extends,
                 suite):
        self.name = name
        self.extends = extends
        self.suite = suite


class TypeInitDef(CoalAST):
    def __init__(self,
                 selector_names,
                 selector_types,
                 selector_aliases,
                 suite):
        self.selectors = ''
        self.selector_names = selector_names
        self.selector_types = selector_types
        self.selector_aliases = selector_aliases
        self.suite = suite

        for selector in selector_names:
            self.selectors += '{}:'.format(selector)


class SelfAssign(CoalAST):
    def __init__(self,
                 name,
                 value):
        self.name = name
        self.value = value


class NameFromSelf(CoalAST):
    def __init__(self,
                 name):
        self.name = name


class SelfRet(CoalAST):
    pass


class NameAsSelector(CoalAST):
    def __init__(self,
                 name):
        self.name = name


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


# Loop
class ForBlock(CoalAST):
    def __init__(self,
                 start,
                 end,
                 interval,
                 name,
                 suite):
        self.start = start
        self.end = end
        self.interval = interval
        self.name = name
        self.suite = suite


class EachBlock(CoalAST):
    def __init__(self,
                 iterable,
                 name,
                 suite):
        self.iterable = iterable
        self.name = name
        self.suite = suite


class WhileBlock(CoalAST):
    def __init__(self,
                 test,
                 suite):
        self.test = test
        self.suite = suite


class FlowBreak(CoalAST):
    pass


class FlowNext(CoalAST):
    pass


# Import
class Import(CoalAST):
    def __init__(self,
                 name,
                 alias=None):
        self.name = name
        self.alias = alias


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


class ExprEqualGreater(CoalAST):
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


class ExprEqualLess(CoalAST):
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
