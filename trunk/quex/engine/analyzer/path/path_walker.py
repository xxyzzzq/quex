from   quex.engine.analyzer.core                import AnalyzerState
from   quex.engine.analyzer.state_entry_action  import SetPathIterator
from   quex.engine.state_machine.transition_map import TransitionMap
import quex.engine.state_machine.index          as     index
from   quex.blackboard                          import \
                                                       E_EngineTypes, \
                                                       E_InputActions, \
                                                       E_Compression

from itertools import imap
from operator  import itemgetter

class PathWalkerState(AnalyzerState):
    """A path walker state is a state that can walk along one or more paths 
       with the same 'skeleton', i.e. remaining transition map. Objects of
       this class are the basis for code generation.
    """
    def __init__(self, FirstPath, EngineType, CompressionType):
        AnalyzerState.set_index(self, index.get())
        AnalyzerState.set_engine_type(self, EngineType)

        self.__path_list      = [ FirstPath.sequence() ]
        self.entry            = self.__adapt_path_walker_id_and_path_id(FirstPath.entry, PathID=0)
        self.drop_out         = FirstPath.drop_out   # map: drop_out --> state_index_list
        self.__skeleton       = FirstPath.skeleton() # map: target_index --> trigger set
        # The skeleton does not contain wild cards anymore, so we can already transform it
        # into a transition map:                     # list: [ ... (interval, target) ... ]
        self.__transition_map = TransitionMap(self.__skeleton).get_trigger_map()

        self.input = { 
            E_EngineTypes.FORWARD:                 E_InputActions.INCREMENT_THEN_DEREF,
            E_EngineTypes.BACKWARD_PRE_CONTEXT:    E_InputActions.DECREMENT_THEN_DEREF,
            E_EngineTypes.BACKWARD_INPUT_POSITION: E_InputActions.DECREMENT_THEN_DEREF,
        }[EngineType]

        self.__uniformity_required_f = (CompressionType == E_Compression.PATH_UNIFORM)
        if not self.__uniformity_required_f:
            # If uniformity is not a required, then there's no need to compute the
            # uniform entry along path of any character path.
            self.__uniform_entry_along_all_paths = None 
        else:
            self.__uniform_entry_along_all_paths = FirstPath.uniform_entry_along_path

        self.__state_index_list     = None # Computed on demand
        self.__end_state_index_list = None # Computed on demand

    @property
    def init_state_f(self): 
        return False

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
        if self.__uniformity_required_f:
            # If uniformity is required, then a non-uniform entry should never been
            # accepted. Thus, there **must** be a 'uniform_entry_along_all_paths'.
            assert self.__uniform_entry_along_all_paths is not None
            # If uniformity is a required, more than one drop-out scheme should never
            # been accepted. 
            assert len(Path.drop_out) == 1 

            # (*) Check Entry Uniformity
            if Path.uniform_entry_along_path is None:
                return False
            elif not Path.uniform_entry_along_path.is_equivalent(self.__uniform_entry_along_all_paths):
                return False
            # (*) Check Drop-Out Uniformity
            elif self.drop_out != Path.drop_out: 
                return False

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
            assert sequence[-1][0] not in state_index_list
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
    def transition_map(self):     return self.__transition_map
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

    @property
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
        assert False, "Use: uniform_entry_along_all_paths"

    @property
    def uniform_entry_along_all_paths(self):   
        """RETURNS: -- An 'CommandList' object if it is common for all paths.
                    -- None, the entries along the paths are somehow differring.
        """
        return self.__uniform_entry_along_all_paths

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
        door_id = self.entry.get_door_id(StateIndex     = terminal_state_index, 
                                         FromStateIndex = before_terminal_state_index)

    def terminal_door_id_is_same_f(self):
        """RETURNS: True  -- if all paths which are involved enter the same 
                             terminal state through the same entry door.
                    False -- if not.
        """
        assert len(self.path_list) != 0
        if len(self.path_list) == 1:
            return True

        prototype = None
        for path_id in xrange(len(self.__path_list)):
            # Determine door entered from last but one to last state on the path
            door_id = self.terminal_door_of_path(path_id)
            if prototype is None: 
                prototype = door_id
            elif not (prototype == door_id):
                return False
        return True

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

    def state_set_iterable(self, StateIndexList, TheAnalyzer):
        def help(StateIdx):
            path_id, path_offset = self.get_path_info(StateIdx)
            return (StateIdx, path_id, path_offset, TheAnalyzer.state_db[StateIdx])

        return sorted(imap(help, StateIndexList), key=itemgetter(1, 2)) # Sort by 'path_id', 'path_offset'

    def replace_door_ids_in_transition_map(self, ReplacementDB):
        pass # Do nothing for the moment

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
            path_walker_list.append(PathWalkerState(candidate, TheAnalyzer.engine_type, CompressionType))

    return path_walker_list
