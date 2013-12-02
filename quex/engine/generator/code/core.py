from   quex.engine.misc.file_in import \
                                       open_file_or_die, \
                                       write_safely_and_close, \
                                       get_current_line_info_number, \
                                       error_msg
from   quex.engine.generator.code_fragment_base import CodeFragment
from   quex.blackboard   import setup as Setup, E_IncidenceIDs, SourceRef
from   quex.engine.tools import typed


class UserCodeFragment(CodeFragment):
    @typed(Code=(str,unicode), SourceReference=(None, SourceReference))
    def __init__(self, Code="", SourceReference=None):
        CodeFragment.__init__(self, Code)
        self.sr = SourceReference

    def clone(self):
        result = UserCodeFragment()
        result.set_code(CodeFragment.get_code(self))
        result.sr = self.sr # SourceRef is immutable
        return result

class CodeGotoTerminal(CodeFragment):
   __slots__ = ("incidence_id",)
   def __init__(self, IncidenceId):
       self.incidence_id = IncidenceId

   def get_code(self):
       LanguageDB = Setup.language_db
       return LanguageDB.GOTO_BY_DOOR_ID(DoorID.incidence(self.incidence_id))

class PatternActionInfo:
    def __init__(self, ThePattern, Action, PatternStr="", IL = None, ModeName="", Comment=""):
        assert    ThePattern in E_IncidenceIDs \
               or (ThePattern.__class__.__name__ == "Pattern") \
               or (ThePattern is None)

        if Action is None or issubclass(Action.__class__, CodeFragment):
            self.__action = Action
        else:
            self.__action = CodeFragment(Action)

        self.__pattern     = ThePattern
        self.__pattern_str = PatternStr
        self.mode_name     = ModeName
        self.comment       = Comment

    @property
    def line_n(self): return self.action().sr.line_n
    @property
    def file_name(self): return self.action().sr.file_name

    def acceptance_id(self):
        if self.__pattern in E_IncidenceIDs: return self.__pattern 
        else:                             return self.__pattern.incidence_id()
    def pattern(self):
        return self.__pattern

    def pattern_string(self):
        return self.__pattern_str

    def action(self):
        return self.__action

    def set_action(self, Action):
        assert Action is None or \
               issubclass(Action.__class__, CodeFragment) or \
               type(Action) in [str, unicode]
        self.__action = Action

    def pattern_index(self):
        return self.pattern_state_machine().get_id()

    def __repr__(self):         
        txt  = ""
        txt += "self.mode_name      = %s\n" % repr(self.mode_name)
        if self.pattern() not in E_IncidenceIDs:
            txt += "self.pattern_string = %s\n" % repr(self.pattern_string())
        txt += "self.pattern        = %s\n" % repr(self.pattern()).replace("\n", "\n      ")
        txt += "self.action         = %s\n" % self.action().get_code_string()
        if self.action().__class__ == UserCodeFragment:
            txt += "self.file_name  = %s\n" % repr(self.action().sr.file_name) 
            txt += "self.line_n     = %s\n" % repr(self.action().sr.line_n) 
        if self.pattern() not in E_IncidenceIDs:
            txt += "self.pattern_index  = %s\n" % repr(self.pattern().incidence_id()) 
        return txt

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


