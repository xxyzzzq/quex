"""
If two states with non-uniform frames (entries and drop-outs) are 
to be combined, then this requires extra effort. Consider the following
case:

        ENTRY0:                       ENTRY1:
           pos[12] = input_p             pos[0] = input_p
           pos[5]  = input_p          
                                      
        MAP:                          MAP:
           ... recurse -> ENTRY0         ... recurse --> ENTRY1
           ... reload(ENTRY0, DROP0)     ... reload(ENTRY1, DROP1)
                                      
        DROP0:                        DROP1:
           goto TERMINAL_15;             goto TERMINAL_FAILURE;

Both states differ in the way they are entered, and the way that they
are dropped out. Consequently, the reload procedure differs, too. The
entries are still be routed by the label, RELOAD and DROP-OUT procedures
are identified by the template key (given at entry). A combination may
look like:

        ENTRY0:
           template_key = 1
        ENTRY0_intern:
           pos[12] = input_p
           pos[5]  = input_p
           acceptance_id = 16;
           goto MAP;

        ENTRY1:
           template_key = 2
        ENTRY1_intern:
           pos[0] = input_p
           goto MAP;

        MAP:
           input_p++;
           ... recurse:
               -- simply: if all recursive states do not change position storage.
               goto MAP; 
               -- or:
               switch( template_key ) {
               case 1: RELOAD(ENTRY0_intern, DROP);
               case 2: RELOAD(ENTRY1_intern, DROP);
               }
           ... reload:
               switch( template_key ) {
               case 1: RELOAD(ENTRY0_intern, DROP);
               case 2: RELOAD(ENTRY1_intern, DROP);
               }

        DROP:
           switch( template_key ) {
           case 1: goto TERMINAL_15;
           case 2: goto FAILURE;
           }
    
This file contains functions that compute the 'gain' (= - 'cost') when two
states (one or both of them may be template states) are combined. There is no
reason to give a template state a 'weight' corresponding to the number of state
it combines. At this point in time, both considered states are already 'states'
and we only want to find out what is getting better (if actually) in case both
are combined.  
"""

class CombinationGain:
    """We start of with a multi-attribute gain, that is then 
       translated into a scalar value through function 'total()'.
    """
    def __init__(self, AdditionN=0, AssignmentN=0, CaseN=0):
        self.__addition_n   = AdditionN
        self.__assignment_n = AssignmentN
        self.__case_n       = CaseN

    def add(self, Other):
        assert isinstance(Other, CombinationGain)
        self.__addition_n   += Other.__addition_n
        self.__assignment_n += Other.__assignment_n
        self.__case_n       += Other.__case_n

    def total(self):
        """The following is only a heuristic with no claim to be perfect.
           It is able to distinguish between the good and the bad cases.
           But, it may fail to distinguish properly between cases that 
           are close to each other in quality. So, no too much to worry about.
        """
        result = self.__addition_n * 2 + self.__assignment_n
        if self.__case_n == 0: return result
        # Assume 2 core instructions for the setup of the switch case ...
        return result + 2 + self.__case_n

def do(StateA, StateB):
    entry_gain    = get_entry_gain(StateA, StateB).total()
    drop_out_gain = get_drop_out_gain(StateA, StateB).total()

    border_n, same_target_n = get_transition_map_metric(StateA, StateB)
    assert border_n >= same_target_n

    avrg_interval_n   = int((len(StateA.transition_map) + len(StateB.transition_map)) / 2.0)
    border_increase_n = border_n - avrg_interval_n

    if border_n == 0: same_target_ratio = 1.0
    else:             same_target_ratio = same_target_n / float(border_n)
    # From assert above, it follows that same_target_ratio >= 0  and <= 1

    return entry_gain + drop_out_gain - border_increase_n * 4 * (1.0 - same_target_ratio)

def get_entry_gain(StateA, StateB):
    """If the two states have the same entries, then the one entry 
       can be spared. Then, the 'entry gain' is the what can be spared the
       the function entry. Otherwise, the combination gain is simply zero.

       The same is true, if a template state already contains the entry 
       scheme of the other.
    """

    if isinstance(StateA, AnalyzerState):
        if isinstance(StateB, AnalyzerState):
            if StateA.entry.is_equal(StateB.entry):        return - __cost_of_entry(StateA.entry) # gain = - cost
            else:                                          return CombinationGain(0, 0, 0)
        else:
            # StateB is a TemplateState, it may contain the scheme of StateA's entry
            if StateB.entry.scheme.contains(StateA.entry): return - __cost_of_entry(StateA.entry) # gain = - cost
            else:                                          return CombinationGain(0, 0, 0)
    else:
        if isinstance(StateB, AnalyzerState):
            # StateA is a TemplateState, it may contain the scheme of StateB's entry
            if StateA.entry.scheme.contains(StateB.entry): return - __cost_of_entry(StateB.entry) # gain = - cost
            else:                                          return CombinationGain(0, 0, 0)

    # StateA and StateB are template states.
    bigger, smaller = sorted([StateA.entry, StateB.entry], key=lambda len(X.scheme))

    result = 0
    for entry in smaller.scheme:
        if bigger.contains(entry): result -= __cost_of_entry(entry)
    return result

def get_drop_out_gain(StateA, StateB):
    """If the two states have the same drop_out handling, then the one entry 
       can be spared. Otherwise, the combination gain is the actually negative,
       because for each drop-out a switch case must be implemented based on
       the template key.
    """
    def __cost_of_switch_case_construct(DropOutSchemeA, DropOutSchemeB):

    if isinstance(StateA, AnalyzerState):
        if isinstance(StateB, AnalyzerState):
            if StateA.drop_out.is_equal(StateB.drop_out):        return - __cost_of_drop_out(StateA.entry) # gain = - cost
            else:                                                return __cost_of_switch_case_construct([StateA.drop_out], [StateB.drop_out])
        else:
            # StateB is a TemplateState, it may contain the scheme of StateA's entry
            if StateB.drop_out.scheme.contains(StateA.drop_out): return - __cost_of_drop_out(StateA.entry) # gain = - cost
            else:                                                return CombinationGain(__cost_of_switch_case_construct([StateA.drop_out], StateB.drop_out.scheme)
    else:
        if isinstance(StateB, AnalyzerState):
            # StateA is a TemplateState, it may contain the scheme of StateB's entry
            if StateA.drop_out.scheme.contains(StateB.entry):    return - __cost_of_drop_out(StateB.entry) # gain = - cost
            else:                                                return __cost_of_switch_case_construct(StateA.drop_out.scheme, [StateB.drop_out])

    # StateA and StateB are template states.
    bigger, smaller = sorted([StateA.drop_out, StateB.drop_out], key=lambda len(X.scheme))

    result = __cost_of_switch_case_construct(DropOutSchemeA, DropOutSchemeB)
    # If a drop_out handling is in both schemes, than we actually gain something by 
    # combining them into one. If the handling in both schemes is different, then
    # we do not loose anything, because if the states were treated separately we
    # would have to pay the price anyway.
    for drop_out in smaller.scheme:
        if bigger.contains(entry): result -= __cost_of_drop_out(entry)
    return result

def get_transition_map_metric(StateA, StateB):
    """Assume that interval list 0 and 1 are sorted.
       
       RETURNS: 
          (1) Number of new borders if both maps are combined. For example:
	
		             |----------------|
		                  |---------------|
		    
		      Requires to setup three intervals in order to cover all cases 
                    propperly: 
		    
		             |----|-----------|---|
		    

          (2) Number of transitions that trigger to the same target state on 
              the same interval in both maps.

       If for an interval the target state is the state itself (recursion), then 
       this counted as a 'same target' since there is no change needed and the 
       template triggers to itself. The combined template will trigger to itself.

    """
    TransitionMapA = StateA.transition_map
    TransitionMapB = StateB.transition_map
    
    def same_target(TA, TB):
        """TA, TB = Target States. Let T be one of TA and TB. Then:
           T == integer if the trigger map belongs to a 'normal' state or
                        to a template combination where all related states
                        trigger to the same target.

             == list    if the trigger map belongs to a template combination.
                        T[i] = target of state with state_index <-> i.
        """
        if isinstance(TA, list) or isinstance(TB, list): return False
        if TA == StateA.index: TA = TargetStateIndices.RECURSIVE
        if TB == StateB.index: TB = TargetStateIndices.RECURSIVE
        return TA == TB
        
    i  = 0 # iterator over interval list 0
    k  = 0 # iterator over interval list 1
    Li = len(TransitionMapA)
    Lk = len(TransitionMapB)
    # Intervals in trigger map are always adjacent, so the '.begin'
    # member is not required.
    border_n      = 0
    same_target_n = 0
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TransitionMapA[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TransitionMapB[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        if same_target(i_target, k_target): same_target_n += 1

        # Step to the next *lowest* border, i.e. increment the 
        # interval line index with the lowest '.end'. For example:
        # 
        #         0   1 2  3 4 5  6   7
        #     i   |     |      |  |   |
        #     k   |   |    | |        |
        #         :   : :  : : :  :   :   (6 intervals, 6 borders)
        #
        #                         i_end:     k_end:
        # Does:  (1) ++i, ++k -->    2            1
        #        (2) ++k      -->    2            3
        #        (3) ++i      -->    5            3
        #        (4) ++k      -->    5            4
        #        (5) ++k      -->    5            6
        #        (6) ++i      -->    6            7
        #        (6) ++i      -->    7            7
        if   i_end == k_end: i += 1; k += 1;
        elif i_end <  k_end: i += 1;
        else:                k += 1;

        border_n += 1

    return border_n, same_target_n

