from   quex.engine.state_machine.state_core_info    import StateOperation
from   quex.engine.state_machine.state.single_entry import SingleEntry
from   quex.engine.state_machine.target_map         import TargetMap
from   quex.engine.tools  import typed

from   quex.blackboard    import E_IncidenceIDs, \
                                 E_PreContextIDs

class Accept:
    def __init__(self):
        self.__acceptance_id                = None
        self.__pre_context_id               = None
        self.__position_register_register_f = False

    def set_acceptance_id(self, PatternId):
        self.__acceptance_id = PatternId

    def acceptance_id(self):
        return self.__acceptance_id

    def set_pre_context_id(self, PatternId):
        self.__pre_context_id = PatternId

    def pre_context_id(self):
        return self.__pre_context_id

    def set_restore_position_register_f(self):
        self.__position_register_register_f = True

    def restore_position_register_f(self):
        return self.__position_register_register_f

class StoreInputPosition:
    @typed(RegisterId=long)
    def __init__(self, RegisterId):
        self.__position_register_register = RegisterId

class State:
    """A state consisting of ONE entry and multiple transitions to other
    states.  One entry means that the exact same actions are applied upon state
    entry, independent from where the state is entered.

           ...   ----->---.                               .--->   ...
                           \                     .-----.-'
           ...   ----->-----+--->[ StateOp ]----( State )----->   ...
                           /                     '-----'
           ...   ----->---'        

    Transitions are of two types:
    
     -- normal transitions: Happen when an input character fits a trigger set.
     -- epsilon transition: Happen without any input.
    
    Collections of states connected by transitions build a StateMachine. States 
    may be used in NFA-s (non-deterministic finite state automatons) and DFA-s
    (deterministic finite state automatons). Where NFA-s put no restrictions on
    transitions, DFA-s do. A state in a DFA has the following properties:
    
       -- Trigger sets of normal transitions do not intersect.
       -- There are no epsilon transitions. 

    Whether or not a state complies to the requirements of a DFA can be checked
    by '.is_DFA_compliant()'.
    """
    def __init__(self, AcceptanceF=False, CloneF=False):
        """Contructor of a State, i.e. a aggregation of transitions.
        """
        if CloneF: return

        self.__target_map   = TargetMap()
        self.__single_entry = SingleEntry()
        if AcceptanceF: self.set_acceptance()

    def clone(self, ReplDbStateIndex=None, ReplDbPreContext=None, ReplDbAcceptance=None):
        """Creates a copy of all transitions, but replaces any state index with the ones 
           determined in the ReplDbStateIndex."""
        assert ReplDbStateIndex is None or isinstance(ReplDbStateIndex, dict)
        result = State()
        result.__target_map   = self.__target_map.clone(ReplDbStateIndex)
        result.__single_entry = self.__single_entry.clone(ReplDbPreContext=ReplDbPreContext,
                                                          ReplDbAcceptance=ReplDbAcceptance)

        return result

    @staticmethod
    def from_state_iterable(StateList):
        """Does not set '.__target_map'
        """
        result = State()
        result.__target_map   = TargetMap()
        result.__single_entry = SingleEntry() 
        result.__single_entry.merge_list(state.single_entry.get_list() for state in StateList)
        return result

    @property
    def single_entry(self):
        return self.__single_entry

    @property
    def target_map(self):
        return self.__target_map

    def is_acceptance(self):
        for origin in self.single_entry:
            if origin.is_acceptance(): return True
        return False

    def input_position_store_f(self):
        for origin in self.single_entry:
            if origin.input_position_store_f(): return True
        return False

    def input_position_restore_f(self):
        for origin in self.single_entry:
            if origin.input_position_restore_f(): return True
        return False

    def pre_context_id(self):
        for origin in self.single_entry:
            if origin.pre_context_id() != E_PreContextIDs.NONE: 
                return origin.pre_context_id()
        return E_PreContextIDs.NONE

    def set_acceptance(self, Value=True):
        # accept_cmd = self.single_entry.find_Accept()
        # assert accept_cmd is None
        # self.single_entry.add(Accept())
        origin = self.single_entry.get_the_only_one()
        origin.set_acceptance_f(Value)
        if Value == False: origin.set_pre_context_id(E_PreContextIDs.NONE)

    def set_input_position_restore_f(self, Value=True):
        # accept_cmd = self.single_entry.find_Accept()
        # assert accept_cmd is not None
        # accept_cmd.set_input_position_restore_f()
        origin = self.single_entry.get_the_only_one()
        origin.set_input_position_restore_f(Value)

    def set_pre_context_id(self, Value=True):
        # accept_cmd = self.single_entry.find_Accept()
        # assert accept_cmd is not None
        # accept_cmd.set_pre_context_id(Value)
        origin = self.single_entry.get_the_only_one()
        origin.set_pre_context_id(Value)

    def set_input_position_store_f(self, Value=True):
        # self.single_entry.add(StoreInputPosition())
        origin = self.single_entry.get_the_only_one()
        origin.set_input_position_store_f(Value)

    def mark_self_as_origin(self, AcceptanceID, StateIndex):
        # accept_cmd = self.single_entry.find_Accept()
        # if accept_cmd is None: return
        # accept_cmd.set_acceptance_id(AcceptanceID)
        origin = self.single_entry.get_the_only_one()
        origin.set_pattern_id(AcceptanceID)
        origin.state_index = StateIndex

    def add_transition(self, Trigger, TargetStateIdx): 
        self.__target_map.add_transition(Trigger, TargetStateIdx)

    def __repr__(self):
        return self.get_string()

    def get_string(self, StateIndexMap=None, Option="utf8", OriginalStatesF=True):
        # if information about origins of the state is present, then print
        msg = self.single_entry.get_string(OriginalStatesF)

        # print out transitionts
        msg += self.target_map.get_string("    ", StateIndexMap, Option)
        return " " + msg

    def get_graphviz_string(self, OwnStateIdx, StateIndexMap, Option):
        assert Option in ["hex", "utf8"]
        return self.target_map.get_graphviz_string(OwnStateIdx, StateIndexMap, Option)

