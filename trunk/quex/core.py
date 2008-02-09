# ActionInfo objects contain information about patterns and actions
#            important to the code generator. They differ slightly from
#            the 'Match' objects created for the 'LexMode' description.
from copy import copy
import os
import sys

from   quex.frs_py.file_in import error_msg

import quex.token_id_maker                      as token_id_maker
import quex.lexer_mode                          as lexer_mode
from   quex.lexer_mode                          import ReferencedCodeFragment_straighten_open_line_pragmas, \
                                                       ReferencedCodeFragment
from quex.token_id_maker                        import TokenInfo

import quex.core_engine.regular_expression.core as regex
import quex.core_engine.generator.core          as generator
import quex.input.quex_file_parser              as quex_file_parser
import quex.consistency_check                   as consistency_check
import quex.output.cpp.core                     as quex_class_out
import quex.output.cpp.action_code_formatter    as action_code_formatter



def do(Setup):
    """Generates state machines for all modes. Each mode results into 
       a separate state machine that is stuck into a virtual function
       of a class derived from class 'quex_mode'.
    """

    LexerClassName = Setup.output_engine_name
    # NOTE: The generated header file that contains the lexical analyser class includes
    #       the file "code_base/code_base/definitions-quex-buffer.h". But the analyser
    #       functions also need 'connection' to the lexer class, so we include the header
    #       of the generated lexical analyser at this place.
    QuexEngineHeaderDefinitionFile = Setup.output_file_stem 

    lexer_mode.token_id_db["TERMINATION"]   = TokenInfo("TERMINATION",   ID=Setup.token_id_termination)
    lexer_mode.token_id_db["UNINITIALIZED"] = TokenInfo("UNINITIALIZED", ID=Setup.token_id_uninitialized)

    # (0) check basic assumptions
    if Setup.input_mode_files == []:
        print "error: no input files"
        sys.exit(-1)
    else:
        pass # print "input:", repr(Setup.input_mode_files)
    
    # (1) input: do the pattern analysis, in case exact counting of newlines is required
    #            (this might speed up the lexer, but nobody might care ...)
    #            pattern_db = analyse_patterns.do(pattern_file)    
    mode_db = quex_file_parser.do(Setup.input_mode_files, Setup)

    # (*) perform consistency check 
    consistency_check.do(mode_db)

    #
    # only inheritable == abstract => no real implemented mode exist of this
    # (such modes only serve as base modes for other modes)
    mode_list = filter(lambda mode: mode.options["inheritable:"] != "only", 
                       mode_db.values())

    mode_name_list = map(lambda mode: mode.name, mode_list)

    # (2) implement the 'quex' core class from a template
    #
    # -- create a file for the creation of the mode class code
    Setup.tmp_mode_class_implementation_file = Setup.output_code_file
    # -- do the coding of the class framework
    quex_class_out.do(mode_db, Setup)

    # (3) create the token ids
    token_id_maker.do(Setup) 

    # (3) implement the lexer mode-specific analyser functions
    inheritance_info_str = "/* [dominating inheritance level] [pattern index] [pattern]\n"
    analyzer_code = ""
    for mode in mode_list:        
        # -- some modes only define event handlers that are inherited
        if mode.matches == {}: continue

        # -- adapt pattern-action pair information so that it can be treated
        #    by the code generator.
        pattern_action_pair_info_list = mode.pattern_action_pairs().values()

        # -- default action
        default_action = action_code_formatter.do(mode, mode.on_failure_code_fragments(), Setup, 
                                                  "on_failure", None, DefaultActionF=True)

        # -- pattern-action pairs
        dummy, pattern_action_pair_list = get_generator_input(mode, pattern_action_pair_info_list, 
                                                              Setup)

        # accumulate inheritance information for comment
        inheritance_info_str += dummy + "**\n"

        analyzer_code += generator.do(pattern_action_pair_list, 
                                      default_action, 
                                      PrintStateMachineF             = True,
                                      StateMachineName               = mode.name,
                                      AnalyserStateClassName         = Setup.output_engine_name,
                                      StandAloneAnalyserF            = False, 
                                      QuexEngineHeaderDefinitionFile = QuexEngineHeaderDefinitionFile,
                                      ModeNameList                   = mode_name_list)   
        
    # write code to a header file
    fh = open(LexerClassName + "-core-engine.cpp", "w")
    if os.linesep == "\n": analyzer_code = analyzer_code.replace("\n", os.linesep)
    fh.write(analyzer_code)
    fh.close()
    ReferencedCodeFragment_straighten_open_line_pragmas(LexerClassName + "-core-engine.cpp", "C")
    ReferencedCodeFragment_straighten_open_line_pragmas(LexerClassName + ".cpp", "C")

    inheritance_info_str += "*/\n"
    
def get_generator_input(Mode, match_info_list, Setup):
    """The module 'quex.core_engine.generator.core' produces the code for the 
       state machine. However, it requires a certain data format. This function
       adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    # (*) sort the patterns:
    #
    #     -- The order of the patterns determine the sequence of the creation of the 
    #        state machines for the patterns.
    #     -- The sequence of the state machines determines the state machine ids. Patterns
    #        that are created earlier have a 'smaller' state machine id than patterns 
    #        that are created later. 
    #     -- The state machine id stands for the 'privilidge' of a pattern. A pattern
    #        with a lower state machine id has a higher priviledge than a pattern with
    #        a higher id. The state machine id is used for **sorting** during code
    #        generation.
    #
    #   A mode potentially accumulates inherited patterns from base modes.
    #   => At this place all patterns are sorted according to their inheritance 
    #      level. Thus, a propper priviledge handling is guaranteed.
    def pattern_precedence(A, B):
        tmp = - cmp(A.inheritance_level, B.inheritance_level)
        if tmp != 0: return tmp
        else:        return cmp(A.pattern_index, B.pattern_index)
        
    match_info_list.sort(pattern_precedence)

    inheritance_info_str     = ""
    pattern_action_pair_list = []
    for pattern_info in match_info_list:

        pattern               = pattern_info.pattern
        safe_pattern_str      = pattern_info.pattern.replace("\"", "\\\"")
        pattern_state_machine = pattern_info.pattern_state_machine

        if len(pattern_state_machine.get_origin_ids_of_acceptance_states()) == 0:
            error_msg("pattern '%s' is not a valid regular expression. " % pattern, 
                      pattern_info.filename, pattern_info.line_n)
        
        # counting the columns,
        # counting the newlines: here one might have analysis about the pattern
        #                        preceeding and only doing the check if the pattern
        #                        potentially contains newlines.
        action = action_code_formatter.do(Mode, pattern_info.action, Setup, safe_pattern_str,
                                          pattern_state_machine)

        
        action_info = generator.ActionInfo(pattern_state_machine, action)

        pattern_action_pair_list.append(action_info)

        try:
            inheritance_info_str += "** %2i %2i %s\n" % (pattern_info.inheritance_level, 
                                                         pattern_info.pattern_index,
                                                         safe_pattern_str)
        except:    
            error_msg("pattern_info object =\n  " + repr(pattern_info).replace("\n", "\n  "), 
                      "assert", 
                      "get_generator_input()")

    
    return inheritance_info_str, pattern_action_pair_list

