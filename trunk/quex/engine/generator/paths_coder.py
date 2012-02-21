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
from   quex.engine.generator.mega_state.core        import prepare_transition_map, \
                                                           drop_out_scheme_implementation
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.analyzer.state_entry_action      import DoorID


from   quex.blackboard import setup as Setup, \
                              E_StateIndices, \
                              E_EngineTypes

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
    drop_out_scheme_implementation(txt, PWState, TheAnalyzer, 
                                   "path_iterator - path_walker_%s_path_base" % PWState.index, 
                                   "__quex_debug_path_walker_drop_out(%i);\n" % PWState.index)

    # (*) Request necessary variable definition _______________________________
    __require_data(PWState, TheAnalyzer)

    return

def __path_walker(txt, PWState, TheAnalyzer):

    # Three Versions of PathWalkers:
    if PWState.uniform_entry_command_list_along_all_paths is not None:
        uniform_entry_door_id          = PWState.entry.get_door_id(PWState.index, PWState.index)
        uniform_terminal_entry_door_id = PWState.uniform_terminal_entry_door_id
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
            jump_to_terminal   = "        %s\n" % LanguageDB.GOTO_BY_DOOR_ID(uniform_terminal_entry_door_id)
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
            code     = ""
            for path_id, sequence in enumerate(PWState.path_list):
                terminal_door_id = PWState.terminal_door_id_of_path(PathID=path_id)
                code +=  "        %s"       % LanguageDB.IF("path_iterator", "==", "path_walker_%i_path_%i + %s" %  \
                                                            (PWState.index, path_id, len(sequence)-1),              \
                                                            FirstF=(path_id == 0))                                  \
                       + "            %s\n" % LanguageDB.GOTO_BY_DOOR_ID(terminal_door_id) 

            code += "        %s\n"     % LanguageDB.ELSE                                  
            code += "            %s\n" % LanguageDB.UNREACHABLE
            code += "        %s\n"     % LanguageDB.END_IF()                                  
            jump_to_terminal = code
    else:
        # (3) -- Non-Uniform entries (ALONG THE PATH)
        #        (The terminal door is going to be listed in the state sequence array)
        #
        #     if input == *path_iterator:
        #        path_iterator  += 1
        #        goto next_state(path_iterator)
        #        else if *path_iterator == TerminationCode:
        #           (input increment/decrement undo)      # we went one step too far
        next_state         = "path_walker_%i_state_base[path_iterator - path_walker_%i_reference]" \
                             % (PWState.index, PWState.index)
        jump_to_next_state = "%s" % (LanguageDB.GOTO_BY_VARIABLE(next_state))
        jump_to_terminal   = ""

    # Jump to terminal: We went one step too far: UNDO input pointer increment/decrement
    if PWState.engine_type == E_EngineTypes.FORWARD: undo_incr_decr = LanguageDB.INPUT_P_DECREMENT()
    else:                                            undo_incr_decr = LanguageDB.INPUT_P_INCREMENT()

    txt.extend(["    __quex_debug_path_walker_iteration(%i, path_iterator);\n" % PWState.index,
                "    %s"     % LanguageDB.IF_INPUT("==", "*path_iterator"),
                "        %s\n" % LanguageDB.PATH_ITERATOR_INCREMENT,
                "        %s\n" % jump_to_next_state,
                "    %s" % LanguageDB.IF("*path_iterator", "==", "QUEX_SETTING_PATH_TERMINATION_CODE", FirstF=False),
                "        %s\n" % undo_incr_decr,
                jump_to_terminal,
                "    %s\n" % LanguageDB.END_IF()])

def __require_data(PWState, TheAnalyzer):
    """Defines the transition targets for each involved state.
    """
    variable_db.require("path_iterator")

    def __state_sequences():
        result = ["{\n"]
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
            result.append("        ")
            for state_index in (x[0] for x in path[1:]):
                result.append("QUEX_LABEL(%i), " % LanguageDB.ADDRESS(state_index, prev_state_index))
                prev_state_index = state_index
            result.append("/* Zero of Elegance */0x0,")
            result.append("\n")

            offset += len(path)

        result.append("    }");
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
            result.append("QUEX_SETTING_PATH_TERMINATION_CODE,")
            result.append("\n")

            variable_db.require("path_walker_%i_path_%i", 
                                Initial = "path_walker_%i_path_base + %i" % (PWState.index, offset), 
                                Index   = (PWState.index, path_id))

            offset += len(path)

        result.append("    }")
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
        # The path_iterator is incremented before the 'goto', thus
        # 'path_iterator - (path_base + 1)' gives actually the correct offset.
        # We define a variable for that, for elegance.
        variable_db.require("path_walker_%i_reference", 
                            Initial = "path_walker_%i_path_base + 1" % PWState.index, 
                            Index   = (PWState.index))

