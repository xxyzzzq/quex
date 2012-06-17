# (C) 2010 Frank-Rene Schaefer
from   quex.engine.misc.tree_walker                      import TreeWalker
import quex.engine.analyzer.transition_map               as transition_map_tools
from   quex.engine.analyzer.mega_state.path_walker.path  import CharacterPath
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
from   quex.engine.analyzer.state.entry_action           import TransitionID, TransitionAction
from   quex.blackboard                                   import E_Compression
from   copy        import deepcopy
from   collections import defaultdict
"""
PATH COMPRESSION: __________________________________________________________

Path compression tries to find paths of single character transitions inside a
state machine. A sequence of single character transitions is called a 'path'.
Instead of implementing each state in isolation a special MegaState, a
'PathWalkerState', implements the states on the path by 'path walking'. That
is, it compares the current input with the current character on the path. If it
fits, it continues on the path, if not it enters the PathWalkerState's
transition map. The transition map of all AnalyzerState-s absorbed by a
PathWalkerState must be the same.

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
way it can be detected when to trigger to the first state after the path.
The common transition map is called 'skeleton'. For a state to be part 
of the path, it must hold that 

    'state.transition_map - character transition' matches 'skeleton'

where 'character transition' is the character on which it transits to its
subsequent state. 

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

The PathWalkerState implements dedicated entries for each state on a path,
where the path iterator is set to the appropriate position.

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
def do(TheAnalyzer, CompressionType, AvailableStateIndexList=None, MegaStateList=None):

    assert CompressionType in [E_Compression.PATH, E_Compression.PATH_UNIFORM]

    if AvailableStateIndexList is None: AvailableStateIndexList = TheAnalyzer.state_db.keys()

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
    """Starting from each state in the state machine, search for paths
       which begin from it.
    """
    AvailableStateIndexSet = set(AvailableStateIndexList)
    done_set = set()

    path_list = []
    for state_index in TheAnalyzer.state_db[TheAnalyzer.init_state_index].map_target_index_to_character_set.iterkeys():
        if   state_index == TheAnalyzer.init_state_index: continue
        elif state_index not in AvailableStateIndexList:  continue

        path_list.extend(__find(TheAnalyzer, state_index,
                                CompressionType, AvailableStateIndexSet))
        done_set.add(state_index)

    for state_index in TheAnalyzer.state_db.iterkeys():
        if   state_index in done_set:                     continue
        elif state_index == TheAnalyzer.init_state_index: continue
        elif state_index not in AvailableStateIndexList:  continue

        path_list.extend(__find(TheAnalyzer, state_index,
                                CompressionType, AvailableStateIndexSet))
    return path_list

def __find(analyzer, StateIndex, CompressionType, AvailableStateIndexSet):
    """Searches for the BEGINNING of a path, i.e. a single character transition
    to a subsequent state. If such a transition is found, a 'skeleton' transition
    map is computed. A 'skeleton' is a transition map which contains 'wildcards' 
    for the characters which constitute the path's transition. For a subsequent
    state to be part of the path, its transition map must match that skeleton. 
       
    This function is not recursive. It simply iterates over all states in the
    state machine. For each state, in isolation, it checks wether it might be
    the beginning of a path.
    """
    result_list = []

    State          = analyzer.state_db[StateIndex]
    target_map     = State.map_target_index_to_character_set
    transition_map = transition_map_tools.relate_to_door_ids(State.transition_map, analyzer, State.index)

    for target_idx, trigger_set in target_map.iteritems():
        if   target_idx not in AvailableStateIndexSet: continue # State is not an option.
        elif target_idx == StateIndex:                 continue # Recursion! Do not go further!

        # Only single character transitions can be element of a path.
        transition_char = trigger_set.get_the_only_element()
        if transition_char is None: continue

        result = __find_continuation(analyzer, CompressionType, AvailableStateIndexSet, 
                                     State, transition_map, transition_char, target_idx)

        result_list.extend(result)

    return result_list

def __find_continuation(analyzer, CompressionType, AvailableStateIndexSet, 
                        FromState, FromTransitionMap, TransitionChar, TargetIndex):
    class PathFinder(TreeWalker):
        """Determines PathTrace objects for each state. The heart of this function is
           the call to 'PathTrace.next_step()' which incrementally develops the 
           acceptance and position storage history of a path.

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path' in the same manner. That means,
                               that if a state appears again in the path, its trace
                               must be different or the recursion terminates.
        """
        def __init__(self, TheAnalyzer, CompressionType, AvailableStateIndexSet):
            self.__depth       = 0
            self.analyzer      = TheAnalyzer
            self.available_set = AvailableStateIndexSet
            self.uniform_f     = CompressionType == E_Compression.PATH_UNIFORM
            self.result        = []
            TreeWalker.__init__(self)

        def on_enter(self, Args):
            path                  = Args[0]
            State                 = Args[1]
            FromToToHereCharacter = Args[2]

            # Can uniformity be maintained?
            if      self.uniform_f                                             \
                and not (    path.drop_out.is_uniform_with(FromState.drop_out) \
                         and path.check_uniform_entry_to_state(FromState)):
                # The current state might be a terminal, even if a required uniformity is not 
                # possible. The terminal is not part of the path, but is entered after the
                # path has ended. This handled by 'on_finished'.
                pass

            # list: (interval, target)
            transition_map = transition_map_tools.relate_to_door_ids(State.transition_map, 
                                                                     self.analyzer, 
                                                                     State.index)
            # List of follow-states to consider. ______________________________
            sub_list = []
            for target_index, trigger_set in State.map_target_index_to_character_set.iteritems():
                if target_index not in self.available_set: return

                # Only single character transitions can be element of a path.
                transition_char = trigger_set.get_the_only_element()
                if transition_char is None: continue

                # A PathWalkerState cannot implement a recursion.
                if path.contains_state(target_index): continue # Recursion--don't go!

                target_state = self.analyzer.state_db[target_index]
                # Do the transitions fit the 'skeleton'?
                target_door_id = target_state.entry.get_door_id(target_index, State.index)
                plug           = path.match(transition_map, target_door_id, transition_char)
                if plug is None: continue # No match possible 

                new_path = path.clone() # May be, we do not have to clone the transition map if plug == -1
                # Find a continuation of the path
                new_path.append_state(State, transition_char)
                if plug != -1: new_path.plug_wildcard(plug)

                sub_list.append((new_path, target_state, transition_char))

            # Termination Condition: 'sub_list = empty' _______________________
            #
            # There are no further transitions to be considered. This is 
            # includes, of course, the case where a state is a dead-end.
            if len(sub_list) == 0 and len(path) > 1: 
                path.append_state(State) # transition_to_next_character = None
                path.finalize()
                self.result.append(path)

            return sub_list

        def on_finished(self, Args):
            self.__depth -= 1

    tm_clone     = transition_map_tools.clone(FromTransitionMap)
    target_state = analyzer.state_db[TargetIndex]
    path         = CharacterPath(FromState, TransitionChar, tm_clone)

    trace_finder = PathFinder(analyzer, CompressionType, AvailableStateIndexSet)
    # FromState         = Args[0]
    # FromTransitionMap = Args[1]  # FromState's adapted transition map
    # FromToCharacter   = Args[2]
    # Plug              = Args[3]
    # ToState           = Args[4]
    # ThePath           = Args[5]
    trace_finder.do((path, target_state, TransitionChar))
    return trace_finder.result

def __OLD_find_continuation(analyzer, StateIndex, the_path, CompressionType, AvailableStateIndexList):
    """A basic skeleton of the path and the remaining trigger map is given. Now,
       try to find a subsequent path step.

    __dive --> This mark is only here to indicate that some recursion 
               is involved. 
    """

    # Check "StateIndex in AvailableStateIndexList" is done by 'continue' in the 
    # loops, if "target_index not in AvailableStateIndexList".
    State       = analyzer.state_db[StateIndex]
    result_list = []

    # list: (interval, target)
    transition_map = transition_map_tools.relate_to_door_ids(State.transition_map, analyzer, State.index)
    # map:  target --> number set that triggers to it
    target_map     = State.map_target_index_to_character_set

    single_char_transition_found_f = False
    for target_index, trigger_set in target_map.iteritems():
        if target_index not in AvailableStateIndexList: continue

        # Only consider single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char is None: continue

        # A PathWalkerState cannot implement a recursion.
        if the_path.contains_state(target_index): continue # Recursion ahead--don't go!

        # Do the transitions fit the 'skeleton'?
        target_door_id = analyzer.state_db[target_index].entry.get_door_id(target_index, State.index)
        plug           = the_path.match(transition_map, target_door_id, path_char)
        if plug is None: continue # No match possible 

        single_char_transition_found_f = True

        path_clone = the_path.clone()
        if plug != -1: path_clone.plug_wildcard(plug)

        # Can uniformity be maintained?
        if      CompressionType == E_Compression.PATH_UNIFORM         \
            and not (    the_path.drop_out.is_uniform_with(State.drop_out) \
                     and the_path.check_uniform_entry_to_state(State)):
            # The current state might be a terminal, even if a required uniformity is not 
            # possible. The terminal is not part of the path, but is entered after the
            # path has ended. 
            if len(path_clone) > 1:            # A path must be more than 'Begin and Terminal'
                path_clone.set_end_state_index(State.index)
                result_list.append(path_clone) # Path must end here.
            continue

        # Find a continuation of the path
        path_clone.append(State, path_char)

        child_results = __find_continuation(analyzer, target_index, path_clone, 
                                            CompressionType, AvailableStateIndexList)
        result_list.extend(child_results)

    if not single_char_transition_found_f and len(the_path) > 1:
        # (len(the_path) > 1, because a path must be more than 'Begin and Terminal')
        the_path.set_end_state_index(StateIndex)
        result_list.append(the_path)

    return result_list

def select(path_list):
    """The desribed paths may have intersections, but a state can only
       appear in one single path. From each set of intersecting pathes 
       choose only the longest one.

       Function modifies 'path_list'.
    """
    def get_best_path(AvailablePathList):
        """The best path is the path that brings the most gain. The 'gain'
        of a path is a function of the number of states it implements minus
        the states that may not be implemented because other intersecting
        paths cannot be chosen anymore.

        RETURN: [0] winning path
                [1] list of indices of paths which would be no longer 
                    available, because the winning path intersects.
        """
        print "#get_best_path_________________________"
        opportunity_db = get_opportunity_db(AvailablePathList)
        max_gain = None
        winner                       = None
        winner_forbidden_path_id_set = None
        for path in AvailablePathList:
            print "# path:", len(path.state_index_set), path.state_index_set 
            print "# max:", max_gain
            if max_gain is not None and len(path.state_index_set) < max_gain: continue # No chance

            gain, forbidden_path_id_set = compute_gain(path, opportunity_db, 
                                                       (p for p in AvailablePathList if p.index != path.index))

            print "#gain:", gain
            if max_gain is None:
                winner                       = path
                winner_forbidden_path_id_set = forbidden_path_id_set
                max_gain                     = gain
            elif max_gain == gain:
                if len(winner.state_index_set) < len(path.state_index_set):
                    winner                       = path
                    winner_forbidden_path_id_set = forbidden_path_id_set
                    max_gain                     = gain
            elif max_gain < gain:
                winner                       = path
                winner_forbidden_path_id_set = forbidden_path_id_set
                max_gain                     = gain


        return winner, winner_forbidden_path_id_set

    def get_opportunity_db(AvailablePathList):
        """opportunity_db: 
          
                      state_index --> paths of which state_index is part. 
        """
        result = defaultdict(set)
        for path in AvailablePathList:
            for state_index in path.state_index_set:
                result[state_index].add(path.index)
        return result

    def compute_gain(path, opportunity_db, AvailablePathListIterable):
        """What happens if 'path' is chosen?

       -- Paths which contain any of its state_indices become unavailable.
          (states can only be implemented once) => forbidden paths.

       -- States in a forbidden path which are not in state_index_set cannot
          be implemented, except that they are implemented by another path
          which does not intersect with this path.

       RETURN: 

          [0] 'gain' of choosing 'path' 
          [1] set of ids of paths which are forbidden if 'path' is chosen.
        """
        # -- The states implemented by path
        state_index_set = path.state_index_set

        # -- Forbidden are those paths which have a state in common with 'path'
        # -- Those states implemented in forbiddent paths become endangered.
        #    I.e. they might not to be implemented by a PathWalkerState.
        endangered_set = set()
        forbidden_path_id_set = set()
        for other_path in AvailablePathListIterable:
            if state_index_set.isdisjoint(other_path.state_index_set): continue
            endangered_set.update(other_path.state_index_set - state_index_set)
            forbidden_path_id_set.add(other_path.index)

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
            alternative_n = len(opportunity_db[endangered_state_index]) 
            cost += 1 / (1 + alternative_n)

        # Gain: Each implemented state counts as '1'
        gain = len(state_index_set)
        return gain - cost, forbidden_path_id_set

    work_db = dict((path.index, path) for path in path_list)

    for path in path_list:
        print "#ps:", len(path.state_index_set), path.state_index_set

    result = []
    while len(work_db):
        elect, dropped_list = get_best_path(sorted(work_db.values(), 
                                                   key=lambda p: - len(p.state_index_set)))
        assert elect is not None
        for path_id in dropped_list:
            del work_db[path_id]
        result.append(elect)
        del work_db[elect.index]
    return result

            
def group(CharacterPathList, TheAnalyzer, CompressionType):
    """Different character paths may be walked down by the same pathwalker, if
       certain conditions are met. This function groups the given list of
       character paths and assigns them to PathWalkerState-s. The PathWalkerState-s
       can then immediately be used for code generation.
    """
    path_walker_list = []
    for candidate in CharacterPathList:
        for path_walker in path_walker_list:
            # Set-up the walk in an existing PathWalkerState
            if path_walker.accept(candidate, TheAnalyzer.state_db): break
        else:
            # Create a new PathWalkerState
            path_walker_list.append(PathWalkerState(candidate, TheAnalyzer, CompressionType))

    absorbance_db = defaultdict(set)
    for path_walker in path_walker_list:
        absorbance_db.update((i, path_walker) for i in path_walker.implemented_state_index_list())

        if path_walker.uniform_entry_command_list_along_all_paths is not None:
            # Assign the uniform command list to the transition 'path_walker -> path_walker'
            transition_action = TransitionAction(path_walker.index, path_walker.index, path_walker.uniform_entry_command_list_along_all_paths)
            # Delete transitions on the path itself => No doors for them will be implemented.
            path_walker.delete_transitions_on_path() # LEAVE THIS! This is the way to 
            #                                        # indicate unimportant entry doors!
        else:
            # Nothing special to be done upon iteration over the path
            transition_action = TransitionAction(path_walker.index, path_walker.index)

        transition_id = TransitionID(path_walker.index, path_walker.index)
        path_walker.entry.action_db[transition_id] = transition_action

        # Once the entries are combined, re-configure the door tree
        path_walker.entry.door_tree_configure()

    return absorbance_db

