from   quex.engine.analyzer.state.entry_action  import SetPathIterator, DoorID
from   quex.engine.analyzer.mega_state.core     import MegaState, MegaState_Target
from   quex.engine.state_machine.transition_map import TransitionMap
from   quex.blackboard                          import E_Compression

class PathWalkerState(MegaState):
    """A path walker state is a state that can walk along one or more paths 
       with the same 'skeleton', i.e. remaining transition map. Objects of
       this class are the basis for code generation.
    """
    def __init__(self, FirstPath, TheAnalyzer, CompressionType):

        self.__path_list = [ FirstPath.sequence() ]
        entry    = PathWalkerState.adapt_path_walker_id_and_path_id(FirstPath.index, FirstPath.entry, PathID=0)
        drop_out = FirstPath.drop_out   # map: drop_out --> state_index_list
        MegaState.__init__(self, entry, drop_out, FirstPath.index)

        self.__skeleton       = FirstPath.skeleton() # map: target_index --> trigger set
        # The skeleton does not contain wild cards anymore, so we can already transform it
        # into a transition map:                     # list: [ ... (interval, target) ... ]
        self.transition_map   = self.__determine_transition_map(self.__skeleton) 

        self.__uniformity_required_f                 = (CompressionType == E_Compression.PATH_UNIFORM)
        self.__uniform_entry_command_list_along_path = FirstPath.get_uniform_entry_command_list_along_path()

        self.__state_index_sequence = None # Computed on demand

    def __determine_transition_map(self, Skeleton):
        """Transforms a 'skeleton', i.e. a map:

                target-door  -->  NumberSet that triggers to it

           into a transition map, i.e. a list of tuples

                (interval, MegaState_Target)

           which represents the same mapping in a 'linear' manner.
        """
        def adapt(Target):
            if isinstance(Target, DoorID): return Target.state_index
            return Target
        return [ (interval, MegaState_Target.create(adapt(target))) \
                 for interval, target in TransitionMap(Skeleton).get_trigger_map() ]

    def accept(self, Path, StateDB):
        """Accepts the given Path to be walked, if the skeleton matches.
           If additionally uniformity is required, then only states with
           same drop_out and entry are accepted.
        """
        def __transition_maps_equal(A, B):
            if set(A.iterkeys()) != set(B.iterkeys()): return False
            for key, trigger_set in A.iteritems():
                if not trigger_set.is_equal(B[key]): return False
            return True

        # (1) Compare the transition maps, i.e. the 'skeletons'.
        #     If they do not fit, refuse immediately.
        if not __transition_maps_equal(self.__skeleton, Path.skeleton()): 
            return False

        # (1b) If uniformity is required and not maintained, then refuse.
        #      Uniformity: -- There exists uniformity in all previously accepted 
        #                     paths. 
        #                  -- There is a uniform command list along the path
        #                  -- The uniform command list is equivalent with the 
        #                     existing one.
        uniform_entry_f = False
        if self.__uniform_entry_command_list_along_path is not None:
            uniform_entry = Path.get_uniform_entry_command_list_along_path()
            if     uniform_entry is not None \
               and uniform_entry.is_equivalent(self.__uniform_entry_command_list_along_path):
                    uniform_entry_f = True

        if self.__uniformity_required_f:
            # If uniformity is required, then a non-uniform entry should never been
            # accepted. Thus, there **must** be a 'uniform_entry_door_id_along_all_paths'.
            assert self.__uniform_entry_command_list_along_path is not None
            # If uniformity is a required, more than one drop-out scheme should never
            # been accepted. 
            assert len(Path.drop_out) == 1 

            # (*) Check Entry Uniformity
            if   not uniform_entry_f:            return False
            # (*) Check Drop-Out Uniformity
            elif self.drop_out != Path.drop_out: return False

        if uniform_entry_f == False:
            self.__uniform_entry_command_list_along_path = None

        # (2)  Absorb the Path
        #      The path_id of the path to be added is the length of the current path list.
        #      (This means: new last index = current size of the list.)
        path_id = len(self.__path_list) 

        # (2a) Absorb the state sequence of the path
        #      (verify/falsify the uniform terminal entry)
        self.__path_list.append(Path.sequence())

        # (2b) Absorb Entry Information
        #      Absorb entry's action_db (maps: 'transition_id --> command_list')
        adapted_entry = PathWalkerState.adapt_path_walker_id_and_path_id(self.index, Path.entry, PathID=path_id)
        self.entry.action_db.update(adapted_entry.action_db)

        # (2c) Absorb the drop-out information
        self.drop_out.update_from_other(Path.drop_out)

        return True

    @staticmethod
    def adapt_path_walker_id_and_path_id(PathWalkerIndex, TheEntry, PathID):
        """Ensure that any 'SetPathIterator' contains the right references
           to the pathwalker and path id.
        """
        for action in TheEntry.action_db.itervalues():
            found_f = False
            for command in action.command_list:
                if isinstance(command, SetPathIterator):
                    assert not found_f # Double check that there are not more than one 
                    #                  # such command per command_list.
                    found_f = True
                    command.set_path_walker_id(PathWalkerIndex)
                    command.set_path_id(PathID)
                    # There shall not be more then one 'SetPathIterator' command 
                    # for one transition.

        return TheEntry

    @property
    def path_list(self):          
        assert type(self.__path_list) == list
        return self.__path_list

    def implemented_state_index_list(self):
        result = [] # **MUST** be a list, because we might identify 'state_keys' with it.
        for path in self.__path_list:
            # The end state of each path is not implemented
            # (It may be part of another path, though)
            result.extend(map(lambda x: x[0], path[:-1]))
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
                result.extend(map(lambda x: x[0], path))
            self.__state_index_sequence = result
        return self.__state_index_sequence

    @property
    def uniform_entries_f(self):   
        assert False, "Use: uniform_entry_door_id_along_all_paths"

    @property
    def uniform_entry_command_list_along_all_paths(self):
        """At any step along the path commands may be executed upon entry
           into the target state. If those commands are uniform, then this
           function returns a CommandList object of those uniform commands.

           RETURNS: None, if the commands at entry of the states on the path
                          are not uniform.
        """
        return self.__uniform_entry_command_list_along_path

    @property
    def uniform_entry_door_id_along_all_paths(self):   
        """RETURNS: -- An 'CommandList' object if it is common for all paths.
                    -- None, the entries along the paths are somehow differring.
        """
        if self.__uniform_entry_command_list_along_path is None: return None

        door_id = self.entry.get_door_id_by_command_list(self.__uniform_entry_command_list_along_path)

        assert door_id is not None, "There MUST be a door for the uniform entry command list."
        return door_id

    @staticmethod
    def get_terminal_door_id(Path, StateDB):
        """Determine the DoorID by which the path number 'PathID' enters
           the terminal state of the path (which is not implemented by 
           the pathwalker).
        """
        assert len(Path) >= 2

        before_terminal_state_index = Path[-2][0]
        terminal_state_index        = Path[-1][0]
        # Determine DoorID by transition
        return StateDB[terminal_state_index].entry.get_door_id(terminal_state_index, 
                                                               before_terminal_state_index)

    def get_uniform_terminal_entry_door_id(self, StateDB):
        """RETURNS: DoorID -- if all paths which are involved enter the same 
                               terminal state through the same entry door.
                    None   -- if not.
        """
        prototype = None
        for sequence in self.__path_list:
            if prototype is None:
                prototype = PathWalkerState.get_terminal_door_id(sequence, StateDB)
            elif prototype != PathWalkerState.get_terminal_door_id(sequence, StateDB):
                return None
        return prototype

    def get_path_info(self, StateIdx):
        """[0] Path ID: Index of the path where StateIdx is located
                        (This can only be one)
           [1] Path Offset: Position of StateIdx in its path.
           [2] Base Offset: Position of StateIdx in the path walkers
                            character sequence 'base'.
        """
        for path_id, path in enumerate(self.__path_list):
            # Last state path[-1][0] is the first state after path is terminated.
            for path_offset, candidate in enumerate(path[:-1]):
                if candidate[0] == StateIdx: return path_id, path_offset
        assert False

    def delete_transitions_on_path(self):
        """Deletes all transitions that lie on the path. That is safe with respect
           to 'doors'. If doors are entered from states along the path and from 
           somewhere else, they still remain in place.
        """
        for sequence in self.__path_list:
            from_index = sequence[0][0]
            for state_index, dummy in sequence[1:-1]:
                self.entry.action_db_delete_transition(state_index, from_index)
                from_index = state_index

