import sys
from copy import copy, deepcopy

from   quex.frs_py.string_handling import blue_print
#
from   quex.core_engine.interval_handling        import NumberSet, Interval
import quex.core_engine.state_machine.index      as     state_machine_index
from   quex.core_engine.state_machine.transition      import Transition, EpsilonTransition
from   quex.core_engine.state_machine.transition_map  import TransitionMap
from   quex.core_engine.state_machine.state_core_info import StateCoreInfo
from   quex.core_engine.state_machine.origin_list     import StateOriginList
#
import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label
#
from   quex.core_engine.state_machine.index import map_state_combination_to_index, \
                                                   get_state_machine_by_id


# definitions for 'history items':
INTERVAL_BEGIN            = True
INTERVAL_END              = False
# real (uni-code) character codes start at zero, thus, it is safe to use 
# -7777 as a marker for undefined borders.
INTERVAL_UNDEFINED_BORDER = -7777

        
class StateInfo:
    # Information about all transitions starting from a particular state. Transitions are
    # of two types:
    #   
    #      -- normal transitions: triggered when a character arrives that falls into 
    #                             a trigger set.
    #      -- epsilon transition: triggered when no other trigger of the normal transitions
    #                             triggers.
    #
    # Objects of this class are to be used in class StateMachine, where a dictionary maps 
    # from a start state index to a StateInfo-object.
    #
    #####################################################################################    
    def __init__(self, AcceptanceF=False, StateMachineID=-1L, StateIndex=-1L):
        """Contructor of a State, i.e. a aggregation of transitions.
        """
        self.__core        = StateCoreInfo(StateMachineID, StateIndex, AcceptanceF=AcceptanceF)
        self.__origin_list = StateOriginList()

        # normal transitions: trigger, action, target-state-index
        self.__transition_map = TransitionMap()

    def core(self):
        return self.__core

    def origins(self):
        return self.__origin_list

    def merge(self, Other):
        # merge core information of self with other state
        self.core().merge(Other.core())
        if   Other.origins().is_empty(): return 
        elif self.origins().is_empty():  
            self.origins().set(Other.origins().get_list())
        else: 
            self.origins().append(Other.origins().get_list(), 
                                  StoreInputPositionFollowsAcceptanceF=False,
                                  SelfAcceptanceF=self.is_acceptance())

    def transitions(self):
        return self.__transition_map()

    def get_origin_list(self):
        return self.origins().get_list()

    def get_transition_list(self):
        return self.__transition_map.get_list()  

    def get_epsilon_trigger_set(self):
        return self.__transition_map.get_trigger_set_union().inverse()

    def get_epsilon_target_state_indices(self):
        return self.__transition_map.get_epsilon_target_state_index_list()

    def get_normal_target_states(self):
        self.transition_map().get_non_epsilon_target_state_index_list()

    def get_target_state_indices(self):
        return self.transition_map().get_target_state_index_list()
        
    def get_result_list(self, Trigger):
        """Returns the set of resulting target states."""
        assert type(Trigger) == int
        return self.__transition_map.get_resulting_target_state_index_list(Trigger)


    def get_result_state_index(self, Trigger):
        """Return one target state that is triggered by the given trigger.
           (there should not be more in a DFA, but in an NFA ...).
        """
        return self.__transition_map.get_resulting_target_state_index(Trigger)
    
    def get_trigger_set_union(self):
        """Returns union of all trigger sets that lead to a target state. Useful
           in order to determine wether a state triggers on some trigger or not.
        """
        return self.__transition_map.get_trigger_set_union().inverse()

    def get_trigger_set_to_target(self, TargetIdx=None):
        return self.__transition_map.get_trigger_set_to_target(TargetIdx)

    def get_trigger_dictionary(self, ConsiderEpsilonTransition=False):
        return self.__transition_map.get_map()
        
    def get_trigger_set_line_up(self):
        return self.__transition_map.get_trigger_set_line_up()

    def get_trigger_map(self):
        return self.__transition_map.get_trigger_map()

    def is_empty(self):
        return self.__transition_map.is_empty()

    def is_acceptance(self):
        return self.core().is_acceptance()
        
    def is_post_conditioned(self):
        """Goes through the list of all origins, if one origin is post-conditioned,
           it means that state is post conditioned. 
        """   
        if self.core().post_conditioned_acceptance_f(): return True
        return self.origins().contains_post_condition_flag()

    def is_store_input_position(self):
        """If one of the origins requires to store the input position, the state requires
           to store the input position."""
        if self.core().store_input_position_f(): return True
        return self.origins().contains_store_input_position()

    def is_DFA_compliant(self):
        return self.__transition_map.is_DFA_compliant()

    def has_trivial_pre_condition_begin_of_line_f(self):
        if self.core().pre_condition_begin_of_line_f(): return True
        return self.origins().contains_pre_condition_begin_of_line()

    def has_one_of_triggers(self, CharacterCodeList):
        assert type(CharacterCodeList) == list
        return self.__transition_map.has_one_of_triggers(CharacterCodeList)

    def has_trigger(self, CharacterCode):
        return self.__transition_map.has_trigger(CharacterCode)

    def has_origin(self):
        return not self.origins().is_empty()

    def set_acceptance(self, Value=True, LeaveStoreInputPositionF=False):
        self.core().set_acceptance_f(Value, LeaveStoreInputPositionF)

    def set_store_input_position_f(self, Value):
        """Sets the 'store_input_position_flag' for all origins."""
        for origin in self.origins().get_list():
            origin.set_store_input_position_f(Value)    

    def set_pseudo_ambiguous_post_condition_id(self, Value):
        """Sets a reference to the detector of the pseudo ambidguous post condition."""
        for origin in self.origins().get_list():
            origin.set_pseudo_ambiguous_post_condition_id(Value)    
    
    def set_trivial_pre_condition_begin_of_line(self, Value=True):
        for origin in self.origins().get_list():
            origin.set_pre_condition_begin_of_line_f(Value)     
    
    def set_pre_condition_id(self, PreConditionStateMachineID):
        """Sets the 'pre_condition_id' for all origins."""
        for origin in self.origins().get_list():
            origin.set_pre_condition_id(PreConditionStateMachineID)     

    def set_post_conditioned_acceptance_f(self, Value):
        """Sets the 'post_conditioned_acceptance_flag' for all origins."""
        for origin in self.origins().get_list():
            origin.set_post_conditioned_acceptance_f(Value)     

    def add_origin(self, StateMachineID_or_StateOriginInfo, StateIdx=None, StoreInputPositionF=None):
        self.origins().add(StateMachineID_or_StateOriginInfo, StateIdx, 
                           StoreInputPositionF, self.is_acceptance())

    def add_origin_list(self, OriginList, StoreInputPositionFollowsAcceptanceF=True):
        self.origins().append(OriginList, StoreInputPositionFollowsAcceptanceF, 
                              SelfAcceptanceF=self.is_acceptance())
                
    def add_epsilon_target_state(self, TargetStateIdx):
        self.__transition_map.add_epsilon_target_state(TargetStateIdx)

    def add_transition(self, Trigger, TargetStateIdx): 
        self.__transition_map.add_transition(Trigger, TargetStateIdx)
    
    def replace_target_index(self, OriginalIdx, NewTargetIdx):
        self.__transition_map.replace_target_index(OriginalIdx, NewTargetIdx)

    def replace_drop_out_target_states_with_adjacent_targets(self):
        return self.__transition_map.replace_drop_out_target_states_with_adjacent_targets()

    def delete_transitions_on_character_list(self, CharacterCodeList):
        self.__transition_map.delete_transitions_on_character_list(CharacterCodeList)

    def delete_transitions_on_empty_trigger_sets(self):
        self.__transition_map.delete_transitions_on_empty_trigger_sets(CharacterCodeList)

    def delete_epsilon_target_state(self, TargetStateIdx):
        self.__transition_map.delete_epsilon_target_state(TargetStateIdx)

    def delete_meaningless_origins(self):
        self.origins().delete_meaningless()

    def adapt_origins(self, StateMachineID, StateIndex):
        """Adapts all origins so that their original state is 'StateIndex' in state machine
           'StateMachineID'. Post- and pre-condition flags remain, and so the store input 
           position flag.
        """
        self.core().state_machine_id = StateMachineID
        self.core().state_index      = StateIndex
        self.origins().adapt(StateMachineID, StateIndex)

    def filter_dominated_origins(self):
        """This function is a simplification in order to allow the Hopcroft Optimization
           to be more efficient. It 'simulates' the code generation where the first unconditional
           pattern matches. The remaining origins of a state are redundant.

           This function is to be seen in analogy with the function 'get_acceptance_detector'. 
           Except for the fact that it requires the 'end of core pattern' markers of post
           conditioned patterns. If the markers are not set, the store input position commands
           are not called properly, and when restoring the input position bad bad things happen 
           ... i.e. segmentation faults.
        """
        self.origins().delete_dominated()

    def clone(self, ReplacementDictionary=None):
        """Creates a copy of all transitions, but replaces any state index with the ones 
           determined in the ReplacementDictionary."""
        result = StateInfo()
        result.__core            = deepcopy(self.__core)
        result.__transition_list = deepcopy(self.__transition_list)
        result.__origin_list     = deepcopy(self.__origin_list)
        # if replacement of indices is desired, than do it
        if ReplacementDictionary != None:
            for ti, replacement_ti in ReplacementDictionary.items():
                result.replace_target_index(ti, replacement_ti)
        return result

    def verify_unique_origin(self, StateMachineID, StateIdx):
        """Verify that there is only one origin and that this origin has a state machine id
           and state id as given by the first and second argument. 

           See also: StateMachine::verify_single_origin()
        """   
        if self.core().state_machine_id != StateMachineID: return False
        if self.core().state_index      != StateIndex:     return False
        return self.origins().is_from_single_state(StateMachineID, StateIdx)

    def __repr__(self):
        return self.get_string()

    def get_string(self, StateIndexMap=None):
        # if information about origins of the state is present, then print
        msg = self.origins().get_string()
        fill_str = ""
        if msg != "": fill_str = "     "

        msg = self.core().get_string(StateMachineAndStateInfoF=False) + msg

        # print out transitionts
        sorted_transitions = self.__transition_list
        sorted_transitions.sort(lambda a, b: cmp(a.target_state_index, b.target_state_index))

        # normal state transitions
        for t in sorted_transitions:
            # note: the fill string for the first line printed is empty, because
            #       the start stae is printed before  this.
            msg += "%s %s\n" % (fill_str, t.get_string(StateIndexMap=StateIndexMap))
            fill_str = "     "

        # the else transition
        msg += "%s %s\n" % (fill_str, self.__epsilon.get_string(StateIndexMap=StateIndexMap))
        return msg

    def get_graphviz_string(self, OwnStateIdx, StateIndexMap):
        msg = ""
        for t in self.__transition_list:
            # note: the fill string for the first line printed is empty, because
            #       the start stae is printed before  this.
            msg += "%i %s" % (OwnStateIdx, t.get_graphviz_string(StateIndexMap))

        # the epsilon transition
        if self.__epsilon.target_state_indices != []:
            msg += "%s" % self.__epsilon.get_graphviz_string(OwnStateIdx, StateIndexMap)
        return msg

    def mark_self_as_origin(self, StateMachineID, StateIndex):
        self.core().state_machine_id = StateMachineID
        self.core().state_index      = StateIndex
        # use the own 'core' as only origin
        self.origins().set([self.core()])

class StateMachine:

    def __init__(self, InitStateIndex=None, AcceptanceF=False, 
                 PreConditionStateMachine=None,
                 TrivialPreConditionBeginOfLineF=False,
                 TrivialPreConditionCharacterCodes=-1):

        # print "##state_machine_init"
        if InitStateIndex == None: self.init_state_index = state_machine_index.get()
        else:                      self.init_state_index = InitStateIndex
            
        # state-idx => StateInfo (information about what triggers
        #              transition to what target state).
        self.states = { self.init_state_index: StateInfo(AcceptanceF) }        
        
        # register this state machine and get a unique id for it
        self.__id = state_machine_index.register_state_machine(self)
      
        # by default, a state machine has no pre-condition
        self.pre_condition_state_machine = PreConditionStateMachine 

        self.__trivial_pre_condition_begin_of_line_f = TrivialPreConditionBeginOfLineF
            
    def clone(self):
        """Clone state machine, i.e. create a new one with the same behavior,
        i.e. transitions, but with new unused state indices. This is used when
        state machines are to be created that combine the behavior of more
        then one state machine. E.g. see the function 'sequentialize'. Note:
        the state ids SUCCESS and TERMINATION are not replaced by new ones.

        RETURNS: cloned object if cloning successful
                 None          if cloning not possible due to external state references

        """
        replacement = {}

        # (*) create the new state machine
        #     (this has to happen first, to get an init_state_index)
        result = StateMachine()

        # every target state has to appear as a start state (no external states)
        # => it is enough to consider the start states and 'rename' them.
        # if later a target state index appears, that is not in this set we
        # return 'None' to indicate that this state machine cannot be cloned.
        sorted_state_indices = self.states.keys()
        sorted_state_indices.sort()
        for state_idx in sorted_state_indices:
            # NOTE: The constructor already delivered an init state index to 'result'.
            #       Thus self's init index has to be translated to result's init index.
            if state_idx == self.init_state_index:
                replacement[state_idx] = result.init_state_index
            else:
                replacement[state_idx] = state_machine_index.get()
        # termination is a global state, it is not replaced by a new index 

        for state_idx, state in self.states.items():
            new_state_idx = replacement[state_idx]
            # print "##", state_idx, "-->", new_state_idx
            result.states[new_state_idx] = self.states[state_idx].clone(replacement)
            
        return result

    def get_id(self):
        return self.__id

    def get_init_state(self):
        return self.states[self.init_state_index]
        
    def get_state_indices(self):
        """Returns list of all state indices that appear as start states inside the machine."""
        return self.states.keys()

    def get_target_state_indices(self, StateIdx):
        """Returns a list of all target states that can be reached from state 'StateIdx'."""
        assert self.has_start_state_index(StateIdx)  

        return self.states[StateIdx].get_target_state_indices()

    def get_result_state_index(self, StateIdx, Trigger):
        """RETURNS: State index of the state reached by triggering 'Trigger'
                    in state 'StateIdx'.
        """
        assert self.has_start_state_index(StateIdx)  

        return self.states[StateIdx].get_result_state_index(Trigger)

    def get_orphaned_state_index_list(self):
        """This function checks for states that are not targeted via any trigger
           by any other state. This indicates most likely a lack off efficiency 
           or an error in the algorithms.
        """
        work_list = self.states.keys()
        try:    del work_list[work_list.index(self.init_state_index)]
        except: assert False, "Init state index is not contained in list of state indices."

        for state in self.states.values():
            target_state_index_list = state.get_target_state_indices()
            work_list = filter(lambda i: i not in target_state_index_list, work_list)
        return work_list

    def get_epsilon_closure_of_state_set(self, StateIdxList):
        """Returns the epsilon closure of a set of set states, i.e. the union
           of the epsilon closures of the single states."""
        result = []
        # the terminal state is not supposed to have any transitions ... well simply
        # that's what 'terminal' means! 

        for state_idx in StateIdxList:
            ec = self.get_epsilon_closure(state_idx)
            for idx in ec:
                if idx not in result: result.append(idx)

        return result

    def get_epsilon_closure(self, StateIdx, done_state_index_list=None):
        """Return all states that can be reached from 'StateIdx' via epsilon
           transition."""
        assert self.has_state_index(StateIdx)

        if done_state_index_list == None: 
           done_state_index_list = []

        aggregated_epsilon_closure = [ StateIdx ] 
        for ti in self.states[StateIdx].get_epsilon_target_state_indices():
            if ti not in done_state_index_list:
                # Do not copy() the done state index list, since anything that has been
                # terminated is fine.
                follow_up_epsilon_closure = self.get_epsilon_closure(ti, done_state_index_list)
                aggregated_epsilon_closure.extend(follow_up_epsilon_closure)
                done_state_index_list.append(ti)

        return aggregated_epsilon_closure
 
    def get_elementary_trigger_sets(self, StateIdxList):
        """Considers the trigger dictionary that contains a mapping from target state index 
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
        def DEBUG_print_history(history):
            txt = ""
            for item in history:
                txt += repr(item) + "\n"
            return txt

        # (*) accumulate the transitions for all states in the state list.
        #     transitions to the same target state are combined by union.
        history = []
        for state_idx in StateIdxList:
            # -- trigger dictionary:  target_idx --> trigger set that triggers to target
            line_up = self.states[state_idx].get_trigger_set_line_up() 
            # NOTE: Doublicate entries in history are perfectly reasonable at this point,
            #       simply if two states trigger on the same character range to the same 
            #       target state. When ranges are opened/closed via the history items
            #       this algo keeps track of doublicates (see below).
            history.extend(line_up)

        # (*) sort history according to position
        history.sort(lambda a, b: cmp(a.position, b.position))

        # (*) build the elementary subset list 
        combinations = {}                             # use dictionary for uniqueness
        map_key_str_to_target_index_combination = {}  # use dictionary for uniqueness 
        current_interval_begin = None
        current_involved_target_indices = {}          # use dictionary for uniqueness
        current_involved_targets_epsilon_closure = []
        for item in history:
            # -- add interval and target indice combination to the data
            #    (only build interval when current begin is there, 
            #     when the interval size is not zero, and
            #     when the epsilon closure of target states is not empty)                   
            if current_interval_begin != None and \
               current_interval_begin != item.position and \
               current_involved_target_indices.keys() != []:

                interval = Interval(current_interval_begin, item.position)
                key_str  = repr(current_involved_targets_epsilon_closure)
                if not combinations.has_key(key_str):   
                    combinations[key_str] = NumberSet(interval)
                    map_key_str_to_target_index_combination[key_str] = \
                                     current_involved_targets_epsilon_closure
                else:
                    combinations[key_str].unite_with(interval)
           
            # -- BEGIN / END of interval:
            #    add or delete a target state to the set of currently considered target states
            #    NOTE: More than one state can trigger on the same range to the same target state.
            #          Thus, one needs to keep track of the 'opened' target states.
            if item.change == INTERVAL_BEGIN:
                if current_involved_target_indices.has_key(item.target_idx):
                    current_involved_target_indices[item.target_idx] += 1
                else:
                    current_involved_target_indices[item.target_idx] = 1
            else:        # == INTERVAL_END
                if current_involved_target_indices[item.target_idx] > 1:
                    current_involved_target_indices[item.target_idx] += 1
                else:    
                    del current_involved_target_indices[item.target_idx] 
    
            # -- re-compute the epsilon closure of the target states
            current_involved_targets_epsilon_closure = \
                self.get_epsilon_closure_of_state_set(current_involved_target_indices.keys())
            current_involved_targets_epsilon_closure.sort()             
    
            # -- set the begin of interval to come
            current_interval_begin = item.position                      
    
        # (*) create the list of pairs [target-index-combination, trigger_set] 
        result = []
        for key_str, target_index_combination in map_key_str_to_target_index_combination.items():
            result.append([target_index_combination, combinations[key_str]])
    
        return result

    def get_acceptance_state_list(self, 
                                  ReturnNonAcceptanceTooF=False, 
                                  SplitAcceptanceStatesByOriginF=False,
                                  CorePatternF=False):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

           If 'SplitAcceptanceStatesByOriginF'=True, then the list of acceptance
           states is split into sets of states of the same origin. The last state
           set is then the set of non-acceptance states (if requested).

           If 'CorePatternF'=True then the 'end acceptance states' of post conditions
           are not returned (acceptance + post condition flag). Instead the core
           patterns acceptance states are returned (post condition flag only).
        """   
        return filter(lambda s: s.is_acceptance(), self.states.values())

    def get_acceptance_state_index_list(self):
        result = []
        for index, state in self.states.items():
            if state.is_acceptance(): result.append(index)
        return result

        """ TODO Throw this out.
        def __criteria(state):
            if not CorePatternF: 
                return state.is_acceptance()
            else:
                return    ( state.is_acceptance() and not state.is_post_conditioned() ) \
                       or ( not state.is_acceptance() and state.is_post_conditioned() ) 

        acceptance_state_list = []
        non_acceptance_state_list = []
        if non_acceptance_state_list  == None: non_acceptance_state_list = []
        for state_idx, state in self.states.items():
            if __criteria(state): acceptance_state_list.append(state_idx)
            else:                 non_acceptance_state_list.append(state_idx)

        if SplitAcceptanceStatesByOriginF:
            # map: set of original states ---> state indices that are of this origin
            sorter_dict = {}   
            def sorter_dict_add(key, list_element):
                if sorter_dict.has_key(key): sorter_dict[key].append(list_element)
                else:                        sorter_dict[key] = [ list_element ]                             
            for state_index in acceptance_state_list:
                origin_state_machine_ids = map(lambda origin: 
                                            origin.state_machine_id, 
                                            self.states[state_index].get_origin_list())
                state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
                sorter_dict_add(state_combination_id, state_index)
            # each 'value' (belonging to a key) represents the set of states that have the
            # same combination of original states
            result = sorter_dict.values()
        else:
            result = [ acceptance_state_list ]
            
        if ReturnNonAcceptanceTooF and non_acceptance_state_list != []: 
            return result + [ non_acceptance_state_list ]
                
        return result
        """

    def get_inverse(self, CutAtShortestAcceptanceF=False):
        """Creates an inverse representation of the state machine. Optionally,
           the longer acceptance paths can be cut, in case that there are shorter
           once. This is the contrary of a 'greedy' wildcard, i.e.
                
                ("hello"|"h") would be equivalent to "h" this is by pure
                logic an redundant construct, since "h" causes acceptance", except
                one goes for 'longest match'
        
           Also "h"*|"h" : HERE cut at first match because it ends after "h"    
        """
        #__________________________________________________________________________________________
        # TODO: See th above comment and think about it.
        assert self.pre_condition_state_machine == None and not self.has_trivial_pre_condition(), \
               "pre-conditioned state machines cannot be inverted via 'get_inverse()'"

        #__________________________________________________________________________________________
        result = StateMachine(InitStateIndex=self.init_state_index)
           
        # -- start from the initial state, consider its transitions,
        #    its follow state become the new worklist, etc.
        worklist  = [ self.init_state_index ] 
        done_list = []
        while worklist != []:    
            # -- pop the next state to be treated from the worklist     
            state_idx = worklist.pop()  
            done_list.append(state_idx)
            # -- enter inverse transitions into 'result': target ---(trigger set)---> source
            for t in self.states[state_idx].get_transition_list():
                # -- add the inverse transition
                result.add_transition(t.target_state_index, t.trigger_set, state_idx)

            epsilon_transition_target_state_list = self.states[state_idx].get_epsilon_target_state_indices()
            for target_state in epsilon_transition_target_state_list:
                # -- ensure that target state exists
                if result.states.has_key(target_state) == False: 
                    result.states[target_state] = StateInfo()                        
                # -- add the inverse transition
                result.states[target_state].add_epsilon_target_state(state_idx)

            # -- from all possible follow states, only consider those that have not been treated yet
            follow_state_list =   self.states[state_idx].get_normal_target_states() \
                                + epsilon_transition_target_state_list
            for follow_state_idx in follow_state_list: 
                if follow_state_idx not in done_list + worklist:
                     worklist.append(follow_state_idx)

        # -- copy all origins of the original state machine
        for state_index, state in self.states.items():
            result.states[state_index].origins().set(state.get_origin_list())

        # -- only the initial state becomes an acceptance state
        result.states[self.init_state_index].set_acceptance(True, LeaveStoreInputPositionF=True)

        # -- setup an epsilon transition from an new init state to all previous 
        #    acceptance states.
        new_init_state_index = result.create_new_init_state() 
        for state_index in self.get_acceptance_state_index_list():
            result.add_epsilon_transition(new_init_state_index, state_index)        

        # -- for uniqueness of state ids, clone the result
        return result.clone()    
        
    def get_origin_ids_of_acceptance_states(self):
        """(1) get ids of all acceptance states.
           (2) extract their origins (provided they store the input position or are post conditioned).
        """
        # -- get list of states that are 'acceptance states'
        acceptance_state_list = self.get_acceptance_state_list()
        if acceptance_state_list == []: return []

        # -- collect origins of the acceptance states
        result = []
        for acceptance_state in acceptance_state_list:
            origin_list = acceptance_state.get_origin_list() 

            # -- do not care about 'traces of loosers' (i.e. non-acceptance states)
            filtered_list = filter(lambda origin:
                                   origin.store_input_position_f() 
                                   or origin.post_conditioned_acceptance_f()
                                   or origin.pseudo_ambiguous_post_condition_id(),
                                   origin_list)

            # extract the state machine ids out of the origin informations
            result.extend(map(lambda x: x.state_machine_id, filtered_list))
        return result
        
    def get_the_unique_original_state_machine_id(self):
        """Checks if there is one single state machine as origin, if not an exception
           is thrown. Otherwise the state machine id of this original state machine 
           is returned.
        """   

        origin_list = []
        for state in self.states.values():
            origin_list.extend(state.get_origin_list())
    
        original_sm_list = {}
        for origin in origin_list:
            original_sm_list[origin.state_machine_id] = True

        assert len(original_sm_list.keys()) <= 1, \
               "state machine has more than one original state machine.\n" + \
               "state machine ids: " + repr(original_sm_list)

        return original_sm_list.keys()[0]         
                
    def get_pseudo_ambiguous_post_condition_id(self):
        pseudo_ambiguous_post_condition_id = -1L

        for state in self.states.values():
            if state.is_acceptance() == False: continue
            origin_list = state.get_origin_list()

            backward_detector_id = None
            for origin in origin_list:
                if origin.pseudo_ambiguous_post_condition_id() != -1L:
                    sm_id = origin.pseudo_ambiguous_post_condition_id()
                    # double check: all pseudo ambiguous post condition ids of a state
                    # machine must point to the same state machine. Note: Normally
                    # one could return here, but for the sake of safety let's check
                    # the consistency at this point.
                    if pseudo_ambiguous_post_condition_id != -1L:
                        assert sm_id == pseudo_ambiguous_post_condition_id
                    pseudo_ambiguous_post_condition_id = sm_id

        return pseudo_ambiguous_post_condition_id

    def get_pre_condition_sm_id(self):
        if self.pre_condition_state_machine !=  None:
            return the_state_machine.pre_condition_state_machine.get_id()
        return -1L

    def is_empty(self):
        """If state machine only contains the initial state that points nowhere,
           then it is empty.
        """
        if len(self.states) != 1: return False
        return self.states[self.init_state_index].is_empty()

    def is_acceptance(self, StartIdx):
        if self.has_start_state_index(StartIdx) == False: return None
        return self.states[StartIdx].is_acceptance()

    def is_post_conditioned(self):
        """Goes through the list of all states, if one state is post-conditioned,
           it means that the whole pattern (i.e. state machine) is post conditioned.
        """   
        for state in self.states.values():
            if state.is_post_conditioned(): return True
        return False                                

    def assert_consistency(self):
        """Check: -- whether each target state in contained inside the state machine.
        """
        target_state_index_list = self.states.keys()
        for index, state in self.states.items():
            for target_state_index in state.get_target_state_indices():
                assert target_state_index in target_state_index_list, \
                       "state machine contains target state that is not contained in itself."

    def has_non_trivial_pre_condition(self):
        return self.pre_condition_state_machine != None

    def has_trivial_pre_condition(self):
        """NOTE: This function was initialy implemented to generalize the 
                 begin of line precondition with the 
                 'one special character preceeding pre-condition'.
        """
        return self.has_trivial_pre_condition_begin_of_line()

    def has_trivial_pre_condition_begin_of_line(self):
        """If one state is conditioned to have the 'begin of line' 
           condition for acceptance, than the whole state machine is
           trivially preconditioned that way.
        """   
        for state in self.states.values():
            if state.has_trivial_pre_condition_begin_of_line_f(): return True
        return False    
    
    def has_start_state_index(self, StartIdx):
        return self.states.has_key(StartIdx)

    def has_state_index(self, StateIdx):
        """RETURNS: True, if state is either a start or a target index.
                    False, othewise.
        """
        if self.has_start_state_index(StateIdx): return True

        for state_info in self.states.values():
            if StateIdx in state_info.get_target_state_indices():
                return True
        return False

    def has_origins(self):
        for state in self.states.values():
            if state.get_origin_list() != []: return True
        return False

    def delete_state_origins(self):
        for state in self.states.values():
            state.origins().clear()

    def delete_meaningless_origins(self):
        """Deletes origins that are not concerned with one of the three:
            -- post-conditions
            -- pre-conditions/trivial pre-conditions included
            -- store input positions
           
            NOTE: This function is only to be used for single patterns not for
                combined state machines. During the NFA to DFA translation
                more than one state is combined into one. This maybe reflected
                in the origin list. However, only at the point when the 
                pattern state machine is ready, then the origin states are something
                meaningful. The other information has to be kept.
                                                                                                                                            
            NOTE: After applying this fuction to a single pattern, there should only
                be one origin for each state.
        """
        for state in self.states.values():
            state.delete_meaningless_origins()

    def delete_epsilon_transition(self, StartStateIdx, TargetStateIdx):

        assert self.has_state_index(StateIdx)

        self.states[StartStateIdx].delete_epsilon_target_state(TargetStateIdx)  

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

    def create_new_init_state(self, AcceptanceF=False):

        self.init_state_index = self.create_new_state()
        return self.init_state_index

    def create_new_state(self, AcceptanceF=False, StateIdx=None):
        if StateIdx == None:
            new_state_index = state_machine_index.get()
        else:
            new_state_index = StateIdx

        self.states[new_state_index] = StateInfo(AcceptanceF)
        return new_state_index
        
    def add_transition(self, StartStateIdx, TriggerSet, TargetStateIdx = None, AcceptanceF = False):
        """Adds a transition from Start to Target based on a given Trigger.

           TriggerSet can be of different types: ... see add_transition()
           
           (see comment on 'StateInfo::add_transition)

           RETURNS: The target state index.
        """
        assert type(StartStateIdx) == long
        # NOTE: The Transition Constructor is very tolerant, so no tests on TriggerSet()
        #       assert TriggerSet.__class__.__name__ == "NumberSet"
        assert type(TargetStateIdx) == long or TargetStateIdx == None
        assert type(AcceptanceF) == bool

        # If target state is undefined (None) then a new one has to be created
        if TargetStateIdx == None:
            TargetStateIdx = state_machine_index.get()
            self.states[TargetStateIdx] = StateInfo()
        if self.has_start_state_index(StartStateIdx) == False:
            self.states[StartStateIdx] = StateInfo()        
        if self.has_start_state_index(TargetStateIdx) == False:
            self.states[TargetStateIdx] = StateInfo()        
        if AcceptanceF:
            self.states[TargetStateIdx].set_acceptance(True)

        return self.states[StartStateIdx].add_transition(TriggerSet, TargetStateIdx)
            
    def add_epsilon_transition(self, StartStateIdx, TargetStateIdx=None, RaiseAcceptanceF=False):
        assert TargetStateIdx == None or type(TargetStateIdx) == long

        # create new state if index does not exist
        if not self.has_start_state_index(StartStateIdx):
            self.states[StartStateIdx] = StateInfo()
        if TargetStateIdx == None:
            TargetStateIdx = self.create_new_state(AcceptanceF=RaiseAcceptanceF)
        elif not self.has_start_state_index(TargetStateIdx):
            self.states[TargetStateIdx] = StateInfo()

        # add the epsilon target state
        self.states[StartStateIdx].add_epsilon_target_state(TargetStateIdx)     
        # optionally raise the state of the target to 'acceptance'
        if RaiseAcceptanceF: self.states[TargetStateIdx].set_acceptance(True)

        return TargetStateIdx

    def mount_to_acceptance_states(self, MountedStateIdx, 
                                   CancelStartAcceptanceStateF=True,
                                   RaiseTargetAcceptanceStateF=False,
                                   LeaveStoreInputPositionsF=False):
        """Mount on any acceptance state the MountedStateIdx via epsilon transition."""

        for state_idx, state in self.states.items():
            # -- only consider state other than the state to be mounted
            # -- only handle only acceptance states
            if not state_idx != MountedStateIdx: continue
            if not state.is_acceptance(): continue
            # add the MountedStateIdx to the list of epsilon transition targets
            state.add_epsilon_target_state(MountedStateIdx)
            # if required (e.g. for sequentialization) cancel the acceptance status
            if CancelStartAcceptanceStateF: state.set_acceptance(False, LeaveStoreInputPositionsF)

        if RaiseTargetAcceptanceStateF: 
            self.states[MountedStateIdx].set_acceptance(True, LeaveStoreInputPositionsF)

    def mount_to_initial_state(self, TargetStateIdx):
        """Adds an epsilon transition from initial state to the given 'TargetStateIdx'. 
           The initial states epsilon transition to TERMINATE is deleted."""

        assert self.has_state_index(self.init_state_index)

        self.states[self.init_state_index].add_epsilon_target_state(TargetStateIdx)

    def set_acceptance(self, StateIdx, StatusF=True):

        assert self.has_state_index(StateIdx)

        self.states[StateIdx].set_acceptance(StatusF)

    def set_trivial_pre_condition_begin_of_line(self):
        self.__trivial_pre_condition_begin_of_line_f = True
    
    def adapt_origins(self, StateMachineID):
        """Adapts origin to origin in a state machine 'StateMachineID'
        """
        for state_idx, state in self.states.items():
            state.adapt_origins(StateMachineID, state_idx)

        if self.pre_condition_state_machine != None:
            self.pre_condition_state_machine.adapt_origins(StateMachineID)

    def adapt_origins_to_self(self):
        """Considers all origins mentioned to be of this state machine, i.e.
           it changes state machine id to its own and the state ids to their state ids.
           The flags for pre-, and post-conditions remain, and so the store input
           position flags.
        """
        self.adapt_origins(self.get_id())

    def filter_dominated_origins(self):
        for state in self.states.values(): state.filter_dominated_origins()

    def verify_unique_origin(self, StateMachineID=-1L):
        """Verifies that all states only have one single original state machine which is this
           one and the state indeces correspond their states in this state machine.

           This function is useful to check that single patterns are consistent. They must not
           have more than one origin! Only the combined state machine can have more than one
           origin. Also, the origin has to fit the state machine as long as it is a single pattern.
           
           See also: adapt_origins()
        """
        if StateMachineID == -1L: StateMachineID = self.get_id()

        for state_idx, state in self.states.items():
            if state.verify_unique_origin(StateMachineID, state_idx) == False:
                return False
           
        if self.pre_condition_state_machine != None:
            return self.pre_condition_state_machine.verify_unique_origin(StateMachineID)
            
        return True    

    def __repr__(self):
        return self.get_string(NormalizeF=True)

    def __get_state_index_normalization(self, NormalizeF):
        index_map         = {}
        inverse_index_map = {}
        counter           = -1L
        if NormalizeF:
            for state_i in self.states.keys():
                counter += 1L
                index_map[state_i]         = counter
                inverse_index_map[counter] = state_i
            index_sequence = range(0, counter+1)
        else:
            index_sequence = []
            for state_i in self.states.keys():
                index_map[state_i]         = state_i
                inverse_index_map[state_i] = state_i
                index_sequence.append(state_i)

        return index_map, inverse_index_map, index_sequence

    def get_string(self, NormalizeF=False):

        # (*) normalize the state indices
        index_map, inverse_index_map, index_sequence = self.__get_state_index_normalization(NormalizeF)

        # (*) construct text 
        msg = "init-state = " + repr(index_map[self.init_state_index]) + "\n"
        for printed_state_i in index_sequence:
            printed_state_i = long(printed_state_i)
            real_state_i    = inverse_index_map[printed_state_i]
            state           = self.states[real_state_i]
            msg += "%05i" % printed_state_i + state.get_string(index_map)
            
        if self.pre_condition_state_machine != None:
            msg += "pre-condition inverted = "
            msg += repr(self.pre_condition_state_machine)           

        return msg

    def get_graphviz_string(self, NormalizeF=False):
        # (*) normalize the state indices
        index_map, inverse_index_map, index_sequence = self.__get_state_index_normalization(NormalizeF)

        # (*) Border of plot block
        frame_txt = """
        digraph state_machine_%i {
	       rankdir=LR;
	       size="8,5"
	       node [shape = doublecircle]; $$ACCEPTANCE_STATES$$;
           node [shape = circle];
           $$TRANSITIONS$$
        }
        """ % self.get_id()

        transition_str       = ""
        acceptance_state_str = ""
        for printed_state_i in index_sequence:
            printed_state_i = long(printed_state_i)
            real_state_i    = inverse_index_map[printed_state_i]
            state           = self.states[real_state_i]
            if state.is_acceptance(): 
                acceptance_state_str += "%i; " % int(printed_state_i)
            transition_str += state.get_graphviz_string(printed_state_i, index_map)

        if acceptance_state_str != "": acceptance_state_str = acceptance_state_str[:-2]
        return blue_print(frame_txt, [["$$ACCEPTANCE_STATES$$", acceptance_state_str],
                                      ["$$TRANSITIONS$$",       transition_str]])
        
            
