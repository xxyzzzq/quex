from   quex.engine.generator.code.base import SourceRef, CodeFragment
from   quex.blackboard import Lng
from   quex.engine.tools import typed


class CodeUser(CodeFragment):
    """User code as it is taken from some input file. It contains:

          .get_code() -- list of strings or text formatting instructions
                         (including possibly annotations about its origin)
          .sr         -- the source reference where it was taken from
    """
    def __init__(self, Code, SourceReference):
        CodeFragment.__init__(self, Code, SourceReference)
        self.mode_name      = ""
        self.pattern_string = ""

    def clone(self):
        result = CodeUser(deepcopy(self.get_code()), self.sr)
        result.mode_name      = self.mode_name
        result.pattern_string = self.pattern_string
        return result

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

class CodeTerminal(CodeFragment):
    __slots__ = ("__requires_lexeme_terminating_zero_f", "__requires_lexeme_begin_f")
    def __init__(self, Code, LexemeRelevanceF=False):
        CodeFragment.__init__(self, Code)
        if LexemeRelevanceF:
            self.__requires_lexeme_terminating_zero_f = self.contains_string(Lng.Match_Lexeme) 
            self.__requires_lexeme_begin_f            =    self.__requires_lexeme_terminating_zero_f \
                                                        or self.contains_string(Lng.Match_LexemeBegin)
        else:
            self.__requires_lexeme_terminating_zero_f = False
            self.__requires_lexeme_begin_f            = False

    def requires_lexeme_begin_f(self):            return self.__requires_lexeme_begin_f
    def requires_lexeme_terminating_zero_f(self): return self.__requires_lexeme_terminating_zero_f

class CodeTerminalOnMatch(CodeTerminal):
    def __init__(self, Code, ModeName, PatternString):
        self.mode_name = ModeName
        self.pattern_string = PatternString
        CodeTerminal.__init__(self, Code, LexemeRelevanceF=True)
    
