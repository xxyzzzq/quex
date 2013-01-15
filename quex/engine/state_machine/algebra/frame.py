import quex.engine.state_machine.algorithm.beautifier as     beautifier
import quex.engine.state_machine.algebra.inverse      as     inverse
import quex.engine.state_machine.index                as     index
from   quex.engine.state_machine.core                 import State, StateMachine
from   quex.engine.misc.tree_walker                   import TreeWalker
from   quex.engine.tools                              import r_enumerate
from   quex.blackboard import E_StateIndices

from   copy import deepcopy
import sys

def do(SM_A, SM_B):
    """Frame:

    Let SM_A match the set of lexemes LA and SM_B match the set of lexemes LB.
    Then, the 'frame' operation 

                           SM_C = frame(SM_A, SM_B)

    results in a state machine SM_C, that matches all lexemes of LA if they are
    substrings of lexemes in LB.

    In this sense, 'SM_B' defines a frame for 'SM_A'.

    NOTE: There is a symmetry relation to 'cut': 
    
          frame(A, B) == cut(A, switched_acceptance(B))

    (C) 2013 Frank-Rene Schaefer
    """
    admissible_sm = SM_B
    print "#SM_A", SM_A.get_string(NormalizeF=False)
    print "#adm:", admissible_sm.get_string(NormalizeF=False)
    cutter = WalkAlong(SM_A, admissible_sm)
    cutter.do((SM_A.init_state_index, admissible_sm.init_state_index))

    # Delete orphaned and hopeless states in result
    ## print "#result.before:", cutter.result
    cutter.result.clean_up()
    ## print "#result.after:", cutter.result

    # Get propper state indices for result
    return beautifier.do(cutter.result)

class WalkAlong(TreeWalker):
    def __init__(self, SM_A, SM_B):
        self.original   = SM_A
        self.admissible = SM_B


        self.result   = StateMachine(InitStateIndex = index.map_state_combination_to_index((SM_A.init_state_index, 
                                                                                            SM_B.init_state_index)), 
                                     InitState      = self.get_state_core(SM_A.init_state_index, 
                                                                          SM_B.init_state_index))
        self.state_db = {}

        self.path     = []
        TreeWalker.__init__(self)

    def on_enter(self, Args):
        ## print "#self.path:", self.path
        if self.check_for_redundant_loop(Args):
            return None

        a_state_index, b_state_index = Args
        self.path.append((a_state_index, b_state_index))

        state = self.get_state(Args)

        a_tm = self.original.states[a_state_index].transitions().get_map()
        b_tm = self.admissible.states[b_state_index].transitions().get_map()
        sub_node_list = []
        for a_ti, a_trigger_set in a_tm.iteritems():
            remainder = a_trigger_set.clone()
            for b_ti, b_trigger_set in b_tm.iteritems():
                intersection = a_trigger_set.intersection(b_trigger_set)
                if intersection.is_empty(): continue
                target_index = index.map_state_combination_to_index((a_ti, b_ti))
                ## print "#transition from: %i -- %s --> %i" % \
                ##      (index.map_state_combination_to_index((a_ti, b_ti)),
                ##       intersection, 
                ##       target_index)
                state.add_transition(intersection, target_index)
                sub_node_list.append((a_ti, b_ti))

        return sub_node_list

    def on_finished(self, Node):
        self.path.pop()

    def get_state_core(self, AStateIndex, BStateIndex):
        acceptance_f =     self.original.states[AStateIndex].is_acceptance() \
                       and self.admissible.states[BStateIndex].is_acceptance()
        
        return State(AcceptanceF=acceptance_f)

    def get_state(self, Args):
        state_index = index.map_state_combination_to_index(Args)
        state       = self.state_db.get(state_index)
        if state is None:
            a_state_index, b_state_index = Args
            state = self.get_state_core(a_state_index, b_state_index)
            self.result.states[state_index] = state
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
        ## print "#i:", i, self.path[0:i]

        # Find last but one occurence of 'Args' in path
        for k, info in r_enumerate(self.path[0: i]):
            if info == Args:
                break
        else:
            return False
        ## print "#k:", k, self.path[0:k]

        # Index where 'Args' would occur: 'len(self.path)'
        if i - k != len(self.path) - i:
            return False

        ## print "#elm:   ", Args
        ## print "#path   ", self.path
        ## print "#path I ", self.path[k:i]
        ## print "#path II", self.path[i:]
        return self.path[k:i] == self.path[i:]

        assert False, "If Args in self.path; then there must be an index for 'Args' in self.path"


