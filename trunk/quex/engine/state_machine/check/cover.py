from quex.engine.state_machine.core import StateMachine
from quex.engine.misc.enum          import Enum 
from quex.engine.misc.tree_walker   import TreeWalker

def do(A, B): 
    """Check whether 'B' can outrun 'A' even though 'A' has matched.
       This means, that 'B' might win against 'A' even if it had a 
       lower priority, because it matches a lexeme that starts with 
       what 'A' matches, but is longer.

       RETURNS: True, if 'B' might outrun a lexeme that matches 'A'.
                False, 'B' can never outrun a lexeme matched by 'A'.
       ________________________________________________________________________

       ASSUMPTION: 
       
       It is assumed, that both machines are HOPCROFT-MINIMIZED! That is,
       there MUST NOT BE A SUPERFLOUS FORK such as in

                      .-- 'a'--->( 2 )-- 'c' --.
                     /                          \
          ... --->( 1 )                        ( 4 )--- ...
                     \                          /
                      '-- 'b'--->( 3 )-- 'c' --'

       which needs to be minized to

          ... --->( 1 )--- 'a' | 'b' --->( 2 )-- 'c' --->( 4 )--- ...
    """
    collector = TunnelToAcceptanceWalker(A, B)
    collector.do([(A.init_state_index, B.init_state_index)])
    if len(collector.result) == 0:
        return False
    detector = DetectTunnelBreakOutWalker(B, A)
    detector.do(collector.result)
    return walker.result

class TunnelWalker(TreeWalker):
    """Step 1: 
    
       This 'walker' collects all acceptance states in 'A' which can be
       reached by a path that is also walkable in 'B'.
    """
    def __init__(self, A, B):
        self.a_sm     = A
        self.b_am     = B
        self.result   = False
        self.done_set = set()
        TreeWalker.__init__(self)

    def on_enter(self, Args):
        # (*) Update the information about the 'trace of acceptances'
        A_StateIndex, B_StateIndex = Args
        if A_StateIndex in self.done_set: return None
        else:                             self.done_set.add(A_StateIndex)
        A_State = self.a_sm.states[A_StateIndex]

        # Follow the path of common trigger sets
        if A_State.is_acceptance():
            self.on_acceptance_state_reached(A_StateIndex, B_StateIndex)
            return None

        B_State       = self.b_sm.states[B_StateIndex]
        A_TriggerMap  = A_State.transitions().get_map()
        B_TriggerMap  = B_State.transitions().get_map()
        sub_node_list = []
        for a_target, a_trigger_set in A_TriggerMap.iteritems():
            for b_target, b_trigger_set in B_TriggerMap.iteritems():
                if not b_trigger_set.is_superset(a_trigger_set): continue
                # The transition in 'A' is covered by a transition in 'B'.
                sub_node_list.append( (a_target, b_target) )
                break
            else:
                # There is no transition in 'B' that covers the step in 'A'
                # => B does not cover the given path in 'A'. 
                # => Further investigation of the current path not necessary.
                self.on_not_covered()
                return None

        # (*) Recurse to all sub nodes
        return sub_node_list

    def on_finished(self, Args):
        pass

class TunnelToAcceptanceWalker(TunnelWalker):
    def __init__(self, SM_A, SM_B):
        TunnelWalker.__init__(self, SM_A, SM_B)
        self.result = []

    def on_acceptance_state_reached(self, A_StateIndex, B_StateIndex):
        self.result.append( (B_StateIndex, A_StateIndex) )

    def on_not_covered(self):
        pass

class DetectTunnelBreakOutWalker(TunnelWalker):
    def __init__(self, SM_A, SM_B):
        TunnelWalker.__init__(self, SM_A, SM_B)
        self.result = False

    def on_acceptance_state_reached(self, A_StateIndex, B_StateIndex):
        self.result  = True
        self.abort_f = True

    def on_not_covered(self):
        self.result  = True
        self.abort_f = True
