from quex.engine.analyzer.core                import AnalyzerState
from quex.engine.state_machine.transition_map import TransitionMap

class PathWalkerState(AnalyzerState):
    """A path walker state is a state that can walk along one or more paths 
       with the same 'skeleton', i.e. remaining transition map. Objects of
       this class are the basis for code generation.


    """
    def __init__(self, FirstPath):
        self.__path_list      = [ FirstPath ]
        self.entry            = FirstPath.entry      # map: entry    --> state_index_list
        self.drop_out         = FirstPath.drop_out   # map: drop_out --> state_index_list
        self.__skeleton       = FirstPath.skeleton() # map: target_index --> trigger set
        # The skeleton does not contain wild cards anymore, so we can already transform it
        # into a transition map:                     # list: [ ... (interval, target) ... ]
        self.__transition_map = TransitionMap(self.__skeleton).get_trigger_map()

    def accept(self, Path, UniformityF):
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

        # (2) Uniformity Test [Optional] 
        if UniformityF:
            assert len(Path.entry)    == 1 # When uniformity is a requirement paths with more
            assert len(Path.drop_out) == 1 # then one entry scheme should have never been created.
            if   self.entry    != Path.entry:    return False
            elif self.drop_out != Path.drop_out: return False

        self.__path_list.append(Path)

        return True

    @property
    def path_list(self):      return self.__path_list
    @property
    def transition_map(self): return self.__transition_map

def group(CharacterPathList):
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
            path_walker_list.append(PathWalkerState(candidate))

    return path_walker_list
