from   quex.blackboard   import E_Values

from   itertools   import izip, islice
from   collections import deque
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
    def __init__(self, EqualCmp=lambda x,y: x==y, Initial=E_Values.UNASSIGNED):
        if isinstance(Initial, UniformObject):
            self._content = Initial._content
        else:
            self._content = Initial
        self._equal       = EqualCmp

    @staticmethod
    def from_iterable(Iterable, EqualCmp=lambda x,y: x==y):
        try:    initial = Iterable.next()
        except: return UniformObject(EqualCmp, Initial=E_Values.VOID)

        result = UniformObject(EqualCmp, Initial=initial)
        for x in Iterable:
            result <<= x
        return result

    def clone(self):
        result = UniformObject(self._equal)
        result._content = self._content
        return result

    def __ilshift__(self, NewContent):
        if isinstance(NewContent, UniformObject):    
            NewContent = NewContent._content

        if   E_Values.UNASSIGNED == self._content:       self._content = NewContent
        elif E_Values.VOID       == self._content:       pass
        elif E_Values.VOID       == NewContent:          self._content = E_Values.VOID
        elif not self._equal(self._content, NewContent): self._content = E_Values.VOID
        return self

    def fit(self, NewContent):
        if isinstance(NewContent, UniformObject):    
            NewContent = NewContent._content

        if   E_Values.UNASSIGNED == self._content: return True
        elif E_Values.VOID       == self._content: return False
        return self._equal(self._content, NewContent)

    @property
    def content(self):
        if   E_Values.UNASSIGNED == self._content: return None
        elif E_Values.VOID       == self._content: return None
        else:                                      return self._content

    def is_uniform(self):
        """If the content is UNASSIGNED or remained uniform, then this
           function returns 'True'. It returns 'False' if two different
           values have been shifted into it.
        """
        return E_Values.VOID != self._content

def _report_failed_assertion(i, thing, last_things, iterable_next_things):
    L = len(last_things)
    for k, thing in enumerate(last_things):
        print "[%i](before) \"%s\"" % (i - L + k, thing)

    print ">> [%i] Error: '%s'" % (i, thing.__class__.__name__)
    print ">> [%i] Error: '%s'" % (i, thing)

    for k in xrange(10):
        try:   thing = iterable_next_things.next()
        except StopIteration: break
        print "[%i](after) \"%s\"" % (i + k + 1, thing)

def _check_all(Iterable, Condition):
    if isinstance(Iterable, (int, long, str, unicode)):
        print "#Iterable is not really an iterable"
        return False

    last_things = deque()
    if isinstance(Iterable, (tuple, list)): iterable = Iterable.__iter__()
    else:                                   iterable = Iterable
    i = -1
    while 1 + 1 == 2:
        i     += 1
        try:   thing = iterable.next()
        except StopIteration: break

        if len(last_things) > 10: last_things.popleft()
        last_things.append(thing)
        if Condition(thing): continue
        _report_failed_assertion(i, thing, last_things, iterable)
        return False
    return True

def all_isinstance(List, Type):
    return _check_all(List, lambda element: isinstance(element, Type))

def none_isinstance(List, Type):
    return _check_all(List, lambda element: not isinstance(element, Type))

def none_is_None(List):
    return _check_all(List, lambda element: element is not None)

def typed(**_parameters_):
    """parameter=Type                --> isinstance(parameter, Type)
       parameter=(Type0, Type1, ...) --> isinstance(parameter, (Type0, Type1, ...))
       parameter=[Type]              --> (1) isinstance(parameter, list)
                                         (2) all_isinstance(parameter, Type)
       parameter=[Type0, Type1]      --> (1) isinstance(parameter, dict)
                                         (2) all_isinstance(parameter.keys(), Type0)
                                         (3) all_isinstance(parameter.keys(), Type1)
    """
    def check_types(_func_, _parameters_ = _parameters_):
        def modified(*arg_values, **kw):
            arg_names = _func_.func_code.co_varnames
            kw.update(zip(arg_names, arg_values))
            for name, type_d in _parameters_.iteritems():
                value = kw[name]
                if value is None:
                    assert (type_d is None) or (None in type_d)
                elif type(type_d) == tuple:
                    assert isinstance(value, type_d), \
                           "Parameter '%s' not one of '%s'" % (name, [x.__name__ for x in type_d])
                elif type(type_d) == list:
                    if len(type_d) == 1:
                        assert isinstance(value, list), \
                               "Parameter '%s' not one of '%s'" % (name, [x.__name__ for x in type_d])
                        assert all_isinstance(value, type_d[0]),
                               "Parameter list '%s' contains element not of of '%s'" % (name, type_d[0].__name__)
                    elif len(type_d) == 2:
                        assert isinstance(value, list), \
                               "Parameter '%s' not one of '%s'" % (name, [x.__name__ for x in type_d])
                        assert all_isinstance(value.iterkeys(), type_d[0]),
                               "Parameter list '%s' contains element not of of '%s'" % (name, type_d[0].__name__)
                        assert all_isinstance(value.itervalues(), type_d[1]),
                               "Parameter list '%s' contains element not of of '%s'" % (name, type_d[1].__name__)
                else:
                    assert isinstance(value, type_d), \
                           "Parameter '%s' not of '%s'" % (name, type_d.__name__)
            return _func_(**kw)
        return modified
    return check_types

def error_abstract_member():
    x = sys._getframe(i).f_code
    assert False, "Call to '%s'. Implementation in derived class." % x.co_name

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
               self._error_value(Value)
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
        print "####", isinstance(Value, long)
        return "%s as value. Found '%s'" % \
                (self._error(self.__value_class), Value.__class__.__name__)

