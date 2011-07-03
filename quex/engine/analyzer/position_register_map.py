from itertools   import imap, ifilter
from collections import defaultdict
from operator    import itemgetter
from copy import copy

def do(analyzer):
    """RETURNS: 
    
       A dictionary that maps:

               post-context-id --> position register index

       where post-context-id == PostContextIDs.NONE means
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
       they never interact. 
       
       For example:                   . b .
                                     /     \ 
                                     \     /
                .-- a -->( 1 )-- b -->( 2 )-- c -->((3))
               /            S47                       R47 
           ( 0 )
               \            S11                       R11
                '-- b -->( 4 )-- c -->( 5 )-- d -->((6))
                             \                     /
                              '-------- e --------'

       The input position needs to be stored for post context 47 in state 1
       and for post context 11 in state 4. Since the paths of the post contexts
       do not cross it is actually not necessary to have to separate
       array registers. One for post context 47 and 11 is enough.

       This function determines what post contexts (together with the
       'acceptance position register) can share a single register/array 
       location. It does so by investigating the drop-out routers and how 
       they use position registers: 
       
            Position registers that appear together in a drop-out router
            CANNOT share a register. Otherwise their positions would not be
            distinguishable. (Exception: if the two position registers are
            applied in exactly the same set of states. This case is
            not yet considered.)
    """
    # IMPORTANT: When we talk about 'post_context' this includes the 
    #            last acceptance position. Indeed, the last acceptance
    #            position is coded as 'PostContextIDs.NONE'.
    # (1) Determine: -- Set of all existing post context ids.
    #                -- Set of constellations of post contexts as they 
    #                   appear in the drop-out routers.
    all_post_context_set, constellation_list = analyzer._get_position_storage_constellations()

    #     Loop over all routers of the drop out handlers.
    constellation_set = set()
    for sub_constellation_list in [ analyze_this(analyzer, x) for x in constellation_list ]:
        for sub_constellation in sub_constellation_list:
            print "##", sub_constellation
            constellation_set.add(sub_constellation)

    # (2) Determine: For each post context the set of post context with which it 
    #                can share the position register.

    # -- First, assume for each post context that it can share with ALL others
    allowed_db = dict([(register, copy(all_post_context_set)) for register in all_post_context_set])
    print "##al", allowed_db
    print "##cs", constellation_set

    # -- Second, delete for each post context the post contexts with which it 
    #    appears together.
    for post_context_id in all_post_context_set:
        for constellation in ifilter(lambda x: register in x, constellation_set):
            # Never remove a register itself from the combinable set
            for other in ifilter(lambda x: x != post_context_id, constellation):
                allowed_db[post_context_id].discard(other)

    # (3) Determine: For each post context the index in an array of stored 
    #                input positions that it would use.
    # -- allowed_db.values() lists all combinable sets of post context.
    combinable_list = allowed_db.values()

    result      = {}
    array_index = 0
    while len(combinable_list) != 0:
        # Allways, try to combine the largest combinable set first.
        k           = max(enumerate(combinable_list), key=itemgetter(1))[0]
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

def analyze_this(analyzer, PostContextIDSet):
    """If different input positions store their content at the same
       input states, then they can still share the same register.
    """
    if len(PostContextIDSet) == 0: return [()]

    # Find all states where post context id is stored
    storing_state_db = dict([(post_context_id, analyzer._get_storing_state_set(post_context_id))
                             for post_context_id in PostContextIDSet])
                                
    inverse_db = defaultdict(set)
    for post_context_id, storing_state_set in storing_state_db.iteritems():
        inverse_db[tuple(sorted(storing_state_set))].add(post_context_id)

    # Post context positions that are stored all in the same states, can 
    # be combined.
    # (1) Compute set of states that never appear in a combinable
    can_be_combined_set_list = [ tuple(x) for x in inverse_db.values() ]
    root_not_combinable      = copy(PostContextIDSet)
    for can_be_combined_set in can_be_combined_set_list:
        root_not_combinable.difference_update(can_be_combined_set)

    LenCBCSL     = len(can_be_combined_set_list)
    limit_vector = [ len(x) for x in can_be_combined_set_list ]
    cursor       = [ 0 ] * LenCBCSL
    combination  = [ 0 ] * LenCBCSL
    # Number of possible combinations of remaining sets:
    N            = reduce(lambda x, y: x * y, limit_vector)
    result       = [ None ] * N
    print "##start", limit_vector, can_be_combined_set_list
    for n in xrange(N):
        print "##cursor", cursor
        for i in xrange(LenCBCSL):
            combination[i] = can_be_combined_set_list[i][cursor[i]]
        result[n] = tuple(sorted(root_not_combinable.union(combination)))
        # Increment cursor:
        for i in xrange(LenCBCSL):
            cursor[i] += 1
            if cursor[i] == limit_vector[i]: cursor[i] = 0; 
            else:                            break

    print "##", result
    return result

