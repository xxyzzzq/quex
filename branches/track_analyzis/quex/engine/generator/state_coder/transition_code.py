from quex.blackboard import E_StateIndices, \
                            setup as Setup
from quex.engine.state_machine.state_core_info import E_EngineTypes

def do(Target, StateIndex, InitStateF, EngineType, ReturnToState_Str, GotoReload_Str):
    """Generate a 'real' target action object based on a given Target that 
       may be an identifier or actually a real object already.

       The approach of having 'code-ready' objects as targets makes code 
       generation much simpler. No information has to be passed down the 
       recursive call tree.
    """
    assert Target is not None
    assert Target != -1

    if isinstance(Target, TransitionCode): 
        return Target
    else:
        return TransitionCode(Target, StateIndex, InitStateF, EngineType, ReturnToState_Str, GotoReload_Str)

class TransitionCode:
    def __init__(self, Target, StateIndex, InitStateF, EngineType, ReturnToState_Str, GotoReload_Str):
        """The generation of transition code is postponed to the moment when
           the code fragment is used. This happens in order to avoid the
           generation of references to 'goto-labels' that are later not used.
           Note, that in some cases, for example 'goto drop-out' can be avoided
           by simply dropping out of an if-else clause or a switch statement.

           if self.__code is None: postponed
           else:                   not postponed
        """
        assert EngineType        in E_EngineTypes
        assert type(InitStateF)  == bool
        assert StateIndex        is None or isinstance(StateIndex, (int, long))
        assert ReturnToState_Str is None or isinstance(ReturnToState_Str, (str, unicode))
        assert GotoReload_Str    is None or isinstance(GotoReload_Str, (str, unicode))
        LanguageDB = Setup.language_db

        self.__target              = Target
        self.__state_index         = StateIndex
        self.__init_state_f        = InitStateF
        self.__engine_type         = EngineType
        self.__return_to_state_str = ReturnToState_Str

        if   Target == E_StateIndices.RELOAD_PROCEDURE:
            self.__drop_out_f = False
            if GotoReload_Str is not None: self.__code = GotoReload_Str
            else:                          self.__code = None # postponing
        elif Target == E_StateIndices.DROP_OUT:
            self.__code       = None # postponing
            self.__drop_out_f = True
        elif isinstance(Target, (int, long)):
            # The transition to another target state cannot possibly be cut out!
            # => no postponed code generation
            self.__code       = LanguageDB.GOTO(Target, StateIndex, EngineType)
            self.__drop_out_f = False
        else:
            assert False # When it hits here, we need to think what to do!

    @property
    def code(self):       
        if self.__code is not None: return self.__code
        LanguageDB = Setup.language_db

        if   self.__target == E_StateIndices.RELOAD_PROCEDURE:
            return LanguageDB.GOTO_RELOAD(self.__state_index, self.__init_state_f, self.__engine_type, self.__return_to_state_str)
        elif self.__target == E_StateIndices.DROP_OUT:
            return LanguageDB.GOTO_DROP_OUT(self.__state_index)
        else:
            assert False

    @property
    def drop_out_f(self): return self.__drop_out_f

def get_transition_to_terminal(Origin):
    LanguageDB = Setup.language_db

    # No unconditional case of acceptance 
    if type(Origin) == type(None): 
        get_label("$terminal-router", U=True) # Mark __TERMINAL_ROUTER as used
        return [ LanguageDB["$goto-last_acceptance"] ]

    assert Origin.is_acceptance()
    # The seek for the end of the core pattern is part of the 'normal' terminal
    # if the terminal 'is' a post conditioned pattern acceptance.
    if Origin.post_context_id() == E_PostContextIDs.NONE:
        return [ "goto %s;" % get_label("$terminal", Origin.state_machine_id, U=True) ]
    else:
        return [ "goto %s;" % get_label("$terminal-direct", Origin.state_machine_id, U=True) ]

