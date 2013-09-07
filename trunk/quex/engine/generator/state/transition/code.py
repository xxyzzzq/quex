from   quex.engine.analyzer.transition_map          import TransitionMap
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.state.entry_action      import DoorID
from   quex.engine.analyzer.mega_state.target       import TargetByStateKey, TargetByStateKey_DROP_OUT
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.generator.languages.address      import map_door_id_to_address
from   quex.engine.tools                            import all_isinstance
import quex.engine.analyzer.transition_map          as     transition_map_tool
from   quex.blackboard import E_StateIndices, \
                              setup as Setup

def relate_to_TransitionCode(tm):
    # If a state has no transitions, no new input needs to be eaten => no reload.
    #
    # NOTE: The only case where the buffer reload is not required are empty states,
    #       AND states during backward input position detection!
    if tm.is_empty():
        return tm

    tm.assert_continuity()
    tm.assert_adjacency()
    # TM.fill_gaps(DoorID.drop_out(StateIndex))
    return TransitionMap.from_iterable(tm, TransitionCodeFactory.do)

def MegaState_relate_to_transition_code(tm, TheState, TheAnalyzer, StateKeyStr):
    TransitionCodeFactory.init_MegaState_handling(TheState, TheAnalyzer, StateKeyStr)
    return relate_to_TransitionCode(tm)

class TransitionCodeFactory:
    @classmethod
    def init_MegaState_handling(cls, TheState, TheAnalyzer, StateKeyStr):
        cls.state         = TheState
        cls.state_db      = TheAnalyzer.state_db
        cls.state_key_str = StateKeyStr

    @classmethod
    def do(cls, Target):
        LanguageDB = Setup.language_db

        if   isinstance(Target, TransitionCode): 
            return Target
        elif isinstance(Target, (str, unicode)) or isinstance(Target, list):
            return TransitionCode(Target)
        elif isinstance(Target, DoorID):
            return TransitionCodeByDoorId(Target)
        elif isinstance(Target, TargetByStateKey):
            if Target.uniform_door_id is not None:
                return TransitionCodeByDoorId(Target.uniform_door_id)

            assert Target.scheme_id is not None
            variable_name = require_scheme_variable(Target.scheme_id, Target.iterable_door_id_scheme(), cls.state, cls.state_db)
            return TransitionCode(LanguageDB.GOTO_BY_VARIABLE("%s[%s]" % (variable_name, cls.state_key_str)))
        else:
            assert False

class TransitionCode:
    def __init__(self, Code, DropOutF=False):
        assert type(DropOutF) == bool
        self.__drop_out_f = DropOutF
        if isinstance(Code, list): self.__code = Code
        else:                      self.__code = [ Code ]
        assert all_isinstance(Code, (int, str, unicode))
    def code(self):          
        return self.__code
    def drop_out_f(self):    
        return self.__drop_out_f
    def __eq__(self, Other): 
        if isinstance(Other, TransitionCode) == False: return False
        return self.__code == Other.__code 
    def __neq__(self, Other): 
        return not self.__eq__(self, Other)

class TransitionCodeByDoorId(TransitionCode):
    """The purpose of this class is to delay the reference of a DoorID until
    it is really used. It may be, that the code generation for a transition
    map implements the transition as a 'drop-into'. In that case, the label
    is not used. A definition of an unused label would cause a compiler warning.
    """
    def __init__(self, DoorId):
        self.__door_id = DoorId
    def code(self):       
        LanguageDB = Setup.language_db
        return LanguageDB.GOTO_BY_DOOR_ID(self.__door_id)
    def drop_out_f(self): 
        return self.__door_id.drop_out_f()
    def __eq__(self, Other):
        if not isinstance(Other, TransitionCodeByDoorId): return False
        return self.__door_id == Other.__door_id

def require_scheme_variable(SchemeID, SchemeIterable, TState, StateDB):
    """Defines the transition targets for each involved state. Note, that
    recursion is handled as part of the general case, where all involved states
    target a common door of the template state.
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


