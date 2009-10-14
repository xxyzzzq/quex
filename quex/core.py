from copy import copy
import os
import sys

from   quex.frs_py.file_in import error_msg, write_safely_and_close

from   quex.input.setup import setup as Setup
import quex.lexer_mode                          as lexer_mode

import quex.consistency_check                   as consistency_check
import quex.core_engine.generator.core          as     generator
from   quex.core_engine.generator.action_info   import PatternActionInfo, \
                                                       UserCodeFragment_straighten_open_line_pragmas, \
                                                       CodeFragment
import quex.input.quex_file_parser              as quex_file_parser
from   quex.output.cpp.token_id_maker           import TokenInfo
import quex.output.cpp.core                     as quex_class_out
import quex.output.cpp.token_id_maker           as token_id_maker
import quex.output.cpp.action_code_formatter    as action_code_formatter
import quex.output.cpp.token_class_maker        as token_class_maker
import quex.output.cpp.codec_converter_helper   as codec_converter_helper 
import quex.output.graphviz.interface           as plot_generator

def do():
    """Generates state machines for all modes. Each mode results into 
       a separate state machine that is stuck into a virtual function
       of a class derived from class 'quex_mode'.
    """
    # NOTE: The generated header file that contains the lexical analyser class includes
    #       the file "code_base/code_base/definitions-quex-buffer.h". But the analyser
    #       functions also need 'connection' to the lexer class, so we include the header
    #       of the generated lexical analyser at this place.
    lexer_mode.token_id_db["TERMINATION"]   = TokenInfo("TERMINATION",   ID=Setup.token_id_termination)
    lexer_mode.token_id_db["UNINITIALIZED"] = TokenInfo("UNINITIALIZED", ID=Setup.token_id_uninitialized)

    mode_db = __get_mode_db(Setup)

    # (*) Get list of modes that are actually implemented
    #     (abstract modes only serve as common base)
    mode_list      = filter(lambda mode: mode.options["inheritable"] != "only", mode_db.values())
    mode_name_list = map(lambda mode: mode.name, mode_list)

    # (*) Implement the 'quex' core class from a template
    # -- do the coding of the class framework
    IndentationSupportF = __requires_indentation_count(mode_db)
    quex_class_out.do(mode_db, IndentationSupportF)

    # (*) Generate the token ids
    token_id_maker.do(Setup) 

    # (*) [Optional] Make a customized token class
    token_class_maker.do()
    
    # (*) [Optional] Generate a converter helper
    codec_converter_helper.do()

    # (*) implement the lexer mode-specific analyser functions
    inheritance_info_str = ""
    analyzer_code        = ""
    for mode in mode_list:        
        # accumulate inheritance information for comment
        analyzer_code        += get_code_for_mode(mode, mode_name_list, IndentationSupportF) 
        inheritance_info_str += mode.get_documentation()
        
    # find unused labels
    analyzer_code = generator.delete_unused_labels(analyzer_code)

    # generate frame for analyser code
    analyzer_code = generator.frame_this(analyzer_code)

    # Bring the info about the patterns first
    analyzer_code = Setup.language_db["$ml-comment"](inheritance_info_str) + "\n" + analyzer_code

    # write code to a header file
    write_safely_and_close(Setup.output_core_engine_file, analyzer_code)

    UserCodeFragment_straighten_open_line_pragmas(Setup.output_file_stem, "C")
    UserCodeFragment_straighten_open_line_pragmas(Setup.output_core_engine_file, "C")
    UserCodeFragment_straighten_open_line_pragmas(Setup.output_code_file, "C")
    if type(lexer_mode.token_type_definition) != dict:
        UserCodeFragment_straighten_open_line_pragmas(lexer_mode.get_token_class_file_name(Setup), "C")

def get_code_for_mode(Mode, ModeNameList, IndentationSupportF):

    # -- some modes only define event handlers that are inherited
    if len(Mode.get_pattern_action_pair_list()) == 0: return "", ""

    # -- 'end of stream' action
    if not Mode.has_code_fragment_list("on_end_of_stream"):
        txt  = "self.send(%sTERMINATION);\n" % Setup.token_id_prefix 
        txt += "return;\n"
        Mode.set_code_fragment_list("on_end_of_stream", CodeFragment(txt))

    end_of_stream_action = action_code_formatter.do(Mode, 
                                                    Mode.get_code_fragment_list("on_end_of_stream"), 
                                                    "on_end_of_stream", None, EOF_ActionF=True, 
                                                    IndentationSupportF=IndentationSupportF)
    # -- 'on failure' action (nothing matched)
    if not Mode.has_code_fragment_list("on_failure"):
        txt  = "self.send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
        txt += "return;\n"
        Mode.set_code_fragment_list("on_failure", CodeFragment(txt))

    on_failure_action = action_code_formatter.do(Mode, 
                                              Mode.get_code_fragment_list("on_failure"), 
                                              "on_failure", None, Default_ActionF=True, 
                                              IndentationSupportF=IndentationSupportF)

    # -- adapt pattern-action pair information so that it can be treated
    #    by the code generator.
    pattern_action_pair_list = get_generator_input(Mode, IndentationSupportF)

    analyzer_code = generator.do(pattern_action_pair_list, 
                                 OnFailureAction                = PatternActionInfo(None, on_failure_action), 
                                 EndOfStreamAction              = PatternActionInfo(None, end_of_stream_action),
                                 PrintStateMachineF             = True,
                                 StateMachineName               = Mode.name,
                                 AnalyserStateClassName         = Setup.analyzer_class_name,
                                 StandAloneAnalyserF            = False, 
                                 QuexEngineHeaderDefinitionFile = Setup.output_file_stem,
                                 ModeNameList                   = ModeNameList)

    return analyzer_code
    
def get_generator_input(Mode, IndentationSupportF):
    """The module 'quex.core_engine.generator.core' produces the code for the 
       state machine. However, it requires a certain data format. This function
       adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    assert isinstance(Mode, lexer_mode.Mode)
    pattern_action_pair_list = Mode.get_pattern_action_pair_list()
    # Assume pattern-action pairs (matches) are sorted and their pattern state
    # machine ids reflect the sequence of pattern precedence.

    ## prepared_pattern_action_pair_list = []

    for pattern_info in pattern_action_pair_list:
        safe_pattern_str      = pattern_info.pattern.replace("\"", "\\\"")
        pattern_state_machine = pattern_info.pattern_state_machine()

        # Prepare the action code for the analyzer engine. For this purpose several things
        # are be added to the user's code.
        prepared_action = action_code_formatter.do(Mode, pattern_info.action(), safe_pattern_str,
                                                   pattern_state_machine,
                                                   IndentationSupportF=IndentationSupportF)

        pattern_info.set_action(prepared_action)

        ## prepared_pattern_action_pair_list.append(action_info)
    
    return pattern_action_pair_list

def __get_post_context_n(match_info_list):
    n = 0
    for info in MatchInfoList:
        if info.pattern_state_machine().core().post_context_id() != -1L:
            n += 1
    return n

def do_plot():

    mode_db = __get_mode_db(Setup)
    IndentationSupportF = __requires_indentation_count(mode_db)

    for mode in mode_db.values():        
        # -- some modes only define event handlers that are inherited
        if len(mode.get_pattern_action_pair_list()) == 0: continue

        # -- adapt pattern-action pair information so that it can be treated
        #    by the code generator.
        pattern_action_pair_list = get_generator_input(mode, IndentationSupportF)

        plotter = plot_generator.Generator(pattern_action_pair_list, 
                                           StateMachineName = mode.name,
                                           GraphicFormat    = Setup.plot_graphic_format)
        plotter.do(Option=Setup.plot_character_display)

def __get_mode_db(Setup):
    # (0) check basic assumptions
    if Setup.input_mode_files == []: error_msg("No input files.")
    
    # (1) input: do the pattern analysis, in case exact counting of newlines is required
    #            (this might speed up the lexer, but nobody might care ...)
    #            pattern_db = analyse_patterns.do(pattern_file)    
    mode_description_db = quex_file_parser.do(Setup.input_mode_files)

    # (*) Translate each mode description int a 'real' mode
    for mode_name, mode_descr in mode_description_db.items():
        lexer_mode.mode_db[mode_name] = lexer_mode.Mode(mode_descr)

    # (*) perform consistency check 
    consistency_check.do(lexer_mode.mode_db)

    return lexer_mode.mode_db


def __requires_indentation_count(ModeDB):
    """Determine whether the lexical analyser needs indentation counting
       support. if one mode has an indentation handler, than indentation
       support must be provided.                                         
    """
    for mode in ModeDB.values():
        if mode.has_code_fragment_list("on_indentation"):
            return True
    return False

#########################################################################################
# Allow to check wether the exception handlers are all in place
def _exception_checker():
    if       len(sys.argv) != 3: return
    elif     sys.argv[1] != "<<TEST:Exceptions/function>>" \
         and sys.argv[1] != "<<TEST:Exceptions/on-import>>":   return

    exception = sys.argv[2]
    if   exception == "KeyboardInterrupt": raise KeyboardInterrupt()
    elif exception == "AssertionError":    raise AssertionError()
    elif exception == "Exception":         raise Exception()

# Double check wether exception handlers are in place:
if len(sys.argv) == 3 and sys.argv[1] == "<<TEST:Exceptions/on-import>>":
    _exception_checker()

