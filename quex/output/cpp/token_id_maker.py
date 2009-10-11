#! /usr/bin/env python
import time
import os
import sys
import re

from quex.GetPot import GetPot

from quex.frs_py.file_in  import open_file_or_die, \
                                 write_safely_and_close, \
                                 delete_comment, \
                                 extract_identifiers_with_specific_prefix, \
                                 get_include_guard_extension
import quex.lexer_mode             as lexer_mode
from   quex.frs_py.string_handling import blue_print
from   quex.input.setup            import setup as Setup

LanguageDB = Setup.language_db

class TokenInfo:
    def __init__(self, Name, ID, TypeName=None, Filename="", LineN=-1):
        self.name         = Name
        self.number       = ID
        self.related_type = TypeName
        self.positions    = [ Filename, LineN ]
        self.id           = None

file_str = \
"""// -*- C++ -*- vim: set syntax=cpp:
// PURPOSE: File containing definition of token-identifier and
//          a function that maps token identifiers to a string
//          name.
//
// NOTE: This file has been created automatically by a
//       quex program.
//
// DATE: $$DATE$$
//
/////////////////////////////////////////////////////////////////////////////////////////
#ifndef __INCLUDE_GUARD__QUEX__AUTO_TOKEN_IDS_$$INCLUDE_GUARD_EXT$$__
#define __INCLUDE_GUARD__QUEX__AUTO_TOKEN_IDS_$$INCLUDE_GUARD_EXT$$__

#include<cstdio> // for: 'std::sprintf'

/* The token class definition file can only be included after the two token identifiers have
 * been defined. Otherwise, it would rely on default values. */
#include "$$TOKEN_CLASS_DEFINITION_FILE$$"

$$TOKEN_ID_DEFINITIONS$$

$$CONTENT$$

#endif // __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_GENERATED__
"""

func_str = \
"""
#ifndef    __QUEX_SETTING_MAP_TOKEN_ID_TO_NAME_DEFINED
#   define __QUEX_SETTING_MAP_TOKEN_ID_TO_NAME_DEFINED

QUEX_NAMESPACE_TOKEN_OPEN

inline const char*
QUEX_TYPE_TOKEN::map_id_to_name(const QUEX_TYPE_TOKEN_ID TokenID)
{
   static char  error_string[64];
   static const char  uninitialized_string[] = "<UNINITIALIZED>";
   static const char  termination_string[]   = "<TERMINATION>";
$$TOKEN_NAMES$$       

   /* NOTE: This implementation works only for token id types that are 
    *       some type of integer or enum. In case an alien type is to
    *       used, this function needs to be redefined.                  */
   switch( TokenID ) {
   default: {
       std::sprintf(error_string, "<UNKNOWN TOKEN-ID: %i>", int(TokenID));
       return error_string;
   }
   case __QUEX_SETTING_TOKEN_ID_TERMINATION:   return termination_string;
   case __QUEX_SETTING_TOKEN_ID_UNINITIALIZED: return uninitialized_string;
$$TOKEN_ID_CASES$$
   }
}

QUEX_NAMESPACE_TOKEN_CLOSE
#endif
"""

def do(setup):
    """Creates a file of token-ids from a given set of names.
       Creates also a function:

       const string& $$token$$::map_id_to_name().
    """
    global file_str
    assert lexer_mode.token_id_db.has_key("TERMINATION"), \
           "TERMINATION token id must be defined by setup or user."
    assert lexer_mode.token_id_db.has_key("UNINITIALIZED"), \
           "UNINITIALIZED token id must be defined by setup or user."
    # (*) Token ID File ________________________________________________________________
    #
    #     The token id file can either be specified as database of
    #     token-id names, or as a file that directly assigns the token-ids
    #     to variables. If the flag '--user-token-id-file' is defined, then
    #     then the token-id file is provided by the user. Otherwise, the
    #     token id file is created by the token-id maker.
    #
    #     The token id maker considers the file passed by the option '-t'
    #     as the database file and creates a C++ file with the output filestem
    #     plus the suffix "--token-ids". Note, that the token id file is a
    #     header file.
    #
    if len(lexer_mode.token_id_db.keys()) == 2:
        # TERMINATION + UNINITIALIZED = 2 token ids. If they are the only ones nothing can be done.
        print "error: No token id other than %sTERMINATION and %sUNINITIALIZED are defined. " % \
              (setup.token_id_prefix, setup.token_id_prefix)
        print "error: Quex refuses to proceed. Please, use the 'token { ... }' section to "
        print "error: specify at least one other token id."
        sys.exit(-1)

    #______________________________________________________________________________________
    L = max(map(lambda name: len(name), lexer_mode.token_id_db.keys()))
    def space(Name):
        return " " * (L - len(Name))

    # -- define values for the token ids
    token_id_txt = ""
    if setup.token_id_foreign_definition_file != "":
        token_id_txt += "#include\"%s\"\n" % setup.token_id_foreign_definition_file

    else:
        token_names = lexer_mode.token_id_db.keys()
        token_names.sort()

        i = setup.id_count_offset
        for token_name in token_names:
            token_info = lexer_mode.token_id_db[token_name] 
            if token_info.number == None: 
                token_info.number = i; i+= 1
            token_id_txt += "#define %s%s %s((QUEX_TYPE_TOKEN_ID)%i)\n" % (setup.token_id_prefix,
                                                                           token_name, space(token_name), 
                                                                           token_info.number)
    # -- define the function for token names
    switch_cases = ""
    token_names  = ""
    for token_name in lexer_mode.token_id_db.keys():
        if token_name in ["TERMINATION", "UNINITIALIZED"]: continue
        switch_cases += "   case %s%s:%s return token_id_str_%s;\n" % \
                        (setup.token_id_prefix, token_name, space(token_name), token_name)
        token_names  += "   static const char  token_id_str_%s[]%s = \"%s\";\n" % \
                        (token_name, space(token_name), token_name)

    name_space = ["quex"]
    if type(lexer_mode.token_type_definition) != dict:
        name_space = lexer_mode.token_type_definition.name_space
    
    file_str = file_str.replace("$$CONTENT$$", func_str)
    content = blue_print(file_str,
                         [["$$TOKEN_ID_DEFINITIONS$$",        token_id_txt],
                          ["$$DATE$$",                        time.asctime()],
                          ["$$TOKEN_CLASS_DEFINITION_FILE$$", lexer_mode.get_token_class_file_name(setup)],
                          ["$$INCLUDE_GUARD_EXT$$",           get_include_guard_extension(setup.output_file_stem)],
                          ["$$TOKEN_ID_CASES$$",              switch_cases],
                          ["$$TOKEN_NAMES$$",                 token_names],
                          ["$$TOKEN_PREFIX$$",                setup.token_id_prefix]])

    write_safely_and_close(setup.output_token_id_file, content)

def parse_token_id_file(ForeignTokenIdFile, TokenPrefix, CommentDelimiterList, IncludeRE):
    """This function somehow interprets the user defined token id file--if there is
       one. It does this in order to find the names of defined token ids. It does
       some basic interpretation and include file following, but: **it is in no
       way perfect**. Since its only purpose is to avoid warnings about token ids
       that are not defined it is not essential that it may fail sometimes.

       It is more like a nice feature that quex tries to find definitions on its own.
       
       Nevertheless, it should work in the large majority of cases.
    """
    include_re_obj = re.compile(IncludeRE)

    # validate(...) ensured, that the file exists.
    work_list    = [ ForeignTokenIdFile ] 
    done_list    = []
    unfound_list = []
    while work_list != []:
        fh = open_file_or_die(work_list.pop(), Mode="rb")
        content = fh.read()
        fh.close()

        # delete any comment inside the file
        for opener, closer in CommentDelimiterList:
            content = delete_comment(content, opener, closer, LeaveNewlineDelimiter=True)

        # add any found token id to the list
        token_id_finding_list = extract_identifiers_with_specific_prefix(content, TokenPrefix)
        for token_name, line_n in token_id_finding_list:
            prefix_less_token_name = token_name[len(TokenPrefix):]
            # NOTE: The line number might be wrong, because of the comment deletion
            lexer_mode.token_id_db[prefix_less_token_name] = \
                    TokenInfo(prefix_less_token_name, None, None, fh.name, line_n) 
        
        # find "#include" statements
        include_file_list = include_re_obj.findall(content)
        include_file_list = filter(lambda file: file not in done_list,    include_file_list)
        include_file_list = filter(lambda file: os.access(file, os.F_OK), include_file_list)
        work_list.extend(include_file_list)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "error: missing command line parameter: input 'token file'"
        sys.exit(-1)

    cl = GetPot(sys.argv)
    input_file       = cl.follow("", "-i")
    token_class_file = cl.follow("", "-t")
    token_class      = cl.follow("token", "--token-class-name")
    token_id_counter_offset = cl.follow(1000, "--offset")
    output_file          = cl.follow("", "-o")
    token_prefix         = cl.follow("TKN_", "--tp")
    
    if "" in [input_file, output_file]:
        print "error: please specify input (option '-i') and output file (option '-o')"
        sys.exit(-1)
        
    do(Setup(input_file, output_file, token_class_file, token_class, token_prefix, token_id_counter_offset))

