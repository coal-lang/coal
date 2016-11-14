#: vim set encoding=utf-8 :
##
 # Standard Library: Core
 #
 # author William F. de Araújo
 # version 0.1
##

from stdlib import throwError, CoalModule, CoalInt, CoalList
import sys


class _stdlib_core(CoalModule):
    def __init__(self):
        super(self.__class__, self).__init__(
            'stdlib.core',
            attributes={
                'version': CoalList((
                    CoalInt(sys.version_info.major),
                    CoalInt(sys.version_info.minor),
                    CoalInt(sys.version_info.micro)
                ))
            }
        )
