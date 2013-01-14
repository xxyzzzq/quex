import quex.engine.state_machine.algorithm.beautifier as     beautifier
import quex.engine.state_machine.index                as     index
from   quex.engine.state_machine.core                 import State, StateMachine
from   quex.engine.misc.tree_walker                   import TreeWalker
from   quex.engine.tools                              import r_enumerate
from   quex.blackboard import E_StateIndices

from   copy import deepcopy
import sys

def do(SM_A, SM_B):
    """Cut:

       Let SM_A match the set of lexemes LA and SM_B match the set 
       of lexemes LB. Then, the 'cut' operation 

                      SM_C = cut(SM_A, SM_B)

       results in a state machine SM_C, matches all lexemes of LA
       except for those that start with a lexeme from LB.

    (C) 2013 Frank-Rene Schaefer
    """
    cutter = Cut(SM_A, SM_B)
    cutter.do((SM_A.init_state_index, SM_B.init_state_index))

    # Delete orphaned states in result
    cutter.result.delete_orphaned_states()

    # Get propper state indices for result
    return beautifier.do(cutter.result)

class Cut(TreeWalker):
    def __init__(self, SM_A, SM_B):
        self.original = SM_A
        self.cutter   = SM_B
        self.result   = StateMachine()
        self.state_db = {}

        self.path     = []
        TreeWalker.__init__(self)

    def get_state(self, Args):
        state_index = index.map_state_combination_to_index(Args)
        state = self.state_db.get(state_index)
        if state is None:
            a_state_index, b_state_index = Args
            if b_state_index != E_StateIndices.NONE:
                acceptance_f = False
            else:
                acceptance_f = self.original.states[Args[0]].is_acceptance()
            
            state = State(AcceptanceF=acceptance_f)
            self.result.states[state_index] = state

        print "#Args:", Args
        print "#get state:", state
        return state

    def check_for_redundant_loop(self, Args):
        if Args not in self.path:
            return False

        # Find alst occurence of 'Args' in path
        for i, info in r_enumerate(self.path):
            if info == Args:
                break
        else:
            return False
        print "#i:", i, self.path[0:i]

        # Find last but one occurence of 'Args' in path
        for k, info in r_enumerate(self.path[0: i]):
            if info == Args:
                break
        else:
            return False
        print "#k:", k, self.path[0:k]

        # Index where 'Args' would occur: 'len(self.path)'
        if i - k != len(self.path) - i:
            return False

        print "#elm:   ", Args
        print "#path   ", self.path
        print "#path I ", self.path[k:i]
        print "#path II", self.path[i:]
        return self.path[k:i] == self.path[i:]

        assert False, "If Args in self.path; then there must be an index for 'Args' in self.path"


    def on_enter(self, Args):
        print "#self.path:", self.path
        if self.check_for_redundant_loop(Args):
            return None

        a_state_index, b_state_index = Args
        self.path.append((a_state_index, b_state_index))

        state = self.get_state(Args)

        a_tm = self.original.states[a_state_index].transitions().get_map()

        if b_state_index == E_StateIndices.NONE:
            # A has a free-pass
            for a_ti, a_trigger_set in a_tm.iteritems():
                target_index = index.map_state_combination_to_index((a_ti, E_StateIndices.NONE))
                state.add_transition(a_trigger_set, target_index) 
            sub_node_list = [ (a_ti, E_StateIndices.NONE) for a_ti in a_tm.iterkeys() ]

        else:
            b_tm = self.cutter.states[b_state_index].transitions().get_map()
            sub_node_list = []
            for a_ti, a_trigger_set in a_tm.iteritems():
                remainder = a_trigger_set.clone()
                for b_ti, b_trigger_set in b_tm.iteritems():
                    in_a_not_in_b = a_trigger_set.difference(b_trigger_set)
                    if not in_a_not_in_b.is_empty(): continue
                    remainder.subtract(in_a_not_in_b)
                    target_index = index.map_state_combination_to_index((a_ti, b_ti))
                    state.add_transition(in_a_not_in_b, target_index)
                    sub_node_list.append((a_ti, b_ti))

                if not remainder.is_empty():
                    target_index = index.map_state_combination_to_index((a_ti, E_StateIndices.NONE))
                    state.transitions().add_transition(remainder, target_index)
                    sub_node_list.append((a_ti, E_StateIndices.NONE))
                elif remainder.is_equal(a_trigger_set):
                    # Untouched --> no correspondent relation in 'B'. Thus we can start
                    # from here.
                    target_index = index.map_state_combination_to_index((a_ti, E_StateIndices.NONE))
                    self.result.get_init_state().add_epsilon_target_state(target_index)

        return sub_node_list

    def on_finished(self, Node):
        self.path.pop()
