from   quex.engine.analyzer.state.core         import AnalyzerState
from   quex.engine.analyzer.state.entry_action import DoorID, SetPathIterator
from   quex.engine.analyzer.mega_state.core    import MegaState_Entry, \
                                                      MegaState_DropOut
import quex.engine.analyzer.transition_map     as transition_map_tools
import quex.engine.state_machine.index         as     index

from   quex.blackboard               import E_StateIndices

from itertools   import ifilter

class PathWalkerState_Entry(MegaState_Entry):
    def __init__(self, MegaStateIndex, TheEntry):
        MegaState_Entry.__init__(self, MegaStateIndex)

        # '.action_db' => '.door_tree_configure()' => '.door_db'
        #                                             '.transition_db'
        #                                             '.door_id_replacement_db'
        self.action_db_update(TheEntry, 0)

    def action_db_update(self, TheEntry, Offset):
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

class CharacterPathElement(object):
    __slots__ = ("state_index", "transition_char_to_next")
    def __init__(self, StateIndex, TransitionChar):
        self.state_index             = StateIndex
        self.transition_char_to_next = TransitionChar

    def clone(self):
        return CharacterPathElement(self.state_index, self.transition_char_to_next)

class CharacterPath(object):
    """A set of states that can be walked along with a character sequence plus
       a common remaining transition map (here called 'skeleton').
    """
    __slots__ = ("index", "entry", "drop_out", "__sequence", "__transition_map", "__wildcard_char")

    def __init__(self, StartState, StartCharacter, AdaptedTransitionMap):
        assert StartState is None     or isinstance(StartState, AnalyzerState)
        assert StartCharacter is None or isinstance(StartCharacter, (int, long))
        assert AdaptedTransitionMap is None or isinstance(AdaptedTransitionMap, list)

        if StartState is None: return # Only for Clone

        self.index    = index.get()
        self.entry    = PathWalkerState_Entry(self.index, StartState.entry)
        self.drop_out = MegaState_DropOut(StartState) 

        self.__sequence         = [ CharacterPathElement(StartState.index, StartCharacter) ]
        self.__transition_map   = AdaptedTransitionMap
        # Set the 'void' target to indicate wildcard.
        transition_map_tools.set(self.__transition_map, StartCharacter, E_StateIndices.VOID)
        self.__wildcard_char  = StartCharacter

        ## print "#construct: {\n%s}" % transition_map_tools.get_string(self.__transition_map)

    def clone(self):
        result = CharacterPath(None, None, None)
        result.index    = self.index
        result.entry    = self.entry
        result.drop_out = self.drop_out
        result.__sequence = [x.clone() for x in self.__sequence]
        def adapt(Target):
            if hasattr(Target, "clone"): return Target.clone()
            else:                        return Target
        result.__transition_map = [(interval.clone(), adapt(target)) for interval, target in self.__transition_map]
        result.__wildcard_char  = self.__wildcard_char
        return result

    @property
    def state_index_set(self):
        """Result **MUST** be a list, because, later on a state key may be 
           associated with it.
        """
        assert len(self.__sequence) > 1
        return set(x.state_index for x in self.__sequence[:-1])

    def has_wildcard(self):
        return self.__wildcard_char is not None

    def sequence(self):
        return self.__sequence

    def has_state_index(self, StateIndex):
        for state_index, char in self.__sequence[:-1]:
            if state_index == StateIndex: return True
        return False

    @property
    def transition_map(self):
        return self.__transition_map

    def end_state_index(self):
        if len(self.__sequence) == 0: return -1
        return self.__sequence[-1].state_index

    def append_state(self, State, TransitionCharacterToNextState=None):
        """Append 'State' to path. If 'TransitionCharacterToNextState' is
        None, then the state is considered a terminal state. Terminal states
        are not themselves implemented inside a PathWalkerState. Thus, their
        entry and drop out information does not have to be absorbed.

        Terminal states are indicated in the 'sequence' by a 'transition_char_to_next'
        of 'None' (which corresponds well with the aforementioned.
        """

        # The index of the state on the path determines the path iterator's offset
        offset = len(self.__sequence)

        # Add the state on the sequence of state along the path
        self.__sequence.append(CharacterPathElement(State.index, 
                                                    TransitionCharacterToNextState))

        if TransitionCharacterToNextState is not None:
            # Adapt the entry's action_db: include the entries of the new state
            self.entry.action_db_update(State.entry, offset)

            # Adapt information about entry and drop-out actions
            self.drop_out.update_from_state(State)

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

        prev_state_index = self.__sequence[0].state_index
        prototype        = None
        for x in self.__sequence[1:-1]:
            action = self.entry.action_db_get_command_list(x.state_index, prev_state_index)
            if prototype is not None:
                if not prototype.is_equivalent(action.command_list):
                    return None
            else:
                prototype = action.command_list.clone()
                prototype.delete_SetPathIterator_commands()

            prev_state_index = x.state_index

        # Since len(sequence) >= 2, then there is a 'prototype' at this point.
        return prototype

    def contains_state(self, StateIndex):
        for dummy in ifilter(lambda x: x.state_index == StateIndex, self.__sequence):
            return True
        return False

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
        action = self.entry.action_db_get_command_list(State.index, self.__sequence[-1].state_index)
        if not uniform_entry.is_equivalent(action.command_list):
            return False
        return True

    def match(self, TransitionMap, TargetDoorID, TriggerCharToTarget):
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
        wildcard_target = -1
        for begin, end, a_target, b_target in transition_map_tools.zipped_iterable(self.__transition_map,
                                                                                   TransitionMap):
            if a_target == b_target: continue    # There is no problem at all

            size = end - begin
            assert size > 0

            if size == 1:  
                if   b_target == TargetDoorID:        continue
                elif a_target == E_StateIndices.VOID: wildcard_target = b_target; continue
                else:                                 return None
            else:
                return None

        # Here: The transition maps match, but possibly require the use of a wildcard.
        return wildcard_target

    def get_sibling(self, StateIndex, TransitionChar, Other):
        """The 'Other' path intersects at 'StateIndex' with this path (StateIndex
        can only appear once in path, since recursion is not possible). This function
        generates a sibling where the Other path is docked to this path at the
        position of 'StateIndex'.
        """
        assert self.__wildcard_char is None   # As long as there is a wildcard, the 
        assert Other.__wildcard_char is None  # transition map is not frozen.
        #                                     # => No siblings can be determined.

        for i, x in self.__sequence:
            if x.state_index == StateIndex: break
        else:
            assert False, "StateIndex must be part of path."

        new_sequence =  Other.sequence() \
                      + [ CharacterPathElement(StateIndex, TransitionChar) ] \
                      + self.__sequence[:i+1]
        return CharacterPathElement(new_sequence)

    def finalize(self):
        # Ensure that there is no wildcard in the transition map
        if self.__wildcard_char is None: return

        transition_map_tools.smoothen(self.__transition_map, self.__wildcard_char)
        self.__wildcard_char = None

    def plug_wildcard(self, Target):
        assert isinstance(Target, DoorID) or Target == E_StateIndices.DROP_OUT, repr(Target)
        assert self.__wildcard_char is not None
        assert transition_map_tools.get_target(self.__transition_map, self.__wildcard_char) == E_StateIndices.VOID

        ## print "#wildcard:", chr(self.__wildcard_char), Target
        ## print "#before plug: {\n%s}" % transition_map_tools.get_string(self.__transition_map)

        transition_map_tools.set(self.__transition_map, self.__wildcard_char, Target)

        ## print "#after plug: {\n%s}" % transition_map_tools.get_string(self.__transition_map)
        
        self.__wildcard_char = None
        return 

    def get_string(self, NormalizeDB=None):
        # assert NormalizeDB is None, "Sorry, I guessed that this was no longer used."
        def norm(X):
            assert isinstance(X, (int, long)) or X is None
            return X if NormalizeDB is None else NormalizeDB[X]

        L            = max(len(x[0].get_utf8_string()) for x in self.__transition_map)
        skeleton_txt = ""
        for interval, target_door_id in self.__transition_map:
            interval_str  = interval.get_utf8_string()
            skeleton_txt += "   %s%s -> %s\n" % (interval_str, " " * (L - len(interval_str)), target_door_id)

        sequence_txt = ""
        for x in self.__sequence[:-1]:
            sequence_txt += "(%i)--'%s'-->" % (x.state_index, chr(x.transition_char_to_next))
        sequence_txt += "[%i]" % norm(self.__sequence[-1].state_index)

        return "".join(["start    = %i;\n" % norm(self.__sequence[0].state_index),
                        "path     = %s;\n" % sequence_txt,
                        "skeleton = {\n%s}\n"  % skeleton_txt, 
                        "wildcard = %s;\n" % repr(self.__wildcard_char is not None)])

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
