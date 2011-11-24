from quex.blackboard import E_TransitionN, E_AcceptanceIDs
from itertools   import ifilter, islice
from collections import defaultdict

def do(analyzer):
    """RETURNS: 
    
       A dictionary that maps:

               post-context-id --> position register index

       where post-context-id == E_PostContextIDs.NONE means
       'last_acceptance_position'.  The position register index starts from
       0 and ends with N, where N-1 is the number of required position
       registers. It can directly be used as index into an array of
       positions.

       -----------------------------------------------------------------------
    
       Under some circumstances it is necessary to store the acceptance
       position or the position in the input stream where a post context
       begins. For this an array of positions is necessary, e.g.

           QUEX_POSITION_LABEL     positions[4];

       where the last acceptance input position or the input position of
       post contexts may be stored. The paths of a state machine, though,
       may allow to store multiple positions in one array location, because

           (1) the path from store to restore does not intersect, or

           (2) they store their positions in exactly the same states.

       A more general and conclusive condition will be derived later. Now,
       consider the following example:
                                      . b .
                                     /     \ 
                                     \     /
                .-- a -->( 1 )-- b -->( 2 )-- c -->((3))
               /            S47                       R47 
           ( 0 )
               \            S11                       R11
                '-- b -->( 4 )-- c -->( 5 )-- d -->((6))
                             \                     /
                              '-------- e --------'

       The input position needs to be stored for post context 47 in state 1 and
       for post context 11 in state 4. Since the paths of the post contexts do
       not cross it is actually not necessary to have to separate array
       registers. One register for post context 47 and 11 is enough.  Reducing
       position registers saves space, but moreover, it may spare the
       computation time to store redundant input positions.

       .-------------------------------------------------------------------------.
       | CONDITION:                                                              |
       |                                                                         |
       | Let 'A' be a state that restores the input position from register 'x'.  |
       | If 'B' be the last state on a trace to 'A' where the position is stored |
       | in 'x'. If another state 'C' stores the input position in register 'y'  |
       | and comes **AFTER** 'B' on the trace, then 'x' and 'y' cannot be the    |
       | same.                                                                   |
       '-------------------------------------------------------------------------'
    """
    # Database that maps for each state with post context id with which post context id
    # it cannot be combined.
    cannot_db = defaultdict(set)

    def cannot_db_update(db, Trace):
        """According to the CONDITION mentioned in the entry, it determined 
           what post contexts cannot be combined for the given trace list.
           Note, that FAILURE never needs a position register. After FAILURE, 
           the position is set to lexeme start plus one.
        """
        entry_list = [x for x in trace.acceptance_db.itervalues() \
                        if     x.transition_n_since_positioning is E_TransitionN.VOID \
                           and x.pattern_id is not E_AcceptanceIDs.FAILURE]
        for i, x in enumerate(entry_list):
            db[x.pattern_id].add(x.pattern_id)
            for y in entry_list[i+1:]:
                if x.positioning_state_index == y.positioning_state_index: continue
                db[x.pattern_id].add(y.pattern_id)
                db[y.pattern_id].add(x.pattern_id)

    for state_index, trace_list in analyzer.trace_db.iteritems():
        for trace in trace_list:
            cannot_db_update(cannot_db, trace)

    all_post_context_id_list = set(cannot_db.iterkeys())

    combinable_db = dict((pattern_id, all_post_context_id_list.difference(cannot_set))
                         for pattern_id, cannot_set in cannot_db.iteritems())

    # IMPORTANT: When we talk about 'post_context' this includes the 
    #            last acceptance position. Indeed, the last acceptance
    #            position is coded as 'E_PostContextIDs.NONE'.

    result      = {}
    array_index = 0
    while len(combinable_list) != 0:
        # Allways, try to combine the largest combinable set first.
        k           = max(enumerate(combinable_list), key=lambda x: len(x[1]))[0]
        combination = combinable_list.pop(k)

        for post_context_id in combination:
            result[post_context_id] = array_index
            # Delete the post_context_id from all combinable sets, because it is done.
            for combination in combinable_list:
                combination.discard(post_context_id)

        # Since: -- The combinations only contain post_context_id's that have not been
        #           mentioned before, and
        #        -- all empty combinations are deleted from the combinable_list,
        # Thus:  It is safe to assume that new entries were made for the current
        #        array index. Thus, a new array index is required for the next turn.
        array_index += 1

        # Delete combinations that have become empty
        size = len(combinable_list)
        p    = 0
        while p < size:
            if len(combinable_list[p]) == 0: del combinable_list[p]; size -= 1
            else:                            p += 1

    return result

