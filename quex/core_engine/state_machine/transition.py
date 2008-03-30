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

