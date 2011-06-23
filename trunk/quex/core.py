from copy import copy
import os
import sys

from   quex.engine.misc.file_in import error_msg, write_safely_and_close, open_file_or_die

from   quex.input.setup                         import setup as Setup
import quex.output.cpp.source_package           as source_package
import quex.blackboard                          as blackboard

from   quex.engine.generator.action_info   import UserCodeFragment_straighten_open_line_pragmas, \
                                                  CodeFragment
#
import quex.input.files.core                    as quex_file_parser
#
import quex.output.cpp.core                     as cpp_generator
import quex.output.cpp.token_id_maker           as token_id_maker
import quex.output.cpp.token_class_maker        as token_class_maker
import quex.output.cpp.analyzer_class           as analyzer_class
import quex.output.cpp.mode_classes             as mode_classes
import quex.output.cpp.action_preparation       as action_preparation
import quex.output.cpp.codec_converter_helper   as codec_converter_helper 

import quex.output.graphviz.core                as grapviz_generator

def do():
    """Generates state machines for all modes. Each mode results into 
       a separate state machine that is stuck into a virtual function
       of a class derived from class 'quex_mode'.
    """
    token_id_maker.prepare_default_standard_token_ids()

    mode_db = quex_file_parser.do(Setup.input_mode_files)

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
        # -- some modes only define event handlers that are inherited
        if len(mode.get_pattern_action_pair_list()) == 0: return []

        # -- prepare the source code fragments for the generator
        required_local_variables_db, \
        pattern_action_pair_list,    \
        end_of_stream_action,        \
        on_failure_action            = action_preparation.do(mode, IndentationSupportF)

        # -- prepare code generation
        generator = cpp_generator.Generator(PatternActionPair_List = pattern_action_pair_list, 
                                            StateMachineName       = mode.name,
                                            AnalyserStateClassName = Setup.analyzer_class_name,
                                            OnFailureAction        = on_failure_action, 
                                            EndOfStreamAction      = end_of_stream_action,
                                            ModeNameList           = mode_name_list,
                                            StandAloneAnalyserF    = False, 
                                            SupportBeginOfLineF    = BeginOfLineSupportF)

        # -- generate!
        analyzer_code += "".join(generator.do(required_local_variables_db))

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

def do_plot():
    mode_db             = quex_file_parser.do(Setup.input_mode_files)
    IndentationSupportF = blackboard.requires_indentation_count(mode_db)

    for mode in mode_db.values():        
        # -- some modes only define event handlers that are inherited
        pattern_action_pair_list = mode.get_pattern_action_pair_list()
        if len(pattern_action_pair_list) == 0: continue

        plotter = grapviz_generator.Generator(pattern_action_pair_list,
                                              StateMachineName = mode.name,
                                              GraphicFormat    = Setup.plot_graphic_format)
        plotter.do(Option=Setup.plot_character_display)

def _exception_checker():
    """Allow to check wether the exception handlers are all in place.
    """
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

