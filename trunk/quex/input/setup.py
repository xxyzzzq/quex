#! /usr/bin/env python
from   quex.DEFINITIONS import *
from   copy import copy
import sys

from   quex.GetPot                 import GetPot
from   quex.frs_py.file_in         import open_file_or_die, error_msg, is_identifier
import quex.lexer_mode as lexer_mode
import quex.input.query as query


class something:
    pass

LIST = -1
FLAG = -2

SETUP_INFO = {         
    # [Name in Setup]                 [ Flags ]                              [Default / Type]
    "begin_of_stream_code":           [["--begin-of-stream"],                "0x19"],
    "buffer_limit_code":              [["--buffer-limit"],                   "0x0"],
    "bytes_per_ucs_code_point":       [["--bytes-per-ucs-code-point", "-b"], "1"],
    "no_dos_carriage_return_newline_f":  [["--no-DOS"],                      FLAG],
    "end_of_stream_code":             [["--end-of-stream"],                  "0x1A"],
    "enable_iconv_f":                 [["--iconv"],                          FLAG],
    "byte_order":                     [["--endian"],                         "<system>"],
    "input_application_version_id":   [["--version-id"],                     "0.0.0-pre-release"],
    "input_derived_class_file":       [["--derived-class-file"],             ""],
    "input_derived_class_name":       [["--derived-class"],                  ""],
    "input_foreign_token_id_file":    [["--foreign-token-id-file"],          ""],
    "input_lexer_class_friends":      [["--friend-class"],                   LIST],
    "input_mode_files":               [["-i", "--mode-files"],               LIST],
    "input_token_class_file":         [["--token-class-file"],               "quex/code_base/token"],
    "input_token_class_name":         [["--token-class"],                    "token"],
    "input_token_counter_offset":     [["--token-offset"],                   "10000"],
    "token_id_termination":           [["--token-id-termination"],           "0"],
    "token_id_uninitialized":         [["--token-id-uninitialized"],         "1"],
    "input_token_id_prefix":          [["--token-prefix"],                   "TKN_"],
    "input_user_token_id_file":       [["--user-token-id-file"],             ""],
    "no_mode_transition_check_f":     [["--no-mode-transition-check"],       FLAG],
    "output_debug_f":                 [["--debug"],                          FLAG],
    "output_engine_name":             [["-o", "--engine"],                   "lexer"],    
    "plain_memory_f":                 [["--plain-memory"],                   FLAG],
    "plot_graphic_format":            [["--plot"],                           ""],
    "plot_graphic_format_list_f":     [["--plot-format-list"],               FLAG],
    #
    "version_information":            [["--version", "-v"],                  FLAG],
    "help":                           [["--help", "-h"],                     FLAG],
    #______________________________________________________________________________________________________
    "flex_engine_f":                  [["--flex-engine"],           FLAG],                    # DEPRECIATED
    "input_pattern_file":             [["-p", "--pattern-file"],    ""],                      # DEPRECIATED 
    "input_token_id_db":              [["-t", "--token-id-db"],     LIST],                    # DEPRECIATED
    "leave_temporary_files_f":        [["--leave-tmp-files"],       FLAG],                    # DEPRECIATED
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
  "std_istream_support_f":
     ("The lexical analyzer has a flexible interface now, for both C++ istreams and FILE*\n" + \
      "so that rigid setting with this option is superfluous", "0.13.1"),
}
 
def do(argv):
    setup = something()

    # (*) Interpret Command Line (A) _____________________________________________________
    command_line = GetPot(argv)

    if command_line.search("--version", "-v"):
        print "Quex - A Mode Oriented Lexical Analyser"
        print "Version " + QUEX_VERSION
        print "(C) 2006, 2007 Frank-Rene Schaefer"
        sys.exit(0)

    if command_line.search("--help", "-h"):
        print "Quex - A Mode Oriented Lexical Analyser"
        print "Please, consult the quex documentation for further help, or"
        print "visit http://quex.sourceforge.net."
        print "(C) 2006, 2007 Frank-Rene Schaefer"
        sys.exit(0)

    for variable_name, info in SETUP_INFO.items():
        if info[1]   == LIST:
            the_list = command_line.nominus_followers(info[0])
            if setup.__dict__.has_key(variable_name):
                setup.__dict__[variable_name].extend(the_list)        
            else:
                setup.__dict__[variable_name] = the_list
        elif info[1] == FLAG:
            setup.__dict__[variable_name] = command_line.search(info[0])        
        else:
            setup.__dict__[variable_name] = command_line.follow(info[1], info[0])

    setup.QUEX_VERSION          = QUEX_VERSION
    setup.QUEX_INSTALLATION_DIR = QUEX_INSTALLATION_DIR
    setup.QUEX_TEMPLATE_DB_DIR  = QUEX_TEMPLATE_DB_DIR
            
    setup.output_file_stem     = setup.output_engine_name
    setup.output_token_id_file = setup.output_engine_name + "-token_ids"
    setup.output_header_file   = setup.output_engine_name + "-internal.h"
    setup.output_code_file     = setup.output_engine_name + ".cpp"

    setup.buffer_limit_code    = __get_integer(setup.buffer_limit_code,    "--buffer-limit")
    setup.begin_of_stream_code = __get_integer(setup.begin_of_stream_code, "--begin-of-stream")
    setup.end_of_stream_code   = __get_integer(setup.end_of_stream_code,   "--end-of-stream")
    setup.control_character_code_list = [setup.buffer_limit_code,
                                         setup.begin_of_stream_code,
                                         setup.end_of_stream_code]

    setup.input_token_counter_offset = __get_integer(setup.input_token_counter_offset,
                                                     "--token-offset")
    setup.token_id_termination       = __get_integer(setup.token_id_termination, 
                                                     "--token-id-termination")
    setup.token_id_uninitialized     = __get_integer(setup.token_id_uninitialized, 
                                                     "--token-id-uninitialized")

    validate(setup, command_line, argv)

    # (*) return setup ___________________________________________________________________
    return setup


def validate(setup, command_line, argv):
    """Does a consistency check for setup and the command line.
    """
    # ensure that options are not specified twice
    for parameter, info in SETUP_INFO.items():
        occurence_n = 0 
        for option in info[0]:
            occurence_n += argv.count(option)
        if occurence_n > 1:
            error_msg("Received more than one of the following options:\n" + \
                      "%s" % repr(info[0])[1:-1])

    # (*) Check for 'Depraceted' Options ___________________________________________________
    for name, info in DEPRECATED.items():
        command_line_options = SETUP_INFO[name][0]
        comment                   = info[0]
        depreciated_since_version = info[1]
        for option in command_line_options:
            if command_line.search(option):
                error_msg("Command line option '%s' is ignored.\n" % option + \
                          "Last version of Quex supporting this option is version %s. Please, visit\n" % version + \
                          "http://quex.sourceforge.net for download---Or use a more advanced approach.\n" + \
                          comment)
                          

    # (*) Check for 'Straying' Options ___________________________________________________
    options = []
    for key, info in SETUP_INFO.items():
        if key in DEPRECATED: continue
        if info[1] != None: options.extend(info[0])
    options.sort(lambda a,b: cmp(a.replace("-",""), b.replace("-","")))

    ufos = command_line.unidentified_options(options)
    if ufos != []:
        error_msg("Unidentified option(s) = " +  repr(ufos) + "\n" + \
                  __get_supported_command_line_option_description(options))

    if setup.input_derived_class_name != "" and \
       setup.input_derived_class_file == "":
            error_msg("Specified derived class '%s' on command line, but it was not\n" % \
                      setup.input_derived_class_name + \
                      "specified which file contains the definition of it.\n" + \
                      "use command line option '--derived-class-file'.\n")

    # check whether the limit codes make sense (end of file, begin of file, buffer limit)
    __check_stream_limit_codes(setup)

    # check validity
    bpc = setup.bytes_per_ucs_code_point
    if bpc != "wchar_t":
        if bpc not in ["1", "2", "4"]:
            error_msg("choice for --bytes-per-ucs-code-point: %s" % bpc + \
                      "quex only supports 1, 2, or 4 bytes per character in internal engine")
            sys.exit(-1)
        else:
            setup.bytes_per_ucs_code_point = int(setup.bytes_per_ucs_code_point)


    if setup.byte_order == "<system>": 
        setup.byte_order = sys.byteorder 
    elif setup.byte_order not in ["<system>", "little", "big"]:
        error_msg("Byte order (option --endian) must be 'little' or 'big'.\n" + \
                  "Note, that this option is only interesting for cross plattform development.\n" + \
                  "By default, quex automatically chooses the endian type of your system.")

    # token offset and several ids
    if setup.input_token_counter_offset == setup.token_id_termination:
        error_msg("Token id offset (--token-offset) == token id for termination (--token-id-termination)\n")
    if setup.input_token_counter_offset == setup.token_id_uninitialized:
        error_msg("Token id offset (--token-offset) == token id for uninitialized (--token-id-uninitialized)\n")
    if setup.token_id_termination == setup.token_id_uninitialized:
        error_msg("Token id for termination (--token-id-termination) and uninitialized (--token-id-uninitialized)\n" + \
                  "are chosen to be the same. Maybe it works.", DontExitF=True)
    if setup.input_token_counter_offset < setup.token_id_uninitialized:
        error_msg("Token id offset (--token-offset) < token id uninitialized (--token-id-uninitialized).\n" + \
                  "Maybe it works.", DontExitF=True)
    if setup.input_token_counter_offset < setup.token_id_termination:
        error_msg("Token id offset (--token-offset) < token id termination (--token-id-termination).\n" + \
                  "Maybe it works.", DontExitF=True)
    
    # check that names are valid identifiers
    __check_identifier(setup, "input_token_id_prefix", "Token prefix")
    __check_identifier(setup, "output_engine_name",    "Engine name")
    if setup.input_derived_class_name != "": 
        __check_identifier(setup, "input_derived_class_name", "Derived class name")
    if setup.input_token_class_name != "": 
        __check_identifier(setup, "input_token_class_name",   "Token class name")
    # __check_identifier("token_id_termination",     "Token id for termination")
    # __check_identifier("token_id_uninitialized",   "Token id for uninitialized")

        
def __check_identifier(setup, Candidate, Name):
    value = setup.__dict__[Candidate]
    if is_identifier(value): return

    CommandLineOption = SETUP_INFO[Candidate][0]

    error_msg("%s must be a valid identifier (%s).\n" % (Name, repr(CommandLineOption)[1:-1]) + \
              "Received: '%s'" % value)

def __get_integer(code, option_name):
    try:
        if   type(code) == int: return code
        elif len(code) > 2:
            if   code[:2] == "0x": return int(code, 16)
            elif code[:2] == "0o": return int(code, 8)
        return int(code)
    except:
        error_msg("Cannot convert '%s' into an integer for '%s'" % (code, option_name))

def __get_supported_command_line_option_description(NormalModeOptions):
    txt = "OPTIONS:\n"
    for option in NormalModeOptions:
        txt += "    " + option + "\n"

    txt += "\nOPTIONS FOR QUERY MODE:\n"
    txt += query.get_supported_command_line_option_description()
    return txt

def __check_stream_limit_codes(setup):
    if setup.begin_of_stream_code == setup.end_of_stream_code:
        error_msg("code for begin/end of stream cannot be equal!")
    if setup.begin_of_stream_code == setup.buffer_limit_code:
        error_msg("code for begin of stream and buffer limit cannot be equal!")
    if setup.buffer_limit_code == setup.end_of_stream_code:
        error_msg("code for end of stream and buffer limit cannot be equal!")
