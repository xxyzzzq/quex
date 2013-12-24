from   quex.engine.tools        import error_abstract_member, \
                                       typed, \
                                       all_isinstance
from   quex.engine.misc.file_in import get_current_line_info_number

from   collections import namedtuple
from   copy        import deepcopy

import re

class SourceRef(namedtuple("SourceRef_tuple", ("file_name", "line_n"))):
    """A reference into source code:
    _______________________________________________________________________________
      
        file_name = Name of the file where the code is located.
        line_n    = Number of line where code is found.
    _______________________________________________________________________________
    """
    def __new__(self, FileName="<default>", LineN=0):
        assert isinstance(FileName, (str, unicode))
        assert isinstance(LineN, (int, long))
        return super(SourceRef, self).__new__(self, FileName, LineN)

    @staticmethod
    def from_FileHandle(Fh):
        if Fh != -1:
            if not hasattr(Fh, "name"): file_name = "<nameless stream>"
            else:                       file_name = Fh.name
            line_n = get_current_line_info_number(Fh)
        else:
            file_name = "<command line>"
            line_n    = -1
        return SourceRef(file_name, line_n)

    def is_void(self):
        return (self.file_name == "<default>") and (self.line_n == 0)

SourceRef_VOID = SourceRef()

class CodeFragment(object):
    """base class for all kinds of generated code and code which
    potentially contains text formatting instructions. Sole feature:

       .get_code() = A list of strings and text formatting instructions.

       .sr         = Reference to the source where the code fragment 
                     was taken from. 
                     
    '.sr.is_void()' tells that the code fragment was either generated
    or is a default setting.
    """
    __slots__ = ("__code", "__source_reference")
    def __init__(self, Code=None, SourceReference=SourceRef_VOID):
        if   Code is None:                     self.__code = []
        elif isinstance(Code, (str, unicode)): self.__code = [ Code ]
        elif isinstance(Code, list):           self.__code = Code
        elif isinstance(Code, tuple):          self.__code = list(Code)
        else:                                  assert False, Code.__class__

        self.__source_reference = SourceReference

    def __check_code(self, condition):
        for string in self.get_code():
            if not isinstance(string, (str, unicode)): continue
            elif condition(string):                    return True
        return False

    @property
    def sr(self): return self.__source_reference

    @typed(Re=re._pattern_type)
    def contains_string(self, Re):  return self.__check_code(lambda x: Re.search(x) is not None)
    def is_empty(self):             return not self.__check_code(lambda x: len(x) != 0)
    def is_whitespace(self):        return not self.__check_code(lambda x: len(x.strip()) != 0)

    def get_code(self):
        """Returns a list of strings and/or integers that are the 'core code'. 
        Integers represent indentation levels.

        This function may be overwritten by a derived class. As a result there
        might be possile annotations.
        """
        return self.get_pure_code()

    def get_pure_code(self):
        """Pure code as stored in the list without any annotation of the derived
        class.
        """
        return self.__code

    def get_text(self):
        """Rely on the possibly overwritten '.get_code()' function to get the
        code to make a text. This may contain annotations of the derived class.
        """
        code = self.get_code()
        assert all_isinstance(code, (str, unicode))
        return "".join(code)

    def get_pure_text(self):
        """Rely on the 'self.__code' member. This avoids any annotation of the
        derived class. 
        """
        assert all_isinstance(self.__code, (str, unicode))
        return "".join(self.__code)

CodeFragment_NULL = CodeFragment([])

class LocalizedParameter:
    def __init__(self, Name, Default, FH=-1, PatternStr = None):
        self.name      = Name
        self.__default = Default
        self.sr        = SourceRef.from_FileHandle(FH)
        if FH == -1: self.__value = None
        else:        self.__value = Default
        self.__pattern_string = PatternStr

    def set(self, Value, fh):
        if self.__value is not None:
            error_msg("%s has been defined more than once.\n" % self.name, fh, DontExitF=True)
            error_msg("previous definition has been here.\n", self.file_name, self.line_n)
                      
        self.__value   = Value
        if fh == -1:
            self.file_name = "<string>"
            self.line_n    = 0
        else:
            self.file_name = fh.name
            self.line_n    = get_current_line_info_number(fh)

    def get(self):
        if self.__value is not None: return self.__value
        return self.__default

    def set_pattern_string(self, Value):
        self.__pattern_string = Value

    def pattern_string(self):
        return self.__pattern_string

    @property
    def comment(self):
        return self.name

