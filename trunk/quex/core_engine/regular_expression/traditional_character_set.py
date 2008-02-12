import sys
import StringIO
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

def do_string(UTF8_String):
    return do(StringIO.StringIO(UTF8_String))

def do(sh):
    """Transforms an expression of the form [a-z0-9A-Z] into a NumberSet of
       code points that corresponds to the characters and character ranges mentioned.
    """
    assert     sh.__class__.__name__ == "StringIO" \
            or sh.__class__.__name__ == "file"

    tracker   = Tracker()
    char_code = None
    while char_code != 0xFF:
        char_code = utf8.__read_one_utf8_code_from_stream(sh)

        if char_code == ord(']'): break

        if char_code == ord('-'):
            #_________________________________________________________________________
            # character range:  'character0' '-' 'character1'
            #
            if tracker.last_letter == -1:
                raise RegularExpressionException("Character range: '-' requires a preceding character, e.g. 'a-z'")

            char_code = utf8.__read_one_utf8_code_from_stream(sh)
            if char_code == 0xFF:
                raise RegularExpressionException("Character range: '-' requires a character following '-'.")

            # value denotes 'end', i.e first character outside the interval
            if char_code == ord("\\"): value = snap_backslashed_character.do(sh) + 1 
            else:                      value = char_code + 1

            tracker.consider_interval(tracker.last_letter, value)

        elif char_code == ord("\\"):
            #_________________________________________________________________________
            # Escape Character / Sophisticated Code Point Definition
            #
            value = snap_backslashed_character.do(sh)
            tracker.consider_letter(value)

        elif char_code == ord("^"):
            #_________________________________________________________________________
            # Negation
            #
            # any characterange or interval that is specified is now
            # negated, i.e. ^0-5 means: 'anything but 0-5'
            tracker.negate()
            tracker.consider_letter(-1)  # '-1' => there is no preceeding character

        else:
            #_________________________________________________________________________
            # Normal character
            #
            tracker.consider_letter(char_code)
    
    # flush last letter if it exists
    tracker.consider_letter(-1)

    # inverse_match_set: if a 'event' appears that is != to any of them, then trigger!
    # direct_match_set:  if a 'event' appears that is == to any of them, then trigger!
    # the whole set:     combine inverse and direct set with 'or', i.e. union
    result = tracker.direct_match_set
    result = result.intersection(tracker.inverse_match_set.inverse())
    return result


