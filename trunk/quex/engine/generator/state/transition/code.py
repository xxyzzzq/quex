import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.entry_action      import DoorID
from   quex.engine.analyzer.mega_state.core         import MegaState_Target, \
                                                           MegaState_Target_DROP_OUT
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.generator.languages.address      import get_address
import quex.engine.analyzer.transition_map              as transition_map_tool
from   quex.blackboard import E_StateIndices, \
                              setup as Setup

class TransitionCodeFactory:
    @classmethod
    def init(cls, EngineType, StateIndex, InitStateF=False, GotoReloadStr=None, TheAnalyzer=None, ImplementedStateIndexList=None):
        assert StateIndex is None or isinstance(StateIndex, (int, long))
        assert type(InitStateF) == bool

        cls.state_index     = StateIndex
        cls.init_state_f    = InitStateF
        cls.goto_reload_str = GotoReloadStr
        cls.engine_type     = EngineType
        cls.analyzer        = TheAnalyzer


    @classmethod
    def prepare_reload_tansition(cls, TM,
                                 StateIndex     = None,
                                 EngineType     = engine.FORWARD,
                                 InitStateF     = False,
                                 GotoReload_Str = None):
        """If the engine type requires a reload the following is done:

           (1) It is made sure that the transition map transits:

                    buffer limit code --> reload procedure.

           (2) An action is determined for the reload itself.
        """
        if not EngineType.requires_buffer_limit_code_for_reload():
            return None

        cls.prepare_transition_map_for_reload(TM)

        return cls.prepare_reload_action(StateIndex, EngineType, InitStateF, GotoReload_Str)

    @classmethod
    def prepare_transition_map_for_reload(cls, TM):
        # Insist that transitions to reload procedure have been prepared!
        # There is no state transition to 'RELOAD_PROCEDURE', so transition on
        # buffer limit code MUST trigger a 'DROP_OUT'.
        blc_target = TM.get_target(Setup.buffer_limit_code) 
        assert    blc_target == E_StateIndices.DROP_OUT \
               or blc_target == MegaState_Target_DROP_OUT \
               or blc_target == E_StateIndices.RELOAD_PROCEDURE

        # Signalize 'reload' upon buffer limit code.
        TM.set_target(Setup.buffer_limit_code, 
                      E_StateIndices.RELOAD_PROCEDURE)

    @classmethod
    def prepare_reload_action(cls, StateIndex, EngineType, InitStateF, GotoReload_Str):
        LanguageDB = Setup.language_db
        result = []

        if GotoReload_Str is not None:
            result.extend(GotoReload_Str)
        else:
            result.append(LanguageDB.GOTO_RELOAD(StateIndex, InitStateF, EngineType))

        return "".join(result)

    @classmethod
    def do(cls, Target):
        LanguageDB = Setup.language_db

        if isinstance(Target, TransitionCode): 
            return Target

        elif isinstance(Target, (str, unicode)) or isinstance(Target, list):
            return TransitionCode(Target)

        elif Target == E_StateIndices.RELOAD_PROCEDURE:
            if cls.goto_reload_str is not None: 
                return TransitionCode(cls.goto_reload_str)
            else:                          
                return TransitionCode(LanguageDB.GOTO_RELOAD(cls.state_index, 
                                                             cls.init_state_f,
                                                             cls.engine_type))

        elif Target == E_StateIndices.DROP_OUT:
            return TransitionCode_DropOut(cls.state_index)

        elif isinstance(Target, DoorID):
            # The transition to another target state cannot possibly be cut out!
            # => no postponed code generation
            return TransitionCode(LanguageDB.GOTO_BY_DOOR_ID(Target))

        else:
            assert False

class MegaStateTransitionCodeFactory:
    @classmethod
    def init(cls, TheState, StateDB, StateKeyStr, EngineType, GotoReloadStr):
        cls.state                        = TheState
        cls.implemented_state_index_list = TheState.implemented_state_index_list()
        cls.state_db                     = StateDB
        cls.state_key_str                = StateKeyStr
        cls.engine_type                  = EngineType
        cls.goto_reload_str              = GotoReloadStr

    @classmethod
    def do(cls, Target):
        LanguageDB = Setup.language_db

        if Target == E_StateIndices.RELOAD_PROCEDURE:
            if cls.goto_reload_str is not None: 
                return TransitionCode(cls.goto_reload_str)
            else:                          
                return TransitionCode(LanguageDB.GOTO_RELOAD(cls.state.index, 
                                                             cls.state.init_state_f,
                                                             cls.engine_type))
        assert isinstance(Target, MegaState_Target)
        if Target.drop_out_f:
            return TransitionCode_DropOut(cls.state.index) 

        elif Target.target_state_index is not None:
            # NOTE: Not all transitions of from 'x' to 'Target.target_state_index' may
            #       be relevant. For example, if the transition lies on a uniform path
            #       which is implemented by the MegaState. The MegaState indicates
            #       the irrelevance by deleting the transition_id. 
            # HOWEVER: If no transition_id is found, then transition_map is erroneous!
            for from_state_index in cls.implemented_state_index_list:
                target_entry = cls.state_db[Target.target_state_index].entry
                door_id      = target_entry.action_db.get_door_id(Target.target_state_index, from_state_index)
                if door_id is None: continue
                code = [LanguageDB.GOTO_BY_DOOR_ID(door_id)]
                break
            else:
                assert False, "TransitionID was not resolved in target state's entry."

            return TransitionCode(code)

        elif Target.target_door_id is not None:
            return TransitionCode(LanguageDB.GOTO_BY_DOOR_ID(Target.target_door_id))

        elif Target.scheme is not None:
            variable_name = require_scheme_variable(Target.scheme_id, Target.scheme, cls.state, cls.state_db)
            return TransitionCode(LanguageDB.GOTO_BY_VARIABLE("%s[%s]" % (variable_name, cls.state_key_str)))

        else:
            assert False

class TransitionCode:
    def __init__(self, Code, DropOutF=False, StateIndex=None):
        assert DropOutF == False or StateIndex is not None

        if isinstance(Code, list):
            for elm in Code: 
                assert isinstance(elm, (int, str, unicode)), "%s" % elm
            self.__code = Code
        else:
            assert isinstance(Code, (str, unicode))
            self.__code = [ Code ]

    @property
    def code(self):       return self._get_code()

    @property
    def drop_out_f(self): return self._get_drop_out_f()

    def _get_code(self):        
        return self.__code

    def _get_drop_out_f(self):  
        return False

    def __eq__(self, Other): 
        if isinstance(Other, TransitionCode) == False: return False
        return self.__code == Other.__code 

    def __neq__(self, Other): 
        return not self.__eq__(self, Other)

class TransitionCode_DropOut(TransitionCode):
    def __init__(self, StateIndex=None):
        self.__code        = None
        self.__state_index = StateIndex

    def _get_code(self):        
        if self.__code is None: 
            LanguageDB = Setup.language_db
            self.__code = LanguageDB.GOTO_DROP_OUT(self.__state_index)
        return self.__code

    def _get_drop_out_f(self):  
        return True

def require_scheme_variable(SchemeID, Scheme, TState, StateDB):
    """Defines the transition targets for each involved state. Note, that recursion
       is handled as part of the general case, where all involved states target 
       a common door of the template state.
    """
    LanguageDB = Setup.language_db
    assert len(Scheme) == len(TState.implemented_state_index_list())

    def get_code(AdrList):
        last_i = len(AdrList) - 1
        txt = ["{ "]
        for i, adr in enumerate(AdrList):
            if i != last_i:
                txt.append("%s, " % LanguageDB.LABEL_BY_ADDRESS(adr)) 
            else:
                txt.append("%s " % LanguageDB.LABEL_BY_ADDRESS(adr)) 
        txt.append(" }")
        return "".join(txt)

    def address(Target, StateKey, TheState):
        if Target == E_StateIndices.DROP_OUT:
            # All drop outs end up at the end of the transition map, where
            # it is routed via the state_key to the state's particular drop out.
            return get_address("$drop-out", TState.index, U=True, R=True)

        from_state_index = TheState.map_state_key_to_state_index(StateKey)
        door_id          = StateDB[Target].entry.action_db.get_door_id(Target, 
                                                                       FromStateIndex=from_state_index)

        if door_id is None:
            # IMPORTANT NOTE: (This case is separated to make this comment)
            #
            # A MegaState's transition map may be partly covered by the
            # MegaState's head.  This implies, that not all implemented
            # states trigger to the state mentioned in the transition map.
            # (A 'pseudo-common' .target_state_index may be split into a
            # scheme, because the entering doors differ.) As a result the
            # '.get_door_id()' may result in a totally legal 'None' for
            # a particular 'state_key'.
            # 
            # Later: 'LABEL_BY_ADDRESS(None) --> "QUEX_GOTO_LABEL_VOID"
            return None 
        else:
            return LanguageDB.ADDRESS_BY_DOOR_ID(door_id)

    address_list = [ address(target_index, state_key, TState) \
                     for state_key, target_index in enumerate(Scheme) ]

    return variable_db.require_array("template_%i_target_%i", 
                                     ElementN = len(TState.implemented_state_index_list()), 
                                     Initial  = get_code(address_list),
                                     Index    = (TState.index, SchemeID))


