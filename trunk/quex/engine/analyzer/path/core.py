# (C) 2010 Frank-Rene Schaefer
from   quex.engine.analyzer.path.path        import CharacterPath
import quex.engine.analyzer.path.path_walker as     path_walker
from   quex.blackboard                       import E_Compression

from   copy        import deepcopy, copy
from   collections import defaultdict
"""
   Path Compression ___________________________________________________________

   For path compression it is necessary to identify traits of single character
   transitions while the remaining transitions of the involved states are the
   same (or covered by what is triggered by the current path element). This
   type of compression is useful in languages that contain keywords. Consider
   for example a state machine, containing the key-word 'for':


   ( 0 )-- 'f' --->( 1 )-- 'o' --->( 2 )-- 'r' -------->(( 3 ))--( [a-z] )-.
      \               \               \                                    |
       \               \               \                                   |
        `--([a-eg-z])---`--([a-np-z])---`--([a-qs-z])-->(( 4 ))<-----------'


   The states 0, 1, and 2 can be implemented by a 'path walker', that is 
   a common transition map, that is preceded by a single character check.
   The single character check changes along a fixed path: the sequence of
   characters 'f', 'o', 'r'. This is shown in the following pseudo-code:

     PATH_WALKER_1:
        /* Single Character Check */
        if   input == *p: ++p; goto PATH_WALKER_1;
        elif *p == 0:          goto STATE_3;

        /* Common Transition Map */
        if   x < 'a': drop out
        elif x > 'z': drop out
        else:         goto STATE_4

   It is assumed that the array with the character sequence ends with a
   terminating character (e.g. zero, but must be different from buffer limit
   code).  This way it can be detected when to trigger to the correspondent end
   state.

   For a state that is part of a 'path', a 'goto state' is transformed into a
   'set path_iterator' plus a 'goto path'. The path iterator determines the
   current character to be checked. The 'path' determines the reminder of the
   transition map. It holds

            path state <--> (path index, path iterator position)

   Assume that in the above example the path is the 'PATH_WALKER_1' and the 
   character sequence is given by an array:

            path_1_sequence = { 'f', 'o', 'r', 0x0 };
            
    then the three states 0, 1, 2 are identified as follows

            STATE_0  <--> (PATH_WALKER_1, path_1_sequence)
            STATE_1  <--> (PATH_WALKER_1, path_1_sequence + 1)
            STATE_2  <--> (PATH_WALKER_1, path_1_sequence + 2)

   Result ______________________________________________________________________


   The result of analysis of path compression is:
    
                       A dictionary mapping  
                  
            start state indices <--> 'CharacterPath' objects. 

   A character path represents a single character sequence that was found in
   the state machine, together with the 'skeleton' which is the remaining
   trigger map. Concrete:

         .sequence()        --> The character sequence of the path
         .end_state_index() --> State index of the state that is
                                entered after the path is terminated.
         .skeleton()        --> Remaining trigger map, that must be
                                applied after the single char check.

   There might be multiple pathes starting from the same start state. And,
   start states might possibly appear in other paths.

   Filtering Pathes ___________________________________________________________

   First, paths that are subsets of other paths might be filtered out without
   loss.

"""
def do(TheAnalyzer, CompressionType, AvailableStateIndexList=None, MegaStateList=None):
    assert CompressionType in [E_Compression.PATH, E_Compression.PATH_UNIFORM]

    if AvailableStateIndexList is None: AvailableStateIndexList = TheAnalyzer.state_db.keys()

    path_list = find_begin(TheAnalyzer, 
                           TheAnalyzer.init_state_index, 
                           TheAnalyzer.init_state_index, 
                           CompressionType, 
                           AvailableStateIndexList)

    __filter_redundant_paths(path_list)

    # A state can only appear in one path, so make sure that intersecting
    # paths are avoided. Always choose the longest alternative.
    __select_longest_intersecting_paths(path_list)

    # The filtering of intersecting paths implies that there are no paths
    # that have the same initial state. 
    #    -- no paths appear twice.
    #    -- no state appears in two paths.

    # Group the paths according to their 'skeleton'. If uniformity is required
    # then this is also a grouping criteria. The result is a list of path walkers
    # that can walk the paths. They can act as AnalyzerState-s for code generation.
    path_walker_state_list = path_walker.group(path_list, TheAnalyzer, CompressionType)
    done_set = set()
    for pw_state in path_walker_state_list:
        done_set.update(pw_state.implemented_state_index_list)

    return done_set, path_walker_state_list

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

        # Does the rest of the transitions fit the 'skeleton'?
        if     CompressionType == E_Compression.PATH_UNIFORM \
           and not the_path.match_entry_and_drop_out(State):
            continue # No match possible

        adapted_transition_map = get_adapted_trigger_map_shallow_copy(transition_map, analyzer, State.index, 
                                                                      ExceptTargetIndex=None)
        plug = the_path.match_skeleton(adapted_transition_map, target_idx, path_char)
        if plug is None: 
            continue # No match possible 

        # Deepcopy is required to completely isolate the transition map and the
        # entry/drop_out schemes that may now be changed.
        path = deepcopy(the_path)
        print "##plug:", plug
        if plug != -1: path.plug_wildcard(plug)

        # Find a continuation of the path
        single_char_transition_found_f = True
        path.append(State, path_char)
        result_list.extend(__find_continuation(analyzer, target_idx, path, CompressionType, AvailableStateIndexList))

    if not single_char_transition_found_f and len(the_path) != 1:
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


