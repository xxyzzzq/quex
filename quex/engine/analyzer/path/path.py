from quex.engine.analyzer.core import AnalyzerState

from quex.engine.interval_handling import NumberSet

from itertools   import ifilter
from operator    import itemgetter
from collections import defaultdict

class CharacterPath:
    """A set of states that can be walked along with a character sequence plus
       a common remaining transition map (here called 'skeleton').
    """
    def __init__(self, StartState, StartCharacter, Skeleton):
        assert isinstance(StartState, AnalyzerState)
        assert isinstance(StartCharacter, (int, long))
        assert isinstance(Skeleton, dict)

        self.entry    = defaultdict(set)  # map: entry    --> state_index_list
        self.drop_out = defaultdict(set)  # map: drop_out --> state_index_list
        self.entry[StartState.entry].add(StartState.index)
        self.drop_out[StartState.drop_out].add(StartState.index)

        self.__sequence           = [ (StartState.index, StartCharacter) ]

        self.__skeleton           = Skeleton
        self.__skeleton_key_set   = set(Skeleton.keys())
        # Character that may trigger to any state. This character is
        # adapted when the first character of the path is different
        # from the wild card character. Then it must trigger to whatever
        # the correspondent state triggers.
        self.__wildcard_character = StartCharacter

    @property
    def state_index_list(self):
        """Result **MUST** be a list, because, later on a state key may be 
           associated with it.
        """
        assert len(self.__sequence) > 1
        return map(lambda x: x[0], self.__sequence[:-1])

    def sequence(self):
        return self.__sequence

    def index(self):
        # Path index = index of the first state in the path
        try:    
            return self.__sequence[0][0]
        except: 
            assert False, \
                   "Character with either no sequence or wrong setup sequence element."

    def skeleton(self):
        assert isinstance(self.__skeleton, dict)
        return self.__skeleton

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

    def match_skeleton(self, TransitionMap, TargetIdx, TriggerCharToTarget):
        """A single character transition 

                        TriggerCharToTarget --> TargetIdx

           has been detected. The question is, if the remaining transitions of
           the state match the skeleton of the current path. There might be a
           wild card, that is the character that is overlapped by the first
           single character transition.  As long as a transition map is differs
           only by this single character, the wild card is plugged into the
           position.

           RETURNS: 
                int > 0, the character that the wild card shall take so
                         that the skeleton matches the TransitionMap.

                    - 1, if skeleton and TransitionMap match anyway and
                         no wild card plug is necessary.

                   None, if there is no way that the skeleton and the
                         TransitionMap could match.
        """
        ## ?? The element of a path cannot be triggered by the skeleton! ??
        ## ?? if self.__skeleton.has_key(TargetIdx): return False        ?? 
        ## ?? Why would it not? (fschaef9: 10y04m11d)                    ??

        # wildcard character is None:  wild card is taken and entered into 'skeleton'
        #                    not None: target for 'wildcard_character' can still be 
        #                              chosen freely.
        if self.__wildcard_character is not None: wildcard_target = None # unused
        else:                                     wildcard_target = -1   # used before

        transition_map_key_set = set(TransitionMap.keys())
        # (1) Target States In TransitionMap and Not in Skeleton
        #
        #     All target states of TransitionMap must be in Skeleton, except:
        #
        #      (1.1) The single char transition target TargetIdx.
        #      (1.2) Maybe, one that is reached by a single char
        #            transition of wildcard.
        delta_set  = transition_map_key_set - self.__skeleton_key_set
        delta_size = len(delta_set)
        if delta_size > 2: return None

        for target_idx in delta_set:
            if   target_idx == TargetIdx:    continue # (1.1)
            elif wildcard_target is not None:                                            return None
            elif not TransitionMap[target_idx].contains_only(self.__wildcard_character): return None
            wildcard_target = target_idx               # (1.2)

        # (2) Target States In Skeleton and Not in TransitionMap
        #
        #     All target states of Skeleton must be in TransitionMap, except:
        #
        #     (2.1) Transition to the target index in skeleton which is 
        #           covered by current single character transition.
        delta_set  = self.__skeleton_key_set - transition_map_key_set
        delta_size = len(delta_set)
        if delta_size > 1: 
            return None
        if delta_size == 1:
            target_idx = delta_set.__iter__().next()
            if not self.__skeleton[target_idx].contains_only(TriggerCharToTarget): return None
            # (2.1) OK, single char covers the transition in skeleton.

        # (3) Target States in both, Skeleton and Transition Map
        #
        #     All correspondent trigger sets must be equal, except:
        #
        #     (3.1) single char transition covers the hole, i.e.
        #           trigger set in transition map + single char ==
        #           trigger set in skeleton. (check this first,
        #           don't waste wildcard).
        #     (3.2) trigger set in skeleton + wildcard == trigger set 
        #           in transition map.
        #      
        common_set = self.__skeleton_key_set & transition_map_key_set
        for target_idx in common_set:
            sk_trigger_set = self.__skeleton[target_idx]
            tm_trigger_set = TransitionMap[target_idx]

            if sk_trigger_set.is_equal(tm_trigger_set): continue

            # (3.1) Maybe the current single transition covers the 'hole'.
            #       (check this first, we do not want to waste the wilcard)
            if can_plug_to_equal(tm_trigger_set, TriggerCharToTarget, sk_trigger_set):
                continue

            elif wildcard_target is None:
                # (3.2) Can difference between trigger sets be plugged by the wildcard?
                if can_plug_to_equal(sk_trigger_set, self.__wildcard_character, tm_trigger_set): 
                    wildcard_target = target_idx
                    continue
                # (3.3) A set extended by wilcard may have only a 'hole' of the
                #       size of the single transition char.
                if can_plug_to_equal(tm_trigger_set, 
                                     TriggerCharToTarget,
                                     sk_trigger_set.union(NumberSet(self.__wildcard_character))): 
                    wildcard_target = target_idx
                    continue

            # Trigger sets differ and no wildcard or single transition can
            # 'explain' that => skeleton does not fit.
            return None

        if wildcard_target is None: return -1 # No plugging necessary
        return wildcard_target

    def plug_wildcard(self, WildcardPlug):
        assert isinstance(WildcardPlug, (int, long))

        # Finally, if there is a plugging to be performed, then do it.
        if WildcardPlug == -1: return
        
        if self.__skeleton.has_key(WildcardPlug):
            self.__skeleton[WildcardPlug].unite_with(NumberSet(self.__wildcard_character))
        else:
            self.__skeleton[WildcardPlug] = NumberSet(self.__wildcard_character)
        self.__skeleton_key_set.add(WildcardPlug)
        self.__wildcard_character = None # There is no more wildcard now
        
        return 

    def get_string(self, NormalizeDB=None):
        def norm(X):
            return X if NormalizeDB is None else NormalizeDB[X]

        skeleton_txt = ""
        for target_idx, trigger_set in sorted(self.__skeleton.iteritems(), key=itemgetter(0)):
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
