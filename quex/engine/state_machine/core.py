from   quex.engine.misc.string_handling          import blue_print
#
from   quex.engine.interval_handling             import NumberSet, Interval
import quex.engine.state_machine.index           as     state_machine_index
from   quex.engine.state_machine.target_map      import TargetMap
from   quex.engine.state_machine.state_core_info import StateCoreInfo
from   quex.engine.state_machine.origin_list     import StateOriginList
from   quex.engine.tools                         import flatten_list_of_lists
from   quex.blackboard                           import E_IncidenceIDs, \
                                                        E_PreContextIDs, \
                                                        E_Border

from   copy      import deepcopy
from   operator  import attrgetter, itemgetter
from   itertools import ifilter, imap
from   collections import defaultdict
import sys

class State:
    # Information about all transitions starting from a particular state. 
    # Transitions are of two types:
    # 
    #  -- normal transitions: triggered when a character arrives that falls into 
    #                         a trigger set.
    #  -- epsilon transition: triggered when no other trigger of the normal 
    #                         transitions triggers.
    #
    # Objects of this class are to be used in class StateMachine, where a 
    # dictionary maps from a start state index to a State-object.
    ## Little Slower: __slots__ = ('__core', '__origin_list', '__target_map')
    def __init__(self, AcceptanceF=False, StateMachineID=E_IncidenceIDs.MATCH_FAILURE, StateIndex=-1L, 
                 AltOriginList=None, AltTM=None):
        """Contructor of a State, i.e. a aggregation of transitions.
        """
        if AltOriginList is None:
            self.__origin_list = StateOriginList([
                                      StateCoreInfo(AcceptanceID = StateMachineID, 
                                                    StateIndex   = StateIndex, 
                                                    AcceptanceF  = AcceptanceF)
                                 ])
            self.__target_map = TargetMap()
        else:
            assert AltTM is not None
            self.__origin_list = AltOriginList
            self.__target_map  = AltTM

    @staticmethod
    def new_merged_core_state(StateList, ClearF=False):
        result      = State()
        origin_list = StateOriginList()

        if not ClearF:
            for state in StateList:
                origin_list.merge(state.origins().get_list())
        else:
            for state in StateList:
                origin_list.merge_clear(state.origins().get_list())

        result.set_origins(origin_list)
        return result

    def merge_core_with(self, StateList):
        for state in StateList:
            self.__merge(state)

    def __merge(self, Other):
        self.origins().merge(Other.origins().get_list()) 

    def clone(self, ReplacementDictionary=None, StateIndex=None, PreContextReplacementDB=None, AcceptanceIDReplacementDB=None):
        """Creates a copy of all transitions, but replaces any state index with the ones 
           determined in the ReplacementDictionary."""
        assert ReplacementDictionary is None or isinstance(ReplacementDictionary, dict)
        assert StateIndex is None            or isinstance(StateIndex, long)
        result = State(AltOriginList = self.__origin_list.clone(PreContextReplacementDB=PreContextReplacementDB,
                                                                AcceptanceIDReplacementDB=AcceptanceIDReplacementDB),
                       AltTM         = self.__target_map.clone())

        # if replacement of indices is desired, than do it
        if ReplacementDictionary is not None:
            result.target_map.replace_target_indices(ReplacementDictionary)

        return result

    def core(self):
        assert False
        return self.__origin_list.get_list()[0]

    def origins(self):
        return self.__origin_list

    def set_origins(self, OriginList):
        assert isinstance(OriginList, StateOriginList)
        self.__origin_list = OriginList

    @property
    def target_map(self):
        return self.__target_map

    def is_acceptance(self):
        for origin in self.origins():
            if origin.is_acceptance(): return True
        return False

    def input_position_store_f(self):
        for origin in self.origins():
            if origin.input_position_store_f(): return True
        return False

    def input_position_restore_f(self):
        for origin in self.origins():
            if origin.input_position_restore_f(): return True
        return False

    def pre_context_id(self):
        for origin in self.origins():
            if origin.pre_context_id() != E_PreContextIDs.NONE: 
                return origin.pre_context_id()
        return E_PreContextIDs.NONE

    def set_acceptance(self, Value=True):
        origin = self.origins().get_the_only_one()
        origin.set_acceptance_f(Value)
        if Value == False and not origin.is_meaningful(): self.origins().remove_the_only_one()

    def set_input_position_store_f(self, Value=True):
        origin = self.origins().get_the_only_one()
        origin.set_input_position_store_f(Value)
        if Value == False and not origin.is_meaningful(): self.origins().remove_the_only_one()

    def set_input_position_restore_f(self, Value=True):
        origin = self.origins().get_the_only_one()
        origin.set_input_position_restore_f(Value)
        if Value == False and not origin.is_meaningful(): self.origins().remove_the_only_one()

    def set_pre_context_id(self, Value=True):
        origin = self.origins().get_the_only_one()
        origin.set_pre_context_id(Value)
        if Value == E_PreContextIDs.NONE and not origin.is_meaningful(): self.origins().remove_the_only_one()

    def mark_self_as_origin(self, AcceptanceID, StateIndex):
        origin = self.origins().get_the_only_one()
        origin.set_pattern_id(AcceptanceID)
        origin.state_index = StateIndex

    def add_origin(self, StateMachineID_or_StateOriginInfo, StateIdx=None, StoreInputPositionF=False):
        self.origins().add(StateMachineID_or_StateOriginInfo, StateIdx, 
                           StoreInputPositionF, self.is_acceptance())

    def add_transition(self, Trigger, TargetStateIdx): 
        self.__target_map.add_transition(Trigger, TargetStateIdx)

    def __repr__(self):
        return self.get_string()

    def get_string(self, StateIndexMap=None, Option="utf8", OriginalStatesF=True):
        # if information about origins of the state is present, then print
        msg = self.origins().get_string(OriginalStatesF)

        # print out transitionts
        msg += self.target_map.get_string("    ", StateIndexMap, Option)
        return " " + msg

    def get_graphviz_string(self, OwnStateIdx, StateIndexMap, Option):
        assert Option in ["hex", "utf8"]
        return self.target_map.get_graphviz_string(OwnStateIdx, StateIndexMap, Option)

class StateMachine(object):
    def __init__(self, InitStateIndex=None, AcceptanceF=False, InitState=None):

        if InitStateIndex is None: InitStateIndex = state_machine_index.get()
        self.init_state_index = InitStateIndex
            
        # State Index => State (information about what triggers transition to what target state).
        if InitState is None: InitState = State(AcceptanceF=AcceptanceF)
        self.states = { self.init_state_index: InitState }        

        # Get a unique state machine id 
        self.set_id(state_machine_index.get_state_machine_id())

    def clean_up(self):
        # Delete states which are not connected from the init state.
        self.delete_orphaned_states()
        # Delete states from where there is no connection to an acceptance state.
        self.delete_hopeless_states() 

    @staticmethod
    def from_sequence(Sequence):
        """Sequence is a list of one of the following:
            -- NumberSet
            -- Number
            -- Character
        """
        assert type(Sequence) == list
        result = StateMachine()
        result.add_transition_sequence(result.init_state_index, Sequence)
        return result

    @staticmethod
    def from_character_set(CharacterSet):
        result = StateMachine()
        result.add_transition(result.init_state_index, CharacterSet, AcceptanceF=True)
        return result

    def clone(self, ReplacementDB=None, PreContextReplacementDB=None, AcceptanceIDReplacementDB=None):
        """Clone state machine, i.e. create a new one with the same behavior,
        i.e. transitions, but with new unused state indices. This is used when
        state machines are to be created that combine the behavior of more
        then one state machine. E.g. see the function 'sequentialize'. Note:
        the state ids SUCCESS and TERMINATION are not replaced by new ones.

        RETURNS: cloned object if cloning successful
                 None          if cloning not possible due to external state references

        """
        def assert_transitivity(db):
            """Ids and their replacement remain in order, i.e. if x > y then db[x] > dv[y]."""
            if db is None: return
            prev_new = -1
            for old, new in sorted(db.iteritems(), key=itemgetter(0)): # x[0] = old value
                assert new > prev_new
                prev_new = new

        def assert_uniqueness(db):
            if db is None: return
            reference_set = set()
            for value in db.itervalues():
                assert value not in reference_set
                reference_set.add(value)

        assert_uniqueness(ReplacementDB)
        assert_uniqueness(PreContextReplacementDB)
        assert_uniqueness(AcceptanceIDReplacementDB)
        assert_transitivity(AcceptanceIDReplacementDB)

        # (*) create the new state machine
        #     (this has to happen first, to get an init_state_index)
        if ReplacementDB is not None: 
            result      = StateMachine(InitStateIndex=ReplacementDB[self.init_state_index])
            replacement = ReplacementDB
        else:                         
            result      = StateMachine()
            replacement = {}
            for state_idx in sorted(self.states.iterkeys()):
                # NOTE: The constructor already delivered an init state index to 'result'.
                #       Thus self's init index has to be translated to result's init index.
                if state_idx == self.init_state_index:
                    replacement[state_idx] = result.init_state_index
                else:
                    replacement[state_idx] = state_machine_index.get()

        for state_idx in self.states.iterkeys():
            new_state_idx = replacement[state_idx]
            result.states[new_state_idx] = \
                    self.states[state_idx].clone(replacement, 
                                                 PreContextReplacementDB=PreContextReplacementDB,
                                                 AcceptanceIDReplacementDB=AcceptanceIDReplacementDB)
        
        return result

    def normalized_clone(self, PreContextReplacementDB=None):
        index_map, dummy, dummy         = self.get_state_index_normalization()
        pre_context_map, pattern_id_map = self.get_pattern_and_pre_context_normalization()
        
        return self.clone(index_map, 
                          PreContextReplacementDB=pre_context_map, 
                          AcceptanceIDReplacementDB=pattern_id_map)

    def delete_orphaned_states(self):
        """Remove all orphan states.

        ORPHAN STATE: A state that is not connected to an init state. That is
                      it can never be reached from the init state.
        """
        for state_index in self.get_orphaned_state_index_list():
            if state_index == self.init_state_index: continue
            del self.states[state_index]

    def delete_hopeless_states(self):
        """Delete all hopeless states and transitions to them.

        HOPELESS STATE: A state that cannot reach an acceptance state.
                       (There is no connection forward to an acceptance state).
        """
        for i in self.get_hopeless_state_index_list():
            for state in self.states.itervalues():
                state.target_map.delete_transitions_to_target(i)
            if i == self.init_state_index: continue
            del self.states[i]

    def delete_transitions_on_number(self, Number):
        """This function deletes any transition on 'Value' to another
           state. The resulting orphaned states are deleted. The operation
           may leave orphaned states! They need to be deleted manually.
        """
        for state in self.states.itervalues():
            # 'items()' not 'iteritems()' because 'delete_transitions_to_target()'
            # may change the dictionaries content.
            for target_state_index, trigger_set in state.target_map.get_map().items():
                assert not trigger_set.is_empty()
                if not trigger_set.contains(Number): continue

                trigger_set.cut_interval(Interval(Number))
                # If the operation resulted in cutting the path to the target state, 
                # => then delete it.
                if trigger_set.is_empty():
                    state.target_map.delete_transitions_to_target(target_state_index)

        return

    def __dive_for_epsilon_closure(self, state_index, result):
        index_list = self.states[state_index].target_map.get_epsilon_target_state_index_list()
        for target_index in ifilter(lambda x: x not in result, index_list):
            result.add(target_index)
            self.__dive_for_epsilon_closure(target_index, result)

    def is_empty(self):
        """If state machine only contains the initial state that points nowhere,
           then it is empty.
        """
        if len(self.states) != 1: return False
        return self.states[self.init_state_index].target_map.is_empty()

    def is_init_state_a_target_state(self):
        init_state_index = self.init_state_index
        for state in self.states.values():
            target_state_index_list = state.target_map.get_target_state_index_list()
            if init_state_index in target_state_index_list: return True
        return False
        
    def is_DFA_compliant(self):
        for state in self.states.values():
            if state.target_map.is_DFA_compliant() == False: 
                return False
        return True

    def has_orphaned_states(self):
        """Detect whether there are states where there is no transition to them."""
        unique = set([])
        for state in self.states.values():
            unique.update(state.target_map.get_target_state_index_list())

        for state_index in self.states.keys():
            # The init state is never considered to be an 'orphan'
            if state_index not in unique and state_index != self.init_state_index: return True
        return False

    def has_acceptance_states(self):
        for state in self.states.itervalues():
            if state.is_acceptance(): return True
        return False

    def has_origins(self):
        for state in self.states.values():
            if len(state.origins()) > 1: return True
        return False

    def create_new_init_state(self, AcceptanceF=False):

        self.init_state_index = self.create_new_state()
        return self.init_state_index

    def create_new_state(self, AcceptanceF=False, StateIdx=None):
        if StateIdx is None: new_state_index = state_machine_index.get()
        else:                new_state_index = StateIdx

        self.states[new_state_index] = State(AcceptanceF)
        return new_state_index
        
    def add_transition(self, StartStateIdx, TriggerSet, TargetStateIdx = None, AcceptanceF = False):
        """Adds a transition from Start to Target based on a given Trigger.

           TriggerSet can be of different types: ... see add_transition()
           
           (see comment on 'State::add_transition)

           RETURNS: The target state index.
        """
        assert type(StartStateIdx) == long
        # NOTE: The Transition Constructor is very tolerant, so no tests on TriggerSet()
        #       assert TriggerSet.__class__.__name__ == "NumberSet"
        assert type(TargetStateIdx) == long or TargetStateIdx is None
        assert type(AcceptanceF) == bool

        # If target state is undefined (None) then a new one has to be created
        if TargetStateIdx is None:                       TargetStateIdx = state_machine_index.get()
        if self.states.has_key(StartStateIdx) == False:  self.states[StartStateIdx]  = State()        
        if self.states.has_key(TargetStateIdx) == False: self.states[TargetStateIdx] = State()
        if AcceptanceF:                                  self.states[TargetStateIdx].set_acceptance(True)

        self.states[StartStateIdx].add_transition(TriggerSet, TargetStateIdx)

        return TargetStateIdx
            
    def add_transition_sequence(self, StartIdx, Sequence, AcceptanceF=True):
        """Add a sequence of transitions which is ending with acceptance--optionally.
        """
        idx = StartIdx
        for x in Sequence:
            idx = self.add_transition(idx, x)
        if AcceptanceF:
            self.states[idx].set_acceptance(True)

    def add_epsilon_transition(self, StartStateIdx, TargetStateIdx=None, RaiseAcceptanceF=False):
        assert TargetStateIdx is None or type(TargetStateIdx) == long

        # create new state if index does not exist
        if not self.states.has_key(StartStateIdx):
            self.states[StartStateIdx] = State()
        if TargetStateIdx is None:
            TargetStateIdx = self.create_new_state(AcceptanceF=RaiseAcceptanceF)
        elif not self.states.has_key(TargetStateIdx):
            self.states[TargetStateIdx] = State()

        # add the epsilon target state
        self.states[StartStateIdx].target_map.add_epsilon_target_state(TargetStateIdx)     
        # optionally raise the state of the target to 'acceptance'
        if RaiseAcceptanceF: self.states[TargetStateIdx].set_acceptance(True)

        return TargetStateIdx

    def mark_state_origins(self, OtherStateMachineID=-1L):
        """Marks at each state that it originates from this state machine. This is
           important, when multiple patterns are combined into a single DFA and
           origins need to be traced down. In this case, each pattern (which is
           are all state machines) needs to mark the states with the state machine 
           identifier and the state inside this state machine.

           If OtherStateMachineID and StateIdx are specified other origins
              than the current state machine can be defined (useful for pre- and post-
              conditions).         

           DontMarkIfOriginsPresentF can be set to ensure that origin data structures
              are only provided for states where non is set yet. This can be unsed
              to ensure that every state has an origin structure related to it, without
              overiding existing ones.
        """
        assert type(OtherStateMachineID) == long

        if OtherStateMachineID == -1L: state_machine_id = self.__id
        else:                          state_machine_id = OtherStateMachineID

        for state_idx, state in self.states.items():
            state.mark_self_as_origin(state_machine_id, state_idx)

    def mount_to_acceptance_states(self, MountedStateIdx, 
                                   CancelStartAcceptanceStateF=True):
        """Mount on any acceptance state the MountedStateIdx via epsilon transition.
        """
        for state_idx, state in self.states.iteritems():
            # -- only handle only acceptance states
            # -- only consider state other than the state to be mounted
            if not state.is_acceptance():    continue
            if state_idx == MountedStateIdx: continue
            # add the MountedStateIdx to the list of epsilon transition targets
            state.target_map.add_epsilon_target_state(MountedStateIdx)
            # if required (e.g. for sequentialization) cancel the acceptance status
            if CancelStartAcceptanceStateF: 
                # If there was a condition to acceptance => Cancel it first
                state.set_pre_context_id(E_PreContextIDs.NONE) 
                state.set_acceptance(False)

    def mount_newline_to_acceptance_states(self, DOS_CarriageReturnNewlineF, InverseF=False):     
        """Adds the condition 'newline or border character' at the end of the given
           state machine. Acceptance is only reached when the newline or border
           occurs. 
           
           This function is used for begin of line or end of line pre-conditions,
           thus: IT DOES NOT SETUP A POST-CONDITITION in the sense that output is
           scanned but cursor is being reset after match!  The caller provides the
           post-condition modifications itself, if needed.

           We simply append to each acceptance state the trigger '\n' or
           BorderCharacter that leads to the new acceptance.  The old acceptance
           state is annulated.  
        """    
        assert type(DOS_CarriageReturnNewlineF) == bool
        assert type(InverseF)                   == bool

        old_acceptance_state_list = self.get_acceptance_state_list() 
        new_state_idx             = state_machine_index.get()
        new_state                 = State(StateIndex=new_state_idx)
        # New state must be just like any of the acceptance states (take the first).
        # The transition map, of course must be empty.
        new_state.origins().set([old_acceptance_state_list[0].origins().get_the_only_one().clone()])

        self.states[new_state_idx] = new_state

        if InverseF: sequence = [ord("\n"), ord("\r")]
        else:        sequence = [ord("\r"), ord("\n")]

        for state in old_acceptance_state_list:
            # Transition '\n' --> Acceptance
            state.add_transition(ord('\n'), new_state_idx)
            
            if DOS_CarriageReturnNewlineF:
                # Alternative Transition '\r\n' --> Acceptance
                aux_idx = self.create_new_state(AcceptanceF=False)
                state.add_transition(sequence[0], aux_idx)
                self.states[aux_idx].add_transition(sequence[1], new_state_idx)

            # (-) Cancel acceptance of old state
            state.origins().remove_the_only_one()
            
        return new_state_idx    

    def mount_to_initial_state(self, TargetStateIdx):
        """Adds an epsilon transition from initial state to the given 'TargetStateIdx'. 
        The initial states epsilon transition to TERMINATE is deleted."""

        assert self.states.has_key(self.init_state_index)

        self.states[self.init_state_index].target_map.add_epsilon_target_state(TargetStateIdx)

    def mount_cloned(self, OtherSM, OperationIndex, OtherStartIndex, OtherEndIndex):
        """Clone all states in 'OtherSM' which lie on the path from 'OtherStartIndex'
        to 'OtherEndIndex'. If 'OtherEndIndex' is None, then it ends when there's no further
        path to go. 

        State indices of the cloned states are generated by pairs of (other_i, OperationIndex).
        This makes it possible to refer to those states, even before they are generated.
        """
        assert OtherStartIndex is not None

        work_set = set([OtherStartIndex])

        if OtherEndIndex is None:   done_set = set()
        else:                       done_set = set([OtherEndIndex])

        while len(work_set) != 0:
            other_i     = work_set.pop()
            other_state = OtherSM.states[other_i]

            state_i = state_machine_index.map_state_combination_to_index((other_i, OperationIndex))
            done_set.add(state_i)

            state = self.states.get(state_i)
            if state is None:
                state = State(AcceptanceF=other_state.is_acceptance())
                self.states[state_i] = state

            for other_ti, other_trigger_set in other_state.target_map.get_map().iteritems():
                target_i = state_machine_index.map_state_combination_to_index((other_ti, OperationIndex))
                # The state 'target_i' either:
                #   -- exists, because it is in the done_set, or
                #   -- will be created because its correspondance 'other_i' is 
                #      added to the work set.
                state.add_transition(other_trigger_set, target_i)
                if target_i not in done_set:
                    assert other_i in OtherSM.states
                    work_set.add(other_ti)

        return

    def mount_cloned_until(self, OtherSM, OtherEndIndex, OperationIndex):
        self.mount_cloned(OtherSM, OperationIndex, 
                          OtherSM.init_state_index, OtherEndIndex)

    def mount_cloned_subsequent_states(self, OtherSM, OtherStartIndex, OperationIndex):
        """Mount a cloned instance of states following 'OtherStartIndex' in 
        'OtherSM' to this state machine. The start state in 'self' is determined
        by an index generated from (OtherStartIndex, OperationIndex). Indices of
        subsequent states are generated by the pairs (other_i, OperationIndex) 
        where 'other_i' is an index from 'OtherSM'. This way, the states
        remain referencable from outside and even before this operation.
        """
        self.mount_cloned(OtherSM, OperationIndex, OtherStartIndex, None)

    def filter_dominated_origins(self):
        for state in self.states.values(): 
            state.origins().delete_dominated()

    def transform_to_anti_pattern(self):
        """Anti Pattern: 
                          -- drop-out                  => transition to acceptance state.
                          -- transition to acceptances => drop-out
        """
        original_acceptance_state_index_list = self.get_acceptance_state_index_list()
        acceptance_state_index               = self.create_new_state(AcceptanceF=True)

        for state_index, state in self.states.iteritems():
            if state_index == acceptance_state_index: continue

            # Transform DropOuts --> Transition to Acceptance
            drop_out_trigger_set = state.target_map.get_drop_out_trigger_set_union()
            state.add_transition(drop_out_trigger_set, acceptance_state_index)

            # Transform Transitions to Acceptance --> DropOut
            transition_map = state.target_map.get_map()
            for target_index in original_acceptance_state_index_list:
                if transition_map.has_key(target_index):
                    state.target_map.delete_transitions_to_target(target_index)

        # All original target states are deleted
        for target_index in original_acceptance_state_index_list:
            del self.states[target_index]

    def get_id(self):
        assert isinstance(self.__id, long) or self.__id == E_IncidenceIDs.INDENTATION_HANDLER
        return self.__id  # core.id()

    def set_id(self, Value):
        assert isinstance(Value, long) or Value == E_IncidenceIDs.INDENTATION_HANDLER
        self.__id = Value # core.set_id(Value)

    def get_init_state(self):
        return self.states[self.init_state_index]

    def get_orphaned_state_index_list(self):
        """Find list of orphan states.

        ORPHAN STATE: A state that is not connected to an init state. That is
                      it can never be reached from the init state.
        """
        work_set      = set([ self.init_state_index ])
        connected_set = set()
        while len(work_set) != 0:
            state_index = work_set.pop()
            state       = self.states[state_index]
            connected_set.add(state_index)

            work_set.update((i for i in state.target_map.get_target_state_index_list()
                             if  i not in connected_set))

        # State indices in 'connected_set' have a connection to the init state.
        # State indice not in 'connected_set' do not. => Those are the orphans.

        return [ i for i in self.states.iterkeys() if i not in connected_set ]

    def get_hopeless_state_index_list(self):
        """Find list of hopeless states, i.e. states from one can never 
        reach an acceptance state. 
        
        HOPELESS STATE: A state that cannot reach an acceptance state.
                       (There is no connection forward to an acceptance state).
        """
        from_db = defaultdict(set)
        for state_index, state in self.states.iteritems():
            target_index_list = state.target_map.get_target_state_index_list()
            for target_index in target_index_list:
                from_db[target_index].add(state_index)

        work_set     = set(self.get_acceptance_state_index_list())
        reaching_set = set()  # set of states that reach acceptance states
        while len(work_set) != 0:
            state_index = work_set.pop()
            state       = self.states[state_index]
            reaching_set.add(state_index)

            work_set.update((i for i in from_db[state_index] if  i not in reaching_set))

        # State indices in 'reaching_set' have a connection to an acceptance state.
        # State indice not in 'reaching_set' do not. => Those are the hopeless.
        return [ i for i in self.states.iterkeys() if i not in reaching_set ]

    def get_epsilon_closure_db(self):
        db = {}
        for index, state in self.states.items():
            # Do the first 'level of recursion' without function call, to save time
            index_list = state.target_map.get_epsilon_target_state_index_list()

            # Epsilon closure for current state
            ec = set([index]) 
            if len(index_list) != 0: 
                for target_index in ifilter(lambda x: x not in ec, index_list):
                    ec.add(target_index)
                    self.__dive_for_epsilon_closure(target_index, ec)

            db[index] = ec

        return db

    def get_epsilon_closure_of_state_set(self, StateIdxList, EC_DB):
        """Returns the epsilon closure of a set of states, i.e. the union
           of the epsilon closures of the single states.
           
           StateIdxList: List of states to be considered.
           EC_DB:        Epsilon closure database, as computed once by
                         'get_epsilon_closure_db()'.
        """
        result = set()
        for index in StateIdxList:
            result.update(EC_DB[index])

        return result

    def get_epsilon_closure(self, StateIdx):
        """Return all states that can be reached from 'StateIdx' via epsilon
           transition."""
        assert self.states.has_key(StateIdx)

        result = set([StateIdx])

        self.__dive_for_epsilon_closure(StateIdx, result)

        return result
 
    def get_elementary_trigger_sets(self, StateIdxList, epsilon_closure_db):
        """NOTE: 'epsilon_closure_db' must previously be calculcated by 
                 self.get_epsilon_closure_db(). This has to happen once
                 and for all in order to save computation time.
        
           Considers the trigger dictionary that contains a mapping from target state index 
           to the trigger set that triggers to it: 
     
                   target_state_index   --->   trigger_set 
    
           The trigger sets of different target state indices may intersect. As a result,
           this function produces a list of pairs:
    
                  [ state_index_list, elementary_trigger_set ]
    
           where the elementary trigger set is the set of all triggers that trigger
           at the same time to all states in the state_index_list. The list contains 
           for one state_index_list only one elementary_trigger_set. All elementary
           trigger sets are disjunct, i.e. they do not intersect.
    
          NOTE: A general solution of this problem would have to consider the 
                inspection of all possible subset combinations. The number of 
                combinations for N trigger sets is 2^N - which potentially blows
                the calculation power of the computer. Excessive optimizations
                would have to be programmed, if not the following were the case: 
    
          NOTE: Fortunately, we are dealing with one dimensional sets! Thus, there is
                a very effective way to determine the elementary trigger sets. Imagine
                three trigger sets stretching over the range of numbers as follows:

          different targets, e.g. T0, T1, T2 are triggered by different sets of letters
          in the alphabet. 
                                                                    letters of alphabet
                      ---------------------------------------------------->

                  T0  [---------)       [----------)
                  T1          [------)      [-----)
                  T2              [----------------------)    
    
          => elementary sets: 
     
             only T0  [-------)
             T0, T1           [-)
             only T1            [-)
             T1, T2               [--)
             only T2                 [---)          [----)
             T0, T2                      [---)     [)
             T0, T1, T2                      [-----)
        """
        # For Documentation Purposes: The following approach has been proven to be SLOWER
        #                             then the one currently implemented. May be, some time
        #                             it can be tweaked to be faster.
        #
        #                             Also, it is not proven to be correct! 
        #
        ##    trigger_list = []
        ##    for state_index in StateIdxList:
        ##        state = self.states[state_index]
        ##        for target_index, trigger_set in state.target_map.get_map().iteritems():
        ##            target_epsilon_closure = epsilon_closure_db[target_index] 
        ##            interval_list          = trigger_set.get_intervals(PromiseToTreatWellF=True)
        ##            trigger_list.extend([x, target_epsilon_closure] for x in interval_list])
        ##
        ##    trigger_list.sort(key=lambda x: x[0].begin)
        ##    for element in trigger_list:
        ##        # ... continue as shown below
        ##                
        ##    return combination_list

        ## Special Case -- Quickly Done: One State, One Target State
        ##        proposal = None
        ##        if len(StateIdxList) == 1:
        ##           state_idx = list(StateIdxList)[0]
        ##            if len(epsilon_closure_db[state_idx]) == 1:
        ##                if len(self.states[state_idx].target_map.get_map()) == 1:
        ##                    target, trigger_set = self.states[state_idx].target_map.get_map().items()[0]
        ##                    proposal = { (target,): NumberSet(trigger_set) }

        # (*) Accumulate the transitions for all states in the state list.
        #     transitions to the same target state are combined by union.
        history = flatten_list_of_lists(
            # -- trigger dictionary:  target_idx --> trigger set that triggers to target
            self.states[state_idx].target_map.get_trigger_set_line_up() 
            # NOTE: Duplicate entries in history are perfectly reasonable at this point,
            #       simply if two states trigger on the same character range to the same 
            #       target state. When ranges are opened/closed via the history items
            #       this algo keeps track of duplicates (see below).
            for state_idx in StateIdxList
        )

        # (*) sort history according to position
        history.sort(key = attrgetter("position")) # lambda a, b: cmp(a.position, b.position))

        # (*) build the elementary subset list 
        combinations           = {}          # use dictionary for uniqueness
        current_interval_begin = None
        current_target_indices = {}          # use dictionary for uniqueness
        current_target_epsilon_closure = []
        for item in history:
            # -- add interval and target indice combination to the data
            #    (only build interval when current begin is there, 
            #     when the interval size is not zero, and
            #     when the epsilon closure of target states is not empty)                   
            if current_interval_begin is not None and \
               current_interval_begin != item.position and \
               len(current_target_indices) != 0:

                interval = Interval(current_interval_begin, item.position)

                # current_target_epsilon_closure.sort()             
                key = tuple(sorted(current_target_epsilon_closure))
                ## Caused 3 failures in unit test:
                ## if len(current_target_epsilon_closure) == 1: key = current_target_epsilon_closure[0]  
                ## else:                                        key = tuple(sorted(current_target_epsilon_closure))
                combination = combinations.get(key)
                if combination is None:
                    combinations[key] = NumberSet(interval, ArgumentIsYoursF=True)
                else:
                    combination.unite_with(interval)
           
            # -- BEGIN / END of interval:
            #    add or delete a target state to the set of currently considered target states
            #    NOTE: More than one state can trigger on the same range to the same target state.
            #          Thus, one needs to keep track of the 'opened' target states.
            if item.change == E_Border.BEGIN:
                if current_target_indices.has_key(item.target_idx):
                    current_target_indices[item.target_idx] += 1
                else:
                    current_target_indices[item.target_idx] = 1
            else:        # == E_Border.END
                if current_target_indices[item.target_idx] > 1:
                    current_target_indices[item.target_idx] -= 1
                else:    
                    del current_target_indices[item.target_idx] 
    
            # -- re-compute the epsilon closure of the target states
            current_target_epsilon_closure = \
                self.get_epsilon_closure_of_state_set(current_target_indices.iterkeys(),
                                                      epsilon_closure_db)
            # -- set the begin of interval to come
            current_interval_begin = item.position                      
    
        ## if proposal is not None:
        ##    if    len(proposal)     != len(combinations) \
        ##       or proposal.keys()   != combinations.keys() \
        ##       or not proposal.values()[0].is_equal(combinations.values()[0]):
        ##        print "##proposal:    ", proposal
        ##        print "##combinations:", combinations

        # (*) create the list of pairs [target-index-combination, trigger_set] 
        return combinations

    def get_acceptance_state_list(self):
        return [ state for state in self.states.itervalues() if state.is_acceptance() ]

    def get_acceptance_state_index_list(self, AcceptanceID=None):
        if AcceptanceID is None:
            return [ index for index, state in self.states.iteritems() if state.is_acceptance() ]
        else:
            return [ index for index, state in self.states.iteritems() if state.is_acceptance() and state.origins().get_the_only_one().acceptance_id() == AcceptanceID ]

    def get_from_to_db(self):
        """RETURNS:
             [0] from_db:  state_index --> states from which it is entered.
             [1] to_db:    state_index --> states which it enters
        """
        from_db = defaultdict(set)
        to_db   = defaultdict(set)
        for from_index, state in self.states.iteritems():
            to_db[from_index] = set(state.target_map.get_map().iterkeys())
            for to_index in state.target_map.get_map().iterkeys():
                from_db[to_index].add(from_index)
        return from_db, to_db

    def match_sequence(self, UserSequence):
        """RETURNS: True, if the sequences ends in an acceptance state.
                    False, if not.

        Works for NFA and DFA.

        '__dive' --> consider implementing with TreeWalker to avoid stack allocation
        trouble.
        """
        assert type(UserSequence) == list

        def dive(StateIndex, Sequence):
            if len(Sequence) == 0:
                return self.states[StateIndex].is_acceptance()

            idx_list = self.states[StateIndex].target_map.get_resulting_target_state_index_list(Sequence[0])
            for candidate in idx_list:
                # One follow-up state could match the sequence
                if dive(candidate, Sequence[1:]): return True
            # No possible follow-up state could match the sequence
            return False

        # Walk with the sequence the state machine
        return dive(self.init_state_index, UserSequence)

    def get_number_sequence(self):
        """Returns a number sequence that represents the state machine.
        If the state machine cannot be represented by a plain chain of 
        number, then it returns 'None'.

        Assumes: State machine is 'beautified'.
        """
        state  = self.get_init_state()
        result = []
        while 1 + 1 == 2:
            target_map = state.target_map.get_map()
            if   len(target_map) == 0:
                return result
            elif len(target_map) > 1:
                return None

            target_index, trigger_set = target_map.iteritems().next() 
            number      = trigger_set.get_the_only_element()
            if number is None:
                return None
            result.append(number)
            state = self.states[target_index]

    def get_number_set(self):
        """Returns a number set that represents the state machine.
        If the state machine cannot be represented by a plain NumberSet,
        then it returns 'None'.

        Assumes: State machine is 'beautified'.
        """
        if len(self.states) != 2:
            return None

        # There can be only one target state from the init state
        target_map = self.get_init_state().target_map.get_map()
        if len(target_map) != 1:
            return None

        return target_map.itervalues().next()

    def get_beginning_character_set(self):
        """Return the character set union of all triggers in the init state.
        """
        return self.get_init_state().target_map.get_trigger_set_union()

    def get_ending_character_set(self):
        """Returns the union of all characters that trigger to an acceptance
           state in the given state machine. This is to detect whether the
           newline or suppressor end with an indentation character (grid or space).
        """
        result = NumberSet()
        for end_state_index in self.get_acceptance_state_index_list():
            for state in self.states.itervalues():
                if state.target_map.has_target(end_state_index) == False: continue
                result.unite_with(state.target_map.get_trigger_set_to_target(end_state_index))
        return result

    def get_only_entry_to_state(self, TargetStateIndex):
        """Checks if the given state has only one entry from another state 
           and if so it returns the state index. Otherwise, it returns None.
        """
        result = None
        for state_index, state in self.states.items():
            if state.target_map.has_target(TargetStateIndex):
                if result is None: result = state_index
                else:              return None           # More than one state trigger to target
        return result

    def get_state_index_normalization(self, NormalizeF=True):
        index_map         = {}
        inverse_index_map = {}

        index_sequence = self.__get_state_sequence_for_normalization()
        if NormalizeF:
            counter = -1L
            for state_i in index_sequence:
                counter += 1L
                index_map[state_i]         = counter
                inverse_index_map[counter] = state_i
        else:
            for state_i in index_sequence:
                index_map[state_i]         = state_i
                inverse_index_map[state_i] = state_i

        return index_map, inverse_index_map, index_sequence

    def get_pattern_and_pre_context_normalization(self, PreContextID_Offset=None, AcceptanceID_Offset=None):
        pre_context_id_set = set()
        pattern_id_set     = set()
        def enter(collection, Value, TheEnum):
            if Value not in TheEnum:
                collection.add(Value)

        for state in self.states.itervalues():
            for origin in state.origins():
                enter(pre_context_id_set, origin.pre_context_id(), E_PreContextIDs)
                enter(pattern_id_set,     origin.acceptance_id(),  E_IncidenceIDs)

        def get_map(id_set, Offset):
            """The 'order' of the IDs must be maintained! In particular, a 
            AcceptanceID with higher precedence than another, must remain of 
            higher precedence."""
            result = {}
            for x in sorted(id_set):
                result[x] = long(len(result) + Offset)
            return result

        if PreContextID_Offset is None: PreContextID_Offset = 1 # Avoid ID = 0
        if AcceptanceID_Offset is None: AcceptanceID_Offset    = 1 # Avoid ID = 0
        assert PreContextID_Offset > 0
        assert AcceptanceID_Offset    > 0
        return get_map(pre_context_id_set, PreContextID_Offset), \
               get_map(pattern_id_set, AcceptanceID_Offset)

    def get_string(self, NormalizeF=False, Option="utf8", OriginalStatesF=True):
        assert Option in ["utf8", "hex"]

        # (*) normalize the state indices
        index_map, inverse_index_map, index_sequence = self.get_state_index_normalization(NormalizeF)

        # (*) construct text 
        msg = "init-state = " + repr(index_map[self.init_state_index]) + "\n"
        for state_i in index_sequence:
            printed_state_i = index_map[state_i]
            state           = self.states[state_i]
            msg += "%05i" % printed_state_i + state.get_string(index_map, Option, OriginalStatesF)

        return msg

    def get_graphviz_string(self, NormalizeF=False, Option="utf8"):
        assert Option in ["hex", "utf8"]

        # (*) normalize the state indices
        index_map, inverse_index_map, index_sequence = self.get_state_index_normalization(NormalizeF)

        # (*) Border of plot block
        frame_txt  = "digraph state_machine_%i {\n" % self.get_id()
        frame_txt += "rankdir=LR;\n"
        frame_txt += "size=\"8,5\"\n"
        frame_txt += "node [shape = doublecircle]; $$ACCEPTANCE_STATES$$\n"
        frame_txt += "node [shape = circle];\n"
        frame_txt += "$$TRANSITIONS$$"
        frame_txt += "}\n"

        transition_str       = ""
        acceptance_state_str = ""
        for printed_state_i, state in sorted(imap(lambda i: (index_map[i], self.states[i]), index_sequence)):
            if state.is_acceptance(): 
                acceptance_state_str += "%i; " % int(printed_state_i)
            transition_str += state.get_graphviz_string(printed_state_i, index_map, Option)

        if acceptance_state_str != "": acceptance_state_str = acceptance_state_str[:-2] + ";"
        return blue_print(frame_txt, [["$$ACCEPTANCE_STATES$$", acceptance_state_str ],
                                      ["$$TRANSITIONS$$",       transition_str]])
        
    def iterable_target_state_indices(self, StateIndex):
        return self.state_db[StateIndex].iterable_target_state_indices(StateIndex)

    def __get_state_sequence_for_normalization(self):

        result     = []
        work_stack = [ self.init_state_index ]
        done_set   = set()
        while len(work_stack) != 0:
            i = work_stack.pop()
            if i in done_set: continue

            result.append(i)
            done_set.add(i)
            state = self.states[i]

            # Decide which target state is to be considered next.
            # sort by 'lowest trigger'
            def comparison_key(state_db, tm, A):
                trigger_set_to_A = tm.get(A)
                assert trigger_set_to_A is not None
                trigger_set_min = trigger_set_to_A.minimum()
                target_tm       = state_db[A].target_map.get_map()
                target_branch_n = len(target_tm)
                if len(target_tm) == 0: target_tm_min = -sys.maxint
                else:                   target_tm_min = min(map(lambda x: x.minimum(), target_tm.itervalues()))
                return (trigger_set_min, target_branch_n, target_tm_min, A)

            tm = state.target_map.get_map()
            target_state_index_list = [ k for k in tm.iterkeys() if k not in done_set ]
            target_state_index_list.sort(key=lambda x: comparison_key(self.states, tm, x), reverse=True)

            work_stack.extend(target_state_index_list)
                                         
        # There might be 'orphans' which are not at all connected. Append them
        # sorted by a simple rule: by state index.
        if len(self.states) != len(result):
            for i in sorted(self.states.iterkeys()):
                if i in result: continue
                result.append(i)

        # DEBUG: double check that the sequence is complete
        x = self.states.keys(); x.sort()  # DEBUG
        y = deepcopy(result);   y.sort()  # DEBUG
        assert x == y                     # DEBUG

        return result

    def __repr__(self):
        return self.get_string(NormalizeF=True)

    def assert_consistency(self):
        """Check: -- whether each target state in contained inside the state machine.
        """
        target_state_index_list = self.states.keys()
        for index, state in self.states.items():
            for target_state_index in state.target_map.get_target_state_index_list():
                assert target_state_index in target_state_index_list, \
                       "state machine contains target state %s that is not contained in itself." \
                       % repr(target_state_index) + "\n" \
                       "present state indices: " + repr(self.states.keys()) + "\n" + \
                       "state machine = " + self.get_string(NormalizeF=False)

            
