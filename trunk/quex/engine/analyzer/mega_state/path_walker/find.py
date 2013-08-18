from   quex.engine.analyzer.mega_state.path_walker.path  import CharacterPath
from   quex.engine.misc.tree_walker                      import TreeWalker
from   quex.blackboard                                   import E_Compression, E_StateIndices

from   collections import defaultdict

def do(TheAnalyzer, CompressionType, AvailableStateIndexList):
    """Starting point of path search. Try for each state in the state
    machine to find paths which branch from it.
    """
    AvailableStateIndexSet = set(AvailableStateIndexList)
    done_set = set()

    # (1) Consider first the states which immediately follow the initial state.
    #     => We quickly get a 'done_set' which covers many states.
    path_list = []
    for state_index in TheAnalyzer.state_db[TheAnalyzer.init_state_index].map_target_index_to_character_set.iterkeys():
        if   state_index == TheAnalyzer.init_state_index: continue
        elif state_index not in AvailableStateIndexList:  continue

        path_list.extend(__find(TheAnalyzer, state_index,
                                CompressionType, AvailableStateIndexSet))
        done_set.add(state_index)

    # (2) All other states. Their analysis may actually be covered
    #     already by what was triggered by (1)
    for state_index in TheAnalyzer.state_db.iterkeys():
        if   state_index in done_set:                     continue
        elif state_index == TheAnalyzer.init_state_index: continue
        elif state_index not in AvailableStateIndexList:  continue

        path_list.extend(__find(TheAnalyzer, state_index,
                                CompressionType, AvailableStateIndexSet))
    return path_list

def __find(analyzer, StateIndex, CompressionType, AvailableStateIndexSet):
    """Searches for the BEGINNING of a path, i.e. a single character transition
    to a subsequent state. If such a transition is found, a search for a path
    is initiated (call to '__find_continuation(..)').

    This function itself it not recursive.
    """
    result_list = []

    State          = analyzer.state_db[StateIndex]
    target_map     = State.map_target_index_to_character_set
    transition_map = State.transition_map 

    for target_idx, trigger_set in target_map.iteritems():
        if   target_idx not in AvailableStateIndexSet: continue # State is not an option.
        elif target_idx == StateIndex:                 continue # Recursion! Do not go further!

        # Only single character transitions can be element of a path.
        transition_char = trigger_set.get_the_only_element()
        if transition_char is None:                    continue # Not a single char transition.

        result = __find_continuation(analyzer, CompressionType, AvailableStateIndexSet, 
                                     State, transition_map, transition_char, target_idx)

        result_list.extend(result)

    return result_list

def __find_continuation(analyzer, CompressionType, AvailableStateIndexSet, 
                        FromState, FromTransitionMap, TransitionChar, TargetIndex):
    """A single character transition has been found for a given state 'FromState'.
    Thus, this function sets up a CharacterPath object that is the 'head' of
    a potential path to be found. 

    This function is its nature recursive. To avoid problems with stack size,
    it relies on 'TreeWalker'.
    """

    class PathFinder(TreeWalker):
        """Recursive search for single character transition paths inside the 
        given state machine. Assume, that a first single character transition
        has been found. As a result, a CharacterPath object must have been
        created which contains a 'wild card', i.e. a character that is left
        to be chosen freely, because it is covered by the first transition
        character.

        RECURSION STEP: 
        
                -- Add current path add the end of the given path.
                -- If required: Plug the wildcard.

        BRANCH: Branch to all follow-up states where:

                -- There is a single character transition to them.
                -- The state itself is not part of the path yet.
                   Loops cannot be modelled by a PathWalkerState.
                -- The transition map fits the transition map of the 
                   given path.

        TERMINAL: There are no further single character transitions which
                  meet the aforementioned criteria.
        """
        def __init__(self, TheAnalyzer, CompressionType, AvailableStateIndexSet):
            self.__depth       = 0
            self.analyzer      = TheAnalyzer
            self.available_set = AvailableStateIndexSet
            self.uniform_f     = (CompressionType == E_Compression.PATH_UNIFORM)
            self.result        = []
            self.info_db       = defaultdict(list)
            TreeWalker.__init__(self)

        def on_enter(self, Args):
            path           = Args[0]  # 'CharacterPath'
            State          = Args[1]  # 'AnalyzerState'
            transition_map = State.transition_map 

            # We are searching on follow states of this 'State'. 
            # => 'State' will becomes an element of the path.
            #    (Its target state still will remain an external 'Terminal')
            # => Entry and DropOut of 'State' are implemented as part of the 
            #    path walker.
            
            # If uniformity is required, then this is the place to check for it.
            if self.uniform_f and not path.uniformity_with_predecessor(State):
                if len(path.step_list) > 1:
                    path.finalize(State.index)
                    self.result.append(path)
                return None

            # BRANCH __________________________________________________________
            sub_list = []
            for target_index, trigger_set in State.map_target_index_to_character_set.iteritems():
                if target_index not in self.available_set: continue

                # Only single character transitions can be element of a path.
                transition_char = trigger_set.get_the_only_element()
                if transition_char is None: continue

                # A PathWalkerState cannot implement a loop.
                if path.contains_state(target_index): continue # Loop--don't go!

                target_state = self.analyzer.state_db[target_index]

                # TransitionMap matching? 
                plug = path.transition_map.match_with_wildcard(transition_map, transition_char)
                if   plug is None:
                    continue # No match possible 
                elif plug > 0  and not path.has_wildcard(): 
                    continue # Wilcard required for match, but there is no wildcard open.

                new_path = path.extended_clone(State, transition_char, plug) 

                # RECURSION STEP ______________________________________________
                # (May be, we do not have to clone the transition map if plug == -1)
                # Clone the current state and append the new terminal.
                sub_list.append((new_path, target_state))

            # TERMINATION _____________________________________________________
            if len(sub_list) == 0:
                if len(path.step_list) > 1: 
                    path.finalize(State.index)
                    self.result.append(path)
                return None

            return sub_list

        def on_finished(self, Args):
            self.__depth -= 1

    target_state = analyzer.state_db[TargetIndex]
    path         = CharacterPath(FromState, FromTransitionMap, TransitionChar)

    path_finder  = PathFinder(analyzer, CompressionType, AvailableStateIndexSet)
    path_finder.do((path, target_state))

    return path_finder.result


