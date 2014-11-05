#! /usr/bin/env python
from quex.core_engine.generator.languages.core import db as quex_core_engine_generator_languages_db
class something:
    pass


LIST = -1
FLAG = -2

SETUP_INFO = {         
    # [Name in Setup]                 [ Flags ]                              [Default / Type]
    "buffer_limit_code":              [["--buffer-limit"],                   "0x0"],
    "bytes_per_ucs_code_point":       [["--bytes-per-ucs-code-point", "-b"], "1"],
    "no_dos_carriage_return_newline_f":  [["--no-DOS"],                      FLAG],
    "enable_iconv_f":                 [["--iconv"],                          FLAG],
    "byte_order":                     [["--endian"],                         "<system>"],
    "input_application_version_id":   [["--version-id"],                     "0.0.0-pre-release"],
    "input_derived_class_file":       [["--derived-class-file"],             ""],
    "input_derived_class_name":       [["--derived-class"],                  ""],
    "input_foreign_token_id_file":    [["--foreign-token-id-file"],          ""],  # provides foreign token-ids to
    #                                                                              # be included in generated file.
    "input_lexer_class_friends":      [["--friend-class"],                   LIST],
    "input_mode_files":               [["-i", "--mode-files"],               LIST],
    "input_token_class_file":         [["--token-class-file"],               "", "quex/code_base/Token"],
    "input_token_sending_via_queue_f": [["--token-queue"],                   FLAG],
    "input_token_class_name":         [["--token-class"],                    "", "Token"],
    "input_token_counter_offset":     [["--token-offset"],                   "10000"],
    "token_id_termination":           [["--token-id-termination"],           "0"],
    "token_id_uninitialized":         [["--token-id-uninitialized"],         "1"],
    "input_token_id_prefix":          [["--token-prefix"],                   "TKN_"],
    "input_user_token_id_file":       [["--user-token-id-file"],             ""],  # disables token-id file generation!
    "no_mode_transition_check_f":     [["--no-mode-transition-check"],       FLAG],
    "output_debug_f":                 [["--debug"],                          FLAG],
    "output_engine_name":             [["-o", "--engine"],                   "lexer"],    
    "post_categorizer_f":             [["--post-categorizer"],               FLAG],
    "plot_graphic_format":            [["--plot"],                           ""],
    "plot_graphic_format_list_f":     [["--plot-format-list"],               FLAG],
    "string_accumulator_f":           [["--string-accumulator", "--sacc"],   FLAG],
    #
    "version_information":            [["--version", "-v"],                  FLAG],
    "help":                           [["--help", "-h"],                     FLAG],
    #______________________________________________________________________________________________________
    "begin_of_stream_code":           [["--begin-of-stream"],       "0x19"],                  # DEPRECIATED
    "end_of_stream_code":             [["--end-of-stream"],         "0x1A"],                  # DEPRECIATED
    "flex_engine_f":                  [["--flex-engine"],           FLAG],                    # DEPRECIATED
    "input_pattern_file":             [["-p", "--pattern-file"],    ""],                      # DEPRECIATED 
    "input_token_id_db":              [["-t", "--token-id-db"],     LIST],                    # DEPRECIATED
    "leave_temporary_files_f":        [["--leave-tmp-files"],       FLAG],                    # DEPRECIATED
    "plain_memory_f":                 [["--plain-memory"],          FLAG],                    # DEPRECIATED
    "std_istream_support_f":          [["--istream-support"],       FLAG],                    # DEPRECIATED
    "yywrap_is_ok_f":                 [["--yywrap-is-ok"],          FLAG],                    # DEPRECIATED
}

DEPRECATED = { 
  "input_pattern_file": 
     ("Write a 'pattern { ... }' section inside the mode files instead.\n" + \
      "Syntax of the 'pattern { ... }' section and the previous file syntax\n" + \
      "are backward compatible.", "0.9.x"),        
  "input_token_id_db":
     ("Write a 'token { ... }' section inside the mode files instead.\n" + \
      "Syntax of the 'token { ... }' section and the previous file syntax\n" + \
      "are backward compatible.", "0.9.x"),        
  "yywrap_is_ok_f":
     ("Since the mentioned version, the flex core engine is no longer supported. The\n" + \
      "flag makes only sense for flex core engines.", "0.13.1"),
  "flex_engine_f":
     ("Since the mentioned version, the flex core engine is no longer supported. The\n" + \
      "flag makes only sense for flex core engines.", "0.13.1"),
  "leave_temporary_files_f":
     ("Since the mentioned version, the flex core engine is no longer supported. The\n" + \
      "flag makes only sense for flex core engines.", "0.13.1"),
  "plain_memory_f":                 
     ("Since the mentioned version, quex does no longer need the '--plain-memory' command\n" + \
      "line argument. The engine can be used with plain memory directly. Please, consider\n" + \
      "reading the documentation on this issue.", "0.31.1"),
  "std_istream_support_f":
     ("The lexical analyzer has a flexible interface now, for both C++ istreams and FILE*\n" + \
      "so that rigid setting with this option is superfluous", "0.13.1"),
  "begin_of_stream_code":
     ("Since the mentioned version, there is no need for end of stream and end of stream\n" + \
      "characters anymore. Options '--end-of-stream' and '--begin-of-stream' are no longer\n" + \
      "supported.", "0.25.2"),
  "end_of_stream_code":
     ("Since the mentioned version, there is no need for end of stream and end of stream\n" + \
      "characters anymore. Options '--end-of-stream' and '--begin-of-stream' are no longer\n" + \
      "supported.", "0.25.2"),
}
 

setup = something()
for key, entry in SETUP_INFO.items():
    if entry[1] == LIST:   default_value = []
    elif entry[1] == FLAG: default_value = False
    else:                  default_value = entry[1]
    setup.__dict__[key] = default_value

setup.language_db = quex_core_engine_generator_languages_db["C++"]
