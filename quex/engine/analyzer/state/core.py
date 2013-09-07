from   quex.engine.state_machine.core          import State
import quex.engine.state_machine.index         as     index
from   quex.engine.analyzer.transition_map     import TransitionMap
from   quex.engine.analyzer.state.entry        import Entry
from   quex.engine.analyzer.state.entry_action import TransitionID, TransitionAction, PrepareAfterReload_InitState, PrepareAfterReload
from   quex.engine.analyzer.mega_state.target  import TargetByStateKey_DROP_OUT
from   quex.blackboard  import setup as Setup, \
                               E_StateIndices, \
                               E_InputActions

class AnalyzerState(object):
    """________________________________________________________________________
    
    AnalyzerState consists of the following major components:

       entry -- tells what has to happen at entry to the state (depending 
                on the state from which it is entered).

       transition_map -- telling what subsequent state is to be entered
                         dependent on the triggering character.

       drop_out -- contains information about what happens when the 
                   transition map cannot trigger on the character.
    ___________________________________________________________________________
    """
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
    def from_State(SM_State, StateIndex, FromStateIndexList, EngineType):
        assert isinstance(SM_State, State)
        assert isinstance(StateIndex, (int, long))
        assert isinstance(FromStateIndexList, set)

        x = AnalyzerState(StateIndex, TransitionMap.from_TargetMap(SM_State.target_map))

        # Test "quex/engine/analyzer/mega_state/template/TEST/best_matching_pair.py" would not work!
        # assert len(FromStateIndexList) != 0

        # (*) Entry Action
        x.entry    = EngineType.create_Entry(SM_State, StateIndex, FromStateIndexList)
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
        self.entry.action_db.enter(TransitionID(self.index, reload_state.index, 0), 
                                   TransitionAction())

        # Prepare the ReloadState for an entry from this state.
        reload_state.add_state(self, TheAnalyzer.is_init_state_forward(self.index))

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

    def entries_empty_f(self):
        """The 'TemplateStateKeySet' commands cost nothing, so an easy condition for
           'all entries empty' is that the door_tree_root reports a cost of '0'.
        """
        return self.entry.action_db.has_commands_other_than_MegaState_Command()

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

    def add_state(self, State, InitStateForwardF):
        if InitStateForwardF: command = PrepareAfterReload_InitState(State, self.index)
        else:                 command = PrepareAfterReload(State, self.index)
        before_reload_action = TransitionAction()
        before_reload_action.command_list.misc.add(command)
        self.entry.action_db.enter(TransitionID(self.index, State.index, 0), 
                                   before_reload_action)

