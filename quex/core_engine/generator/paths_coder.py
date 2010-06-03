"""Path Compression ___________________________________________________________

   Consider the file 'core_engine/state_machine/compression/paths.py' for 
   a detailed explanation of path compression.

   Code Generation ____________________________________________________________

   Let 'path walker' be a code fragment that is able to 'walk' along a given
   path and follow a 'skeleton', i.e. a general transition map, if the current
   character is not the one of the path. As described in the above file, 
   a state is defined by a 'path walker' index and an iterator position that
   points to the position of a specific character string. Following code
   fragments need to be generated:

   (1) The pathes, i.e. array containing identified sequences, e.g.

        QUEX_CHARACTER_TYPE   path_0 = { 'o', 'r' }; 
        QUEX_CHARACTER_TYPE   path_1 = { 'h', 'i', 'l', 'e' }; 
        QUEX_CHARACTER_TYPE   path_2 = { 'e', 't', 'u', 'r', 'n' }; 

       The init state shall usually not be a path state. It rather routes
       to paths. This is why identified pathes usually do not contain the
       first character of a related keyword. Note, however, that quex 
       may find paths that are not explicitly considered by the user.

   (2) The path walker.

       The path walker consist of a 'prolog' where the current input character
       is checked whether it belongs to the path, and the remainging trigger
       map, in case that the path is left, e.g.

         PATH_WALKER_1:
            /* Single Character Check */
            if   input == *path_iterator: ++path_iterator; goto PATH_WALKER_1
            elif *path_iterator == 0:     goto STATE_3

            /* Common Transition Map */
            if   x < 'a': drop out
            elif x > 'z': drop out
            else:         goto STATE_4

   (3) State entries

       When pathes are keywords, then states that belong to a path are not
       entered except through 'path walk' along the character sequence.
       Theoretically, however, a state of a path might be entered from
       everywhere. Thus, at least for those states that are entered from
       somewhere, a path entry must be provided. 

       A path entry consists of: setting the path iterator and goto the
       related path walker. Additionally, state attributes, such as 
       'acceptance' and 'store_input_position' must be considered. 
       Example:

          STATE_10:
                path_iterator = path_0;
                goto PATH_WALKER_1;
          STATE_11:
                path_iterator = path_0 + 1;
                goto PATH_WALKER_1;
          ...
            
    (4) State router, this might be necessary, if states are non-uniform.
        Because, after reload the current state entry must passed by again.
        In buffer based analyzis no state router is required. Example of 
        a state router (same as for template compression):
        
        
            switch( state_index ) {
            case 2222: goto STATE_2222;
            case 3333: goto STATE_3333;
            ...
            }
"""
from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator

import quex.core_engine.generator.state_coder.core             as state_coder
import quex.core_engine.generator.state_coder.transition       as transition
import quex.core_engine.generator.state_coder.input_block      as input_block
import quex.core_engine.generator.state_coder.acceptance_info  as acceptance_info
import quex.core_engine.generator.state_coder.transition_block as transition_block
import quex.core_engine.generator.state_coder.drop_out         as drop_out
import quex.core_engine.generator.template_coder               as template_coder
import quex.core_engine.state_machine.index                    as index
import quex.core_engine.state_machine.core                     as state_machine
import quex.core_engine.state_machine.compression.paths        as paths 


from copy import deepcopy
from quex.input.setup import setup as Setup


LanguageDB = None # Set during call to 'do()', not earlier

def do(SMD):
    """RETURNS: Array 'x'

       x[0] transition target definitions in terms of a 
            local variable database
       x[1] code for templates and state entries
       x[2] state router for template targets
       x[3] involved_state_index_list
    """
    assert isinstance(SMD, StateMachineDecorator)
          
    # (1) Find possible state combinations
    path_list = paths.do(SMD.sm())

    # (2) Implement code for template combinations
    path_array_definitions,   \
    code,                     \
    router,                   \
    involved_state_index_list =  _do(path_list, SMD)

    local_variable_db = path_array_definitions
    if len(local_variable_db) != 0:
        local_variable_db.update({
          "path_iterator"   [ "QUEX_TYPE_GOTO_LABEL", "(QUEX_TYPE_GOTO_LABEL)0x0"],
          "path_state_key": [ "int",                  "(int)0"],
        })

    return "".join(code + router), \
           local_variable_db, \
           involved_state_index_list

def _do(PathList, SMD):
    """-- Returns generated code for all templates.
       -- Sets the template_compression_db in SMD.
    """
    global LanguageDB 

    assert type(PathList) == list
    assert isinstance(SMD, StateMachineDecorator)

    def __equal(SkeletonA, SkeletonB):
        if len(SkeletonA) != len(SkeletonB): return False

        for key, trigger_set in SkeletonA:
            if SkeletonB.has_key(key) == False: return False
            if trigger_set != SkeletonB[key]:   return False
        return True

    def __add_to_equivalent_path(path, path_db):
        for index, equivalent_path_list in path_db.items():
            for path in equivalent_path_list:
                if __same(path.skeleton(), candidate.skeleton()):
                    equivalent_path_list.append(path)
                    return True
        return False

    LanguageDB = Setup.language_db
    state_db   = SMD.sm().states
    SM_ID      = SMD.sm().get_id()

    # -- Sort the paths according their skeleton. Paths with the 
    #    same skeleton will use the same pathwalker.
    path_db = {}
    for candidate in PathList:
        assert isinstance(path, paths.CharacterPath)
        # Is there a path with the same skeleton?
        if __add_to_equivalent_path(candidate, path_db): continue
        path_db[index.get()] = [ candidate ]

    # -- Create 'PathWalkerState' objects that can mimik state machine states.
    # -- Collect all indices of states involved in paths
    involved_state_index_list = set([])
    for state_index, path_list in path_db.items():
        # Two Scenarios for settings at state entry (last_acceptance_position, ...)
        # 
        #   (i) All state entries are uniform: 
        #       -- Then, a representive state entry can be implemented at the 
        #          template entry. 
        #       -- Recursion happens to the template entry.
        #
        #   (ii) One or more state entry are different (non-uniform):
        #       -- The particularities of each state entry need to be implemented
        #          at state entry.
        #       -- Recursion is routed to entries of involved states.
        #      
        # The last state in sequence is the end target state, which cannot be 
        # addressed inside the pathwalker. It is the first state after the path.
        for path in path_list:
            involved_state_list = map(lambda info: info[0], path.sequence()[:-1])
            involved_state_index_list.update(involved_state_list)

        # -- Determine if all involved states are uniform
        prototype = template_coder.get_uniform_prototype(SMD, involved_state_list)

        pathwalker_list.append(PathWalkerState(path_list, SM_ID, state_index, prototype))


    # -- Generate code for:
    #        -- related variables: paths for pathwalkers
    #        -- state entries
    #        -- the pathwalkers
    #        -- state routes, required for example after reload.
    variable_db = {}
    code        = []
    router_code = []
    for pathwalker in pathwalker_list:
        for path in pathwalker.path_list():
            __add_path_definition(variable_db, path, path_id) 
        __state_entries(core, pathwalker)
        __path_walker(code, pathwalker)
        if not pathwalker.uniform_state_entries_f(): 
            __pathwalker_state_router(router_code, pathwalker)

    return variable_db, code, involved_state_index_list

class PathWalkerState(state_machine.State):
    """Implementation of a Path Walker that is able to play the role of a state
       machine state. It is constructed on the basis of a CharacterPath object
       that is create by module
       
                state_machine.compression.paths

       Goal of this definition is to have a state that is able to comply the
       requirements of 'state_coder.core'. Thus, the path walker generation can
       rely on the same procedure as all state machine states.  
    """

    def __init__(self, Path, StateMachineID, StateIndex, RepresentiveState):
        """Path contains all information about the states of a path and the
                path walker.
           
           StateIndex is the state index that is assigned to the path walker.

           RepresentiveState is a state that can represent all states in
                             the path. If all states of a path are
                             equivalent, so any of them can do.

                             If == None, then it means that state entries
                             differ and there is no representive state.
        """
        assert isinstance(Path, paths.CharacterPath)
        assert isinstance(RepresentiveState, state_machine.State) or RepresentiveState == None
        assert type(StateIndex) == long

        # (0) Components required to be a 'State'
        if RepresentiveState != None:
            self.__uniform_state_entries_f = True
            core        = deepcopy(RepresentiveState.core())
            origin_list = deepcopy(RepresentiveState.origins())
        else:
            self.__uniform_state_entries_f = False
            # Empty core and origins, since the particularities are handled at individual 
            # state entries.
            core        = state_machine.StateCoreInfo(StateMachineID, StateIndex, 
                                                      AcceptanceF=False)   
            origin_list = state_machine.StateOriginList()          

        state_machine.State._set(self, core, origin_list, Path.skeleton()) 

        state_machine.State.core(self).state_index = StateIndex

        # (1) Template related information
        self.__path = Path

    def uniform_state_entries_f(self):
        return self.__uniform_state_entries_f

    def path(self):
        return self.__path

def __path_definition(variable_db, Path):
    """Defines the transition targets for each involved state.
    """
    L = len(Path.sequence())
    txt = []
    for character in Path.sequence():
        txt.append("%i," % character)
    txt.append("0x0")

    variable_name  = "path_%i" % Path.index()
    variable_type  = "QUEX_TYPE_CHARACTER"
    dimension      = L + 1  # 1 space for terminating zero
    variable_value = "{ " + "".join(txt) + "}"

    variable_db[variable_name] = [ variable_type, variable_value, dimension ]

    variable_name  = "path_end_%i" % Path.index()
    variable_type  = "QUEX_TYPE_CHARACTER*"
    variable_value = "path_%i + %i" % (Path.index(), L + 1)
    variable_db[variable_name] = [ variable_type, variable_value ]

def __state_entries(code, PathWalker, SMD):
    """Defines the entries of the path's states, so that the state key
       for the template is set, before the jump into the template. E.g.

            STATE_4711: 
               path_iterator = path_23 + 0; goto PATHWALKER_23;
            STATE_3123: 
               path_iterator = path_23 + 1; goto PATHWALKER_23;
            STATE_8912: 
               path_iterator = path_23 + 2; goto PATHWALKER_23;
    """
    targeted_state_list = SMD.targeted_state_list()

    # Last state of sequence is not in the path, it is the first state after.
    for info in PathWalker.path.sequence()[:-1]:
        state_index = info[0]
        if state_index not in targeted_state_list: continue

        # Print the state label
        label_str = LanguageDB["$label-def"]("$entry", state_index)
        if state_index != SMD.sm().init_state_index:
            label_str = "    __quex_assert(false); /* No drop-through between states */\n" + \
                        label_str
        txt.append(label_str)

        state = SMD.sm().states[state_index]
        # If all state entries are uniform, the entry handling happens uniformly at
        # the entrance of the template, not each state.
        if not PathWalker.uniform_state_entries_f():
            txt.extend(input_block.do(state_index, False, SMD.backward_lexing_f()))
            txt.extend(acceptance_info.do(state, state_index, SMD, ForceSaveLastAcceptanceF=True))
            txt.append("    ")
            txt.append(LanguageDB["$assignment"]("state_index", "%i" % key).replace("\n", "\n    "))
        txt.append(LanguageDB["$goto"]("$path", PathWalker.core().state_index))
        txt.append("\n\n")

def __path_walker(txt, PathWalker):
    """Generates the path walker, that walks along the character sequence.
    """
    PathList     = PathWalker.path_list
    PathN        = len(PathList)
    Skeleton     = PathList[0].skeleton()
    PathWalkerID = PathWalker.core().state_index

    label_str = "    __quex_assert(false); /* No drop-through between states */\n" + \
                LanguageDB["$label-def"]("$path", PathID)
    txt.append(label_str)

    # -- The comparison with the path's current character
    #    If terminating zero is reached, the path's end state is entered.
    txt.append(LanguageDB["$if =="]("*path_iterator"))
    txt.append(LanguageDB["$goto"]("$path", PathWalkerID)
    txt.append(LanguageDB["$elseif"] 
               + LanguageDB["$=="]("path_iterator", "(QUEX_TYPE_CHARACTER)(0)")
               + LanguageDB["$then"])

    # -- Transition to the first state after the path:
    if PathN == 1:
        # (i) There is only one path for the pathwalker, then there is only
        #     one terminal and it is determined at compilation time.
        txt.append(LanguageDB["$goto"]("$entry", Path.end_state_index()))
    else:
        # (ii) There are multiple paths for the pathwalker, then the terminal
        #      must be determined at run time.
        def __get_action(txt, Path): 
            txt.append(LanguageDB["$goto"]("$entry", Path.end_state_index()))
        __path_specific_action(txt, PathList, __get_action)

    # -- Transition map of the 'skeleton'        
    if PathWalker.uniform_state_entries_f():
        txt.extend(input_block.do(state_index, False, SMD.backward_lexing_f()))
        txt.extend(acceptance_info.do(state, state_index, SMD, ForceSaveLastAcceptanceF=True))
    txt.extend(transition_block.do(TriggerMap, state_index, False, SMD))
    txt.extend(drop_out.do(state, state_index, SMD))

def __pathwalker_state_router(txt, PathWalker):
    """Create code that allows to jump to a state based on the path_iterator.

       NOTE: Paths cannot be recursive. Also, path transitions are linear, i.e.
             target states are either subsequent path states or the path
             is left. 

             State routing is only required at reload. There, the current state
             is identified by the 'path_iterator':

             (1) determine to what path the path_iterator belongs.
             (2) 'path_iterator - path_begin' gives an integer that identifies
                 the particular state of the path.
    """
    assert PathWalker.uniform_state_entries_f() == False

    def __get_action(Path):
        #    switch( path_iterator - path[i].begin ) {
        #         case 0:  STATE_341;
        #         case 1:  STATE_345;
        #         case 3:  STATE_346;
        #    }
        txt.append(LanguageDB["$switch"]("(int)(path_iterator - path_%i)"  % Path.index()))
        for i, info in enumarate(Path.sequence()[:-1]):
            txt.append(LanguageDB["$case"](i))
            txt.append(LanguageDB["$goto"]("$entry", info[0]))
        txt.append(LanguageDB["$switchend"])

    __path_specific_action(txt, PathWalker.path_list(), __get_action)

def __path_specific_action(txt, PathList, get_action):
    first_f = True
    for path in PathList:
        # if path_iterator >= path[i].begin and path_iterator < path[i].end:
        #      action of action_list[i]
        #    }
        sequence   = path.sequence()
        path_index = path.index()
        if first_f: 
            first_f = False
            txt.append(LanguageDB["$if"])
        else:
            txt.append(LanguageDB["$elsif"])
        txt.extend([
            LanguageDB["$>="]("path_iterator", "path_%i" % path_index),
            LanguageDB["$&&"],
            LanguageDB["$<"]("path_iterator", "path_%i_end" % path_index),
            LanguageDB["$then"]
        ])
        
        # Enter the path specific action
        txt.append(get_action(path))

        txt.append(LanguageDB["$endif"])
    return

