#! /usr/bin/env python
import os

import quex.output.cpp.mode_classes     as     mode_classes
from   quex.engine.misc.string_handling import blue_print
from   quex.engine.misc.file_operations import get_file_content_or_die
from   quex.engine.misc.file_in         import get_include_guard_extension
from   quex.DEFINITIONS                 import QUEX_PATH, QUEX_VERSION
import quex.blackboard                  as     blackboard
from   quex.blackboard                  import setup as Setup, \
                                               Lng, \
                                               E_IncidenceIDs

def do(ModeDB):
    assert blackboard.token_type_definition is not None
    

    QuexClassHeaderFileTemplate = os.path.normpath(  QUEX_PATH
                                                   + Lng["$code_base"] 
                                                   + Lng["$analyzer_template_file"]).replace("//","/")
    LexerClassName = Setup.analyzer_class_name

    quex_converter_coding_name_str = Setup.converter_ucs_coding_name

    mode_id_definition_str = mode_classes.mode_id_definition(ModeDB)

    # -- instances of mode classes as members of the lexer
    mode_object_members_txt,     \
    mode_specific_functions_txt, \
    friend_txt                   = mode_classes.get_related_code_fragments(ModeDB)

    # -- define a pointer that directly has the type of the derived class
    if Setup.analyzer_derived_class_name != "":
        analyzer_derived_class_name    = Setup.analyzer_derived_class_name
        derived_class_type_declaration = "class %s;" % Setup.analyzer_derived_class_name
    else:
        analyzer_derived_class_name    = Setup.analyzer_class_name
        derived_class_type_declaration = ""

    token_class_file_name = blackboard.token_type_definition.get_file_name()
    token_class_name      = blackboard.token_type_definition.class_name
    token_class_name_safe = blackboard.token_type_definition.class_name_safe

    template_code_txt = get_file_content_or_die(QuexClassHeaderFileTemplate)

    include_guard_ext = get_include_guard_extension(
            Lng.NAMESPACE_REFERENCE(Setup.analyzer_name_space) 
            + "__" + Setup.analyzer_class_name)

    if len(Setup.token_id_foreign_definition_file) != 0:
        token_id_definition_file = Setup.token_id_foreign_definition_file
    else:
        token_id_definition_file = Setup.output_token_id_file

    lexer_name_space_safe = get_include_guard_extension(Lng.NAMESPACE_REFERENCE(Setup.analyzer_name_space))

    txt = blue_print(template_code_txt,
            [
                ["$$___SPACE___$$",                      " " * (len(LexerClassName) + 1)],
                ["$$CLASS_BODY_EXTENSION$$",             Lng.SOURCE_REFERENCED(blackboard.class_body_extension)],
                ["$$CONVERTER_HELPER$$",                 Setup.get_file_reference(Setup.output_buffer_codec_header)],
                ["$$INCLUDE_GUARD_EXTENSION$$",          include_guard_ext],
                ["$$LEXER_CLASS_NAME$$",                 LexerClassName],
                ["$$LEXER_NAME_SPACE$$",                 lexer_name_space_safe],
                ["$$LEXER_CLASS_NAME_SAFE$$",            Setup.analyzer_name_safe],
                ["$$LEXER_CONFIG_FILE$$",                Setup.get_file_reference(Setup.output_configuration_file)],
                ["$$LEXER_DERIVED_CLASS_DECL$$",         derived_class_type_declaration],
                ["$$LEXER_DERIVED_CLASS_NAME$$",         analyzer_derived_class_name],
                ["$$QUEX_MODE_ID_DEFINITIONS$$",         mode_id_definition_str],
                ["$$MEMENTO_EXTENSIONS$$",               Lng.SOURCE_REFERENCED(blackboard.memento_class_extension)],
                ["$$MODE_CLASS_FRIENDS$$",               friend_txt],
                ["$$MODE_OBJECTS$$",                     mode_object_members_txt],
                ["$$MODE_SPECIFIC_ANALYSER_FUNCTIONS$$", mode_specific_functions_txt],
                ["$$PRETTY_INDENTATION$$",               "     " + " " * (len(LexerClassName)*2 + 2)],
                ["$$QUEX_TEMPLATE_DIR$$",                QUEX_PATH + Lng["$code_base"]],
                ["$$QUEX_VERSION$$",                     QUEX_VERSION],
                ["$$TOKEN_CLASS_DEFINITION_FILE$$",      Setup.get_file_reference(token_class_file_name)],
                ["$$TOKEN_CLASS$$",                      token_class_name],
                ["$$TOKEN_CLASS_NAME_SAFE$$",            token_class_name_safe],
                ["$$TOKEN_ID_DEFINITION_FILE$$",         Setup.get_file_reference(token_id_definition_file)],
                ["$$CORE_ENGINE_CHARACTER_CODING$$",     quex_converter_coding_name_str],
                ["$$USER_DEFINED_HEADER$$",              Lng.SOURCE_REFERENCED(blackboard.header) + "\n"],
             ])

    return txt

def do_implementation(ModeDB):

    FileTemplate = os.path.normpath(QUEX_PATH
                                    + Lng["$code_base"] 
                                    + "/analyzer/TXT-Cpp.i")
    func_txt = get_file_content_or_die(FileTemplate)

    func_txt = blue_print(func_txt,
            [
                ["$$CONSTRUCTOR_EXTENSTION$$",                  Lng.SOURCE_REFERENCED(blackboard.class_constructor_extension)],
                ["$$CONVERTER_HELPER_I$$",                      Setup.get_file_reference(Setup.output_buffer_codec_header_i)],
                ["$$CONSTRUCTOR_MODE_DB_INITIALIZATION_CODE$$", get_constructor_code(ModeDB)],
                ["$$RESET_EXTENSIONS$$",                        Lng.SOURCE_REFERENCED(blackboard.reset_extension)],
                ["$$MEMENTO_EXTENSIONS_PACK$$",                 Lng.SOURCE_REFERENCED(blackboard.memento_pack_extension)],
                ["$$MEMENTO_EXTENSIONS_UNPACK$$",               Lng.SOURCE_REFERENCED(blackboard.memento_unpack_extension)],
                ])
    return func_txt

def get_constructor_code(ModeDb):
    L = max(map(lambda m: len(m.name), ModeDb.itervalues()))

    return "".join(
        "    __quex_assert(QUEX_NAME(mode_db)[QUEX_NAME(ModeID_%s)] %s== &QUEX_NAME(%s));\n" % \
        (mode.name, " " * (L-len(mode.name)), mode.name)
        for mode in ModeDb.values() if not mode.abstract_f()
    )

