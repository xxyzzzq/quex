"""
(Work in Progress)

   CodeFragment:
   (Delayed code generation/pasting)
   .get_code() 
    --> contains 'text' and 'instructions'

   CodeUser:
   .get_code()
    --> possibly annotated code that tells about the source ref.
   .sr

   CodeOnPatternMatch:
   .get_code()
   .lexeme_terminating_zero_required_f
   .lexeme_begin_required_f
   
   .sr         --> the reference into the origin (file name, line number)

CLASS HIERARCHY
                               CodeFragment
                             [+ .get_code() ]
                     /            |                     
                    /             |                      
                CodeUser    CodeForTerminal            
                [+ .sr ]    [+ lexeme_begin_required_f]   
                            [+ lexeme_terminating_zero_required_f]
                            
"""
from   quex.engine.tools        import error_abstract_member, \
                                       typed
from   quex.engine.misc.file_in import get_current_line_info_number
from   quex.blackboard          import Lng

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

class CodeUser_Base:
    """ABSTRACT base class for all pieces of code that have some reference into
    user code. Sole feature:

            .sr -- Source reference telling where the user's code 
                   was taken.
    """
    __slots__ = ("__sr",)
    def __init__(self, SourceReference):
        self.__sr = SourceReference
    @property
    def sr(self):                   return self.__sr
    def contains_string(self, Re):  error_abstract_member()
    def is_empty(self):             error_abstract_member()
    def is_whitespace(self):        error_abstract_member()

class CodeUserPlain(CodeUser_Base):
    """Plain user code that does not contain text formatting instructions
    and does not generate any code. It consists of:

        .text -- (unicode) text

        .sr  -- Source reference (file name, line n) telling from where
                the text was taken.
    """
    @typed(Text=(str, unicode), SourceReference=SourceRef)
    def __init__(self, Text, SourceReference):
        CodeUser_Base.__init__(self, SourceReference)
        self.__text = Text 

    @property
    def text(self):                 return self.__text

    @typed(Re=re._pattern_type)
    def contains_string(self, Re):  return Re.search(self.text) is not None

    def is_empty(self):             return len(self.__text) == 0
    def is_whitespace(self):        return len(self.__text.strip()) == 0

class CodeFragment(object):
    """ABSTRACT base class for all kinds of generated code and code which
    potentially contains text formatting instructions. Sole feature:

       .get_code() = A list of strings and text formatting instructions.
    """
    __slots__ = ("__code")
    def __init__(self, Code=None):
        if   Code is None:                     self.__code = []
        elif isinstance(Code, (str, unicode)): self.__code = [ Code ]
        elif isinstance(Code, list):           self.__code = Code
        elif isinstance(Code, tuple):          self.__code = list(Code)
        else:                                  assert False, Code.__class__

    def clone(self):                              error_abstract_member()
    def lexeme_begin_required_f(self):            error_abstract_member()
    def lexeme_terminating_zero_required_f(self): error_abstract_member()
    def subject_to_match_f(self):                 error_abstract_member()

    def get_code(self):
        """Returns a list of strings and/or integers that are the 'core code'. 
        Integers represent indentation levels.
        """
        return self.__code

class CodeUser(CodeUser_Base, CodeFragment):
    """User code as it is taken from some input file. It contains:

          .get_code() -- list of strings or text formatting instructions
                         (including possibly annotations about its origin)
          .sr         -- the source reference where it was taken from
    """
    def __init__(self, Code, SourceReference):
        CodeFragment.__init__(self, Code)
        CodeUser_Base.__init__(self, SourceReference)

    def subject_to_match_f(self):                 
        return False

    def clone(self):
        return CodeUser(deepcopy(self.get_code()), self.sr)

    def __check_code(self, condition):
        for string in self.get_code():
            if not isinstance(string, (str, unicode)): continue
            elif __condition(string):                  return True
        return False

    @typed(Re=re._pattern_type)
    def contains_string(self, Re):  return self.__check_code(lambda x: Re.search(string) is not None)
    def is_empty(self):             return not self.__check_code(lambda x: len(x) != 0)
    def is_whitespace(self):        return not self.__check_code(lambda x: len(x.strip()) != 0)

    def lexeme_begin_required_f(self):            return self.contains_string(Match_Lexeme) or self.contains_string(Match_LexemeBegin)
    def lexeme_terminating_zero_required_f(self): return self.contains_string(Match_Lexeme) 

    def get_code(self):
        """Returns a list of strings and/or integers that are the 'core code'. 
        Integers represent indentation levels. Source code is adorned with 
        a source reference.
        """
        code = CodeFragment.get_code(self)
        if len(code) == 0: return []

        result      = [ Lng.SOURCE_REFERENCE_BEGIN(self.sr)]
        result.extend(code)
        result.append("\n%s" % Lng.SOURCE_REFERENCE_END())
        return result

CodeUser_NULL = CodeUser([], SourceRef())

class CodeOnPatternMatch(CodeUser):
    def __init__(self, Code, SourceReference, ModeName=None, PatternStr=None):
        CodeUser.__init__(Code, SourceReference)
        self.mode_name      = ModeName
        self.pattern_string = PatternStr

    def subject_to_match_f(self):                 
        return True

class CodeGenerated(CodeFragment):
    """Abstract Class"""
    def contains_string(self, Re):  return False
    def is_empty(self):             return False
    def is_whitespace(self):        return False

    def lexeme_begin_required_f(self):            return False
    def lexeme_terminating_zero_required_f(self): return False
    def subject_to_match_f(self):                 return False


class CodeFinalized(CodeFragment):
    """A fragment of finalized code.
    ___________________________________________________________________________
    A CodeFinalized will not be subject to and addition or subtraction of code.
    No further consideration of related code fragments (on_match, 
    on_after_match, ...) will be done.
    ___________________________________________________________________________
    """
    def __init__(self, TxtList, LexemeTerminatingZeroRequiredF, LexemeBeginRequiredF):
        CodeFragment.__init__(self, TxtList)
        self.__lexeme_terminating_zero_f = LexemeTerminatingZeroRequiredF
        self.__lexeme_begin_f            = LexemeBeginRequiredF

    def contains_string(self, Re):     return False
    def is_empty(self):      return False
    def is_whitespace(self): return False

    def lexeme_begin_required_f(self):            return self.__lexeme_begin_f
    def lexeme_terminating_zero_required_f(self): return self.__lexeme_terminating_zero_f
    def subject_to_match_f(self):                 return False

_Empty = None
def CodeFragment_Empty():
    global _Empty
    if _Empty is None: 
        _Empty = CodeFragment("")
    return _Empty
    
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

