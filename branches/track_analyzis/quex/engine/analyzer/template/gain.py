# vim:set encoding=utf8:
from quex.engine.analyzer.core import AnalyzerState, \
                                      Entry, \
                                      EntryBackward, \
                                      EntryBackwardInputPositionDetection
from quex.engine.analyzer.template.common import get_iterable, get_state_list
import quex.engine.analyzer.template.combine_maps as combine_maps
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

def do(CombinedState, StateA, StateB):
    """Compute the 'gain' that results from combining entries, drop_outs
       and transition maps. We start with a multi-attribute gain as 
       given by 'CombinationGain' objects. At the end a scalar value
       is computed by the '.total()' member function.
    """
    entry_gain          = __compute_gain(__entry_cost, CombinedState.entry,    
                                         StateA.entry, StateB.entry)
    drop_out_gain       = __compute_gain(__drop_out_cost, CombinedState.drop_out, 
                                         StateA.drop_out, StateB.drop_out)
    transition_map_gain = __transition_map_gain(CombinedState, StateA, StateB)

    return (entry_gain + drop_out_gain + transition_map_gain).total()

def __compute_gain(__cost, Combined, A, B):
    """Computes the gain of combining two objects 'A' and 'B' into the combined
       object 'Combined'. Objects can be state Entry-s or state DropOut-s. By
       means of the function 'get_iterable' a list of tuples is obtained as 
       below:

             [ ...
               (X, [state_index_list])
               ...
             ]

       The 'X' contains an unique object and 'state_index_list' contains the
       list of indices from the original state machine that require this
       particular object (be it 'DropOut' or 'Entry'). For original states this
       list is, of course, simply [ (Object, [state_index]) ]. But, by this
       adaption it is possible to treat TemplateState-s and AnalyzerState-s in
       a unified manner.
    """
    combined = sum(map(lambda element: __cost(element[0]), get_iterable(Combined)))
    a_cost   = sum(map(lambda element: __cost(element[0]), get_iterable(A)))
    b_cost   = sum(map(lambda element: __cost(element[0]), get_iterable(B)))

    return (a_cost + b_cost) - combined_cost

def __entry_cost(X):
    if   isinstance(X, Entry):
        pass

    elif isinstance(X, EntryBackward):
        pass

    elif isinstance(X, EntryBackwardInputPositionDetection):
        pass

def __drop_out_cost(X):
    if   isinstance(X, DropOut):
        La = len(X.acceptance_checker)
        Lt = len(X.terminal_router)
        assignment_n  = len(ifilter(lambda x: x.acceptance_id != E_AcceptanceIDs.NONE, X.acceptance_checker)) 
        case_n       += La + Lt    # each case must be distinguished
        goto_n        = Lt         # goto terminal ...

    elif isinstance(X, DropOutBackward):
        # Drop outs in pre-context checks all simply transit to the begin 
        # of the forward analyzer. No difference.
        return 0

    elif isinstance(X, DropOutBackwardInputPositionDetection):
        # Drop outs of backward input position handling either do not
        # happen or terminate input position detection.
        return 0

    else:
        assert False

def __transition_map_gain(CombinedState, StateA, StateB):
    assert border_n >= same_target_n

    avrg_interval_n   = int((len(StateA.transition_map) + len(StateB.transition_map)) / 2.0)
    border_increase_n = border_n - avrg_interval_n
- border_increase_n * 4 * (1.0 - same_target_ratio)
    if border_n == 0: same_target_ratio = 1.0
    else:             same_target_ratio = same_target_n / float(border_n)
    # From assert above, it follows that same_target_ratio >= 0  and <= 1
    result, scheme_list = combine_maps.do(StateA, StateB)
    return len(result), len(scheme_list)


