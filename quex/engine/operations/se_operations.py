"""This file defines commands that appear in 'single entry state machines'. 
They are NOT immutable. Thus, they are NOT subject to 'fly-weight-ing'.

Commands of single entry state machines should never appear together with
commands of multi-entry state machines. 

(C) Frank-Rene Schaefer
"""
from quex.engine.misc.tools import typed

from quex.blackboard import E_PreContextIDs, \
                            E_IncidenceIDs, \
                            E_PostContextIDs, \
                            E_R

class SeOp:
    def __init__(self):
        self.__acceptance_id = E_IncidenceIDs.MATCH_FAILURE

    def set_acceptance_id(self, PatternId):
        self.__acceptance_id = PatternId

    def acceptance_id(self):
        return self.__acceptance_id

    def _string_annotate(self, Str):
        if self.__acceptance_id == E_IncidenceIDs.MATCH_FAILURE: return Str
        return "%s%s" % (Str, self.__acceptance_id)

    def __eq__(self, Other):
        return self.__acceptance_id == Other.__acceptance_id

    def __ne__(self, Other):
        """This function implements '__ne__' for all derived classes. It relies
        on the possibly overwritten '__eq__' operator.
        """
        return not self.__eq__(self, Other)

class SeAccept(SeOp):
    def __init__(self):
        SeOp.__init__(self)
        self.__pre_context_id              = E_PreContextIDs.NONE
        self.__restore_position_register_f = False

    def clone(self, ReplDbPreContext=None, ReplDbAcceptance=None):
        result = SeAccept()
        if ReplDbAcceptance is None: result.set_acceptance_id(self.acceptance_id())
        else:                        result.set_acceptance_id(ReplDbAcceptance[self.acceptance_id()])
        if ReplDbPreContext is None: result.__pre_context_id = self.__pre_context_id
        else:                        result.__pre_context_id = ReplDbPreContext[self.__pre_context_id]
        result.__restore_position_register_f = self.__restore_position_register_f
        return result

    def set_pre_context_id(self, PatternId):
        self.__pre_context_id = PatternId

    def pre_context_id(self):
        return self.__pre_context_id

    def set_restore_position_register_f(self):
        self.__restore_position_register_f = True

    def restore_position_register_f(self):
        return self.__restore_position_register_f
    
    def get_concerned_registers(self):
        if self.__pre_context_id != E_PostContextIDs.NONE:
            return (E_R.Acceptance, E_R.InputPosition, E_R.PrecontexID)
        else:
            return (E_R.Acceptance, E_R.InputPosition)

    def __eq__(self, Other):
        if   not Other.__class__ == SeAccept:                       return False
        elif not SeOp.__eq__(self, Other):                       return False
        elif not self.__pre_context_id == Other.__pre_context_id: return False
        return self.__restore_position_register_f == Other.__restore_position_register_f

    def __str__(self):
        acceptance_id_txt = ""
        pre_txt           = ""
        restore_txt       = ""
        if self.acceptance_id() != E_IncidenceIDs.MATCH_FAILURE:
            acceptance_id_txt = repr(self.acceptance_id()).replace("L", "")
        if self.__pre_context_id != E_PreContextIDs.NONE:            
            if self.__pre_context_id == E_PreContextIDs.BEGIN_OF_LINE:
                pre_txt = "pre=bol"
            else: 
                pre_txt = "pre=%s" % repr(self.__pre_context_id).replace("L", "")
        if self.__restore_position_register_f: 
            restore_txt = self._string_annotate("R")

        txt = [ x for x in (acceptance_id_txt, pre_txt, restore_txt) if x ]
        if txt: return "A(%s)" % reduce(lambda x, y: "%s,%s" % (x,y), txt)
        else:   return "A"

class SeStoreInputPosition(SeOp):
    @typed(RegisterId=long)
    def __init__(self, RegisterId=E_PostContextIDs.NONE):
        SeOp.__init__(self)
        self.__position_register_id = RegisterId

    def clone(self, ReplDbPreContext=None, ReplDbAcceptance=None):
        result = SeStoreInputPosition()
        if ReplDbAcceptance is None: result.set_acceptance_id(self.acceptance_id())
        else:                        result.set_acceptance_id(ReplDbAcceptance[self.acceptance_id()])
        result.__position_register_id = self.__position_register_id
        return result

    def get_concerned_registers(self):
        return E_R.InputPosition

    def __eq__(self, Other):
        if   Other.__class__ != SeStoreInputPosition: return False
        elif not SeOp.__eq__(self, Other):         return False
        return self.__position_register_id == Other.__position_register_id

    def __str__(self):
        return self._string_annotate("S")
