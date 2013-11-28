"""

   CodeFragment:
   (Delayed code generation/pasting)
   .get_code() --> contains 'text' and 'instructions'
   .lexeme_terminating_zero_required_f()
   .lexeme_begin_required_f()
   .subject_to_match_f()

   UserCode_Base:
   (Referenced source code of user)
   .get_code() --> possibly annotated code that tells about the source ref.
   .sr         --> the reference into the origin (file name, line number)

   GeneratedCode:
   (Generated code by quex)

CLASS HIERARCHY
                             CodeFragment
                              /       \  \__________ 
   unicode   CodeUser_Base   /         \            \
      |         /   \       /       GeneratedCode   CodeFinalized
      |        /     \     /          |      |      (Finalized UserCode)
      |       /       \   /           |      |
   CodeUserPlain    CodeUser      CodeSkip  CodeIndentationHandler ...

"""
from   quex.engine.tools import error_abstract_member
from   copy import deepcopy
import re

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

class CodeUserPlain(unicode, CodeUser_Base):
    """Plain user code that does not contain text formatting instructions
    and does not generate any code. It consists of:

        self -- (unicode) text

        .sr  -- Source reference (file name, line n) telling from where
                the text was taken.
    """
    @typed(Text=unicode)
    def __init__(self, Text, SourceReference):
        unicode.__init__(self, Text)
        CodeUser_Base.__init__(self, SourceReference)

    @typed(Re=re._pattern_type)
    def contains_string(self, Re):  return Re.search(string) is not None
    def is_empty(self):             return unicode.__len__(self) == 0
    def is_whitespace(self):        return len(self.strip()) == 0

class CodeFragment_Base(object):
    """ABSTRACT base class for all kinds of generated code and code which
    potentially contains text formatting instructions. Sole feature:

       .get_code() = A list of strings and text formatting instructions.
    """
    __slots__ = ("__code")
    def __init__(self, Code=None):
        self.set_code(Code)

    def clone(self):
        return CodeFragment([deepcopy(x) for x in self.__code], self.__require_lexeme_begin_f)

    def lexeme_begin_required_f(self):            error_abstract_member()
    def lexeme_terminating_zero_required_f(self): error_abstract_member()
    def subject_to_match_f(self):                 error_abstract_member()

    def set_code(self, Code):
        if   Code is None:                     self.__code = []
        elif isinstance(Code, (str, unicode)): self.__code = [ Code ]
        elif isinstance(Code, list):           self.__code = Code
        elif isinstance(Code, tuple):          self.__code = list(Code)
        else:                                  assert False, Code.__class__

    def append_CodeFragment(self, Other):
        assert isinstance(Other, CodeFragment)
        self.__code.extend(Other.__code)

    def append_text(self, Text):
        assert isinstance(Text, (str, unicode))
        self.__code.append(Text)

    def get_code(self, Mode=None):
        """Returns a list of strings and/or integers that are the 'core code'. 
        Integers represent indentation levels.
        """
        return self.__code

class CodeUser(CodeUser_Base, CodeFragment_Base):
    """User code as it is taken from some input file. It contains:

          .get_code() -- list of strings or text formatting instructions
                         (including possibly annotations about its origin)
          .sr         -- the source reference where it was taken from
    """
    def __init__(self, Code, SourceReference, SubjectToMatchF=True):
        CodeFragment.__init__(self, Code)
        CodeUser_Base.__init__(self, SourceReference)
        self.__subject_to_match_f = SubjectToMatchF

    def clone(self):
        return CodeUser(CodeFragment.clone(self), self.sr, self.__subject_to_match_f)

    def __check_code(self, condition):
        for string in self.__code:
            if not isinstance(string, (str, unicode)): continue
            if __condition(string): return True
        return False

    @typed(Re=re._pattern_type)
    def contains_string(self, Re):  return self.__check_code(lambda x: Re.search(string) is not None)
    def is_empty(self):             return not self.__check_code(lambda x: len(x) != 0)
    def is_whitespace(self):        return not self.__check_code(lambda x: len(x.strip()) != 0)

    def lexeme_begin_required_f(self):            return self.contains_string(Match_Lexeme) or self.contains_string(Match_LexemeBegin)
    def lexeme_terminating_zero_required_f(self): return self.contains_string(Match_Lexeme) 
    def subject_to_match_f(self):                 return self.__subject_to_match_f

    def get_code(self):
        """Returns a list of strings and/or integers that are the 'core code'. 
        Integers represent indentation levels. Source code is adorned with 
        a source reference.
        """
        code = CodeFragment_Base.get_code(self)
        if len(code) == 0: return []

        result      = [ gt]
        result.extend(code)
        result.append(LanguageDB.SOURCE_REFERENCE_END())
        return result

class CodeGenerated(CodeFragment_Base):
    """Abstract Class"""
    def contains_string(self, Re):  return False
    def is_empty(self):             return False
    def is_whitespace(self):        return False

    def lexeme_begin_required_f(self):            return False
    def lexeme_terminating_zero_required_f(self): return False
    def subject_to_match_f(self):                 return False


class CodeFinalized(CodeFragment_Base):
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
    
