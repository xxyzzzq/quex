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

    query_f, command_line = argv_interpret(argv)

    if command_line is None: return False
    elif not query_f:        code_generation.setup(command_line, argv)
    else:                    query.run(command_line, argv)

    __extra_option_message(location_list)
    return not query_f

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

def argv_interpret(argv):
    """RETURNS:
         QueryF -- True, if quex is run in query mode.
                   False, if it is run in code generation mode.
         Setup  -- information about the command line.
    """
    command_line = GetPot(argv)

    query_f = None
    command_line.disable_loop()
    known_option_list = []
    for variable_name, info in SETUP_INFO.items():
        query_f = argv_is_query_option(variable_name)
        known_option_list.extend(info[0])

        command_line.reset_cursor()
        # Some parameters are not set on the command line. Their entry is not associated
        # with a description list.
        if type(info) != list: continue

        if info[1] == SetupParTypes.FLAG:
            setup.__dict__[variable_name] = command_line.search(info[0])        

        elif info[1] == SetupParTypes.NEGATED_FLAG:
            setup.__dict__[variable_name] = not command_line.search(info[0])        

        elif info[1] == SetupParTypes.INT_LIST:
            self.__dict__[variable_name] = argv_catch_int_list(info[0])

        elif info[1] == SetupParTypes.LIST:
            self.__dict__[variable_name] = argv_catch_list(info[0])

        elif command_line.search(info[0]):
            if not command_line.search(info[0]):
                # Set default value
                setup.__dict__[variable_name] = info[1]
                continue

            value = command_line.follow("##EMPTY##", info[0])
            if value == "##EMPTY##":
                error_msg("Option %s\nnot followed by anything." % repr(info[0])[1:-1])
            setup.__dict__[variable_name] = value

    # Handle unidentified command line options.
    argv_ufo_detections(known_option_list)

    return query_f, command_line

def argv_is_query_option(PrevQueryF, ParameterName):
    """Determines whether the setup parameter is a parameter related to 
    queries (or to code generation). If a mixed usage is detected an 
    error is issued.

    RETURN: True, if the setup parameter is query related. 
    """
    query_f = (ParameterName.find("query_") == 0)
    if PrevQueryF is None:
        return query_f
    elif PrevQueryF != query_f:
        error_msg("Mixed options: query and code generation mode.\n"
                  "The option(s) '%s' cannot be combined with preceeding options." \
                  % SETUP_INFO[ParameterName][0][1:-1])
    else:
        return query_f

def argv_catch_int_list(argv, Option):
    """RETURNS: list of integers built from the list of no-minus followers of 
    the given option.
    """
    return [
        __get_integer_core(variable_name, x)
        for x in argv_catch_list(info[0])
    ]

def argv_catch_list(argv, Option):
    """Catch the list of no-minus followers of the given option. Multiple
    occurrencies of Option are considered.

    RETURNS: list of no-minus followers.
    """
    result = []
    while 1 + 1 == 2:
        if not command_line.search(Option):
            break

        the_list = command_line.nominus_followers(Option)
        if len(the_list) == 0:
            error_msg("Option %s\nnot followed by anything." % repr(Option)[1:-1])

        for x in the_list:
            if x not in entry: 
                result.append(x)
    return result

def argv_ufo_detections(Cl, KnownOptions):
    """Detects unidentified command line options.
    """
    ufo_list = Cl.unidentified_options(KnownOptions)
    if len(ufo_list) == 0: return
    option_str = "".join("%s\n" % ufo_list)
    error_msg("Following command line options are unknown to current version of quex:\n" \
              + option_str, 
             SuppressCode=NotificationDB.error_ufo_on_command_line_f)
