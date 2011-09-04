from quex.engine.analyzer.core import AnalyzerState, \
                                      Entry, \
                                      EntryBackward, \
                                      EntryBackwardInputPositionDetection
import quex.engine.analyzer.template.combine_maps as combine_maps
from   quex.engine.analyzer.template.common       import get_state_list 
"""
(C) 2010-2011 Frank-Rene Schäfer

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

    def neg(self):
        return CombinationGain(AdditionN   = - self.__addition_n, 
                               AssignmentN = - self.__assignment_n, 
                               CaseN       = - self.__case_n)

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
    def __cost_of_entry(TheEntry):
        if isinstance(TheEntry, Entry):
            if TheEntry.is_uniform(): 
                return CombinationGain(1, 0, 0).neg()
            else:
                Lp = len(TheEntry.positioner)
                La = len(TheEntry.accepter)
                return CombinationGain(AdditionN = Lp, AssignmentN = La, CaseN = Lp + La).neg()

        elif isinstance(TheEntry, EntryBackward):
            return CombinationGain(AssignmentN = len(TheEntry.pre_context_fulfilled_set))

        elif isinstance(TheEntry, EntryBackwardInputPositionDetection):
            if TheEntry.terminated_f: return CombinationGain(CaseN=1).neg()
            else:                     return CombinationGain(0, 0, 0)

    if isinstance(StateA, AnalyzerState):
        if isinstance(StateB, AnalyzerState):
            if StateA.entry.is_equal(StateB.entry):        return __cost_of_entry(StateA.entry).neg() # gain = - cost
            else:                                          return CombinationGain(0, 0, 0)
        else:
            # StateB is a TemplateState, it may contain the scheme of StateA's entry
            if StateB.entry.scheme.contains(StateA.entry): return __cost_of_entry(StateA.entry).neg() # gain = - cost
            else:                                          return CombinationGain(0, 0, 0)
    else:
        if isinstance(StateB, AnalyzerState):
            # StateA is a TemplateState, it may contain the scheme of StateB's entry
            if StateA.entry.scheme.contains(StateB.entry): return __cost_of_entry(StateB.entry).neg() # gain = - cost
            else:                                          return CombinationGain(0, 0, 0)

    # StateA and StateB are template states.
    bigger, smaller = sorted([StateA.entry, StateB.entry], key=lambda x: len(x.scheme))

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
        return CombinationGain(CaseN=len(DropOutSchemeA) + len(DropOutSchemeB)).neg()
    def __cost_of_drop_out(TheDropOut):
        return CombinationGain(AssignmentN=len(TheDropOut.checker), CaseN=len(TheDropOut.router)).neg()

    if isinstance(StateA, AnalyzerState):
        if isinstance(StateB, AnalyzerState):
            if StateA.drop_out.is_equal(StateB.drop_out):        return __cost_of_drop_out(StateA.drop_out).neg() # gain = - cost
            else:                                                return __cost_of_switch_case_construct([StateA.drop_out], [StateB.drop_out])
        else:
            # StateB is a TemplateState, it may contain the scheme of StateA's entry
            if StateB.drop_out.scheme.contains(StateA.drop_out): return __cost_of_drop_out(StateA.drop_out).neg() # gain = - cost
            else:                                                return __cost_of_switch_case_construct([StateA.drop_out], StateB.drop_out.scheme)
    else:
        if isinstance(StateB, AnalyzerState):
            # StateA is a TemplateState, it may contain the scheme of StateB's entry
            if StateA.drop_out.scheme.contains(StateB.entry):    return __cost_of_drop_out(StateB.drop_out).neg() # gain = - cost
            else:                                                return __cost_of_switch_case_construct(StateA.drop_out.scheme, [StateB.drop_out])

    # StateA and StateB are template states.
    bigger, smaller = sorted([StateA.drop_out, StateB.drop_out], key=lambda x: len(x.scheme))

    result = __cost_of_switch_case_construct(DropOutSchemeA, DropOutSchemeB)
    # If a drop_out handling is in both schemes, than we actually gain something by 
    # combining them into one. If the handling in both schemes is different, then
    # we do not loose anything, because if the states were treated separately we
    # would have to pay the price anyway.
    for drop_out in smaller.scheme:
        if bigger.contains(entry): result -= __cost_of_drop_out(entry)
    return result

def get_transition_map_metric(StateA, StateB):
    result, scheme_list = combine_maps.do(StateA, StateB)
    return len(result), len(scheme_list)


