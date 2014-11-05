#! /usr/bin/env python
import time
import os
import sys
from GetPot import GetPot

import quex.frs_py.file_in  as file_in
import quex.lexer_mode      as lexer_mode

from quex.frs_py.string_handling import blue_print

class TokenInfo:
    def __init__(self, Name, ID, TypeName=None, Filename="", LineN=-1):
        self.name         = Name
        self.number       = ID
        self.related_type = TypeName
        self.positions    = [ Filename, LineN ]
        self.id           = None

class Setup:
    def __init__(self, GlobalSetup):

        self.input_files      = GlobalSetup.input_token_id_db
        self.output_file      = GlobalSetup.output_token_id_file
        self.token_class_file = GlobalSetup.input_token_class_file
        self.token_class      = GlobalSetup.input_token_class_name
        self.token_prefix     = GlobalSetup.input_token_id_prefix
        self.id_count_offset  = GlobalSetup.input_token_counter_offset
        self.input_foreign_token_id_file = GlobalSetup.input_foreign_token_id_file
        
file_str = \
"""// -*- C++ -*-
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
#ifndef __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_$$DATE_IG$$__
#define __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_$$DATE_IG$$__

#include<cstdio> // for: 'std::sprintf'
#include<map>    // for: 'token-id' <-> 'name map'
#include "$$TOKEN_CLASS_DEFINITION_FILE$$"


$$TOKEN_ID_DEFINITIONS$$

namespace quex {

$$CONTENT$$

}
#endif // __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_GENERATED__
"""

func_str = \
"""
    inline const std::string&
    $$TOKEN_CLASS$$::map_id_to_name(const QUEX_TOKEN_ID_TYPE TokenID)
    {
       static bool virginity_f = true;
       static std::map<QUEX_TOKEN_ID_TYPE, std::string>  db;
       static std::string  error_string("");
       static std::string  uninitialized_string("<UNINITIALIZED>");
       static std::string  termination_string("<TERMINATION>");
       
       // NOTE: In general no assumptions can be made that the QUEX_TOKEN_ID_TYPE
       //       is an integer. Thus, no switch statement is used. 
       if( virginity_f ) {
           virginity_f = false;
           // Create the Database mapping TokenID -> TokenName
           $$TOKEN_ID_CASES$$
       }

       if     ( TokenID == $$TOKEN_PREFIX$$TERMINATION )   return termination_string;
       else if( TokenID == $$TOKEN_PREFIX$$UNINITIALIZED ) return uninitialized_string;
       std::map<QUEX_TOKEN_ID_TYPE, std::string>::const_iterator it = db.find(TokenID);
       if( it != db.end() ) return (*it).second;
       else {
          char tmp[64];
          std::sprintf(tmp, "<UNKNOWN TOKEN-ID: %i>", int(TokenID));
          error_string = std::string(tmp);
          return error_string;
       }
    }
"""

def do(global_setup):
    """Creates a file of token-ids from a given set of names.
       Creates also a function:

       const string& $$token$$::map_id_to_name().
    """
    # file contains simply a whitespace separated list of token-names
    output(global_setup)
    return

    # THIS IS A FIRST ATTEMPT TO PARSE FOREIGN TOKEN ID DEFINITIONS
    for input_file in global_setup.input_token_id_db:
        curr_tokens = file_in.open_file_or_die(input_file).read().split(";")        
        curr_token_infos = map(lambda x: TokenInfo(x.split(), input_file), curr_tokens)

        for token_info in curr_token_infos:
            if token_info.name == "": continue
            
            if token_info.name in lexer_mode.token_id_db.keys():
                print "%s:0:error: token name '%s' defined twice." % (input_file, token_info.name)
                print "%s:0:error: previously defined here." % lexer_mode.token_id_db[token_info.name].filename
                sys.exit(-1)

            lexer_mode.token_id_db[token_info.name] = token_info

def output(global_setup):
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
    setup = Setup(global_setup)
    if len(lexer_mode.token_id_db.keys()) == 2:
        # TERMINATION + UNINITIALIZED = 2 token ids. If they are the only ones nothing can be done.
        print "error: No token id other than %sTERMINATION and %sUNINITIALIZED are defined. " % \
              (setup.token_prefix, setup.token_prefix)
        print "error: Quex refuses to proceed. Please, use the 'token { ... }' section to "
        print "error: specify at least one other token id."
        sys.exit(-1)

    if global_setup.input_user_token_id_file != "":
        ## print "(0) token ids provided by user"
        ## print "   '%s'" % global_setup.input_user_token_id_file
        global_setup.output_token_id_file = global_setup.input_user_token_id_file
        return
    
    if global_setup.input_token_id_db == "":
        print "error: token-id database not specified"
        sys.exit(-1)
        
    ## print "   token class file = '%s'" % global_setup.input_token_class_file
    ## print "   => '%s'" % global_setup.output_token_id_file
    
    #______________________________________________________________________________________
    L = max(map(lambda name: len(name), lexer_mode.token_id_db.keys()))
    def space(Name):
        return " " * (L - len(Name))

    # -- define values for the token ids
    token_id_txt  = "namespace quex {\n"  
    if setup.input_foreign_token_id_file != "":
        token_id_txt += "#include\"%s\"\n" % setup.input_foreign_token_id_file

    else:
        token_names = lexer_mode.token_id_db.keys()
        token_names.sort()

        i = setup.id_count_offset
        for token_name in token_names:
            token_info = lexer_mode.token_id_db[token_name] 
            if token_info.number == None: 
                token_info.number = i; i+= 1
            token_id_txt += "const QUEX_TOKEN_ID_TYPE %s%s %s= %i;\n" % (setup.token_prefix,
                                                                         token_name, space(token_name), 
                                                                         token_info.number)
    token_id_txt += "} // namespace quex\n" 

    # -- define the function for token names
    db_build_txt = ""
    for token_name in lexer_mode.token_id_db.keys():
        db_build_txt += '\n           db[%s%s] %s= std::string("%s");' % (setup.token_prefix,
                                                                          token_name,
                                                                          space(token_name),
                                                                          token_name)
    
    txt = blue_print(func_str, [["$$TOKEN_ID_CASES$$", db_build_txt],
                                ["$$TOKEN_PREFIX$$",   setup.token_prefix]])


    t = time.localtime()
    date_str = "%iy%im%id_%ih%02im%02is" % (t[0], t[1], t[2], t[3], t[4], t[5])

    # -- storage classes for different types
    # TODO: "struct data_x { type0, type1 }", the redefine the previous
    #       to 'typedef data_x  type;"
    content = blue_print(file_str,
                         [["$$CONTENT$$",                     txt],
                          ["$$TOKEN_ID_DEFINITIONS$$",        token_id_txt],
                          ["$$DATE$$",                        time.asctime()],
                          ["$$TOKEN_CLASS_DEFINITION_FILE$$", setup.token_class_file],
                          ["$$DATE_IG$$",                     date_str]])

    content = content.replace("$$TOKEN_CLASS$$", setup.token_class)

    fh = open(setup.output_file, "wb")
    if os.linesep == "\n": content = content.replace("\n", os.linesep)
    fh.write(content)
    fh.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "error: missing command line parameter: input 'token file'"
        sys.exit(-1)

    cl = GetPot(sys.argv)
    input_file       = cl.follow("", "-i")
    token_class_file = cl.follow("", "-t")
    token_class      = cl.follow("token", "--token-class-name")
    token_counter_offset = cl.follow(1000, "--offset")
    output_file          = cl.follow("", "-o")
    token_prefix         = cl.follow("TKN_", "--tp")
    
    if "" in [input_file, output_file]:
        print "error: please specify input (option '-i') and output file (option '-o')"
        sys.exit(-1)
        
    do(Setup(input_file, output_file, token_class_file, token_class, token_prefix, token_counter_offset))

