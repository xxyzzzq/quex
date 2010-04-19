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
from copy import copy

class Combination:
    def __init__(self, TriggerMapA, TriggerMapB):
        self.__trigger_map                 = {}
        self.__target_index_combination_db = {}

    def __getitem__(self, Index):
        return self.__trigger_map[Index]

    def __len__(self):
        return len(self.__trigger_map)

# Parameters:
#    NC_t = number of comparisons in the table
#    NS_t = number of states in the table
#
#    NC(state) = number of comparisons of original table
#
#    NAC(state0, state1) = number of additional boundaries
#                          if state0 is combined with state1
def delta_cost(SizeA, SizeB, N, CombinedBorderN, TargetStateCombinationN):
    """BEFORE: 
                Cost0 = (SizeA + SizeB) * CI

                where CI is the average 'identification cost', i.e. the
                cose for branching through the 'if/else' statements of 
                the transition map, plus the cost for a goto.

       AFTER:
                Cost1 =   CombinedBorderN * CI
                        + TargetStateCombinationN * N * CR

                where N is the number of combined states.
                      CR is the cost for routing, i.e. jumping to
                         the correct target state depending on template.

       THUS:    
                Delta = Cost0 - Cost1

                      = ( SizeA + SizeB - CombinedBorderN ) * CI
                         - TargetStateCombinationN * N * CR

                Delta shall be a 'measure', so there is no loss of 
                information if we devide by a constant, e.g. CR. Thus

                Delta = CX * (SizeA + SizeB - CombinedBorderN)
                        - TargetStateCombinationN * N

                Where CX = CI/CR. The constants CI and CR where place-
                holders anyway for something that can only be assumed.
                Now, CI and CR can be replaced by a single heuristic
                value CX.

    """
    return (SizeA + SizeB - CombinedBorderN) - TargetStateCombinationN * 2


class TriggerMapDB:
    def __init__(self, SM):
        assert SM.__class__.__name__ == "StateMachine"

        # (1) Get the trigger maps of all states of the state machine
        self.__db = {}
        for index, state in sm.states.items():
            trigger_map = state.transitions().get_trigger_map()
            # Dead ends, cannot be part of the code generation
            if trigger_map == []: continue
            self.__db[index] = trigger_map

        self.__metric_cache = {}

    def get_best_matching_pair(self):
        """Determines the two trigger maps that are closest to each
           other. The consideration includes the trigger maps of
           combined trigger maps. Thus this function supports the
           clustering of the best trigger maps into combined trigger
           maps.
        """

        best_i = None 
        best_k = None

        index_list = self.__db.keys()
        L          = len(index_list)
        max_gain   = -1
        for i in range(L):
            TriggerMapA = index_list[i]
            SizeA       = len(TriggerMapA)

            for k in range(i + 1, L):
                TriggerMapB = index_list[k]

                delta_cost = self.metric_cache_get(i, k)
                if delta_cost == None:
                    bn, net    = get_metric(TriggerMapA, TriggerMapB)
                    delta_cost = delta_cost(SizeA, len(TriggerMapB), 2, bn, len(net))
                    self.metric_cache_set(i, k, delta_cost)

                if delta_cost > max_gain: 
                    max_gain  = delta_cost
                    best_i = i; best_k = k;

        return best_i,  best_k

    def metric_cache_get(self, I, K):
        # Return 'None' if element '(I, K)' is not in cache
        return self.__metric_cache.get(I, {}).get(K)

    def metric_cache_set(self, I, K, Value):
        # Set dictionary[I][K] = Value
        self.__metric_cache.setdefault(I, {})[K] = Value

    def delete_pair(self, I, K):
        del self.__db[I]
        del self.__db[K]

def TEST_get_NAC_matrix(sm):

    db = TriggerMapDB(sm)

    # (2) Build clusters by finding best pairs, until there 
    #     is no meaningful way to build clusters. The elements
    #     of the pair can also be clusters.
    while 1 + 1 == 2:
        i, k = get_best_matching_pair()
        if i == None: break

        # Add new element: The combined pair
        trigger_map_db[new_sm_index()] = Combination(trigger_map[i], trigger_map[k])
        trigger_map_db.delete_pair(i, k) 

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

    assert TriggerMap0[0][0].begin == -sys.maxint
    assert TriggerMap1[0][0].begin == -sys.maxint
    assert TriggerMap0[-1][0].end  == sys.maxint
    assert TriggerMap1[-1][0].end  == sys.maxint

    equivalent_target_list = []
    def __check_targets(T0, T1):
        if T0 == T1: return

        # The 'trigger map' may as well be a combination of trigger maps,
        # thus the 'target' may be a list of targets.
        if type(T0) != list: combination = [T0]
        else:                combination = copy(T0)
        if type(T1) == list: combination.extend(T1)
        else:                combination.append(T1)
        if combination not in equivalent_target_list:
            equivalent_target_list.append(combination)

    i = 0 # iterator over interval list 0
    k = 0 # iterator over interval list 1

    # Intervals in trigger map are always adjacent, so the '.end'
    # member is not required.
    border_count_n = 0
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TriggerMap0[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TriggerMap1[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        __check_targets(i_target, k_target)

        # Step to the next *lowest* border, i.e. increment the 
        # interval line index with the lowest '.end'. For example:
        # 
        #         0   1 2  3 4 5  6   7
        #     i   |     |      |  |   |
        #     k   |   |    | |        |
        #         :   : :  : : :  :   :   (6 intervals, 6 borders)
        #
        #                         i_end:     k_end:
        # Does:  (1) ++i, ++k -->    2            1
        #        (2) ++k      -->    2            3
        #        (3) ++i      -->    5            3
        #        (4) ++k      -->    5            4
        #        (5) ++k      -->    5            6
        #        (6) ++i      -->    6            7
        #        (6) ++i      -->    7            7
        if   i_end == k_end:  i += 1; k += 1;
        elif i_end < k_end:   i += 1;
        else:                 k += 1;

        border_count_n += 1

    # Treat the last trigger interval
    __check_targets(TriggerMap0[-1][1], TriggerMap1[-1][1])

    return border_count_n, \
           equivalent_target_list

def get_combined_trigger_map(TriggerMap0, TriggerMap1):
    Li = len(TriggerMap0)
    Lk = len(TriggerMap1)

    assert TriggerMap0[0][0].begin == -sys.maxint
    assert TriggerMap1[0][0].begin == -sys.maxint
    assert TriggerMap0[-1][0].end  == sys.maxint
    assert TriggerMap1[-1][0].end  == sys.maxint

    equivalent_target_list = []
    def __get_target_index(T0, T1):
        if T0 == T1: return

        # The 'trigger map' may as well be a combination of trigger maps,
        # thus the 'target' may be a list of targets.
        if type(T0) != list: combination = [T0]
        else:                combination = copy(T0)
        if type(T1) == list: combination.extend(T1)
        else:                combination.append(T1)
        if combination not in equivalent_target_list:
            equivalent_target_list.append(combination)

    i = 0 # iterator over interval list 0
    k = 0 # iterator over interval list 1

    # Intervals in trigger map are always adjacent, so the '.end'
    # member is not required.
    trigger_map = []
    while not (i == Li-1 and k == Lk-1):
        i_trigger = TriggerMap0[i]
        i_end     = i_trigger[0].end
        i_target  = i_trigger[1]

        k_trigger = TriggerMap1[k]
        k_end     = k_trigger[0].end
        k_target  = k_trigger[1]

        target_idx = __get_target_index(i_target, k_target)

        trigger_map.append(Interval(prev_end, min(i_end, k_end)), target_idx)

        if   i_end == k_end:  i += 1; k += 1;
        elif i_end < k_end:   i += 1;
        else:                 k += 1;

        border_count_n += 1

    # Treat the last trigger interval
    __check_targets(TriggerMap0[-1][1], TriggerMap1[-1][1])

    return border_count_n, \
           equivalent_target_list
