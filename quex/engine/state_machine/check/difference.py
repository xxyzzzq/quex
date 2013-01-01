from quex.engine.misc.tree_walker    import TreeWalker
import quex.engine.state_machine.index as     index
from   quex.engine.state_machine.core  import StateMachine
import quex.engine.state_machine.algorithm.beautifier  as beautifier

def do(A, B): 
    """Computes the 'difference' between two state machines. That is, 
    for two state machines A and B it holds for S = difference(A, B)

        S matches all lexemes that A matches but not those matched by B.

    """
    processor = Processor(A, B)
    processor.do([(processor.result.init_state_index, A.init_state_index, B.init_state_index)])

    processor.result.delete_orphaned_states()
    return beautifier.do(processor.result)

class Processor(TreeWalker):
    """Dive until an acceptance state in A is reached while walking along B. 
    Note down the path and the trigger set in B that leads along the path.
    Once an acceptance state is reached, delete the path from B in A.
    """
    def __init__(self, A, B):
        self.a_sm   = A 
        self.b_sm   = B
        self.result = StateMachine()
        self.b_path   = []
        # Detect loops in both state machines by target state indices that
        # correspond to (state_a_index, state_b_index).
        self.done_set = set([])

        # The 'state_index' for not in 'b' must be unique. If we subtract from 
        # 'A' a second time a new wildcard index is required.
        self.wildcard = index.get()

        TreeWalker.__init__(self)

    def on_enter(self, Args):
        result_index, a_state_index, b_state_index = Args
        self.done_set.add(result_index)

        a_state       = self.a_sm.states[a_state_index]
        a_trigger_map = a_state.transitions().get_map().iteritems()

        if a_state.is_acceptance():
            self.result.delete_path(self.b_path)

        sub_node_list = []
        b_trigger_map = None # to pass pyflykes -- not implemented code
     
        for a_target, a_trigger_set in a_trigger_map:
            intersection_f = True
            for b_target, b_trigger_set in b_trigger_map:
                if not a_trigger_set.has_intersection(b_trigger_set):
                    continue
                intersection_f = True

                difference = a_trigger_set.difference(b_trigger_set)
                if difference.is_empty(): # Connection to 'a_target' is cut.
                    break

                result_target_index = index.map_state_combination_to_index((a_target, b_target))

                self.result.add_transition(result_index, difference, result_target_index, 
                                           AcceptanceF=self.a_sm.states[a_target].is_acceptance())

                if result_target_index not in self.done_set:
                    sub_node_list.append((result_target_index, a_target, b_target))
            
            if not intersection_f:
                result_target_index = index.map_state_combination_to_index((a_target, self.wildcard))
                self.result.add_transition(result_index, a_trigger_set, result_target_index, 
                                           AcceptanceF=self.a_sm.states[a_target].is_acceptance())
                if result_target_index not in self.done_set:
                    sub_node_list.append((result_target_index, a_target, self.wildcard))

            return sub_node_list

    def on_finished(self, Args):
        pass

