from copy import copy
import os
import sys

from   quex.engine.misc.file_in import error_msg, write_safely_and_close, open_file_or_die

from   quex.input.setup                         import setup as Setup
import quex.output.cpp.source_package           as source_package
import quex.blackboard                          as blackboard

import quex.engine.generator.state_coder.indentation_counter as indentation_counter
from   quex.engine.generator.action_info   import PatternActionInfo, \
                                                  UserCodeFragment_straighten_open_line_pragmas, \
                                                  CodeFragment
#
import quex.input.files.core                    as quex_file_parser
#
import quex.output.cpp.core                     as cpp_generator
import quex.output.cpp.token_id_maker           as token_id_maker
import quex.output.cpp.token_class_maker        as token_class_maker
import quex.output.cpp.analyzer_class           as analyzer_class
import quex.output.cpp.action_code_formatter    as action_code_formatter
import quex.output.cpp.codec_converter_helper   as codec_converter_helper 
import quex.output.cpp.mode_classes             as mode_classes

import quex.output.graphviz.core                as grapviz_generator

def do():
    """Generates state machines for all modes. Each mode results into 
       a separate state machine that is stuck into a virtual function
       of a class derived from class 'quex_mode'.
    """
    token_id_maker.prepare_default_standard_token_ids()

    mode_db = __get_mode_db(Setup)

    IndentationSupportF = blackboard.requires_indentation_count(mode_db)
    BeginOfLineSupportF = blackboard.requires_begin_of_line_condition_support(mode_db)

    # (*) Implement the 'quex' core class from a template
    # -- do the coding of the class framework
    header_engine_txt,           \
    constructor_and_memento_txt, \
    header_configuration_txt     = analyzer_class.do(mode_db, IndentationSupportF, 
                                                     BeginOfLineSupportF)

    mode_implementation_txt  = mode_classes.do(mode_db)

    # (*) Generate the token ids
    #     (This needs to happen after the parsing of mode_db, since during that
    #      the token_id_db is developped.)
    token_id_maker.do(Setup, IndentationSupportF) 
    map_id_to_name_function_implementation_txt = token_id_maker.do_map_id_to_name_function()

    # (*) [Optional] Make a customized token class
    token_class_h, token_class_txt = token_class_maker.do()
    
    # (*) [Optional] Generate a converter helper
    codec_converter_helper.do()

    # (*) implement the lexer mode-specific analyser functions
    inheritance_info_str = ""
    analyzer_code        = ""

    # (*) Get list of modes that are actually implemented
    #     (abstract modes only serve as common base)
    mode_list      = filter(lambda mode: mode.options["inheritable"] != "only", mode_db.values())
    mode_name_list = map(lambda mode: mode.name, mode_list)

    for mode in mode_list:        
        code = get_code_for_mode(mode, mode_name_list, IndentationSupportF, BeginOfLineSupportF) 
        analyzer_code += "".join(code)

        if Setup.comment_mode_patterns_f:
            inheritance_info_str += mode.get_documentation()

    # Bring the info about the patterns first
    if Setup.comment_mode_patterns_f:
        analyzer_code += Setup.language_db["$ml-comment"]("BEGIN: MODE PATTERNS\n" + \
                                                          inheritance_info_str     + \
                                                          "\nEND: MODE PATTERNS")
        analyzer_code += "\n" # For safety: New content may have to start in a newline, e.g. "#ifdef ..."

    # generate frame for analyser code
    analyzer_code = cpp_generator.frame_this(analyzer_code)

    # Implementation (Potential Inline Functions)
    implemtation_txt =   constructor_and_memento_txt + "\n" \
                       + token_class_txt             + "\n" 

    # Engine (Source Code)
    source_txt =   mode_implementation_txt                    + "\n" \
                 + analyzer_code                              + "\n" \
                 + map_id_to_name_function_implementation_txt + "\n" 

    # (*) Write Files
    write_safely_and_close(Setup.output_configuration_file, header_configuration_txt)
    if Setup.language == "C":
        write_safely_and_close(Setup.output_header_file, header_engine_txt)
        write_safely_and_close(Setup.output_code_file, 
                               source_txt + implemtation_txt)
    else:
        header_txt = header_engine_txt.replace("$$ADDITIONAL_HEADER_CONTENT$$", implemtation_txt)
        write_safely_and_close(Setup.output_header_file, header_txt)
        write_safely_and_close(Setup.output_code_file, source_txt)

    if token_class_h != "":
        write_safely_and_close(blackboard.token_type_definition.get_file_name(), 
                               token_class_h)

    UserCodeFragment_straighten_open_line_pragmas(Setup.output_header_file, "C")
    UserCodeFragment_straighten_open_line_pragmas(Setup.output_code_file, "C")

    # assert blackboard.token_type_definition is not None
    UserCodeFragment_straighten_open_line_pragmas(blackboard.token_type_definition.get_file_name(), "C")

    if Setup.source_package_directory != "":
        source_package.do()

def __prepare_end_of_stream_action(Mode, IndentationSupportF):
    if not Mode.has_code_fragment_list("on_end_of_stream"):
        # We cannot make any assumptions about the token class, i.e. whether
        # it can take a lexeme or not. Thus, no passing of lexeme here.
        txt  = "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
        txt += "RETURN;\n"

        Mode.set_code_fragment_list("on_end_of_stream", CodeFragment(txt))

    if IndentationSupportF:
        if Mode.default_indentation_handler_sufficient():
            code = "QUEX_NAME(on_indentation)(me, /*Indentation*/0, LexemeNull);\n"
        else:
            code = "QUEX_NAME(%s_on_indentation)(me, /*Indentation*/0, LexemeNull);\n" % Mode.name

        code_fragment = CodeFragment(code)
        Mode.insert_code_fragment_at_front("on_end_of_stream", code_fragment)

    # RETURNS: end_of_stream_action, db 
    return action_code_formatter.do(Mode, Mode.get_code_fragment_list("on_end_of_stream"), 
                                    None, EOF_ActionF=True)

def __prepare_on_failure_action(Mode):
    if not Mode.has_code_fragment_list("on_failure"):
        txt  = "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % Mode.name 
        txt += "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
        txt += "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
        Mode.set_code_fragment_list("on_failure", CodeFragment(txt))

    # RETURNS: on_failure_action, db 
    return action_code_formatter.do(Mode, Mode.get_code_fragment_list("on_failure"), 
                                    None, Default_ActionF=True) 

def get_code_for_mode(Mode, ModeNameList, IndentationSupportF, BeginOfLineSupportF):
    required_local_variables_db = {}
   
    # -- some modes only define event handlers that are inherited
    if len(Mode.get_pattern_action_pair_list()) == 0: return []

    # -- 'end of stream' action
    end_of_stream_action, db = __prepare_end_of_stream_action(Mode, IndentationSupportF)
    required_local_variables_db.update(db)

    # -- 'on failure' action (on the event that nothing matched)
    on_failure_action, db = __prepare_on_failure_action(Mode)
    required_local_variables_db.update(db)

    # -- adapt pattern-action pair information so that it can be treated
    #    by the code generator.
    pattern_action_pair_list, db = prepare_pattern_actions(Mode, IndentationSupportF)
    required_local_variables_db.update(db)

    generator = cpp_generator.Generator(PatternActionPair_List = pattern_action_pair_list, 
                                        StateMachineName       = Mode.name,
                                        AnalyserStateClassName = Setup.analyzer_class_name,
                                        OnFailureAction        = PatternActionInfo(None, on_failure_action), 
                                        EndOfStreamAction      = PatternActionInfo(None, end_of_stream_action),
                                        ModeNameList           = ModeNameList,
                                        StandAloneAnalyserF    = False, 
                                        SupportBeginOfLineF    = BeginOfLineSupportF)

    return generator.do(required_local_variables_db)

def __get_indentation_counter_terminal_index(PatterActionPairList):
    """Under some circumstances a terminal code need to jump to the indentation
       counter directly. Thus, it must be known in what terminal it is actually 
       located.

        RETURNS: None, if no indentation counter is involved.
                 > 0,  terminal id of the terminal that contains the indentation
                       counter.
    """
    for info in PatterActionPairList:
        action = info.action()
        if   action.__class__.__name__ != "GeneratedCode": continue
        elif action.function != indentation_counter.do:    continue
        return info.pattern_state_machine().get_id()
    return None

def prepare_pattern_actions(Mode, IndentationSupportF):
    """The module 'quex.output.cpp.core' produces the code for the 
       state machine. However, it requires a certain data format. This function
       adapts the mode information to this format. Additional code is added 

       -- for counting newlines and column numbers. This happens inside
          the function ACTION_ENTRY().
       -- (optional) for a virtual function call 'on_action_entry()'.
       -- (optional) for debug output that tells the line number and column number.
    """
    assert Mode.__class__.__name__ == "Mode"
    variable_db              = {}
    pattern_action_pair_list = Mode.get_pattern_action_pair_list()

    indentation_counter_terminal_id = __get_indentation_counter_terminal_index(pattern_action_pair_list)

    # Assume pattern-action pairs (matches) are sorted and their pattern state
    # machine ids reflect the sequence of pattern precedence.

    for pattern_info in pattern_action_pair_list:

        # Prepare the action code for the analyzer engine. For this purpose several things
        # are be added to the user's code.
        action                = pattern_info.action()
        pattern_state_machine = pattern_info.pattern_state_machine()

        # Generated code fragments may rely on some information about the generator
        if hasattr(action, "data") and type(action.data) == dict:   
            action.data["indentation_counter_terminal_id"] = indentation_counter_terminal_id

        prepared_action, db = action_code_formatter.do(Mode, action, 
                                                       pattern_state_machine, 
                                                       SelfCountingActionF=False)
        variable_db.update(db)

        pattern_info.set_action(prepared_action)
    
    return pattern_action_pair_list, variable_db

def do_plot():

    mode_db             = __get_mode_db(Setup)
    IndentationSupportF = blackboard.requires_indentation_count(mode_db)

    for mode in mode_db.values():        
        # -- some modes only define event handlers that are inherited
        pattern_action_pair_list = mode.get_pattern_action_pair_list()
        if len(pattern_action_pair_list) == 0: continue

        plotter = grapviz_generator.Generator(pattern_action_pair_list,
                                              StateMachineName = mode.name,
                                              GraphicFormat    = Setup.plot_graphic_format)
        plotter.do(Option=Setup.plot_character_display)

def __get_mode_db(Setup):
    # (0) check basic assumptions
    if len(Setup.input_mode_files) == 0: error_msg("No input files.")
    
    # (1) input: do the pattern analysis, in case exact counting of newlines is required
    #            (this might speed up the lexer, but nobody might care ...)
    #            pattern_db = analyse_patterns.do(pattern_file)    
    quex_file_parser.do(Setup.input_mode_files)

    return blackboard.mode_db

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

