from quex.engine.analyzer.core import AnalyzerState

from quex.engine.interval_handling import NumberSet

from itertools   import ifilter
from operator    import itemgetter
from collections import defaultdict
import sys

class CharacterPath:
    """A set of states that can be walked along with a character sequence plus
       an underlying common_transition_map.
    """
    def __init__(self, StartState, StartCharacter, TransitionMap):
        assert isinstance(StartState, AnalyzerState)
        assert isinstance(StartCharacter, (int, long))
        assert isinstance(TransitionMap, list)

        self.entry    = defaultdict(set)  # map: entry    --> state_index_list
        self.drop_out = defaultdict(set)  # map: drop_out --> state_index_list
        self.entry[StartState.entry].add(StartState.index)
        self.drop_out[StartState.drop_out].add(StartState.index)

        self.__sequence              = [ (StartState.index, StartCharacter) ]
        self.__common_transition_map = TransitionMap

        # Character that may trigger to any state. This character is adapted
        # when the first character of the path is different from the wild card
        # character. Then it must trigger to whatever the correspondent state
        # triggers.
        self.__wildcard_character = StartCharacter

    @property
    def sequence(self):              return self.__sequence

    @property
    def common_transition_map(self): return self.__common_transition_map

    def index(self):
        # Path index = index of the first state in the path
        try:    
            return self.__sequence[0][0]
        except: 
            assert False, \
                   "Character with either no sequence or wrong setup sequence element."

    def end_state_index(self):
        if len(self.__sequence) == 0: return -1
        return self.__sequence[-1][0]

    def set_end_state_index(self, StateIndex):
        self.__sequence.append((StateIndex, None))

    def append(self, State, Char):
        self.entry[State.entry].add(State.index)
        self.drop_out[State.drop_out].add(State.index)
        self.__sequence.append((State.index, Char))

    def contains(self, StateIndex):
        for dummy in ifilter(lambda x: x[0] == StateIndex, self.__sequence):
            return True
        return False

    def covers(self, Other):
        assert isinstance(Other, CharacterPath)
        assert len(self.__sequence) >= 2
        assert len(Other.__sequence) >= 2

        def __find(StateIndex):
            for i, x in enumerate(self.__sequence):
                if x[0] == StateIndex: return i
            return -1

        # Sequences should not be empty, but if (for some weird reason) it happens
        # make sure it is deleted by __filter_redundant_paths()
        if len(Other.__sequence) == 0: return False

        start_state_index = Other.__sequence[0][0]
        i = __find(start_state_index)
        if i == -1: return False

        # Do the remaining indices fit?
        L = len(self.__sequence)
        for state_index, char in Other.__sequence[1:]:
            i += 1
            if i >= L: 
                return False
            if self.__sequence[i][0] != state_index: 
                return False

        return True

    def get_intersections(self, Other):
        """Determines the state at which the sequences intersect. This
           is mathematically simple the 'intersection' of both sets.
        """

        # The end states are not considered 'intersections'. They are the target
        # states that are transitted after the path is terminated. There is no
        # harm in entering a path after exiting another.
        set_a = set(map(lambda x: x[0], self.__sequence[:-1]))
        set_b = set(map(lambda x: x[0], Other.__sequence[:-1]))

        return set_a.intersection(set_b)

    def match_entry_and_drop_out(self, State):
        """Determine whether the State's entry and drop_out match the entry
           and drop_out of the character path. This is important if uniformity
           of the path is required.
        """
        assert len(self.entry) == 1
        assert len(self.drop_out) == 1
        entry = self.entry.iterkeys().next()
        if entry != State.entry: return False

        drop_out = self.drop_out.iterkeys().next()
        if drop_out != State.drop_out: return False
        return True

    def match_transition_map(self, TransitionMap, PathTargetIdx, PathChar):
        """A single character transition 

                        PathChar --> PathTargetIdx

           has been detected. The question is, if the remaining transitions of
           the state match the common transition map of the current path. There
           might be a wild card, that is the character that is overlapped by
           the first single character transition.  As long as a transition map
           is differs only by this single character, the wild card is plugged
           into the position.

           RETURNS: 
                int > 0, the target index that the wild card character shall trigger
                         that the common transition map matches the TransitionMap.

                    - 1, if common transition map and TransitionMap match anyway 
                         and no wild card plug is necessary.

                   None, if there is no way that the common transition map and the
                         TransitionMap could match.
        """
        my_iterable    = self.__common_transition_map.__iter__()
        other_iterable = TransitionMap.__iter__()

        my_interval,    my_target    = my_iterable.next()
        other_interval, other_target = other_iterable.next()

        prev_end         = my_interval.begin
        assert prev_end == other_interval.begin

        # Keep track whether the wild card was used in this call.
        if self.__wildcard_character is not None: wildcard_target = None # wildcard target can be used
        else:                                     wildcard_target = -1L

        while not (my_interval.end == sys.maxint and other_interval.end == sys.maxint):
            # Prepare next iteration via '(*_interval, *_next_target)'. A temporary
            # '*_next_interval' is not required, since the interval is not used after the
            # if-block.
            if my_interval.end < other_interval.end:   
                interval_end                = my_interval.end
                my_interval, my_next_target = my_iterable.next()
            elif my_interval.end > other_interval.end: 
                interval_end                      = other_interval.end
                other_interval, other_next_target = other_iterable.next()
            else: 
                interval_end                      = other_interval.end   # == my_interval.end
                my_interval,    my_next_target    = my_iterable.next()
                other_interval, other_next_target = other_iterable.next()

            if my_target != other_target:                                    
                #                             my transition    other transition
                #  [prev_end, interval_end)      my_target       other_target
                success_f, wildcard_target_proposed = self.try_cover(prev_end, interval_end,
                                                                     PathChar, PathTargetIdx, 
                                                                     wildcard_target)
                if not success_f:
                    # Undo wild card usage, if it happened during this function call.
                    return None
                elif wildcard_target_proposed is not None: 
                    wildcard_target = wildcard_target_proposed

            my_target    = my_next_target
            other_target = other_next_target

        # Enter the wild card in the transition map if necessary
        return wildcard_target
                
    def try_cover(self, Begin, End, PathChar, PathTargetIndex, WildCardTarget):
        """Tries to cover the interval [Begin, End) by the given Char or
           the wild card if it is still available.

           RETURNS: success_f, wild_card_applied_f
        """
        Size = End - Begin
        assert Size > 0

        if   Size > 1:   
            return False, None

        assert Size == 1
        # NOTE: Size == 2 can never cover, because:
        #       For covering two characters are required to adapt, but we 
        #       have only 'PathChar' and '__wildcard_character' at most.
        #       The 'PathChar', though triggers by definition on a single 
        #       character interval, so there cannot be an interval of size
        #       two that triggers to 'PathTargetIndex'.

        Char = Begin
        if   Char == PathChar:                   return True,  None
        elif WildCardTarget is not None:         return False, None
        elif Char == self.__wildcard_character:  return True,  PathTargetIndex
        else:                                    return False, None

    def plug_wildcard_target(self, TargetIndex):
        # Use linear search, for a quick solution ...
        for i, info in enumerate(self.__common_transition_map):
            if info[0].begin == self.__wildcard_character: break
        else:
            assert False

        size = len(self.__common_transition_map)
        assert self.__common_transition_map[i][0].size() == 1
        if i != 0 and self.__common_transition_map[i-1][1] == TargetIndex:
            # Append to previous entry
            self.__common_transition_map[i-1][0].end += 1
            del self.__common_transition_map[i]
            i    -= 1
            size -= 1
        else:
            self.__common_transition_map[i][1] = TargetIndex

        if i != (size - 1) and self.__common_transition_map[i+1][1] == TargetIndex:
            # Append to subsequent entry
            self.__common_transition_map[i+1][0].begin = self.__common_transition_map[i][0].begin
            del self.__common_transition_map[i]
            
        assert False

    def get_string(self, NormalizeDB=None):
        def norm(X):
            return X if NormalizeDB is None else NormalizeDB[X]

        # Build a transition database
        transition_db = defaultdict(NumberSet)
        for interval, target_index in self.__common_transition_map:
            if target_index == E_StateIndices.DROP_OUT: continue
            transition_db[target_index].union(interval)

        skeleton_txt = ""
        for target_idx, trigger_set in sorted(transition_db.iteritems(), key=itemgetter(0)):
            skeleton_txt += "(%i) by " % norm(target_idx)
            skeleton_txt += trigger_set.get_utf8_string()
            skeleton_txt += "; "

        sequence_txt = ""
        for state_idx, char in self.__sequence[:-1]:
            state_idx = norm(state_idx)
            sequence_txt += "(%i)--'%s'-->" % (state_idx, chr(char))
        sequence_txt += "[%i]" % norm(self.__sequence[-1][0])

        return "".join(["start    = %i;\n" % norm(self.__sequence[0][0]),
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = %s\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.__wildcard_character is not None)])

    def __repr__(self):
        return self.get_string()

    def __len__(self):
        return len(self.__sequence)


def can_plug_to_equal(Set0, Char, Set1):
    """Determine whether the character 'Char' can be plugged
       to Set0 to make both sets equal.

       (1) If Set0 contains elements that are not in Set1, then 
           this is impossible.
       (2) If Set1 contains elements that are not in Set0, then
           it is possible, if the difference is a single character.

       NOTE:
                Set subtraction: A - B != empty, 
                                 A contains elements that are not in B.
    """
    # If interval number differs more than one, then no single
    # character can do the job.
    if Set1.interval_number() - Set0.interval_number() > 1: return False
    # It is possible that Set0 has more intervals than Set1, e.g.
    # Set0 = {[1,2], [4]}, and Set1={[1,4]}. In this example, '3'
    # can plug Set0 to be equal to Set1. A difference > 1 is impossible,
    # because, one character can plug at max. one 'hole'.
    if Set0.interval_number() - Set1.interval_number() > 1: return False

    # Does Set0 contain elements that are not in Set1?
    # if not Set0.difference(Set1).is_empty(): return False
    if not Set1.is_superset(Set0): return False

    # If there is no difference to make up for, then no plugging possible.
    # if Set1.difference(Set0).is_empty(): return False
    if Set0.is_superset(Set1): return False

    delta = Set1.difference(Set0)
    return delta.contains_only(Char)
