#! /usr/bin/env python
from quex.DEFINITIONS import *
from copy import copy
import sys

from GetPot import GetPot
from frs_py.string_handling import trim
from quex.frs_py.file_in    import open_file_or_die, error_msg

class something:
    pass

LIST = -1
FLAG = -2

SETUP_INFO = {         
    # [Name in Setup]                 [ Flags ]                              [Default / Type]
    "begin_of_stream_code":           [["--begin-of-stream"],                0x19],
    "bytes_per_ucs_code_point":       [["--bytes-per-ucs-code-point", "-b"], 1],
    "dos_carriage_return_newline_f":  [["--DOS"],                            FLAG],
    "end_of_stream_code":             [["--end-of-stream"],                  0x1A],
    "enable_iconv_f":                 [["--iconv"],                          FLAG],
    "byte_order":                     [["--endian"],                         "<system>"],
    "input_application_version_id":   [["--version-id"],                     "0.0.0-pre-release"],
    "input_derived_class_file":       [["--derived-class-file"],             ""],
    "input_derived_class_name":       [["--derived-class"],                  ""],
    "input_foreign_token_id_file":    [["--foreign-token-id-file"],          ""],
    "input_lexer_class_friends":      [["--friend-class"],                   LIST],
    "input_mode_files":               [["-i", "--mode-files"],               LIST],
    "input_token_class_file":         [["--token-class-file"],               QUEX_TEMPLATE_DB_DIR + "/token"],
    "input_token_class_name":         [["--token-class"],                    "token"],
    "input_token_counter_offset":     [["--token-offset"],                   10000],
    "input_token_id_prefix":          [["--token-prefix"],                   "TKN_"],
    "input_user_token_id_file":       [["--user-token-id-file"],             ""],
    "no_mode_transition_check_f":     [["--no-mode-transition-check"],       FLAG],
    "output_debug_f":                 [["--debug"],                          FLAG],
    "output_engine_name":             [["-o", "--engine"],                   "lexer"],    
    "plain_memory_f":                 [["--plain-memory"],                   FLAG],
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
	print "(C) 2006, 2007 Frank-Rene Schaefer"
        print "visit http://quex.sourceforge.net."
        sys.exit(0)


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
			  

    for variable_name, info in SETUP_INFO.items():
	if info[1]   == LIST:
            setup.__dict__[variable_name] = command_line.nominus_followers(info[0])        
	elif info[1] == FLAG:
            setup.__dict__[variable_name] = command_line.search(info[0])        
        else:
            setup.__dict__[variable_name] = command_line.follow(info[1], info[0])

    setup.QUEX_VERSION          = QUEX_VERSION
    setup.QUEX_INSTALLATION_DIR = QUEX_INSTALLATION_DIR
    setup.QUEX_TEMPLATE_DB_DIR  = QUEX_TEMPLATE_DB_DIR
            
    if setup.input_derived_class_name != "" and \
       setup.input_derived_class_file == "":
            print "error: specified derived class '%s' on command line, but it was not" % \
		  setup.input_derived_class_name
            print "error: specified which file contains the definition of it."
            print "error: use command line option '--derived-class-file'."
            sys.exit(-1)

    setup.output_file_stem     = setup.output_engine_name
    setup.output_token_id_file = setup.output_engine_name + "-token_ids"
    setup.output_header_file   = setup.output_engine_name + "-internal.h"
    setup.output_code_file     = setup.output_engine_name + ".cpp"

    def __get_integer(code, option_name):
	try:
	    if   type(code) == int: return code
	    elif len(code) > 2:
		if   code[:2] == "0x": return int(code, 16)
		elif code[:2] == "0o": return int(code, 8)
		else:                  return int(code)
	except:
	    pass
	print "error: cannot convert %s into an intege for '%s'" % (code, option_name)
	sys.exit(-1)

    setup.begin_of_stream_code = __get_integer(setup.begin_of_stream_code, "--begin-of-stream")
    setup.end_of_stream_code   = __get_integer(setup.end_of_stream_code, "--end-of-stream")

    if setup.begin_of_stream_code == 0 or setup.end_of_stream_code == 0:
	print "error: code for begin/end of stream cannot be zero!"
	sys.exit(-1)

    # check validity
    if setup.bytes_per_ucs_code_point not in ["whar_t", 1, 2, 4]:
	print "error: choice for --bytes-per-ucs-code-point: %i" % setup.bytes_per_ucs_code_point
	print "error: quex only supports 1, 2, or 4 bytes per character in internal engine"
	sys.exit(-1)

    if setup.byte_order == "<system>": 
	setup.byte_order = sys.byteorder 
    elif setup.byte_order not in ["<system>", "little", "big"]:
	print "error: Byte order (option --endian) must be 'little' or 'big'."
	print "error: Note, that this option is only interesting for cross plattform development."
	print "error: By default, quex automatically chooses the endian type of your system."
	sys.exit(-1)
        
    # (*) Check for 'Straying' Options ___________________________________________________
    options = []
    for info in SETUP_INFO.values():
        if info[1] != None: options.extend(info[0])

    ufos = command_line.unidentified_options(options)
    if ufos != []:
        options.sort(lambda a,b: cmp(a.replace("-",""),b.replace("-","")))
        print "error: unidentified option(s) = ", repr(ufos)
        print "error: accepted options = ", repr(options)[1:-1]
        sys.exit(-1)

    # (*) return setup ___________________________________________________________________
    return setup


