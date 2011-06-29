from quex.blackboard import TargetStateIndices, \
                            setup as Setup
from quex.engine.analyzer.core import AnalyzerState

def do(Target, TheState, ReturnToState_Str, GotoReload_Str):
    """Generate a 'real' target action object based on a given Target that may be
       an identifier or actually a real object already.

       The approach of having 'code-ready' objects as targets makes code 
       generation much simpler. No information has to be passed down the 
       recursive call tree.
    """
    if isinstance(Target, TransitionCode): 
        return Target
    else:
        return TransitionCode(Target, TheState, ReturnToState_Str, GotoReload_Str)

class TransitionCode:
    def __init__(self, Target, TheState, ReturnToState_Str, GotoReload_Str):
        assert isinstance(TheState, AnalyzerState)
        assert ReturnToState_Str is None or isinstance(ReturnToState_Str, (str, unicode))
        assert GotoReload_Str    is None or isinstance(GotoReload_Str, (str, unicode))
        LanguageDB = Setup.language_db

        if   Target == TargetStateIndices.RELOAD_PROCEDURE:
            if GotoReload_Str is not None: self.__code = GotoReload_Str
            else:                          self.__code = LanguageDB.GOTO_RELOAD(TheState, ReturnToState_Str)
            self.__drop_out_f = False
        elif Target == TargetStateIndices.DROP_OUT:
            self.__code       = LanguageDB.GOTO_DROP_OUT(TheState.index)
            self.__drop_out_f = True
        elif isinstance(Target, (int, long)):
            self.__code       = LanguageDB.GOTO(Target)
            self.__drop_out_f = False
        else:
            assert isinstance(Target, TransitionCode) # No change necessary
            return Target

    @property
    def code(self):       return self.__code
    @property
    def drop_out_f(self): return self.__drop_out_f

def __transition_to_reload(StateIdx, SMD, ReturnStateIndexStr=None):
    LanguageDB = Setup.language_db

def get_transition_to_terminal(Origin):
    LanguageDB = Setup.language_db

    # No unconditional case of acceptance 
    if type(Origin) == type(None): 
        get_label("$terminal-router", U=True) # Mark __TERMINAL_ROUTER as used
        return [ LanguageDB["$goto-last_acceptance"] ]

    assert Origin.is_acceptance()
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == PostContextIDs.NONE:
        return [ "goto %s;" % get_label("$terminal", Origin.state_machine_id, U=True) ]
    else:
        return [ "goto %s;" % get_label("$terminal-direct", Origin.state_machine_id, U=True) ]

