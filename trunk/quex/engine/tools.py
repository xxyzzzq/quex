from   itertools       import izip, islice
import sys
import os

def r_enumerate(x):
    """Reverse enumeration."""
    return izip(reversed(xrange(len(x))), reversed(x))

def print_callstack(BaseNameF=False):
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
        if BaseNameF: name = os.path.basename(x[0])
        else:         name = x[0]
        print "%s%s:%s:%s(...)" % (" " * ((L-i)*4), name, x[1], x[2]) 

def pair_combinations(iterable):
    other = tuple(iterable)
    for i, x in enumerate(other):
        for y in islice(other, i+1, None):
            yield x, y

class UniformObject(object):
    __slots__ = ("_content", "_equal")
    def __init__(self, EqualCmp=lambda x,y: x!=y):
        self._content = -1   # '-1' Not yet set; 'None' set but not uniform
        self._equal   = EqualCmp

    def __ilshift__(self, NewContent):
        if   self._content == - 1:                   self._content = NewContent
        elif self._content is None:                  return
        elif self._equal(self._content, NewContent): self._content = None
        return self

    def fit(self, NewContent):
        if   self._content == -1:   return True
        elif self._content is None: return False
        return self._equal(self._content, NewContent)

    @property
    def content(self):
        if self._content == -1: return None
        else:                   return self._content

class TypedSet(set):
    def __init__(self, Cls):
        self.__element_class = Cls

    def add(self, X):
        assert isinstance(X, self.__element_class)
        set.add(self, X)

    def update(self, Iterable):
        for x in Iterable:
            assert isinstance(x, self.__element_class)
        set.update(self, Iterable)

class TypedDict(dict):
    def __init__(self, ClsKey=None, ClsValue=None):
        self.__key_class   = ClsKey
        self.__value_class = ClsValue

    def get(self, Key):
        assert self.__key_class is None or isinstance(Key, self.__key_class), \
               self._error_key(Key)
        return dict.get(self, Key)

    def __getitem__(self, Key):
        assert self.__key_class is None or isinstance(Key, self.__key_class), \
               self._error_key(Key)
        return dict.__getitem__(self, Key)

    def __setitem__(self, Key, Value):
        assert self.__key_class   is None or isinstance(Key, self.__key_class), \
               self._error_key(Key)
        assert self.__value_class is None or isinstance(Value, self.__value_class), \
               self._error_value(Key)
        return dict.__setitem__(self, Key, Value)

    def update(self, Iterable):
        # Need to iterate twice: 'list()' may be faster here then 'tee()'.
        if isinstance(Iterable, dict): iterable2 = Iterable.iteritems()
        else:                          Iterable = list(Iterable); iterable2 = Iterable.__iter__()

        for x in iterable2:
            assert isinstance(x, tuple)
            assert self.__key_class   is None or isinstance(x[0], self.__key_class), \
                   self._error_key(x[0])
            assert self.__value_class is None or isinstance(x[1], self.__value_class), \
                   self._error_value(x[1])

        dict.update(self, Iterable)

    def _error(self, ExpectedClass):
        return "TypedDict(%s, %s) expects %s" % \
                (self.__key_class.__name__, self.__value_class.__name__, \
                 ExpectedClass.__name__)

    def _error_key(self, Key):
        return "%s as a key. Found type='%s; value='%s';" % \
                (self._error(self.__key_class), Key.__class__.__name__, Key)

    def _error_value(self, Value):
        return "%s as a key. Found '%s'" % \
                (self._error(self.__value_class), Value.__class__.__name__)

