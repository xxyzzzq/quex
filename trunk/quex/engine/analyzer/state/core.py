from   quex.engine.state_machine.core          import State
import quex.engine.state_machine.index         as     index
from   quex.engine.analyzer.transition_map     import TransitionMap
from   quex.engine.analyzer.state.entry        import Entry
from   quex.engine.analyzer.state.entry_action import TransitionID, TransitionAction, DoorID
from   quex.engine.analyzer.commands           import CommandList, PrepareAfterReload, InputPIncrement, InputPDecrement, InputPDereference
from   quex.engine.analyzer.mega_state.target  import TargetByStateKey_DROP_OUT
from   quex.blackboard  import setup as Setup, \
                               E_StateIndices, \
                               E_InputActions

#__________________________________________________________________________
#
# AnalyzerState consists of the following major components:
#
#   entry -- tells what has to happen at entry to the state (depending 
#            on the state from which it is entered).
#
#   transition_map -- telling what subsequent state is to be entered
#                     dependent on the triggering character.
#
#   drop_out -- contains information about what happens when the 
#               transition map cannot trigger on the character.
#__________________________________________________________________________
class AnalyzerState(object):
    __slots__ = ("__index", 
                 "entry", 
                 "drop_out", 
                 "map_target_index_to_character_set", 
                 "transition_map") 

    def __init__(self, StateIndex, TheTransitionMap):
        self.__index                           = StateIndex
        self.drop_out                          = None
        self.entry                             = None
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

    @property
    def index(self):                  return self.__index
    def set_index(self, Value):       assert isinstance(Value, long); self.__index = Value

    def prepare_for_reload(self, TheAnalyzer):
        """Prepares state for reload:
           (i)   Create entry from 'reload procedure'.
           (ii)  Create in reload state entry from this state, so
                 that reload is prepared propperly.
           (iii) Adapt the transition map, so that:
                 buffer_limit_code --> reload procedure.
           
        """
        reload_state = TheAnalyzer.reload_state
        assert reload_state.index in (E_StateIndices.RELOAD_FORWARD, E_StateIndices.RELOAD_BACKWARD)

        # Empty states simply drop_out, they do NOT reload.
        if self.transition_map.is_empty():
            return

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

        reload_state.add_state(self.index, on_success_door_id, on_failure_door_id)

        # Ensure a transition on 'buffer limit code' to the reload procedure.
        self.transition_map.set_target(Setup.buffer_limit_code, reload_state.index)

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

class ReloadState:
    """The 'reload' state shall partly be handled like a normal state. It does
    not have a transition map (i.e. 'input causes transition'). But it has an
    entry action database. That is dependent from where it is entered different
    things are done.

    A 'normal' state, for example sets the address where to go upon successful
    reload and the address where to go upon failure. 

                     ReloadState
                     .--------------------------------------------.
     .-----.         |                                            |
     | 341 |--'load'--> S = 341;                                  |
     '-----'         |  F = DropOut(341); --.            .----------> goto S
     .-----.         |                      |           / success |
     | 412 |--'load'--> S = 412;            |          /          |
     '-----'         |  F = DropOut(412); --+--> Reload           |
     .-----.         |                      |          \          |
     | 765 |--'load'--> S = 765;            |           \ failure |
     '-----'         |  F = DropOut(765); --'            '----------> goto F
                     |                                            |
                     '--------------------------------------------'
    """
    def __init__(self, EngineType):
        if EngineType.is_FORWARD(): self.index = E_StateIndices.RELOAD_FORWARD
        else:                       self.index = E_StateIndices.RELOAD_BACKWARD
        self.entry = Entry()

    def remove_states(self, StateIndexSet):
        self.entry.action_db.remove_transition_from_states(StateIndexSet)

    def absorb(self, OtherReloadState):
        # Do not absorb RELOAD_FORWARD into RELOAD_BACKWARD, and vice versa.
        assert self.index == OtherReloadState.index
        self.entry.action_db.absorb(OtherReloadState.entry.action_db)

    def add_state(self, StateIndex, OnSuccessDoorId, OnFailureDoorId):
        ta = TransitionAction()
        ta.command_list = CommandList(PrepareAfterReload(OnSuccessDoorId, OnFailureDoorId))

        self.entry.action_db.enter(TransitionID(self.index, StateIndex, 0), ta)

