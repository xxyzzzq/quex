from quex.engine.state_machine.core import StateMachine
from quex.engine.misc.enum          import Enum 
from quex.engine.misc.tree_walker   import TreeWalker

def do(High, Low): 
    """Check whether lower priority pattern 'Low' can outrun by length a 
       pattern 'High' even though 'High' has matched. 
       
       EXAMPLE: High:  print
                Low:   [a-z]+

          If a stream contains "printer", then 'Low' would match even 
          though 'High' could have matched if 'Low' was not there. The
          writer of 'High' might be surprised if he was not aware of 
          'Low'.
       
       RETURNS: True, if 'Low' might outrun a lexeme that matches 'High'.
                False, 'Low' can never outrun a lexeme matched by 'High'.
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
    # Step 1: Find acceptance states which are reached while walking
    #         along paths of 'High' that are also inside 'Low'.
    collector = Step1_Walker(High, Low)
    collector.do([(High.init_state_index, Low.init_state_index)])
    # Result: List of pairs (HighIndex, LowIndex) 
    #         HighIndex = index of acceptance state in 'High' that has been reached.
    #         LowIndex  = index of state in 'Low' that was reached when walking
    #                     along the path to 'HighIndex'.
    if len(collector.result) == 0:
        return False

    # Step 2: Detect paths in Low that divert from High starting from
    #         the acceptance states collected in step 1.
    detector = Step2_Walker(High, Low)
    # Start searching for diversion from the critical acceptance states in High.
    detector.do(collector.result)

    # Result: True  -- if there are paths in Low that divert
    #         False -- if all paths from acceptance states in High are 
    #                  also in Low.

    # RETURN: 
    #
    # True    If there were acceptance states in High that would be reached
    #         by paths that also are feasible in Low; And if Low then 
    #         diverts from those paths, i.e. there are paths in Low which
    #         are not in High.
    #
    # False   Else.
    #
    return walker.result

class Base_TunnelWalker(TreeWalker):
    """Walks along paths of 'A' if they are covered by 'B'. In a sense, it
       walks the paths of 'A' in the tunnels of 'B'.
    
       If an acceptance state of 'A' is reached, then function 
       
                    self.on_acceptance_state_reached(...)

       is executed. Its implemented in the derived class. When a step in 'A'
       is detected that is not covered by 'B', then function 

                    self.on_not_covered()

       is executed which is also implemented in a derived class.
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

class Step1_Walker(Base_TunnelWalker):
    """Find acceptance states of 'High' which are reachable
       by walking along possible paths in 'Low'. 
       
       Use the algorithm provided by 'Base_TunnelWalker' where
       "A = High" and "B = Low".

       -- If an acceptance state in High ('A') is reached, then a pair
          (Low_StateIndex, High_StateIndex) is appended to 'self.result'. 

       Later, Step2_Walker will walk along paths of 'Low' starting 
       from these detected states to see whether it diverts.
    """
    def __init__(self, High, Low):
        Base_TunnelWalker.__init__(self, SM_A=High, SM_B=Low)
        self.result = []

    def on_acceptance_state_reached(self, High_StateIndex, Low_StateIndex):
        # A = High, B = Low
        self.result.append( (Low_StateIndex, High_StateIndex) )

    def on_not_covered(self):
        pass

class Step2_Walker(Base_TunnelWalker):
    """Starts at the acceptance states of 'High' that can be walked
       along in 'Low'. It then checks whether 'Low' can walk paths from
       there which are not covered by 'High'.

       Use the algorithm provided by 'Base_TunnelWalker' where
       "A = Low" and "B = High".

       -- If an acceptance state in Low ('A') is reached while High does
          not accept, then Low has outrun High after match. 
          
          Set 'result = True' and abort.

       -- If a step in Low is detected which is not feasible in High, 
          then Low has outrun High after match.

          Set 'result = True' and abort.
    """
    def __init__(self, High, Low):
        Base_TunnelWalker.__init__(self, SM_A=Low, SM_B=High)
        self.result = False

    def on_acceptance_state_reached(self, Low_StateIndex, High_StateIndex):
        # A = Low, B = High
        if self.sm_b[High_StateIndex].is_acceptance(): 
            return # High still wins, continue
        self.result  = True
        self.abort_f = True

    def on_not_covered(self):
        self.result  = True
        self.abort_f = True
