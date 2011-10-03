from   quex.engine.analyzer.core                import AnalyzerState
from   quex.engine.state_machine.transition_map import TransitionMap
import quex.engine.state_machine.index          as     index
from   quex.blackboard                          import setup as Setup, \
                                                       E_EngineTypes, \
                                                       E_InputActions, \
                                                       E_Compression

from itertools import imap, ifilter
from operator  import itemgetter

class PathWalkerState(AnalyzerState):
    """A path walker state is a state that can walk along one or more paths 
       with the same 'skeleton', i.e. remaining transition map. Objects of
       this class are the basis for code generation.
    """
    def __init__(self, FirstPath, EngineType, CompressionType):
        self.__path_list      = [ FirstPath.sequence() ]
        self.entry            = FirstPath.entry      # map: entry    --> state_index_list
        self.drop_out         = FirstPath.drop_out   # map: drop_out --> state_index_list
        self.__skeleton       = FirstPath.skeleton() # map: target_index --> trigger set
        # The skeleton does not contain wild cards anymore, so we can already transform it
        # into a transition map:                     # list: [ ... (interval, target) ... ]
        self.__transition_map = TransitionMap(self.__skeleton).get_trigger_map()

        AnalyzerState.set_index(self, index.get())
        self.input = { 
            E_EngineTypes.FORWARD:                 E_InputActions.INCREMENT_THEN_DEREF,
            E_EngineTypes.BACKWARD_PRE_CONTEXT:    E_InputActions.DECREMENT_THEN_DEREF,
            E_EngineTypes.BACKWARD_INPUT_POSITION: E_InputActions.DECREMENT_THEN_DEREF,
        }[EngineType]

        self.__uniformity_required_f = (CompressionType == E_Compression.PATH_UNIFORM)

        AnalyzerState.set_engine_type(self, EngineType)

        self.__state_index_list     = None # Computed on demand
        self.__end_state_index_list = None # Computed on demand

    @property
    def init_state_f(self): return False

    def accept(self, Path):
        """Accepts the given Path to be walked, if the skeleton matches.
           If additionally uniformity is required, then only states with
           same drop_out and entry are accepted.
        """
        def is_equal(A, B):
            if set(A.keys()) != set(B.keys()): return False
            for key, trigger_set in A.iteritems():
                if not trigger_set.is_equal(B[key]): return False
            return True

        # (1) Compare 'skeletons', i.e. remaining transition_maps
        if not is_equal(self.__skeleton, Path.skeleton()): 
            return False

        sequence = Path.sequence()
        # (2) Uniformity Test [Optional] 
        if self.__uniformity_required_f:
            assert len(Path.entry)    == 1 # When uniformity is a requirement paths with more
            assert len(Path.drop_out) == 1 # then one entry scheme should have never been created.
            if   self.entry    != Path.entry:    return False
            elif self.drop_out != Path.drop_out: return False
        else:
            # NOTE: The 'end state' of a path should never occur in an entry/drop out scheme
            #       it is the first state after the path and not part of the path itself.
            for entry, state_index_list in Path.entry.iteritems():
                assert sequence[-1][0] not in state_index_list
                self.entry[entry].update(state_index_list) 
            for drop_out, state_index_list in Path.drop_out.iteritems():
                assert sequence[-1][0] not in state_index_list
                self.drop_out[drop_out].update(state_index_list) 
        self.__path_list.append(sequence)

        return True

    @property
    def path_list(self):          assert type(self.__path_list) == list; return self.__path_list
    @property
    def transition_map(self):     return self.__transition_map
    @property
    def state_index_list(self):
        if self.__state_index_list is None:
            result = [] # **MUST** be a list, because we might identify 'state_keys' with it.
            for path in self.__path_list:
                result.extend(map(lambda x: x[0], path))
            self.__state_index_list = result
        return self.__state_index_list
    @property
    def implemented_state_index_list(self):
        result = [] # **MUST** be a list, because we might identify 'state_keys' with it.
        for path in self.__path_list:
            # The end state of each path is not implemented
            # (It may be part of another path, though)
            result.extend(map(lambda x: x[0], path[:-1]))
        return result

    @property
    def uniform_entries_f(self):   return len(self.entry) == 1
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

def group(CharacterPathList, TheAnalyzer, CompressionType):
    """Different character paths may be walked down by the same pathwalker, if
       certain conditions are met. This function groups the given list of
       character paths and assigns them to PathWalkerState-s. The PathWalkerState-s
       can then immediately be used for code generation.
    """

    LanguageDB = Setup.language_db
    state_db   = TheAnalyzer.state_db
    SM_ID      = TheAnalyzer.state_machine_id

    path_walker_list = []
    for candidate in CharacterPathList:
        for path_walker in path_walker_list:
            if path_walker.accept(candidate): break
        else:
            path_walker_list.append(PathWalkerState(candidate, TheAnalyzer.engine_type, CompressionType))

    return path_walker_list
