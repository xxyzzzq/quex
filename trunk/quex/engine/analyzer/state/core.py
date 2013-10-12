from   quex.engine.state_machine.core          import State
import quex.engine.state_machine.index         as     state_index
from   quex.engine.analyzer.transition_map     import TransitionMap
from   quex.engine.analyzer.state.entry        import Entry
from   quex.engine.analyzer.state.entry_action import TransitionID, TransitionAction, DoorID
from   quex.engine.analyzer.commands           import CommandList, PrepareAfterReload, InputPIncrement, InputPDecrement, InputPDereference
from   quex.engine.analyzer.mega_state.target  import TargetByStateKey_DROP_OUT
from   quex.blackboard  import setup as Setup, \
                               E_StateIndices, \
                               E_InputActions

class Processor(object):
    __slots__ = ("_index", "entry")
    def __init__(self, StateIndex, TheEntry=None):
        self._index = StateIndex
        self.entry  = TheEntry
    
    @property
    def index(self):            return self._index
    def set_index(self, Value): assert isinstance(Value, long); self._index = Value

#__________________________________________________________________________
#
# AnalyzerState:
# 
#                  AnalyzerState
#                  .--------------------------------------------.
#  .-----.         |                                  .---------|
#  | 341 |--'load'--> Entry  ----->-----.             |tm(input)| 
#  '-----'         |  actions           |             |  'a' ------> 313
#  .-----.         |                    '             |  'c' ------> 142
#  | 412 |--'load'--> Entry  ---> input = *input_p -->|  'p' ------> 721
#  '-----'         |  actions           .             |  'q' ------> 313
#  .-----.         |                    |             |  'x' ------> 472
#  | 765 |--'load'--> Entry  --->-------'             |  'y' ------> 812
#  '-----'         |  actions                         |- - - - -|
#                  |                                  |drop out ---> 
#                  |                                  '---------|
#                  '--------------------------------------------'
#
# The entry actions depend on the state from which the state is entered.
# Next, the input pointer is dereferenced and 'input' is assigned. Based
# on the value of 'input' a subsequent state is targetted. The relation
# between 'input' and the target state is given by the 'TransitionMap'.
# If no state transition is possible, then 'drop out actions' are executed.
#__________________________________________________________________________
class AnalyzerState(Processor):
    __slots__ = ("drop_out", 
                 "map_target_index_to_character_set", 
                 "transition_map") 

    def __init__(self, StateIndex, TheTransitionMap):
        # Empty transition maps are reported as 'None'
        assert isinstance(TheTransitionMap, TransitionMap) or TheTransitionMap is None
        Processor.__init__(self, StateIndex)
        self.drop_out                          = None
        self.map_target_index_to_character_set = None
        self.transition_map                    = TheTransitionMap

    @staticmethod
    def from_State(SM_State, StateIndex, EngineType):
        assert isinstance(SM_State, State)
        assert isinstance(StateIndex, (int, long))

        x = AnalyzerState(StateIndex, TransitionMap.from_TargetMap(SM_State.target_map))

        # (*) Entry Action
        x.entry    = Entry()
        # (*) Drop Out
        x.drop_out = EngineType.create_DropOut(SM_State)

        # (*) Transition
        # Currently, the following is only used for path compression. If the alternative
        # is implemented, then the following is no longer necessary.
        x.map_target_index_to_character_set = SM_State.target_map.get_map()

        return x

    def prepare_for_reload(self, TheAnalyzer):
        """Prepares state for reload:
           (i)   Create entry from 'reload procedure'.
           (ii)  Create in reload state entry from this state, so
                 that reload is prepared propperly.
           (iii) Adapt the transition map, so that:
                 buffer_limit_code --> reload procedure.
           
        """
        if self.transition_map is None: # A transition map which is not a transition map
            return                      # cannot trigger any reload.

        reload_state = TheAnalyzer.reload_state
        assert reload_state.index in (E_StateIndices.RELOAD_FORWARD, E_StateIndices.RELOAD_BACKWARD)

        # Prepare the entry into the state from 'After Reload'.
        # => Emtpy transition action, nothing to do.
        ta = TransitionAction()
        if TheAnalyzer.engine_type.is_FORWARD(): ta.command_list = CommandList(InputPIncrement(), InputPDereference())
        else:                                    ta.command_list = CommandList(InputPDecrement(), InputPDereference())

        assert self.index in TheAnalyzer.state_db
        self.entry.action_db.enter(TransitionID(self.index, reload_state.index, 0), ta)
        # Need to categorize here, all other transitions have been categorized before
        self.entry.action_db.categorize(self.index)

        # Prepare the ReloadState for an entry from this state.
        on_success_door_id = self.entry.action_db.get_door_id(self.index, TheAnalyzer.reload_state.index)

        if TheAnalyzer.is_init_state_forward(self.index):
            on_failure_door_id = DoorID.global_terminal_end_of_file()
        else:
            on_failure_door_id = DoorID.drop_out(self.index)
        assert on_failure_door_id != on_success_door_id

        reload_door_id = reload_state.add_state(self.index, on_success_door_id, on_failure_door_id)

        # Ensure a transition on 'buffer limit code' to the reload procedure.
        self.transition_map.set_target(Setup.buffer_limit_code, reload_door_id)

    def get_string_array(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        txt = [ "State %s:\n" % repr(self.index).replace("L", "") ]
        # if InputF:         txt.append("  .input: move position %s\n" % repr(self.input))
        if EntryF:         txt.append("  .entry:\n"); txt.append(repr(self.entry))
        if TransitionMapF: txt.append("  .transition_map:\n")
        if DropOutF:       txt.extend(["  .drop_out:\n",    repr(self.drop_out)])
        txt.append("\n")
        return txt

    def get_string(self, InputF=True, EntryF=True, TransitionMapF=True, DropOutF=True):
        return "".join(self.get_string_array(InputF, EntryF, TransitionMapF, DropOutF))

    def __repr__(self):
        return self.get_string()

#__________________________________________________________________________
#
# ReloadState:
#                  .--------------------------------------------.
#  .-----.         |                                            |
#  | 341 |--'load'--> S = 341;                                  |
#  '-----'         |  F = DropOut(341); --.            .----------> goto S
#  .-----.         |                      |           / success |
#  | 412 |--'load'--> S = 412;            |          /          |
#  '-----'         |  F = DropOut(412); --+--> Reload           |
#  .-----.         |                      |          \          |
#  | 765 |--'load'--> S = 765;            |           \ failure |
#  '-----'         |  F = DropOut(765); --'            '----------> goto F
#                  |                                            |
#                  '--------------------------------------------'
# 
# The entry of the reload state sets two variables: The address where to
# go if the reload was successful and the address where to go in case that
# the reload fails. 
#__________________________________________________________________________
class ReloadState(Processor):
    def __init__(self, EngineType):
        if EngineType.is_FORWARD(): index = E_StateIndices.RELOAD_FORWARD
        else:                       index = E_StateIndices.RELOAD_BACKWARD
        Processor.__init__(self, index, Entry())

    def remove_states(self, StateIndexSet):
        self.entry.action_db.remove_transition_from_states(StateIndexSet)

    def absorb(self, OtherReloadState):
        # Do not absorb RELOAD_FORWARD into RELOAD_BACKWARD, and vice versa.
        assert self.index == OtherReloadState.index
        self.entry.action_db.absorb(OtherReloadState.entry.action_db)

    def add_state(self, StateIndex, OnSuccessDoorId, OnFailureDoorId, BeforeReload=None):
        """Adds a state from where the reload state is entered. When reload is
        done it jumps to 'OnFailureDoorId' if the reload failed and to 'OnSuccessDoorId'
        if the reload succeeded.

        RETURNS: DoorID into the reload state. Jump to this DoorID in order
                 to trigger the reload for the state given by 'StateIndex'.
        """
        assert BeforeReload is None or isinstance(BeforeReload, CommandList) 
        ta = TransitionAction()
        ta.command_list = CommandList(PrepareAfterReload(OnSuccessDoorId, OnFailureDoorId))
        if BeforeReload is not None:
            ta.command_list.extend(BeforeReload)

        tid = TransitionID(self.index, StateIndex, 0)
        assert self.entry.action_db.get(tid) is None # Cannot be in there twice!

        # No two transitions into the reload state have the same CommandList!
        # No two transitions can have the same DoorID!
        # => it is safe to assign a new DoorID withouth .categorize()
        ta.door_id = self.entry.action_db.new_DoorID(self.index)

        self.entry.action_db.enter(tid, ta)

        return ta.door_id

#__________________________________________________________________________
#
# TerminalState:
#                    .-------------------------------------------------.
#  .-----.           |                                                 |
#  | 341 |--'accept'--> input_p = position[2]; --->---+---------.      |
#  '-----'           |  set terminating zero;         |         |      |
#  .-----.           |                                |    .---------. |
#  | 412 |--'accept'--> column_n += length  ------>---+    | pattern | |
#  '-----'           |  set terminating zero;         |    |  match  |--->
#  .-----.           |                                |    | actions | |
#  | 765 |--'accept'--> line_n += 2;  ------------>---'    '---------' |
#  '-----'           |  set terminating zero;                          |
#                    |                                                 |
#                    '-------------------------------------------------'
# 
# A terminal state prepares the execution of the user's pattern match 
# actions and the start of the next analysis step. For this, it computes
# line and column numbers, sets terminating zeroes in strings and resets
# the input pointer to the position where the next analysis step starts.
#__________________________________________________________________________
class TerminalState(Processor):
    __slots__ = ("action", "pattern_id")
    def __init__(self, PatternId, PatternMatchAction):
        Processor.__init__(self, state_index.get_terminal_state_index(PatternId), Entry())
        self.pattern_id = PatternId
        self.action     = PatternMatchAction

