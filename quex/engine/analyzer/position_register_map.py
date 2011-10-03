from itertools   import ifilter, islice

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

       This present function determines what post contexts (together with the
       'acceptance position register) can share a single register/array
       location. As a result it delivers a mapping from post context id to
       an array index in a position storage array. 
    """
    # IMPORTANT: When we talk about 'post_context' this includes the 
    #            last acceptance position. Indeed, the last acceptance
    #            position is coded as 'E_PostContextIDs.NONE'.

    # (1) Determine: -- Set of all present post-context-ids that are related to store/restore.
    #                -- Sets of post_context_ids that store their positions in exactly the
    #                   same states.
    all_post_context_id_set, \
    equivalent_sets          = analyzer._get_equivalent_post_context_id_sets()

    # (2) Determine: Sets of post context ids, where the paths from storage
    #                of input position and restore of input position does 
    #                not interact.
    combinable_list = find_non_intersecting_post_context_id_groups(all_post_context_id_set, analyzer)

    # (*) To each non-intersecting state set on can add the equivalent 
    #     post-context-ids.
    for candidate in combinable_list:
        for equivalent in ifilter(lambda x : not x.isdisjoint(candidate), equivalent_sets):
            candidate.update(equivalent)

    # -- Make sure, that each post-context-id is at least considered, even though,
    #    it may not appear in the combinable set.
    combinable_list.extend(set([x]) for x in all_post_context_id_set)
    # -- Make sure, that all equivalent sets appear
    combinable_list.extend(equivalent_sets)

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

def find_non_intersecting_post_context_id_groups(AllPostContextID_List, analyzer):
    """Determine groups of post-context-ids where the path from store input 
       position to restore input position does not intersect.
    """
    StateSetDB = analyzer._find_state_sets_from_store_to_restore()

    result = []
    for i, post_context_id in enumerate(AllPostContextID_List):
        non_intersecting_group = set([post_context_id])
        state_set              = StateSetDB[post_context_id]
        for other_post_context_id in islice(AllPostContextID_List, i + 1, None):
            other_state_set = StateSetDB[other_post_context_id]
            if state_set.isdisjoint(other_state_set):
                non_intersecting_group.add(other_post_context_id)
        if len(non_intersecting_group) > 1:
            if non_intersecting_group not in result:
                result.append(non_intersecting_group)

    # NOTE: A non-intersecting set of size < 2 does not make any statement.
    #       At least, there must be two elements, so that this means 'A is 
    #       equivalent to B'. Thus, filter anything of size < 2.
    return result
            


