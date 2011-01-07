"""Identify 'barren' transitions that can be nested in a state.

   -- find 'simple transitions'.

   -- arrange the paths in a tree data structure (dictionary)
"""

class TreeNode:
    def __init__(self, FirstTarget, FirstTriggerSet):
        self.barren_trigger_map[FirstTarget] = FirstTriggerSet

        self.common_trigger_set = NumberSet()

    def append(self, Target, TriggerSet):
        assert self.barren_trigger_map.has_key(Target) == False
        self.barren_trigger_map[Target] = TriggerSet
        

def do(SM):

    # Build database about what state has what 'barren child transitions'
    child_db = __build_child_db(SM, LimitEffort=2.0)

    # Take only childs that can be combined nicely, i.e. that are either
    # very small or have a lot in common.
    for node in child_db.itervalues():
        __filter_childs(node)

    # Setup common trigger maps and private trigger maps
    for node in child_db.itervalues():
        __setup_trigger_maps(node)

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
                if node == None: child_db[target_index] = TreeNode(target_index, trigger_set, trigger_map)
                else:            node.append(target_index)

    return child_db

def __filter_childs(SM, node):

    common_tm = __find_common_tm(SM, TreeNode.state_index_list())

    effort_common_tm = effort(common_tm)

    effort_common_tm    = effort(common_tm)
    parent_remainder_tm = __parent_minus_transition_to_childs(child_index_list)

    effort_common_tm_vs_child_list.append((effort_common_tm_min * len(child_index_list), 
                                          None, 
                                          parent_remainder_tm))

    effort_common_tm_vs_child_list = []

    while len(child_index_list) != 0:
        common_effort_tm_min = 1e37
        child_index_of_min   = -1

        for child_index in child_list:
            common_tm = __get_common_trigger_map(parent_remainder_tm, child_tm_list)
            effort_common_tm = effort(common_tm)
            if effort_common_tm < effort_common_tm_min:
                effort_common_tm_min = effort_common_tm
                child_index_of_min   = child_index
        
        parent_remainder_tm  = __parent_minus_transition_to_childs(child_index_list)
        effort_common_tm_vs_child_list.append((effort_common_tm_min * len(child_index_list), 
                                              child_index_min, 
                                              parent_remainder_tm))
        # Remove worst child, and computer further
        node.remove(child_index_min)

    effort_common_tm_vs_child_list.sort(reverse=True)
    node.set_child_list(effort_common_tm_vs_child_list[0][1])

def __setup_trigger_maps(node):

    common_child_tm = __get_common_trigger_map(None, child_tm_list)

    for child in node.child_list:
        private_tm = __get_private_tm(node.common_child_tm)

        node.private_child_tm[child_index] = private_tm

    # What is common between parent and child can be done by the parent
    node.parent_child_common    = __get_common_trigger_map(parent_tm, common_child_tm)
    node.parent_private_tm      = __get_private_tm(node.parent_child_common, parent_tm)
    node.remaining_child_common = __get_private_tm(parent_child_common, remaining_child_common)
