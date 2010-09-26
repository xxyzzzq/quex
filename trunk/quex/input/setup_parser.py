from   quex.DEFINITIONS import *
from   copy import copy, deepcopy
import sys
import os
from   StringIO import StringIO

from   quex.GetPot                 import GetPot
from   quex.frs_py.file_in         import error_msg, error_msg_file_not_found, is_identifier, \
                                          extract_identifiers_with_specific_prefix, \
                                          delete_comment, verify_word_in_list, read_namespaced_name, \
                                          read_integer
import quex.lexer_mode  as lexer_mode
import quex.input.query as query
import quex.input.codec_db as codec_db
from   quex.output.cpp.token_id_maker import parse_token_id_file

from   quex.input.setup import setup, SETUP_INFO, LIST, FLAG, NEGATED_FLAG, DEPRECATED
from   quex.core_engine.generator.languages.core import db as quex_core_engine_generator_languages_db

from   quex.core_engine.generator.action_info import CodeFragment

class ManualTokenClassSetup:
    """Class to mimik as 'real' TokenTypeDescriptor as defined in 
       quex.input.token_type.py. Names and functions must remain
       as they are for compatibility.
    """
    def __init__(self, FileName, ClassName, NameSpace, ClassNameSafe, TokenIDType):
        
        self.__file_name       = FileName
        self.class_name        = ClassName
        self.name_space        = NameSpace
        self.class_name_safe   = ClassNameSafe

        self.column_number_type = CodeFragment("size_t")
        self.line_number_type   = CodeFragment("size_t")
        self.token_id_type      = CodeFragment(TokenIDType)

    def get_file_name(self):
        return self.__file_name

    def manually_written(self):
        return True

def do(argv):
    """RETURN:  True, if process needs to be started.
                False, if job is done.
    """
    global setup

    # (*) Interpret Command Line (A) _____________________________________________________
    command_line = GetPot(argv)

    if command_line.search("--version", "-v"):
        print "Quex - Fast Universal Lexical Analyzer Generator"
        print "Version " + QUEX_VERSION
        print "(C) 2006-2010 Frank-Rene Schaefer"
        print "ABSOLUTELY NO WARRANTY"
        return False

    if command_line.search("--help", "-h"):
        print "Quex - Fast Universal Lexical Analyzer Generator"
        print "Please, consult the quex documentation for further help, or"
        print "visit http://quex.org"
        print "(C) 2006-2010 Frank-Rene Schaefer"
        print "ABSOLUTELY NO WARRANTY"
        return False

    if command_line.search("--plot-format-list"):
        print quex.output.graphviz.interface.get_supported_graphic_format_description()
        return False

    for variable_name, info in SETUP_INFO.items():
        # Some parameters are not set on the command line. Their entry is not associated
        # with a description list.
        if type(info) != list: continue

        if info[1] == FLAG:
            setup.__dict__[variable_name] = command_line.search(info[0])        

        elif info[1] == NEGATED_FLAG:
            setup.__dict__[variable_name] = not command_line.search(info[0])        

        elif info[1] == LIST:
            if not command_line.search(info[0]):
                setup.__dict__[variable_name] = []
            else:
                the_list = command_line.nominus_followers(info[0])
                if the_list == []:
                    error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])

                if setup.__dict__.has_key(variable_name):
                    setup.__dict__[variable_name].extend(the_list)        
                else:
                    setup.__dict__[variable_name] = the_list

        elif command_line.search(info[0]):
            if not command_line.search(info[0]):
                setup.__dict__[variable_name] = info[1]
            else:
                value = command_line.follow("--EMPTY--", info[0])
                if value == "--EMPTY--":
                    error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])
                setup.__dict__[variable_name] = value

    setup.QUEX_VERSION          = QUEX_VERSION
    setup.QUEX_INSTALLATION_DIR = QUEX_INSTALLATION_DIR

    # (*) Classes and their namespace
    setup.analyzer_class_name, \
    setup.analyzer_name_space, \
    setup.analyzer_name_safe   = \
         read_namespaced_name(setup.analyzer_class_name, 
                              "analyzer engine (options -o, --engine, --analyzer-class)")
    if setup.analyzer_name_space == []:
        setup.analyzer_name_space = ["quex"]
    if setup.token_class_name == "":
        setup.token_class_name = "%s::Token" % reduce(lambda a, b: a + "::" + b, setup.analyzer_name_space)

    # Token classes and derived classes have the freedom not to open a namespace,
    # thus no check 'if namespace == []'.
    setup.token_class_name,       \
    setup.token_class_name_space, \
    setup.token_class_name_safe = \
         read_namespaced_name(setup.token_class_name, 
                              "token class (options --token-class, --tc)")

    if setup.token_class_file != "":
        lexer_mode.token_type_definition = \
                ManualTokenClassSetup(setup.token_class_file,
                                      setup.token_class_name,
                                      setup.token_class_name_space,
                                      setup.token_class_name_safe,
                                      setup.token_id_type)

    if setup.token_class_name_space == []:
        setup.token_class_name_space = deepcopy(setup.analyzer_name_space)

    setup.analyzer_derived_class_name,       \
    setup.analyzer_derived_class_name_space, \
    setup.analyzer_derived_class_name_safe = \
         read_namespaced_name(setup.analyzer_derived_class_name, 
                              "derived analyzer class (options --derived-class, --dc)",
                              AllowEmptyF=True)

    # (*) Output programming language        
    setup.language = setup.language.upper()
    verify_word_in_list(setup.language,
                        quex_core_engine_generator_languages_db.keys(),
                        "Programming language '%s' is not supported." % setup.language)
    setup.language_db = quex_core_engine_generator_languages_db[setup.language]

    # (*) Output files
    prepare_file_names(setup)

    if setup.engine_character_encoding != "":
        # Note, that the name may be set to 'None' if the conversion is utf8 or utf16
        # See Internal engine character encoding'
        setup.engine_character_encoding_header = __prepare_file_name("-converter-%s" % setup.engine_character_encoding)
    else:
        setup.engine_character_encoding_header = None

    if setup.byte_order == "<system>": 
        setup.byte_order = sys.byteorder 
        setup.byte_order_is_that_of_current_system_f = True
    else:
        setup.byte_order_is_that_of_current_system_f = False

    make_numbers(setup)

    validate(setup, command_line, argv)

    if setup.token_id_foreign_definition_file != "": 
        CommentDelimiterList = [["//", "\n"], ["/*", "*/"]]
        # Regular expression to find '#include <something>' and extract the 'something'
        # in a 'group'. Note that '(' ')' cause the storage of parts of the match.
        IncludeRE            = "#[ \t]*include[ \t]*[\"<]([^\">]+)[\">]"
        #
        parse_token_id_file(setup.token_id_foreign_definition_file, setup.token_id_prefix, 
                            CommentDelimiterList, IncludeRE)

    # (*) return setup ___________________________________________________________________
    return True

def validate(setup, command_line, argv):
    """Does a consistency check for setup and the command line.
    """
    setup.output_directory = os.path.normpath(setup.output_directory)
    if setup.output_directory != "":
        # Check, if the output directory exists
        if os.access(setup.output_directory, os.F_OK) == False:
            error_msg("The directory %s was specified for output, but does not exists." % setup.output_directory)
        if os.access(setup.output_directory, os.W_OK) == False:
            error_msg("The directory %s was specified for output, but is not writeable." % setup.output_directory)

    # if the mode is 'plotting', then check wether a graphic format is speicified
    for plot_option in SETUP_INFO["plot_graphic_format"][0]:
        if plot_option in argv and setup.plot_graphic_format == "":
            error_msg("Option '%s' must be followed by a graphic format specifier (bmp, svg, jpg, ...)" % \
                      plot_option)

    if setup.plot_character_display not in ["hex", "utf8"]:
        error_msg("Plot character display must be either 'hex' or 'utf8'.\nFound: '%s'" % 
                  setup.plot_character_display)

    # ensure that options are not specified twice
    for parameter, info in SETUP_INFO.items():
        if type(info) != list: continue
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
                          comment + "\n" + \
                          "Last version of Quex supporting this option is version %s. Please, visit\n" % \
                          depreciated_since_version + \
                          "http://quex.org for further information.")
                          

    # (*) Check for 'Straying' Options ___________________________________________________
    options = []
    for key, info in SETUP_INFO.items():
        if type(info) != list: continue
        if key in DEPRECATED: continue
        if info[1] != None: options.extend(info[0])
    options.sort(lambda a,b: cmp(a.replace("-",""), b.replace("-","")))

    ufos = command_line.unidentified_options(options)
    if ufos != []:
        error_msg("Unidentified option(s) = " +  repr(ufos) + "\n" + \
                  __get_supported_command_line_option_description(options))

    if setup.analyzer_derived_class_name != "" and \
       setup.analyzer_derived_class_file == "":
            error_msg("Specified derived class '%s' on command line, but it was not\n" % \
                      setup.analyzer_derived_class_name + \
                      "specified which file contains the definition of it.\n" + \
                      "use command line option '--derived-class-file'.\n")

    # Check validity
    bpc = setup.bytes_per_ucs_code_point
    if bpc.isdigit():
        if bpc not in ["1", "2", "4"]:
            error_msg("choice for '--bytes-per-trigger': '%s'\n" % bpc + \
                      "quex only supports 1, 2, 4, or 'wchar_t' as setting for this parameter.")
        else:
            setup.bytes_per_ucs_code_point = __get_integer("bytes_per_ucs_code_point")

    elif bpc not in ["wchar_t", ""]:
        error_msg("choice for '--bytes-per-trigger': '%s'\n" % bpc + \
                  "quex only supports 1, 2, 4, or 'wchar_t' as setting for this parameter.")

    if setup.byte_order not in ["<system>", "little", "big"]:
        error_msg("Byte order (option --endian) must be 'little', 'big', or '<system>'.\n" + \
                  "Note, that this option is only interesting for cross plattform development.\n" + \
                  "By default, quex automatically chooses the endian type of your system.")

    # Manually written token class requires token class name to be specified
    if setup.token_class_file != "" and command_line.search("--token-class", "--tc") == False:
        error_msg("The use of a manually written token class requires that the name of the class\n"
                  "is specified on the command line via the '--token-class' option.")
    
    # Token queue
    if setup.token_policy != "queue" and command_line.search("--token-queue-size"):
        error_msg("Option --token-queue-size determines a fixed token queue size. This makes\n" + \
                  "only sense in conjunction with '--token-policy queue'.\n")
    if setup.token_queue_size <= setup.token_queue_safety_border + 1:
        if setup.token_queue_size == setup.token_queue_safety_border: cmp_str = "equal to"
        else:                                                         cmp_str = "less than"
        error_msg("Token queue size is %i is %s token queue safety border %i + 1.\n" % \
                  (setup.token_queue_size, cmp_str, setup.token_queue_safety_border) + 
                  "Set appropriate values with --token-queue-size and --token-queue-safety-border.")

    # Check that names are valid identifiers
    __check_identifier(setup, "token_id_prefix",    "Token prefix")
    __check_identifier(setup, "analyzer_class_name", "Engine name")
    if setup.analyzer_derived_class_name != "": 
        __check_identifier(setup, "analyzer_derived_class_name", "Derived class name")
    
    __check_file_name(setup, "token_class_file",            "file containing token class definition")
    __check_file_name(setup, "analyzer_derived_class_file", "file containing user derived lexer class")
    __check_file_name(setup, "token_id_foreign_definition_file", "file containing user token ids")
    __check_file_name(setup, "input_mode_files", "quex source file")

    # Check that not more than one converter is specified
    converter_n = 0
    if setup.converter_iconv_f:             converter_n += 1
    if setup.converter_icu_f:               converter_n += 1 
    if setup.converter_user_new_func != "": converter_n += 1
    if converter_n > 1:
        error_msg("More than one character converter has been specified. Note, that the\n" + \
                  "options '--icu', '--iconv', and '--converter-new' (or '--cn') are\n" + \
                  "to be used mutually exclusively.")
    if converter_n == 1 and setup.engine_character_encoding != "":  
        error_msg("An engine that is to be generated for a specific codec cannot rely\n" + \
                  "on converters. Do no use '--codec' together with '--icu', '--iconv', or\n" + \
                  "`--converter-new`.")

    # Token transmission policy
    token_policy_list = ["queue", "single", "users_token", "users_queue"]
    if setup.token_policy not in token_policy_list:
        error_msg("Token policy '%s' not supported. Use one of the following:\n" % setup.token_policy + \
                  repr(token_policy_list)[1:-1])
    elif setup.token_policy == "users_token":
        error_msg("Token policy 'users_queue' has be deprecated since 0.49.1. Use\n"
                  "equivalent policy 'single'.")
    elif setup.token_policy == "users_queue":
        error_msg("Token policy 'users_queue' has be deprecated since 0.49.1\n")

    # Internal engine character encoding
    if setup.engine_character_encoding != "":
        verify_word_in_list(setup.engine_character_encoding,
                            codec_db.get_supported_codec_list() + ["utf8", "utf16"],
                            "Codec '%s' is not supported." % setup.engine_character_encoding)
        if setup.engine_character_encoding in ["utf8", "utf16"]:
            setup.engine_character_encoding_transformation_info = \
                    setup.engine_character_encoding + "-state-split"
            if setup.engine_character_encoding == "utf8":
               if setup.bytes_per_ucs_code_point != 1:
                   error_msg("Using codec 'utf8' while bytes per trigger is != 1.\n"
                             "Consult command line argument '--bytes-per-trigger'.")
            if setup.engine_character_encoding == "utf16":
               if setup.bytes_per_ucs_code_point != 2:
                   error_msg("Using codec 'utf16' while bytes per trigger is != 2.\n"
                             "Consult command line argument '--bytes-per-trigger'.")
        else:
            setup.engine_character_encoding_transformation_info = \
                  codec_db.get_codec_transformation_info(setup.engine_character_encoding)

    if setup.engine_character_encoding_transformation_info in ["utf8-state-split", "utf16-state-split"]: 
        setup.engine_character_encoding_header = None

    # Path Compression
    if setup.compression_path_uniform_f and setup.compression_path_f:
        error_msg("Both flags for path compression were set: '--path-compression' and\n" 
                  "'--path-compression-uniform'. Please, choose only one!")
                
def __check_file_name(setup, Candidate, Name):
    value             = setup.__dict__[Candidate]
    CommandLineOption = SETUP_INFO[Candidate][0]

    if value == "": return

    if type(value) == list:
        for name in value:
            if name != "" and name[0] == "-": 
                error_msg("Quex refuses to work with file names that start with '-' (minus).\n"  + \
                          "Received '%s' for %s (%s)" % (value, name, repr(CommandLineOption)[1:-1]))
            if os.access(name, os.F_OK) == False:
                # error_msg("File %s (%s)\ncannot be found." % (name, Name))
                error_msg_file_not_found(name, Name)
    else:
        QUEX_PATH = os.environ["QUEX_PATH"]
        if value == "" or value[0] == "-":              return
        if os.access(value, os.F_OK):                   return
        if os.access(QUEX_PATH + "/" + value, os.F_OK): return
        if     os.access(os.path.dirname(value), os.F_OK) == False \
           and os.access(QUEX_PATH + "/" + os.path.dirname(value), os.F_OK) == False:
            error_msg("File '%s' is supposed to be located in directory '%s' or\n" % \
                      (os.path.basename(value), os.path.dirname(value)) + \
                      "'%s'. No such directories exist." % \
                      (QUEX_PATH + "/" + os.path.dirname(value)))
        error_msg_file_not_found(value, Name)

def __check_identifier(setup, Candidate, Name):
    value = setup.__dict__[Candidate]
    if is_identifier(value): return

    CommandLineOption = SETUP_INFO[Candidate][0]

    error_msg("%s must be a valid identifier (%s).\n" % (Name, repr(CommandLineOption)[1:-1]) + \
              "Received: '%s'" % value)

def __get_float(MemberName):
    ValueStr = setup.__dict__[MemberName]
    if type(ValueStr) == float: return ValueStr
    try:
        return float(ValueStr)
    except:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an floating point number for '%s'" % (ValueStr, option_name))

def prepare_file_names(setup):
    setup.output_code_file          = __prepare_file_name(setup.language_db["$file_extension"])
    setup.output_file_stem          = __prepare_file_name("")
    setup.output_configuration_file = __prepare_file_name("-configuration")
    setup.output_token_id_file      = __prepare_file_name("-token_ids")
    setup.output_token_class_file   = __prepare_file_name("-token")

def make_numbers(setup):
    setup.compression_template_coef  = __get_float("compression_template_coef")
    setup.buffer_limit_code          = __get_integer("buffer_limit_code")
    setup.path_limit_code            = __get_integer("path_limit_code")

    setup.token_id_counter_offset    = __get_integer("token_id_counter_offset")
    setup.token_queue_size           = __get_integer("token_queue_size")
    setup.token_queue_safety_border  = __get_integer("token_queue_safety_border")

def __get_integer(MemberName):
    ValueStr = setup.__dict__[MemberName]
    if type(ValueStr) == int: return ValueStr
    result = read_integer(StringIO(ValueStr))
    if result == None:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an integer for '%s'.\n" % (ValueStr, option_name) + \
                  "Use prefix '0x' for hexadecimal numbers.\n" + \
                  "           '0o' for octal numbers.\n"       + \
                  "           '0b' for binary numbers.\n"      + \
                  "           '0r' for roman numbers.\n"      + \
                  "           and no prefix for decimal numbers.")
    return result

def __prepare_file_name(Suffix, FileStemIncludedF=False):
    global setup
    if FileStemIncludedF: 
        FileName = Suffix
    else:          
        prefix = ""
        if setup.analyzer_name_space != ["quex"]:
            for name in setup.analyzer_name_space:
                prefix += name + "_"
        FileName = prefix + setup.analyzer_class_name + Suffix

    if setup.output_directory == "": return FileName
    else:                            return os.path.normpath(setup.output_directory + "/" + FileName)

def __get_supported_command_line_option_description(NormalModeOptions):
    txt = "OPTIONS:\n"
    for option in NormalModeOptions:
        txt += "    " + option + "\n"

    txt += "\nOPTIONS FOR QUERY MODE:\n"
    txt += query.get_supported_command_line_option_description()
    return txt

