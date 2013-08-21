# (C) 2010-2013 Frank-Rene Schaefer
from   quex.engine.analyzer.transition_map      import TransitionMap   
from   quex.engine.analyzer.state.entry_action  import PathIteratorSet, \
                                                       PathIteratorIncrement, \
                                                       DoorID
from   quex.engine.analyzer.mega_state.core     import MegaState, MegaState_Transition
import quex.engine.state_machine.index          as     index
from   quex.engine.tools                        import UniformObject
from   quex.blackboard                          import E_Compression
from   quex.engine.analyzer.mega_state.core     import MegaState_Entry, \
                                                       MegaState_DropOut

from   itertools import izip

class PathWalkerState_Entry(MegaState_Entry):
    """________________________________________________________________________

    Entry into a PathWalkerState. As the base's base class 'Entry' it holds
    information about what CommandList is to be executed upon entry from a
    particular source state.
    
    PRELIMINARY: Documentation of class 'MegaState_Entry'.

    A PathWalkerState is a MegaState, meaning it implements multiple states at
    once. Entries into the PathWalkerState must have an action that sets the
    'state key' for the state that it is about to represent. The 'state key'
    of a PathWalkerState is the offset of the path iterator from the character
    path's base.

    During analysis nothing actually happens, accept that the transitions
    which happen inside the path are tagged in 

                  .transition_reassignment_candidate_list

    Once, the PathWalkerState is constructed the reassignment happens and
    the action_db is updated.
    ___________________________________________________________________________
    """
    def __init__(self):
        MegaState_Entry.__init__(self)

    def action_db_update(self, From, To, FromOutsideCmd, FromInsideCmd):
        """Considers the actions related to transitions on the path of a
        PathWalkerState.  For transitions from outside need to set a
        'state_key', i.e.  the PathIteraor.  Transitions inside the only
        increment the path_iterator which is done in the implementation of the
        PathWalkerState.
        """

        for transition_id, action in self.action_db.iteritems():

            if transition_id.target_state_index != To:
                # This transition does not concern the state which is meant.
                continue

            elif transition_id.source_state_index != From:
                cmd = FromOutsideCmd

            else:
                cmd = FromInsideCmd
                # Later we will try to unify all entries from inside.
                self.transition_reassignment_candidate_list.append((From, transition_id))

            if cmd is not None:
                action.command_list.misc.add(cmd)

        return

class PathWalkerState(MegaState):
    """________________________________________________________________________
    A path walker state is a state that can walk along one or more paths
    with the same remaining transition map. Objects of this class are the basis
    for code generation.

                    path ['w', 'h', 'i', 'l', 'e', PTC]
                    path ['f', 'o', 'r', PTC]
                    path ['f', 'u', 'n', 'c', 't', 'i', 'o', 'n', PTC]
                    path ['p', 'r', 'i', 'n', 't', PTC]
           path_iterator ---->--'                    
                    path ['s', 't', 'r', 'u', 'c', 't', PTC]

                    .-------------------------.
                    | path_iterator = path[0] |
                    '-------------------------'
                                |
                                |<-----------------------------------.
                                |                                    |
                   .-----------'''--------------.    true   .-----------------.
                  / *input_p == *path_iterator ? \----------| ++path_iterator |
                  \______________________________/          | ++input_p       |
                                |                           '-----------------'
                                |
                      .------------------------.
                      |                        |----- [a-h] ----> state 21
                      |                        |----- [j]   ----> state 185
                      | transition_map(*input) |----- 'o'   ----> state 312
                      |                        |----- [p-z] ----> state 21
                      |                        |----- [a-h] ----> state 21
                      '------------------------'

    The 'group()' function in 'path_walker.core.py' develops a set of path
    walkers for a set of given CharacterPath list.
    ___________________________________________________________________________
    """
    def __init__(self, FirstPath, TheAnalyzer):
        MegaState.__init__(self, PathWalkerState_Entry(), MegaState_DropOut(), index.get())

        # Uniform CommandList along entries on the path (optional)
        self.uniform_entry_CommandList = FirstPath.uniform_entry_CommandList.clone()
        self.uniform_DropOut           = FirstPath.uniform_DropOut.clone()

        self.__path_list                   = []
        self.__implemented_state_index_set = set()
        self.__state_index_sequence        = []
        self.__absorb_path(FirstPath, TheAnalyzer)

        self.__transition_map_to_door_ids = FirstPath.transition_map
        self.__transition_map             = None

        # Following are set by 'finalize()'.
        self.__finalized = None # <-- PathWalkerState_ContentFinalized()

    @property
    def transition_map(self):
        if self.__transition_map is None:
            self.__transition_map = TransitionMap.from_iterable(self.__transition_map_to_door_ids, \
                                                                MegaState_Transition.create)
        return self.__transition_map

    def accept(self, Path, TheAnalyzer, CompressionType):
        """Checks whether conditions of absorbing the Path are met, and if
        so then the Path is absorbed. 

        RETURNS: False -- Path does not fit the PathWalkerState.
                 True  -- Path can be walked by PathWalkerState and has been 
                          accepted.
        """
        if not self.__can_absorb_path(Path, TheAnalyzer, CompressionType):
            return False

        self.__absorb_path(Path, TheAnalyzer)
        return True

    def __can_absorb_path(self, Path, TheAnalyzer, CompressionType):
        """Check whether a path can be walked along with the given PathWalkerState.
        For this, the following has to hold:

            -- The transition_maps must match.
            -- If uniformity is required, the entries and drop-outs must 
               be uniform with the existing onces.
        """
        if not self.__transition_map_to_door_ids.is_equal(Path.transition_map): 
            return False

        if CompressionType == E_Compression.PATH_UNIFORM:
            if    (not self.uniform_entry_CommandList.fit(Path.uniform_entry_CommandList)) \
               or (not self.uniform_DropOut.fit(Path.uniform_DropOut)):
                return False

        return True

    def __absorb_path(self, Path, TheAnalyzer):
        """-- Absorb the state sequence of the path.
           -- Absorb the Entry/DropOut information.
        """

        # (Meaningful paths consist of more than one state and a terminal.)
        assert len(Path.step_list) > 2
        self.__path_list.append(Path.step_list)

        # (1) Absorb the state sequence of the path.
        #
        new_state_index_list            = [x.state_index for x in Path.step_list]
        new_implemented_state_index_set = set(new_state_index_list[:-1])

        # Assert: A state cannot be implemented on two different paths.
        assert set(self.__implemented_state_index_set).isdisjoint(new_implemented_state_index_set)
        self.__state_index_sequence.extend(new_state_index_list)
        self.__implemented_state_index_set.update(new_implemented_state_index_set)

        # (2) Absorb Entry/DropOut Information
        #
        self.uniform_entry_CommandList <<= Path.uniform_entry_CommandList
        self.uniform_DropOut           <<= Path.uniform_DropOut

        # Entry's action_db: transition_id --> command_list
        #
        #    --> now:              simply absorb all informations about 
        #                          transitions.
        #    --> in '.finalize()': adapt transitions on the path and those
        #                          which come from outside.
        #
        # DropOut:   index of represented state --> its drop out CommandList)
        #
        for state_index in (step.state_index for step in Path.step_list[:-1]):
            state = TheAnalyzer.state_db[state_index]

            self.entry.action_db.absorb(state.entry.action_db)
            self.drop_out.absorb(state_index, state.drop_out)
            # HERE: We cannot conclude anything from 'not uniform_DropOut'
            #       => NOT: assert uniform_DropOut.is_uniform() == drop_out.is_uniform()
            if self.uniform_DropOut.is_uniform(): assert self.drop_out.is_uniform()

        assert self.uniform_DropOut.is_uniform() == self.drop_out.is_uniform()

        return True

    def finalize(self, TheAnalyzer):
        """Ensure that the CommandList-s for the entries along the 
           path are properly setup. Also, determine whether those
           entries are uniform.
        """
        # Entries along the path: PathIteratorIncrement
        #                         ... but this is handled better by the code generator.
        # Entries from outside:   PathIteratorSet
        for path_id, step_list in enumerate(self.__path_list):
            prev_state_index = None
            # Terminal is not element of path => consider only 'step_list[:-1]'
            for offset, step in enumerate(step_list[:-1]):
                from_outside = PathIteratorSet(self.index, path_id, offset)

                self.entry.action_db_update(From           = prev_state_index, 
                                            To             = step.state_index, 
                                            FromOutsideCmd = from_outside,
                                            FromInsideCmd  = None)

                prev_state_index = step.state_index

        # Make sure, that the CommandList-s on the paths are organized and
        # assigned with new DoorID-s. 
        assert len(self.entry.transition_reassignment_candidate_list) > 0
        self.entry.transition_reassignment_db_construct(self.index)

        self.__finalized = PathWalkerState_ContentFinalized(self, TheAnalyzer)
        return

    @property
    def path_list(self):          
        assert type(self.__path_list) == list
        return self.__path_list

    def implemented_state_index_set(self):
        return self.__implemented_state_index_set

    def state_index_sequence(self):
        """RETURN: The sequence of involved states according to the position on
           the path that they occur. This is different from
           'implemented_state_index_set' because it maintains the 'order' and 
           it allows to associate a 'state_index' with a 'state_key'.

           It actually contain states which are not element of a path: the
           terminal states.
        """
        return self.__state_index_sequence

    def map_state_index_to_state_key(self, StateIndex):
        return self.__finalized.map_state_index_to_state_key[StateIndex]

    def map_state_key_to_state_index(self, StateKey):
        return self.__state_index_sequence[StateKey]

    @property
    def uniform_door_id(self):
        """At any step along the path commands may be executed upon entry
           into the target state. If those commands are uniform, then this
           function returns a CommandList object of those uniform commands.

           RETURNS: None, if the commands at entry of the states on the path
                          are not uniform.
        """
        return self.__finalized.uniform_door_id_along_all_paths.content

    @property
    def door_id_sequence_list(self):
        return self.__finalized.door_id_sequence_list

    @property
    def uniform_terminal_door_id(self):
        """RETURNS: DoorID -- if all paths which are involved enter the same 
                               terminal state through the same entry door.
                    None   -- if not.
        """
        return self.__finalized.uniform_terminal_door_id.content

    def delete_transitions_on_path(self):
        """Deletes all transitions that lie on the path. That is safe with respect
           to 'doors'. If doors are entered from states along the path and from 
           somewhere else, they still remain in place.
        """
        for sequence in self.__path_list:
            from_index = sequence[0].state_index
            for x in sequence[1:-1]:
                self.entry.action_db.delete(x.state_index, from_index)
                from_index = x.state_index

    def assert_consistency(self, CompressionType):
        # Each state is only implemented once.
        # => The mapping from 'state_index' to 'state_key' is 1:1.
        assert len(self.__implemented_state_index_set) == len(self.__finalized.map_state_index_to_state_key)
        for state_index in self.__implemented_state_index_set:
            assert state_index in self.__finalized.map_state_index_to_state_key

        # If uniform_DropOut is claimed, then there can be only
        # drop-out alternative--and vice versa.
        assert self.drop_out.is_uniform() == self.uniform_DropOut.is_uniform()

        # If uniform_entry_CommandList is claimed, then the DoorID must be 
        # the same along all paths--and vice versa.
        assert    (self.uniform_door_id is not None) \
               == self.uniform_entry_CommandList.is_uniform()

        # If uniformity was required, then it must have been maintained.
        if CompressionType == E_Compression.PATH_UNIFORM:
            assert self.uniform_door_id is not None
            assert self.drop_out.is_uniform()
            assert self.uniform_DropOut.is_uniform()
            assert self.uniform_entry_CommandList.is_uniform()

        # The door_id_sequence_list corresponds to the path_list.
        assert len(self.door_id_sequence_list) == len(self.path_list)
        for door_id_sequence, step_list in izip(self.door_id_sequence_list, self.path_list):
            # Path entry is not element of door_id_sequence => '-1'
            assert len(door_id_sequence) == len(step_list) - 1 

        # A CommandList at a door can at maximum contain 1 path iterator command!
        for action in self.entry.action_db.itervalues():
            path_iterator_cmd_n = 0
            for cmd in action.command_list:
                if not isinstance(cmd, (PathIteratorSet, PathIteratorIncrement)): continue
                path_iterator_cmd_n += 1
                assert path_iterator_cmd_n < 2

class PathWalkerState_ContentFinalized(object):
    __slots__ = ("map_state_index_to_state_key",
                 "uniform_door_id_along_all_paths",
                 "uniform_terminal_door_id",
                 "door_id_sequence_list")

    def __init__(self, PWState, TheAnalyzer):
        self.map_state_index_to_state_key    = self.__map_state_index_to_state_key_construct()

        self.uniform_door_id_along_all_paths = UniformObject()
        self.uniform_terminal_door_id        = UniformObject()
        self.door_id_sequence_list           = []
        for step_list in PWState.path_list:
            # Meaningful paths consist of more than one state and a terminal. 
            assert len(step_list) > 2

            door_id_sequence = self.__consider_step_list(step_list, TheAnalyzer, PWState)

            self.door_id_sequence_list.append(door_id_sequence)

        return

    def __consider_step_list(self, step_list, TheAnalyzer, PWState):
        # -- States on path
        #    (entries are considered from the second state on path on)
        door_id_sequence = []
        prev_step        = step_list[0]
        action_db        = PWState.entry.action_db
        for step in step_list[1:-1]:
            # (Recall: there is only one transition (from, to) => TriggerId == 0)
            door_id = action_db.get_door_id(step.state_index, prev_step.state_index, TriggerId=0)

            # Every DoorID on the path must be a newly-assigned one to this PathWalkerState.
            assert door_id.state_index == PWState.index

            door_id_sequence.append(door_id)
            self.uniform_door_id <<= door_id

            prev_step = step

        # -- Terminal
        step      = step_list[-1] 

        #! A terminal of one path cannot be element of another path of the
        #! same PathWalkerState. This might cause huge trouble!
        #! (Ensured by the function '.accept(Path)')
        # assert step.state_index not in PWState.implemented_state_index_set()

        action_db = TheAnalyzer.state_db[step.state_index].entry.action_db
        door_id   = action_db.get_door_id(step.state_index, prev_step.state_index, TriggerId=0)

        door_id_sequence.append(door_id)
        self.uniform_terminal_door_id <<= door_id

        return door_id_sequence

    def __map_state_index_to_state_key_construct(self):
        offset = 0
        for step_list in PWState.path_list:
            for i, step in enumerate(step_list[:-1]):
                self.map_state_index_to_state_key[step.state_index] = offset + i
            offset += len(step_list)

