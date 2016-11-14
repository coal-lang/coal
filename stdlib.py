#: vim set encoding=utf-8 :
##
 # Coal
 # Python implementation of the Coal language
 #
 # Module: Standard Library
 # version 0.22
##

# Imports
import sys
# import copy


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

# TODO: It's actually a list:
# [x] Change "_" in method calls to ":" (since you can use "_" in names).
# [ ] Implement private properties.
# [ ] Implement protected properties.

class CoalObject(object):
    def __init__(self, obj_type, type, value):
        self.object_type = obj_type
        self.type = type
        self.value = value

        self.public = [
            'length:'
        ]
        self.protected = []
        self.private = []

        self.methods = {
            'length:': self._method_length_
        }
        self.attributes = {}

        self.repr_as = {
            'String': lambda: CoalString(self.value),
            'Raw': lambda: CoalString(self.value)
        }

    def call(self, selectors, args):
        if selectors in self.public:
            result = self.methods[selectors](*args)

            if result is None:
                return CoalVoid()
            else:
                return result
        elif selectors[:-1] in self.public:
            if len(args) == 0:
                return self.attributes[selectors[:-1]]
            else:
                self.attributes[selectors[:-1]] = args[0]
        else:
            throwMethodError('"{}" object has no method/attribute "{}".'
                             .format(self.object_type, selectors))
            sys.exit(1)

    def repr(self, as_type):
        return self.repr_as[as_type]()

    def _method_length_(self):
        return CoalInt(len(self.value))


# Sub-types
class CoalModule(CoalObject):
    def __init__(self, name, attributes={}, methods={}):
        CoalObject.__init__(self, name, None, None)

        for attribute in attributes.keys():
            self.public.append(attribute)

        for method in methods.keys():
            self.public.append(method)

        self.attributes.update(attributes)
        self.methods.update(methods)

        self.repr_as['String'] = lambda: CoalString('Module({})'
                                                    .format(self.object_type))


class CoalIterableObject(CoalObject):
    def __init__(self, *args):
        CoalObject.__init__(self, *args)

        # self.public = list(self.public) + [
        self.public += [
            'iterate:'
        ]

        # self.methods = copy.deepcopy(self.methods)
        self.methods.update({
            'iterate:': self._method_iterate_
        })

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
        return CoalList([
            CoalInt(i) for i in range(self.call('length:', []).value)
        ])


# Void
class CoalVoid(CoalObject):
    def __init__(self, of_type=None, obj_type=None):
        if of_type is None:
            if obj_type is not None:
                super(self.__class__, self).__init__('Void({})'
                                                     .format(obj_type),
                                                     'void',
                                                     obj_type)
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


# Type

# TODO: Another list!
# [ ] Optimize the whole initialization process.
# [ ] Implement "repr".

class CoalType(CoalObject):
    def __init__(self, name, inits={}, public={}, protected={}, private={}):
        super(self.__class__, self).__init__(name,
                                             'object',
                                             None)

        self.inits = inits
        self.public += public
        self.attributes = self.public
        self.protected.update(protected)
        self.private.update(private)

    def __call__(self, selectors, scope, args):
        if selectors in self.inits:
            return self.inits[selectors](scope, args)
        else:
            throwError('MethodError: "{}" type has no'
                       ' constructor "{}"'
                       .format(self.object_type, selectors))


class CoalTypeInit(CoalObject):
    def __init__(self, selectors, names, types, aliases, suite):
        self.selectors = selectors
        self.names = names
        self.types = types
        self.aliases = aliases
        self.suite = suite

        self._function = CoalFunction(
            selectors,
            names,
            types,
            aliases,
            'Void',
            suite
        )

    def __call__(self, scope, args):
        for i in range(len(args)):
            if args[i].object_type != self.types[i]:
                throwError('TypeError: Wrong argument type for "{}": "{}".'
                           .format(self.selectors, args[i].object_type))

            if self.aliases[i] is not None:
                scope['names'][self.aliases[i]] = args[i]
            else:
                scope['names'][self.names[i]] = args[i]

        return (self.suite, scope)


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
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('String',
                                                 'string',
                                                 str(value))

            # self.public = list(self.public) + [
            self.public += [
                'length:',
                'concat:',
                'format:',
                'toUpper:',
                'toLower:',
                'replace:with:',
                'replace:with:times:',
                'stringAfterReplacing:with:',
                'stringAfterReplacing:with:times:',
                'stringAfterTrimming:'
            ]

            # self.methods = copy.deepcopy(self.methods)
            self.methods.update({
                'length:': self._method_length_,
                'concat:': self._method_concat_,
                'format:': self._method_format_,
                'toUpper:': self._method_toUpper_,
                'toLower:': self._method_toLower_,
                'replace:with:': self._method_replace_with_,
                'replace:with:times:': self._method_replace_with_times_,
                'stringAfterReplacing:with:':
                self._method_stringAfterReplacing_with_,
                'stringAfterReplacing:with:times:':
                self._method_stringAfterReplacing_with_times_,
                'stringAfterTrimming:': self._method_stringAfterTrimming_
            })

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

    def _method_format_(self, arg):
        if not isinstance(arg, CoalIterableObject):
            throwError('TypeError: "{}" object is not iterable.'
                       .format(arg.object_type))

        names = []
        for i in range(arg.call('length:', []).value):
            names.append(arg.iter(CoalInt(i)).repr('String').value)

        return CoalString(self.value.format(*names))

    def _method_toUpper_(self):
        return CoalString(self.value.upper())

    def _method_toLower_(self):
        return CoalString(self.value.lower())

    def _method_replace_with_(self, old, new):
        self.value = self.value.replace(old.repr('String').value,
                                        new.repr('String').value)

    def _method_replace_with_times_(self, old, new, times):
        if not isinstance(times, CoalInt):
            throwError('TypeError: String method "replace:with:times:"'
                       ' takes "times:" as "Int".')

        self.value = self.value.replace(old.repr('String').value,
                                        new.repr('String').value,
                                        times.value)

    def _method_stringAfterReplacing_with_(self, old, new):
        return CoalString(self.value.replace(old.repr('String').value,
                                             new.repr('String').value))

    def _method_stringAfterReplacing_with_times_(self, old, new, times):
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
    def __init__(self, value, obj_type=None):
        try:
            super(self.__class__, self).__init__('List',
                                                 'list',
                                                 list(value))

            # self.public = list(self.public) + [
            self.public += [
                'append:',
                'update:'
            ]

            # self.methods = copy.deepcopy(self.methods)
            self.methods.update({
                'append:': self._method_append_,
                'update:': self._method_update_
            })

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

        for i in range(arg.call('length:', []).value):
            self.value.append(arg.iter(CoalInt(i)))


# Builtins!
class CoalBuiltin(CoalObject):
    def __init__(self):
        super(self.__class__, self).__init__('Builtins', None, None)

        sys.path.append('lib')

        # Standard Library
        from stdlib_core import _stdlib_core
        from stdlib_math import _stdlib_math

        self.modules = {
            'core': _stdlib_core,
            'math': _stdlib_math
        }

        # Built-in types
        self.types = {
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

        # Built-in names
        self.names = {}

        # Built-in methods
        # self.public = list(self.public) + [
        self.public += [
            'license:',
            'quit:',
            'print:',
            'print:sep:',
            'chr:',
            'ord:'
        ]

        # self.methods = copy.deepcopy(self.methods)
        self.methods.update({
            'license:': self._method_license_,
            'quit:': self._method_quit_,
            'print:': self._method_print_,
            'print:sep:': self._method_print_sep_,
            'chr:': self._method_chr_,
            'ord:': self._method_ord_
        })

    def _method_license_(self):
        print('''MIT License

Copyright (c) 2016 William F. de Araújo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.''')

    def _method_quit_(self, status=CoalInt(0)):
        sys.exit(status.value)

    def _method_print_(self, value=CoalString('')):
        if isinstance(value, CoalString):
            print(value.value)
        else:
            print(value.repr('String').value)

    def _method_print_sep_(self, value, sep):
        if not isinstance(sep, CoalString):
            throwError('TypeError: Builtin-method "print:sep:" takes "sep:"'
                       ' as "Int".')

        if isinstance(value, CoalString):
            sys.stdout.write(value.value + sep.value)
        else:
            sys.stdout.write(value.repr('String').value + sep.value)

    def _method_chr_(self, num):
        if isinstance(num, CoalInt):
            return CoalString(chr(num.value))
        else:
            throwError('TypeError: Built-in method "chr:" takes "Int".')

    def _method_ord_(self, char):
        if isinstance(char, CoalString):
            return CoalInt(ord(char.value))
        else:
            throwError('TypeError: Built-in method "ord:" takes "String".')
