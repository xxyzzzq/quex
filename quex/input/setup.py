#! /usr/bin/env python
from quex.core_engine.generator.languages.core import db as quex_core_engine_generator_languages_db
class something:
    pass


LIST         = -1111
FLAG         = -2222
NEGATED_FLAG = -3333

SETUP_INFO = {         
    # [Name in Setup]                 [ Flags ]                                [Default / Type]
    "_debug_exception_f":             [["--debug-exception"],                  FLAG], 
    "analyzer_class_name":            [["-o", "--engine", "--analyzer-class"], "quex::lexer"],    
    "analyzer_derived_class_file":    [["--derived-class-file"],               ""],
    "analyzer_derived_class_name":    [["--derived-class", "--dc"],            ""],
    "buffer_codec":                   [["--codec"],                            ""],
    "buffer_limit_code":              [["--buffer-limit"],                     0x0],
    "buffer_element_size":            [["--bytes-per-trigger", "-b"],          -1],
    "buffer_element_type":            [["--engine-character-type", "--ect"],   ""],
    "buffer_based_analyzis_f":        [["--buffer-based", "--bb"],             FLAG],
    "buffer_byte_order":              [["--endian"],                           "<system>"],
    "compression_template_f":         [["--template-compression"],             FLAG],
    "compression_template_coef":      [["--template-compression-coefficient"], 1.0],
    "compression_path_f":             [["--path-compression"],                 FLAG],
    "compression_path_uniform_f":     [["--path-compression-uniform"],         FLAG],
    "count_column_number_f":          [["--no-count-lines"],                   NEGATED_FLAG],
    "count_line_number_f":            [["--no-count-columns"],                 NEGATED_FLAG],
    "path_limit_code":                [["--path-termination"],                 0x1],
    "dos_carriage_return_newline_f":  [["--no-DOS"],                           NEGATED_FLAG],
    "string_accumulator_f":           [["--no-string-accumulator", "--nsacc"], NEGATED_FLAG],
    "converter_iconv_f":              [["--iconv"],                            FLAG],
    "converter_icu_f":                [["--icu"],                              FLAG],
    "converter_user_new_func":        [["--converter-new", "--cn"],            ""],
    "converter_ucs_coding_name":      [["--converter-ucs-coding-name", "--cucn"], ""],
    "include_stack_support_f":        [["--no-include-stack", "--nois"],       NEGATED_FLAG],
    "input_mode_files":               [["-i", "--mode-files"],                 LIST],
    "token_class_file":               [["--token-class-file"],                 ""],
    "token_class_name":               [["--token-class", "--tc"],              ""],
    "token_class_take_text_check_f":  [["--token-type-no-take_text-check",     "--ttnttc"], NEGATED_FLAG], 
    "token_id_foreign_definition_file":  [["--foreign-token-id-file"],         ""],  
    "token_id_counter_offset":        [["--token-id-offset"],                  "10000"],
    "token_id_type":                  [["--token-id-type"],                  "uint32_t"],
    "token_id_prefix":                [["--token-prefix"],                   "QUEX_TKN_"],
    "token_queue_size":               [["--token-queue-size"],               "64"],
    "token_queue_safety_border":      [["--token-queue-safety-border"],      "16"],
    "token_policy":                   [["--token-policy", "--tp"],           "queue"],                
    "token_memory_management_by_user_f": [["--token-memory-management-by-user", "--tmmbu"], FLAG],
    "mode_transition_check_f":        [["--no-mode-transition-check"],       NEGATED_FLAG],
    "language":                       [["--language", "-l"],                 "C++"],
    "output_debug_f":                 [["--debug"],                          FLAG],
    "output_file_naming_scheme":      [["--file-extension-scheme", "--fes"],  ""],
    "post_categorizer_f":             [["--post-categorizer"],               FLAG],
    "output_directory":               [["--output-directory", "--odir"],     ""],
    "plot_graphic_format":            [["--plot"],                           ""],
    "plot_character_display":         [["--plot-character-display", "--pcd"],  "utf8"],
    "plot_graphic_format_list_f":     [["--plot-format-list"],               FLAG],
    "user_application_version_id":    [["--version-id"],                     "0.0.0-pre-release"],
    #
    "version_information":               [["--version", "-v"],                FLAG],
    "help":                              [["--help", "-h"],                   FLAG],
    "warning_disabled_no_token_queue_f": [["--no-warning-on-no-token-queue"], FLAG],
    # Parameters not set on the command line:
    "byte_order_is_that_of_current_system_f":    True,
    "analyzer_name_space":                       None,
    "analyzer_name_safe":                        None,
    "analyzer_derived_class_name_space":         None,
    "analyzer_derived_class_name_safe":          None,
    "token_class_name_space":                    None,
    "token_class_name_safe":                     None,
    "token_id_prefix_name_space":                None,
    "token_id_prefix_plain":                     None,   # i.e. without the namespace specified.
    "output_buffer_codec_header_file": None,
    "output_header_file":                           None,
    "output_configuration_file":                    None,
    "output_code_file":                             None,
    "output_token_id_file":                         None,
    "output_token_class_file_implementation":       None,
    "output_token_class_file":                      None,
    "language_db":                                  None,
    "extension_db":                                 None,
    #______________________________________________________________________________________________________
    "XX_begin_of_stream_code":           [["--begin-of-stream"],       "0x19"],                  # DEPRECATED
    "XX_buffer_element_size":       [["--bytes-per-ucs-code-point"], "1"],                  # DEPRECATED
    "XX_end_of_stream_code":             [["--end-of-stream"],         "0x1A"],                  # DEPRECATED
    "XX_flex_engine_f":                  [["--flex-engine"],           FLAG],                    # DEPRECATED
    "XX_input_pattern_file":             [["-p", "--pattern-file"],    ""],                      # DEPRECATED 
    "XX_input_token_id_db":              [["-t", "--token-id-db"],     LIST],                    # DEPRECATED
    "XX_leave_temporary_files_f":        [["--leave-tmp-files"],       FLAG],                    # DEPRECATED
    "XX_plain_memory_f":                 [["--plain-memory"],          FLAG],                    # DEPRECATED
    "XX_std_istream_support_f":          [["--istream-support"],       FLAG],                    # DEPRECATED
    "XX_yywrap_is_ok_f":                 [["--yywrap-is-ok"],          FLAG],                    # DEPRECATED
    "XX_input_token_sending_via_queue_f":[["--token-queue"],           FLAG],                    # DEPRECATED
    "XX_string_accumulator_f":           [["--string-accumulator", "--sacc"],   FLAG],           # DEPRECATED
    "XX_disable_token_queue_f":          [["--no-token-queue", "--ntq"],        FLAG],           # DEPRECATED     
    "XX_disable_return_token_id_f":      [["--no-return-token-id"],             FLAG],           # DEPRECATED
    "XX_input_lexer_class_friends":      [["--friend-class"],                   LIST],           # DEPRECATED
    "XX_token_class_name":               [["--token-class-name"],               ""],             # DEPRECATED
    "XX_token_class_stringless_check_f": [["--token-type-no-stringless-check",  "--ttnsc"], NEGATED_FLAG], # DEPRECATED
    "XX_token_id_counter_offset":        [["--token-offset"],                   "10000"],        # DEPRECATED
    "XX_token_id_termination":           [["--token-id-termination"],           "0"],            # DEPRECATED
    "XX_token_id_uninitialized":         [["--token-id-uninitialized"],         "1"],            # DEPRECATED
    "XX_token_id_indentation_error":     [["--token-id-indentation-error"],     "2"],            # DEPRECATED
}

DEPRECATED = { 
  "XX_input_pattern_file": 
     ("Write a 'pattern { ... }' section inside the mode files instead.\n" + \
      "Syntax of the 'pattern { ... }' section and the previous file syntax\n" + \
      "are backward compatible.", "0.9.x"),        
  "XX_input_token_id_db":
     ("Write a 'token { ... }' section inside the mode files instead.\n" + \
      "Syntax of the 'token { ... }' section and the previous file syntax\n" + \
      "are backward compatible.", "0.9.x"),        
  "XX_yywrap_is_ok_f":
     ("Since the mentioned version, the flex core engine is no longer supported. The\n" + \
      "flag makes only sense for flex core engines.", "0.13.1"),
  "XX_flex_engine_f":
     ("Since the mentioned version, the flex core engine is no longer supported. The\n" + \
      "flag makes only sense for flex core engines.", "0.13.1"),
  "XX_leave_temporary_files_f":
     ("Since the mentioned version, the flex core engine is no longer supported. The\n" + \
      "flag makes only sense for flex core engines.", "0.13.1"),
  "XX_plain_memory_f":                 
     ("Since the mentioned version, quex does no longer need the '--plain-memory' command\n" + \
      "line argument. The engine can be used with plain memory directly. Please, consider\n" + \
      "reading the documentation on this issue.", "0.31.1"),
  "XX_std_istream_support_f":
     ("The lexical analyzer has a flexible interface now, for both C++ istreams and FILE*\n" + \
      "so that rigid setting with this option is superfluous", "0.13.1"),
  "XX_begin_of_stream_code":
     ("Since the mentioned version, there is no need for end of stream and end of stream\n" + \
      "characters anymore. Options '--end-of-stream' and '--begin-of-stream' are no longer\n" + \
      "supported.", "0.25.2"),
  "XX_end_of_stream_code":
     ("Since the mentioned version, there is no need for end of stream and end of stream\n" + \
      "characters anymore. Options '--end-of-stream' and '--begin-of-stream' are no longer\n" + \
      "supported.", "0.25.2"),
  "XX_input_token_sending_via_queue_f":
     ("The token queue was temporarily turned off by default. Since 0.31.5 the token queue is again\n" + \
      "turned on by default, since the lexical analysers can be described much more natural. If you\n" + \
      "want to disable the token queue, please, use '--no-token-queue', or '--ntq'.", "0.31.5"),
  "XX_string_accumulator_f":
     ("The string accumulator was temporarily turned off by default. Since 0.31.5 the it is again\n" + \
      "turned on by default. If you want to disable the token queue, please, use '--no-string-accumulator',\n" + \
      "or '--nsacc'.", "0.31.5"),
  "XX_disable_token_queue_f":
     ("Since version 0.36.5 the flag '--no-token-queue' and '--ntq' have been deprecated.\n" + \
      "Use flag '--token-policy' or '--tp' instead.", "0.36.5"),     
  "XX_disable_return_token_id_f":      
     ("Flag --no-return-token-id is no longer supported. In recent versions of quex\n" + \
      "token-IDs are not passed as return values at all.", "0.37.1"), 
  "XX_input_lexer_class_friends":  
      ("Since version 0.46.3, friend classes are no longer defined on the command line. Please,\n"
       "use the 'body { ... }' section and fill be-'friend'-ing code there.", "0.46.3"),
  "XX_token_class_name":
      ("Command line option '--token-class--name' has been renamed to '--token-class'\n"
       "for uniformity.", "0.46.3"),
  "XX_token_class_stringless_check_f": 
      ("Command line options --token-type-no-stringless-check and --ttnsc are deprecated. Please,\n"
       "use --token-type-no-take_text-check or --ttnttc", 
       "0.48.1"), 
  "XX_buffer_element_size": 
      ("The command line option '--bytes-per-ucs-code-point' has been renamed to\n"
       "'--bytes-per-trigger'. The old name causes heavy confusion when it was\n"
       "used in combination with dynamic length codecs (option --codec).", "0.49.1"),
  "XX_token_id_counter_offset":
      ("The command line option '--token-offset' has been replaced by '--token-id-offset'."
       "0.51.1"),
  "XX_token_id_termination":
      ("Option '--token-id-termination' is no longer supported.\n" \
       "Numeric value for token ids are no longer defined on the command line.\n" \
       "Numeric values for token ids can be defined in token sections, e.g.\n" \
       "    token {\n" \
       "       TERMINATION = 4711;\n"
       "    }", "0.51.1"),
  "XX_token_id_uninitialized":         
      ("Option '--token-id-uninitialized' is no longer supported.\n" \
       "Numeric value for token ids are no longer defined on the command line.\n" \
       "Numeric values for token ids can be defined in token sections, e.g.\n" \
       "    token {\n" \
       "       UNINITIALIZED = 4711;\n"
       "    }", "0.51.1"),
  "XX_token_id_indentation_error":     
      ("Option '--token-id-indentation-error' is no longer supported.\n" \
       "Numeric value for token ids are no longer defined on the command line.\n" \
       "Numeric values for token ids can be defined in token sections, e.g.\n" \
       "    token {\n" \
       "       INDENTATION_ERROR = 4711;\n"
       "    }", "0.51.1"),
}
 
HEADER              = 0
HEADER_IMPLEMTATION = 1
SOURCE              = 2

global_character_type_db = {
        # Name:         Type:         LittleEndian     Big Endian       Bytes per 
        #                             Converter Name:  Converter Name:  engine character:
        "uint8_t":    [ "uint8_t",    "ASCII",         "ASCII",         1],
        "uint16_t":   [ "uint16_t",   "UCS-2LE",       "UCS-2BE",       2],
        "uint32_t":   [ "uint32_t",   "UCS-4LE",       "UCS-4BE",       4],
        "u8":         [ "u8",         "ASCII",         "ASCII",         1],
        "u16":        [ "u16",        "UCS-2LE",       "UCS-2BE",       2],
        "u32":        [ "u32",        "UCS-4LE",       "UCS-4BE",       4],
        "unsigned8":  [ "unsigned8",  "ASCII",         "ASCII",         1],
        "unsigned16": [ "unsigned16", "UCS-2LE",       "UCS-2BE",       2],
        "unsigned32": [ "unsigned32", "UCS-4LE",       "UCS-4BE",       4],
        "wchar_t":    [ "wchar_t",    "WCHAR_T",       "WCHAR_T",       -1],
}

global_extension_db = {
    "C++": {
        "": { 
              SOURCE:              ".cpp",
              HEADER:              "",
              HEADER_IMPLEMTATION: ".i",
        },
        "++": { 
              SOURCE:              ".c++",
              HEADER:              ".h++",
              HEADER_IMPLEMTATION: ".h++",
        },
        "pp": { 
              SOURCE:              ".cpp",
              HEADER:              ".hpp",
              HEADER_IMPLEMTATION: ".hpp",
        },
        "cc": { 
              SOURCE:              ".cc",
              HEADER:              ".hh",
              HEADER_IMPLEMTATION: ".hh",
        },
        "xx": { 
              SOURCE:              ".cxx",
              HEADER:              ".hxx",
              HEADER_IMPLEMTATION: ".hxx",
        },
   },
    "C": {
        "": {
              SOURCE:              ".c",
              HEADER:              ".h",
              HEADER_IMPLEMTATION: ".c",
        }
   }
}

setup = something()
for key, entry in SETUP_INFO.items():
    if type(entry) != list:        default_value = entry
    elif entry[1] == LIST:         default_value = []
    elif entry[1] == FLAG:         default_value = False
    elif entry[1] == NEGATED_FLAG: default_value = True
    else:                          default_value = entry[1]
    setup.__dict__[key] = default_value

# Default values, maybe overiden later on.
setup.language_db = quex_core_engine_generator_languages_db["C++"]
setup.language_db = global_extension_db["C++"]
setup.buffer_codec_transformation_info = None
