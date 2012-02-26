from   quex.engine.analyzer.state.core         import AnalyzerState
from   quex.engine.analyzer.state.entry        import Entry
from   quex.engine.analyzer.state.entry_action import DoorID, SetPathIterator
import quex.engine.state_machine.index         as     index

from quex.engine.interval_handling import NumberSet

from itertools   import ifilter
from operator    import itemgetter
from collections import defaultdict

class PathWalkerState_Entry(Entry):
    def __init__(self, StateIndex, TheEntry):
        Entry.__init__(self, StateIndex, [])
        self.update(TheEntry, 0)

    def update(self, TheEntry, Offset):
        """Include 'TheState.entry.action_db' into this state. That means,
           that any mapping:
           
                transition (StateIndex, FromStateIndex) --> CommandList 

           is absorbed in 'self.__action_db'. Additionally, any command list
           must contain the 'SetTemplateStateKey' command that sets the state key for
           TheState. At each (external) entry into the Template state the
           'state_key' must be set, so that the template state can operate
           accordingly.  
        """
        for transition_id, action in TheEntry.action_db.iteritems():
            clone = action.clone()
            # Create new 'SetPathIterator' for current state
            clone.command_list.misc.add(SetPathIterator(Offset=Offset))

            self.action_db[transition_id] = clone

class CharacterPath:
    """A set of states that can be walked along with a character sequence plus
       a common remaining transition map (here called 'skeleton').
    """
    def __init__(self, StartState, StartCharacter, Skeleton):
        assert isinstance(StartState, AnalyzerState)
        assert isinstance(StartCharacter, (int, long))
        assert isinstance(Skeleton, dict)

        self.entry    = PathWalkerState_Entry(index.get(), StartState.entry)
        self.drop_out = defaultdict(set)
        self.drop_out[StartState.drop_out].add(StartState.index)

        self.__sequence         = [ (StartState.index, StartCharacter) ]
        self.__skeleton         = Skeleton
        self.__skeleton_key_set = set(Skeleton.keys())
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

        # The index of the state on the path determines the path iterator's offset
        offset = len(self.__sequence)

        # Adapt the entry's action_db: include the entries of the new state
        self.entry.update(State.entry, offset)

        # Adapt information about entry and drop-out actions
        self.drop_out[State.drop_out].add(State.index)

        # Add the state on the sequence of state along the path
        self.__sequence.append((State.index, Char))

    def get_uniform_entry_command_list_along_path(self):
        """When a state is entered (possibly) some commands are executed, for
           example 'position[1] = input_p' or 'last_acceptance = 13'. The states
           on the path may require also actions to be taken when walking along
           the path. 

           This function determines whether those commands are always the same
           or not.

           THIS DOES NOT INCLUDE THE TERMINAL STATE! 
           THE ENTRY OF THE TERMINAL STATE IS NOT PART OF THE PATHWALKER!

           RETURNS: ComandList -- if the commands are uniform.
                    None       -- if the commands are not uniform.
        """
        # A path where there are not at least two states, is not a path.
        assert len(self.__sequence) >= 2

        prev_state_index = self.__sequence[0][0]
        prototype        = None
        for state_index, char in self.__sequence[1:-1]:
            action = self.entry.action_db_get_command_list(state_index, prev_state_index)
            if prototype is not None:
                if not prototype.is_equivalent(action.command_list):
                    return None
            else:
                prototype = action.command_list.clone()
                prototype.delete_SetPathIterator_commands()

            prev_state_index = state_index

        # Since len(sequence) >= 2, then there is a 'prototype' at this point.
        return prototype

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

    def check_uniform_entry_to_state(self, State):
        """Checks whether the entry from the end of the path to the state
           would be uniform with the entries along the path. 

           RETURNS: True -- State would be entered through the same 
                            entry as all the other states on the path.
                    False -- State would require a separate entry, because
                             some commands need to be executed that are 
                             not done for all other transitions on the path.
        """
        if len(self.__sequence) < 2: 
            # The 'State' will be the first entry along the path, so it can only 
            # be uniform. There is simply no other entry.
            return True

        uniform_entry = self.get_uniform_entry_command_list_along_path()
        if uniform_entry is None: # Actually, this could be an assert. This function is only
            return False          # to be executed when building uniform paths.
        action = self.entry.action_db_get_command_list(State.index, self.__sequence[-1][0])
        if not uniform_entry.is_equivalent(action.command_list):
            return False
        return True

    def check_uniform_drop_out(self, State):
        """Checks whether the State's drop-out behavior is uniform with all
           the other State's drop out behaviors on the path.
        """
        if len(self.drop_out) != 1: # Actually, this could be an assert. This function is only
            return False            # to be executed when building uniform paths.

        drop_out = self.drop_out.iterkeys().next()
        return drop_out == State.drop_out

    def match_skeleton(self, TransitionMap, TargetDoorID, TriggerCharToTarget):
        """A single character transition 

                        TriggerCharToTarget --> DoorID

           has been detected. The question is, if the remaining transitions of
           the state match the skeleton of the current path. There might be a
           wild card, that is the character that is overlapped by the first
           single character transition.  As long as a transition map differs
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
        assert isinstance(TargetDoorID, DoorID)
        ## ?? The element of a path cannot be triggered by the skeleton! ??
        ## ?? if self.__skeleton.has_key(TargetDoorID): return False        ?? 
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
        #      (1.1) The single char transition target TargetDoorID.
        #      (1.2) Maybe, one that is reached by a single char
        #            transition of wildcard.
        delta_set  = transition_map_key_set - self.__skeleton_key_set
        delta_size = len(delta_set)
        if delta_size > 2: return None

        for target_door_id in delta_set:
            if   target_door_id == TargetDoorID: continue # (1.1)
            elif wildcard_target is not None:                                                return None
            elif not TransitionMap[target_door_id].contains_only(self.__wildcard_character): return None
            wildcard_target = target_door_id              # (1.2)

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
            target_door_id = delta_set.__iter__().next()
            if not self.__skeleton[target_door_id].contains_only(TriggerCharToTarget): return None
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
        for target_door_id in common_set:
            sk_trigger_set = self.__skeleton[target_door_id]
            tm_trigger_set = TransitionMap[target_door_id]

            if sk_trigger_set.is_equal(tm_trigger_set): continue

            # (3.1) Maybe the current single transition covers the 'hole'.
            #       (check this first, we do not want to waste the wilcard)
            if can_plug_to_equal(tm_trigger_set, TriggerCharToTarget, sk_trigger_set):
                continue

            elif wildcard_target is None:
                # (3.2) Can difference between trigger sets be plugged by the wildcard?
                if can_plug_to_equal(sk_trigger_set, self.__wildcard_character, tm_trigger_set): 
                    wildcard_target = target_door_id
                    continue
                # (3.3) A set extended by wilcard may have only a 'hole' of the
                #       size of the single transition char.
                if can_plug_to_equal(tm_trigger_set, 
                                     TriggerCharToTarget,
                                     sk_trigger_set.union(NumberSet(self.__wildcard_character))): 
                    wildcard_target = target_door_id
                    continue

            # Trigger sets differ and no wildcard or single transition can
            # 'excuse' that => skeleton does not fit.
            return None

        if wildcard_target is None: return -1 # No plugging necessary
        return wildcard_target

    def plug_wildcard(self, WildcardPlug):
        assert isinstance(WildcardPlug, DoorID)

        # If there is a plugging to be performed, then do it.
        if self.__skeleton.has_key(WildcardPlug):
            self.__skeleton[WildcardPlug].unite_with(NumberSet(self.__wildcard_character))
        else:
            self.__skeleton[WildcardPlug] = NumberSet(self.__wildcard_character)
        self.__skeleton_key_set.add(WildcardPlug)
        self.__wildcard_character = None # There is no more wildcard now
        
        return 

    def get_string(self, NormalizeDB=None):
        # assert NormalizeDB is None, "Sorry, I guessed that this was no longer used."
        def norm(X):
            assert isinstance(X, (int, long)) or X is None
            return X if NormalizeDB is None else NormalizeDB[X]

        skeleton_txt = ""
        for target_door_id, trigger_set in sorted(self.__skeleton.iteritems(), key=itemgetter(0)):
            skeleton_txt += "(s=%s,d=%i) by " % (norm(target_door_id.state_index), target_door_id.door_index)
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
