# vim:set encoding=utf8:
# (C) 2010-2012 Frank-Rene Schäfer
from   quex.engine.analyzer.mega_state.core    import TargetByStateKey
from   quex.engine.analyzer.state.entry_action import DoorID_Scheme
from   quex.engine.analyzer.state.drop_out     import DropOut, \
                                                      DropOutIndifferent, \
                                                      DropOutBackwardInputPositionDetection
from   quex.engine.analyzer.transition_map  import TransitionMap       

from   quex.blackboard import E_AcceptanceIDs, \
                              E_TransitionN, \
                              E_StateIndices
from   itertools import chain

class TemplateStateCandidate(object):
    """________________________________________________________________________
    
    A TemplateStateCandidate determines a tentative template combination of two
    states (where each one of them may already be a TemplateState).  It sets up
    a TemplateState and determines the 'gain of combination'.

    The 'Cost' class is used to describe gain/cost as a multi-attribute
    measure. The member '.total()' determines a scalar value by means of a
    heuristics.

    ___________________________________________________________________________
    """
    __slots__ = ("__gain", "__state_a", "__state_b")

    def __init__(self, StateA, StateB):
        entry_gain          = _compute_entry_gain(StateA.entry, StateB.entry)
        drop_out_gain       = _compute_drop_out_gain(StateA.drop_out, StateB.drop_out)
        transition_map_gain = _transition_map_gain(StateA, StateB)

        self.__gain         = entry_gain + drop_out_gain + transition_map_gain
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
        """The following is only a heuristic with no claim to be perfect.  It
        is able to distinguish between the good and the bad cases.  But, it may
        fail to distinguish properly between cases that are close to each other
        in quality. So, no too much to worry about.
        """
        result  = self.__byte_n
        result += self.__assignment_n * 12 # Bytes (= 4 bytes command + 4 bytes address + 4 bytes value) 
        result += self.__comparison_n * 12 # Bytes (= 4 bytes command + 4 bytes address + 4 bytes value) 
        result += self.__jump_n       * 8  # Bytes (= 4 bytes command + 4 bytes address)
        return result
               
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
    # (1) Compute sizes BEFORE setting Combined_cl_set = A_unique_cl_set
    A_size = len(A_unique_cl_set)
    B_size = len(B_unique_cl_set)
    # (2) Compute combined cost
    Combined_cl_set = A_unique_cl_set  # reuse 'A_unique_cl_set'
    Combined_cl_set.update(B_unique_cl_set)
    return Cost(AssignmentN = A_size + B_size - len(Combined_cl_set)).total()
    
def _compute_drop_out_gain(A, B):
    """Computes 'gain' with respect to drop-out actions, if two states are
    combined.
    """
    a_cost_db = dict((drop_out, _drop_out_cost(drop_out, len(state_index_list))) \
                     for drop_out, state_index_list in A.iteritems())
    b_cost_db = dict((drop_out, _drop_out_cost(drop_out, len(state_index_list))) \
                     for drop_out, state_index_list in B.iteritems())

    # (1) Compute sum BEFORE setting 'combined_cost_db = a_cost_db'!
    ab_sum = 0
    for cost in a_cost_db.itervalues():
        ab_sum += cost

    for cost in b_cost_db.itervalues():
        ab_sum += cost

    # (2) Compute combined cost
    combined_cost_db = a_cost_db       # reuse 'a_cost_db'
    combined_cost_db.update(b_cost_db)

    # Each state in the Template requires some routing: switch(state_key) { ... case 4: ... }
    # Thus, there is some 'cost = C * state number' for a template state. However, 
    # "state_a_n * C + state_b_n * C = combined_state_n * C" which falls out
    # when the subtraction is done.
    c_sum = 0
    for cost in combined_cost_db.itervalues():
        c_sum += cost

    return ab_sum - c_sum

def _drop_out_cost(X, StateIndexN):
    if   isinstance(X, DropOutIndifferent):
        # Drop outs in pre-context checks all simply transit to the begin 
        # of the forward analyzer. No difference.
        return Cost(0, 0, 0).total()

    elif isinstance(X, DropOutBackwardInputPositionDetection):
        # Drop outs of backward input position handling either do not
        # happen or terminate input position detection.
        return Cost(0, 0, 0).total()

    assert isinstance(X, DropOut)
    # One Acceptance Check implies:
    #    if( pre_condition == Const ) acceptance = const; 
    # in pseudo-assembler:
    #    jump-if-not (pre_condition == Const) --> goto After
    #    acceptance = Const;
    # After:
    #        ...
    La = len(filter(lambda x: x.acceptance_id != E_AcceptanceIDs.VOID, X.get_acceptance_checker()))
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
    Lt = len(X.get_terminal_router())
    assignment_n += len(filter(lambda x:     x.positioning != E_TransitionN.VOID 
                                         and x.positioning != E_TransitionN.LEXEME_START_PLUS_ONE, 
                        X.get_terminal_router()))
    cmp_n  += Lt
    goto_n += Lt  

    return Cost(AssignmentN = assignment_n, 
                ComparisonN = cmp_n, 
                JumpN       = goto_n).total() * StateIndexN

def _transition_map_gain(StateA, StateB):
    """Estimate the gain that can be achieved by combining two transition
       maps into a signle one.
    
    """
    a_cost        = _transition_cost_single(StateA)
    b_cost        = _transition_cost_single(StateB)
    combined_cost = _transition_cost_combined(StateA, StateB)

    return ((a_cost + b_cost) - combined_cost).total()

def _transition_cost_single(State):
    """Computes the storage consumption of a transition map.
    """
    if hasattr(State, "target_scheme_n"): scheme_n = State.target_scheme_n
    else:                                 scheme_n = 0

    return __transition_cost(InvolvedStateN = len(State.implemented_state_index_set()), 
                             IntervalN      = len(State.transition_map),
                             SchemeN        = scheme_n)
    
def update_scheme_set(scheme_set, TA, TB):
    """This function is used to count the number of different schemes in a
    combination of transition maps. The number of different schemes is used
    to determine the cost a combination of transition maps.

    NOTE: The use of 'hash' has the potential to miss a non-equal occurrence.
          The value is only for metrics. So its no great deal.
    """
    assert isinstance(TA, TargetByStateKey) 
    assert isinstance(TB, TargetByStateKey) 

    # The 'common drop_out case' is covered by 'uniform_door_id'
    if TA.uniform_door_id is not None:
        if TA.uniform_door_id == TB.uniform_door_id:
            return 

    my_hash = 0x5A5A5A5A
    for x in chain(TA.iterable_door_id_scheme(), TB.iterable_door_id_scheme()):
        my_hash ^= hash(x)
    scheme_set.add(my_hash)

def _transition_cost_combined(StateA, StateB):
    """Computes the storage consumption of a transition map.
    """
    involved_state_n =  len(StateA.implemented_state_index_set()) \
                      + len(StateB.implemented_state_index_set())
    TM_A = StateA.transition_map
    TM_B = StateB.transition_map

    # Count the number of unique schemes and the total interval number
    interval_n = 0
    scheme_set = set()
    for begin, end, a_target, b_target in TransitionMap.izip(TM_A, TM_B):
        interval_n += 1
        update_scheme_set(scheme_set, a_target, b_target)

    scheme_n = len(scheme_set)

    return __transition_cost(involved_state_n, interval_n, scheme_n)

def __transition_cost(InvolvedStateN, IntervalN, SchemeN):
    border_n = IntervalN - 1
    jump_n   = IntervalN * 2  # because: if 'jump', else 'jump'
    cmp_n    = border_n
    byte_n   = SchemeN * InvolvedStateN * 4  # assume 4 bytes per entry in scheme
    return Cost(ComparisonN=cmp_n, JumpN=jump_n, ByteN=byte_n)

