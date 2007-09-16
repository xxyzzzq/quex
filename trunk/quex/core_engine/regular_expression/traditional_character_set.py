import sys
import quex.core_engine.utf8 as utf8
import quex.core_engine.regular_expression.snap_backslashed_character as snap_backslashed_character
from quex.core_engine.interval_handling  import *
from quex.core_engine.state_machine.core import StateMachine


def do(UTF8_String):
    """Maps a'set string' to a state machine. Set strings are
       of the format "a-z0123_" as used in regular expressions.
       The resulting state machine has only three states:
       the initial state, FAIL, and SUCCESS. If a trigger matches
       one of the triggers in the set it transits from Initial
       to success, else it transits to FAIL.

       FORMAT: [a-zA-9012^w^\n]
    """
    
    # transform the range-string into a trigger set
    trigger_set, comment = __get_utf8_trigger_set(UTF8_String)
    assert trigger_set != False, comment

    # create state machine that triggers with the trigger set to SUCCESS
    # NOTE: The default for the ELSE transition is FAIL.
    sm = StateMachine()
    sm.add_transition(sm.init_state_index, trigger_set, AcceptanceF=True)
    return sm

class Tracker:
    def __init__(self):
        self.direct_match_set = NumberSet()
        self.inverse_match_set  = NumberSet()
        self.negation_f = False
        # NOTE: each incoming letter is written into 'last_letter' because 
        #       a minus sign might occur to span a range from this character
        #       to the following character. (see: consider_letter(...)).
        self.last_letter = -1 
 
    def __consider_interval(self, x0, x1):
        """... the core of the matter"""
        if x1 == None: x1 = x0 + 1
        #
        if self.negation_f == False:  self.direct_match_set.add_interval(Interval(x0,x1))
        else:                         self.inverse_match_set.add_interval(Interval(x0,x1))

    def consider_interval(self, x0, x1 = None):
        # flush last letter if it exists
        self.consider_letter(-1)
        # flush interval
        self.__consider_interval(x0, x1)

    def consider_letter(self, x):
        # if previous character was a letter, than add it to the set of trigger letters
        if self.last_letter != -1: self.__consider_interval(self.last_letter, self.last_letter+1)
        # store currently incoming letter code in 'self.last_letter' (maybee, its used for a 
        # character range).
        self.last_letter = x
 
    def negate(self):
         # flush last letter if it exists
        self.consider_letter(-1)

        if self.negation_f: self.negation_f = False
        else:               self.negation_f = True 


def __get_utf8_trigger_set(UTF8_String):
    """Transforms the regular expression character set expression into 
       an object of type NumberSet, i.e. a set of integers representing
       the unicode characters of the set.
    """
    tracker = Tracker()
    x  = utf8.map_n_utf8_to_unicode(UTF8_String)
    Lx = len(x)
    i = 0
    while i < Lx:
        if x[i] == ord('-'):
            #_________________________________________________________________________
            # character range:  'character0' '-' 'character1'
            #
            if tracker.last_letter == -1:
                return False, "'-' requires a preceding letter, e.g. 'a-z'"
            tracker.consider_interval(tracker.last_letter, x[i+1] + 1)
            # ATE: 2 characters
            i += 2

        elif i + 1 < Lx and x[i] == ord("\\"):
            #_________________________________________________________________________
            # Escape Character / Sophisticated Code Point Definition
            #
            value, i = snap_backslashed_character.do(x, i)
            if value == None:
                max_i = min(len(x), i + 3)
                return False, "backslashed character(s) %s ... cannot be backslashed" % repr(map(chr, x[i:max_i]))
            tracker.consider_letter(value)

        elif x[i] == ord("^"):
            #_________________________________________________________________________
            # Negation
            #
            # any characterange or interval that is specified is now
            # negated, i.e. ^0-5 means: 'anything but 0-5'
            tracker.negate()
            tracker.consider_letter(-1)  # '-1' => there is no preceeding character
            # ATE: one character
            i += 1

        else:
            #_________________________________________________________________________
            # Normal character
            #
            tracker.consider_letter(x[i])
            # ATE: one character
            i += 1
    
    # flush last letter if it exists
    tracker.consider_letter(-1)

    # inverse_match_set: if a 'event' appears that is != to any of them, then trigger!
    # direct_match_set:  if a 'event' appears that is == to any of them, then trigger!
    # the whole set:     combine inverse and direct set with 'or', i.e. union
    result = tracker.direct_match_set
    result = result.intersection(tracker.inverse_match_set.inverse())
    return result, ""


