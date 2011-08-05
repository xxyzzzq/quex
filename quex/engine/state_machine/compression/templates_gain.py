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
           ... recurse:
               switch( template_key ) {
               case 1: goto ENTRY0_intern;
               case 2: goto ENTRY1_intern;
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
    
This file contains functions that compute the 'gain' (= - 'cost') 
when two states (one or both of them may be template states) are
combined. There is no reason to give a template state a 'weight' 
corresponding to the number of state it combines. At this point
in time, both considered states are already 'states' and we only
want to find out what is getting better (if actually) in case
both are combined. 
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

def sort_this(X, Y, key):
    if key(X) >= key(Y): return X, Y
    else:                return Y, X
        
def entry_gain(StateA, StateB):
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
    bigger, smaller = sort_this(StateA.entry, StateB.entry, lambda len(X.scheme))

    result = 0
    for entry in smaller.scheme:
        if bigger.contains(entry): result -= __cost_of_entry(entry)
    return result


def drop_out_gain(StateA, StateB):
    """If the two states have the same drop_out handling, then the one entry 
       can be spared. Otherwise, the combination gain is the actually negative,
       because for each drop-out a switch case must be implemented based on
       the template key.
    """
    def __cost_of_switch_case_construct(DropOutSchemeA, DropOutSchemeB):

    if isinstance(StateA, AnalyzerState):
        if isinstance(StateB, AnalyzerState):
            if StateA.drop_out.is_equal(StateB.entry):        return - __cost_of_drop_out(StateA.entry) # gain = - cost
            else:                                             return __cost_of_switch_case_construct([StateA.drop_out], [StateB.drop_out])
        else:
            # StateB is a TemplateState, it may contain the scheme of StateA's entry
            if StateB.drop_out.scheme.contains(StateA.entry): return - __cost_of_drop_out(StateA.entry) # gain = - cost
            else:                                             return CombinationGain(__cost_of_switch_case_construct([StateA.drop_out], StateB.drop_out.scheme)
    else:
        if isinstance(StateB, AnalyzerState):
            # StateA is a TemplateState, it may contain the scheme of StateB's entry
            if StateA.drop_out.scheme.contains(StateB.entry): return - __cost_of_drop_out(StateB.entry) # gain = - cost
            else:                                             return __cost_of_switch_case_construct(StateA.drop_out.scheme, [StateB.drop_out])

    # StateA and StateB are template states.
    bigger, smaller = sort_this(StateA.drop_out, StateB.drop_out, lambda len(X.scheme))

    result = __cost_of_switch_case_construct(DropOutSchemeA, DropOutSchemeB)
    # If a drop_out handling is in both schemes, than we actually gain something by 
    # combining them into one. If the handling in both schemes is different, then
    # we do not loose anything, because if the states were treated separately we
    # would have to pay the price anyway.
    for drop_out in smaller.scheme:
        if bigger.contains(entry): result -= __cost_of_drop_out(entry)
    return result
