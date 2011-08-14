# Source: http://code.activestate.com/recipes/413486/
# Modified: (C) 2011 Frank-Rene Schaefer

def Enum(*names):
    assert names, "Empty enums are not supported"

    class EnumClass(object):
        __slots__ = names
        def __iter__(self):        return iter(constants)
        def __len__(self):         return len(constants)
        def __getitem__(self, i):  return constants[i]
        def __repr__(self):        return 'Enum' + str(names)
        def __str__(self):         return 'enum ' + str(constants)

    class EnumValue(object):
        """Enum values are **all unique** by means of the __cmp__ and the __eq__
           operator. To be used as keys for dictionaries (dict) they must 
           provide:
                        __hash__  to determine the 'bucket'.
                        __eq__    (better than __cmp__) to determine equality
                                  inside a bucket. 

           It is made sure, that only the same enumeration objects compare equal.
           The non-equal comparisons "<", ">", ">=", and "<=" shall trigger an
           assert if they are applied to objects from different enums or totally
           other typed objects.
        """
        __slots__ = ('__value')
        def __init__(self, value): 
            self.__value = value

        Value = property(lambda self: self.__value)
        EnumType = property(lambda self: EnumType)

        def __hash__(self):        
            return hash(self.__value)

        def __eq__(self, other):
            """Whatever the other may be, it is only equal if points to 
               the same enumeration value object.
            """
            if not hasattr(other, "EnumType"):      return False
            if not self.EnumType is other.EnumType: return False
            return self.__value == other.__value

        def __cmp__(self, other):
            """For 'sort' operations (such as in 'sorted') let the enum values
               always be smaller than other objects.
            """
            if not hasattr(other, "EnumType"):      return -1
            if not self.EnumType is other.EnumType: return -1 
            return cmp(self.__value, other.__value)

        def __invert__(self):      return constants[maximum - self.__value]
        def __nonzero__(self):     return bool(self.__value)
        def __repr__(self):        return str(names[self.__value])

    maximum   = len(names) - 1
    constants = [None] * len(names)
    for i, each in enumerate(names):
        val = EnumValue(i)
        setattr(EnumClass, each, val)
        constants[i] = val

    EnumType = EnumClass()
    return EnumType


