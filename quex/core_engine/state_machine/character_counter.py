from quex.core_engine.interval_handling import Interval, NumberSet

def get_newline_n(state_machine):   
    """
       Counts the number of newlines that appear until the acceptance state. 
       The part of the post condition is omitted. 

       RETURNS:  0      if statemachine / pattern does not contain the newline
                        character at all.
                 N > 0  number of newlines that are **always** required in order to
                        reach an acceptance state.
                 -1     the number of newlines cannot be determined, because of 
                        recursion or because there are different pathes to acceptance
                        with different numbers of newlines occuring.

       NOTE: Only the core pattern is concerned---not the pre- or post-condition.
    """
    return __dive(state_machine, state_machine.init_state_index, 0, [], CharacterToCount=ord('\n'))

def get_character_n(state_machine):
    """
       Counts the number of newlines that appear until the acceptance state. 
       The part of the post condition is omitted. 

       RETURNS:  0      if statemachine / pattern does not contain the newline
                        character at all.
                 N > 0  number of newlines that are **always** required in order to
                        reach an acceptance state.
                 -1     the number of newlines cannot be determined, because of 
                        recursion or because there are different pathes to acceptance
                        with different numbers of newlines occuring.

       NOTE: Only the core pattern is concerned---not the pre- or post-condition.
    """
    return __dive(state_machine, state_machine.init_state_index, 0, [], CharacterToCount=-1)

def contains_only_spaces(state_machine):
    """Determines wether there are only spaces on the way to the acceptance state.
    """
    state = state_machine.get_init_state()

    done_state_index_list = [ state_machine.init_state_index ]
    while 1 + 1 == 2:
        target_state_list = state.get_target_state_indices()
        # if a pattern contains only ' ', then there is no place for more than
        # one target state, since every state has only one trigger and one target state
        if len(target_state_list) > 1: return False

        # does state exclusively trigger on ' '
        all_trigger_set = state.get_trigger_set_union()
        if all_trigger_set.contains(ord(' ')) == False: return False
        if all_trigger_set.difference(NumberSet(ord(' '))).is_empty() == False: return False

        next_state = state.get_result_state_index(ord(' ')) 
        if next_state == None: return False

        state = state_machine.states[next_state]

        # -- acceptance state of non-post-conditioned pattern, or
        # -- end of core pattern of a post-conditioned pattern => done
        if state.is_store_input_position(): return True

        if next_state in done_state_index_list: return False




def __recursion_contains_critical_character(state_machine, Path, TargetStateIdx, Character):
    """Path      = list of state indices
       Character = character code of concern.
                   -1 => any character.
       
       RETURNS:  True = the path contains the TargetStateIdx and on the path
                        there is the critical character.
                 False = the path does either not contain the TargetStateIdx,
                         i.e. there will be no recursion, or the recursion
                         path does not contain the critical character and 
                         therefore is not dangerous.

       NOTE: This function is required to judge wether a recursion occurs
             that effects the number of characters to be counted. If so,
             then the recursion signifies that the number of characters
             to be matched cannot be determined directly from the state machine.
             They have to be computed after a match has happend.
    """
    if TargetStateIdx not in Path: 
        raise "error: function considered to be used for recursion paths. no recursion here."

    # -- recursion detected!
    #    did the critical character occur in the path?
    if Character == -1: return True

    occurence_idx = Path.index(TargetStateIdx)
    prev_idx      = TargetStateIdx
    for idx in Path[occurence_idx+1:] + [TargetStateIdx]:
        # does transition from prev_state to state contain newline?
        trigger_set = state_machine.states[prev_idx].get_trigger_set(idx)
        if trigger_set.contains(Character):
            return True                       # YES! recursion with critical character
        prev_idx = idx

    # -- no critical character in recursion --> OK, no problem
    # -- state has been already handled, no further treatment required
    return False

def __recursion_with_critical_character_ahead(state_machine, State, PassedStateList, Character):

    for follow_state_index in State.get_target_state_indices():

        if follow_state_index not in PassedStateList: continue

        if __recursion_contains_critical_character(state_machine, PassedStateList, follow_state_index, Character):
            return True

    return False

def __dive(state_machine, state_index, character_n, passed_state_list, CharacterToCount):

    state = state_machine.states[state_index]

    new_passed_state_list = passed_state_list + [ state_index ]

    # -- recursion?
    if __recursion_with_critical_character_ahead(state_machine, state, new_passed_state_list, 
                                                 CharacterToCount):
        return -1
    # -- if no recursion is detected and the state is the end of a core exression
    #    of a post conditioned pattern, then this is it. No further investigation
    #    from this point on. The post condition state machine is not considered 
    #    for line number counting.
    if state.is_post_conditioned(): return character_n
    
    # trigger_map[target_state_index] = set that triggers to target state index
    trigger_dict = state.get_trigger_dictionary()
    if trigger_dict == {}: return character_n
        
    if state.is_acceptance():  prev_characters_found_n = character_n
    else:                      prev_characters_found_n = None

    for follow_state_index in trigger_dict.keys():

        # -- do not follow recursive paths. note: this is only relevant for specified
        #    CharacterToCount != -1. Otherwise, recursions are broken up when detected ahead.
        if follow_state_index in new_passed_state_list: continue
            
        increment = 0
        trigger_set = trigger_dict[follow_state_index]
        if CharacterToCount == -1:
            increment = 1
        elif trigger_set.contains(CharacterToCount):
            # -- if a transition contains character and also another possible trigger to the 
            #    same target, then the number of characters is undefined.
            if trigger_set.difference(Interval(CharacterToCount)).is_empty() == False: return -1
            increment = 1

        characters_found_n = __dive(state_machine, follow_state_index, character_n + increment, 
                                    new_passed_state_list, CharacterToCount)


        # -- if one path contains an undefined number of characters, then the whole pattern
        #    has an undefined number of characters.
        if characters_found_n == -1: return -1
        # -- if one path contains a different number of characters than another path
        #    then the number of characters is undefined.
        if prev_characters_found_n != None and \
           prev_characters_found_n != characters_found_n: return -1

        prev_characters_found_n = characters_found_n

    return prev_characters_found_n


