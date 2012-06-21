# vim:set encoding=utf8:
"""
(C) 2010-2011 Frank-Rene Schäfer
"""
import quex.engine.analyzer.transition_map as     transition_map_tools
from   quex.engine.analyzer.state.drop_out import DropOut, \
                                                  DropOutBackward, \
                                                  DropOutBackwardInputPositionDetection
from   quex.blackboard import E_AcceptanceIDs, E_TransitionN

class TemplateStateCandidate(object):
    """A TemplateStateCandidate determines a tentative template combination 
       of two states (where each one of them may already be a TemplateState).
       It sets up a TemplateState and determines the 'gain of combination'.

       The 'Cost' class is used to describe gain/cost as a multi-attribute
       measure. The member '.total()' determines a scalar value by means
       of a heuristics.
    """
    __slots__ = ("__gain", "__state_a", "__state_b")

    def __init__(self, StateA, StateB, StateDB):
        TemplateState.__init__(self, StateA, StateB, StateDB)

        involved_state_n    = len(StateA.implemented_state_index_list()) + len(StateB.implemented_state_index_list())

        entry_gain          = _compute_entry_gain(StateA.entry, StateB.entry)
        drop_out_gain       = _compute_drop_out_gain(StateA.drop_out, StateA.index, 
                                                     StateB.drop_out, StateB.index)
        transition_map_gain = _transition_map_gain(involved_state_n,
                                                   StateA.transition_map, StateB.transition_map)

        self.__gain         = (entry_gain + drop_out_gain + transition_map_gain).total()
        self.__state_a      = StateA
        self.__state_b      = StateB

    @property 
    def gain(self):    return self.__gain
    @property
    def state_a(self): return self.__state_a
    @property
    def state_b(self): return self.__state_b

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
               
def _transition_map_gain(CombinedTM, InvolvedStateN, TM_A, TM_B):
    """Estimate the gain that can be achieved by combining two transition
       maps into a signle one.
    
    """
    a_cost        = _transition_cost(TM_A)
    b_cost        = _transition_cost(TM_B)
    combined_cost = _transition_cost_combined(TM_A, TM_B, InvolvedStateN)

    return (a_cost + b_cost) - combined_cost

def _compute_entry_gain(A, B):
    """Computes 'gain' with respect to entry actions, if two states are
    combined.
    """
    # Every different command list requires a separate door.
    # => Entry cost is proportional to number of unique command lists.
    # => Gain =   number of unique command lists of A an B each
    #           - number of unique command lists of Combined(A, B)
    A_unique_cl_set = set(ta.command_list for ta in A.action_db.itervalues())
    B_unique_cl_set = set(ta.command_list for ta in B.action_db.itervalues())
    A_size = len(A_unique_cl_set)
    B_size = len(B_unique_cl_set)
    Combined_cl_set = A_unique_cl_set#
    Combined_cl_set.update(B_unique_cl_set)
    return Cost(AssignmentN = A_size + B_size - len(Combined_cl_set))
    
def _compute_drop_out_gain(A, B):
    """Computes 'gain' with respect to drop-out actions, if two states are
    combined.
    """
    a_cost_db = dict((drop_out, __cost(drop_out)) for drop_out in A.itervalues())
    b_cost_db = dict((drop_out, __cost(drop_out)) for drop_out in A.itervalues())

    combined_cost_db = a_cost_db
    combined_cost_db.update(b_cost_db)

    a_cost        = sum(cost for cost in a_cost_db.itervalues())
    b_cost        = sum(cost for cost in b_cost_db.itervalues())
    combined_cost = sum(cost for cost in combined_cost_db.itervalues())
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

def _transition_cost_combined(TM_A, TM_B, InvolvedStateN):
    """Computes the storage consumption of a transition map.
    """
    interval_n              = 0
    target_scheme_element_n = 0
    scheme_set              = set()
    cost                    = 0
    for begin, end, a_target, b_target in transition_map_tools.zipped_iterable(TM_A, TM_B):
        interval_n += 1
        cost       += TargetFactory.combination_cost(a_target, b_target, scheme_set)

    # '1' cost means: a target scheme has been represented
    # => 'real cost' = cost * InvolvedStateN
    cost *= InvolvedStateN

    border_n   = interval_n - 1
    # 
    jump_n     = interval_n * 2  # because: if 'jump', else 'jump'
    cmp_n      = border_n

    target_scheme_element_n
    byte_n                  = target_scheme_element_n * 4
    return Cost(ComparisonN=cmp_n, JumpN=jump_n, ByteN=byte_n)

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
        target_scheme_element_n  = sum(len(scheme) for scheme in TargetSchemeList)
        byte_n                   = target_scheme_element_n * 4
    else:
        byte_n = 0
    return Cost(ComparisonN=cmp_n, JumpN=jump_n, ByteN=byte_n)

class TargetFactory:
    """Produces MegaState_Target-s based on the combination of two MegaState_Target-s
       which are associated each with a State (MegaState, or PseudoMegaState).
    """
    def __init__(self, StateA, StateB):
        self.__length_a = len(StateA.implemented_state_index_list())
        self.__length_b = len(StateB.implemented_state_index_list())
        self.__drop_out_scheme_a = (E_StateIndices.DROP_OUT,) * self.__length_a
        self.__drop_out_scheme_b = (E_StateIndices.DROP_OUT,) * self.__length_b

    def get(self, TA, TB):
        assert isinstance(TA, MegaState_Target) 
        assert isinstance(TB, MegaState_Target) 

        if TA.drop_out_f:
            if TB.drop_out_f:
                return TA
            TA_scheme = self.__drop_out_scheme_a

        elif TA.target_state_index is not None:
            if TB.target_state_index is not None and TA.target_state_index == TB.target_state_index:
                return TA
            TA_scheme = (TA.target_state_index,) * self.__length_a

        else:
            TA_scheme = TA.scheme

        if TB.drop_out_f:
            # TA was not drop-out, otherwise we would have returned earlier
            TB_scheme = self.__drop_out_scheme_b

        elif TB.target_state_index is not None:
            # TA was not the same door, otherwise we would have returned earlier
            TB_scheme = (TB.target_state_index,) * self.__length_b

        else:
            TB_scheme = TB.scheme

        return MegaState_Target.create(TA_scheme + TB_scheme)

    @staticmethod
    def combination_cost(TA, TB, scheme_set):
        assert isinstance(TA, MegaState_Target) 
        assert isinstance(TB, MegaState_Target) 

        if TA.drop_out_f:
            if TB.drop_out_f:
                return 0
            TA_scheme_r = E_StateIndices.DROP_OUT # We only need a 'key'

        elif TA.target_state_index is not None:
            if TB.target_state_index is not None and TA.target_state_index == TB.target_state_index:
                return 0
            TA_scheme_r = TA.target_state_index # We only need a 'key' 

        else:
            TA_scheme_r = TA.scheme

        if TB.drop_out_f:
            # TA was not drop-out, otherwise we would have returned earlier
            TB_scheme_r = E_StateIndices.DROP_OUT # We only need a 'key'

        elif TB.target_state_index is not None:
            # TA was not the same door, otherwise we would have returned earlier
            TB_scheme_r = TB.target_state_index # We only need a 'key' 

        else:
            TB_scheme_r = TB.scheme

        scheme_representive = (TA_scheme_r, TB_scheme_r)
        if scheme_representive in scheme_set:
            return 0
        else:
            scheme_set.add(scheme_representive)

        return 1


