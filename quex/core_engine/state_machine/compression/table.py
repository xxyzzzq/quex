# PURPOSE: Optionally, a state machine can be transformed 
#          into an optimized table. That is, the boundaries
#          of the intervals are connected to table entries
#          that indicate state transitions. 
# EXAMPLE:
#                           
#        ,-----<-----------( [a-z0] )-----<------. 
#       /                                         \ 
#    ( 0 )--( [a-z][A-Z] )-->( 1 )--( [_0-9] )-->( 2 )
#       \                                         /
#        `----->-----------( [45] )------->------'
#
# SIMPLIFIED TABLE:
#
#               ( 0 )    ( 1 )     ( 2 )
#    '0'                   2         0
#    '1'                   2
#    '2'-'3'               2
#    '4'-'5'      2        2
#    '6'-'9'               2
#    '_'                   2
#    'a'-'z'      1                  0
#    'A'-'Z'      1                  0
import sys
# Parameters:
#    NC_t = number of comparisons in the table
#    NS_t = number of states in the table
#
#    NC(state) = number of comparisons of original table
#
#    NAC(state0, state1) = number of additional boundaries
#                          if state0 is combined with state1
def TEST_get_NAC_matrix(sm):
    trigger_map_db = {}
    for index, state in sm.states.items():
        trigger_map = state.transitions().get_trigger_map()
        trigger_map_db[index] = trigger_map

    fh = open("/tmp/nac.dat", "w")
    state_index_list = sm.states.keys()
    L                = len(state_index_list)
    for i in range(L):
        state_index_0 = state_index_list[i]
        trigger_map_0 = trigger_map_db[state_index_0]
        for k in range(i + 1, L):
            state_index_1 = state_index_list[k]
            trigger_map_1 = trigger_map_db[state_index_1]
            bn, nst, net = get_metric(trigger_map_0, trigger_map_1)
            sum    = len(trigger_map_0) + len(trigger_map_1)
            saving = sum - bn
            ratio  = 0.0
            if sum != 0: ratio = 100.0 * saving / float(sum)

            fh.write("%i %.2f %i %i %i %i %i %i\n" % (abs(len(trigger_map_0) - len(trigger_map_1)), ratio, saving, sum, nst, net, i, k))
    fh.close()

def get_metric(TriggerMap0, TriggerMap1):
    """Assume that interval list 0 and 1 are sorted."""
    Li = len(TriggerMap0)
    Lk = len(TriggerMap1)
    # Count the number of additional intervals if list 0 is combined with list 1
    # Each intersection requires the setup of new intervals, e.g.
    #
    #          |----------------|
    #               |---------------|
    #
    # Requires to setup three intervals in order to cover all cases propperly: 
    #
    #          |----|-----------|---|
    #
    # Thus, the additional_n += 2
    same_target_list       = {}
    equivalent_target_list = []

    i = 0 # iterator over interval list 0
    k = 0 # iterator over interval list 1
    assert TriggerMap0[0][0].begin == -sys.maxint
    assert TriggerMap1[0][0].begin == -sys.maxint

    focus_line     = - sys.maxint
    border_count_n = 0

    # -- intervals in trigger map are always adjacent, so the '.end'
    #    member is not required.
    while i != Li and k != Lk:
        i_trigger = TriggerMap0[i]
        k_trigger = TriggerMap1[k]

        i_begin   = i_trigger[0].begin
        i_target  = i_trigger[1]

        k_begin   = k_trigger[0].begin
        k_target  = k_trigger[1]

        # Step to the next *lowest* border, i.e. increment the 
        # interval line index with the lowest '.begin'. For example:
        # 
        #         0   1 2  3 4 5  6   7
        #     i   |     |      |  |   |
        #     k   |   |    | |        |
        #         :   : :  : : :  :   :   (6 intervals, 6 borders)
        #
        #                         i_begin:     k_begin:
        # Does:  (1) ++i, ++k -->    2            1
        #        (2) ++k      -->    2            3
        #        (3) ++i      -->    5            3
        #        (4) ++k      -->    5            4
        #        (5) ++k      -->    5            6
        #        (6) ++i      -->    6            7
        #        (6) ++i      -->    7            7
        if   i_begin == k_begin:  i += 1; k += 1;
        elif i_begin < k_begin:   i += 1;
        else:                     k += 1;

        if i_target == k_target: 
            same_target_list[i_target] = True

        else:
            pair = (i_target, k_target)
            if pair not in equivalent_target_list:
                equivalent_target_list.append(pair)

        border_count_n += 1

    border_count_n += (Li - i) + (Lk - k)

    return border_count_n, \
           len(same_target_list), \
           len(equivalent_target_list)


def xxxx():
    while 1 + 1 == 2:
        # HERE: Intersection detected: 
        #        i_begin == k_begin < i_end == k_end --> +/-0, break      (a)
        #        i_begin == k_begin < i_end <  k_end --> +1,   break      (b)
        #        i_begin == k_begin < k_end <  i_end --> +1,   continue   (c)
        #        k_begin < i_begin  < i_end == k_end --> +1,   break      (d)
        #        i_begin < k_begin  < i_end == k_end --> +1,   break      (e)
        #        i_begin < k_begin  < k_end <  i_end --> +2,   continue   (f)
        #        k_begin < i_begin  < k_end <  i_end --> +2,   continue   (g)
        #        i_begin < k_begin  < i_end <  k_end --> +2,   break      (h)
        #        k_begin < i_begin  < i_end <  k_end --> +2,   break      (i)
        register(i_target, k_target)
        if i_begin == k_begin:
            if i_end == k_end: break # (a) 
            additional_n += 1
            if i_end < k_end:  break              # (b)
            else:              k += 1; continue   # (c)
        elif i_end == k_end:
            additional_n += 1; break              # (d) (e)
        elif k_end < i_end:
            additional_n += 2; k += 1; continue   # (f) (g)
        else:
            additional_n += 2; break              # (h) (i)

        if k == L1: break

    return additional_n  
        
    
