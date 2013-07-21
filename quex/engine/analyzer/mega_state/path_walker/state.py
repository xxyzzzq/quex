# (C) 2010-2013 Frank-Rene Schaefer
from   quex.engine.analyzer.transition_map      import TransitionMap   
from   quex.engine.analyzer.state.entry_action  import SetPathIterator, DoorID
from   quex.engine.analyzer.mega_state.core     import MegaState, MegaState_Target
import quex.engine.state_machine.index          as     index
from   quex.engine.tools                        import uniformity_check_and_set
from   quex.blackboard                          import E_Compression

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
        print "#reascl:", FirstPath.entry.transition_reassignment_candidate_list

        MegaState.__init__(self, FirstPath.entry, FirstPath.drop_out, my_index)


        self.__path_list = [ FirstPath.sequence ]

        # original_transition_map: interval --> DoorID
        #
        #     '.accept(...)' requires a 'DoorID - transition_map' for 
        #     comparison. Thus, keep original transition map as reference.
        #
        # transition_map:          interval --> MegaState_Target
        self.__transition_map_to_door_ids           = FirstPath.transition_map
        self.__transition_map_to_mega_state_targets =                          \
                TransitionMap.from_iterable(self.__transition_map_to_door_ids, \
                                            MegaState_Target.create)

        self.__uniformity_required_f                 = (CompressionType == E_Compression.PATH_UNIFORM)
        self.__uniform_entry_command_list_along_path = FirstPath.uniform_entry_command_list_along_path

        self.__state_index_sequence    = None # Computed on demand

        # Following are set by 'finalize()'.
        self.__uniform_door_id          = -1
        self.__uniform_terminal_door_id = -1
        self.__door_id_sequence         = -1

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
        print "#reascl:", Path.entry.transition_reassignment_candidate_list
        self.entry.absorb(Path.entry)

        # (2b) Absorb the state sequence of the path
        #      (verify/falsify the uniform terminal entry)
        self.__path_list.append(Path.sequence)

        # (2c) Absorb the drop-out information
        self.drop_out.update(Path.drop_out.iteritems())

        return True

    def finalize(self):
        """Ensure that the CommandList-s for the entries along the 
           path are properly setup. Also, determine whether those
           entries are uniform.
        """
        # First make sure, that the CommandList-s on the paths are organized
        # and assigned with new DoorID-s.
        self.entry.transition_reassignment_db_construct(self.index)

        # Determine uniformity and the door_id_sequence.
        uniform_door_id          = -1 # Not yet set.
        uniform_terminal_door_id = -1 # Not yet set.
        door_id_sequence         = []
        for path in self.__path_list:

            for step in path[:-1]:
                # DoorID -- replace old be new.
                print "#step:", step
                new_door_id = self.entry.transition_reassignment_db.get_replacement(step.state_index, 
                                                                                    step.door_id)
                assert new_door_id is not None
                door_id_sequence.append(new_door_id)

                # CommandList -- consider unformity expressed as uniform door_id.
                uniform_door_id = uniformity_check_and_set(uniform_door_id, new_door_id)

            # DoorID -- replace old be new.
            step = path[-1]
            new_door_id = self.entry.transition_reassignment_db.get_replacement(step.state_index, 
                                                                                step.door_id, 
                                                                                Default=step.door_id)
            door_id_sequence.append(new_door_id)

            # Terminal DoorID uniform?
            uniform_terminal_door_id = uniformity_check_and_set(uniform_terminal_door_id, 
                                                                new_door_id)

        self.__uniform_door_id_along_all_paths = uniform_door_id
        self.__uniform_terminal_door_id        = uniform_terminal_door_id
        self.__door_id_sequence                = door_id_sequence

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
    def door_id_sequence(self):
        return self.__door_id_sequence

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

