"""Identify 'barren' transitions that can be nested in a state.

   -- find 'simple transitions'.

   -- arrange the paths in a tree data structure (dictionary)
"""

class TreeNode:
    def __init__(self, FirstTarget, FirstTriggerSet):
        self.parent_state_index        = ParentStateIndex
        self.parent_tm                 = ParentTM
        self.child_db[ChildStateIndex] = ChildTM

        self.parent_catch_tm     = []
        self.children_common_tm  = []
        self.children_private_tm = {}

    def append(self, ChildStateIndex, ChildTM):
        self.child_db[ChildStateIndex] = ChildTM

    def child_list(self):
        return self.child_db.items()
        
    def freeze_this(self, ChildIndexList, ParentCatchTM, ChildrenCommonTM, ChildrenPrivateTM):
        for child_index in self.child_list.keys(): # NOT 'iterkeys()' we change the dictionary!
            if child_index not in ChildIndexList:
                del self.child_db[child_index]

        self.parent_catch_tm     = ParentCatchTM
        self.children_common_tm  = ChildrenCommonTM
        self.children_private_tm = ChildrenPrivateTM

def do(SM):

    # Build database about what state has what 'barren child transitions'
    child_db = __build_child_db(SM, LimitEffort=2.0) # DONE

    # Take only children that can be combined nicely, i.e. that are either
    # very small or have a lot in common.
    for node in child_db.itervalues():
        __build_best_construction(node)

    return child_db

def __build_child_db(SM, LimitEffort):
    """Build a database about 'child states' that are reached from their
       parent state through a 'barren transition', i.e. a transition that
       requires only view comparisons.

              child_db:  state_index --> list of child state indices

       The number of comparisons is limited by the 'LimitEffort'.
    """
    child_db = {}
    for state_index, state in SM.states.iteritems():
        for target_index, trigger_set in state.transitions().get_map().iteritems():
            if effort(trigger_set) < LimitEffort:
                node = child_db.get(state_index)
                if node == None: child_db[target_index] = TreeNode(state_index, target_index, trigger_set, trigger_map)
                else:            node.append(target_index)

    return child_db


def __construction_code(ParentTM, ChildTM_List):
    # Delete transitions to children from ParentTM
    parent_tm = copy(ParentTM)
    for child_index in ChildList:
        del parent_tm[child_index]
    
    total_common_tm         = __get_common_tm([parent_tm] + ChildTM_List)
    children_only_common_tm = __get_common_tm(ChildTM_List)

    parent_catch_tm         = __get_common_tm([total_common_tm, children_only_common_tm])
    children_common_tm      = __difference(children_only_common_tm, parent_catch_tm)

    children_private_tm_db  = {}

    cost =   effort(parent_catch_tm) \
           + effort(children_common_tm)
    for child_tm in ChildTM_List:
        private_tm  = __difference(child_tm, children_only_common_tm)
        cost       += effort(private_tm)
        children_private_tm_db[child_index] = private_tm

    return cost, (total_common_tm, children_only_common_tm, children_private_tm_db)

def __build_best_construction(SM, parent_tm, node):
    # Start with all children present
    child_list = node.child_list()
    # Loop over exclusion. Always remove the 'worst' child and store
    # consider the cost of the 'construction'. Keep track of the best
    # construction in 'best_cost' and 'best_construction'.
    best_cost         = 1e37
    best_construction = None
    length = len(child_list)
    while length != 1:
        # Iterate over all children and determine the one that causes the highest cost
        best_tmp_cost         = 1e37
        best_tmp_construction = None
        best_tmp_child_list   = None
        for i in range(length):
            tmp_child_list = set(child_list)
            del tmp_child_set[i]
            cost, construction = __get_construction(ParentTM, tmp_child_list)
            if cost < best_tmp_cost:
                best_tmp_cost         = cost
                best_tmp_construction = construction
                best_tmp_child_list   = tmp_child_list

        # For the best child combination, check whether it competes with previous combinations
        if best_tmp_cost < best_cost:
            best_cost         = best_tmp_cost
            best_construction = best_tmp_construction
            best_child_list   = best_tmp_child_list

    # Tell the node, that may be some children are remove from the barren
    # transition. Also, tell the node about the code construction details.
    node.freeze_this(best_child_list, best_construction)

