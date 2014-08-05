import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.blackboard                    import setup, \
                                                 E_Compression
import quex.blackboard                    as     blackboard
from   quex.input.files.token_type        import TokenTypeDescriptorManual
from   quex.input.command_line.GetPot     import GetPot
import quex.input.command_line.validation as     validation
from   quex.input.command_line.code_generation as code_generation
from   quex.input.command_line.query      as      query     
from   quex.input.setup                   import SETUP_INFO,               \
                                                 SetupParTypes,            \
                                                 global_extension_db,      \
                                                 global_character_type_db, \
                                                 command_line_args_defined, \
                                                 command_line_arg_position, \
                                                 E_Files, \
                                                 NotificationDB

from   quex.output.cpp.token_id_maker     import parse_token_id_file

from   quex.engine.misc.file_in           import error_msg,                \
                                                 verify_word_in_list,      \
                                                 read_namespaced_name,     \
                                                 read_integer,             \
                                                 open_file_or_die
import quex.engine.codec_db.core            as   codec_db
from   quex.engine.generator.languages.core import db as output_language_db
from   quex.engine.generator.code.base      import CodeFragment

from   quex.DEFINITIONS import QUEX_VERSION

from   StringIO import StringIO
from   operator import itemgetter
import re

def do(argv):
    """RETURNS: True,  if CODE GENERATION needs to happen.
                False, if NOTHING remains to be done.
    """        
    global setup
    location_list = __extra_option_extend_argv(argv)

    query_f, command_line  = __interpret_command_line(argv)
    if command_line is None: 
        return False

    if not query_f:
        result = code_generation.setup(command_line, argv)
    else:
        result = query.run(command_line, argv)
        return False

    __extra_option_message(location_list)
    return result

def __get_float(MemberName):
    ValueStr = setup.__dict__[MemberName]
    if type(ValueStr) == float: return ValueStr
    try:
        return float(ValueStr)
    except:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an floating point number for '%s'" % (ValueStr, option_name))

def prepare_file_names(setup):
    setup.output_file_stem = ""
    if setup.analyzer_name_space != ["quex"]:
        for name in setup.analyzer_name_space:
            setup.output_file_stem += name + "_"
    setup.output_file_stem += setup.analyzer_class_name

    setup.output_code_file                       = __prepare_file_name("",               E_Files.SOURCE) 
    setup.output_header_file                     = __prepare_file_name("",               E_Files.HEADER)
    setup.output_configuration_file              = __prepare_file_name("-configuration", E_Files.HEADER)
    setup.output_token_id_file                   = __prepare_file_name("-token_ids",     E_Files.HEADER)
    setup.output_token_class_file                = __prepare_file_name("-token",         E_Files.HEADER)
    if setup.token_class_only_f == False:
        setup.output_token_class_file_implementation = __prepare_file_name("-token",     E_Files.HEADER_IMPLEMTATION)
    else:
        setup.output_token_class_file_implementation = __prepare_file_name("-token",     E_Files.SOURCE)

    if   setup.buffer_codec == "utf8":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-utf8"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-utf8.i"

    elif setup.buffer_codec == "utf16":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-utf16"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-utf16.i"

    elif setup.buffer_codec == "utf32":
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-utf32"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-utf32.i"

    elif setup.buffer_codec != "unicode":
        # Note, that the name may be set to 'None' if the conversion is utf8 or utf16
        # See Internal engine character encoding'
        setup.output_buffer_codec_header = \
            __prepare_file_name("-converter-%s" % setup.buffer_codec, E_Files.HEADER)
        setup.output_buffer_codec_header_i = \
            __prepare_file_name("-converter-%s" % setup.buffer_codec, E_Files.HEADER_IMPLEMTATION)
    else:
        setup.output_buffer_codec_header   = "quex/code_base/converter_helper/from-unicode-buffer"
        setup.output_buffer_codec_header_i = "quex/code_base/converter_helper/from-unicode-buffer.i"

def make_numbers(setup):
    setup.compression_template_min_gain = __get_integer("compression_template_min_gain")
    setup.buffer_limit_code             = __get_integer("buffer_limit_code")
    setup.path_limit_code               = __get_integer("path_limit_code")

    setup.token_id_counter_offset       = __get_integer("token_id_counter_offset")
    setup.token_queue_size              = __get_integer("token_queue_size")
    setup.token_queue_safety_border     = __get_integer("token_queue_safety_border")
    setup.buffer_element_size           = __get_integer("buffer_element_size")

    setup.suppressed_notification_list  = __get_integer_list("suppressed_notification_list")

def __get_integer(MemberName):
    return __get_integer_core(MemberName, setup.__dict__[MemberName])

def __get_integer_list(MemberName):
    return map(lambda x: __get_integer_core(MemberName, x), setup.__dict__[MemberName])

def __get_integer_core(MemberName, ValueStr):
    if type(ValueStr) == int: 
        return ValueStr
    result = read_integer(StringIO(ValueStr))
    if result is None:
        option_name = repr(SETUP_INFO[MemberName][0])[1:-1]
        error_msg("Cannot convert '%s' into an integer for '%s'.\n" % (ValueStr, option_name) + \
                  "Use prefix '0x' for hexadecimal numbers.\n" + \
                  "           '0o' for octal numbers.\n"       + \
                  "           '0b' for binary numbers.\n"      + \
                  "           '0r' for roman numbers.\n"      + \
                  "           and no prefix for decimal numbers.")
    return result

def __prepare_file_name(Suffix, ContentType):
    global setup
    assert ContentType in E_Files

    # Language + Extenstion Scheme + ContentType --> name of extension
    ext = setup.extension_db[setup.output_file_naming_scheme][ContentType]

    file_name = setup.output_file_stem + Suffix + ext

    if setup.output_directory == "": return file_name
    else:                            return os.path.normpath(setup.output_directory + "/" + file_name)

def __setup_analyzer_class(setup):
    """ X0::X1::X2::ClassName --> analyzer_class_name = ClassName
                                  analyzer_name_space = ["X0", "X1", "X2"]
        ::ClassName --> analyzer_class_name = ClassName
                        analyzer_name_space = []
        ClassName --> analyzer_class_name = ClassName
                      analyzer_name_space = ["quex"]
    """
    if setup.analyzer_class.find("::") == -1:
        setup.analyzer_class = "quex::%s" % setup.analyzer_class

    setup.analyzer_class_name, \
    setup.analyzer_name_space, \
    setup.analyzer_name_safe   = \
         read_namespaced_name(setup.analyzer_class, 
                              "analyzer class (options -o, --analyzer-class)")

    if setup.show_name_spaces_f:
        print "Analyzer: {"
        print "     class_name:  %s;" % setup.analyzer_class_name
        print "     name_space:  %s;" % repr(setup.analyzer_name_space)[1:-1]
        print "     name_prefix: %s;" % setup.analyzer_name_safe   
        print "}"

    setup.analyzer_derived_class_name,       \
    setup.analyzer_derived_class_name_space, \
    setup.analyzer_derived_class_name_safe = \
         read_namespaced_name(setup.analyzer_derived_class_name, 
                              "derived analyzer class (options --derived-class, --dc)",
                              AllowEmptyF=True)

def __setup_lexeme_null(setup):
    if len(setup.external_lexeme_null_object) != 0:
        lexeme_null_object = setup.external_lexeme_null_object
        default_name_space = setup.analyzer_name_space
    elif setup.token_class_only_f:
        lexeme_null_object = "LexemeNullObject"
        default_name_space = setup.token_class_name_space
    else:
        lexeme_null_object = "LexemeNullObject"
        default_name_space = setup.analyzer_name_space

    if lexeme_null_object.find("::") == -1:
        # By default, setup the token in the analyzer's namespace
        if len(setup.analyzer_name_space) != 0:
            name_space = reduce(lambda x, y: "%s::%s" % (x, y), default_name_space)
        else:
            name_space = ""
        lexeme_null_object = "%s::%s" % (name_space, lexeme_null_object)

    setup.lexeme_null_name,        \
    setup.lexeme_null_namespace,   \
    setup.lexeme_null_name_safe  = \
         read_namespaced_name(lexeme_null_object, 
                              "lexeme null object (options --lexeme-null-object, --lno)")
    setup.lexeme_null_full_name_cpp = "::" 
    for name in setup.lexeme_null_namespace:
        setup.lexeme_null_full_name_cpp += name + "::"
    setup.lexeme_null_full_name_cpp += setup.lexeme_null_name

def __setup_token_class(setup):
    """ X0::X1::X2::ClassName --> token_class_name = ClassName
                                  token_name_space = ["X0", "X1", "X2"]
        ::ClassName --> token_class_name = ClassName
                        token_name_space = []
        ClassName --> token_class_name = ClassName
                      token_name_space = analyzer_name_space
    """
    if setup.token_class.find("::") == -1:
        # By default, setup the token in the analyzer's namespace
        if len(setup.analyzer_name_space) != 0:
            analyzer_name_space = reduce(lambda x, y: "%s::%s" % (x, y), setup.analyzer_name_space)
        else:
            analyzer_name_space = ""
        setup.token_class = "%s::%s" % (analyzer_name_space, setup.token_class)

    # Token classes and derived classes have the freedom not to open a namespace,
    # thus no check 'if namespace == empty'.
    setup.token_class_name,       \
    setup.token_class_name_space, \
    setup.token_class_name_safe = \
         read_namespaced_name(setup.token_class, 
                              "token class (options --token-class, --tc)")

    if setup.show_name_spaces_f:
        print "Token: {"
        print "     class_name:  %s;" % setup.token_class_name
        print "     name_space:  %s;" % repr(setup.token_class_name_space)[1:-1]
        print "     name_prefix: %s;" % setup.token_class_name_safe   
        print "}"

    if setup.token_class_file != "":
        blackboard.token_type_definition = \
                TokenTypeDescriptorManual(setup.token_class_file,
                                          setup.token_class_name,
                                          setup.token_class_name_space,
                                          setup.token_class_name_safe,
                                          setup.token_id_type)

    #if len(setup.token_class_name_space) == 0:
    #    setup.token_class_name_space = deepcopy(setup.analyzer_name_space)

def __setup_token_id_prefix(setup):
    setup.token_id_prefix_plain,      \
    setup.token_id_prefix_name_space, \
    dummy                           = \
         read_namespaced_name(setup.token_id_prefix, 
                              "token prefix (options --token-id-prefix)", 
                              AllowEmptyF=True)

    if len(setup.token_id_prefix_name_space) != 0 and setup.language.upper() == "C":
         error_msg("Token id prefix cannot contain a namespaces if '--language' is set to 'C'.")

def __extra_option_extend_argv(argv):
    """Checks for source files mentioned in the command line. Some may
    contain sections that extend the command line. If so, the command line
    options are parsed and added to 'argv'.

    Details in '__extra_option_extract_from_file()'.
    """
    extra_location_list = []
    try:    
        idx = argv.index("--token-class-file")
        if idx + 1 < len(argv): idx += 1
        else:                   idx  = None
    except: 
        idx = None 

    if idx is None:
        # No file with extra command line options.
        return

    extra_argv, extra_location_list = __extra_option_extract_from_file(argv[idx])
    if extra_argv is None: 
        # No extra option in file. 
        return

    argv.extend(extra_argv)
    return extra_location_list

def __extra_option_extract_from_file(FileName):
    """Extract an option section from a given file. The quex command line 
       options may be given in a section surrounded by '<<<QUEX-OPTIONS>>>'
       markers. For example:

           <<<QUEX-OPTIONS>>>
              --token-class-file      Common-token
              --token-class           Common::Token
              --token-id-type         uint32_t
              --buffer-element-type   uint8_t
              --lexeme-null-object    ::Common::LexemeNullObject
              --foreign-token-id-file Common-token_ids
           <<<QUEX-OPTIONS>>>

       This function extracts those options and builds a new 'argv' array, i.e.
       an array of strings are if they would come from the command line.
    """
    MARKER = "<<<QUEX-OPTIONS>>>"
    fh     = open_file_or_die(FileName)

    while 1 + 1 == 2:
        line = fh.readline()
        if line == "":
            return None, [] # Simply no starting marker has been found
        elif line.find(MARKER) != -1: 
            pos = fh.tell()
            break

    result = []
    location_list = []

    line_n = 0
    while 1 + 1 == 2:
        line_n += 1
        line    = fh.readline()
        if line == "":
            fh.seek(pos)
            error_msg("Missing terminating '%s'." % MARKER, fh)

        if line.find(MARKER) != -1: 
            break
        
        idx = line.find("-")
        if idx == -1: continue
        options = line[idx:].split()

        location_list.append((SourceRef(FileName, line_n), options))
        result.extend(options)

    if len(result) == 0: return None, location_list

    return result, location_list

def __extra_option_message(ExtraLocationList):
    if NotificationDB.message_on_extra_options in setup.suppressed_notification_list:
        return
    elif len(ExtraLocationList) == 0:
        return

    error_msg("Command line arguments from inside files:", sr, NoteF=True)
    for sr, option in ExtraLocationList:
        if len(option) < 2: option_str = option[0]
        else:               option_str = reduce(lambda x, y: "%s %s" % (x.strip(), y.strip()), option)
        error_msg("%s" % option_str, sr, NoteF=True)
    error_msg("", file_name, LineN=line_n, NoteF=True, SuppressCode=NotificationDB.message_on_extra_options)

def __interpret_command_line(argv):
    """RETURNS:
         QueryF -- True, if quex is run in query mode.
                   False, if it is run in code generation mode.
         Setup  -- information about the command line.
    """
    command_line = GetPot(argv)

    if command_line.search("--version", "-v"):
        print "Quex - Fast Universal Lexical Analyzer Generator"
        print "Version " + QUEX_VERSION
        print "(C) 2005-2013 Frank-Rene Schaefer"
        print "ABSOLUTELY NO WARRANTY"
        return True, None

    if command_line.search("--help", "-h"):
        print "Quex - Fast Universal Lexical Analyzer Generator"
        print "Please, consult the quex documentation for further help, or"
        print "visit http://quex.org"
        print "(C) 2005-2013 Frank-Rene Schaefer"
        print "ABSOLUTELY NO WARRANTY"
        return True, None

    def is_query_option(MemberName):
        return MemberName.find("query_") == 0

    query_f = None
    command_line.disable_loop()
    for variable_name, info in SETUP_INFO.items():
        if    (query_f == True  and not is_query_option(variable_name)) \
           or (query_f == False and     is_query_option(variable_name)):
            error_msg("Mixed options: query and code generation mode.")
        elif query_f is not None:
            query_f = is_query_option(variable_name)

        command_line.reset_cursor()
        # Some parameters are not set on the command line. Their entry is not associated
        # with a description list.
        if type(info) != list: continue

        if info[1] == SetupParTypes.FLAG:
            setup.__dict__[variable_name] = command_line.search(info[0])        

        elif info[1] == SetupParTypes.NEGATED_FLAG:
            setup.__dict__[variable_name] = not command_line.search(info[0])        

        elif info[1] == SetupParTypes.LIST:
            setup.__dict__[variable_name] = []
            entry = setup.__dict__.get(variable_name)
            while 1 + 1 == 2:
                if not command_line.search(info[0]):
                    break

                the_list = command_line.nominus_followers(info[0])
                if len(the_list) == 0:
                    error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])

                for x in the_list:
                    if x not in entry: 
                        entry.append(x)

        elif command_line.search(info[0]):
            if not command_line.search(info[0]):
                # Set default value
                setup.__dict__[variable_name] = info[1]
                continue

            value = command_line.follow("##EMPTY##", info[0])
            if value == "##EMPTY##":
                error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])
            setup.__dict__[variable_name] = value

    return query_f, command_line

def __compile_regular_expression(Str, Name):
    tmp = Str.replace("*", "\\*")
    tmp = tmp.replace("?", "\\?")
    tmp = tmp.replace("{", "\\{")
    tmp = tmp.replace("}", "\\}")
    try:
        return re.compile(tmp)
    except:
        error_msg("Invalid %s: %s" % (Name, Str))

