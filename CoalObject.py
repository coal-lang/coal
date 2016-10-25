#!/usr/env/bin python
#: vim set encoding=utf-8 :
##
 # Stove
 # Coal interpreter prototype
 #
 # Module: Built-in Objects
 # version 0.1
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

    def call(self, name, arg=None, kwargs=None):
        if name in self.methods:
            if arg is None:
                return getattr(self, '_method_{}'.format(name))()
            elif kwargs is None:
                return getattr(self, '_method_{}'.format(name))(arg)
            else:
                return getattr(self, '_method_{}'.format(name))(arg, kwargs)
        elif name in self.attributes:
            return self.attributes[name]
        else:
            throwMethodError('"{}" object has no method/attribute "{}".'
                             .format(type(self).__name__, name))
            sys.exit(1)

    def repr(self, as_type):
        return self.repr_as[as_type]()


# Void
class Void(Object):
    def __init__(self, of_type=None):
        if of_type is None:
            super(self.__class__, self).__init__('Void', 'void', 'Void')
        else:
            super(self.__class__, self).__init__('Void',
                                                 'void',
                                                 of_type.obj_type)

        self.repr_as = {
            'String': lambda: String('Void({})'.format(self.value))
        }


# Builtins!
class _Builtins(Object):
    methods = [
        'print',
        'chr',
        'ord'
    ]

    def __init__(self):
        super(self.__class__, self).__init__('Builtins', None, None)

    def _method_print(self, arg):
        _value = arg

        if isinstance(_value, String):
            print(_value.value)
        else:
            print(_value.repr('String').value)

    def _method_chr(self, arg):
        _value = arg

        if isinstance(_value, Int):
            return String(chr(_value.value))
        else:
            throwError('TypeError: Built-in method "chr" takes "Int".')

    def _method_ord(self, arg):
        _value = arg

        if isinstance(_value, String):
            return Int(ord(_value.value))
        else:
            throwError('TypeError: Built-in method "ord" takes "String".')

Builtins = _Builtins()


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
        'concat',
        'stringToUppercase',
        'stringToLowercase',
        'stringAfterReplacing',
        'stringAfterTrimming'
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

    def _method_concat(self, arg):
        return String(self.value + arg.repr('String').value)

    def _method_stringToUppercase(self):
        return String(self.value.upper())

    def _method_stringToLowercase(self):
        return String(self.value.lower())

    def _method_stringAfterReplacing(self, arg, kwargs):
        _old = arg

        if 'with' in kwargs:
            _with = kwargs['with']

        else:
            throwWrongCallError(self, 'stringAfterReplacing')

        if 'times' not in kwargs:
            return String(self.value.replace(_old.repr('String').value,
                                             _with.repr('String').value))
        else:
            _times = kwargs['times']

            if not isinstance(_times, Int):
                throwError('TypeError: String method "stringAfterReplacing"\'s'
                           ' argument "times" takes "Int".')

            return String(self.value.replace(_old.repr('String').value,
                                             _with.repr('String').value,
                                             _times.value))

    def _method_stringAfterTrimming(self, arg):
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

    def getItem(self, index):
        if index < len(self.value):
            return self.value[index]
        else:
            return Void()
