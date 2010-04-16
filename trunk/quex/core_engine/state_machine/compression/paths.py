from quex.core_engine.interval_handling import NumberSet, Interval
from copy import deepcopy, copy

"""Checks whether the transitions of state 0 and state 1
   can be part of a path, e.g.

      (0)-----( 'a' )---->(1)-----( 'b' )----->(2)

   can be setup as path, i.e 'ab'.
"""

class SingleCharacterPath:
    def __init__(self, StartStateIdx, Skeleton, StartCharacter):
        self.start_state_index = StartStateIdx
        self.end_state_index   = -1
        self.sequence          = [ (StartStateIdx, StartCharacter) ]

        self.skeleton          = Skeleton
        self.skeleton_key_set  = set(Skeleton.keys())
        self.skeleton_key_n    = len(self.skeleton_key_set)
        # Character that may trigger to any state. This character is
        # adapted when the first character of the path is different
        # from the wildcard character. Then it must trigger to whatever
        # the correspondent state triggers.
        self.wildcard          = StartCharacter

    def contains(self, StateIdx):
        for state_idx, char in self.sequence:
            if state_idx == StateIdx: return True
        return False

    def match_skeleton(self, TransitionMap, TargetIdx, TriggerCharToTarget):
        """A single character transition 

                        TriggerCharToTarget --> TargetIdx

           has been detected. The question is, if the remaining transitions
           of the state match the skeleton of the current path. There might
           be a wildcard, that is the character that is overlayed by the
           first single character transition. As soon as a transition map
           is differs only by this single character, the wildcard is 
           plugged into the position.
        """
        ## ?? The element of a path cannot be triggered by the skeleton! ??
        ## ?? if self.skeleton.has_key(TargetIdx): return False          ?? 
        ## ?? Why? (fschaef9: 10y04m11d)

        if self.wildcard != None: wildcard_plug = None # unused
        else:                     wildcard_plug = -1   # used before

        transition_map_key_set = set(TransitionMap.keys())
        # (1) Target States In TransitionMap and Not in Skeleton
        #
        #     All target states of TransitionMap must be in Skeleton,
        #     except:
        #
        #      (1.1) The single char transition target TargetIdx.
        #      (1.2) Maybe, one that is reached by a single char
        #            transition of wildcard.
        delta_set  = transition_map_key_set - self.skeleton_key_set
        delta_size = len(delta_set)
        if delta_size > 2: return False

        for target_idx in delta_set:
            if   target_idx == TargetIdx:    continue # (1.1)
            elif wildcard_plug != None:                                      return False
            elif not TransitionMap[target_idx].contains_only(self.wildcard): return False
            wildcard_plug = target_idx                # (1.2)

        # (2) Target States In Skeleton and Not in TransitionMap
        #
        #     All target states of Skeleton must be in TransitionMap,
        #     except:
        #
        #      (2.1) Transition to the target index in skeleton
        #            is covered by current single transition.
        delta_set = self.skeleton_key_set - transition_map_key_set
        delta_size = len(delta_set)
        if delta_size > 1: return False
        if delta_size == 1:
            for target_idx in delta_set:
                if not self.skeleton[target_idx].contains_only(TriggerCharToTarget): return False
            # (2.1) OK, single char covers the transition in skeleton.

        # (3) Target States in both, Skeleton and Transition Map
        #
        #     All correspondent trigger sets must be equal, except:
        #
        #      (3.1) single char transition covers the hole, i.e.
        #            trigger set in transition map + single char ==
        #            trigger set in skeleton. (check this first,
        #            don't waste wildcard).
        #      (3.2) trigger set in skeleton + wildcard == trigger set 
        #            in transition map.
        #       
        common_set = self.skeleton_key_set & transition_map_key_set
        ##print "##common", common_set
        for target_idx in common_set:
            sk_trigger_set = self.skeleton[target_idx]
            tm_trigger_set = TransitionMap[target_idx]

            if sk_trigger_set.is_equal(tm_trigger_set): continue

            # (3.1) Maybe the current single transition covers the 'hole'.
            #       (check this first, we do not want to waste the wilcard)
            if can_plug_to_equal(tm_trigger_set, TriggerCharToTarget, sk_trigger_set):
                continue

            elif wildcard_plug == None:
                # (3.2) Can difference between trigger sets be plugged by the wildcard?
                if can_plug_to_equal(sk_trigger_set, self.wildcard, tm_trigger_set): 
                    wildcard_plug = target_idx
                    continue
                # (3.3) A set extended by wilcard may have only a 'hole' of the
                #       size of the single transition char.
                if can_plug_to_equal(tm_trigger_set, 
                                     TriggerCharToTarget,
                                     sk_trigger_set.union(NumberSet(self.wildcard))): 
                    wildcard_plug = target_idx
                    continue

            # Trigger sets differ and no wildcard or single transition
            # can 'explain' that => skeleton does not fit.
            return False

        # Finally, if there is a plugging to be performed, then do it.
        if wildcard_plug != -1 and wildcard_plug != None:
            if self.skeleton.has_key(wildcard_plug):
                self.skeleton[wildcard_plug].unite_with(NumberSet(self.wildcard))
            else:
                self.skeleton[wildcard_plug] = NumberSet(self.wildcard)
            self.skeleton_key_set.add(wildcard_plug)
            self.wildcard = None # There is no more wildcard now

        return True

    def __repr__(self):
        skeleton_txt = ""
        for target_idx, trigger_set in self.skeleton.items():
            skeleton_txt += "(%i) by " % target_idx
            skeleton_txt += trigger_set.get_utf8_string()
            skeleton_txt += "; "

        sequence_txt = ""
        for state_idx, char in self.sequence:
            sequence_txt += "(%i)--'%s'-->" % (state_idx, chr(char))
        sequence_txt += "[%i]" % self.end_state_index

        return "".join(["start    = %i;\n" % self.start_state_index,
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = %s\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.wildcard != None)])

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

__find_begin_touched_state_idx_list = {}
def __find_begin(sm, StateIdx):
    global __find_begin_touched_state_idx_list

    State       = sm.states[StateIdx]
    result_list = []

    transition_map = State.transitions().get_map()
    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():
        if __find_begin_touched_state_idx_list.has_key(target_idx): continue

        __find_begin_touched_state_idx_list[target_idx] = True
        result_list.extend(__find_begin(sm, target_idx))

        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # A new path begins, find the 'skeleton'.
        # The 'skeleton' is the transition map without the single transition
        skeleton = copy(transition_map) # Shallow copy, i.e. copy references
        del skeleton[target_idx]        # Delete reference to 'target_idx->trigger_set'

        path = SingleCharacterPath(StateIdx, skeleton, path_char)
            
        result_list.extend(__find_continuation(sm, target_idx, path))

    return result_list

INDENT = 0
def __find_continuation(sm, StateIdx, the_path):
    global INDENT
    INDENT += 4
    ##print (" " * INDENT) + "##StateIdx=%i" % StateIdx 
    ##print (" " * (INDENT)) + repr(the_path).replace("\n", "\n" + " " * (INDENT))

    State       = sm.states[StateIdx]
    result_list = []

    transition_map = State.transitions().get_map()


    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():

        # Find a 'single character transition'
        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # Does the rest of the transitions fit the 'skeleton'?
        path = deepcopy(the_path)
        ##print (" " * INDENT) + "##try match %i, %s" % (target_idx, trigger_set.get_utf8_string()) 
        if not path.match_skeleton(transition_map, target_idx, path_char): continue 
        ##print (" " * INDENT) + "##matched"

        ## print "##", target_idx, path

        # A recursion cannot be covered by a 'path state'. We cannot 
        # extract a state that contains recursions and replace it with
        # a skeleton plus a 'character string position'. Omit this path!
        if path.contains(target_idx): continue # Recursion ahead! Don't go!

        # Find a continuation of the path
        single_char_transition_found_f = True
        path.sequence.append((StateIdx, path_char))
        result_list.extend(__find_continuation(sm, target_idx, path))

    if not single_char_transition_found_f and len(the_path.sequence) != 1:
        the_path.end_state_index = StateIdx
        result_list.append(the_path)

    ##print (" " * INDENT) + "##result_list" 
    ##print (" " * (INDENT + 4)) + repr(result_list).replace("\n", "\n" + " " * (INDENT + 4))
    INDENT -= 4
    return result_list

def can_plug_to_equal(Set0, Char, Set1):
    """Determine whether the character 'Char' can be plugged
       to Set0 to make both sets equal.

       (1) If Set0 contains elements that are not in Set1, then 
           this is impossible.
       (2) If Set1 contains elements that are not in Set0, then
           it is possible, if the difference is a single character.

       NOTE:
                Set subtraction: A - B != empty, 
                                 A contains elements that are not in B.
    """
    # If interval number differs more than one, then no single
    # character can do the job.
    if Set1.interval_number() - Set0.interval_number() > 1: return False
    # It is possible that Set0 has more intervals than Set1, e.g.
    # Set0 = {[1,2], [4]}, and Set1={[1,4]}. In this example, '3'
    # can plug Set0 to be equal to Set1. A difference > 1 is impossible,
    # because, one character can plug at max. one 'hole'.
    if Set0.interval_number() - Set1.interval_number() > 1: return False

    # Does Set0 contain elements that are not in Set1?
    if not Set0.difference(Set1).is_empty(): return False

    delta = Set1.difference(Set0)
    # If there is no difference to make up for, then no plugging possible.
    if delta.is_empty(): return False

    return delta.contains_only(Char)

    


        









