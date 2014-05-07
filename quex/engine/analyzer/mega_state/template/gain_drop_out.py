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

    return X.cost()

