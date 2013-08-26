import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.entry_action      import DoorID, DoorID_DROP_OUT, DoorID_RELOAD
from   quex.engine.analyzer.mega_state.target       import TargetByStateKey, TargetByStateKey_DROP_OUT, TargetByStateKey_RELOAD
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.generator.languages.address      import get_address
import quex.engine.analyzer.transition_map          as     transition_map_tool
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
    def prepare_reload_tansition(cls, 
                                 TM,
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

        # RETURN: goto_reload_str
        return cls.prepare_reload_action(StateIndex, EngineType, InitStateF, GotoReload_Str)

    @staticmethod
    def prepare_transition_map_for_reload(TM):
        """Ensures that the buffer limit code causes a transition to a
        reload section. That is, there will be an interval of size 1 at
        the buffer limit code which maps to DoorID_RELOAD.
        """
        # Insist that transitions to reload procedure have been prepared!
        assert TM.get_target(Setup.buffer_limit_code) in (DoorID_DROP_OUT, DoorID_RELOAD), \
               "%s" % TM.get_target(Setup.buffer_limit_code)
        TM.set_target(Setup.buffer_limit_code, DoorID_RELOAD)

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

        elif isinstance(Target, DoorID):
            if   Target == DoorID_DROP_OUT:
                return TransitionCode_DropOut(cls.state_index)
            elif Target == DoorID_RELOAD:
                if cls.goto_reload_str is not None: 
                    return TransitionCode(cls.goto_reload_str)
                else:                          
                    return TransitionCode(LanguageDB.GOTO_RELOAD(cls.state_index, 
                                                                 cls.init_state_f,
                                                                 cls.engine_type))
            else:
                # The transition to another target state cannot possibly be cut out!
                # => no postponed code generation
                return TransitionCode(LanguageDB.GOTO_BY_DOOR_ID(Target))

        else:
            assert False, "Target = '%s'" % Target

class MegaStateTransitionCodeFactory(TransitionCodeFactory):
    @classmethod
    def init(cls, TheState, StateDB, StateKeyStr, EngineType, GotoReloadStr):
        cls.state                        = TheState
        cls.implemented_state_index_list = TheState.implemented_state_index_set()
        cls.state_db                     = StateDB
        cls.state_key_str                = StateKeyStr
        cls.engine_type                  = EngineType
        cls.goto_reload_str              = GotoReloadStr

    @staticmethod
    def prepare_transition_map_for_reload(TM):
        """Ensures that the buffer limit code causes a transition to a
        reload section. That is, there will be an interval of size 1 at
        the buffer limit code which maps to DoorID_RELOAD.
        """
        # Insist that transitions to reload procedure have been prepared!
        assert TM.get_target(Setup.buffer_limit_code) in (TargetByStateKey_DROP_OUT, TargetByStateKey_RELOAD), \
               "%s" % TM.get_target(Setup.buffer_limit_code)
        TM.set_target(Setup.buffer_limit_code, TargetByStateKey_RELOAD)

    @classmethod
    def do(cls, Target):
        LanguageDB = Setup.language_db

        if Target == TargetByStateKey_RELOAD:
            if cls.goto_reload_str is not None: 
                return TransitionCode(cls.goto_reload_str)
            else:                          
                return TransitionCode(LanguageDB.GOTO_RELOAD(cls.state.index, 
                                                             cls.state.init_state_f,
                                                             cls.engine_type))
        assert isinstance(Target, TargetByStateKey)
        if Target.uniform_door_id is not None:
            if Target.drop_out_f:
                return TransitionCode_DropOut(cls.state.index) 
            else:
                return TransitionCode(LanguageDB.GOTO_BY_DOOR_ID(Target.uniform_door_id))

        else:
            assert Target.scheme_id is not None
            variable_name = require_scheme_variable(Target.scheme_id, Target.iterable_door_id_scheme(), cls.state, cls.state_db)
            return TransitionCode(LanguageDB.GOTO_BY_VARIABLE("%s[%s]" % (variable_name, cls.state_key_str)))

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

def require_scheme_variable(SchemeID, SchemeIterable, TState, StateDB):
    """Defines the transition targets for each involved state. Note, that recursion
       is handled as part of the general case, where all involved states target 
       a common door of the template state.
    """
    LanguageDB = Setup.language_db

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

    def _address(Target):
        assert isinstance(Target, DoorID)
        if Target == DoorID_DROP_OUT:
            # All drop outs end up at the end of the transition map, where
            # it is routed via the state_key to the state's particular drop out.
            return get_address("$drop-out", TState.index, U=True, R=True)
        else:
            return LanguageDB.ADDRESS_BY_DOOR_ID(Target)

    def address(Target):
        result = _address(Target)
        return result

    address_list = [ address(x) for x in SchemeIterable ]

    assert len(address_list) == len(TState.state_index_sequence())

    return variable_db.require_array("template_%i_target_%i", 
                                     ElementN = len(TState.state_index_sequence()), 
                                     Initial  = get_code(address_list),
                                     Index    = (TState.index, SchemeID))


