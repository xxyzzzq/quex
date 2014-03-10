from   quex.engine.tools        import error_abstract_member, \
                                       typed, \
                                       all_isinstance
from   quex.engine.misc.file_in import get_current_line_info_number
from   quex.engine.tools        import none_isinstance

from   collections import namedtuple
from   copy        import deepcopy

import types
import re

class SourceRef(namedtuple("SourceRef_tuple", ("file_name", "line_n", "mode_name"))):
    """A reference into source code:
    _______________________________________________________________________________
      
        file_name = Name of the file where the code is located.
        line_n    = Number of line where code is found.
    _______________________________________________________________________________
    """
    def __new__(self, FileName="<default>", LineN=0, ModeName=""):
        assert isinstance(FileName, (str, unicode))
        assert isinstance(LineN, (int, long))
        return super(SourceRef, self).__new__(self, FileName, LineN, ModeName)

    @staticmethod
    def from_FileHandle(Fh, ModeName=""):
        if Fh != -1:
            if not hasattr(Fh, "name"): file_name = "<nameless stream>"
            else:                       file_name = Fh.name
            line_n = get_current_line_info_number(Fh)
        else:
            file_name = "<command line>"
            line_n    = -1
        return SourceRef(file_name, line_n, ModeName)

    def is_void(self):
        return (self.file_name == "<default>") and (self.line_n == 0) and len(self.mode_name) == 0

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
    @typed(Code=(list, str, unicode, types.NoneType), SourceReference=SourceRef)
    def __init__(self, Code=None, SourceReference=SourceRef_VOID):
        # Elements of 'Code' shall not be lists.
        assert not isinstance(Code, list) or none_isinstance(Code, list)

        if   Code is None:                     self.__code = []
        elif isinstance(Code, (str, unicode)): self.__code = [ Code ]
        else:                                  self.__code = Code

        self.__source_reference = SourceReference

    def __check_code(self, condition):
        for string in self.get_code():
            if not isinstance(string, (str, unicode)): continue
            elif condition(string):                    return True
        return False

    @property
    def sr(self):                   
        return self.__source_reference

    def set_source_reference(self, SourceReference): 
        self.__source_reference = SourceReference

    @typed(Re=re._pattern_type)
    def contains_string(self, Re):  return self.__check_code(lambda x: Re.search(x) is not None)
    def is_empty(self):             return not self.__check_code(lambda x: len(x) != 0)
    def is_whitespace(self):        return not self.__check_code(lambda x: len(x.strip()) != 0)

    def get_code(self):
        """RETURNS: List of text elements. 
        
        May contain annotations to the code made by the derived class. 
        """
        return self.__code

    def get_pure_code(self):
        """RETURNS: List of text elements. 

        The returned code is free from any annotations.
        """
        return self.__code

    def get_text(self):
        """RETURNS: Text

        May contain annotations to the code may by the derived class.
        """
        code = self.get_code()
        assert all_isinstance(code, (str, unicode))
        return "".join(code)

    def get_pure_text(self):
        """RETURNS: Text

        The returned text is free from any annotations.
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

    def set(self, Value, fh, PatternStr=None):
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

        self.__pattern_string = PatternStr

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

