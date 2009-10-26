#! /usr/bin/env python
import os
from copy import copy
import time

from quex.frs_py.string_handling import blue_print
from quex.frs_py.file_in  import open_file_or_die, \
                                 write_safely_and_close, \
                                 get_include_guard_extension, \
                                 make_safe_identifier

import quex.lexer_mode              as lexer_mode
import quex.output.cpp.mode_classes as mode_classes
from   quex.input.setup             import setup as Setup

LanguageDB = Setup.language_db


def do(Modes, IndentationSupportF):
    assert lexer_mode.token_type_definition != None

    write_engine_header(Modes)
    write_configuration_header(Modes, IndentationSupportF)
    write_mode_class_implementation(Modes)

def write_configuration_header(Modes, IndentationSupportF):
    OutputConfigurationFile   = Setup.output_configuration_file
    LexerClassName            = Setup.analyzer_class_name
    ConfigurationTemplateFile = (Setup.QUEX_TEMPLATE_DB_DIR 
                                   + "/analyzer/configuration/CppTemplate.txt").replace("//","/")

    fh  = open_file_or_die(ConfigurationTemplateFile)
    txt = fh.read()

    # -- check if exit/entry handlers have to be active
    entry_handler_active_f = False
    exit_handler_active_f = False
    for mode in Modes.values():
        if mode.get_code_fragment_list("on_entry") != []: entry_handler_active_f = True
        if mode.get_code_fragment_list("on_exit") != []:  exit_handler_active_f = True

    # Buffer filler converter (0x0 means: no buffer filler converter)
    converter_new_str = "#   define QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW " 
    if Setup.converter_user_new_func != "": 
        converter_new_str += Setup.converter_user_new_func + "()"
        user_defined_converter_f = True
    else: 
        converter_new_str = "/* " + converter_new_str + " */"
        user_defined_converter_f = False

    # -- determine character type according to number of bytes per ucs character code point
    #    for the internal engine.
    quex_character_type_str = { 1: "uint8_t ", 2: "uint16_t", 4: "uint32_t", 
                                   "wchar_t": "wchar_t" }[Setup.bytes_per_ucs_code_point]

    txt = __switch(txt, "QUEX_OPTION_COLUMN_NUMBER_COUNTING",        True)        
    txt = __switch(txt, "QUEX_OPTION_DEBUG_MODE_TRANSITIONS",        Setup.output_debug_f)
    txt = __switch(txt, "QUEX_OPTION_DEBUG_QUEX_PATTERN_MATCHES",    Setup.output_debug_f)
    txt = __switch(txt, "QUEX_OPTION_DEBUG_TOKEN_SENDING",           Setup.output_debug_f)
    txt = __switch(txt, "QUEX_OPTION_ENABLE_ICONV",                  Setup.converter_iconv_f)
    txt = __switch(txt, "QUEX_OPTION_ENABLE_ICU",                    Setup.converter_icu_f)
    txt = __switch(txt, "QUEX_OPTION_INCLUDE_STACK",                 Setup.include_stack_support_f)
    txt = __switch(txt, "QUEX_OPTION_LINE_NUMBER_COUNTING",          True)      
    txt = __switch(txt, "QUEX_OPTION_POST_CATEGORIZER",              Setup.post_categorizer_f)
    txt = __switch(txt, "QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK", Setup.mode_transition_check_f)
    txt = __switch(txt, "QUEX_OPTION_STRING_ACCUMULATOR",            Setup.string_accumulator_f)
    txt = __switch(txt, "QUEX_OPTION_TOKEN_POLICY_QUEUE",            Setup.token_policy == "queue")
    txt = __switch(txt, "QUEX_OPTION_TOKEN_POLICY_USERS_QUEUE",      Setup.token_policy == "users_queue")
    txt = __switch(txt, "QUEX_OPTION_TOKEN_POLICY_USERS_TOKEN",      Setup.token_policy == "users_token")
    txt = __switch(txt, "__QUEX_OPTION_BIG_ENDIAN",                  Setup.byte_order == "big")
    txt = __switch(txt, "__QUEX_OPTION_CONVERTER_ENABLED",           user_defined_converter_f )
    txt = __switch(txt, "__QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT", IndentationSupportF)     
    txt = __switch(txt, "__QUEX_OPTION_LITTLE_ENDIAN",               Setup.byte_order == "little")
    txt = __switch(txt, "__QUEX_OPTION_ON_ENTRY_HANDLER_PRESENT",    entry_handler_active_f)
    txt = __switch(txt, "__QUEX_OPTION_ON_EXIT_HANDLER_PRESENT",     exit_handler_active_f)
    txt = __switch(txt, "__QUEX_OPTION_SUPPORT_BEGIN_OF_LINE_PRE_CONDITION",  True)
    txt = __switch(txt, "__QUEX_OPTION_SYSTEM_ENDIAN",               Setup.byte_order_is_that_of_current_system_f)

    # -- token class related definitions
    token_descr = lexer_mode.token_type_definition
    token_namespace_plain_str = make_safe_identifier(LanguageDB["$namespace-ref"](token_descr.name_space))

    txt = blue_print(txt, 
            [["$$BUFFER_LIMIT_CODE$$",          "0x%X" % Setup.buffer_limit_code],
             ["$$INCLUDE_GUARD_EXTENSION$$",    get_include_guard_extension(
                                                         LanguageDB["$namespace-ref"](Setup.analyzer_name_space) 
                                                             + "__" + Setup.analyzer_class_name)],
             ["$$QUEX_TYPE_CHARACTER$$",        quex_character_type_str],
             ["$$TOKEN_QUEUE_SAFETY_BORDER$$",  repr(Setup.token_queue_safety_border)],
             ["$$INITIAL_LEXER_MODE_ID$$",      LexerClassName + "_QuexModeID_" + lexer_mode.initial_mode.get_pure_code()],
             ["$$MAX_MODE_CLASS_N$$",           repr(len(Modes))],
             ["$$LEXER_CLASS_NAME$$",           LexerClassName],
             ["$$LEXER_DERIVED_CLASS_NAME$$",   Setup.analyzer_derived_class_name],
             ["$$TOKEN_CLASS$$",                token_descr.class_name],
             ["$$TOKEN_ID_TYPE$$",              token_descr.token_id_type.get_pure_code()],
             ["$$TOKEN_TYPE_STR$$",             token_namespace_plain_str + "__" + token_descr.class_name],
             ["$$TOKEN_QUEUE_SIZE$$",           repr(Setup.token_queue_size)],
             ["$$NAMESPACE_MAIN$$",             LanguageDB["$namespace-ref"](Setup.analyzer_name_space)[:-2]],
             ["$$NAMESPACE_MAIN_OPEN$$",        LanguageDB["$namespace-open"](Setup.analyzer_name_space).replace("\n", "\\\n")],
             ["$$NAMESPACE_MAIN_CLOSE$$",       LanguageDB["$namespace-close"](Setup.analyzer_name_space).replace("\n", "\\\n")],
             ["$$NAMESPACE_TOKEN$$",            LanguageDB["$namespace-ref"](token_descr.name_space)],
             ["$$NAMESPACE_TOKEN_OPEN$$",       LanguageDB["$namespace-open"](token_descr.name_space).replace("\n", "\\\n")],
             ["$$NAMESPACE_TOKEN_CLOSE$$",      LanguageDB["$namespace-close"](token_descr.name_space).replace("\n", "\\\n")],
             ["$$TOKEN_LINE_N_TYPE$$",          token_descr.line_number_type.get_pure_code()],
             ["$$TOKEN_COLUMN_N_TYPE$$",        token_descr.column_number_type.get_pure_code()],
             ["$$TOKEN_PREFIX$$",               Setup.token_id_prefix],
             ["$$QUEX_SETTING_BUFFER_FILLERS_CONVERTER_NEW$$", converter_new_str]])

    write_safely_and_close(OutputConfigurationFile, txt)

def __switch(txt, Name, SwitchF):
    if SwitchF: txt = txt.replace("$$SWITCH$$ %s" % Name, "#define    %s" % Name)
    else:       txt = txt.replace("$$SWITCH$$ %s" % Name, "/* #define %s */" % Name)
    return txt
    
def write_engine_header(Modes):

    QuexClassHeaderFileTemplate = (Setup.QUEX_TEMPLATE_DB_DIR 
                                   + "/analyzer/CppTemplate.txt").replace("//","/")
    CoreEngineDefinitionsHeader = (Setup.QUEX_TEMPLATE_DB_DIR + "/core_engine/").replace("//","/")
    QuexClassHeaderFileOutput   = Setup.output_file_stem
    LexerFileStem               = Setup.output_file_stem
    LexerClassName              = Setup.analyzer_class_name
    VersionID                   = Setup.user_application_version_id
    QuexVersionID               = Setup.QUEX_VERSION

    #    are bytes of integers Setup 'little endian' or 'big endian' ?
    if Setup.byte_order == "little":
        quex_coding_name_str = { 1: "ASCII", 2: "UCS-2LE", 4: "UCS-4LE", 
                                    "wchar_t": "WCHAR_T" }[Setup.bytes_per_ucs_code_point]
    else:
        quex_coding_name_str = { 1: "ASCII", 2: "UCS-2BE", 4: "UCS-4BE", 
                                    "wchar_t": "WCHAR_T" }[Setup.bytes_per_ucs_code_point]

    mode_id_definition_str = "" 
    # NOTE: First mode-id needs to be '1' for compatibility with flex generated engines
    i = -1
    for name in Modes.keys():
        i += 1
        mode_id_definition_str += "const int %s_QuexModeID_%s = %i;\n" % (LexerClassName, name, i)

    # -- instances of mode classes as members of the lexer
    mode_object_members_txt,     \
    constructor_txt,             \
    mode_specific_functions_txt, \
    friend_txt =                 \
         get_mode_class_related_code_fragments(Modes.values(), LexerClassName)

    # -- define a pointer that directly has the type of the derived class
    if Setup.analyzer_derived_class_name == "":
        Setup.analyzer_derived_class_name = LexerClassName
        derived_class_type_declaration = ""
    else:
        derived_class_type_declaration = "class %s;" % Setup.analyzer_derived_class_name

    fh = open_file_or_die(QuexClassHeaderFileTemplate)
    template_code_txt = fh.read()
    fh.close()


    token_class_file_name = lexer_mode.token_type_definition.get_file_name()

    txt = template_code_txt
    txt = blue_print(txt,
            [
                ["$$CONSTRUCTOR_EXTENSTION$$",                  lexer_mode.class_constructor_extension.get_code()],
                ["$$CONSTRUCTOR_MODE_DB_INITIALIZATION_CODE$$", constructor_txt],
                ["$$CORE_ENGINE_DEFINITIONS_HEADER$$",          CoreEngineDefinitionsHeader],
                ["$$CLASS_BODY_EXTENSION$$",         lexer_mode.class_body_extension.get_code()],
                ["$$INCLUDE_GUARD_EXTENSION$$",      get_include_guard_extension(
                                                         LanguageDB["$namespace-ref"](Setup.analyzer_name_space) 
                                                             + "__" + Setup.analyzer_class_name)],
                ["$$LEXER_BUILD_DATE$$",             time.asctime()],
                ["$$USER_LEXER_VERSION$$",               VersionID],
                ["$$LEXER_CLASS_NAME$$",                 LexerClassName],
                ["$$LEXER_CONFIG_FILE$$",                Setup.output_configuration_file],
                ["$$LEXER_DERIVED_CLASS_DECL$$",         derived_class_type_declaration],
                ["$$LEXER_DERIVED_CLASS_NAME$$",         Setup.analyzer_derived_class_name],
                ["$$QUEX_MODE_ID_DEFINITIONS$$",         mode_id_definition_str],
                ["$$MODE_CLASS_FRIENDS$$",               friend_txt],
                ["$$MODE_OBJECTS$$",                     mode_object_members_txt],
                ["$$MODE_SPECIFIC_ANALYSER_FUNCTIONS$$", mode_specific_functions_txt],
                ["$$MEMENTO_EXTENSIONS$$",               lexer_mode.memento_class_extension.get_code()],
                ["$$MEMENTO_EXTENSIONS_PACK$$",          lexer_mode.memento_pack_extension.get_code()],
                ["$$MEMENTO_EXTENSIONS_UNPACK$$",        lexer_mode.memento_unpack_extension.get_code()],
                ["$$PRETTY_INDENTATION$$",               "     " + " " * (len(LexerClassName)*2 + 2)],
                ["$$QUEX_TEMPLATE_DIR$$",                Setup.QUEX_TEMPLATE_DB_DIR],
                ["$$QUEX_VERSION$$",                     QuexVersionID],
                ["$$TOKEN_CLASS_DEFINITION_FILE$$",      token_class_file_name.replace("//", "/")],
                ["$$TOKEN_CLASS_DECLARATION$$",          write_token_class_declaration()],
                ["$$TOKEN_ID_DEFINITION_FILE$$",         Setup.output_token_id_file.replace("//","/")],
                ["$$CORE_ENGINE_CHARACTER_CODING$$",     quex_coding_name_str],
                ["$$USER_DEFINED_HEADER$$",              lexer_mode.header.get_code() + "\n"],
             ])

    write_safely_and_close(QuexClassHeaderFileOutput, txt)

def write_token_class_declaration():
    
    # A valid token_type_definition must have been parsed at this point
    assert lexer_mode.token_type_definition != None
    namespace  = lexer_mode.token_type_definition.name_space
    class_name = lexer_mode.token_type_definition.class_name

    txt  = LanguageDB["$namespace-open"](namespace)
    txt += "class %s;\n" % class_name
    txt += LanguageDB["$namespace-close"](namespace)
    return txt

def write_mode_class_implementation(Modes):
    LexerClassName              = Setup.analyzer_class_name
    TokenClassName              = Setup.token_class_name
    OutputFilestem              = Setup.output_file_stem
    DerivedClassName            = Setup.analyzer_derived_class_name
    DerivedClassHeaderFileName  = Setup.analyzer_derived_class_file
    ModeClassImplementationFile = Setup.output_code_file

    if DerivedClassHeaderFileName != "": txt = "#include<" + DerivedClassHeaderFileName +">\n"
    else:                                txt = "#include\"" + OutputFilestem +"\"\n"
    
    # -- mode class member function definitions (on_entry, on_exit, has_base, ...)
    mode_class_member_functions_txt = mode_classes.do(Modes.values()).replace("$$CLASS$$", LexerClassName)

    mode_objects_txt = ""    
    for mode_name in Modes:
        mode_objects_txt += "        QUEX_TYPE_MODE  $$LEXER_CLASS_NAME$$::%s;\n" % mode_name

    txt += "namespace quex {\n"
    txt += mode_objects_txt
    txt += mode_class_member_functions_txt
    txt += "} // END: namespace quex\n"

    txt = blue_print(txt, [["$$LEXER_CLASS_NAME$$",         LexerClassName],
                           ["$$LEXER_DERIVED_CLASS_NAME$$", DerivedClassName]])
    
    write_safely_and_close(ModeClassImplementationFile, txt)

quex_mode_init_call_str = """
     me->$$MN$$.id   = $$CLASS$$_QuexModeID_$$MN$$;
     me->$$MN$$.name = "$$MN$$";
     me->$$MN$$.analyzer_function = $analyzer_function;
#    ifdef __QUEX_OPTION_INDENTATION_TRIGGER_SUPPORT    
     me->$$MN$$.on_indentation = $on_indentation;
#    endif
     me->$$MN$$.on_entry       = $on_entry;
     me->$$MN$$.on_exit        = $on_exit;
#    ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK
     me->$$MN$$.has_base       = $has_base;
     me->$$MN$$.has_entry_from = $has_entry_from;
     me->$$MN$$.has_exit_to    = $has_exit_to;
#    endif
"""

def __get_mode_init_call(mode, LexerClassName):
    
    header_str = "%s_%s_" % (LexerClassName, mode.name)

    analyzer_function = header_str + "analyzer_function" 
    on_indentation    = header_str + "on_indentation"    
    on_entry          = header_str + "on_entry"          
    on_exit           = header_str + "on_exit"           
    has_base          = header_str + "has_base"          
    has_entry_from    = header_str + "has_entry_from"    
    has_exit_to       = header_str + "has_exit_to"       

    if mode.options["inheritable"] == "only": 
        analyzer_function = "QuexMode_uncallable_analyzer_function"

    if mode.get_code_fragment_list("on_entry") == []:
        on_entry = "QuexMode_on_entry_exit_null_function"

    if mode.get_code_fragment_list("on_exit") == []:
        on_exit = "QuexMode_on_entry_exit_null_function"

    if mode.get_code_fragment_list("on_indentation") == []:
        on_indentation = "QuexMode_on_indentation_null_function"

    txt = blue_print(quex_mode_init_call_str,
                [["$$MN$$",             mode.name],
                 ["$$CLASS$$",          LexerClassName],
                 ["$analyzer_function", analyzer_function],
                 ["$on_indentation",    on_indentation],
                 ["$on_entry",          on_entry],
                 ["$on_exit",           on_exit],
                 ["$has_base",          has_base],
                 ["$has_entry_from",    has_entry_from],
                 ["$has_exit_to",       has_exit_to]])

    return txt

def __get_mode_function_declaration(Modes, LexerClassName, FriendF=False):

    if FriendF: prolog = "        friend "
    else:       prolog = "    extern "

    def __mode_functions(Prolog, ReturnType, NameList, ArgList):
        txt = ""
        for name in NameList:
            function_signature = "%s %s_%s_%s(%s);" % \
                     (ReturnType, LexerClassName, mode.name, name, ArgList)
            txt += "%s" % Prolog + "    " + function_signature + "\n"

        return txt

    txt = ""
    for mode in Modes:
        if mode.options["inheritable"] != "only":
            txt += __mode_functions(prolog, "void", ["analyzer_function"],
                                    "QUEX_TYPE_ANALYZER_DATA*")
    for mode in Modes:
        if mode.has_code_fragment_list("on_indentation"):
            txt += __mode_functions(prolog, "void", ["on_indentation"], 
                                    "QUEX_TYPE_ANALYZER_DATA*, const int")

    for mode in Modes:
        for event_name in ["on_exit", "on_entry"]:
            if not mode.has_code_fragment_list(event_name): continue
            txt += __mode_functions(prolog, "void", [event_name], 
                                    "QUEX_TYPE_ANALYZER_DATA*, const QuexMode*")

    txt += "#ifdef __QUEX_OPTION_RUNTIME_MODE_TRANSITION_CHECK\n"
    for mode in Modes:
        txt += __mode_functions(prolog, "bool", ["has_base", "has_entry_from", "has_exit_to"], 
                                "const QUEX_TYPE_MODE*")
        
    txt += "#endif\n"
    txt += "\n"

    return txt

def get_mode_class_related_code_fragments(Modes, LexerClassName):
    """
       RETURNS:  -- members of the lexical analyzer class for the mode classes
                 -- static member functions declaring the analyzer functions for he mode classes 
                 -- constructor init expressions (before '{'),       
                 -- constructor text to be executed at construction time 
                 -- friend declarations for the mode classes/functions

    """

    L = max(map(lambda m: len(m.name), Modes))

    members_txt = ""    
    for mode in Modes:
        members_txt += "        static QUEX_TYPE_MODE  %s;\n" % mode.name

    # constructor code
    txt = ""
    for mode in Modes:
        txt += "        __quex_assert(%s_QuexModeID_%s %s< %i);\n" % \
               (LexerClassName, mode.name, " " * (L-len(mode.name)), len(Modes))

    for mode in Modes:
        txt += __get_mode_init_call(mode, LexerClassName)

    for mode in Modes:
        txt += "        me->mode_db[%s_QuexModeID_%s]%s = &me->%s;\n" % \
               (LexerClassName, mode.name, " " * (L-len(mode.name)), mode.name)

    constructor_txt = txt

    mode_functions_txt = __get_mode_function_declaration(Modes, LexerClassName, FriendF=False)
    friends_txt        = __get_mode_function_declaration(Modes, LexerClassName, FriendF=True)

    return members_txt,        \
           constructor_txt,    \
           mode_functions_txt, \
           friends_txt


