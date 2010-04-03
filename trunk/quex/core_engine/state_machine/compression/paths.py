

"""Checks whether the transitions of state 0 and state 1
   can be part of a path, e.g.

      (0)-----( 'a' )---->(1)-----( 'b' )----->(2)

   can be setup as path, i.e 'ab'.
"""
# map0 = State0.transitions().get_map()
# map1 = State1.transitions().get_map()

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
    state_A_idx = SM.init_state_index
    state_A     = SM.states[state_idx]
    return

class SingleCharacterPath:
    def __init__(self, StartStateIdx, Skeleton, StartPath):
        self.start_state_index = StartStateIdx
        self.skeleton          = Skeleton

        self.character_sequence = StartPath

    def __repr__(self):
        "".join(["start    = %i;\n"    % self.start_state_index,
                 "skeleton = %s;\n" % self.skeleton,
                 "path     = %s;\n" % repr(map(chr, self.character_sequence)]))

def __find(StateIdx, StateA, Skeleton, the_path):
    exclude_target_idx = -1L

    result_list = []
    if Skeleton != None:
        target_idx, character = get_step_on_path(Skeleton, StateA)
        if target_idx != None: 
            the_path.character_sequence.append(character)
            result_list.extend(__find(sm.states[target_idx], Skeleton, the_path))
            # When analyzing the remaining target states, this target
            # state must be excluded, since a 'the' path has been analyzed.
            exclude_target_idx = target_idx
        else:
            # The end of a path has been detected
            result_list = [the_path]
        
    for target_idx in StateA.transitions().get_target_state_index_list():
        if target_idx == exclude_target_idx:       continue
        if target_idx in __done_target_index_list: continue

        state_B = sm.states[target_idx]

        info = find_skeleton(StateA.transitions(), state_B.transitions())

        # No skeleton --> recurse without starting skeleton
        if info == None: 
            result_list.extend(__find(state_B, None, []))

        step_1            = info[1][1] # 1st character on path in StateA
        step_2            = info[2][1] # 2nd character on path in target state
        step_2_target_idx = info[2][0] # target triggered by second character
        path = SingleCharacterPath(StateIdx, Skeleton, info[0], [step_0, step_1])
        
        result_list.extend(__find(sm.states[step_2_target_idx], Skeleton, path))

        # When analyzing the remaining target states, this target
        # state must be excluded, since a path has been analyzed.
        exclude_target_idx = target_idx

    __done_target_index_list.append(StateIdx)
    return result_list

def find_skeleton(MapA, MapB):
    """The goal is to replace the transitions of A and B by a single transition
       map where the initial check is on a single character. For Example

                  A                                 B
                [a-t]  ---->   State0             [a-d]  ---->   State0
                [u]    ---->   State1             [e]    ---->   State4
                [v-z]  ---->   State0             [f-z]  ---->   State0
                [0-4]  ---->   State2             [0-4]  ---->   State2
                [5-9]  ---->   State3             [5-9]  ---->   State3

       The two states can be replaced by one 'parameterized state' P:

                  P
            (1) input == X      ---->   SX
            (2) input in [a-z]  ---->   State0            
                         [0-4]  ---->   State2            
                         [5-9]  ---->   State3            

       Where:  (X = 'u', SX = State1) for P to represent state A.
               (X = 'e', SX = State4) for P to represent state B.

    RETURNS:  None --> there is no skeleton that could fit
              (dict, A_plug, B_plug) --> (possibly empty) skeleton
                                         A_plug = (target_idx, character) of
                                                  single transition for 'A'.
                                         B_plug = same for 'B'.
    """
    A_plug, B_plug = extract_admissible_single_transitions(MapA, MapB)

    if A_plug == None or B_plug == None:
        return None

    skeleton        = {}
    difference_list = []
    A_plug_used_f = False
    B_plug_used_f = False
    for target_idx, A_trigger_set in MapA.items():
        # The plugs are excempted
        if target_idx == A_plug[0] or target_idx == B_plug[0]: continue

        # B must have target index!
        B_trigger_set = MapB.get(target_idx)
        if B_trigger_set == None: return None
        
        if A_trigger_set.is_equal(B_trigger_set):
            skeleton[target_idx] = A_trigger_set

        elif not A_plug_used_f and can_plug_to_equal(A_trigger_set, B_trigger_set, A_plug[1]):
            A_plug_used_f = True # mark the plug as used (for safety)
            skeleton[target_idx] = B_trigger_set

        elif not B_plug_used_f and can_plug_to_equal(B_trigger_set, A_trigger_set, B_plug[1]):
            B_plug_used_f = True # mark the plug as used (for safety)
            skeleton[target_idx] = A_trigger_set

        else:
            return None

    return (skeleton, A_plug, B_plug)

def get_step_on_path(SkeletonKeySet, Skeleton, Map):
    """Given a specific transition skeleton, try to find a single
       character transition that can be added to the skeleton in
       order to represent the Map.

       There can be only one differing target state in the Map,
       and this target state must be triggered on a single character.

       RETURNS: TargetStateIdx, TriggeringCharacter that describes
                           the difference between the 'Map' and the 
                           skeleton.
                None, None is returned if there is no such simple
                           difference.
    """
    map_key_set = Map.keys()
    if len(map_key_set) != len(SkeletonKeySet) + 1: return None, None

    # Find the key that differs:
    for target_idx in map_key_set:
        if target_idx not in SkeletonKeySet: break
    else:
        assert False, \
               "Since keys are unique and len(map_key_set) > len(SkeletonKeySet)\n" + \
               "there must be a key in map_key_set that is not in SkeletonKeySet."

    trigger_set = Map[target_idx]
    candidate   = trigger_set.get_the_only_element()
    if candidate == None: return None, None
    else:                 return target_idx, candidate

def find_single_transitions(Map):
    """Find transitions that trigger on a single character to 
       a subsequent state.
    """
    db = {}
    for target_idx, trigger_set in Map.items():
        candidate = trigger_set.get_the_only_element()
        if candidate == None: continue
        db[target_idx] = candidate
    return db

def extract_admissible_single_transitions(MapA, MapB):
    """-- The only differing target states allowed are those
          of the single transitions which are later 'plugged'.
       -- The single transitions must trigger to different
          states, otherwise no 'path' (sequence of chars)
          is possible.
       Thus: There is only one single transition per state
             that is admissible.
             The single transitions from both states must be 
             different.
    """
    found_f = False
    A_plug  = None
    for target in MapA.keys():
        if MapB.has_key(target): continue
        # 'B' has no correspondent target index
        if A_plug != None:    return None, None
        candidate = MapA[target].get_the_only_element()
        if candidate == None: return None, None
        A_plug = (target, candidate)

    B_plug  = None
    for target in MapB.keys():
        if MapA.has_key(target): continue
        # 'A' has no correspondent target index
        if B_plug != None:    return None, None
        candidate = MapB[target].get_the_only_element()
        if candidate == None: return None, None
        # B_plug's target cannot be equal to A_plug's target, 
        # because A has no correspondent target index.
        B_plug = (target, candidate)

    return A_plug, B_plug

def can_plug_to_equal(Set0, Set1, PlugChar):
    """Determine wether Set0 + Plug == Set1."""
    # If Set1 does not at all contain the plug character,
    # then the character cannot 'plug' Set0 to be equal to Set1.
    if not Set1.contains(PlugChar): return False

    # First compare interval numbers to quickly exclude
    # impossible cases.
    in_0 = Set0.interval_number()
    in_1 = Set1.interval_number()
    if in_0 > in_1 + 1: return False
    if in_1 - in_0 > 1: return False

    # If the difference Set1 - Set0 == PlugChar than the
    # character can plug Set0 so that it fits Set0.
    delta = Set1.difference(Set0)
    if delta.interval_number() != 1: return False
    x = delta.get_intervals(PromiseToTreatWellF=True)
    if x[0].end - x[0].begin != 1:   return False

    return x[0].begin == PlugChar
        









