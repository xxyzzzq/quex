from quex.blackboard import setup as Setup

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
        LanguageDB = Setup.language_db
        assert type(DropOutF) == bool

        if   Target == TargetStateIndices.RELOAD_PROCEDURE:
            self.__code       = LanguageDB.TRANSITION_TO_RELOAD(GotoReload_Str, TheState.index, DSM, ReturnToState_Str)
            self.__drop_out_f = False
        elif Target == TargetStateIndices.DROP_OUT
            self.__code       = LanguageDB.GOTO_DROP_OUT(TheState.index)
            self.__drop_out_f = True
        elif isinstance(Target, (int, long)):
            self.__code       = LanguageDB.GOTO(Target)
            self.__drop_out_f = False
        else:
            assert isinstance(Target, TransitionCode) # No change necessary
            return Target

    @property
    def code(self):       return self._code
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

