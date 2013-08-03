# (C) 2010-2013 Frank-Rene Schaefer
from   quex.engine.analyzer.transition_map      import TransitionMap   
from   quex.engine.analyzer.state.entry_action  import SetPathIterator, DoorID
from   quex.engine.analyzer.mega_state.core     import MegaState, MegaState_Transition
import quex.engine.state_machine.index          as     index
from   quex.engine.tools                        import UniformObject
from   quex.blackboard                          import E_Compression

from   itertools import izip

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
        FirstPath.entry.adapt_SetStateKey(my_index, PathID=0)

        MegaState.__init__(self, FirstPath.entry, FirstPath.drop_out, my_index)


        self.__path_list = [ FirstPath.step_list ]

        # original_transition_map: interval --> DoorID
        #
        #     '.accept(...)' requires a 'DoorID - transition_map' for 
        #     comparison. Thus, keep original transition map as reference.
        #
        # transition_map:          interval --> MegaState_Transition
        self.__transition_map_to_door_ids           = FirstPath.transition_map
        self.__transition_map_to_mega_state_targets =                          \
                TransitionMap.from_iterable(self.__transition_map_to_door_ids, \
                                            MegaState_Transition.create)

        # Uniform CommandList along entries on the path (optional)
        self.__uniformity_required_f                 = (CompressionType == E_Compression.PATH_UNIFORM)
        self.__uniform_entry_command_list_along_path = \
                FirstPath.uniform_entry_command_list_along_path
        assert not self.__uniformity_required_f \
               or  self.__uniform_entry_command_list_along_path is not None

        self.__state_index_sequence    = None # Computed on demand

        # Following are set by 'finalize()'.
        self.__uniform_door_id_along_all_paths = None
        self.__uniform_terminal_door_id        = None
        self.__door_id_sequence_list           = None

    @property
    def transition_map(self):
        return self.__transition_map_to_mega_state_targets 

    def accept(self, Path):
        """Accepts the given Path to be walked, if the remaining transition_maps
        match. If additionally uniformity is required, then only states with
        same drop_out and entry are accepted.

        RETURNS: False -- Path does not fit the PathWalkerState.
                 True  -- Path can be walked by PathWalkerState and has been 
                          accepted.
        """
        # (1) Compare the transition maps.
        if not self.__transition_map_to_door_ids.is_equal(Path.transition_map): 
            return False

        # (1b) If uniformity is required and not maintained, then refuse.
        #      Uniformity: -- There exists uniformity in all previously accepted 
        #                     paths. 
        #                  -- There is a uniform command list along the path
        #                  -- The uniform command list is equivalent with the 
        #                     existing one.
        uniform_entry_f = False
        if self.__uniform_entry_command_list_along_path is not None:
            # other_ueclap := other's .__uniform_entry_command_list_along_path
            other_ueclap = Path.uniform_entry_command_list_along_path
            if     other_ueclap is not None \
               and other_ueclap.is_equivalent(self.__uniform_entry_command_list_along_path):
                    uniform_entry_f = True

        if self.__uniformity_required_f:
            # If uniformity is required, then a non-uniform entry should never been
            # accepted. Thus, there **must** be a 'uniform_door_id'.
            assert self.__uniform_entry_command_list_along_path is not None
            # If uniformity is a required, more than one drop-out scheme should never
            # been accepted. 
            assert len(Path.drop_out) == 1, repr(Path.drop_out)

            # (*) Check Entry Uniformity
            if   not uniform_entry_f:            return False
            # (*) Check Drop-Out Uniformity
            elif self.drop_out != Path.drop_out: return False

        # (**) HERE: We ACCEPT the Path!

        if uniform_entry_f == False:
            self.__uniform_entry_command_list_along_path = None

        # (2)  Absorb the Path
        #      The path_id of the path to be added is the length of the current path list.
        #      (This means: new last index = current size of the list.)
        path_id = len(self.__path_list) 

        # (2a) Absorb Entry Information
        #      Absorb entry's action_db (maps: 'transition_id --> command_list')
        Path.entry.adapt_SetStateKey(self.index, PathID=path_id)
        self.entry.absorb(Path.entry)

        # (2b) Absorb the state sequence of the path
        #      (Meaningful paths consist of more than one state and a terminal.)
        assert len(Path.step_list) > 2
        self.__path_list.append(Path.step_list)

        # (2c) Absorb the drop-out information
        self.drop_out.update(Path.drop_out.iteritems())

        return True

    def finalize(self, TheAnalyzer):
        """Ensure that the CommandList-s for the entries along the 
           path are properly setup. Also, determine whether those
           entries are uniform.
        """
        # First make sure, that the CommandList-s on the paths are organized
        # and assigned with new DoorID-s.
        self.entry.transition_reassignment_db_construct(self.index)

        # Determine uniformity and the door_id_sequence.
        uniform_door_id          = UniformObject()
        uniform_terminal_door_id = UniformObject()

        print "#action_db:", [x for x, y in self.entry.action_db.iteritems()]
        self.__door_id_sequence_list = []
        for step_list in self.__path_list:
            # Meaningful paths consist of more than one state and a terminal. 
            assert len(step_list) > 2

            door_id_sequence = []
            prev_step        = step_list[0]
            action_db        = self.entry.action_db
            for step in step_list[1:-1]:
                # (Recall: there is only one transition (from, to) => TriggerId == 0)
                door_id = action_db.get_door_id(step.state_index, prev_step.state_index, TriggerId=0)
                print "# %s->%s: %s" % (prev_step.state_index, step.state_index, door_id)

                door_id_sequence.append(door_id)
                uniform_door_id <<= door_id

                prev_step = step

            step           = step_list[-1] # Terminal
            terminal_state = TheAnalyzer.state_db[step.state_index]
            action_db      = terminal_state.entry.action_db
            door_id        = action_db.get_door_id(step.state_index, prev_step.state_index, TriggerId=0)

            door_id_sequence.append(door_id)
            uniform_terminal_door_id <<= door_id

            print "# %s->%s: %s" % (prev_step.state_index, step.state_index, door_id)
            print "#step_list:", [ x.state_index for x in step_list ]
            print "#door_id_sequence:", door_id_sequence
            self.__door_id_sequence_list.append(door_id_sequence)

        self.__uniform_door_id_along_all_paths = uniform_door_id.content
        self.__uniform_terminal_door_id        = uniform_terminal_door_id.content

    @property
    def path_list(self):          
        assert type(self.__path_list) == list
        return self.__path_list

    def implemented_state_index_list(self):
        result = [] # **MUST** be a list, because we might identify 'state_keys' with it.
        for path in self.__path_list:
            # The end state of each path is not implemented
            # (It may be part of another path, though)
            result.extend(x.state_index for x in path)
        return result

    def map_state_index_to_state_key(self, StateIndex):
        return self.state_index_sequence().index(StateIndex)

    def map_state_key_to_state_index(self, StateKey):
        return self.state_index_sequence()[StateKey]

    def state_index_sequence(self):
        """RETURN: The sequence of involved states according to the position on
           the path that they occur. This is different from
           'implemented_state_index_list' because it maintains the 'order' and 
           it allows to associate a 'state_index' with a 'state_key'.
        """
        if self.__state_index_sequence is None:
            result = [] # **MUST** be a list, because we identify 'state_keys' with it.
            for path in self.__path_list:
                result.extend(x.state_index for x in path)
            self.__state_index_sequence = result
        return self.__state_index_sequence

    @property
    def uniform_door_id(self):
        """At any step along the path commands may be executed upon entry
           into the target state. If those commands are uniform, then this
           function returns a CommandList object of those uniform commands.

           RETURNS: None, if the commands at entry of the states on the path
                          are not uniform.
        """
        return self.__uniform_door_id_along_all_paths

    @property
    def door_id_sequence_list(self):
        assert len(self.__path_list) == len(self.__door_id_sequence_list)
        for path, door_id_sequence in izip(self.__path_list, self.__door_id_sequence_list):
            assert len(path) == len(door_id_sequence) + 1
        return self.__door_id_sequence_list

    @property
    def uniform_terminal_door_id(self):
        """RETURNS: DoorID -- if all paths which are involved enter the same 
                               terminal state through the same entry door.
                    None   -- if not.
        """
        return self.__uniform_terminal_door_id

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

