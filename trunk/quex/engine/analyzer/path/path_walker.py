from   quex.engine.analyzer.state_entry_action  import SetPathIterator, DoorID, TransitionID, TransitionAction
from   quex.engine.analyzer.mega_state          import MegaState
from   quex.engine.state_machine.transition_map import TransitionMap
from   quex.blackboard                          import \
                                                       E_EngineTypes, \
                                                       E_InputActions, \
                                                       E_Compression, \
                                                       E_StateIndices

class PathWalkerState(MegaState):
    """A path walker state is a state that can walk along one or more paths 
       with the same 'skeleton', i.e. remaining transition map. Objects of
       this class are the basis for code generation.
    """
    def __init__(self, FirstPath, TheAnalyzer, CompressionType):
        MegaState.__init__(self, TheAnalyzer)

        self.__path_list      = [ FirstPath.sequence() ]
        self.entry            = self.__adapt_path_walker_id_and_path_id(FirstPath.entry, PathID=0)
        self.drop_out         = FirstPath.drop_out   # map: drop_out --> state_index_list
        self.__skeleton       = FirstPath.skeleton() # map: target_index --> trigger set
        # The skeleton does not contain wild cards anymore, so we can already transform it
        # into a transition map:                     # list: [ ... (interval, target) ... ]
        self.transition_map   = TransitionMap(self.__skeleton).get_trigger_map()

        self.input = { 
            E_EngineTypes.FORWARD:                 E_InputActions.INCREMENT_THEN_DEREF,
            E_EngineTypes.BACKWARD_PRE_CONTEXT:    E_InputActions.DECREMENT_THEN_DEREF,
            E_EngineTypes.BACKWARD_INPUT_POSITION: E_InputActions.DECREMENT_THEN_DEREF,
        }[TheAnalyzer.engine_type]

        self.__uniformity_required_f = (CompressionType == E_Compression.PATH_UNIFORM)
        self.__uniform_entry_command_list_along_path = FirstPath.get_uniform_entry_command_list_along_path()

        self.__state_index_list     = None # Computed on demand
        self.__end_state_index_list = None # Computed on demand

    def accept(self, Path):
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
        # (*) Check Entry Uniformity
        if self.__uniform_entry_command_list_along_path is None:
            uniform_entry_f = False
        else:
            uniform_entry = Path.get_uniform_entry_command_list_along_path()
            if uniform_entry is None:
                uniform_entry_f = False
            elif not uniform_entry.is_equivalent(self.__uniform_entry_command_list_along_path):
                uniform_entry_f = False
            else:
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
        self.__path_list.append(Path.sequence())

        # (2b) Absorb Entry Information
        #      Absorb entry's action_db (maps: 'transition_id --> command_list')
        adapted_entry = self.__adapt_path_walker_id_and_path_id(Path.entry, PathID=path_id)
        self.entry.action_db.update(adapted_entry.action_db)

        # (2c) Absorb the drop-out information
        #      Absorb drop-out information
        for drop_out, state_index_list in Path.drop_out.iteritems():
            self.drop_out[drop_out].update(state_index_list) 

        return True

    def __adapt_path_walker_id_and_path_id(self, TheEntry, PathID):
        """Ensure that any 'SetPathIterator' contains the right references
           to the pathwalker and path id.
        """
        for action in TheEntry.action_db.itervalues():
            for command in action.command_list:
                if isinstance(command, SetPathIterator):
                    command.set_path_walker_id(self.index)
                    command.set_path_id(PathID)
        return TheEntry

    @property
    def path_list(self):          assert type(self.__path_list) == list; return self.__path_list

    @property
    def state_index_list(self):
        """map:   state_key --> state_index of involved state
        """
        if self.__state_index_list is None:
            result = [] # **MUST** be a list, because we identify 'state_keys' with it.
            for path in self.__path_list:
                result.extend(map(lambda x: x[0], path))
            self.__state_index_list = result
        return self.__state_index_list

    def implemented_state_index_list(self):
        """This is different from 'state_index_list', because the end state
           of a path is not implemented!
        """
        result = [] # **MUST** be a list, because we might identify 'state_keys' with it.
        for path in self.__path_list:
            # The end state of each path is not implemented
            # (It may be part of another path, though)
            result.extend(map(lambda x: x[0], path[:-1]))
        return result

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

    def terminal_door_id_of_path(self, PathID):
        """Determine the DoorID by which the path number 'PathID' enters
           the terminal state of the path (which is not implemented by 
           the pathwalker).
        """
        sequence = self.__path_list[PathID]
        assert len(sequence) >= 2

        before_terminal_state_index = sequence[-2][0]
        terminal_state_index        = sequence[-1][0]
        # Determine DoorID by transition
        return self.analyzer.state_db[terminal_state_index].entry.get_door_id(terminal_state_index, 
                                                                              before_terminal_state_index)

    @property
    def uniform_terminal_entry_door_id(self):
        """RETURNS: DoorID -- if all paths which are involved enter the same 
                               terminal state through the same entry door.
                    None   -- if not.
        """
        assert len(self.path_list) != 0
        if len(self.__path_list) == 1:
            return self.terminal_door_id_of_path(0)

        prototype = None
        for path_id in xrange(len(self.__path_list)):
            # Determine door entered from last but one to last state on the path
            door_id = self.terminal_door_id_of_path(path_id)
            if prototype is None: 
                prototype = door_id
            elif not (prototype == door_id):
                return None
        return prototype

    @property
    def uniform_drop_outs_f(self): 
        return len(self.drop_out) == 1

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

    def replace_door_ids_in_transition_map(self, ReplacementDB):
        """See TemplateState, for more information."""
        def replace_if_required(DoorId):
            replacement = ReplacementDB.get(DoorId)
            if replacement is not None: return replacement
            return DoorId

        for i, info in enumerate(self.transition_map):
            interval, target = info

            if target == E_StateIndices.DROP_OUT: continue
            assert isinstance(target, DoorID)

            new_door_id = ReplacementDB.get(target)
            if new_door_id is not None:
                self.transition_map[i] = (interval, new_door_id)

def group(CharacterPathList, TheAnalyzer, CompressionType):
    """Different character paths may be walked down by the same pathwalker, if
       certain conditions are met. This function groups the given list of
       character paths and assigns them to PathWalkerState-s. The PathWalkerState-s
       can then immediately be used for code generation.
    """
    path_walker_list = []
    for candidate in CharacterPathList:
        for path_walker in path_walker_list:
            if path_walker.accept(candidate): break
        else:
            path_walker_list.append(PathWalkerState(candidate, TheAnalyzer, CompressionType))

    for path_walker in path_walker_list:
        if path_walker.uniform_entry_command_list_along_all_paths is not None:
            # Assign the uniform command list to the transition 'path_walker -> path_walker'
            transition_action = TransitionAction(path_walker.index, path_walker.index, path_walker.uniform_entry_command_list_along_all_paths)
            # Delete transitions on the path itself => No doors for them will be implemented.
            path_walker.delete_transitions_on_path()
        else:
            # Nothing special to be done upon iteration over the path
            transition_action = TransitionAction(path_walker.index, path_walker.index)

        transition_id = TransitionID(path_walker.index, path_walker.index)
        path_walker.entry.action_db[transition_id] = transition_action

        # Once the entries are combined, re-configure the door tree
        path_walker.entry.door_tree_configure(path_walker.index)

    return path_walker_list
