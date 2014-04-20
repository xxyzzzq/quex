# vim:set encoding=utf8:
# (C) 2010-2012 Frank-Rene Schäfer
from   quex.engine.analyzer.mega_state.core       import TargetByStateKey
from   quex.engine.analyzer.door_id_address_label import DoorID_Scheme
from   quex.engine.analyzer.state.drop_out        import DropOut, \
                                                         DropOutIndifferent, \
                                                         DropOutBackwardInputPositionDetection
from   quex.engine.analyzer.transition_map        import TransitionMap       

from   quex.blackboard import E_IncidenceIDs, \
                              E_TransitionN, \
                              E_StateIndices
from   itertools import chain

class TemplateStateCandidate(object):
    """________________________________________________________________________
    
    Contains information about a possible combination of two states into 
    a single template state. It computes:

        -- entry gain: That is the gain which results from have the state
                       entries implemented in a single state. This gain 
                       results from command lists appearring in both states.
                       Instead of being implemented twice, they are 
                       implemented once.

        -- drop-out gain: Like 'entry gain' respectively for drop outs.

        -- transition map gain: The gain from combining the state's tran-
                                sition map.
    ___________________________________________________________________________
    """
    __slots__ = ("__gain", "__state_a", "__state_b")

    def __init__(self, StateA, StateB):
        entry_gain          = _compute_entry_gain(StateA.entry, StateB.entry)
        drop_out_gain       = _compute_drop_out_gain(StateA.drop_out, StateB.drop_out)

        transition_map_gain = _transition_map_gain(StateA.transition_map,
                                                   len(StateA.implemented_state_index_set()),
                                                   StateA.target_scheme_n,
                                                   StateB.transition_map,
                                                   len(StateB.implemented_state_index_set()),
                                                   StateB.target_scheme_n)

        self.__gain    = entry_gain + drop_out_gain + transition_map_gain
        self.__state_a = StateA
        self.__state_b = StateB

    @property 
    def gain(self):    return self.__gain
    @property
    def state_a(self): return self.__state_a
    @property
    def state_b(self): return self.__state_b

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
    return A_size + B_size - len(Combined_cl_set)
    
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
        return 0

    elif isinstance(X, DropOutBackwardInputPositionDetection):
        # Drop outs of backward input position handling either do not
        # happen or terminate input position detection.
        return 0

    assert isinstance(X, DropOut)
    # One Acceptance Check implies:
    #    if( pre_condition == Const ) acceptance = const; 
    # in pseudo-assembler:
    #    jump-if-not (pre_condition == Const) --> goto After
    #    acceptance = Const;
    # After:
    #        ...
    La = len(filter(lambda x: x.acceptance_id != E_IncidenceIDs.VOID, X.get_acceptance_checker()))
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

    return assignment_ns + cmp_n,  + goto_n 

def _transition_map_gain(ATm, AStateN, ASchemeN, BTm, BStateN, BSchemeN):
    """*Tm      -- transition map.
       *StateN  -- number of implemented states.
       *SchemeN -- number of different target schemes in transition map.
    
       Estimate the gain that can be achieved by combining two transition
       maps into a signle one.
    
    """
    # Costs of each single transition maps
    a_cost = __transition_map_cost(AStateN, len(ATm), ASchemeN)
    b_cost = __transition_map_cost(BStateN, len(BTm), BSchemeN)

    # Cost of the combined transition map
    combined_cost = _transition_cost_combined(ATm, BTm, AStateN + BStateN)

    return ((a_cost + b_cost) - combined_cost)
    
def update_scheme_set(scheme_set, TA, TB):
    """This function is used to count the number of different schemes in a
    combination of transition maps. The number of different schemes is used
    to determine the cost a combination of transition maps.

    NOTE: The use of 'hash' has the potential to miss a non-equal occurrence.
          The value is only for metrics. So its no great deal.

    RETURNS: True  -- if size remains the same
             False -- if size increases (scheme was new)
    """
    assert isinstance(TA, TargetByStateKey) 
    assert isinstance(TB, TargetByStateKey) 

    # The 'common drop_out case' is covered by 'uniform_door_id'
    if TA.uniform_door_id is not None:
        if TA.uniform_door_id == TB.uniform_door_id:
            return False

    my_hash = 0x5A5A5A5A
    prime   = 1299827  # Use a huge prime number for deterministic randomization
    for i, x in enumerate(chain(TA.iterable_door_id_scheme(), 
                                TB.iterable_door_id_scheme())):
        my_hash ^= hash(x) * i
        my_hash ^= prime

    size_before = len(scheme_set)
    scheme_set.add(my_hash)
    return size_before == len(scheme_set)

def _transition_cost_combined(TM_A, TM_B, ImplementedStateN):
    """Computes the storage consumption of a transition map.
    """
    # Count the number of unique schemes and the total interval number
    scheme_set       = set()
    uniform_target_n = 0
    interval_n       = 0
    for begin, end, a_target, b_target in TransitionMap.izip(TM_A, TM_B):
        interval_n += 1
        if     a_target.uniform_door_id is not None \
           and a_target.uniform_door_id == a_target.uniform_door_id:
            uniform_target_n += 1
        else:
            update_scheme_set(scheme_set, a_target, b_target)

    # The number of different schemes:
    scheme_n = len(scheme_set)

    return __transition_map_cost(ImplementedStateN, interval_n, scheme_n)

def __transition_map_cost(ImplementedStateN, IntervalN, SchemeN):
    """ImplementedStateN -- Number of states which are implemeted in the scheme.
       IntervalN         -- Number of intervals in the transition map.
       SchemeN           -- Number of DIFFERENT schemes in the transition map.
    
    Find a number which is proportional to the 'cost' of the transition
    map. Example:

         interval 1 --> [1, 3, 5, 1]
         interval 2 --> drop_out
         interval 3 --> [1, 3, 5, 1]
         interval 4 --> 5
         interval 5 --> [1, 3, 5, 1]
         interval 6 --> [2, 1, 1, 2]

     This transition map has 5 borders and 5 targets. Let the cost
     of a border as well as the cost for a single target be '1'.
     The additional cost for a required scheme is chosen to be 
     'number of scheme elements' which is the number of implemented
     states. Schemes that are the same are counted as 1.
    """
    #print "#ImplementedStateN", ImplementedStateN
    #print "#IntervalN", IntervalN
    #print "#SchemeN", SchemeN

    cost_border  = IntervalN - 1
    target_n     = IntervalN
    cost_targets = target_n + SchemeN * ImplementedStateN

    return cost_border + cost_targets

