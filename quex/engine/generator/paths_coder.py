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
from   quex.engine.generator.state.transition.code  import TextTransitionCode
from   quex.engine.generator.languages.address      import get_label
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.analyzer.state_entry_action      import DoorID
from   quex.engine.interval_handling                import Interval


from   quex.blackboard import setup as Setup, \
                              E_StateIndices, \
                              E_EngineTypes, \
                              E_Compression

from   itertools import imap
import sys

LanguageDB = None # Set during call to 'do()', not earlier

def do(txt, PWState, TheAnalyzer):
    global LanguageDB
    LanguageDB = Setup.language_db

    # (*) Entry _______________________________________________________________
    entry_coder.do(txt, PWState, TheAnalyzer) 

    # (*) Access input character ______________________________________________
    input_do(txt, PWState, ForceInputDereferencingF=True) 

    # (*) The Path Walker Framework
    __path_walker(txt, PWState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    prepare_transition_map(PWState)
    transition_block.do(txt, 
                        PWState.transition_map, 
                        PWState.index, 
                        PWState.engine_type, 
                        PWState.init_state_f, 
                        TheAnalyzer = TheAnalyzer)

    # (*) Drop Out ____________________________________________________________
    __drop_out(txt, PWState, TheAnalyzer)

    # (*) Request necessary variable definition _______________________________
    __require_data(PWState, TheAnalyzer)

    return

def __path_walker(txt, PWState, TheAnalyzer):
    uniform_entry_door_id          = PWState.uniform_entry_door_id_along_all_paths
    uniform_terminal_entry_door_id = PWState.uniform_terminal_entry_door_id
    # Three Versions of PathWalkers:
    # 
    if uniform_entry_door_id is not None:
        if uniform_terminal_entry_door_id is not None:
            # (1) -- Uniform entries (ALONG THE PATH)
            #     -- All path have same terminal state and enter it at the same door
            # 
            # if input == *path_iterator:
            #    path_iterator += 1
            #    goto the single path walker entry     # jump to next state
            # else if *path_iterator == TerminationCode:
            #    (input increment/decrement undo)      # we went one step too far
            #    goto TerminalDoorID
            jump_to_next_state = LanguageDB.GOTO_BY_DOOR_ID(uniform_entry_door_id)
            jump_to_terminal   = LanguageDB.GOTO_BY_DOOR_ID(uniform_terminal_entry_door_id)
        else:
            #   (2) -- Uniform entries (ALONG THE PATH)
            #       -- The terminal of the paths are different
            # 
            #        if input == *path_iterator:
            #           path_iterator += 1
            #           goto the single path walker entry     # jump to next state
            #        else if *path_iterator == TerminationCode:
            #           (input increment/decrement undo)      # we went one step too far
            #           if      path_iterator == path_0_end:  goto terminal_0
            #           else if path_iterator == path_1_end:  goto terminal_1
            #           else if path_iterator == path_2_end:  goto terminal_2
            #           ...
            jump_to_next_state = LanguageDB.GOTO_BY_DOOR_ID(uniform_entry_door_id)
            if PWState.engine_type == E_EngineTypes.FORWARD: undo_incr_decr = LanguageDB.INPUT_P_DECREMENT()
            else:                                            undo_incr_decr = LanguageDB.INPUT_P_INCREMENT()
            txt      = ""
            else_str = ""
            for path_id, sequence in enumerate(PWState.path_list):
                terminal_door_id = PWState.terminal_door_id_of_path(PathID=path_id)
                txt +=   "    %s%s\n"   % (else_str, LanguageDB.IF("path_iterator", "==", "path_walker_%i_path_%i%s" %  \
                                                                   (PWState.index, path_id, len(sequence))))            \
                       + "        %s\n" % LanguageDB.GOTO_BY_DOOR_ID(terminal_door_id)                                  \
                       + "    %s\n"     % LanguageDB.END_IF()                                              

            jump_to_terminal = "%s\n%s" % (undo_incr_decr, txt)
    else:
        # (3) -- Non-Uniform entries (ALONG THE PATH)
        #        (The terminal door is going to be listed in the state sequence array)
        #
        #     if input == *path_iterator:
        #        path_iterator  += 1
        #        state_iterator += 1    # The 'entries' must set the state iterator appropriately
        #        goto *state_iterator
        jump_to_next_state = "%s\n    %s\n" % (LanguageDB.STATE_ITERATOR_INCREMENT, 
                                               LanguageDB.GOTO_BY_VARIABLE("*state_iterator"))
        jump_to_terminal   = None

    txt.extend(["    __quex_debug_path_walker_iteration(%i, path_iterator);\n" % PWState.index,
                "    %s\n"     % LanguageDB.IF_INPUT("==", "*path_iterator"),
                "        %s\n" % LanguageDB.PATH_ITERATOR_INCREMENT,
                "        %s\n" % jump_to_next_state])

    if jump_to_terminal is None:
        txt.append("    %s\n" % LanguageDB.END_IF())
    else:
        txt.extend(["    %s\n" % LanguageDB.IF("*path_iterator", "==", "QUEX_SETTING_PATH_TERMINATION_CODE", FirstF=False),
                    "        %s\n" % jump_to_end_state,
                    "    %s\n" % LanguageDB.END_IF()])

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
        drop_out_txt = []
        drop_out_coder.do(drop_out_txt, prototype, TheAnalyzer, DefineLabelF=False)
        case_list.append( (state_key_list, drop_out_txt) )

    case_txt = LanguageDB.SELECTION("path_iterator - path_walker_%s_path_base" % PWState.index, 
                                    case_list, CaseFormat="dec")
    LanguageDB.INDENT(case_txt)
    txt.extend(case_txt)

def __require_data(PWState, TheAnalyzer):
    """Defines the transition targets for each involved state.
    """
    variable_db.require("path_iterator")
    if PWState.uniform_entry_door_id_along_all_paths is None:
        variable_db.require("state_iterator")

    def __state_sequences():
        result = ["{ "]
        offset = 0
        for path_id, path in enumerate(PWState.path_list):
            # NOTE: For all states in the path the 'from_state_index, to_state_index' can
            #       be determined, **except** for the FIRST state in the path. Thus for
            #       this state the 'door' cannot be determined in case that it is 
            #       "not uniform_doors_f()". 
            #
            #       However, the only occasion where the FIRST state in the path may be 
            #       used is reload during the FIRST state. The reload adapts the positions
            #       and acceptances are not changed. So, we can use the common entry
            #       to the first state as a reference here.
            prev_state_index  = path[0][0]
            for state_index in (x[0] for x in path[1:]):
                result.append("QUEX_LABEL(%i), " % LanguageDB.ADDRESS(state_index, prev_state_index))
                prev_state_index = state_index
            result.append("\n")

            # The initial iterator always points ONE before the beginning of the list.
            # BECAUSE: '*state_iterator' is first called after 'state_iterator += 1'
            # BUT:     This happens when the 'SetStateIterator' objects are created.
            variable_db.require("path_walker_%i_path_%i_states", 
                                Initial = "path_walker_%i_state_base + %i" % (PWState.index, offset), 
                                Index   = (PWState.index, path_id))

            offset += len(path)

        result.append(" }");
        return offset, result

    def __character_sequences():

        result = ["{\n"]
        offset = 0
        for path_id, path in enumerate(PWState.path_list):
            # Commenting the transition sequence is not dangerous. 'COMMENT' eliminates
            # comment delimiters if they would appear in the sequence_str.
            # sequence_str = imap(lambda x: Interval(x[1]).get_utf8_string(), path[:-1])
            # memory.append(LanguageDB.COMMENT("".join(sequence_str)) + "\n")

            # Last element of sequence contains only the 'end state'.
            result.append("        ")
            result.extend(imap(lambda x: "%i, " % x[1], path[:-1]))
            result.append("QUEX_SETTING_PATH_TERMINATION_CODE, ")
            result.append("\n")

            variable_db.require("path_walker_%i_path_%i", 
                                Initial = "path_walker_%i_path_base + %i" % (PWState.index, offset), 
                                Index   = (PWState.index, path_id))

            offset += len(path)

        result.append("\n    }")
        return offset, result

    # (*) Path Walker Basis
    # The 'base' must be defined before all --> PriorityF (see table in variable_db)
    element_n, character_sequence_str = __character_sequences()
    variable_db.require_array("path_walker_%i_path_base", 
                              ElementN = element_n,
                              Initial  = character_sequence_str,
                              Index    = PWState.index)
    
    # (*) The State Information for each path step
    if PWState.uniform_entry_door_id_along_all_paths is None:
        element_n, state_sequence_str = __state_sequences()
        variable_db.require_array("path_walker_%i_state_base", 
                                  ElementN = element_n,
                                  Initial  = state_sequence_str,
                                  Index    = PWState.index)

def prepare_transition_map(PWState):
    """Prepare the transition map of the PWState for code generation.
       The targets of a PathWalkerState are all 'DoorID's. Here, they
       are translated into text.

       NOTE: A word about the reload procedure.
       
       Reload can end either with success (new data has been loaded), or failure
       (no more data available). In case of success the **only** the transition
       step has to be repeated. Nothing else is effected.  Stored positions are
       adapted automatically.
       
       By convention we redo the transition map, in case of reload success and 
       jump to the state's drop-out in case of failure. There is no difference
       here in the template state example.
    """
    # Transition map of the 'skeleton'        
    if PWState.transition_map_empty_f:
        # Transition Map Empty:
        # This happens, for example, if there are only keywords and no 
        # 'overlaying' identifier pattern. But, in this case also, there
        # must be something that catches the 'buffer limit code'. 
        # => Define an 'all drop out' trigger_map, and then later
        # => Adapt the trigger map, so that the 'buffer limit' is an 
        #    isolated single interval.
        PWState.transition_map = [ (Interval(-sys.maxint, sys.maxint), E_StateIndices.DROP_OUT) ]

    transition_map = PWState.transition_map

    for i, info in enumerate(transition_map):
        interval, target = info
        if target == E_StateIndices.DROP_OUT: continue
        assert isinstance(target, DoorID)
        target            = TextTransitionCode([LanguageDB.GOTO_BY_DOOR_ID(target)])
        transition_map[i] = (interval, target)
    return

