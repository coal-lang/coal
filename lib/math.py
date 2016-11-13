##
 # Standard Library: Math
 #
 # author William F. de Araújo
 # version 0.1
##

from stdlib import throwError, CoalModule, CoalInt, CoalFloat
import math


class _stdlib_math(CoalModule):
    def __init__(self):
        super(self.__class__, self).__init__('stdlib.math', {
            'sqrt:': self._method_sqrt_
        })

    def _method_sqrt_(self, number):
        if not isinstance(number, CoalInt)\
           and not isinstance(number, CoalFloat):
            throwError('TypeError: "math sqrt:" takes "Int" or'
                       ' "Float".')

        return CoalFloat(math.sqrt(number.value))
