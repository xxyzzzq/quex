from itertools       import izip
import sys
import os

def r_enumerate(x):
    """Reverse enumeration."""
    return izip(reversed(xrange(len(x))), reversed(x))

def print_callstack():
    try:
        i = 2
        name_list = []
        while 1 + 1 == 2:
            x = sys._getframe(i).f_code
            name_list.append([x.co_filename, x.co_firstlineno, x.co_name])
            i += 1
    except:
        pass

    L = len(name_list)
    for i, x in r_enumerate(name_list):
        print "%s%s:%s(...)" % (" " * ((L-i)*4), os.path.basename(x[0]), x[2]) 
