import sys

from   quex.engine.misc.file_in                 import write_safely_and_close

from   quex.blackboard                          import setup as Setup
import quex.output.cpp.source_package           as source_package
import quex.blackboard                          as blackboard

from   quex.engine.generator.action_info        import UserCodeFragment_straighten_open_line_pragmas
#
import quex.input.files.core                    as quex_file_parser
#
import quex.output.cpp.core                     as cpp_generator
import quex.output.cpp.token_id_maker           as token_id_maker
import quex.output.cpp.token_class_maker        as token_class_maker
import quex.output.cpp.analyzer_class           as analyzer_class
import quex.output.cpp.configuration            as configuration 
import quex.output.cpp.mode_classes             as mode_classes
import quex.output.cpp.action_preparation       as action_preparation
import quex.output.cpp.codec_converter_helper   as codec_converter_helper 

import quex.output.graphviz.core                as grapviz_generator

def do():
    """Generates state machines for all modes. Each mode results into 
       a separate state machine that is stuck into a virtual function
       of a class derived from class 'quex_mode'.
    """
    if Setup.language == "DOT": 
        return do_plot()

    mode_db = quex_file_parser.do(Setup.input_mode_files)

    # (*) Implement the 'quex' core class from a template
    # -- do the coding of the class framework
    analyzer_class_header,                     \
    analyzer_class_constructor_and_memento_txt = analyzer_class.do(mode_db)
    mode_implementation_txt = mode_classes.do(mode_db)
    configuration_txt       = configuration.do(mode_db) 

    # (*) Generate the token ids
    #     (This needs to happen after the parsing of mode_db, since during that
    #      the token_id_db is developed.)
    token_id_maker.do(Setup) 
    map_id_to_name_function_implementation_txt = token_id_maker.do_map_id_to_name_function()

    # (*) [Optional] Make a customized token class
    token_class_h, token_class_txt = token_class_maker.do()
    
    # (*) [Optional] Generate a converter helper
    codec_converter_helper.do()

    # (*) implement the lexer mode-specific analyser functions
    analyzer_functions_txt = analyzer_functions_get(mode_db)

    # Implementation (Potential Inline Functions)
    implemtation_txt =   analyzer_class_constructor_and_memento_txt + "\n" \
                       + token_class_txt             + "\n" 

    # Engine (Source Code)
    source_txt =   mode_implementation_txt                    + "\n" \
                 + analyzer_functions_txt                     + "\n" \
                 + map_id_to_name_function_implementation_txt + "\n" 

    # (*) Write Files
    write_safely_and_close(Setup.output_configuration_file, configuration_txt)
    if Setup.language == "C":
        write_safely_and_close(Setup.output_header_file, analyzer_class_header)
        write_safely_and_close(Setup.output_code_file, 
                               source_txt + implemtation_txt)
    else:
        header_txt = analyzer_class_header.replace("$$ADDITIONAL_HEADER_CONTENT$$", implemtation_txt)
        write_safely_and_close(Setup.output_header_file, header_txt)
        write_safely_and_close(Setup.output_code_file, source_txt)

    if token_class_h != "":
        write_safely_and_close(blackboard.token_type_definition.get_file_name(), 
                               token_class_h)

    for file_name in [Setup.output_header_file, 
                      Setup.output_code_file, 
                      blackboard.token_type_definition.get_file_name()]:
        UserCodeFragment_straighten_open_line_pragmas(file_name, "C")

    if Setup.source_package_directory != "":
        source_package.do()

def analyzer_functions_get(ModeDB):
    IndentationSupportF = blackboard.requires_indentation_count(ModeDB)
    BeginOfLineSupportF = blackboard.requires_begin_of_line_condition_support(ModeDB)

    inheritance_info_str = ""
    analyzer_code        = ""

    # (*) Get list of modes that are actually implemented
    #     (abstract modes only serve as common base)
    mode_list      = [ mode for mode in ModeDB.itervalues() 
                       if mode.options["inheritable"] != "only" ]
    mode_name_list = [ mode.name for mode in mode_list ] 

    for mode in mode_list:        
        # -- some modes only define event handlers that are inherited
        if len(mode.get_pattern_action_pair_list()) == 0: continue

        # -- prepare the source code fragments for the generator
        required_local_variables_db, \
        pattern_action_pair_list,    \
        end_of_stream_action,        \
        on_failure_action            = action_preparation.do(mode, IndentationSupportF)

        # -- prepare code generation
        generator = cpp_generator.Generator(StateMachineName       = mode.name,
                                            PatternActionPair_List = pattern_action_pair_list, 
                                            OnFailureAction        = on_failure_action, 
                                            EndOfStreamAction      = end_of_stream_action,
                                            ModeNameList           = mode_name_list,
                                            SupportBeginOfLineF    = BeginOfLineSupportF)

        # -- generate!
        analyzer_code += "".join(generator.do(required_local_variables_db))

        if Setup.comment_mode_patterns_f:
            inheritance_info_str += mode.get_documentation()

    # Bring the info about the patterns first
    if Setup.comment_mode_patterns_f:
        comment = []
        Setup.language_db.ML_COMMENT(comment, 
                                     "BEGIN: MODE PATTERNS\n" + \
                                     inheritance_info_str     + \
                                     "\nEND: MODE PATTERNS")
        comment.append("\n") # For safety: New content may have to start in a newline, e.g. "#ifdef ..."
        analyzer_code += "".join(comment)

    # generate frame for analyser code
    return cpp_generator.frame_this(analyzer_code)

def do_plot():
    mode_db = quex_file_parser.do(Setup.input_mode_files)

    for mode in mode_db.values():        
        # -- some modes only define event handlers that are inherited
        pattern_action_pair_list = mode.get_pattern_action_pair_list()
        if len(pattern_action_pair_list) == 0: continue

        plotter = grapviz_generator.Generator(pattern_action_pair_list,
                                              StateMachineName = mode.name)
        plotter.do(Option=Setup.character_display)

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

