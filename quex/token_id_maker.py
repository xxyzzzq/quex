#! /usr/bin/env python
import time
import sys
from GetPot import GetPot

import quex.frs_py.file_in  as file_in
import quex.lexer_mode      as lexer_mode

from frs_py.string_handling import blue_print


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
// DATE: %%DATE%%
//
/////////////////////////////////////////////////////////////////////////////////////////
#ifndef __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_%%DATE_IG%%__
#define __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_%%DATE_IG%%__

#include<cstdio> // for: 'sprintf'
#include<map>    // for: 'token-id' <-> 'name map'
#include<%%TOKEN_CLASS_DEFINITION_FILE%%>


%%TOKEN_ID_DEFINITIONS%%

namespace quex {

%%CONTENT%%

// NOT YET:
//   template <%%TOKEN_CLASS%%::id_type TokenT>
//   struct token_trait;
//
%%TOKEN_TRAITS%%
}
#endif // __INCLUDE_GUARD__QUEX__TOKEN_IDS__AUTO_GENERATED__
"""

func_str = \
"""
    inline const std::string&
    %%TOKEN_CLASS%%::map_id_to_name(const %%TOKEN_CLASS%%::id_type TokenID)
    {
       static bool virginity_f = true;
       static std::map<%%TOKEN_CLASS%%::id_type, std::string>  db;
       static std::string  error_string("");
       static std::string  uninitialized_string("<UNINITIALIZED>");
       static std::string  termination_string("<TERMINATION>");
       
       // NOTE: In general no assumptions can be made that the token::id_type
       //       is an integer. Thus, no switch statement is used. 
       if( virginity_f ) {
           virginity_f = false;
           // Create the Database mapping TokenID -> TokenName
           %%TOKEN_ID_CASES%%
       }

       if     ( TokenID == %%TOKEN_CLASS%%::ID_TERMINATION )   return termination_string;
       else if( TokenID == %%TOKEN_CLASS%%::ID_UNINITIALIZED ) return uninitialized_string;
       std::map<%%TOKEN_CLASS%%::id_type, std::string>::const_iterator it = db.find(TokenID);
       if( it != db.end() ) return (*it).second;
       else {
          char tmp[64];
          sprintf(tmp, "<UNKNOWN TOKEN-ID: %i>", int(TokenID));
          error_string = std::string(tmp);
          return error_string;
       }
    }
"""

class TokenInfo:
    def __init__(self, Name, IDNumber, TypeName, Filename, LineN):
	self.name         = Name
	self.number       = IDNumber
	self.related_type = TypeName
	self.positions    = [ Filename, LineN ]


def do(global_setup):
    """Creates a file of token-ids from a given set of names.
       Creates also a function:

       const string& %%token%%::map_id_to_name().
    """
    # file contains simply a whitespace separated list of token-names
    output(global_setup)
    return

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
    if lexer_mode.token_id_db.keys() == []:
        print "error: empty token-id list. quex cannot proceed."
        print "error: use the 'token { ... }' section to specify at least one token id."
        sys.exit(-1)

    setup = Setup(global_setup)
    if global_setup.input_user_token_id_file != "":
        print "(0) token ids provided by user"
        print "   '%s'" % global_setup.input_user_token_id_file

        global_setup.output_token_id_file = global_setup.input_user_token_id_file
	return
    
    print "(0) create token id file"
    if global_setup.input_token_id_db == "":
	print "error: token-id database not specified"
	sys.exit(-1)
	
    print "   token class file = '%s'" % global_setup.input_token_class_file
    print "   => '%s'" % global_setup.output_token_id_file
    
    #______________________________________________________________________________________
    L = max(map(lambda name: len(name), lexer_mode.token_id_db.keys()))
    def space(Name):
        return " " * (L - len(Name))

    # -- define values for the token ids
    token_id_txt = "#ifdef QUEX_FOREIGN_TOKEN_ID_DEFINITION\n"
    if setup.input_foreign_token_id_file != "":
        token_id_txt += "// If token ids come from somewhere else (e.g. the parser)\n"
        token_id_txt += "#include<%s>\n" % setup.input_foreign_token_id_file

    else:
        token_id_txt += "// No file provided that contains potentially a foreign token-id\n"
        token_id_txt += "// definition. Use quex command line option '--foreign-token-id-file'\n"
    token_id_txt += "#else // QUEX_FOREIGN_TOKEN_ID_DEFINITION\n"
    
    token_names = lexer_mode.token_id_db.keys()
    token_names.sort()

    i   = setup.id_count_offset
    for token_name in token_names:
	token_info = lexer_mode.token_id_db[token_name] 
	id = i
	if token_info.number != None: id = token_info.number
        token_id_txt += "const quex::%s::id_type %s%s %s= %i;\n" % (setup.token_class,
                                                                    setup.token_prefix,
                                                                    token_name, space(token_name), id)
        i += 1
    token_id_txt += "#endif // QUEX_FOREIGN_TOKEN_ID_DEFINITION\n"

    # -- define the function for token names
    db_build_txt = ""
    for token_name in lexer_mode.token_id_db.keys():
        db_build_txt += '\n           db[%s%s] %s= std::string("%s");' % (setup.token_prefix,
                                                                          token_name,
                                                                          space(token_name),
                                                                          token_name)
    
    txt = blue_print(func_str, [["%%TOKEN_ID_CASES%%", db_build_txt]])


    # -- define the token traits
    trait_txt = ""
    for info in lexer_mode.token_id_db.values():
        trait_txt += "//    template<> struct token_trait <%s%s> %s{ typedef %s type; };\n" % \
                     (setup.token_prefix, info.name, space(info.name), info.related_type)


    t = time.localtime()
    date_str = "%iy%im%id_%ih%02im%02is" % (t[0], t[1], t[2], t[3], t[4], t[5])

    # -- storage classes for different types
    # TODO: "struct data_x { type0, type1 }", the redefine the previous
    #       to 'typedef data_x  type;"
    content = blue_print(file_str,
                         [["%%CONTENT%%",                     txt],
                          ["%%TOKEN_ID_DEFINITIONS%%",        token_id_txt],
                          ["%%DATE%%",                        time.asctime()],
                          ["%%TOKEN_TRAITS%%",                trait_txt],
                          ["%%TOKEN_CLASS_DEFINITION_FILE%%", setup.token_class_file],
                          ["%%DATE_IG%%",                     date_str]])

    content = content.replace("%%TOKEN_CLASS%%", setup.token_class)

    fh = open(setup.output_file, "w")
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

#license-info Sat Aug  5 12:31:27 2006#
#license-info Sat Aug  5 13:05:27 2006#
#license-info Sat Aug  5 14:10:32 2006#
