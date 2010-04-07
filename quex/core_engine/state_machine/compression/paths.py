from quex.core_engine.interval_handling import NumberSet
from copy import deepcopy, copy

"""Checks whether the transitions of state 0 and state 1
   can be part of a path, e.g.

      (0)-----( 'a' )---->(1)-----( 'b' )----->(2)

   can be setup as path, i.e 'ab'.
"""

class SingleCharacterPath:
    def __init__(self, StartStateIdx, Skeleton, FirstWildCardChar, StartPath):
        self.start_state_index = StartStateIdx
        self.end_state_index   = -1
        self.character_sequence = [ StartPath ]

        self.skeleton          = Skeleton
        self.skeleton_key_set  = Skeleton.keys()
        self.skeleton_key_n    = len(self.skeleton_key_set)
        # Character that may trigger to any state. This character is
        # adapted when the first character of the path is different
        # from the wildcard character. Then it must trigger to whatever
        # the correspondent state triggers.
        self.first_wildcard    = FirstWildCardChar

    def match_skeleton(self, TransitionMap, TargetIdx, TriggerCharToTarget):

        # The element of a path cannot be triggered by the skeleton!
        if self.skeleton.has_key(TargetIdx): return False
        # All other target states must be the same, otherwise the 
        # skeleton is not a skeleton for the transition.
        # But, wait: The wildcard might be used to trigger to another
        #            state. If it is still available, the state can
        #            trigger to one more single character transition.
        delta_n = len(TransitionMap) - self.skeleton_key_n
        if self.first_wildcard != None:
            if delta_n not in [1, 2]: return False
        else:
            if delta_n != 1:          return False

        # Now: -- All target indices in skeleton *must* also in TransitionMap!
        #      -- TransitionMap shall contain only one target index that is not
        #         in skeleton: 'TargetIdx', plus maybe another that is then
        #         to be handled by the wildcard.
        for target_idx, skeleton_trigger_set in self.skeleton.items():
            other_trigger_set = TransitionMap.get(target_idx)
            if other_trigger_set != None:
                if skeleton_trigger_set.is_equal(other_trigger_set): 
                    continue
                # Can be plug a wildcard into skeleton trigger set?
                if self.wildcard != None \ 
                   and can_plug_to_equal(skeleton_trigger_set, self.wildcard, 
                                         other_trigger_set): 
                    self.wildcard = None # wildcard is used now
                    continue

                # Maybe the current single transition intersects with a 
                # skeleton domain => no problem.
                if can_plug_to_equal(other_trigger_set, TriggerCharToTarget,
                                     skeleton_trigger_set):
                    continue
                # Trigger sets differ and no wildcard or single transition
                # can 'explain' that => skeleton does not fit.
                return False
            else:
                # Skeleton *must* have the key otherwise it would not be there
                candidate = self.skeleton[target_idx].get_the_only_element()
                # If the additional target has a trigger set of size > 1
                # => no single character transition can fix it.
                if   candidate == None:                return False
                elif candidate != TriggerCharToTarget: return False
                continue
        return True



    def __repr__(self):
        return "".join(["start    = %i;\n" % self.start_state_index,
                        "skeleton = %s;\n" % self.skeleton,
                        "path     = '"] + map(chr, self.character_sequence) +
                        ["';\n"])

def find_paths(SM):
    """SM = state machine of analyzer.

       Try to identify 'pathes' that is state transitions in the state
       machine so that a sequence of states can be combined into 
       a single state of the shape:

           /* Pre-Test for walking on the path */
           if( input == path_element ) {
               ++path_element;
               if( *path_element == 0 ) goto terminal_of_path;
           }
           /* Skeleton (transitions that are common for all elements of path) */
    """
    return __find_begin(SM, SM.init_state_index)

__find_begin_done_state_idx_list = {}
def __find_begin(sm, StateIdx):
    global __find_begin_done_state_idx_list

    State       = sm.states[StateIdx]
    result_list = []

    transition_map = State.transitions().get_map()
    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():
        if __find_begin_done_state_idx_list.has_key(target_idx): continue

        result_list.extend(__find_begin(sm, target_idx))

        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # A new path begins, find the 'skeleton'.
        # The 'skeleton' is the transition map without the single transition
        skeleton = copy(transition_map) # Shallow copy, i.e. copy references
        del skeleton[target_idx]        # Delete reference to 'target_idx->trigger_set'

        path = SingleCharacterPath(StateIdx, skeleton, path_char)
            
        result_list.extend(__find_continuation(sm, target_idx, path))

    __find_begin_done_state_idx_list[StateIdx] = True
    return result_list

__find_continuation_done_state_idx_list = {}
def __find_continuation(sm, StateIdx, the_path):
    global __find_continuation_done_state_idx_list 
    State       = sm.states[StateIdx]
    result_list = []
    print "##fc:", the_path.character_sequence

    transition_map = State.transitions().get_map()

    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():

        # Find a 'single character transition'
        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue
        print "##", path_char

        # Does the rest of the transitions fit the 'skeleton'?
        if not the_path.match_skeleton(transition_map, target_idx): continue 
        print "##match"
                                       
        single_char_transition_found_f = True

        path = deepcopy(the_path)
        path.character_sequence.append(path_char)

        if __find_continuation_done_state_idx_list.has_key(target_idx): 
            # End of path detected
            path.end_state_index = StateIdx
            result_list.append(path)
        else:
            # Find a continuation of the path
            result_list.extend(__find(sm, target_idx, path))

    if not single_char_transition_found_f and len(the_path.character_sequence) != 1:
        the_path.end_state_index = StateIdx
        result_list.append(the_path)

    __find_continuation_done_state_idx_list[StateIdx] = True
    return result_list

def is_difference_single_character(Set0, Set1, Char):
    """If Set1 contains more characters than Set0, then can the
       difference be described by 'Char'?
    
       IMPORTANT NOTE: This function talks about a **set difference**,
       thus from 
                       Set1 - Set0 == empty

       it cannot be concluded that 

                       Set0 - Set1 == empty.

       RETURNS: None,  if Set0 covers Set1 completely and no 'plug' is needed.
                False, if Set0 cannot cover Set1 just by adding the character 'Char'.
                True,  if Set0 + Char covers Set1.
    
    """
    # If interval number differs more than one, then no single
    # character can do the job.
    if Set1.interval_number() - Set0.interval_number() > 1: return False

    # If the difference Set1 - Set0 == Char, then the Set0 can be
    # fixed, so that the difference is empty.
    delta = Set1.difference(Set0)
    # If there is no difference to make up for, then no plug needed.
    if delta.is_empty(): return None

    # Check wether the single character can plug
    if delta.interval_number() != 1: return False
    x = delta.get_intervals(PromiseToTreatWellF=True)
    if x[0].end - x[0].begin != 1:   return False

    return x[0].begin == Char
        









