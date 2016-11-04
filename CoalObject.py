#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # Module: Built-in Objects
 # version 0.2
##

# Imports
import sys


# Utils
def throwMethodError(message):
    print('MethodError: {}'.format(message))
    sys.exit(1)


def throwWrongCallError(obj, method):
    throwMethodError('Wrong call to method "{}" of object "{}".'
                     .format(method, type(obj).__name__))
    sys.exit(1)


def throwTypeError(obj, obj_type):
    print('TypeError: Wrong type of value for object "{}": {}.'
          .format(obj, obj_type))
    sys.exit(1)


def throwError(message):
    print('{}'.format(message))
    sys.exit(1)


# Basic object
class CoalObject(object):
    methods = []

    def __init__(self, obj_type, type, value):
        self.object_type = obj_type
        self.type = type
        self.value = value

        self.attributes = {}

        self.repr_as = {
            'String': lambda: CoalString(self.value),
            'Raw': lambda: CoalString(self.value)
        }

    def call(self, selectors, args):
        if selectors in self.methods:
            return getattr(self, '_method_{}'.format(selectors))(*args)
        elif selectors in self.attributes:
            return self.attributes[selectors]
        else:
            throwMethodError('"{}" object has no method/attribute "{}".'
                             .format(type(self).__name__, selectors))
            sys.exit(1)

    def repr(self, as_type):
        return self.repr_as[as_type]()

    def _method_length_(self):
        return CoalInt(len(self.value))


# Sub-types
class CoalIterableObject(CoalObject):
    def __init__(self, *args):
        CoalObject.__init__(self, *args)

    def iter(self, start, end=None):
        try:
            if end is None:
                return self.value[start.value]
            else:
                return self.__class__(self.value[start.value:end.value])
        except:
            return CoalVoid()

    def assign(self, index, value):
        if index.value == len(self.value) + 1:
            self.value.append(value)
        elif index.value <= len(self.value) - 1:
            self.value[index.value] = value
        else:
            throwError('IndexError: List assignment index out of range.')

    def _method_iterate_(self):
        return CoalList([CoalInt(i) for i in range(self.call('length_', []).value)])


# Void
class CoalVoid(CoalObject):
    def __init__(self, of_type=None, obj_type=None):
        if of_type is None:
            if obj_type is not None:
                super(self.__class__, self).__init__('Void', 'void', obj_type)
            else:
                super(self.__class__, self).__init__('Void', 'void', 'Void')
        else:
            super(self.__class__, self).__init__('Void',
                                                 'void',
                                                 of_type.object_type)

        self.repr_as = {
            'String': lambda: CoalString('Void({})'.format(self.value))
        }


class CoalBool(CoalObject):
    def __init__(self, value, obj_type=None):
        try:
            if str(value).lower() == 'true':  # TODO: Fix this fix.
                boole = True
            else:
                boole = False

            super(self.__class__, self).__init__('Bool',
                                                 value,
                                                 boole)

            self.repr_as = {
                'String': lambda: CoalString('Bool({})'.format(value))
            }
        except:
            throwTypeError('Bool', obj_type)


# Function
class CoalFunction(object):
    def __init__(self, selectors, names, types, aliases, rtype, suite,
                 simple=False):
        self.selectors = selectors
        self.names = names
        self.types = types
        self.aliases = aliases
        self.rtype = rtype
        self.suite = suite
        self.simple = simple

    def __call__(self, scope, args):
        if len(args) < len(self.names) and not self.simple:
            throwError('Exception: Wrong argument count for {}.'
                       .format(self.selectors))

        for i in range(len(args)):
            if args[i].object_type != self.types[i]:
                throwError('TypeError: Wrong argument type for "{}": "{}"'
                           .format(self.selectors, args[i].object_type))

            if self.aliases[i] is not None:
                scope['names'][self.aliases[i]] = args[i]
            else:
                scope['names'][self.names[i]] = args[i]

        return (self.suite, scope, self.rtype)


# Integer
class CoalInt(CoalObject):
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('Int',
                                                 'int',
                                                 int(value))
        except:
            throwTypeError('Int', obj_type)


# Float
class CoalFloat(CoalObject):
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('Float',
                                                 'float',
                                                 float(value))
        except:
            throwTypeError('Float', obj_type)


# String
class CoalString(CoalObject):
    methods = [
        'length_',
        'concat_',
        'toUpper_',
        'toLower_',
        'replace_with_',
        'replace_with_times_',
        'trim_',
        'stringAfterReplacing_with_',
        'stringAfterReplacing_with_times_',
        'stringAfterTrimming_'
    ]

    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('String',
                                                 'string',
                                                 str(value))

            self.repr_as['Raw'] = lambda: CoalString('"{}"'.format(self.value))
        except:
            throwTypeError('String', obj_type)

    def iter(self, start, end=None):
        try:
            if end is None:
                return CoalString(self.value[start.value])
            else:
                return CoalString(self.value[start.value:end.value])
        except:
            return CoalVoid()

    def _method_concat_(self, arg):
        return CoalString(self.value + arg.repr('String').value)

    def _method_toUpper_(self):
        return CoalString(self.value.upper())

    def _method_toLower_(self):
        return CoalString(self.value.lower())

    def _method_replace_with_(self, old, new):
        self.value.replace(old.repr('String').value,
                           new.repr('String').value)

    def _method_replace_with_times_(self, old, new, times):
        if not isinstance(times, CoalInt):
            throwError('TypeError: String method "replace:with:times:"'
                       ' takes "times:" as "Int".')

        self.value.replace(old.repr('String').value,
                           new.repr('String').value,
                           times.value)

    def _method_stringAfterReplacing_with_(self, old, new):
        return CoalString(self.value.replace(old.repr('String').value,
                                             new.repr('String').value))

    def _method_stringAfterReplacing_with_times(self, old, new, times):
        if not isinstance(times, CoalInt):
            throwError('TypeError: String method "stringAfterReplacing:with'
                       'times:" takes "times:" as "Int".')

        return CoalString(self.value.replace(old.repr('String').value,
                                             new.repr('String').value,
                                             times.value))

    def _method_stringAfterTrimming_(self, arg):
        _value = arg

        return CoalString(self.value.replace(_value.value, ''))


# List
class CoalList(CoalIterableObject):
    methods = [
        'length_',
        'iterate_',
        'append_',
        'update_'
    ]

    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('List',
                                                 'list',
                                                 list(value))

            self.repr_as['String'] = lambda: CoalString('List({})'.format(
                ', '.join([str(n.repr('Raw').value) for n in self.value]))
            )
            self.repr_as['Raw'] = self.repr_as['String']
        except:
            throwTypeError('List', obj_type)

    def _method_append_(self, arg):
        self.value.append(arg)

    def _method_update_(self, arg):
        if not isinstance(arg, CoalIterableObject):
            throwError('TypeError: Object "{}" is not iterable.'
                       .format(arg.object_type))

        for i in range(arg.call('length_', []).value):
            self.value.append(arg.iter(CoalInt(i)))


# Builtins!
class CoalBuiltin(CoalObject):
    methods = [
        'print_',
        'chr_',
        'ord_'
    ]

    types = {
        'Void': {
            'init': CoalVoid
        },
        'Bool': {
            'init': CoalBool
        },
        'Int': {
            'init': CoalInt
        },
        'Float': {
            'init': CoalFloat
        },
        'String': {
            'init': CoalString
        },
        'List': {
            'init': CoalList
        }
    }

    names = {}

    def __init__(self):
        super(self.__class__, self).__init__('Builtins', None, None)

    def _method_print_(self, arg):
        _value = arg

        if isinstance(_value, CoalString):
            print(_value.value)
        else:
            print(_value.repr('String').value)

    def _method_chr_(self, arg):
        _value = arg

        if isinstance(_value, CoalInt):
            return CoalString(chr(_value.value))
        else:
            throwError('TypeError: Built-in method "chr" takes "Int".')

    def _method_ord_(self, arg):
        _value = arg

        if isinstance(_value, CoalString):
            return CoalInt(ord(_value.value))
        else:
            throwError('TypeError: Built-in method "ord" takes "String".')
