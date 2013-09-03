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

       input -- determined how to access the character that is used for 
                transition triggering.

       transition_map -- telling what subsequent state is to be entered
                         dependent on the triggering character.

       drop_out -- contains information about what happens when the 
                   transition map cannot trigger on the character.
    ___________________________________________________________________________
    """
    __slots__ = ("__index", 
                 "__init_state_f", 
                 "__target_index_list", 
                 "__engine_type", 
                 "__state_machine_id",
                 "input", 
                 "entry", 
                 "map_target_index_to_character_set", 
                 "transition_map", 
                 "drop_out", 
                 "_origin_list")

    def __init__(self, SM_State, StateIndex, InitStateF, EngineType, FromStateIndexList):
        assert isinstance(SM_State, State)
        assert isinstance(StateIndex, (int, long))
        assert type(InitStateF) is bool
        assert isinstance(FromStateIndexList, set)

        self.__index        = StateIndex
        self.__init_state_f = InitStateF
        self.__engine_type  = EngineType

        if self.__init_state_f: 
            if E_StateIndices.NONE not in FromStateIndexList:
                FromStateIndexList.add(E_StateIndices.NONE)

        # Test "quex/engine/analyzer/mega_state/template/TEST/best_matching_pair.py" would not work!
        # assert len(FromStateIndexList) != 0

        # (*) Entry Action
        self.entry = EngineType.create_Entry(SM_State, StateIndex, FromStateIndexList)

        # (*) Transition
        self.transition_map      = TransitionMap.from_TargetMap(SM_State.target_map)
        self.__target_index_list = SM_State.target_map.get_map().keys()
        # Currently, the following is only used for path compression. If the alternative
        # is implemented, then the following is no longer necessary.
        self.map_target_index_to_character_set = SM_State.target_map.get_map()

        # (*) Drop Out
        self.drop_out     = EngineType.create_DropOut(SM_State)

        self._origin_list = SM_State.origins().get_list()

    @property
    def index(self):                  return self.__index
    def set_index(self, Value):       assert isinstance(Value, long); self.__index = Value
    @property
    def init_state_f(self):           return self.__init_state_f
    @property
    def init_state_forward_f(self):   return self.__init_state_f and self.__engine_type.is_FORWARD()
    @property
    def engine_type(self):            return self.__engine_type
    @property
    def target_index_list(self):      return self.__target_index_list
    @property
    def transition_map_empty_f(self): 
        L = len(self.transition_map)
        if   L > 1:  return False
        elif L == 0: return True
        elif self.transition_map[0][1].drop_out_f(): return True
        return False

    def prepare_for_reload(self, reload_state):
        """Prepares state for reload:
           (i)   Create entry from 'reload procedure'.
           (ii)  Create in reload state entry from this state, so
                 that reload is prepared propperly.
           (iii) Adapt the transition map, so that:
                 buffer_limit_code --> reload procedure.
           
        """
        assert reload_state.index in (E_StateIndices.RELOAD_FORWARD, E_StateIndices.RELOAD_BACKWARD)

        # Prepare the entry into the state from 'After Reload'.
        # => Emtpy transition action, nothing to do.
        self.entry.action_db.enter(TransitionID(self.index, reload_state.index, 0), 
                                   TransitionAction())

        # Prepare the ReloadState for an entry from this state.
        reload_state.add_state(self, self.init_state_f)

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
     | 341 |--'load'--> s = 341;                                  |
     '-----'         |  f = DropOut(341); --.            .----------> goto 's'
     .-----.         |                      |           / success |
     | 412 |--'load'--> s = 412;            |          /          |
     '-----'         |  f = DropOut(412); --+--> Reload           |
     .-----.         |                      |          \          |
     | 765 |--'load'--> s = 765;            |           \ failure |
     '-----'         |  f = DropOut(765); --'            '----------> goto 'f'
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

    def add_state(self, State, InitStateF):
        if InitStateF: command = PrepareAfterReload_InitState(State, self.index)
        else:          command = PrepareAfterReload(State, self.index)
        before_reload_action = TransitionAction()
        before_reload_action.command_list.misc.add(command)
        self.entry.action_db.enter(TransitionID(self.index, State.index, 0), 
                                   before_reload_action)

