# vim:set encoding=utf8:
from   quex.engine.analyzer.core import Entry, \
                                        EntryBackward, \
                                        EntryBackwardInputPositionDetection, \
                                        DropOut, \
                                        DropOutBackward, \
                                        DropOutBackwardInputPositionDetection
from   quex.engine.analyzer.template.state import TemplateState, \
                                                  TargetScheme, \
                                                  get_iterable, \
                                                  get_state_list
from   quex.blackboard import E_AcceptanceIDs, \
                              E_TransitionN

from itertools import ifilter
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

class Cost:
    """We start of with a multi-attribute cost, that is then translated into a
       scalar value through function 'total()'.
    """
    def __init__(self, AssignmentN=0, ComparisonN=0, JumpN=0, ByteN=0):
        self.__assignment_n = AssignmentN
        self.__comparison_n = ComparisonN
        self.__jump_n       = JumpN
        self.__byte_n       = ByteN

    def __add__(self, Other):
        assert isinstance(Other, Cost)
        return Cost(AssignmentN = self.__assignment_n + Other.__assignment_n,
                    ComparisonN = self.__comparison_n + Other.__comparison_n,
                    JumpN       = self.__jump_n       + Other.__jump_n,
                    ByteN       = self.__byte_n       + Other.__byte_n)

    def __sub__(self, Other):
        assert isinstance(Other, Cost)
        return Cost(AssignmentN = self.__assignment_n - Other.__assignment_n,
                    ComparisonN = self.__comparison_n - Other.__comparison_n,
                    JumpN       = self.__jump_n       - Other.__jump_n,
                    ByteN       = self.__byte_n       - Other.__byte_n)

    def total(self):
        """The following is only a heuristic with no claim to be perfect.
           It is able to distinguish between the good and the bad cases.
           But, it may fail to distinguish properly between cases that 
           are close to each other in quality. So, no too much to worry about.
        """
        result  = self.__byte_n
        result += self.__assignment_n * 12 # Bytes (= 4 bytes command + 4 bytes address + 4 bytes value) 
        result += self.__comparison_n * 12 # Bytes (= 4 bytes command + 4 bytes address + 4 bytes value) 
        result += self.__jump_n       * 8  # Bytes (= 4 bytes command + 4 bytes address)
        return result
               
class TemplateStateCandidate(TemplateState):
    def __init__(self, StateA, StateB):
        """Compute the 'gain' that results from combining entries, drop_outs
           and transition maps. We start with a multi-attribute gain as 
           given by 'Cost' objects. At the end a scalar value
           is computed by the '.total()' member function.
        """
        TemplateState.__init__(self, StateA, StateB)

        entry_gain          = _compute_gain(_entry_cost, self.entry,    
                                            StateA.entry, StateA.index, 
                                            StateB.entry, StateB.index)
        drop_out_gain       = _compute_gain(_drop_out_cost, self.drop_out, 
                                            StateA.drop_out, StateA.index, 
                                            StateB.drop_out, StateB.index)
        transition_map_gain = _transition_map_gain(self.transition_map, 
                                                   StateA.transition_map, StateB.transition_map)

        self.__gain = (entry_gain + drop_out_gain + transition_map_gain).total()

    @property 
    def gain(self):
        return self.__gain

def _transition_map_gain(CombinedTM, TM_A, TM_B):
    """Estimate the gain that can be achieved by combining two transition
       maps into a signle one.
    """
    a_cost        = _transition_cost(TM_A)
    b_cost        = _transition_cost(TM_B)
    combined_cost = _transition_cost(CombinedTM)

    return (a_cost + b_cost) - combined_cost

def _compute_gain(cost_function, Combined, A, StateA_Index, B, StateB_Index):
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
    # Cost of each object if separated in two states
    a_cost   = sum(map(lambda element: cost_function(element[0]), get_iterable(A, StateA_Index)), Cost())
    b_cost   = sum(map(lambda element: cost_function(element[0]), get_iterable(B, StateB_Index)), Cost())
    # Cost if it is combined
    combined_cost = sum(map(lambda element: cost_function(element[0]), Combined.iteritems()), Cost())

    return (a_cost + b_cost) - combined_cost

def _entry_cost(X):
    if   isinstance(X, Entry):
        La = len(ifilter(lambda x: x.acceptance_id != E_AcceptanceIDs.VOID, X.accepter))
        # Number of accepter elements: if(pre-context) acceptance = ...
        assignment_n  = La
        goto_n        = La
        cmp_n         = La
        Lp = len(X.positioner)
        # Assume that we store the positions without watching for pre-contexts
        assignment_n += Lp

        return Cost(AssignmentN = assignment_n, 
                    ComparisonN = cmp_p, 
                    JumpN       = goto_n)

    elif isinstance(X, EntryBackward):
        La = len(X.pre_context_fulfilled_set)
        # Number of accepter elements: pre_context_fulfilled_XYZ_f = true
        # (No positions will ever be stored with Backward Analyzis for pre-contexts ...
        #  remember, we go back to the initial position to start forward analyzis.)
        return Cost(AssignmentN=La)

    elif isinstance(X, EntryBackwardInputPositionDetection):
        return Cost(0, 0, 0)

    else:
        assert False

def _drop_out_cost(X):
    if   isinstance(X, DropOut):
        # (1) One Acceptance Check implies:
        #        if( pre_condition == Const ) acceptance = const; 
        #     in pseudo-assembler:
        #        jump-if-not (pre_condition == Const) --> goto After
        #        acceptance = Const;
        #     After:
        #        ...
        La = len(filter(lambda x: x.acceptance_id != E_AcceptanceIDs.VOID, X.acceptance_checker))
        assignment_n  = La
        goto_n        = La
        cmp_n         = La
        # (2) Terminal Routing:
        #         jump-if-not (acceptance == Const0 ) --> Next0
        #         goto TerminalXY
        #     Next0:
        #         jump-if-not (acceptance == Const0 ) --> Next1
        #         position = something;
        #         goto TerminalYZ
        #     Next1:
        #         ...
        Lt = len(X.terminal_router)
        assignment_n += len(filter(lambda x:     x.positioning != E_TransitionN.VOID 
                                             and x.positioning != E_TransitionN.LEXEME_START_PLUS_ONE, 
                            X.terminal_router))
        cmp_n  += Lt
        goto_n += Lt  

        return Cost(AssignmentN = assignment_n, 
                    ComparisonN = cmp_n, 
                    JumpN       = goto_n)

    elif isinstance(X, DropOutBackward):
        # Drop outs in pre-context checks all simply transit to the begin 
        # of the forward analyzer. No difference.
        return Cost(0, 0, 0)

    elif isinstance(X, DropOutBackwardInputPositionDetection):
        # Drop outs of backward input position handling either do not
        # happen or terminate input position detection.
        return Cost(0, 0, 0)

    else:
        assert False

def _transition_cost(TM):
    """Computes the storage consumption of a transition map."""
    interval_n = len(TM)
    border_n   = interval_n - 1
    # 
    jump_n     = interval_n * 2  # because: if 'jump', else 'jump'
    cmp_n      = border_n
    # For each target scheme, the target state needs to be stored for each state_key.
    target_scheme_n  = 0
    involved_state_n = 0
    for interval, target in ifilter(lambda x: isinstance(x[1], TargetScheme), TM):
        if involved_state_n == 0:
            # The number of involved states is the same for all target schemes.
            involved_state_n = len(target.scheme)
        target_scheme_n += 1

    byte_n = (target_scheme_n * involved_state_n) * 4
    return Cost(ComparisonN=cmp_n, JumpN=jump_n, ByteN=byte_n)


