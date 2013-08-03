# (C) 2010-2013 Frank-Rene Schaefer
from   quex.engine.analyzer.mega_state.path_walker.path  import CharacterPath
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
from   quex.engine.analyzer.state.entry_action           import TransitionID, \
                                                                TransitionAction
import quex.engine.analyzer.transition_map               as     transition_map_tools
from   quex.engine.misc.tree_walker                      import TreeWalker
from   quex.blackboard                                   import E_Compression, E_StateIndices

from   collections import defaultdict
from   copy        import copy

def do(TheAnalyzer, CompressionType, AvailableStateIndexList=None):
    """PATH COMPRESSION: _______________________________________________________

    Path compression tries to find paths of single character transitions inside a
    state machine. A sequence of single character transitions is called a 'path'.
    Instead of implementing each state in isolation a special MegaState, a
    'PathWalkerState', implements the states on the path by 'path walking'. That
    is, it compares the current input with the current character on the path. If it
    fits, it continues on the path. If it does not it enters the PathWalkerState's
    transition map. The transition map of all AnalyzerState-s absorbed by a
    PathWalkerState must be the same.

    (In practical, the transition map may be adapted later. DoorIDs may change as 
    target states from the transition map are implemented by MegaState-s.)

    EXPLANATION: _______________________________________________________________

    For path compression, traits of single character transitions are identified
    while the remaining transitions of the involved states are the same (or covered
    by what is triggered by the current path element). This type of compression is
    useful in languages that contain keywords. Consider for example a state
    machine, containing the key-word 'for':


    ( 0 )-- 'f' --->( 1 )-- 'o' --->( 2 )-- 'r' -------->(( 3 ))--( [a-z] )-.
       \               \               \                                    |
        \               \               \                                   |
         `--([a-eg-z])---`--([a-np-z])---`--([a-qs-z])-->(( 4 ))<-----------'


    The states 0, 1, and 2 can be implemented by a special MegaState 'path walker'.
    It consists of a common transition map which is preceded by a single character
    check. The single character check changes along a fixed path: the sequence of
    characters 'f', 'o', 'r'. This is shown in the following pseudo-code:

      /* Character sequence of path is stored in array. */
      character array[4] = { 'f', 'o', 'r', PTC, };

      0: p = &array[0]; goto PATH_WALKER_1;
      1: p = &array[1]; goto PATH_WALKER_1;
      2: p = &array[2]; goto PATH_WALKER_1;

      PATH_WALKER_1:
         /* Single Character Check */
         if   input == *p: ++p; goto PATH_WALKER_1;
         elif input == PTC:     goto StateAfterPath;
         elif *p == 0:          goto STATE_3;

         /* Common Transition Map: The 'skeleton transition map' */
         if   x < 'a': drop out
         elif x > 'z': drop out
         else:         goto STATE_4

    The array with the character sequence ends with a path terminating character
    PTC.  It acts similar to the 'terminating zero' in classical C Strings. This
    way it can be detected when to trigger to the terminal state, i.e. the first
    state after the path. For a state to be part of the path, it must hold that 

                'state.transition_map - transition character' 
        matches 'path.transition_map'

    where 'transition character' is the character on which it transits to its
    subsequent state. The 'transition character' is a 'wildcard', because it 
    is handled in the pathwalker's head and not as part of the path walker's
    body (if state_key = this state).

    Each state which is part of a path, can be identified by the identifier of the
    PathWalkerState + the position on the path (+ the id of the path, if a
    PathWalkerState walks more than one path), i.e.

         state on path <--> (PathWalkerState.index, path iterator position)

    Assume that in the above example the path is the 'PATH_WALKER_1' and the
    character sequence is given by an array:

         path_1_sequence = { 'f', 'o', 'r', PTC };
             
    then the three states 0, 1, 2 are identified as follows

             STATE_0  <--> (PATH_WALKER_1, path_1_sequence)
             STATE_1  <--> (PATH_WALKER_1, path_1_sequence + 1)
             STATE_2  <--> (PATH_WALKER_1, path_1_sequence + 2)

    In the MegaState terminology, the path iterator position acts as a 'state_key'
    which identifies the state the pathwalker current represents.  The
    PathWalkerState implements dedicated entry doors for each state on a path,
    where the path iterator (~ state  key) is set to the appropriate position.

    RESULT: _____________________________________________________________________

    Dictionary:

           AnalyzerState.index  --->  PathWalkerState which implements it.

    That is, all keys of the returned dictionary are AnalyzerState-s which have
    been absorbed by a PathWalkerState.

    NOTE: _______________________________________________________________________

    Inheritance:

          AnalyzerState <----- MegaState <------- PathWalkerState


    (C) 2009-2012 Frank-Rene Schaefer
    """
    assert CompressionType in [E_Compression.PATH, E_Compression.PATH_UNIFORM]

    if AvailableStateIndexList is None: 
        AvailableStateIndexList = TheAnalyzer.state_db.keys()

    # (*) Find all single character transitions (paths) inside TheAnalyzer's 
    #     state machine.
    path_list = collect(TheAnalyzer, CompressionType, AvailableStateIndexList)

    # (*) Select paths, so that a maximum of states is implemented by path walkers.
    path_list = select(path_list)

    # (*) Group paths
    #    
    #     Different paths may have the same common transition map. If this is
    #     the case, they can be implemented by the same PathWalkerState.
    return group(path_list, TheAnalyzer, CompressionType)

def collect(TheAnalyzer, CompressionType, AvailableStateIndexList):
    """Starting point of path search. Try for each state in the state
    machine to find paths which branch from it.
    """
    AvailableStateIndexSet = set(AvailableStateIndexList)
    done_set = set()

    # (1) Consider first the states which immediately follow the initial state.
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
            drop_out_uniform_f = path.drop_out.is_uniform_with(State.drop_out)
            entry_uniform_f    = path.entry_uniformity_with_predecessor(State)
            if self.uniform_f and (not drop_out_uniform_f) or (not entry_uniform_f):
                if len(path.step_list) > 1:
                    path.finalize(State.index)
                    self.result.append(path)
                return None

            if not entry_uniform_f:
                path.entry_uniformity_along_path_unset()

            # BRANCH __________________________________________________________
            sub_list = []
            for target_index, trigger_set in State.map_target_index_to_character_set.iteritems():
                if target_index not in self.available_set: continue

                # Only single character transitions can be element of a path.
                transition_char = trigger_set.get_the_only_element()
                if transition_char is None: continue

                # A PathWalkerState cannot implement a loop.
                if path.contains_state(target_index): continue # Loop--don't go!

                target_state   = self.analyzer.state_db[target_index]

                # TransitionMap matching? 
                print "#step_list:", [ x.trigger for x in path.step_list ]
                plug = path.transition_map.match_with_wildcard(transition_map, transition_char)
                print "#plug:", plug, path.has_wildcard()
                if   plug is None:
                    continue # No match possible 
                elif plug > 0  and not path.has_wildcard(): 
                    continue # Wilcard required for match, but there is no wildcard open.

                new_path = path.extended_clone(State, transition_char, plug) 
                print "#new.step_list:", [ x.trigger for x in new_path.step_list ]

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

def select(path_list):
    """The desribed paths may have intersections, but a state can only appear
    in one single path. From each set of intersecting pathes choose only the
    longest one.

    Function modifies 'path_list'.
    """
    def get_belong_db(AvailablePathList):
        """belong_db: 
          
                      state_index --> paths of which state_index is part. 
        """
        result = defaultdict(set)
        for i, path in enumerate(AvailablePathList):
            for state_index in path.state_index_set():
                result[state_index].add(i)
        return result

    def get_best_path(AvailablePathList):
        """The best path is the path that brings the most gain. The 'gain'
        of a path is a function of the number of states it implements minus
        the states that may not be implemented because other intersecting
        paths cannot be chosen anymore.

        RETURN: [0] winning path
                [1] list of indices of paths which would be no longer 
                    available, because the winning path intersects.
        """
        AvailablePathList = sorted(AvailablePathList, key=lambda p: - p.state_index_list_size())
        belong_db         = get_belong_db(AvailablePathList)

        max_gain               = None
        winner_i               = None
        winner_forbidden_i_set = None
        for i, path in enumerate(AvailablePathList):
            if max_gain is not None and len(path.state_index_set()) < max_gain: continue # No chance

            all_but_path = (p for k, p in enumerate(AvailablePathList) if k != i)
            gain, forbidden_i_set = compute_gain(path, belong_db, all_but_path)
                                                       
            if max_gain is None or max_gain < gain:
                max_gain               = gain
                winner_i               = i
                winner_forbidden_i_set = forbidden_i_set

        return winner_i, winner_forbidden_i_set

    def compute_gain(path, BelongDB, AvailablePathListIterable):
        """What happens if 'path' is chosen?

           -- Paths which contain any of its state_indices become unavailable.
              (states can only be implemented once) => forbidden paths.
           
           -- States in a forbidden path which are not in state_index_set cannot
              be implemented, except that they are implemented by another path
              which does not intersect with this path.
           
          RETURNS: [0] 'gain' of choosing 'path' 
                   [1] set of ids of paths which are forbidden if 'path' is chosen.
        """
        # -- The states implemented by path
        state_index_set = path.state_index_set()

        # -- Forbidden are those paths which have a state in common with 'path'
        # -- Those states implemented in forbidden paths become endangered.
        #    I.e. they might not to be implemented by a PathWalkerState.
        endangered_set        = set()
        forbidden_path_id_set = set()
        for other_path_i, other_path in enumerate(AvailablePathListIterable):
            if state_index_set.isdisjoint(other_path.state_index_set()): continue

            # If 'other_path' is dropped: 
            # => its states may not be implemented in PathWalkerState.
            endangered_set.update(other_path.state_index_set() - state_index_set)

            forbidden_path_id_set.add(other_path_i)

        # (*) Function to model 'cost for an endangered state'
        # 
        #                       1 / (1 + alternative_n)
        # 
        #  = 1,  if there is no alternative implementation for 'state_index'. 
        #        The state is definitely not implemented in a PathWalkerState. 
        #
        #  decreasing, with the number of remaining alternatives.
        #
        # 'Cost' of choosing 'path' = sum of costs for endangered state indices.
        cost = 0 
        for endangered_state_index in endangered_set:
            alternative_n = len(BelongDB[endangered_state_index]) 
            cost += 1 / (1 + alternative_n)

        # Gain: Each implemented state counts as '1'
        gain = len(state_index_set)
        return gain - cost, forbidden_path_id_set

    result    = []
    work_list = copy(path_list)
    while len(work_list):
        elect_i, dropped_list = get_best_path(work_list)

        # Delete all paths which are impossible, if 'elect_i' is chosen.
        for i in dropped_list:
            del work_list[i]

        # Move path from 'work_list' to 'result'.
        result.append(work_list[elect_i])
        del work_list[elect_i]

    return result

def group(CharacterPathList, TheAnalyzer, CompressionType):
    """Different character paths may be walked down by the same pathwalker, if
    certain conditions are met. This function groups the given list of
    character paths and assigns them to PathWalkerState-s. The
    PathWalkerState-s can then immediately be used for code generation.  
    """

    # Generate the path walkers.  One pathwalker may be able to walk along more
    # than one path.  If a pathwalker accepts another path, no extra pathwalker
    # needs to be created.
    path_walker_list = []
    for path in CharacterPathList:
        for path_walker in path_walker_list:
            # Set-up the walk in an existing PathWalkerState
            if path_walker.accept(path): break
        else:
            # Create a new PathWalkerState
            path_walker_list.append(PathWalkerState(path, TheAnalyzer, CompressionType))

    # Once, all path walkers are setup, finalize.
    for path_walker in path_walker_list:
        path_walker.finalize(TheAnalyzer)

    return path_walker_list

