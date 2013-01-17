import quex.engine.state_machine.algorithm.beautifier as     beautifier
import quex.engine.state_machine.check.special        as     special
import quex.engine.state_machine.algebra.inverse      as     inverse
import quex.engine.state_machine.index                as     index
from   quex.engine.state_machine.core                 import State, StateMachine
from   quex.engine.misc.tree_walker                   import TreeWalker
from   quex.engine.tools                              import r_enumerate
from   quex.blackboard import E_StateIndices

from   copy import deepcopy
import sys

def do(SM_A, SM_B):
    """Cut:

    Let SM_A match the set of lexemes LA and SM_B match the set of lexemes LB.
    Then, the 'cut' operation 

                           SM_C = cut(SM_A, SM_B)

    results in a state machine SM_C, matches all lexemes of LA except for those
    that start with a lexeme from LB.

    NOTE: There is a symmetry relation to 'frame': 
    
          frame(A, B) == cut(A, tame(inverse((B)))

    EXAMPLE 1: 

          cut([0-9]+, [0-9]) = \None

    That is where '[0-9]+' required at least one character in [0-9], the 
    cut version does not allow lexemes with one [0-9]. The result is a
    repetition of at least two characters in [0-9].

    EXAMPLE 2: 

          cut(1(2?), 12) = 1

    Because the lexeme "12" is not to be matched by the result. The lexeme
    "1", though, does not start with "12". Thus, it remains.

    EXAMPLE 2: 

          cut([a-z]+, print) = all identifiers except 'print'

    (C) 2013 Frank-Rene Schaefer
    """
    cutter = WalkAlong(SM_A, SM_B)
    if SM_B.get_init_state().is_acceptance():
        return special.get_none()

    ## print "#SM_A", SM_A.get_string(NormalizeF=False)
    ## print "#SM_B", SM_B.get_string(NormalizeF=False)

    cutter.do((SM_A.init_state_index, SM_B.init_state_index))

    # Delete orphaned and hopeless states in result
    cutter.result.clean_up()

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
        # print "#self.path:", self.path
        if Args in self.path: # self.check_for_redundant_loop(Args):
            return None

        a_state_index, b_state_index = Args
        self.path.append((a_state_index, b_state_index))

        state = self.get_state(Args)

        sub_node_list = []

        a_tm = self.original.states[a_state_index].transitions().get_map()
        if b_state_index == E_StateIndices.NONE:
            # Everything 'A' does is admissible. 'B' is not involved.
            for a_ti, a_trigger_set in a_tm.iteritems():
                combi = (a_ti, E_StateIndices.NONE)
                state.add_transition(a_trigger_set, index.map_state_combination_to_index(combi))
                sub_node_list.append(combi)
            ## print "#0-sub_node_list:", sub_node_list
            return sub_node_list

        b_tm = self.admissible.states[b_state_index].transitions().get_map()
        for a_ti, a_trigger_set in a_tm.iteritems():
            remainder = a_trigger_set.clone()
            for b_ti, b_trigger_set in b_tm.iteritems():
                # If an acceptance state in 'B' is reached, than the lexeme starts
                # with something in 'LB'. Thus, rest of paths is inadmissible.
                if self.admissible.states[b_ti].is_acceptance(): 
                    remainder.subtract(b_trigger_set)
                    continue                                     

                intersection = a_trigger_set.intersection(b_trigger_set)
                ## print "# a: %i -> %i: %s" % (a_state_index, a_ti, a_trigger_set)
                ## print "# b: %i -> %i: %s" % (b_state_index, b_ti, b_trigger_set)
                ## print "# intersection:", intersection
                if intersection.is_empty(): 
                    continue

                combi = (a_ti, b_ti)
                state.add_transition(intersection, index.map_state_combination_to_index(combi))
                sub_node_list.append(combi)

                remainder.subtract(intersection)

            if not remainder.is_empty():
                combi = (a_ti, E_StateIndices.NONE)
                state.add_transition(remainder, index.map_state_combination_to_index(combi))
                sub_node_list.append(combi)

        ## print "#1-sub_node_list:", sub_node_list
        return sub_node_list

    def on_finished(self, Node):
        self.path.pop()

    def get_state_core(self, AStateIndex, BStateIndex):
        acceptance_f = self.original.states[AStateIndex].is_acceptance() 
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


