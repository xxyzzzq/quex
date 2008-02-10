import sys
import quex.core_engine.utf8 as utf8
import quex.core_engine.regular_expression.snap_backslashed_character as snap_backslashed_character
from quex.core_engine.interval_handling  import *
from quex.exception                      import RegularExpressionException



class Tracker:
    def __init__(self):
        self.direct_match_set = NumberSet()
        self.inverse_match_set  = NumberSet()
        self.negation_f = False
        # NOTE: each incoming letter is written into 'last_letter' because 
        #       a minus sign might occur to span a range from this character
        #       to the following character. (see: consider_letter(...)).
        self.last_letter = -1 
 
    def __consider_interval(self, Begin, End):
        """... the core of the matter"""
        if End == None: End = Begin + 1
        #
        if Begin > End:
            # In case that the 'end' is lesser than the begin, on canot simply switch
            # end and begin. End points to the first element beyond the valid interval.
            begin = End - 1
            end = Begin
        else:
            begin = Begin
            end   = End

        interval = Interval(begin, end)
        if self.negation_f == False:  self.direct_match_set.add_interval(interval)
        else:                         self.inverse_match_set.add_interval(interval)

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

def do(UTF8_String):
    """Transforms an expression of the form [a-z0-9A-Z] into a NumberSet of
       code points that corresponds to the characters and character ranges mentioned.
    """

    def __consider_backslash_occurence(x, i):
        value, i = snap_backslashed_character.do(x, i)
        if value == None:
            max_i = min(len(x), i + 3)
            raise RegularExpressionException(
                "Character range: backslashed character(s) %s ... cannot be backslashed" % \
                repr(map(chr, x[i:max_i])))
        return value, i

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
                raise RegularExpressionException("Character range: '-' requires a preceding character, e.g. 'a-z'")

            i += 1
            if len(x) <= i:
                raise RegularExpressionException("Character range: '-' requires a character following '-'.")

            if i + 1 < Lx and x[i] == ord("\\"):
                value, i = __consider_backslash_occurence(x, i) 
                value += 1        # value denotes 'end', i.e first character outside the interval
            else:
                value = x[i] + 1  # value denotes 'end'
                i += 1

            tracker.consider_interval(tracker.last_letter, value)

        elif i + 1 < Lx and x[i] == ord("\\"):
            #_________________________________________________________________________
            # Escape Character / Sophisticated Code Point Definition
            #
            value, i = __consider_backslash_occurence(x, i)
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
    return result


