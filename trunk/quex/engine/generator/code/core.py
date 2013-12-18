from   quex.engine.misc.file_in import \
                                       open_file_or_die, \
                                       write_safely_and_close, \
                                       get_current_line_info_number, \
                                       error_msg
from   quex.engine.generator.code.base import CodeFragment
from   quex.blackboard   import setup as Setup, E_IncidenceIDs, SourceRef
from   quex.engine.tools import typed


class UserCodeFragment_DELETED(CodeFragment):
    @typed(Code=(str,unicode), SourceReference=(None, SourceRef))
    def __init__(self, Code="", SourceReference=None):
        CodeFragment.__init__(self, Code)
        self.sr = SourceReference

    def clone(self):
        result = UserCodeFragment()
        result.set_code(CodeFragment.get_code(self))
        result.sr = self.sr # SourceRef is immutable
        return result

class CodeGotoTerminal_DELETED(CodeFragment):
   __slots__ = ("incidence_id",)
   def __init__(self, IncidenceId):
       self.incidence_id = IncidenceId

   def get_code(self):
       LanguageDB = Setup.language_db
       return LanguageDB.GOTO_BY_DOOR_ID(DoorID.incidence(self.incidence_id))

