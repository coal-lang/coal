import collections
from ast import CoalAST


# flatten
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
