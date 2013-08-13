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

class PathWalkerState_ContentFinalized(object):
    def __init__(self, PWState, TheAnalyzer):

        self.uniform_door_id_along_all_paths = None
        self.uniform_terminal_door_id        = None
        self.door_id_sequence_list           = []

        # First make sure, that the CommandList-s on the paths are organized
        # and assigned with new DoorID-s. Assume, that 
        # 'transition_reassignment_candidate_list' has been set properly.
        assert len(PWState.entry.transition_reassignment_candidate_list) > 0
        PWState.entry.transition_reassignment_db_construct(PWState.index)

        # Determine uniformity and the door_id_sequence.
        uniform_door_id          = UniformObject()
        uniform_terminal_door_id = UniformObject()

        for step_list in PWState.path_list:
            # Meaningful paths consist of more than one state and a terminal. 
            assert len(step_list) > 2

            # -- States on path
            #    (entries are considered from the second state on path on)
            door_id_sequence = []
            prev_step        = step_list[0]
            action_db        = PWState.entry.action_db
            for step in step_list[1:-1]:
                # (Recall: there is only one transition (from, to) => TriggerId == 0)
                door_id = action_db.get_door_id(step.state_index, prev_step.state_index, TriggerId=0)

                # Every DoorID on the path must be a new-assigned one to this PathWalkerState.
                assert door_id.state_index == PWState.index, \
                       "From: %s; To: %s; --> DoorID: %s" % (prev_step.state_index, step.state_index, door_id)

                door_id_sequence.append(door_id)
                uniform_door_id <<= door_id

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
            uniform_terminal_door_id <<= door_id

            self.door_id_sequence_list.append(door_id_sequence)

        self.uniform_door_id_along_all_paths = uniform_door_id.content
        self.uniform_terminal_door_id        = uniform_terminal_door_id.content

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

    During analysis, only the '.action_db' is of interest. There the 
    'PathIteratorSet' command is to each TransitionAction's CommandList. The
    command lists 'equal' and 'not-equal' relationships remain the same, since
    the 'PathIteratorSet' for all TransitionAction of a given state. Thus,
    the DoorID objects can act as unique identifiers of command lists.
    ___________________________________________________________________________
    """
    def __init__(self):
        MegaState_Entry.__init__(self)

    def action_db_update(self, From, To, FromOutsideCmd, FromInsideCmd):
        """Include 'TheState.entry.action_db' into this state. That means,
        that any mappings:
           
             transition (StateIndex, FromStateIndex) --> CommandList 

        is ABSORBED AS THEY ARE from  'TheEntry.action_db'.  Additionally, any
        command list must contain the 'PathIteratorSet' command that sets the
        state key for represented state. At each (external) entry into the path
        walker state the 'state_key' must be set, so that it can mimik the
        represented state.
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
    ___________________________________________________________________________
    """
    def __init__(self, FirstPath, TheAnalyzer, CompressionType):
        # Overtake '.entry' and '.drop_out' from the 'FirstPath'. 
        # ('FirstPath' will no longer be referenced elsewhere.)
        my_index = index.get()

        MegaState.__init__(self, PathWalkerState_Entry(), MegaState_DropOut(), my_index)

        # Uniform CommandList along entries on the path (optional)
        self.__uniformity_required_f   = (CompressionType == E_Compression.PATH_UNIFORM)
        self.uniform_entry_CommandList = FirstPath.uniform_entry_CommandList
        self.uniform_DropOut           = FirstPath.uniform_DropOut
        assert not self.__uniformity_required_f \
               or  self.uniform_entry_CommandList.content is not None

        self.__path_list                   = []
        self.__implemented_state_index_set = set()
        self.__state_index_sequence        = []
        self.absorb_path(FirstPath, TheAnalyzer)

        self.__transition_map_to_door_ids = FirstPath.transition_map

        # Following are set by 'finalize()'.
        self.__finalized = None # <-- PathWalkerState_ContentFinalized()

    @property
    def transition_map(self):
        return TransitionMap.from_iterable(self.__transition_map_to_door_ids, \
                                           MegaState_Transition.create)

    def accept(self, Path, TheAnalyzer):
        """Accepts the given Path to be walked, if the remaining transition_maps
        match. If additionally uniformity is required, then only states with
        same drop_out and entry are accepted.

        RETURNS: False -- Path does not fit the PathWalkerState.
                 True  -- Path can be walked by PathWalkerState and has been 
                          accepted.
        """
        # (1) Check conditions for acceptance

        # (1.1) Compare the transition maps.
        if not self.__transition_map_to_door_ids.is_equal(Path.transition_map): 
            return False

        # (1.2) If uniformity is required, check it!
        if self.__uniformity_required_f:
            if    (not self.uniform_entry_CommandList.fit(Path.uniform_entry_CommandList)) \
               or (not self.uniform_DropOut.fit(Path.uniform_entry_CommandList)):
                return False

        # (2)   Path has been accepted.
        #
        # (2.1) Absorb information about uniformity.
        self.uniform_entry_CommandList <<= Path.uniform_entry_CommandList
        self.uniform_DropOut           <<= Path.uniform_DropOut

        # (2.2) Absorb the steps on the path
        self.absorb_path(Path, TheAnalyzer)
        return True

    def absorb_path(self, Path, TheAnalyzer):

        # (1) Absorb the state sequence of the path
        #     Resulting data is required (1) for decisions made in (2).

        # (Meaningful paths consist of more than one state and a terminal.)
        assert len(Path.step_list) > 2
        self.__path_list.append(Path.step_list)

        new_state_index_list            = [x.state_index for x in Path.step_list]
        new_implemented_state_index_set = set(new_state_index_list[:-1])

        # (A state cannot be implemented by two different paths)
        assert set(self.__implemented_state_index_set).isdisjoint(new_implemented_state_index_set), \
               "%s & %s != empty" % (self.__implemented_state_index_set, new_implemented_state_index_set)
        self.__state_index_sequence.extend(new_state_index_list)
        self.__implemented_state_index_set.update(new_implemented_state_index_set)

        # (2) Absorb Entry/DropOut Information
        #     Entry's action_db (maps: 'transition_id --> command_list')
        for step in Path.step_list[:-1]:
            state     = TheAnalyzer.state_db[step.state_index]

            self.entry.action_db.absorb(state.entry.action_db)
            self.drop_out.absorb(step.state_index, state.drop_out)

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

        # A CommandList at a door can at maximum contain 1 path iterator command!
        for action in self.entry.action_db.itervalues():
            path_iterator_cmd_n = 0
            for cmd in action.command_list:
                if not isinstance(cmd, (PathIteratorSet, PathIteratorIncrement)): continue
                path_iterator_cmd_n += 1
                assert path_iterator_cmd_n < 2

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
        return self.state_index_sequence().index(StateIndex)

    def map_state_key_to_state_index(self, StateKey):
        return self.state_index_sequence()[StateKey]

    @property
    def uniform_door_id(self):
        """At any step along the path commands may be executed upon entry
           into the target state. If those commands are uniform, then this
           function returns a CommandList object of those uniform commands.

           RETURNS: None, if the commands at entry of the states on the path
                          are not uniform.
        """
        return self.__finalized.uniform_door_id_along_all_paths

    @property
    def door_id_sequence_list(self):
        return self.__finalized.door_id_sequence_list

    @property
    def uniform_terminal_door_id(self):
        """RETURNS: DoorID -- if all paths which are involved enter the same 
                               terminal state through the same entry door.
                    None   -- if not.
        """
        return self.__finalized.uniform_terminal_door_id

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

