import sys
from   quex.core_engine.interval_handling        import NumberSet, Interval

class Transition:
    # Information about a transition:
    #
    #      ----( trigger ? )----[ success flag/or not ]---> target state
    #
    # A transition is activated by a trigger, i.e. a character comes in that is 
    # in the set of triggering characters. Then an action is performed: eating
    # the character (moving on to the next) not not (leaving character for further
    # transitions to trigger). Finally, the target state is entered.
    #
    def __init__(self, TriggerSet, TargetStateIdx):
        assert TriggerSet.__class__ == NumberSet
        assert type(TargetStateIdx) == long
       
        # set of characters that trigger the transition 
        self.trigger_set        = TriggerSet
        # target state index (where one lands if transition is performed)
        self.target_state_index = TargetStateIdx

    def get_string(self, StateIndexMap=None):
        """Return a string representation of the Transition."""
        trigger_str = self.trigger_set.get_utf8_string()
        if StateIndexMap == None:
            target_str  = "%05i" % self.target_state_index
        else:
            target_str  = "%05i" % StateIndexMap[self.target_state_index]
            
        return "== %s ==> %s" % (trigger_str, target_str)

    def get_graphviz_string(self, StateIndexMap=None):
        trigger_str = self.trigger_set.get_utf8_string()
        if StateIndexMap == None:
            target_str  = "%i" % self.target_state_index
        else:
            target_str  = "%i" % StateIndexMap[self.target_state_index]
            
        return "-> %s [label =\"%s\"];\n" % (target_str, trigger_str.replace("\"", ""))

 
    def set(self, TriggerSet=None, TargetIdx=None):
        if TriggerSet != None:  self.trigger_set  = TriggerSet
        elif TargetIdx != None: self.target_index = TargetIdx

class EpsilonTransition:
    """Information about the epsilon transition of a state. Note, that the
       function 'StateInfo::add_transition(...) computes the trigger set of the
       epsilon transition as the remaining set where nothing else triggers.
       
       target_state_indices = []  => no epsilon transition, but the trigger
                                     set contains still the remaining triggers 
                                     of a state transition.
    """

    def __init__(self):
        self.trigger_set          = NumberSet(Interval(-sys.maxint, sys.maxint))
        # epsilon trigger to empty set of target states --> missmatch
        self.target_state_indices = [ ]

    def is_empty(self):
        return self.trigger_set.is_all() and self.target_state_indices == []
        
    def get_string(self, StateIndexMap=None):
        if self.target_state_indices == [ ]: return "<no epsilon>"

        trigger_str = self.trigger_set.get_utf8_string()
        self.target_state_indices.sort()

        target_str = ""
        for ti in self.target_state_indices:
            if StateIndexMap == None: target_str += "%05i, " % int(ti) 
            else:                     target_str += "%05i, " % int(StateIndexMap[ti]) 

        if target_str != "": target_str = target_str[:-2]
        return "epsilon == %s ==> %s" % (trigger_str, target_str)

    def get_graphviz_string(self, OwnStateIndex, StateIndexMap=None):
        msg = ""
        for ti in self.target_state_indices:
            if StateIndexMap == None: target_str = "%i" % int(ti) 
            else:                     target_str = "%i" % int(StateIndexMap[ti]) 
            msg += "%i -> %s [label =\"<epsilon>\"];\n" % (OwnStateIndex, target_str)
        return msg


