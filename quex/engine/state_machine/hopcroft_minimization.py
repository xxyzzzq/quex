# (C) 2005-2011 Frank-Rene Schaefer
import quex.engine.state_machine.index as     state_machine_index
from   quex.engine.state_machine.core  import StateMachine
from   quex.engine.state_machine.index import map_state_combination_to_index
from   itertools   import islice, ifilter, chain
from   collections import defaultdict
import sys

DEBUG_cmp = defaultdict(int)

class HopcroftMinization:
    """Combine sets of states that are equivalent. 

       Example:
                      .-- 'a' --->( 2 )--- 'a' --.           (( 3 )) accepts
                     /                            \ 
                  ( 1 )                         (( 3 ))
                     \                            /
                      '-- 'b' --->( 4 )--- 'a' --'

        Triggers exactly the same as 

                  ( 1 )--- [ab] --->( 2 )--- 'a' -->(( 3 ))

        In which case one state is spared. In practical applications the
        Hopcroft Minization can tremendously reduce the size of a state
        machine.

        The mathematics behind it can be found at 
        
                    http://en.wikipedia.org/wiki/DFA_minimization

        The algorithm below adapted the hopcroft algorithm in order to
        cope with the large trigger sets.

        (1) Basic Idea of Hopcroft Minimization _______________________________

            (i) Define the initial state sets:

                States that accept patterns --> each in the corresponding acceptance state set
                Non-acceptance states       --> all together in one state set.

                All states are marked 'to do', i.e. to be considered.

            (ii) Loop over all 'to do' state sets:

                 if all states in a state set trigger to the same target state sets,
                 then they are equivalent. 

                 if then, the target state set is 'done', the state set can be 
                 considered done. (done = delete from 'to do').

                 if not, the state set needs to be split. Add the new one to to do list.

             (iii) Goto (ii) until to do list is empty.


        (2) Frank-Rene Schaefer's Adaptations _________________________________

             In many cases, already the difference in target_sets reveals that
             a state set needs to be split. The term 'harmonic' is defined for
             the algorithm below:

             Harmonic: A state set is harmonic, if and only if all states in the
                       state set trigger to target states that belong to the
                       same state set.

             The split is then separated into two repeated phases:

                 (1) Split until all non-harmonic state sets disappear.
                 (2) Split all states in the current to do list.
                 Repeat
    """
    def __init__(self, StateMachine):
        self.sm = StateMachine
        #
        # -- map: state index --> index of the state set that contains it
        self.map = {} 
        #
        # -- create: self.state_set_list by initial split of all states.
        self.__todo         = set([])  # state sets to be investigated
        self.__non_harmonic = set([])  # suspects to trigger to different target state sets
        self.size           = 0
        self.__initial_split()
        # -- from_map: target index --> from what states the target state is entered
        self.from_map = dict([(i, []) for i in self.sm.states.iterkeys()])
        for origin_index, state in self.sm.states.iteritems():
            for target_index in state.transitions().get_map().iterkeys():
                self.from_map[target_index].append(origin_index)
        # -- to_map: state_index --> list of target states
        self.to_map = dict([(i, self.sm.states[i].transitions().get_map()) for i in self.sm.states.keys()])

        self.run()

    def todo_list(self):
        return list(self.__todo)

    def todo_add(self, StateSetIndex):
        self.__todo.add(StateSetIndex)

    def todo_remove(self, StateSetIndex):
        assert StateSetIndex not in self.__non_harmonic
        self.__todo.remove(StateSetIndex)

    def non_harmonic_list(self):
        return list(self.__non_harmonic)

    def non_harmonic_remove(self, StateSetIndex):
        if StateSetIndex in self.__non_harmonic: 
            self.__non_harmonic.remove(StateSetIndex)

    def non_harmonic_add(self, StateSetIndex):
        # assert StateSetIndex in self.__todo
        self.__non_harmonic.add(StateSetIndex)

    def run(self):
        # It is conceivable (an appears in practise) that target state sets 
        # that are undone point to each other in loops. Then, they can never
        # be considered undone. Check against this by means of a change flag.

        ## all_state_index_list = set(self.sm.states.iterkeys())

        ## print "##SM:", self.sm.get_string()

        change_f = True
        while len(self.__todo) != 0 and change_f:
            # Loop over all sets in state set
            # by default the next state set list is the same
            while len(self.__non_harmonic) != 0:
                for i in list(self.__non_harmonic):
                    self.pre_split(i)

            ## print "##_________________"
            ## for i in sorted(self.__todo, key=lambda x: min(self.state_set_list[x])):
            ##    print "##", self.state_set_list[i]

            change_f = False
            for i in list(sorted(self.__todo, key=lambda i: len(self.state_set_list[i]), reverse=True)): 
                if i in self.__non_harmonic: continue

                st = len(self.__todo); sn = len(self.__non_harmonic)
                if self.split(i): change_f = True           
                else:             assert len(self.__non_harmonic) == sn
                assert len(self.__todo) <= st + 1

            # assert self.__non_harmonic.issubset(self.__todo)

        global DEBUG_cmp
        # print "##", DEBUG_cmp
        # 'self.state_set_list' now contains the state sets that represent
        #                       the state machine. 
        ## result_state_index_list = set()
        ## for state_set in self.state_set_list:
        ##    assert result_state_index_list.isdisjoint(state_set)
        ##    result_state_index_list.update(state_set)
        ## assert result_state_index_list == all_state_index_list
            
    def pre_split(self, StateSetIndex):
        """Separate state_set into two state sets:

           (1) The set of states that have the same target state sets,
               as a arbitrarily chosen prototype := 'harmonic'.
           (2) Those who differ from the prototype.

           The state set that matches the prototype can be considered 
           'harmonic' since it triggers for sure to the same target
           state sets. The prototype is packed into a separate state
           set. The other states remain in the old state set. 

           If there was a prototype that separated the set then the
           what does not match the prototype is possibly not-harmonic.

           RETURNS: True  Split happened.
                          The old state set is possible non-harmonic.
                    False No split happened.
                          The old state set and the prototype are
                          identical.
        """
        assert StateSetIndex in self.__todo
        assert StateSetIndex in self.__non_harmonic
        state_set = self.state_set_list[StateSetIndex]
        assert len(state_set) > 1

        # NOTE: Previous experiments have shown, that the split does **not** become
        #       faster, if all non-harmonic states are identified at once. The overhead
        #       of the book-keeping is much higher than the benefit. Also, statistics
        #       have shown that a very large majority of cases results in one or two
        #       state sets only.

        def get_target_state_set_list(StateIndex):
            target_list = self.to_map[StateIndex].iterkeys()
            return set([self.map[i] for i in target_list])

        state_set = self.state_set_list[StateSetIndex]
        prototype = get_target_state_set_list(state_set[0])

        match_set = [ state_set[0] ] 
        for state_index in islice(state_set, 1, None):
            if prototype == get_target_state_set_list(state_index): 
                match_set.append(state_index)

        # NOW: match_set = harmonic
        #      remainder = possibly not harmonic

        # To split, or not to split ...
        if len(match_set) == len(state_set): 
            self.non_harmonic_remove(StateSetIndex)
            return False 

        # The match set is now extracted from the original state set

        # -- Delete all states that are put into other sets from the original state set
        # -- Add the new set to the state_set_list
        # -- Sets of size == 1: 1. are harmonic (trigger all to the same target state sets).
        #                       2. cannot be split further => done.
        self.__extract(StateSetIndex, state_set, match_set)
        # (by default, the new set is not added to non_harmonic, which is true.)

        # -- Neither the new, nor the old state set can be labeled as 'done' because
        #    the exact transitions have not been investigated, yet. The only exception
        #    if len(state_set) == 1, because then it cannot be split anyway.
        #    if len(match_set) == 1, it is not added to the todo list by __add_state_set().
        if len(state_set) == 1: 
            self.non_harmonic_remove(StateSetIndex)
            self.todo_remove(StateSetIndex)

        # -- The state set is split, thus state sets triggering to it may be non-harmonic
        #    (this may include recursive states, so this has to come after anything above)
        self.__check_dependencies(chain(state_set, match_set))

    def split(self, StateSetIndex):
        """RETURNS:  False   if StateSet does not need to be split up any further.
                     True    if the state set requires a split.
        """
        pass#assert StateSetIndex in self.__todo
        state_set = self.state_set_list[StateSetIndex]
        #
        N         = len(state_set)
        pass#assert N != 0, "State set of size '0'. List = " + repr(self.state_set_list)
        # only one state in state set => no change possible
        if N == 1: 
            self.todo_remove(StateSetIndex)
            return False    

        def normalized_map(DB):
            result = {}
            for target_index, trigger_map in DB.iteritems():
                # Target in terms of equivalent state sets
                target = self.map[target_index]
                entry  = result.get(target)
                if entry == None: entry = trigger_map 
                else:             entry = entry.union(trigger_map)
                result[target] = entry
            return result

        # -- choose one arbitrary state (for example state 0) as a prototype
        #    which is compared against the remaining states in the state set.
        prototype_index      = state_set[0]
        prototype_map        = normalized_map(self.to_map[prototype_index])
        equivalent_state_set = [ prototype_index ] 

        if len(prototype_map) == 0:
            # If there are no target states, then there can be no split.
            # The state set is done.
            self.todo_remove(StateSetIndex)
            return False

        # Since all state sets are 'harmonized' at the entry of this function
        # It can be assumed that the prototype contains all target_set indices
        # Loop over all remaining states from state set
        for state_index in islice(state_set, 1, None):
            state_map = normalized_map(self.to_map[state_index])
            for target in prototype_map.iterkeys():
                if not prototype_map[target].is_equal(state_map[target]): break
            else:
                equivalent_state_set.append(state_index)

        # The transitions have been investigated. Now, we can judge whether 
        # a state set is done: All target state sets must be done.
        if self.__todo.isdisjoint(prototype_map.keys()):  
            done_f = True
        elif StateSetIndex in self.__todo:
            # If the only undone target state set is the set itself (loop),
            # then it is also considered as 'done'.
            tmp = set(self.__todo)
            tmp.remove(StateSetIndex)
            if tmp.isdisjoint(prototype_map.keys()): done_f = True
            else:                                    done_f = False
        else: 
            done_f = False

        if len(equivalent_state_set) == len(state_set): 
            self.non_harmonic_remove(StateSetIndex)
            if done_f: self.todo_remove(StateSetIndex)
            return False

        # -- The state set is split, thus state sets triggering to it may be non-harmonic
        #    (this may include recursive states, so this has to come after anything above)
        self.__check_dependencies(state_set)

        new_index = self.__extract(StateSetIndex, state_set, equivalent_state_set)

        if len(state_set) == 1: self.non_harmonic_remove(StateSetIndex); self.todo_remove(StateSetIndex)
        else:                   self.non_harmonic_add(StateSetIndex)
        if done_f:
            # if the new state state is of size one, it has not been added to 'todo' list
            if len(equivalent_state_set) != 1: self.todo_remove(new_index)

        return True

    def __initial_split(self):
        """Returns the set of states that are 'acceptance'. If the optional     
           argument 'ReturnNonAcceptanceTooF' is specified, then the non-
           acceptance states are also returned.

        """   
        self.state_set_list = []

        non_acceptance_state_set = []
        for state_index, state in ifilter(lambda x: not x[1].is_acceptance(), self.sm.states.iteritems()):
            non_acceptance_state_set.append(state_index) 

        # NOTE: Under normal conditions, there **must** be at least one non-acceptance state,
        #       which happens to be the initial state (otherwise nothing would be acceptable).
        #       But: The minimization might be called for sub-patterns such as 'a*' which
        #       actually allow the first state to be acceptance.
        if len(non_acceptance_state_set) != 0: 
            i = self.__add_state_set(non_acceptance_state_set)
            if len(non_acceptance_state_set) != 1: self.non_harmonic_add(i)

        # BUT: There should always be at least one acceptance state.
        pass#assert len(self.sm.states) - len(non_acceptance_state_set) != 0

        # (2) Split the acceptance states according to their origin. An acceptance
        #     state maching the, for example, an identifier is not equivalent an 
        #     acceptance state thate that matches a number.
        db = {}   
        for state_index in ifilter(lambda x: x not in non_acceptance_state_set, self.sm.states.iterkeys()): 
            state = self.sm.states[state_index]
            origin_state_machine_ids = map(lambda origin: origin.state_machine_id, 
                                           state.origins())
            state_combination_id = map_state_combination_to_index(origin_state_machine_ids) 
            if db.has_key(state_combination_id): db[state_combination_id].append(state_index)
            else:                                db[state_combination_id] = [ state_index ]                             

        # (2b) Enter the split acceptance state sets.
        for state_set in db.values():
            i = self.__add_state_set(state_set)
            if len(state_set) != 1: self.non_harmonic_add(i)

    def __extract(self, MotherIdx, mother_state_set, NewStateSet):
        # -- Delete states from the mother set
        for state_index in NewStateSet:
            del mother_state_set[mother_state_set.index(state_index)]

        # (if all was to be extracted then the mother state set could remain
        #  and the new state set be represented by the mother_state_set)
        pass#assert len(mother_state_set) != 0

        # -- Create a new state set in state_set_list
        return self.__add_state_set(NewStateSet)

    def __check_dependencies(self, StateSet):
        # If a state set is split, then every state set that triggered to it may be non-harmonic
        # origin_state_list = list of states that trigger to states inside mother_state_set.
        for state_index in StateSet:
            origin_state_list = self.from_map[state_index]
            for state_set_index in [self.map[i] for i in origin_state_list]:
                # Exception: state set is of size 'one', then it cannot be non-harmonic
                pass#assert len(self.state_set_list[state_set_index]) != 0
                if len(self.state_set_list[state_set_index]) != 1:
                    # A state_set cannot be 'done' if one of the target state_sets is not done
                    # Such a case, would be caught by the assert inside 'non_harmonic_add'.
                    self.non_harmonic_add(state_set_index)

        return True

    def __add_state_set(self, NewStateSet):
        """DoneF -- The new state set does not need to be further investigated.

           HarmonicF -- All states of the new state set trigger to the same
                        target state sets.
        
           RETURNS: N >= 0 index of the new state set, if it is added to 
                           the todo list
                    - 1    if the new state set is not added to the todo list.
        """
        pass#assert len(NewStateSet) != 0

        #    Create the new state set at the end of the list
        self.state_set_list.append(NewStateSet)
        # -- Mark in the map the states that have moved to the new state set at the end.
        for state_index in NewStateSet:
            self.map[state_index] = self.size

        # -- Index of the last state set = size - 1
        if len(NewStateSet) != 1: self.todo_add(self.size)

        # -- increase the size counter
        self.size += 1 

        return self.size - 1

def do(SM, CreateNewStateMachineF=True):
    """Reduces the number of states according to equivalence classes of states. It starts
       with two sets: 
       
            (1) the set of acceptance states, 
                -- these states need to be split again according to their origin.
                   Acceptance of state machine A is not equal to acceptance of 
                   state machine B.
            (2) the set of non-acceptance states.
       
       Whenever one finds a state in a state set that triggers on the same characters to 
       a different state set, the set has to be split in two sets of states:

           -- the set of states that trigger on trigger 'X' to state set 'K'
           -- the set of states that trigger on trigger 'X' to another state set

       The original state set is replaced by the two new ones. This algorithm is 
       repeated until the state sets do not change anymore.
    """        
    result = HopcroftMinization(SM)

    if CreateNewStateMachineF: return create_state_machine(SM, result)
    else:                      return adapt_state_machine(SM, result)

def create_state_machine(SM, Result):
    # If all states are of size one, this means, that there were no states that
    # could have been combined. In this case a simple copy of the original
    # state machine will do.
    if len(filter(lambda state_set: len(state_set) != 1, Result.state_set_list)) == 0:
        return SM.clone()
    
    # Define a mapping from the state set to a new target state index
    map_new_state_index = dict([(i, state_machine_index.get()) for i in xrange(len(Result.state_set_list))])
                
    # The state set that contains the initial state becomes the initial state of 
    # the new state machine.   
    state_set_containing_initial_state_i = Result.map[SM.init_state_index]
    result = StateMachine(map_new_state_index[state_set_containing_initial_state_i],
                          Core = SM.core())

    # Ensure that each target state index has a state inside the state machine
    for new_state_index in map_new_state_index.values():
        result.create_new_state(StateIdx=new_state_index)

    # Build up the state machine out of the remaining state sets
    state_set_idx = -1L
    for state_set in Result.state_set_list:
        state_set_idx += 1L
        pass#assert len(state_set) != 0, "State set of size '0'. List = " + repr(Result)

        # The prototype: States in one set behave all equivalent with respect to target state sets
        # thus only one state from the start set has to be considered.      
        prototype    = SM.states[state_set[0]]
        # The representive: shall represent the state set in the new state machine.
        representive = result.states[map_new_state_index[state_set_idx]]

        # The representive must have all transitions that the prototype has
        for target_state_index, trigger_set in prototype.transitions().get_map().iteritems():
            target_state_set_index = Result.map[target_state_index]
            representive.add_transition(trigger_set, 
                                        map_new_state_index[target_state_set_index])

        # Merge all core information of the states inside the state set.
        # If one state set contains an acceptance state, then the result is 'acceptance'.
        # (Note: The initial split separates acceptance states from those that are not
        #  acceptance states. There can be no state set containing acceptance and 
        #  non-acceptance states) 
        # (Note, that the prototype's info has not been included yet, consider whole set)
        for state_idx in state_set:
            representive.merge(SM.states[state_idx])

    return result    

def adapt_state_machine(sm, Result):
    # If all states are of size one, this means, that there were no states that
    # could have been combined. In this case nothing is to be done.
    for dummy in ifilter(lambda state_set: len(state_set) != 1, Result.state_set_list):
        break
    else:
        return sm
    
    # We know, that all states in a state set are equivalent. Thus, all but one
    # of each set can be thrown away.
    replacement_dict = {}
    for state_set in Result.state_set_list:
        if len(state_set) == 1: continue

        # Merge all core information of the states inside the state set.
        # Do not delete the init state
        if sm.init_state_index in state_set: prototype_index = sm.init_state_index
        else:                                prototype_index = state_set[0]  

        prototype = sm.states[prototype_index]
        for state_idx in ifilter(lambda x: x != prototype_index, state_set):
            prototype.merge(sm.states[state_idx])
            # The prototype takes over the role of all
            replacement_dict[state_idx] = prototype_index

    pass#assert sm.init_state_index not in replacement_dict.iterkeys()

    # Replace the indices of the thrown out states
    for state_idx in replacement_dict.iterkeys():
        del sm.states[state_idx]

    for state in sm.states.itervalues():
        state.transitions().replace_target_indices(replacement_dict)

    return sm    

