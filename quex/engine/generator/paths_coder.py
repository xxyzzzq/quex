"""(C) Frank-Rene Schaefer

   Path Compression ___________________________________________________________

   Consider the file 'engine/analyzer/path/core.py' for a detailed explanation 
   of path compression.

   Code Generation ____________________________________________________________

   Let 'path walker' be a code fragment that is able to 'walk' along a given
   path and follow a 'skeleton', i.e. a general transition map, if the current
   character is not the one of the path. As described in the above file, 
   a state is defined by a 'path walker' index and an iterator position that
   points to the position of a specific character string. Following code
   fragments need to be generated:

   (1) The pathes, i.e. array containing identified sequences, e.g.

        QUEX_CHARACTER_TYPE   path_0 = { 'o', 'r', PTC }; 
        QUEX_CHARACTER_TYPE   path_1 = { 'h', 'i', 'l', 'e', PTC }; 
        QUEX_CHARACTER_TYPE   path_2 = { 'e', 't', 'u', 'r', 'n', PTC }; 

       where PTC is the path terminating code that must be 
       different from the buffer limit code BLC.

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
            elif *path_iterator == PTC:     goto STATE_3

            /* Common Transition Map */
            if   x < 'a': drop out
            elif x > 'z': drop out
            else:         goto STATE_4

   (3) State entries

       It is very plausible that states that belong to a path are not
       entered except through 'path walk' along the character sequence.
       In general, however, a state of a path might be entered from
       anywhere. Thus, at least for those states that are entered from
       elsewhere, a path entry must be provided. 

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
        In buffer based analysis no state router is required. Example of 
        a state router (same as for template compression):
        
        
            switch( state_index ) {
            case 2222: goto STATE_2222;
            case 3333: goto STATE_3333;
            ...
            }
"""
import quex.engine.generator.state.transition.core  as transition_block
import quex.engine.generator.state.drop_out         as drop_out_coder
import quex.engine.generator.state.entry            as entry_coder
from   quex.engine.generator.state.core             import input_do
from   quex.engine.generator.template_coder               import handle_source_state_dependent_transitions
from   quex.engine.generator.languages.address            import get_label
from   quex.engine.generator.languages.variable_db        import variable_db
from   quex.engine.interval_handling                      import Interval

import quex.engine.analyzer.path.core                     as paths 

from   quex.blackboard import setup as Setup, \
                              E_StateIndices, \
                              E_EngineTypes, \
                              E_Compression

from   itertools import imap
import sys

LanguageDB = None # Set during call to 'do()', not earlier

def do(txt, TheAnalyzer, CompressionType, Remainder):
    """--> Accept only uniform states in path.
                        (This must be done by the 'analyzer module' too.)
    
       RETURNS: List of done state indices.
    """
    assert CompressionType in [E_Compression.PATH, E_Compression.PATH_UNIFORM]

    global LanguageDB
    LanguageDB = Setup.language_db

    # (1) Find possible state combinations
    path_walker_list = paths.do(TheAnalyzer, CompressionType, AvailableStateIndexList=Remainder)

    if len(path_walker_list) == 0: return []

    # (2) Implement code for path combinations
    variable_db.require("path_iterator")

    done_set = set()
    for pw_state in path_walker_list:
        state_coder_do(txt, pw_state, TheAnalyzer)
        done_set.update(pw_state.implemented_state_index_list)

    return done_set

def state_coder_do(txt, PWState, TheAnalyzer):
    # (*) Entry _______________________________________________________________
    __entry(txt, PWState, TheAnalyzer)

    # (*) Access input character ______________________________________________
    input_do(txt, PWState, ForceInputDereferencingF=True) 

    # (*) Transition Map ______________________________________________________
    __transition_map(txt, PWState, TheAnalyzer)

    # (*) Drop Out ____________________________________________________________
    __drop_out(txt, PWState, TheAnalyzer)

    # (*) Request necessary variable definition _______________________________
    __require_data(PWState, TheAnalyzer)

    return

def __entry(txt, PWState, TheAnalyzer):
    """Implement entries of states related to the path walker. If the states
       are uniform then only those states need entries that are entered from other
       states than the predecessor on the path. If the states are non-uniform,
       each entry pattern needs to be implemented.  

       This function is very similar to 'template_coder.__entry()' where further 
       explanations are provided.
    """
    path_end_state_required_f = (PWState.uniform_entries_f and len(PWState.path_list) != 1)
    if path_end_state_required_f: variable_db.require("path_end_state")

    def prepare_path_iterator(txt, PathID, PathOffset):
        if path_end_state_required_f:
            assert len(PWState.path_list[PathID]) >= 2
            end_state_index  = PWState.path_list[PathID][-1][0]
            prev_state_index = PWState.path_list[PathID][-2][0]
            txt.append("    path_end_state                 = QUEX_LABEL(%i);\n" \
                       % LanguageDB.ADDRESS(end_state_index, prev_state_index))
        offset_str = ""
        if PathOffset != 0: offset_str = " + %i" % PathOffset
        txt.append(1)
        txt.append(LanguageDB.ASSIGN("path_iterator", 
                                     "path_walker_%i_path_%i%s" % (PWState.index, PathID, offset_str)))
        txt.append("\n")

    def is_iterator_setup_required(StateIndex, PathOffset, TheAnalyzer):
        """Determine whether an external entry definition for the given state is required. 
           This is the case, if the state is the first state of the path. For states
           along the path, this is only necessary, if there are entries from outside.
           Then the number of states that enter it is >= 1.
        """
        if PathOffset == 0:                             return True
        elif len(TheAnalyzer.from_db[state_index]) > 1: return True
        return False
                
    if PWState.uniform_entries_f:
        entry, dummy = PWState.entry.iteritems().next()
        state_index_list = PWState.implemented_state_index_list
        # Assign the state keys for each state involved
        for state_index, path_id, path_offset, state in PWState.state_set_iterable(state_index_list, TheAnalyzer):
            if not is_iterator_setup_required(state_index, path_offset, TheAnalyzer): continue
            LanguageDB.STATE_ENTRY(txt, state)
            txt.append("    __quex_debug_path_walker_entry(%i, %i);\n" % (PWState.index, path_id))
            prepare_path_iterator(txt, path_id, path_offset)
            txt.append("    %s\n" % LanguageDB.GOTO(PWState.index))

        # Implement the common entry
        txt.extend("%s\n" % LanguageDB.LABEL(PWState.index))
        entry_coder.do(txt, PWState, TheAnalyzer, UnreachablePrefixF=False, LabelF=False)
        return
                
    # Non-Uniform Entries
    i = -1
    for entry, state_index_list in PWState.entry.iteritems():
        iterable = PWState.state_set_iterable(state_index_list, TheAnalyzer)
        if entry.is_independent_of_source_state():
            i += 1
            # Assign the state keys for each state involved
            for state_index, path_id, path_offset, state in iterable:
                LanguageDB.STATE_ENTRY(txt, state)
                txt.append("    __quex_debug_path_walker_entry(%i, %i);\n" % (PWState.index, path_id))
                if is_iterator_setup_required(state_index, path_offset, TheAnalyzer): 
                    prepare_path_iterator(txt, path_id, path_offset)
                if len(state_index_list) != 1:
                    txt.append("    %s\n" % LanguageDB.GOTO_SHARED_ENTRY(PWState.index, i))
            # Implement the common entry
            if len(state_index_list) != 1:
                txt.extend("%s\n" % LanguageDB.LABEL_SHARED_ENTRY(PWState.index, i))
            prototype = TheAnalyzer.state_db[state_index_list.__iter__().next()]
            entry_coder.do(txt, prototype, TheAnalyzer, UnreachablePrefixF=False, LabelF=False)
            txt.append("    %s\n" % LanguageDB.GOTO(PWState.index))
        else:
            for state_index, path_id, path_offset, state in iterable:
                # Implement the particular entry
                entry_coder.do(txt, state, TheAnalyzer) # , UnreachablePrefixF=(i==0))
                txt.append("    __quex_debug_path_walker_entry(%i, %i);\n" % (PWState.index, path_id))
                # Assign the state keys for each state involved
                if is_iterator_setup_required(state_index, path_offset, TheAnalyzer): 
                    prepare_path_iterator(txt, path_id, path_offset)
                txt.append("    %s\n" % LanguageDB.GOTO(PWState.index))

    # Implement entry point
    txt.extend("%s\n" % LanguageDB.LABEL(PWState.index))

def __transition_map(txt, PWState, TheAnalyzer):
    """Generates the path walker, that walks along the character sequence.
    """
    # (3) Transition Map

    # (3.1) The comparison with the path's current character
    #       If terminating zero is reached, the path's end state is entered.
    if PWState.uniform_entries_f:
        jump_to_next_state = [ LanguageDB.GOTO(PWState.index), "\n" ]
        jump_to_end_state  = __jump_to_path_end_state(PWState)
    else:
        jump_to_next_state = [ __jump_to_state_router(PWState) ]
        jump_to_end_state  = [2, __jump_to_state_router(PWState) ]

    # Two Versions:
    #   (i) Uniform Entries
    #       if input == *path_iterator:
    #          path_iterator += 1
    #          jump to path walker entry                # jump to next state
    #       else if *path_iterator == TerminationCode:
    #          end state router(path_iterator)          # goto first state after path
    #       end
    #    (ii) Non-Uniform Entries
    #         (goto first state after path == jump to next state)
    #       if input == *path_iterator:
    #          path_iterator += 1
    #          state router(path_iterator)              # jump to next state
    #       else if *path_iterator == TerminationCode:
    #          state router(path_iterator)              # goto first state after path
    #       end
    txt.append(1)
    txt.append("__quex_debug_path_walker_iteration(%i, path_iterator);\n" % PWState.index)
    txt.append(1)
    txt.append(LanguageDB.IF_INPUT("==", "*path_iterator"))
    txt.append(2)
    txt.append(LanguageDB.PATH_ITERATOR_INCREMENT)
    txt.append("\n")
    txt.append(2)
    txt.extend(jump_to_next_state)
    txt.append(1)
    txt.append(LanguageDB.IF("*path_iterator", "==", "QUEX_SETTING_PATH_TERMINATION_CODE", FirstF=False))
    txt.append(2)
    txt.append("__quex_debug_path_walker_exit(%i);\n" % PWState.index)
    txt.extend(jump_to_end_state)
    txt.append(1)
    txt.append(LanguageDB.END_IF())
    txt.append("\n")

    # (3.2) Transition map of the 'skeleton'        
    if not PWState.transition_map_empty_f:
        transition_map = PWState.transition_map
    else:
        # (This happens, for example, if there are only keywords and no 
        #  'overlaying' identifier pattern.)
        # Even if the skeleton/trigger map is empty there must be something
        # that catches the 'buffer limit code'. 
        # => Define an 'all drop out' trigger_map and then,
        # => Adapt the trigger map, so that the 'buffer limit' is an 
        #    isolated single interval.
        transition_map = [ (Interval(-sys.maxint, sys.maxint), E_StateIndices.DROP_OUT) ]

    handle_source_state_dependent_transitions(PWState.transition_map, 
                                              TheAnalyzer, 
                                              "path_iterator - path_walker_%i_base" % PWState.index, 
                                              PWState.state_index_list)

    # A word about the reload procedure:
    #
    # Reload can end either with success (new data has been loaded), or failure
    # (no more data available). In case of success the **only** the transition
    # step has to be repeated. Nothing else is effected.  Stored positions are
    # adapted automatically.
    #
    # By convention we redo the transition map, in case of reload success and 
    # jump to the state's drop-out in case of failure. There is no difference
    # here in the template state example.
    transition_block.do(txt, 
                        transition_map, 
                        PWState.index, 
                        PWState.engine_type, 
                        PWState.init_state_f, 
                        TheAnalyzer = TheAnalyzer)
    return 

def __drop_out(txt, PWState, TheAnalyzer):
    # (*) Central Label for the Templates Drop Out
    txt.append("%s\n" % LanguageDB.LABEL_DROP_OUT(PWState.index))
    txt.append(1)
    txt.append("__quex_debug_path_walker_drop_out(%i);\n" % PWState.index)

    # (*) Drop Out Section(s)
    if PWState.uniform_drop_outs_f:
        # -- uniform drop outs => no switch required
        prototype = TheAnalyzer.state_db[PWState.state_index_list.__iter__().next()]
        drop_out_coder.do(txt, prototype, TheAnalyzer, DefineLabelF=False)
        return

    # -- non-uniform drop outs => route by 'state_key'
    case_list = []
    for drop_out, state_index_list in PWState.drop_out.iteritems():
        # state keys related to drop out
        state_key_list = map(lambda i: PWState.state_index_list.index(i), 
                             state_index_list)
        # drop out action
        prototype = TheAnalyzer.state_db[state_index_list.__iter__().next()]
        action    = []
        drop_out_coder.do(action, prototype, TheAnalyzer, DefineLabelF=False)
        case_list.append( (state_key_list, action) )

    case_txt = LanguageDB.SELECTION("path_iterator - path_walker_%i_base" % PWState.index, 
                                    case_list, CaseFormat="dec")
    LanguageDB.INDENT(case_txt)
    txt.extend(case_txt)

def __require_data(PWState, TheAnalyzer):
    """Defines the transition targets for each involved state.
    """
    def __state_sequences():
        result    = ["{ "]
        element_n = 0
        for path in PWState.path_list:
            first_state_index = path[0][0]
            # NOTE: For all states in the path the 'from_state_index, to_state_index' can
            #       be determined, **except** for the FIRST state in the path. Thus for
            #       this state the 'door' cannot be determined in case that it is 
            #       "not is_independent_of_source_state()". 
            #
            #       However, the only occasion where the FIRST state in the path may be 
            #       used is reload during the FIRST state. The reload adapts the positions
            #       and acceptances are not changed. So, we can use the common entry
            #       to the first state as a reference here.
            result.append("QUEX_LABEL(%i), " % LanguageDB.ADDRESS(first_state_index, None))

            prev_state_index = first_state_index
            for state_index in imap(lambda x: x[0], path[1:]):
                result.append("QUEX_LABEL(%i), " % LanguageDB.ADDRESS(state_index, prev_state_index))
                prev_state_index = state_index
            result.append("\n")

            element_n += len(path)

        result.append(" }");
        return element_n, result

    def __character_sequences():

        result = ["{\n"]
        offset = 0
        for path_id, path in enumerate(PWState.path_list):
            # Commenting the transition sequence is not dangerous. 'COMMENT' eliminates
            # comment delimiters if they would appear in the sequence_str.
            # sequence_str = imap(lambda x: Interval(x[1]).get_utf8_string(), path[:-1])
            # memory.append(LanguageDB.COMMENT("".join(sequence_str)) + "\n")

            # Last element of sequence contains only the 'end state'.
            result.append(2)
            result.extend(imap(lambda x: "%i, " % x[1], path[:-1]))
            result.append("QUEX_SETTING_PATH_TERMINATION_CODE, ")
            result.append("\n")

            variable_db.require("path_walker_%i_path_%i", 
                                Initial = "path_walker_%i_base + %i" % (PWState.index, offset), 
                                Index   = (PWState.index, path_id))

            offset += len(path)

        result.append("\n    }")
        return offset + 1, result

    # (*) Path Walker Basis
    # The 'base' must be defined before all --> PriorityF (see table in variable_db)
    element_n, character_sequence_str = __character_sequences()
    variable_db.require_array("path_walker_%i_base", 
                              ElementN = element_n,
                              Initial  = character_sequence_str,
                              Index    = PWState.index)
    
    # (*) The State Information for each path step
    if not PWState.uniform_entries_f:
        element_n, state_sequence_str = __state_sequences()
        variable_db.require_array("path_walker_%i_state", 
                                  ElementN = element_n,
                                  Initial  = state_sequence_str,
                                  Index    = PWState.index)

def get_reload_info(PWState):
    """The 'reload' must know where to go in case that the reload succeeds 
       and in case that it fails:
       
       -- If the reload succeeds it must reenter the same state. If the 
          entries are not uniform, the entry must be identified by 'state key'. 
          
       -- If the reload fails the current state's drop out section must be 
          entered. The routing to state's particular drop out section happens
          from the templates central drop out at the end of the transition map.
    """
    if PWState.uniform_entries_f:
        ok_state_str = None # Default: Template's common entry
    else:
        ok_state_str = "path_walker_%i_map_state_key_to_entry_index[path_iterator - path_walker_%i_base]" \
                       % (PWState.index, PWState.index)

    # DropOut is handled at the end of the transition map.
    # From there, it is routed by the state_key to the particular drop out.
    fail_state_str = "QUEX_LABEL(%i)" % LanguageDB.ADDRESS_DROP_OUT(PWState.index)

    return ok_state_str, fail_state_str

def __jump_to_state_router(PWState):
    """Create code that jumps to a state based on the path_iterator.

       NOTE: Paths cannot be recursive. Also, path transitions are linear, i.e.
             target states are either subsequent path states or the path
             is left. 

             The current state is identified by the 'path_iterator'

             (1) determine to what path the path_iterator belongs.
             (2) 'path_iterator - path_begin' gives an integer that identifies
                 the particular state of the path.

       NOTE: In the case of non-uniform path state elements, the state router
             takes care of the detection of the end-state, thus it has not
             to be determined in the '*path_iterator == PTC' section.
    """
    assert not PWState.uniform_entries_f

    ID = PWState.index

    # Make sure that the state router is implemented, add reference:
    get_label("$state-router", U=True)
    return "QUEX_GOTO_STATE(path_walker_%i_state[path_iterator - path_walker_%i_base]);\n" % (ID, ID)

def __jump_to_path_end_state(PWState):
    """After the last transition of the path, transit into the 'end state',
       i.e. the first state after the path. If the path walker contains multiple
       path, this might include state routing.  
    """
    assert PWState.uniform_entries_f

    PathList = PWState.path_list
    PathN    = len(PathList)

    txt = []
    txt.append(2)
    # Undo last step
    if PWState.engine_type == E_EngineTypes.FORWARD: txt.append(LanguageDB.INPUT_P_DECREMENT())
    else:                                            txt.append(LanguageDB.INPUT_P_INCREMENT())
    txt.append("\n")

    # -- Transition to the first state after the path:
    if PathN == 1:
        # (i) There is only one path for the pathwalker, then there is only
        #     one terminal and it is determined at compilation time.
        prototype_path  = PathList[0]
        end_state_index = prototype_path[-1][0]
        txt.append(2)
        txt.append(LanguageDB.GOTO(end_state_index))
    else:
        # (ii) There are multiple paths for the pathwalker, then the terminal
        #      must be determined at run time.
        #   -- At the end of the path, path_iterator == path_end, thus we can identify
        #      the path by comparing simply against all path_ends.
        get_label("$state-router", U=True) # Make sure, that state router is referenced
        txt.append(2)
        txt.append("QUEX_GOTO_STATE(path_end_state);")

    txt.append("\n")
    return txt

