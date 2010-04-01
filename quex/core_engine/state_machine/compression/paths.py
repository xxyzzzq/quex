

"""Checks whether the transitions of state 0 and state 1
   can be part of a path, e.g.

      (0)-----( 'a' )---->(1)-----( 'b' )----->(2)

   can be setup as path, i.e 'ab'.
"""
# map0 = State0.transitions().get_map()
# map1 = State1.transitions().get_map()


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

    """
    A_single_transitions = find_single_transitions(MapA)
    B_single_transitions = find_single_transitions(MapB)

    A_plug, B_plug = extract_admissible_single_transitions(A_single_transitions,
                                                           B_single_transitions)
    if A_plug == None and B_plug == None:
        return None

    skeleton        = {}
    difference_list = []
    for target_idx, A_trigger_set in MapA.items():
        # B must have target index. See conditions above.
        B_trigger_set = MapB[target_idx]

        if A_trigger_set.is_equal(B_trigger_set):
            skeleton[target_idx] = A_trigger_set

        elif can_plug_to_equal(A_trigger_set, B_trigger_set, A_plug):
            A_plug = None # mark the plug as used (for safety)
            skeleton[target_idx] = B_trigger_set

        elif can_plug_to_equal(B_trigger_set, A_trigger_set, B_plug):
            B_plug = None # mark the plug as used (for safety)
            skeleton[target_idx] = A_trigger_set

        else:
            return None

    return skeleton

def find_single_transitions(Map):
    """Find transitions that trigger on a single character to 
       a subsequent state.
    """
    db = {}
    for target_idx, number_set in Map.items():
        candidate = trigger_set.get_the_only_element()
        if candidate == None: continue
        db[target_idx] = candidate
    return db

def extract_admissible_single_transitions(TA, TB):
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
    for target in TA.keys():
        if TB.has_key(target): continue
        # 'B' has no correspondent target index
        if A_plug != None: return None, None
        A_plug = (target, TA[target])

    B_plug  = None
    for target in TB.keys():
        if TA.has_key(target): continue
        # 'A' has no correspondent target index
        if B_plug != None:      return None, None
        if target == A_plug[0]: return None, None
        B_plug = (target, TA[target])

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
        









