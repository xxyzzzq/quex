import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.entry_action      import DoorID
from   quex.engine.analyzer.mega_state.target       import TargetByStateKey, TargetByStateKey_DROP_OUT
from   quex.engine.generator.languages.variable_db  import variable_db
import quex.engine.analyzer.transition_map          as     transition_map_tool
from   quex.blackboard import E_StateIndices, \
                              setup as Setup

class TransitionCodeFactory:
    @classmethod
    def init(cls, EngineType, StateIndex, InitStateF=False, TheAnalyzer=None, ImplementedStateIndexList=None):
        assert StateIndex is None or isinstance(StateIndex, (int, long))
        assert type(InitStateF) == bool

        cls.state_index     = StateIndex
        cls.init_state_f    = InitStateF
        cls.engine_type     = EngineType
        cls.analyzer        = TheAnalyzer


    @classmethod
    def do(cls, Target):
        LanguageDB = Setup.language_db

        if isinstance(Target, TransitionCode): 
            return Target

        elif isinstance(Target, (str, unicode)) or isinstance(Target, list):
            return TransitionCode(Target)

        elif isinstance(Target, DoorID):
            return TransitionCode(LanguageDB.GOTO_BY_DOOR_ID(Target))

        else:
            assert False, "Target = '%s'" % Target

class MegaStateTransitionCodeFactory(TransitionCodeFactory):
    @classmethod
    def init(cls, TheState, TheAnalyzer, StateKeyStr):
        cls.state                        = TheState
        cls.implemented_state_index_list = TheState.implemented_state_index_set()
        cls.state_db                     = StateDB
        cls.state_key_str                = StateKeyStr
        cls.engine_type                  = EngineType

    @classmethod
    def do(cls, Target):
        LanguageDB = Setup.language_db

        assert isinstance(Target, TargetByStateKey)
        if Target.uniform_door_id is not None:
            if Target.drop_out_f:
                return TransitionCode_DropOut(cls.state.index) 
            else:
                return TransitionCode(LanguageDB.GOTO_BY_DOOR_ID(Target.uniform_door_id))

        else:
            assert Target.scheme_id is not None
            variable_name = require_scheme_variable(Target.scheme_id, Target.iterable_door_id_scheme(), cls.state, cls.analyzer.state_db)
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
    door_id_list = list(SchemeIterable)

    txt = ["{ "]
    for door_id in door_id_list[:-1]:
        txt.append("QUEX_LABEL(%s), " % map_door_id_to_address(door_id, RoutedF=True)) 
    txt.append("QUEX_LABEL(%s) }" % map_door_id_to_address(door_id_list[-1], RoutedF=True)) 

    return variable_db.require_array("template_%i_target_%i", 
                                     ElementN = len(TState.state_index_sequence()), 
                                     Initial  = "".join(txt),
                                     Index    = (TState.index, SchemeID))


