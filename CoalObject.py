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
class Object(object):
    methods = []

    def __init__(self, obj_type, type, value):
        self.object_type = obj_type
        self.type = type
        self.value = value

        self.attributes = {}

        self.repr_as = {
            'String': lambda: String(self.value),
            'Raw': lambda: String(self.value)
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


# Void
class Void(Object):
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
            'String': lambda: String('Void({})'.format(self.value))
        }


class Bool(Object):
    def __init__(self, value, obj_type=None):
        try:
            if value == 'true':
                boole = True
            else:
                boole = False

            super(self.__class__, self).__init__('Bool',
                                                 value,
                                                 boole)

            self.repr_as = {
                'String': lambda: String('Bool({})'.format(self.value))
            }
        except:
            throwTypeError('Bool', obj_type)


# Function
class Function(object):
    def __init__(self, code):
        self.code = code

    def __call__(self, *args):
        pass


# Integer
class Int(Object):
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('Int',
                                                 'int',
                                                 int(value))
        except:
            throwTypeError('Int', obj_type)


# Float
class Float(Object):
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('Float',
                                                 'float',
                                                 float(value))
        except:
            throwTypeError('Float', obj_type)


# String
class String(Object):
    methods = [
        'concat_',
        'stringToUppercase_',
        'stringToLowercase_',
        'stringAfterReplacing_with_',
        'stringAfterReplacing_with_times_'
        'stringAfterTrimming_'
    ]

    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('String',
                                                 'string',
                                                 str(value))

            self.attributes = {
                'length': Int(len(str(value)))
            }

            self.repr_as['Raw'] = lambda: String('"{}"'.format(self.value))
        except:
            throwTypeError('String', obj_type)

    def iter(self, start, end=None):
        try:
            if end is None:
                return String(self.value[start])
            else:
                return String(self.value[start:end])
        except:
            return Void()

    def _method_concat_(self, arg):
        return String(self.value + arg.repr('String').value)

    def _method_stringToUppercase_(self):
        return String(self.value.upper())

    def _method_stringToLowercase_(self):
        return String(self.value.lower())

    def _method_stringAfterReplacing_with_(self, old, new):
        return String(self.value.replace(old.repr('String').value,
                                         new.repr('String').value))

    def _method_stringAfterReplacing_with_times(self, old, new, times):
        if not isinstance(times, Int):
            throwError('TypeError: String method "stringAfterReplacing:with'
                       'times:"takes "times:" as "Int".')

        return String(self.value.replace(old.repr('String').value,
                                         new.repr('String').value,
                                         times.value))

    def _method_stringAfterTrimming_(self, arg):
        _value = arg

        return String(self.value.replace(_value.value, ''))


# List
class List(Object):
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('List',
                                                 'list',
                                                 list(value))

            self.attributes = {
                'length': Int(len(list(value)))
            }

            self.repr_as['String'] = lambda: String('List({})'.format(
                ', '.join([str(n.repr('Raw').value) for n in self.value]))
            )
            self.repr_as['Raw'] = self.repr_as['String']
        except:
            throwTypeError('List', obj_type)

    def iter(self, start, end=None):
        try:
            if end is None:
                return self.value[start]
            else:
                return self.value[start:end]
        except:
            return Void()


# Builtins!
class CoalBuiltin(Object):
    methods = [
        'print_',
        'chr_',
        'ord_'
    ]

    types = {
        'Void': {
            'init': Void
        },
        'Bool': {
            'init': Bool
        },
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
    }

    names = {}

    def __init__(self):
        super(self.__class__, self).__init__('Builtins', None, None)

    def _method_print_(self, arg):
        _value = arg

        if isinstance(_value, String):
            print(_value.value)
        else:
            print(_value.repr('String').value)

    def _method_chr_(self, arg):
        _value = arg

        if isinstance(_value, Int):
            return String(chr(_value.value))
        else:
            throwError('TypeError: Built-in method "chr" takes "Int".')

    def _method_ord_(self, arg):
        _value = arg

        if isinstance(_value, String):
            return Int(ord(_value.value))
        else:
            throwError('TypeError: Built-in method "ord" takes "String".')
