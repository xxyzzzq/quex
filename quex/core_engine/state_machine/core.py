import sys
from copy import copy, deepcopy

from   quex.frs_py.string_handling import blue_print
#
from   quex.core_engine.interval_handling   import NumberSet, Interval
import quex.core_engine.state_machine.index as     state_machine_index
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

class Transition:
    # Information about a transition:
    #
    #      ----( trigger ? )----[ success flag/or not ]---> target state
    #
    # A transition is activated by a trigger, i.e. a character comes in that is 
    # in the set of triggering characters. Then an action is performed: eating
    # the character (moving on to the next) not not (leaving character for further
    # transitions to trigger). Finally, the target state is entered.
    #
    def __init__(self, TriggerSet, TargetStateIdx):
        assert TriggerSet.__class__ == NumberSet
        assert type(TargetStateIdx) == long
       
        # set of characters that trigger the transition 
        self.trigger_set        = TriggerSet
        # target state index (where one lands if transition is performed)
        self.target_state_index = TargetStateIdx

    def get_string(self, StateIndexMap=None):
        """Return a string representation of the Transition."""
        trigger_str = self.trigger_set.get_utf8_string()
        if StateIndexMap == None:
            target_str  = "%05i" % self.target_state_index
        else:
            target_str  = "%05i" % StateIndexMap[self.target_state_index]
            
        return "== %s ==> %s" % (trigger_str, target_str)

    def get_graphviz_string(self, StateIndexMap=None):
        trigger_str = self.trigger_set.get_utf8_string()
        if StateIndexMap == None:
            target_str  = "%i" % self.target_state_index
        else:
            target_str  = "%i" % StateIndexMap[self.target_state_index]
            
        return "-> %s [label =\"%s\"];\n" % (target_str, trigger_str.replace("\"", ""))

 
    def set(self, TriggerSet=None, TargetIdx=None):
        if TriggerSet != None:  self.trigger_set = TriggerSet
        elif TargetIdx != None: self.target_index = TargetIdx

class EpsilonTransition:
    """Information about the epsilon transition of a state. Note, that the
       function 'StateInfo::add_transition(...) computes the trigger set of the
       epsilon transition as the remaining set where nothing else triggers.
       
       target_state_indices = []  => no epsilon transition, but the trigger
                                     set contains still the remaining triggers 
                                     of a state transition.
    """

    def __init__(self):
        self.trigger_set          = NumberSet(Interval(-sys.maxint, sys.maxint))
        # epsilon trigger to empty set of target states --> missmatch
        self.target_state_indices = [ ]

    def is_empty(self):
        return self.trigger_set.is_all() and self.target_state_indices == []
        
    def get_string(self, StateIndexMap=None):
        if self.target_state_indices == [ ]: return "<no epsilon>"

        trigger_str = self.trigger_set.get_utf8_string()
        self.target_state_indices.sort()

        target_str = ""
        for ti in self.target_state_indices:
            if StateIndexMap == None: target_str += "%05i, " % int(ti) 
            else:                     target_str += "%05i, " % int(StateIndexMap[ti]) 

        if target_str != "": target_str = target_str[:-2]
        return "epsilon == %s ==> %s" % (trigger_str, target_str)

    def get_graphviz_string(self, OwnStateIndex, StateIndexMap=None):
        msg = ""
        for ti in self.target_state_indices:
            if StateIndexMap == None: target_str = "%i" % int(ti) 
            else:                     target_str = "%i" % int(StateIndexMap[ti]) 
            msg += "%i -> %s [label =\"<epsilon>\"];\n" % (OwnStateIndex, target_str)
        return msg


StateOriginInfo_POST_CONDITION_END          = 1
StateOriginInfo_NON_ACCEPTANCE              = 2
StateOriginInfo_ACCEPTANCE                  = 3
StateOriginInfo_POST_CONDITIONED_ACCEPTANCE = 4
StateOriginInfo_PRE_CONDITIONEND_ACCEPTANCE = 5
StateOriginInfo_ERROR                       = -1

class StateOriginInfo:
    """-- store input position: if an origin is flagged that way it 
          imposes that the input position is to be stored.

       -- post conditioned acceptance: 
          indicates that the original pattern was a 'post-conditioned'
          pattern. It follows:

       -- if store input position is required, then it has to be 
          stored in a dedicated variable, because, multiple 
          patterns may be post conditioned and only the one (if one)
          succeeds, has to store set the input position to the position
          where the first post conditioned acceptance occured.

       -- if store input position is not required, this implies that
          the original state was the 'final acceptance' state, i.e.
          the end of the post condition. no input position is to be
          stored in this case, because the position of the first
          success is to be restored.

       -- pre condition id:
          id of the state machine that constitutes the pre-condition. 
          if not pre-condition is set it is -1L. 

       -- pseudo ambiguous post condition id:
          id of the state machine that constitutes the state machine 
          that is used to go backwards to search the end of the core
          condition.
          In the large majority of cases, where there is no pseudo 
          ambiguous post condition (e.g. x*/x), it is set it is -1L. 
    """    
    def __init__(self, StateMachineIdx, StateIdx, StoreInputPositionF=False, 
                 PostConditionedAcceptanceF=False, PreConditionedStateMachineID=-1L,
                 PreConditionBeginOfLineF=False,
                 PseudoAmbiguousPostConditionID=-1L):
        self.state_machine_id = StateMachineIdx
        self.state_index      = StateIdx
        # Input position of the current input stream is to be stored in 
        # the following cases: 
        #
        #   -- 'normal acceptance state', i.e. not the acceptance state of a post condition.
        #   -- 'ex acceptance state', i.e. states that were acceptance states of state machines
        #      that have a post condition.      
        #
        # NOTE: By default, the function 'set_acceptance(True)' and 'set_acceptance(False)'
        #       of class StateInfo sets the 'store_input_position_f' to True, respectively
        #       false, because this is the normal case. When a post condition is to be appended
        #       the 'store_input_position_f' is to be stored manually - see the function
        #       'state_machine.post_condition_append.do(...).
        self.__store_input_position_f = StoreInputPositionF
        # -- was the origin a post-conditioned acceptance?
        #    (then we have to store the input position, store the original state machine
        #     as winner, but continue)
        self.__post_conditioned_acceptance_f = PostConditionedAcceptanceF
        # -- was the origin a pre-conditioned acceptance?
        #    (then one has to check at the end if the pre-condition holds)
        self.__pre_condition_id = PreConditionedStateMachineID  
        #
        # -- trivial pre-condition: begin of line
        self.__pre_condition_begin_of_line_f = PreConditionBeginOfLineF

        # -- id of state machine that is used to go backwards from the end
        #    of a post condition that is pseudo-ambiguous. 
        self.__pseudo_ambiguous_post_condition_id = PseudoAmbiguousPostConditionID
        
    def is_acceptance(self):
        """Use state machine id and state id to get access to the state.
           Note: acceptance states may be changed, so this function gets the
                 current acceptance state of the origin.
        """
        sm = get_state_machine_by_id(self.state_machine_id)

        if sm.states.has_key(self.state_index):
            state = sm.states[self.state_index]
        else:
            # key has not been found in the core state machine, ...
            # does it exist in the pre-condition state machine?
           assert sm.pre_condition_state_machine != None \
                  and sm.pre_condition_state_machine.states.has_key(self.state_index), \
                  "state machine '%s' does not have a state '%s'" % \
                  (self.state_machine_id, self.state_index) + \
                  "nor does its pre-condition state machine"

           state = sm.pre_condition_state_machine.states[self.state_index]
                   
               
        return state.is_acceptance()

    def __eq__(self, other):
        """Two origins are the same if they origin from the same state machine and 
           have the same state index. If they then differ in the 'store_input_position_f'
           there is a major error. It would mean that one StateOriginInfo states about the
           same original state something different than another StateOriginInfo.
        """
        result = self.state_machine_id == other.state_machine_id and \
                 self.state_index      == other.state_index                           

        if result == True: 
            assert self.__store_input_position_f == other.__store_input_position_f, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the input being stored or not.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)
            assert self.__pre_condition_id == other.__pre_condition_id, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the pre-conditioned acceptance.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)
            assert self.__post_conditioned_acceptance_f == other.__post_conditioned_acceptance_f, \
                   "Two StateOriginInfo objects report about the same state different\n" \
                   "information about the post-conditioned acceptance.\n" \
                   "state machine id = " + repr(self.state_machine_id) + "\n" + \
                   "state index      = " + repr(self.state_index)

        return result     

    def set_store_input_position_f(self, Value=True):
        assert type(Value) == bool
        self.__store_input_position_f = Value

    def set_pre_condition_id(self, Value=True):
        assert type(Value) == long
        self.__pre_condition_id = Value

    def set_pre_condition_begin_of_line_f(self, Value=True):
        self.__pre_condition_begin_of_line_f = Value

    def set_post_conditioned_acceptance_f(self, Value=True):
        assert type(Value) == bool
        self.__post_conditioned_acceptance_f = Value

    def set_pseudo_ambiguous_post_condition_id(self, Value):
        assert type(Value) == long
        self.__pseudo_ambiguous_post_condition_id = Value

    def pre_condition_id(self):
        return self.__pre_condition_id  

    def post_conditioned_acceptance_f(self):
        return self.__post_conditioned_acceptance_f     

    def pre_condition_begin_of_line_f(self):
        return self.__pre_condition_begin_of_line_f

    def store_input_position_f(self):
        return self.__store_input_position_f    

    def pseudo_ambiguous_post_condition_id(self):
        return self.__pseudo_ambiguous_post_condition_id

    def is_end_of_post_conditioned_core_pattern(self):
        return self.post_conditioned_acceptance_f() and self.store_input_position_f()
                            
    def __repr__(self):
        appendix = ""
        if self.__store_input_position_f:        
            appendix += ", S"
        if self.__post_conditioned_acceptance_f: 
            appendix += ", post"
        if self.__pre_condition_id != -1L:            
            appendix += ", pre=" + repr(self.__pre_condition_id).replace("L", "")
        if self.__pseudo_ambiguous_post_condition_id != -1L:            
            appendix += ", papc=" + repr(self.__pseudo_ambiguous_post_condition_id).replace("L", "")
        if self.__pre_condition_begin_of_line_f:
            appendix += ", bol"
        return "(%s, %s%s)" % (repr(self.state_machine_id), repr(self.state_index), appendix)

    def type(self):
        Acc   = self.is_acceptance()
        Store = self.store_input_position_f()
        Post  = self.post_conditioned_acceptance_f()
        Pre   = self.pre_condition_id() 
        if     Acc and     Store and not Post and not Pre: return StateOriginInfo_ACCEPTANCE
        if not Acc and not Store and not Post and not Pre: return StateOriginInfo_NON_ACCEPTANCE
        if     Acc and     Store and     Post and not Pre: return StateOriginInfo_POST_CONDITIONED_ACCEPTANCE
        if     Acc and not Store and     Post and not Pre: return StateOriginInfo_POST_CONDITION_END    
        if     Acc and     Store and not Post and     Pre: return StateOriginInfo_PRE_CONDITIONEND_ACCEPTANCE
        # the constitution of the state origin is not valid --> return error
        return StateOriginInfo_ERROR    

    def __cmp__(self, Other):
        if self.is_acceptance() == True  and Other.is_acceptance() == False: return -1
        if self.is_acceptance() == False and Other.is_acceptance() == True:  return 1

        # NOTE: The state machine ID directly corresponds to the 'position in the list'
        #       where the pattern was specified. Low ID == early specification.
        return cmp(self.state_machine_id, Other.state_machine_id)
            
                    
        
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
    def __init__(self, AcceptanceF=False):
        """Contructor of a State, i.e. a aggregation of transitions.
        """

        # normal transitions: trigger, action, target-state-index
        self.__transition_list = []
        # epsilon transition: if no other trigger triggers
        self.__epsilon = EpsilonTransition()
        # is a acceptance state?
        self.__acceptance_f = AcceptanceF 
        # relation (origin of this state in terms of state machine (pattern) and state)
        self.__origin_list = []

    def get_origin_list(self):
        return self.__origin_list

    def get_transitions(self):
        return self.__transition_list  

    def get_epsilon_trigger_set(self):
        return deepcopy(self.__epsilon.trigger_set)

    def get_epsilon_target_state_indices(self):
        return deepcopy(self.__epsilon.target_state_indices)

    def get_normal_target_states(self):
        target_index_unique = {}
        for t in self.__transition_list:
            target_index_unique[t.target_state_index] = 1
        return target_index_unique.keys()

    def get_target_state_indices(self):
        ti_list = self.get_normal_target_states()
        if not self.__epsilon.trigger_set.is_empty():
            for ti in self.__epsilon.target_state_indices:
                if ti not in ti_list:
                    ti_list.append(ti)
        return ti_list 
        
    def get_result_list(self, Trigger):
        """Returns the set of resulting target states."""
        assert type(Trigger) == int

        result_list = []
        for t in self.__transition_list:
            if t.trigger_set.contains(Trigger):
                if t.target_state_index not in result_list:
                    result_list.append(t.target_state_index) 

        if self.__epsilon.trigger_set.contains(Trigger):
            for ti in self.__epsilon.target_state_indices:
                if ti not in result_list:
                    result_list.append(ti)

        return result_list

    def get_result_state_index(self, Trigger):
        """Return one target state that is triggered by the given trigger.
           (there should not be more in a DFA, but in an NFA ...).
        """
        target_state_list = self.get_result_list(Trigger)
        if target_state_list != []: 
            return target_state_list[0]
        else:
            return None
    
    def get_trigger_set_union(self):
        """Returns union of all trigger sets that lead to a target state. Useful
           in order to determine wether a state triggers on some trigger or not.
        """
        result = NumberSet()
        for t in self.__transition_list:
            result.unite_with(t.trigger_set)
        if self.__epsilon.target_state_indices != []:
            result.unite_with(self.__epsilon.trigger_set)
        return result

    def get_trigger_set(self, TargetIdx=None):
        """Returns all triggers that lead to target 'TargetIdx'. If a trigger 'None' is returned
           it means that the epsilon transition triggers to target state. If the TargetIndex is 
           omitted the set of all triggers, except the epsilon triggers, are returned."""
        if TargetIdx == None:
            return self.__epsilon.trigger_set.inverse() 

        for t in self.__transition_list:
            if t.target_state_index == TargetIdx:
                return t.trigger_set

        if self.__epsilon.trigger_set.contains(TargetIdx):
            return None 
        return NumberSet() 

    def get_trigger_dictionary(self, ConsiderEpsilonTransition=False):
        """Returns a map from target state index to trigger that triggers it. This
           includes the trigger set of the epsilon transition and its target states."""
        def consider(target_state_index, trigger_set):
            if not result.has_key(target_state_index):
                result[target_state_index] = NumberSet(trigger_set)
            else:
                result[target_state_index].unite_with(trigger_set)        

        result = {}
        for t in self.__transition_list: 
            consider(t.target_state_index, t.trigger_set)

        # if not self.__epsilon.trigger_set.is_empty():
        #    for ti in self.__epsilon.target_state_indices: 
        #       consider(ti, self.__epsilon.trigger_set) 

        return result
        
    def get_trigger_set_line_up(self):
        """Lines the triggers up on a 'time line'. A target is triggered by
           certain characters that belong to 'set' (trigger sets). Those sets
           are imagined as ranges on a time line. The 'history' is described
           by means of history items. Each item tells wether a range begins
           or ends, and what target state is reached in that range.

           [0, 10] [90, 95] [100, 200] ---> TargetState0
           [20, 89]                    ---> TargetState1
           [96, 99] [201, 205]         ---> TargetState2

           results in a 'history':

           0:  begin of TargetState0
           10: end of   TargetState0
           11: begin of DropOut
           20: begin of TargetState1
           89: end of   TargetState1
           90: begin of TargetState0
           95: end of   TargetState0
           96: begin of TargetState2
           99: end of   TargetState2
           100 ...
           
        """
        # (*) create a 'history', i.e. note down any change on the trigger set combination
        #     (here the alphabet plays the role of a time scale)
        class history_item:
            def __init__(self, Position, ChangeF, TargetIdx):
                self.position   = Position
                self.change     = ChangeF
                self.target_idx = TargetIdx 
                
            def __repr__(self):         
                if self.change == INTERVAL_BEGIN: ChangeStr = "begin"
                else:                             ChangeStr = "end"
                return "%i: %s %s" % (self.position, ChangeStr, self.target_idx)

            def __eq__(self, Other):
                return     self.position   == Other.position \
                       and self.change     == Other.change   \
                       and self.target_idx == Other.target_idx 
                

        history = []
        # NOTE: This function only deals with non-epsilon triggers. Empty
        #       ranges in 'history' are dealt with in '.get_trigger_map()'. 
        for target_idx, trigger_set in self.get_trigger_dictionary().items():
            interval_list = trigger_set.get_intervals()
            for interval in interval_list: 
                # add information about start and end of current interval
                history.append(history_item(interval.begin, INTERVAL_BEGIN, target_idx))
                history.append(history_item(interval.end, INTERVAL_END, target_idx))

        # (*) sort history according to position
        history.sort(lambda a, b: cmp(a.position, b.position))

        return history      

    def get_trigger_map(self):
        """Consider the set of possible characters as aligned on a 1 dimensional line.
           This one-dimensional line is remiscent of a 'time line' so we call the change
           of interval coverage 'history'.         

           Returns a trigger map consisting of a list of pairs: (Interval, TargetIdx)

                    [ [ interval_0, target_0],
                      [ interval_1, target_1],
                      ...
                      [ interval_N, target_N] ]

           The intervals are sorted and non-overlapping (use this function only for DFA).
        """
        # NOTE: The response '[]' is a **signal** that there is only an epsilon
        #       transition. The response as such would be incorrect. But the signal
        #       'empty reply' needs to be treated by the caller.
        if self.__transition_list == []: return []
            
        history = self.get_trigger_set_line_up()
        
        def query_trigger_map(EndPosition, TargetIdx):
            """Find all map entries that have or have not an open interval and
               point to the given TargetIdx. If TargetIdx = None it is not checked.
            """
            entry_list = []
            for entry in trigger_map:
                if entry[0].end == EndPosition and entry[1] == TargetIdx: 
                    entry_list.append(entry)
            return entry_list 

        # (*) build the trigger map
        trigger_map = []    
        for item in history:
            if item.change == INTERVAL_BEGIN: 
                # if an interval has same target index and ended at the current
                # intervals begin, then extend the last interval, do not create a new one.
                adjacent_trigger_list = query_trigger_map(item.position, item.target_idx)
                if adjacent_trigger_list == []:
                    # open a new interval (set .end = None to indicate 'open')
                    trigger_map.append([Interval(item.position, INTERVAL_UNDEFINED_BORDER), 
                                       item.target_idx])
                else:
                    for entry in adjacent_trigger_list: 
                        # re-open the adjacent interval (set .end = None to indicate 'open')
                        entry[0].end = INTERVAL_UNDEFINED_BORDER
                
            else:
                # item.change == INTERVAL_END   
                # close the correspondent intervals
                # (search for .end = None indicating 'open interval')           
                for entry in query_trigger_map(INTERVAL_UNDEFINED_BORDER, item.target_idx):
                    entry[0].end = item.position
            
        # (*) fill all gaps in the trigger map with target = epsilon_target
        epsilon_target = None
        if self.__epsilon.target_state_indices != []: 
            epsilon_target = self.__epsilon_target_indices[0]   

        gap_filler = [] 
        if len(trigger_map) >= 2:    
            prev_entry = trigger_map[0]    
            for entry in trigger_map[1:]:    
                if prev_entry[0].end != entry[0].begin: 
                    gap_filler.append([Interval(prev_entry[0].end, entry[0].begin), epsilon_target])
                prev_entry = entry
    
        # -- append the last interval until 'infinity' (if it is not yet specified   
        #    (do not switch this with the following step, .. or you screw it)           
        if trigger_map[-1][0].end != sys.maxint:    
            trigger_map.append([Interval(trigger_map[-1][0].end, sys.maxint), epsilon_target])
        # -- insert a first interval from -'infinity' to the start of the first interval
        if trigger_map[0][0].begin != -sys.maxint:
            trigger_map.append([Interval(-sys.maxint, trigger_map[0][0].begin), epsilon_target])
           
        # -- insert the gap fillers and get the trigger map straigtened up again
        trigger_map.extend(gap_filler) 
        trigger_map.sort(lambda a, b: cmp(a[0].begin, b[0].begin))

        # (*) post check assert
        for entry in trigger_map:
            assert entry[0].end != None, \
                   "remaining open intervals in trigger map construction"

        return trigger_map

    def is_empty(self):
        return self.__transition_list == [] and self.__epsilon.is_empty()

    def is_acceptance(self):
        return self.__acceptance_f
        
    def is_post_conditioned(self):
        """Goes through the list of all origins, if one origin is post-conditioned,
           it means that state is post conditioned. 
        """   
        for origin in self.__origin_list:
            if origin.post_conditioned_acceptance_f(): return True
        return False                                

    def is_store_input_position(self):
        """If one of the origins requires to store the input position, the state requires
           to store the input position."""
        for origin in self.__origin_list:
            if origin.store_input_position_f() == True: return True
        return False

    def is_DFA_compliant(self):
        """Checks if the current state transitions are DFA compliant, i.e. it
           investigates if trigger sets pointing to different targets intersect.
           RETURN:  True  => OK
                    False => Same triggers point to different target. This cannot
                             be part of a deterministic finite automaton (DFA).
        """
        # NOTE: 'add_transition' ensures that the path '(target_state, action)' is
        #       **unique** in the transition list.
        #
        # (*) the comparison could be displayed in a matrix. a comparison
        #     only has to happen in one diagonal half of the matrix.        
        i = -1
        for tA in self.__transition_list:
            i += 1
            # -- check against normal transitions:
            for tB in self.__transition_list[i+1:]:
                # -- does trigger_list_A and trigger_list_B intersect?
                if not tA.trigger_set.has_intersection(tB.trigger_set):
                    return False
            # -- check against else transition - should not be necessary if transitions
            #    are set up propperly
            if not tA.trigger_set.has_intersection(self.__epsilon.trigger_set):
                return False
                
        return True

    def has_trivial_pre_condition_begin_of_line_f(self):
        for origin in self.__origin_list:
            if origin.pre_condition_begin_of_line_f(): return True
        return False    

    def has_only_one_target_for_trigger_set(self, TriggerSet, TargetIdx):
        """Returns True if all triggers in TriggerSet trigger to the state TargetIdx.
           If not it returns False.
        """
        # 'normal transitions'
        for t in self.__transition_list:
            if not t.trigger_set.has_intersection(TriggerSet): continue
            elif t.target_state_index != TargetIdx: return False

        # epsilon transition
        if   not self.__epsilon.trigger_set.has_intersection(TriggerSet): return True
        elif len(self.__epsilon.target_state_indices) != 1:                return False
        elif self.__epsilon.target_state_indices[0] != TargetIdx:          return False
        
        # if no normal transition trigger set triggered, the epsilon trigger set needs to trigger
        # otherwise there is something seriously wrong (probably in 'add_transition'    
        raise "epsilon trigger set did not catch a trigger set that did not match normal transitions.\n" + \
              "epsilon trigger set = " + repr(self.__epsilon.trigger_set) + "\n" \
              "normal trigger sets = " + repr(map(lambda ts: ts.get_utf8_string(), 
                                                  map(lambda t: t.trigger_set, self.__transition_list)))
              
    def has_none_of_triggers(self, CharacterCodeList):
        assert type(CharacterCodeList) == type([])

        for code in CharacterCodeList:
            if self.has_trigger(code): return False
        return True

    def has_one_of_triggers(self, CharacterCodeList):
        assert type(CharacterCodeList) == type([])

        for code in CharacterCodeList:
            if self.has_trigger(code): return True
        return False

    def has_trigger(self, CharacterCode):
        assert type(CharacterCode) == int

        if self.get_result_state_index(CharacterCode) == None: return False
        else:                                                  return True

    def has_origin(self):
        return self.__origin_list != []

    def set_origin_list(self, OriginList, StoreInputPositionFollowsAcceptanceF=True):
        """Replaces the current origin list with a given one."""
        self.__origin_list = []
        if OriginList != []: self.add_origin_list(OriginList, StoreInputPositionFollowsAcceptanceF)
    
    def set_acceptance(self, Value=True, LeaveStoreInputPositionF=False):
        """NOTE: By default, when a state is set to acceptance the input
                 position is to be stored for all related origins, if this is 
                 not desired (as by 'post_condition_append.do(..)' the flag
                 'store_input_position_f' is to be adpated manually using the
                 function 'set_store_input_position_f'
        """      
        assert type(Value) == bool

        self.__acceptance_f = Value
        # default: store_input_position_f follows acceptance_f
        if not LeaveStoreInputPositionF: self.set_store_input_position_f(Value)

    def set_store_input_position_f(self, Value):
        """Sets the 'store_input_position_flag' for all origins."""
        for origin in self.__origin_list:
            origin.set_store_input_position_f(Value)    

    def set_pseudo_ambiguous_post_condition_id(self, Value):
        """Sets a reference to the detector of the pseudo ambidguous post condition."""
        for origin in self.__origin_list:
            origin.set_pseudo_ambiguous_post_condition_id(Value)    
    
    def set_trivial_pre_condition_begin_of_line(self, Value=True):
        for origin in self.__origin_list:
            origin.set_pre_condition_begin_of_line_f(Value)     
    
    def set_pre_condition_id(self, PreConditionStateMachineID):
        """Sets the 'pre_condition_id' for all origins."""
        for origin in self.__origin_list:
            origin.set_pre_condition_id(PreConditionStateMachineID)     

    def set_post_conditioned_acceptance_f(self, Value):
        """Sets the 'post_conditioned_acceptance_flag' for all origins."""
        for origin in self.__origin_list:
            origin.set_post_conditioned_acceptance_f(Value)     

    def add_origin(self, StateMachineID_or_StateOriginInfo, StateIdx=None, StoreInputPositionF=None):
        """Add the StateMachineID and the given StateIdx to the list of origins of 
           this state.
           NOTE: The rule is that by default the 'store_input_position_f' flag
                 follows the acceptance state flag (i.e. by default any acceptance
                 state stores the input position). Thus when an origin is  added
                 to a state that is an acceptance state, the 'store_input_position_f'
                 has to be raised for all incoming origins.      
        """
        def __set_origin(self, origin):
            # check if origin has already been mentioned, else append the new origin
            try:
                idx = self.__origin_list.index(origin)  
                self.__origin_list[idx] = origin
            except:    
                self.__origin_list.append(origin)
            
        # -- entry checks 
        if StateMachineID_or_StateOriginInfo.__class__.__name__ == "StateOriginInfo":
            new_origin = deepcopy(StateMachineID_or_StateOriginInfo)
            __set_origin(self, new_origin)
            return

        StateMachineID = StateMachineID_or_StateOriginInfo
        assert type(StateMachineID) == long
        assert type(StateIdx) == long
           
        # -- create the origin data structure             
        if StoreInputPositionF == None: StoreInputPositionF = self.is_acceptance()
        new_origin = StateOriginInfo(StateMachineID, StateIdx, StoreInputPositionF)
        __set_origin(self, new_origin)

    def add_origin_list(self, OriginList, StoreInputPositionFollowsAcceptanceF=True):
        """Add list of origins to the StateInfo object. Optional argument tells wether
           the 'store_input_position_f' shall adapt to the acceptance of self, or
           the acceptance of the origin list is to be copied.
        """
        if StoreInputPositionFollowsAcceptanceF: 
            for origin in OriginList:
                self.add_origin(origin.state_machine_id, origin.state_index, 
                                StoreInputPositionF=self.is_acceptance())
        else:
            for origin in OriginList: self.add_origin(origin)
                
    def add_epsilon_target_state(self, TargetStateIdx):
        if TargetStateIdx not in self.__epsilon.target_state_indices:
            self.__epsilon.target_state_indices.append(TargetStateIdx)

    def add_transition(self, Trigger, TargetStateIdx): 
        """Adds a transition according to trigger and target index.

           Trigger == one of {integer, Interval, Interval Array} possible

           TargetStateIdx == None (default) => create new target state index 
        
        RETURNS: The target state index (may be created newly).
        """
        assert type(TargetStateIdx) == long or TargetStateIdx == None
        assert Trigger.__class__ in [int, long, list, Interval, NumberSet] or Trigger == None

        if Trigger == None:
            # Trigger = None means that the remaining set of triggers is to be
            # used (if the epsilon set is already empt, then one cannot assign
            # to it anything)
            if self.__epsilon.trigger_set.is_empty():
                return None
            Trigger = copy(self.__epsilon.trigger_set)
            self.__epsilon.trigger_set = NumberSet()

        if type(Trigger) == long: Trigger = int(Trigger)
            
        # (*) Append Transition: StartState --- Trigger ---> TargetState
        #
        #     -- ensure that for a given target state and 'raise-succes-action', there is only
        #        one trigger set. That means, that if a transition with the same 'path' exists
        #        do not create a new transition.
        for t in self.__transition_list:
            if t.target_state_index == TargetStateIdx:
                t.set(TriggerSet=t.trigger_set.union(NumberSet(Trigger)))
                break
        else:
            self.__transition_list.append(Transition(NumberSet(Trigger), TargetStateIdx))

        # (*) re-compute the epsilon trigger set
        all_triggers = NumberSet()
        for t in self.__transition_list:
            all_triggers.unite_with(t.trigger_set)
        self.__epsilon.trigger_set = all_triggers.inverse()

        return TargetStateIdx
    
    def replace_target_index(self, OriginalIdx, NewTargetIdx):
        """Replaces given OriginalIdx of a target state with the index of the
           new target state 'NewTargetIdx.
        """   
        # investigate normal transitions
        for t in self.__transition_list:
            if t.target_state_index == OriginalIdx:
                t.target_state_index = NewTargetIdx

        # investiage 'ELSE' transition
        if OriginalIdx in self.__epsilon.target_state_indices:
            # delete the original index from the list
            del self.__epsilon.target_state_indices[self.__epsilon.target_state_indices.index(OriginalIdx)]
            # add the replaced index to it
            self.__epsilon.target_state_indices.append(NewTargetIdx)

    def replace_drop_out_target_states_with_adjacent_targets(self):
        trigger_map = self.get_trigger_map() 

        if trigger_map == []:  # Nothing to be done, since there is nothing adjacent 
            return             # to the 'drop out' trigger. There is only an epsilon transition.

        assert len(trigger_map) >= 2

        # Target of internval (-oo, X) must be 'drop out' since there are no unicode 
        # code points below 0.
        assert trigger_map[0][1] == None
        assert trigger_map[0][0].begin == - sys.maxint


        # The first interval mentioned after that must not point to 'drop out' since
        # the trigger map must collect the same targets into one single interval.
        assert trigger_map[1][1] != None

        non_drop_out_target = trigger_map[1][1]
        self.add_transition(trigger_map[0][0], non_drop_out_target)
        
        # NOTE: Here we know that len(trigger_map) >= 2
        for trigger_set, target in trigger_map[2:]:

            if target == None: target = non_drop_out_target
            else:              non_drop_out_target = target

            self.add_transition(trigger_set, target)

    def delete_transitions_on_character_list(self, ForbiddenCharacterList):
        for char_code in ForbiddenCharacterList:
            for t in self.__transition_list:
                if t.trigger_set.contains(char_code):
                    t.trigger_set.cut_interval(Interval(char_code, char_code+1))
        self.delete_transitions_on_empty_trigger_sets()

    def delete_transitions_on_empty_trigger_sets(self):
        new_transition_list = []
        for t in self.__transition_list:
            if not t.trigger_set.is_empty(): new_transition_list.append(t)
        self.__transition_list = new_transition_list

    def delete_epsilon_target_state(self, TargetStateIdx):
        if TargetStateIdx in self.__epsilon.target_state_indices:
            del self.__epsilon.target_state_indices[self.__epsilon.target_state_indices.index(TargetStateIdx)]

    def delete_meaningless_origins(self):
        """Deletes origins that are not concerned with one of the three:
           -- post-conditions
           -- pre-conditions/also trivials
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
        self.__origin_list = filter(lambda origin:
                                    origin.post_conditioned_acceptance_f() or
                                    origin.pre_condition_id() != -1L       or
                                    origin.store_input_position_f()        or
                                    origin.pre_condition_begin_of_line_f(),
                                    self.__origin_list)

    def adapt_origins(self, StateMachineID, StateIndex):
        """Adapts all origins so that their original state is 'StateIndex' in state machine
           'StateMachineID'. Post- and pre-condition flags remain, and so the store input 
           position flag.
        """
        for origin in self.__origin_list:
            origin.state_machine_id = StateMachineID
            origin.state_index      = StateIndex 

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
        # NOTE: Acceptance origins sort before non-acceptance origins
        self.__origin_list.sort()
        new_origin_list = []
        unconditional_acceptance_found_f = False
        for origin in self.__origin_list:

            if origin.is_acceptance():
                # Only append acceptance origins until the first unconditional acceptance state 
                # is found. 
                if not unconditional_acceptance_found_f:
                    if origin.pre_condition_id() == -1L and not origin.pre_condition_begin_of_line_f():
                        unconditional_acceptance_found_f = True # prevent entering this part again
                    new_origin_list.append(origin)

            else:
                # Non-Acceptance origins do not harm in any way. Actually, the origins
                # with 'origin.is_end_of_post_conditioned_core_pattern() == True' **need**
                # to be in there. See the comment at the entry of this function.
                new_origin_list.append(origin)

        self.__origin_list = new_origin_list 

    def clone(self, ReplacementDictionary=None):
        """Creates a copy of all transitions, but replaces any state index with the ones 
           determined in the ReplacementDictionary."""
        result = StateInfo()
        result.__transition_list = deepcopy(self.__transition_list)
        result.__epsilon         = deepcopy(self.__epsilon)
        result.__origin_list     = deepcopy(self.__origin_list)
        result.__acceptance_f    = self.__acceptance_f
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
        if len(self.__origin_list) == 1:                             return False
        if self.__origin_list[0].state_machine_id != StateMachineID: return False
        if self.__origin_list[0].state_index != StateIdx:            return False

        return True
        
    def __repr__(self):
        return self.get_string()

    def get_string(self, StateIndexMap=None):
        msg = ""
        fill_str = ""
        # if information about origins of the state is present, then print
        if self.__origin_list != []:
            msg += " <~ "
            for origin in self.__origin_list:
                msg += repr(origin) + ", "
            msg = (msg[:-2] + "\n").replace("L","")     
            fill_str = "     "

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
        self.__trivial_pre_condition_character_codes = []
        if TrivialPreConditionCharacterCodes != -1:
            self.__trivial_pre_condition_character_codes = TrivialPreConditionCharacterCodes
            
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

    def get_trigger_set(self, StartIdx, TargetIdx):
        """Returns a set of triggers that lead from state 'StateIdx' to 'TargetIdx'.
        """
        if self.has_start_state_index(StartIdx) == False: 
            return None
        return self.states[StartIdx].get_trigger_set(TargetIdx)

    def get_invese_trigger_dictionary(self, StateIdx):
        """Returns a map, associating origin states to the triggers that 
           trigger from the origin states to the state index 'StateIndex'
        """
        dict = {}
        for state_index, state in self.states.items():
            if state.has_target_state(StateIdx):
                dict[state_index] = state.get_trigger_set(StateIdx)
        return dict

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

    def get_epsilon_closure(self, StateIdx, _considered_state_indices=None):
        """Return all states that can be reached from 'StateIdx' via epsilon
        transition."""
        assert self.has_state_index(StateIdx)

        if _considered_state_indices == None: 
            _considered_state_indices = []

        aggregated_epsilon_closure = [ StateIdx ] 
        for ti in self.states[StateIdx].get_epsilon_target_state_indices():
            if ti not in _considered_state_indices:
                aggregated_epsilon_closure.extend(self.get_epsilon_closure(ti, _considered_state_indices))
                _considered_state_indices.append(ti)

        return aggregated_epsilon_closure
                
    def get_transitions_of_state_set(StateIndices):
        """IS THIS FUNCTION STILL USED? 
           Returns all transitions that are possible from the give set of states. A transition
           consists of a trigger_set and a target_state_index. This function is useful for the
           subset construction on the epsilon closures (see: from NFA to DFA).
           NOTE: This functions traces down the epsilon transitions and adds all states of the
                 epsilon transition to the collected transitions.
        """
        assert type(state_machines) == list
        assert len(state_machines) != 0

        assert map(lambda x: x.__class__.__name__, state_machines) == ["StateMachine"] * len(state_machines)

        # epsilon closure of state = union of epsilon closure of each state
        # (use a dictionary to ensure uniqueness of states)
        # epsilon_closure_dict = {}
        #for state_index in StateIndices:  
        #    for si in self.get_epsilon_closure(state_index): 
        #        epsilon_closure_dict[si] = True   
        #epsilon_closure = epsilon_closure_dict.keys()
 
        # collect all transitions from the states in the state list
        # (use dictionary to combine transitions for each target state)
        transition_list_dict = {}
        for state_index in state_list:         
            for t in self.states[state_index].get_transitions():
                if transition_list_dict.has_key(t.target_state_index):  
                    transition_list_dict[t.target_state_index].append(deepcopy(t))
                else:
                    transition_list_dict[t.target_state_index] = [ deepcopy(t) ]
 
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

    def get_DFA(self):
        """Creates a deterministic finite automaton (DFA) from the current state 
           machine - which may be a NFA (non-deterministic finite automaton). This is
           a generlized version of the 'subset construction' algorithm. Where 
           subsection construction focusses on letters of an alphabet for the
           investigation of transitions, this algorithm focusses on elementary
           trigger sets. A very good description of the subset construction 
           algorithm can be found in 'Engineering a Compiler' by Keith Cooper.
        """
        def DEBUG_print(elementary_trigger_list):
            for ti, trigger_set in elementary_trigger_list:
                print "##elmtl: target=", ti, "trigger set=", trigger_set.get_utf8_string()
            print "----"

        # (*) create the result state machine
        initial_state_epsilon_closure = self.get_epsilon_closure(self.init_state_index) 
        #     -- one state in the initial state set = acceptance --> acceptance
        acceptance_f = False
        for state_index in initial_state_epsilon_closure:
            if self.is_acceptance(state_index): acceptance_f = True; break      

        result = StateMachine(AcceptanceF=acceptance_f, 
                              PreConditionStateMachine          = self.pre_condition_state_machine,
                              TrivialPreConditionBeginOfLineF   = self.__trivial_pre_condition_begin_of_line_f,
                              TrivialPreConditionCharacterCodes = self.__trivial_pre_condition_character_codes)

        # (*) initial state of resulting DFA = epsilon closure of initial state of NFA
        #     -- add the origin list of all states in the epsilon closure
        for state in map(lambda idx: self.states[idx], initial_state_epsilon_closure):
            result.states[result.init_state_index].add_origin_list(state.get_origin_list(), 
                                                                   StoreInputPositionFollowsAcceptanceF=False)
    
        # (*) prepare the initial worklist
        worklist = [ ( result.init_state_index, initial_state_epsilon_closure) ]

        while worklist != []:
            start_state_index, initial_state_combination = worklist.pop()
     
            # (*) compute the elementary trigger sets together with the 
            #     epsilon closure of target state combinations that they trigger to.
            #     In other words: find the ranges of characters where the state triggers to
            #     the given state combination.
            elementary_trigger_set_infos = self.get_elementary_trigger_sets(initial_state_combination)
     
            # DEBUG_print(elementary_trigger_set_infos)

            # (*) loop over all elementary trigger sets
            for epsilon_closure_of_target_state_combination, trigger_set in elementary_trigger_set_infos:
                #  -- if there is no trigger to the given target state combination, then drop it
                if trigger_set.is_empty(): continue

                # -- add a new target state representing the state combination
                #    (if this did not happen yet)
                target_state_index = \
                     map_state_combination_to_index(epsilon_closure_of_target_state_combination)

                # -- if target state combination was not considered yet, then also create 
                #    a new state in the state machine
                if result.has_state_index(target_state_index):
                    # -- add the transition 'start-state' to the 'target state'
                    result.add_transition(start_state_index, trigger_set, target_state_index)
                else:
                    # -- if one target in target combination == acceptance state
                    #    => combined target states == acceptance
                    acceptance_f = False
                    for state_index in epsilon_closure_of_target_state_combination:
                        if self.is_acceptance(state_index): acceptance_f = True
                    # -- add the transition 'start-state' to the 'target state'
                    #    (create implicitly the new target state in the state machine)
                    result.add_transition(start_state_index, trigger_set, target_state_index, acceptance_f)
                    # -- add the origin list of all states in the epsilon closure to the
                    #    the newly created target state.
                    for state in map(lambda idx: self.states[idx], epsilon_closure_of_target_state_combination):
                        result.states[target_state_index].add_origin_list(state.get_origin_list(),
                                                                          StoreInputPositionFollowsAcceptanceF=False)

                    worklist.append((target_state_index, epsilon_closure_of_target_state_combination))  
 
        return result 

    def get_hopcroft_optimization(self):
        """Reduces the number of states according to equivalence classes of states. It starts
           with two sets: 
           
                (1) the set of acceptance states, 
                    -- these states need to be splitted again according to their origin.
                       acceptance of state machine A is not equal to acceptance of 
                       state machine B.
                (2) the set of non-acceptance states.
           
           Whenever one finds a state in a state set that triggers on the same characters to 
           a different state set, the set has to be split in two sets of states:

               -- the set of states that trigger on trigger 'X' to state set 'K'
               -- the set of states that trigger on trigger 'X' to another state set

           The original state set is replaced by the two new ones. This algorithm is 
           repeated until the state sets do not change anymore.
        """        

        def get_state_set_containing_state_index(StateIdx, StateSetList):
            """Returns the index of the state set that contains the given 
               StateIdx. It returns -1  if no state set contains that index.
            """
            i = -1L   
            for state_set in StateSetList:
                i += 1L
                if StateIdx in state_set: return i
            return -1L  
                
        def get_aux_state(StateIdx, StateSetList):
            """Receives: an index of a state and a list of state sets. 
               Creates: a StateInfo-object where the transitions contain
               target indices of the state set, rather the the 'real' target 
               state, i.e. for any transition 't' in the auxiliary state:

                     t.target_state_index = Index of the StateSet, that contains
                                            the original target state in
                                            self.states[StateIdx]
            """
            assert type(StateIdx) == long

            aux_state = StateInfo()
            for t in self.states[StateIdx].get_transitions():
                state_set_i = get_state_set_containing_state_index(t.target_state_index, StateSetList)  
                assert state_set_i != -1L, \
                       "target state '" + repr(t.target_state_index) + "' not contained in any state set" + \
                       "state sets = " + repr(StateSetList)
                    
                aux_state.add_transition(t.trigger_set, state_set_i)

            aux_state.set_acceptance(self.states[StateIdx].is_acceptance())
            # add dynamically a new field to the StateInfo object: the original state of the aux state
            aux_state.related_state_idx = StateIdx
            return aux_state

        def split_state_set(AuxliaryStateSet, TriggerSet, TargetIdx):
            """Splits the given StateSet into two sets:
               -- one that contains states that trigger via TriggerSet **only** to TargetIdx, and
               -- one that contains states that trigger via TriggerSet to a different target.
            """ 
            states_that_fit = []
            states_that_do_not_fit = []
            for state in AuxliaryStateSet:
                if state.has_only_one_target_for_trigger_set(TriggerSet, TargetIdx):
                    states_that_fit.append(state.related_state_idx)
                else:
                    states_that_do_not_fit.append(state.related_state_idx)

            return states_that_fit, states_that_do_not_fit
           
        # (*) main algorithm    
        state_set_list = self.get_acceptance_state_list(ReturnNonAcceptanceTooF=True,
                                                        SplitAcceptanceStatesByOriginF=True)     
        state_set_list_changed_f = True   
        while state_set_list_changed_f:
            # loop over all sets in state set
            # by default the next state set list ist the same
            state_set_list_changed_f = False

            state_set_i = -1
            for state_set in state_set_list:
                state_set_i += 1
                
                N = len(state_set)
                assert N != 0, \
                       "state set of size '0' occured\n" + \
                       "state sets = " + repr(state_set_list)

                if N == 1:
                    # only one state in state set => no change possible
                    continue    
                # auxiliary states: an auxiliary state 'i' triggers to the state_set 'k' if 
                #                   the original state 'i' triggered to a target state belonging
                #                   to state set 'k'. (target-index = state set to which the
                #                   original target belongs).
                # NOTE: An auxiliary state contains an extra field: related_state_idx that
                #       contains the index as it appears in the state set and in self.states.
                aux_states = map(lambda x: get_aux_state(x, state_set_list), state_set)

                # -- sort the auxiliary state, so that aux states with only an epsilon transition
                #    come last. this way we ensure that they are checked against all normal transitions
                #    and no trigger sets considerations for epsilon transitions have to be made.
                aux_states.sort(lambda x, y: - cmp(len(x.get_transitions()), len(y.get_transitions())))
        
                # loop over all auxiliary states from state set
                for i in range(N):
                    # check for all a transitions: does a state in the same state set trigger
                    # on the same trigger to a different state set?
                    other_index_list = filter(lambda k: k != i, range(N))
                    other_aux_states = map(lambda k: aux_states[k], other_index_list)
                    for t in aux_states[i].get_transitions():
                        # split the auxiliary states in those that trigger on t.trigger_set to t.target_state_index
                        # and those that do not. If the second set, i.e. the set of stats that do not is non-empty
                        # then there are states that behave unequivalent, and we need to split the state set.
                        set_of_fit_states, set_of_others = split_state_set(other_aux_states, 
                                                                           t.trigger_set, t.target_state_index)     
                        if set_of_others != []: 
                            set_of_fit_states += [ aux_states[i].related_state_idx ]   # add the currently considered state, of course
                            # replace the currently considered state set by the 'split-up' 
                            del state_set_list[state_set_i]
                            state_set_list.extend([set_of_fit_states, set_of_others])
                            state_set_list_changed_f = True
                            # state set list has changed, return to lowest loop level
                            break
                    if state_set_list_changed_f: break
                if state_set_list_changed_f: break
                # if all states in the state sets trigger equivalently, then the state set remains
                # nothing has to be done to the new state_set list, because its by default setup that way 

            # next run with newly configured state set list

        # when the list of state sets did not change, it means that no states inside any
        # state set triggers to a different state set on the same trigger. the state sets can
        # become a new state machine. the state set that contains the initial state becomes 
        # the initial state of the new state machine.   
        state_set_containing_initial_state_i = get_state_set_containing_state_index(self.init_state_index, 
                                                                                    state_set_list)
        map_new_state_index = {}
        def get_new_state_index(state_set_index):
            if not map_new_state_index.has_key(state_set_index):
                map_new_state_index[state_set_index] = state_machine_index.get()
            return map_new_state_index[state_set_index]
                    
        result = StateMachine(get_new_state_index(state_set_containing_initial_state_i),
                              PreConditionStateMachine          = self.pre_condition_state_machine, 
                              TrivialPreConditionBeginOfLineF   = self.__trivial_pre_condition_begin_of_line_f,
                              TrivialPreConditionCharacterCodes = self.__trivial_pre_condition_character_codes)
        # build up the state machine out of the auxiliary states
        state_set_idx = -1L
        for state_set in state_set_list:
            state_set_idx += 1L
            assert state_set != [], \
                   "state set of size '0' occured\n" + \
                   "state sets = " + repr(state_set_list)

            # states in one set behave all equivalent with respect to target state sets
            # thus only one state from the start set has to be considered.      
            # NOTE: the target_state_index of an auxiliary state contains the index
            #       of a state set.           
            aux_state = get_aux_state(state_set[0], state_set_list)
            start_index = get_new_state_index(state_set_idx)
            if result.has_start_state_index(start_index) == False:
                result.create_new_state(StateIdx=start_index)

            # if state set contains an acceptance state, then the result is 'acceptance'
            # (NOTE: if some state in a state set where 'acceptance' states and others not,
            #        then the state sets where not equivalence classes. Thus checking one
            #        state in the set is enough. anyway the initial sets are splitted according
            #        to acceptance.)        
            result.set_acceptance(start_index, aux_state.is_acceptance())
    
            for t in aux_state.get_transitions():
                result.add_transition(start_index, 
                                      t.trigger_set, 
                                      get_new_state_index(t.target_state_index))

    
            # tracing the origins
            for state_idx in state_set:
                result.states[start_index].add_origin_list(self.states[state_idx].get_origin_list(),
                                                           StoreInputPositionFollowsAcceptanceF=False)
    
        return result    
        
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
            for t in self.states[state_idx].get_transitions():
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
            result.states[state_index].set_origin_list(state.get_origin_list())

        # -- only the initial state becomes an acceptance state
        result.states[self.init_state_index].set_acceptance(True, LeaveStoreInputPositionF=True)

        # -- setup an epsilon transition from an new init state to all previous 
        #    acceptance states.
        new_init_state_index = result.create_new_init_state() 
        for state_index in self.get_acceptance_state_list()[0]:
            result.add_epsilon_transition(new_init_state_index, state_index)        

        # -- for uniqueness of state ids, clone the result
        return result.clone()    
        
    def get_origin_ids_of_acceptance_states(self):
        """(1) get ids of all acceptance states.
           (2) extract their origins (provided they store the input position or are post conditioned).
        """
        # -- get list of states that are 'acceptance states'
        acceptance_state_id_list = self.get_acceptance_state_list()
        if acceptance_state_id_list == []: return []

        # -- collect origins of the acceptance states
        result = []
        for state_index in acceptance_state_id_list[0]:
            acceptance_state = self.states[state_index]
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
        return (self.__trivial_pre_condition_character_codes != []) or \
                self.has_trivial_pre_condition_begin_of_line()

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
            state.set_origin_list([])

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

    def mark_state_origins(self, OtherStateMachineID=-1L, DontMarkIfOriginsPresentF=False):
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
            if DontMarkIfOriginsPresentF and state.has_origin(): continue
            state.add_origin(state_machine_id, state_idx, state.is_acceptance())

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
        for state_i in self.states.keys():
            if NormalizeF:
                counter += 1L
                index_map[state_i]         = counter
                inverse_index_map[counter] = state_i
            else:
                index_map[state_i]         = state_i
                inverse_index_map[state_i] = state_i

        return index_map, inverse_index_map, counter

    def get_string(self, NormalizeF=False):

        # (*) normalize the state indices
        index_map, inverse_index_map, counter = self.__get_state_index_normalization(NormalizeF)
    
        # (*) construct text 
        msg = "init-state = " + repr(index_map[self.init_state_index]) + "\n"
        for printed_state_i in range(0, counter+1):
            printed_state_i = long(printed_state_i)
            real_state_i    = inverse_index_map[printed_state_i]
            state           = self.states[real_state_i]
            if state.is_acceptance(): msg += "%05i*" % printed_state_i + state.get_string(index_map)
            else:                     msg += "%05i"  % printed_state_i + state.get_string(index_map)
            
        if self.pre_condition_state_machine != None:
            msg += "pre-condition inverted = "
            msg += repr(self.pre_condition_state_machine)           

        return msg

    def get_graphviz_string(self, NormalizeF=False):
        # (*) normalize the state indices
        index_map, inverse_index_map, counter = self.__get_state_index_normalization(NormalizeF)

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
        for printed_state_i in range(0, counter+1):
            printed_state_i = long(printed_state_i)
            real_state_i    = inverse_index_map[printed_state_i]
            state           = self.states[real_state_i]
            if state.is_acceptance(): 
                acceptance_state_str += "%i; " % int(printed_state_i)
            transition_str += state.get_graphviz_string(printed_state_i, index_map)

        if acceptance_state_str != "": acceptance_state_str = acceptance_state_str[:-2]
        return blue_print(frame_txt, [["$$ACCEPTANCE_STATES$$", acceptance_state_str],
                                      ["$$TRANSITIONS$$",       transition_str]])
        
            
