# vim:set encoding=utf8:
"""
(C) 2010-2011 Frank-Rene Schäfer
"""
from quex.engine.analyzer.state.drop_out import DropOut, \
                                                DropOutBackward, \
                                                DropOutBackwardInputPositionDetection
from quex.engine.analyzer.mega_state.template.state import TemplateState, \
                                                           get_iterable
from quex.blackboard import E_AcceptanceIDs, \
                            E_TransitionN

class TemplateStateCandidate(TemplateState):
    """A TemplateStateCandidate determines a tentative template combination 
       of two states (where each one of them may already be a TemplateState).
       It sets up a TemplateState and determines the 'gain of combination'.

       The 'Cost' class is used to describe gain/cost as a multi-attribute
       measure. The member '.total()' determines a scalar value by means
       of a heuristics.
    """
    def __init__(self, StateA, StateB, TheAnalyzer):
        TemplateState.__init__(self, StateA, StateB, TheAnalyzer)
        self.__asserts(TheAnalyzer)

        entry_gain          = _compute_entry_gain(self.entry, StateA.entry, StateB.entry)
        drop_out_gain       = _compute_drop_out_gain(self.drop_out, 
                                                     StateA.drop_out, StateA.index, 
                                                     StateB.drop_out, StateB.index)
        transition_map_gain = _transition_map_gain(self.transition_map, self.target_scheme_list,
                                                   StateA.transition_map, StateB.transition_map)

        self.__gain         = (entry_gain + drop_out_gain + transition_map_gain).total()

    def __asserts(self, TheAnalyzer):
        if TheAnalyzer is None: return

        # All states in the state_index_list must be from the original analyzer
        def _check(StateIndexList):
            for state_index in StateIndexList:
                assert TheAnalyzer.state_db.has_key(state_index)

        _check(self.state_index_list)
        # for entry, state_index_list in self.entry.iteritems():
        #    check(state_index_list)
        for drop_out, state_index_list in self.drop_out.iteritems():
            _check(state_index_list)

    @property 
    def gain(self):
        return self.__gain

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
               
def _transition_map_gain(CombinedTM, TargetSchemeList, TM_A, TM_B):
    """Estimate the gain that can be achieved by combining two transition
       maps into a signle one.
    
    """
    a_cost        = _transition_cost(TM_A)
    b_cost        = _transition_cost(TM_B)
    combined_cost = _transition_cost(CombinedTM, TargetSchemeList)

    return (a_cost + b_cost) - combined_cost

def _compute_entry_gain(Combined, A, B):
    """Computes cost of each entry by recursively walking through the
       door tree--summing up the cost of each command list in the nodes.
    """
    def __dive(Node):
        assert Node is not None, "Entry has not been 'finish()-ed'"
        result  = sum(__dive(child) for child in Node.child_list)
        result += Node.common_command_list.cost()
        return result

    # Cost of each object if separated in two states
    a_cost        = __dive(A.door_tree_root)
    b_cost        = __dive(B.door_tree_root)
    # Cost if it is combined
    combined_cost = __dive(Combined.door_tree_root)

    return Cost(AssignmentN = (a_cost + b_cost) - combined_cost)

def _compute_drop_out_gain(Combined, A, StateA_Index, B, StateB_Index):
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
    def __cost(Iterable):
        return sum(map(lambda element: _drop_out_cost(element[0]), Iterable), Cost())

    # Cost of each object if separated in two states
    a_cost        = __cost(get_iterable(A, StateA_Index))
    b_cost        = __cost(get_iterable(B, StateB_Index))
    # Cost if it is combined
    combined_cost = __cost(Combined.iteritems())

    return (a_cost + b_cost) - combined_cost

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

def _transition_cost(TM, TargetSchemeList=None):
    """Computes the storage consumption of a transition map.
    """
    interval_n = len(TM)
    border_n   = interval_n - 1
    # 
    jump_n     = interval_n * 2  # because: if 'jump', else 'jump'
    cmp_n      = border_n
    if TargetSchemeList is not None:
        # For each target scheme, the target state needs to be stored for each state_key.
        target_scheme_element_n  = sum(len(target.scheme) for target in TargetSchemeList)
        byte_n = target_scheme_element_n * 4
    else:
        byte_n = 0
    return Cost(ComparisonN=cmp_n, JumpN=jump_n, ByteN=byte_n)


