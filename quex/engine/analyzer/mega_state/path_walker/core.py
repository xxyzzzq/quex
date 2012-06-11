# (C) 2010 Frank-Rene Schaefer
from   quex.engine.analyzer.mega_state.path_walker.path  import CharacterPath
from   quex.engine.analyzer.mega_state.path_walker.state import PathWalkerState
from   quex.engine.analyzer.state.entry_action           import TransitionID, TransitionAction
from   quex.blackboard                                   import E_Compression
from   copy        import deepcopy
from   collections import defaultdict
"""PATH COMPRESSION: __________________________________________________________

   Path compression tries to find paths of single character transitions inside
   a state machine. A sequence of single character transitions is called a
   'path'.  Instead of implementing each state in isolation a special
   MegaState, a 'PathWalkerState', implements the states on the path by 'path
   walking'. That is, it compares the current input with the current character
   on the path. If it fits, it continues on the path, if not it enters the
   PathWalkerState's transition map. The transition map of all AnalyzerState-s
   absorbed by a PathWalkerState must be the same.

   EXPLANATION: _______________________________________________________________

   For path compression it is necessary to identify traits of single character
   transitions while the remaining transitions of the involved states are the
   same (or covered by what is triggered by the current path element). This
   type of compression is useful in languages that contain keywords. Consider
   for example a state machine, containing the key-word 'for':


   ( 0 )-- 'f' --->( 1 )-- 'o' --->( 2 )-- 'r' -------->(( 3 ))--( [a-z] )-.
      \               \               \                                    |
       \               \               \                                   |
        `--([a-eg-z])---`--([a-np-z])---`--([a-qs-z])-->(( 4 ))<-----------'


   The states 0, 1, and 2 can be implemented by a special MegaState'path
   walker', that is a common transition map, that is preceded by a single
   character check.  The single character check changes along a fixed path: the
   sequence of characters 'f', 'o', 'r'. This is shown in the following
   pseudo-code:

     PATH_WALKER_1:
        /* Single Character Check */
        if   input == *p: ++p; goto PATH_WALKER_1;
        elif *p == 0:          goto STATE_3;

        /* Common Transition Map */
        if   x < 'a': drop out
        elif x > 'z': drop out
        else:         goto STATE_4

   It is assumed that the array with the character sequence ends with a
   terminating character (such as the 'terminating zero' in classical C
   Strings), which must be different from buffer limit code. This way it can be
   detected when to trigger to the correspondent end state.

   Each state which is part of a path, can be identified by the identifier
   of the PathWalkerState + the position on the path (+ the id of the path,
   if a PathWalkerState walks more than one path), i.e.

            state on path <--> (PathWalkerState.index, path iterator position)

   Assume that in the above example the path is the 'PATH_WALKER_1' and the 
   character sequence is given by an array:

            path_1_sequence = { 'f', 'o', 'r', 0x0 };
            
   then the three states 0, 1, 2 are identified as follows

            STATE_0  <--> (PATH_WALKER_1, path_1_sequence)
            STATE_1  <--> (PATH_WALKER_1, path_1_sequence + 1)
            STATE_2  <--> (PATH_WALKER_1, path_1_sequence + 2)

   The PathWalkerState implements dedicated entries for each state on a 
   path, where the path iterator is set to the appropriate position.

   RESULT: _____________________________________________________________________

   Dictionary:

          AnalyzerState.index  --->  PathWalkerState which implements it.


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
    path_list = find_begin(TheAnalyzer, 
                           TheAnalyzer.init_state_index, 
                           TheAnalyzer.init_state_index, 
                           CompressionType, 
                           AvailableStateIndexList)

    # (*) Filter subsets of longer paths
    #
    #     Only the longest path alternative remains.
    __filter_redundant_paths(path_list)

    # (*) Avoid intersections
    #
    #     An AnalyzerState can only be implemented by one PathWalkerState.
    #     If paths intersect choose the longest alternative.
    __select_longest_intersecting_paths(path_list)

    # (*) Group paths
    #    
    #     Different paths may have the same common transition map. If this is
    #     the case, they can be implemented by the same PathWalkerState.
    return group_paths(path_list, TheAnalyzer, CompressionType)

def group_paths(CharacterPathList, TheAnalyzer, CompressionType):
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

def __filter_redundant_paths(path_list):
    """Due to the search algorithm, it is not safe to assume that there are
       no paths which are sub-pathes of others. Those pathes are identified.
       Pathes that are sub-pathes of others are deleted.

       Function modifies 'path_list'.
    """
    size = len(path_list)
    i    = 0
    while i < size: 
        i_path = path_list[i]
        # k = i, does not make sense; a path covers itself, so what!?
        k = i + 1
        while k < size: 
            k_path = path_list[k]

            if k_path.covers(i_path):
                # if 'i' is a subpath of something => delete, no further considerations
                del path_list[i]
                size -= 1
                # No change to 'i' since the elements are shifted
                break

            elif i_path.covers(k_path):
                del path_list[k]
                size -= 1
                # No break, 'i' is greater than 'k' so just continue analyzis.

            else:
                k += 1
        else:
            # If the loop is not left by break (element 'i' was deleted), then ...
            i += 1

    # Content of path_list is changed
    return

def __select_longest_intersecting_paths(path_list):
    """The desribed paths may have intersections, but a state can only
       appear in one single path. From each set of intersecting pathes 
       choose only the longest one.

       Function modifies 'path_list'.
    """
    # The intersection db maps: intersection state --> involved path indices
    intersection_db = defaultdict(list)
    for i, path_i in enumerate(path_list):
        k = i # is incremented to 'i+1' in the first iteration
        for path_k in path_list[i + 1:]:
            k += 1
            intersection_state_list = path_i.get_intersections(path_k)
            for state_index in intersection_state_list:
                intersection_db[state_index].extend([i, k])

    return __filter_longest_options(path_list, intersection_db)

def __filter_longest_options(path_list, equivalence_db):
    def __longest_path(PathIndexList):
        max_i      = -1
        max_length = -1
        for path_index in PathIndexList:
            length = len(path_list[path_index])
            if length > max_length: 
                max_i      = path_index
                max_length = length
        return max_i

    # Determine the list of states to be deleted
    delete_list = set([])
    for intersection_state, path_index_list in equivalence_db.items():
        i = __longest_path(path_index_list)
        delete_list.update(filter(lambda index: index != i, path_index_list))

    # Now, delete
    offset = 0
    for i in delete_list:
        del path_list[i - offset]
        offset += 1

    # Content of path_list is changed
    return

find_begin_touched_state_idx_list = {}
def find_begin(analyzer, StateIndex, InitStateIndex, CompressionType, AvailableStateIndexList):
    """Searches for the beginning of a path, i.e. a single character 
       transition to a subsequent state. If such a transition is found,
       a 'skeleton' is computed in the 'CharacterPath' object. With this
       object a continuation of the path is searched starting from the
       transitions target state. 
       
       In any case, it is tried to find a path begin in the target state.
       Even if the target state is part of a path, it might have non-path
       targets that lead to paths. Thus,

       IT CANNOT BE AVOIDED THAT THE RESULT CONTAINS PATHS WHICH ARE 
                           SUB-PATHS OF OTHERS.

       __dive --> This mark is only here to indicate that some recursion 
                  is involved. 
    """
    global find_begin_touched_state_idx_list

    result_list = []

    State          = analyzer.state_db[StateIndex]
    transition_map = State.map_target_index_to_character_set

    for target_idx, trigger_set in transition_map.iteritems():
        if target_idx not in AvailableStateIndexList: continue

        if find_begin_touched_state_idx_list.has_key(target_idx): continue
        find_begin_touched_state_idx_list[target_idx] = True

        # IN ANY CASE: Check for paths in the subsequent state
        result_list.extend(find_begin(analyzer, target_idx, InitStateIndex, CompressionType, AvailableStateIndexList))

        # Never allow the init state to be part of the path
        if StateIndex == InitStateIndex: continue
        # Do not consider indices that are not available
        if StateIndex not in AvailableStateIndexList: return result_list

        # Only single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char is None: continue

        # A new path begins, find the 'skeleton'.
        # The 'skeleton' is the transition map without the single transition

        # Adapt trigger_map: -- map from DoorID to TriggerSet
        #                    -- extract the transition to 'target_idx'.
        # The skeleton is possibly changed in __find_continuation(), but then
        # a 'deepcopy' is applied to disconnect it, see __find_continuation().
        skeleton = get_adapted_trigger_map_shallow_copy(transition_map, analyzer, State.index, 
                                                        ExceptTargetIndex=target_idx)

        path = CharacterPath(State, path_char, skeleton)
            
        result_list.extend(__find_continuation(analyzer, target_idx, path, CompressionType, AvailableStateIndexList))

    return result_list

def __find_continuation(analyzer, StateIndex, the_path, CompressionType, AvailableStateIndexList):
    """A basic skeleton of the path and the remaining trigger map is given. Now,
       try to find a subsequent path step.
    """
    # Check "StateIndex in AvailableStateIndexList" is done by 'continue' in the 
    # loops, if "target_idx not in AvailableStateIndexList".
    State       = analyzer.state_db[StateIndex]
    result_list = []

    transition_map = State.map_target_index_to_character_set

    single_char_transition_found_f = False
    for target_idx, trigger_set in transition_map.items():
        if target_idx not in AvailableStateIndexList: continue

        # Only consider single character transitions can be element of a path.
        path_char = trigger_set.get_the_only_element()
        if path_char is None: continue

        # A recursion cannot be covered by a 'path state'. We cannot extract a
        # state that contains recursions and replace it with a skeleton plus a
        # 'character string position'. Omit this path!
        if the_path.contains(target_idx): continue # Recursion ahead! Don't go!

        # Do the transitions fit the 'skeleton'?
        adapted_transition_map = get_adapted_trigger_map_shallow_copy(transition_map, analyzer, State.index, 
                                                                      ExceptTargetIndex=None)
        target_door_id         = analyzer.state_db[target_idx].entry.get_door_id(target_idx, State.index)
        plug = the_path.match_skeleton(adapted_transition_map, target_door_id, path_char)
        if plug is None: continue # No match possible 

        single_char_transition_found_f = True

        # Deepcopy is required to completely isolate the transition map and the
        # entry/drop_out schemes that may now be changed.
        path_copy = deepcopy(the_path)
        if plug != -1: path_copy.plug_wildcard(plug)

        # Can uniformity be maintained?
        if      CompressionType == E_Compression.PATH_UNIFORM         \
            and not (    the_path.drop_out.is_uniform_with(State.drop_out) \
                     and the_path.check_uniform_entry_to_state(State)):
            # The current state might be a terminal, even if a required uniformity is not 
            # possible. The terminal is not part of the path, but is entered after the
            # path has ended. 
            if len(path_copy) > 1:            # A path must be more than 'Begin and Terminal'
                path_copy.set_end_state_index(State.index)
                result_list.append(path_copy) # Path must end here.
            continue

        # Find a continuation of the path
        path_copy.append(State, path_char)
        result_list.extend(__find_continuation(analyzer, target_idx, path_copy, CompressionType, AvailableStateIndexList))

    if not single_char_transition_found_f and len(the_path) != 1:
        if len(the_path) > 1:            # A path must be more than 'Begin and Terminal'
            the_path.set_end_state_index(StateIndex)
            result_list.append(the_path)

    return result_list

def  get_adapted_trigger_map_shallow_copy(TriggerMap, TheAnalyzer, StateIndex, ExceptTargetIndex):
    """Before: 
    
             TriggerMap:  target_state_index ---> NumberSet that triggers to it

       After: 

             TriggerMap:  DoorID             ---> NumberSet that triggers to it.
    
       The adapted trigger map is possibly changed in __find_continuation(), but then a
       'deepcopy' is applied to disconnect it, see __find_continuation().

       RETURN: A trigger map that triggers to DoorID objects, rather 
               than plain states. This is required. A pathwalker
               can only walk propperly, if it enters the same doors.
    """
    def adapt(TargetIndex, TriggerSet):
        return (TheAnalyzer.state_db[TargetIndex].entry.get_door_id(StateIndex=TargetIndex, FromStateIndex=StateIndex),
                TriggerSet.clone())

    if ExceptTargetIndex is not None:
        return dict(adapt(target_index, number_set) \
                    for target_index, number_set in TriggerMap.iteritems() \
                    if target_index != ExceptTargetIndex)
    else:
        return dict(adapt(target_index, number_set) \
                    for target_index, number_set in TriggerMap.iteritems())


