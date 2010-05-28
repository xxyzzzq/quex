# (C) 2010 Frank-Rene Schaefer
"""
   Path Compression ___________________________________________________________

   For path compression it is necessary to identify traits of single character
   transitions while the remaining transitions of the involved states are the
   same (or covered by what is trigger by the current path element). This
   type of compression is useful in languages that contain keywords. Consider
   for example a state machine, containing the key-word 'for':


   ( 0 )-- 'f' --->( 1 )-- 'o' --->( 2 )-- 'r' -------->(( 3 ))--( [a-z] )-.
      \               \               \                                    |
       \               \               \                                   |
        `--([a-eg-z])---`--([a-np-z])---`--([a-qs-z])-->(( 4 ))<-----------'

   The states 0, 1, and 2 can be implemented by a 'path walker', that is 
   a common transition map, that is preceeded by a single character check.
   The single character check changes along a fixed path: the sequence of
   characters 'f', 'o', 'r'. This is shown in the following pseudo-code:

     PATH_1:
        /* Single Character Check */
        if   input == p: ++p; goto PATH_1;
        elif *p == 0:         goto STATE_3;

        /* Common Transition Map */
        if   x < 'a': drop out
        elif x > 'z': drop out
        else:         goto STATE_4

   It is assumed that the array with the character sequence ends with zero.
   This way it can be detected when to trigger to the correspondent end state.

   For a state that is part of a 'path', a 'goto state' is transformed into a
   'set path_iterator' plus a 'goto path'. The path iterator determines the 
   current character to be checked against. The 'path' determines the reminder
   of the transition map. It holds

            path state <--> (path index, path iterator position)

   Assume that in the above example the path is the 'PATH_1' and the character
   sequence is given by an array:

            path_1_sequence = { 'f', 'o', 'r', 0x0 };
            
    then the three states 0, 1, 2 are identified as follows

            STATE_0  <--> (PATH_1, path_1_sequence)
            STATE_1  <--> (PATH_1, path_1_sequence + 1)
            STATE_2  <--> (PATH_1, path_1_sequence + 2)

   Result ______________________________________________________________________


   The result of analyzis of path compression is:
    
                       A dictionary mapping  
                  
            start state indices <--> 'CharacterPath' objects. 

   A character path represents a single character sequence that was found in
   the statemachine, together with the 'skeleton' which is the remaining
   trigger map. Concrete:

         .sequence()        --> The character sequence of the path
         .end_state_index() --> State index of the state that is
                                entered after the path is terminated.
         .skeleton()        --> Remaining trigger map, that must be
                                applied after the single char check.

   There might be multiple pathes starting from the same start state. And,
   start states might possible appear in other paths.

   Filtering Pathes ___________________________________________________________

   First, paths that are subsets of other paths might be filtered out without
   loss.

"""
from quex.core_engine.interval_handling import NumberSet, Interval
from copy import deepcopy, copy

class CharacterPath:
    def __init__(self, StartStateIdx, Skeleton, StartCharacter):
        self.__start_state_index = StartStateIdx
        self.__end_state_index   = -1
        self.__sequence          = [ (StartStateIdx, StartCharacter) ]

        self.__skeleton          = Skeleton
        self.__skeleton_key_set  = set(Skeleton.keys())
        # Character that may trigger to any state. This character is
        # adapted when the first character of the path is different
        # from the wildcard character. Then it must trigger to whatever
        # the correspondent state triggers.
        self.__wildcard          = StartCharacter

    def sequence(self):
        return self.__sequence

    def skeleton(self):
        return self.__skeleton

    def end_state_index(self):
        return self.__end_state_index

    def set_end_state_index(self, Value):
        self.__end_state_index = Value

    def append(self, StateIdx, Char):
        self.__sequence.append((StateIdx, Char))

    def contains(self, StateIdx):
        for state_idx, char in self.__sequence:
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
        ## ?? if self.__skeleton.has_key(TargetIdx): return False          ?? 
        ## ?? Why? (fschaef9: 10y04m11d)

        if self.__wildcard != None: wildcard_plug = None # unused
        else:                       wildcard_plug = -1   # used before

        transition_map_key_set = set(TransitionMap.keys())
        # (1) Target States In TransitionMap and Not in Skeleton
        #
        #     All target states of TransitionMap must be in Skeleton,
        #     except:
        #
        #      (1.1) The single char transition target TargetIdx.
        #      (1.2) Maybe, one that is reached by a single char
        #            transition of wildcard.
        delta_set  = transition_map_key_set - self.__skeleton_key_set
        delta_size = len(delta_set)
        if delta_size > 2: return False

        for target_idx in delta_set:
            if   target_idx == TargetIdx:    continue # (1.1)
            elif wildcard_plug != None:                                        return False
            elif not TransitionMap[target_idx].contains_only(self.__wildcard): return False
            wildcard_plug = target_idx                # (1.2)

        # (2) Target States In Skeleton and Not in TransitionMap
        #
        #     All target states of Skeleton must be in TransitionMap,
        #     except:
        #
        #      (2.1) Transition to the target index in skeleton
        #            is covered by current single transition.
        delta_set  = self.__skeleton_key_set - transition_map_key_set
        delta_size = len(delta_set)
        if delta_size > 1: return False
        if delta_size == 1:
            for target_idx in delta_set:
                if not self.__skeleton[target_idx].contains_only(TriggerCharToTarget): return False
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
        common_set = self.__skeleton_key_set & transition_map_key_set
        ##print "##common", common_set
        for target_idx in common_set:
            sk_trigger_set = self.__skeleton[target_idx]
            tm_trigger_set = TransitionMap[target_idx]

            if sk_trigger_set.is_equal(tm_trigger_set): continue

            # (3.1) Maybe the current single transition covers the 'hole'.
            #       (check this first, we do not want to waste the wilcard)
            if can_plug_to_equal(tm_trigger_set, TriggerCharToTarget, sk_trigger_set):
                continue

            elif wildcard_plug == None:
                # (3.2) Can difference between trigger sets be plugged by the wildcard?
                if can_plug_to_equal(sk_trigger_set, self.__wildcard, tm_trigger_set): 
                    wildcard_plug = target_idx
                    continue
                # (3.3) A set extended by wilcard may have only a 'hole' of the
                #       size of the single transition char.
                if can_plug_to_equal(tm_trigger_set, 
                                     TriggerCharToTarget,
                                     sk_trigger_set.union(NumberSet(self.__wildcard))): 
                    wildcard_plug = target_idx
                    continue

            # Trigger sets differ and no wildcard or single transition can
            # 'explain' that => skeleton does not fit.
            return False

        # Finally, if there is a plugging to be performed, then do it.
        if wildcard_plug != -1 and wildcard_plug != None:
            if self.__skeleton.has_key(wildcard_plug):
                self.__skeleton[wildcard_plug].unite_with(NumberSet(self.__wildcard))
            else:
                self.__skeleton[wildcard_plug] = NumberSet(self.__wildcard)
            self.__skeleton_key_set.add(wildcard_plug)
            self.__wildcard = None # There is no more wildcard now

        return True

    def __repr__(self):
        skeleton_txt = ""
        for target_idx, trigger_set in self.__skeleton.items():
            skeleton_txt += "(%i) by " % target_idx
            skeleton_txt += trigger_set.get_utf8_string()
            skeleton_txt += "; "

        sequence_txt = ""
        for state_idx, char in self.__sequence:
            sequence_txt += "(%i)--'%s'-->" % (state_idx, chr(char))
        sequence_txt += "[%i]" % self.__end_state_index

        return "".join(["start    = %i;\n" % self.__start_state_index,
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = %s\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.__wildcard != None)])

    def __len__(self):
        return len(self.__sequence)


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
    """Searches for the beginning of a path, i.e. a single character 
       transition to a subsequent state. If such a transition is found,
       a 'skeleton' is computed in the 'CharacterPath' object. With this
       object a continuation of the path is searched starting from the
       transitions target state. 
       
       In any case, it is tried to find a path begin in the target state.
       Even if the target state is part of a path, it might have non-path
       targets that lead to pathes. Thus,

       IT CANNOT BE AVOIDED THAT THE RESULT CONTAINS PATHES WHICH ARE 
                           SUB-PATHES OF OTHERS.
    """
    global __find_begin_touched_state_idx_list

    State       = sm.states[StateIdx]
    result_list = []

    transition_map = State.transitions().get_map()
    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():
        if __find_begin_touched_state_idx_list.has_key(target_idx): continue
        __find_begin_touched_state_idx_list[target_idx] = True

        # IN ANY CASE: Check for paths in the subsequent state
        result_list.extend(__find_begin(sm, target_idx))

        # Only consider single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # A new path begins, find the 'skeleton'.
        # The 'skeleton' is the transition map without the single transition
        skeleton = copy(transition_map) # Shallow copy, i.e. copy references
        del skeleton[target_idx]        # Delete reference to 'target_idx->trigger_set'

        path = CharacterPath(StateIdx, skeleton, path_char)
            
        result_list.extend(__find_continuation(sm, target_idx, path))

    return result_list

INDENT = 0
def __find_continuation(sm, StateIdx, the_path):
    """A basic skeleton of the path and the remaining trigger map is given. Now,
       try to find a subsequent path step.
    """
    global INDENT
    INDENT += 4
    ##print (" " * INDENT) + "##StateIdx=%i" % StateIdx 
    ##print (" " * (INDENT)) + repr(the_path).replace("\n", "\n" + " " * (INDENT))

    State       = sm.states[StateIdx]
    result_list = []

    transition_map = State.transitions().get_map()


    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():

        # Only consider single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char == None: continue

        # A recursion cannot be covered by a 'path state'. We cannot extract a
        # state that contains recursions and replace it with a skeleton plus a
        # 'character string position'. Omit this path!
        if the_path.contains(target_idx): continue # Recursion ahead! Don't go!

        # Does the rest of the transitions fit the 'skeleton'?
        # 'match_skeleton()' changes content, so make a backup of the path
        path = deepcopy(the_path)
        ##print (" " * INDENT) + "##try match %i, %s" % (target_idx, trigger_set.get_utf8_string()) 
        if not path.match_skeleton(transition_map, target_idx, path_char): continue 
        ##print (" " * INDENT) + "##matched"

        ## print "##", target_idx, path

        # Find a continuation of the path
        single_char_transition_found_f = True
        path.append(StateIdx, path_char)
        result_list.extend(__find_continuation(sm, target_idx, path))

    if not single_char_transition_found_f and len(the_path) != 1:
        the_path.set_end_state_index(StateIdx)
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

    


        









