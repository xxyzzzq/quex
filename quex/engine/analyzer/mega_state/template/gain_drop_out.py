from   quex.engine.analyzer.state.drop_out import DropOutIndifferent, \
                                                  DropOutBackwardInputPositionDetection, \
                                                  DropOut
from   quex.blackboard import E_IncidenceIDs, \
                              E_TransitionN
from   itertools import chain

def do(A, B):
    """Computes 'gain' with respect to drop-out actions, if two states are
    combined.
    """
    a_cost_db = dict((drop_out, _drop_out_cost(drop_out, len(state_index_list))) \
                     for drop_out, state_index_list in A.iteritems())
    b_cost_db = dict((drop_out, _drop_out_cost(drop_out, len(state_index_list))) \
                     for drop_out, state_index_list in B.iteritems())

    # (1) Compute sum BEFORE setting 'combined_cost_db = a_cost_db'!
    ab_sum = sum(chain(a_cost_db.itervalues(), b_cost_db.itervalues()))

    # (2) Compute combined cost
    combined_cost_db = a_cost_db       # reuse 'a_cost_db'
    combined_cost_db.update(b_cost_db)

    # Each state in the Template requires some routing: switch(state_key) { ... case 4: ... }
    # Thus, there is some 'cost = C * state number' for a template state. However, 
    # "state_a_n * C + state_b_n * C = combined_state_n * C" which falls out
    # when the subtraction is done.
    c_sum = sum(combined_cost_db.itervalues())

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

    return assignment_n + cmp_n + goto_n 

