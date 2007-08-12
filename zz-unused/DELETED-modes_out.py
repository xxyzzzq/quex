#! /usr/bin/env python
# Quex is  free software;  you can  redistribute it and/or  modify it  under the
# terms  of the  GNU Lesser  General  Public License  as published  by the  Free
# Software Foundation;  either version 2.1 of  the License, or  (at your option)
# any later version.
# 
# This software is  distributed in the hope that it will  be useful, but WITHOUT
# ANY WARRANTY; without even the  implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the  GNU Lesser General Public License for more
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along
# with this  library; if not,  write to the  Free Software Foundation,  Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
################################################################################

import re       # regular expression handling
import sys

import file_in
import quex_class_out
import lexer_mode

def do(Modes, setup):

    fh = open(setup.tmp_flex_input_file, "w")

    # write the header file
    header_txt = write_header(Modes, setup)

    # write the pattern match code
    code_str, brief_str = write_pattern_match_code(Modes, setup.output_debug_f)

    fh.write(header_txt)
    fh.write("/*\n" + brief_str + "*/\n")
    fh.write("\n%%\n\n")
    fh.write(code_str)
    fh.write("%%\n")        
    fh.write("/* end of file */\n")
    # terminating newline
    fh.write("\n")                     
    fh.close()

    # write the mode-classes required for mode transition events
    quex_class_out.do(Modes, setup)


def consistency_check(Modes):
    """If consistency check fails due to a fatal error, then this functions
    exits back to the system with error code -1.  Otherwise, in 'not so
    perfect' cases there might be only a warning being printed to standard
    output.
    """
    if len(Modes) == 0:
        print "error: no single mode define - bailing out"
        sys.exit(-1)

    # is there a mode that is applicable?
    for mode in Modes.values():
        if mode.options["inheritable:"] != "only": break
    else:
        print "error: there is no mode that can be applied"
        print "error: all are inheritable only"
        sys.exit(-1)

    # is the initial mode defined
    if lexer_mode.initial_mode.line_n == -1:
        # find first mode that can actually be applied
        for mode in Modes.values():
            if mode.options["inheritable:"] != "only":
                selected_mode = mode.name
                break
            
        lexer_mode.initial_mode.code     = selected_mode
        lexer_mode.initial_mode.line_n   = 0
        lexer_mode.initial_mode.filename = "automatical-selection-by-quex"
        print "warning: no initial mode defined via 'start'"
        print "warning: using mode '%s' as initial mode" % selected_mode
                
    for mode in Modes.values():
        mode.consistency_check()


def write_header(Modes, setup):

    PatternFile    = setup.input_pattern_file
    LexerClassName = setup.output_engine_name

    # (*) perform consistency check 
    consistency_check(Modes)
    
    # (*) Prolog: includes/ pattern definitions/ options -------------------------------------
    header_txt  = "/* -*- C++ -*- */\n"
    header_txt += "%{\n"
    header_txt += "#include <%s>\n" % setup.output_file_stem
    if setup.input_derived_class_file != "":
        header_txt += "#include <%s>\n" % setup.input_derived_class_file
    
    header_txt += "\n%}\n"
    #    -- reading the basic patterns used by lexical rules
    #       (delete C++ comments, because Flex cannot read it)
    txt = file_in.get_plain_file_content(PatternFile)
    txt = re.compile("//.*").sub("", txt)  # regular expression substitution
                                 
    header_txt += txt
    #    -- options for flex
    #       (**do not forget about the '\n' in front of the marker, otherwise
    #          post-flex errs in case that the pattern file does not end with a newline**)
    header_txt += "\n/* <<pre_flex.py: mode definitions>> */\n"
    #      -- each real appearing mode is an EXCLUSIVE mode in the flex terminology.

    for mode_name, mode in Modes.items():
        # if mode.options["inheritable:"] == "only": continue
        header_txt += "%%x LEX_ID_%s\n" % mode_name

    #      -- documentation about the inheritance structure of modes
    header_txt += "\n/* mode inheritance structure */\n"
    for mode_name, mode in Modes.items():
        if mode.options["inheritable:"] == "only": continue
        header_txt += "/* \n" 
        header_txt += Modes[mode_name].inheritance_structure_string()
        header_txt += "*/\n"

    #    -- the parser class 
    header_txt += "%%option yyclass=\"quex::%s\"\n\n" % LexerClassName

    return header_txt


def write_pattern_match_code(Modes, DebugF):
    """Writes for all modes in the database a set of rules. Inheritances
    are resolves, i.e. patterns from base modes are inherited. If the
    base and derived modes share a pattern, the derived mode's pattern
    wins.

    Before anything happens a sanity check is done. That means, that
    only modes that are open to be inherited really are used as
    base modes.

    (not implemented yet: Further on, modes with base classes of restricted
    exits/entry shall not open other exits by other base modes or
    or its own explicit exits.)

    (not implemented yet: Mode exits/entrances must fit the given options
    about the exits/entrance rights.)    
    """

    brief_str = ""
    code_str = ""

    # nicer names for lexemes and lexem lengths:
    code_str += "   // NOTE: indented text before the first rule is pasted right before the\n"
    code_str += "   //       infinite loop of the lexical analyser => initialization.\n"
    code_str += "   char*& Lexeme  = yytext;\n"
    code_str += "   int&   LexemeL = yyleng;\n"
    code_str += "   // make sure that compiler does not complain about unsued variables:\n"
    code_str += "   // NOTE: we are here before any pattern matching. the first incoming\n"
    code_str += "   //       pattern will setup the correct values\n"
    code_str += "   LexemeL = (int)(Lexeme); LexemeL = 0;\n\n"
    
    for mode_name, mode in Modes.items():        
        # only inheritable: abstract - no real mode exist of this
        if mode.options["inheritable:"] == "only": continue

        # pattern_action_pairs returns a dictionary with unique keys.
        # using the .values() function returns a list of patterns that
        # belong to the keys
        mode_patterns = mode.pattern_action_pairs().values()

        # sort patterns with inheritance:
        #   => base patterns preceed if they have the same length.
        def pattern_precedence(A, B):
            tmp = - cmp(A.inheritance_level, B.inheritance_level)
            if tmp != 0: return tmp
            else:        return cmp(A.pattern_index, B.pattern_index)
            
        mode_patterns.sort(pattern_precedence)

        first_f = True
        for pattern_info in mode_patterns:

            pattern = pattern_info.pattern

            action  = "{"
            # counting the columns,
            # counting the newlines: here one might have analysis about the pattern
            #                        preceeding and only doing the check if the pattern
            #                        potentially contains newlines.
            action += "\nthis->ACTION_ENTRY(yytext, yyleng);"
            action += "\nthis->on_action_entry(yytext, yyleng);\n"
            if DebugF == True:
                action += '#ifdef DEBUG_QUEX_PATTERN_MATCHES\n'
                action += '    std::cerr << "(" << line_number() << ", " << column_number()'
                safe_pattern_str = pattern_info.pattern.replace("\"", "\\\"")

                action += '<< ") %s: %s \'" << yytext << "\'\\n";\n' % (mode_name, safe_pattern_str)
                action += '#endif // DEBUG_QUEX_PATTERN_MATCHES\n'
                
            action += "#line %i \"%s\"\n" % (pattern_info.line_n, pattern_info.filename)
            action += pattern_info.action + "\n}"
            
            code_str  += "<LEX_ID_" + mode_name + ">" + pattern + " " + action + "\n\n"

            # accumulate inheritance information for comment
            brief_str += "** %2i %2i" % (pattern_info.inheritance_level, pattern_info.pattern_index)
            if first_f: brief_str += "   <LEX_ID_" + mode_name + ">" + pattern + "\n"
            else:       brief_str += "   " + (" " * len(mode_name)) + "  " + pattern + "\n"            
            first_f = False

        brief_str += "**\n"

    return code_str, brief_str




#license-info Sat Aug  5 12:31:27 2006#
