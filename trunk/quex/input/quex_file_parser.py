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
import subprocess
#
from   quex.frs_py.file_in          import *
from   quex.token_id_maker          import TokenInfo
from   quex.exception               import RegularExpressionException
import quex.lexer_mode                          as lexer_mode
import quex.core_engine.regular_expression.core as regex


def do(file_list, Setup):
    global mode_db

    for file in file_list:
        fh = open_file_or_die(file)
        # read all modes until end of file
        try:
            while 1 + 1 == 2:
                parse_section(fh, Setup)
        except EndOfStreamException:
            pass
        
    return lexer_mode.mode_db

def parse_unique_code_fragment(fh, code_fragment_name, possible_code_fragment_carrier):
    """Parse a code fragment that can only be defined once. That includes that
       and error is sent, if it is tried to define it a second time.
    """   
    if possible_code_fragment_carrier.line_n != -1:
        error_msg("%s defined twice" % code_fragment_name, fh, DontExitF=True)
        error_msg("previously defined here", 
                  possible_code_fragment_carrier.filename,
                  possible_code_fragment_carrier.line_n)

    result = parse_code_fragment(fh, code_fragment_name)
    possible_code_fragment_carrier.code     = result.code
    possible_code_fragment_carrier.filename = result.filename
    possible_code_fragment_carrier.line_n   = result.line_n
    
def parse_code_fragment(fh, code_fragment_name):
    result = lexer_mode.ReferencedCodeFragment()
    
    dummy, i = read_until_letter(fh, ["{"], Verbose=True)

    if i == -1: error_message("missing open bracket after '%s' definition" % code_fragment_name, fh)

    result.code = read_until_closing_bracket(fh, "{", "}")
    result.filename = fh.name
    result.line_n   = get_current_line_info_number(fh)

    return result

def __parse_domain_of_whitespace_separated_elements(fh, CodeFragmentName, ElementNames, MinElementN):   
    """Returns list of lists, where 
     
         record_list[i][k]  means element 'k' of line 'i'

       NOTE: record_list[i][-1] contains the line 'i' as it appeared as a whole.
             record_list[i][-2] contains the line number of line in the given file.

    """       
    start_line_n = get_current_line_info_number(fh)
    dummy, i = read_until_letter(fh, ["{"], Verbose=True)
    if i == -1: 
        error_msg("missing '{' after %s statement" % CodeFragmentName, fh)
    #
    line_n = start_line_n       
    record_list = []
    while 1 + 1 == 2:
        line = fh.readline()
        line_n += 1
        #
        if line == "": 
            error_msg("found end of file while parsing a '%s' range.\n" % CodeFragmentName + \
                      "range started here.", fh, start_line_n)    
        line = line.strip()
        if line == "":                           continue           # empty line
        elif line[0] == '}':                     return record_list # end of define range
        elif len(line) > 1 and line[:2] == "//": continue           # comment

        # -- interpret line as list of whitespace separated record elements
        fields = line.split()    
        if len(fields) < MinElementN: 
            format_str = ""
            for element in ElementNames:
                format_str += "%s   " % element 
            error_msg("syntax error in pattern definition\n" + \
                      "format: %s  NEWLINE" % format_str , fh, line_n)
        record_list.append(fields + [line_n, line])    


    assert True == False, "this code section should have never been reached!"

def parse_pattern_name_definitions(fh):
    """Parses pattern definitions of the form:
   
          WHITESPACE  [ \t\n]
          IDENTIFIER  [a-zA-Z0-9]+
          OP_PLUS     "+"
          
       That means: 'name' whitespace 'regular expression' whitespace newline.
       Comments can only be '//' nothing else and they have to appear at the
       beginning of the line.
       
       One regular expression can have more than one name, but one name can 
       only have one regular expression.
    """
    #
    record_list = __parse_domain_of_whitespace_separated_elements(fh, "define", 
                                                                  ["NAME", "REGULAR-EXPRESSION"], 2)
    
    db = lexer_mode.shorthand_db
    for record in record_list:
        line_n                 = record[-2]
        line                   = record[-1]
        name                   = record[0]
        regular_expression_str = line[len(name):].strip()
        #
        if db.has_key(name):    
            error_msg("pattern name defined twice: '%s'" % name, fh.name, line_n, DontExitF=True)
            error_msg("previously define here.", db[name].filename, db[name].line_n)
        else:    
            db[name] = lexer_mode.PatternShorthand(name, regular_expression_str, 
                                                   fh.name, line_n)
        line_n += 1

def parse_token_id_definitions(fh, Setup):
    """Parses token definitions of the form:
  
          TOKEN_ID_NAME [Number] [TypeName] 
          
       For example:

          TKN_IDENTIFIER   1002  std::string
  
       defines an token_id with value 1002 and type std::string.
   
          TKN_NUMBER   std::double
          TKN_FLAG     1008
          TKN_NUMBER   2999       
         
       defines an id TKN_NUMBER, where the type is set to 'std::string'. Then
       TKN_FLAG is defined as numerical value 1008. Finally an addition to 
       TKN_NUMBER is made, saying that is has the numerical value of 2999.       
          
    """
    #
    record_list = __parse_domain_of_whitespace_separated_elements(fh, "define", 
                                                                  ["TOKEN-ID-NAME", 
                                                                   "[Number]", "[TypeName]"], 1)
    
    db = lexer_mode.token_id_db
    for record in record_list:
        # NOTE: record[-1] -> line text, record[-2] -> line number
        #       record[:-2] fields of the line
        line_n    = record[-2]
        name      = record[0]
        type_name = None
        number    = None
        #
        # -- check the name, if it starts with the token prefix paste a warning
        token_prefix = Setup.input_token_id_prefix
        if name.find(token_prefix) == 0:
            error_msg("Token identifier '%s' starts with token prefix '%s'.\n" % (name, token_prefix) + \
                      "Token prefix is mounted automatically. This token id appears in the source\n" + \
                      "code as '%s%s'." % (token_prefix, name), \
                      fh, DontExitF=True)

        #
        if len(record) - 2 > 1: 
            candidate = record[1]
            # does candidate consist only of digits ? --> number
            # is first character a letter or '_' ?    --> type_name     
            if candidate.isdigit():                             number = long(candidate)
            elif candidate[0].isalpha() or candidate[0] == "_": type_name = candidate
        #
        if len(record) - 2 > 2:
            candidate = record[2]
            # is first character a letter or '_' ?      
            if candidate[0].isalpha() or candidate[0] == "_": 
                if type_name != None:
                    error_msg("Token can only have *one* type associated with it", fh, line_n)
                type_name = candidate
        #
        if not db.has_key(name): 
            db[name] = TokenInfo(name, number, type_name, fh.name, line_n)
        else:
            if number != None:    db[name].id        = number
            if type_name != None: db[name].type_name = type_name
            db[name].positions.append([fh.name, line_n])

def parse_initial_mode_definition(fh):
    verify_next_word(fh, "=")
    # specify the name of the intial lexical analyser mode
    mode_name = read_next_word(fh)
    if lexer_mode.initial_mode.line_n != -1:
        error_msg("start mode defined more than once!", fh, DontExitF=True)
        error_msg("previously defined here",
                  lexer_mode.initial_mode.filename,
                  lexer_mode.initial_mode.line_n)
        
    lexer_mode.initial_mode.code     = mode_name
    lexer_mode.initial_mode.filename = fh.name
    lexer_mode.initial_mode.line_n   = get_current_line_info_number(fh)

def parse_section(fh, Setup):

    skip_whitespace(fh)

    # (*) determine what is defined
    #
    #     -- 'mode { ... }'   => define a mode
    #     -- 'start ='        => define the name of the initial mode
    #     -- 'header { ... }' => define code that is to be pasted on top
    #                            of the engine (e.g. "#include<...>")
    #     -- 'body { ... }'   => define code that is to be pasted in the class' body
    #                            of the engine (e.g. "public: int  my_member;")
    #     -- 'init { ... }'   => define code that is to be pasted in the class' constructors
    #                            of the engine (e.g. "my_member = -1;")
    #     -- 'define { ... }' => define patterns shorthands such as IDENTIFIER for [a-z]+
    #     -- 'token { ... }'  => define token ids
    #
    word = read_next_word(fh)

    if word == "start":
        parse_initial_mode_definition(fh)
        return
    
    elif word == "header":
        parse_unique_code_fragment(fh, "header", lexer_mode.header)        
        return

    elif word == "body":
        parse_unique_code_fragment(fh, "body", lexer_mode.class_body)        
        return

    elif word == "init":
        parse_unique_code_fragment(fh, "init", lexer_mode.class_init)
        return
        
    elif word == "define":
        parse_pattern_name_definitions(fh)
        return

    elif word == "token":       
        parse_token_id_definitions(fh, Setup)
        return

    elif word == "mode":
        parse_mode_definition(fh, Setup)
        return
    else:
        error_msg("sequence '%s' not recognized as valid keyword in this context" % word + \
                  "use: 'mode', 'header', 'body', 'init', 'define', 'token' or 'start'", fh)

def parse_mode_definition(fh, Setup):

    skip_whitespace(fh)
    mode_name = read_next_word(fh)
    # NOTE: constructor does register this mode in the mode_db
    new_mode  = lexer_mode.LexMode(mode_name, fh.name, get_current_line_info_number(fh))

    # (*) inherited modes / options
    skip_whitespace(fh)
    dummy, k = read_until_letter(fh, [":", "{"], Verbose=1)

    if k != 1 and k != 0:
        error_message("missing ':' or '{' after mode '%s'" % mode_name, fh)

    if k == 0:
        # ':' => inherited modes/options follow
        skip_whitespace(fh)

        # (*) base modes 
        base_modes, i = read_until_letter(fh, ["{", "<"], Verbose=1)
        new_mode.base_modes = split(base_modes)
    
        if i == 1:
            # (*) options
            while 1 + 1 == 2:
                content = read_until_letter(fh, [">"])
                fields = split(content)
                if len(fields) != 2:
                    error_msg("options must have exactly two arguments\n" + \
                              "found: %s" % repr(fields), fh)
                option, value = split(content)
                new_mode.add_option(option, value)
                content, i = read_until_letter(fh, ["<", "{"], Verbose=True)
                if i != 0: break

    # (*) read in pattern-action pairs
    pattern_i = -1
    while 1 + 1 == 2:
        pattern_i += 1
        

        skip_whitespace(fh)
        position = fh.tell()
        word     = read_next_word(fh)

        if word == "}":
            if new_mode.matches == {}:
                error_msg("mode '%s' does not contain any pattern" % new_mode.name, fh)
            break

        result = check_for_event_specification(word, fh, new_mode, Setup, pattern_i)
        if result == True: 
            continue

        elif type(result) == str:
            pattern = result
            pattern_state_machine = regex.do(pattern, {}, 
                                             Setup.begin_of_stream_code, Setup.end_of_stream_code,
                                             DOS_CarriageReturnNewlineF=Setup.dos_carriage_return_newline_f)

        else:
            fh.seek(position)
            pattern, pattern_state_machine = parse_regular_expression_specification(fh, Setup)

        parse_action_code(new_mode, fh, Setup, pattern, pattern_state_machine, pattern_i)

def parse_action_code(new_mode, fh, Setup, pattern, pattern_state_machine, PatternIdx):
    skip_whitespace(fh)
    position = fh.tell()
        
    if fh.read(1) == "{":
        line_n = get_current_line_info_number(fh) + 1
        code   = read_until_closing_bracket(fh, "{", "}")

        new_mode.matches[pattern] = lexer_mode.Match(pattern, code, pattern_state_machine, 
                                                     PatternIdx, fh.name, line_n)
        return

    fh.seek(position)
    word = read_next_word(fh)

    if word == "PRIORITY-MARK":
        # This mark 'lowers' the priority of a pattern to the priority of the current
        # pattern index (important for inherited patterns, that have higher precedence).
        new_mode.matches[pattern] = lexer_mode.Match(pattern, "", pattern_state_machine, 
                                                     PatternIdx, PriorityMarkF = True)

    elif word == "DELETION":
        # This mark deletes any pattern that was inherited with the same 'name'
        new_mode.matches[pattern] = lexer_mode.Match(pattern, "", pattern_state_machine, 
                                                     PatternIdx, DeletionF = True)
        
    elif word == "=>":
        parse_brief_token_sender(new_mode, fh, pattern, pattern_state_machine, PatternIdx, Setup)

    else:
        error_msg("missing token '{', 'PRIORITY-MARK', 'DELETE', or '=>'.", fh)

    return

def parse_brief_token_sender(new_mode, fh, pattern, pattern_state_machine, PatternIdx, Setup):
    skip_whitespace(fh)
    # shorthand for { self.send(TKN_SOMETHING); RETURN; }
    token_name, bracket_i = read_until_letter(fh, ["(", ";"], Verbose=True)
    if bracket_i == -1: 
        error_msg("missing ending ';' at end of '=>' token sending statement.", fh)

    token_name = token_name.strip()
    if bracket_i == 0:
        token_constructor_args = read_until_closing_bracket(fh, "(", ")")
        token_constructor_args = ", " + token_constructor_args
        verify_next_word(fh, ";")
    else:
        token_constructor_args = ""
        
    # after 'send' the token queue is filled and one can safely return
    if token_name.find(Setup.input_token_id_prefix) != 0:
        error_msg("token identifier does not begin with token prefix '%s'\n" % Setup.input_token_id_prefix + \
                  "found: '%s'" % token_name, fh)
    prefix_less_token_name = token_name[len(Setup.input_token_id_prefix):]

    if not lexer_mode.token_id_db.has_key(prefix_less_token_name):
        msg = "Token id '%s' defined implicitly." % token_name
        if token_name in lexer_mode.token_id_db.keys():
            msg += "\nNOTE: '%s' has been defined in a token { ... } section!" % \
                   (Setup.input_token_id_prefix + token_name)
            msg += "\nNote, that tokens in the token { ... } section are automatically prefixed."
        error_msg(msg, fh, DontExitF=True)

        lexer_mode.token_id_db[prefix_less_token_name] = \
                TokenInfo(prefix_less_token_name, None, None, fh.name, get_current_line_info_number(fh)) 

    code = "self.send(%s%s); RETURN;" % (token_name, token_constructor_args)

    line_n = get_current_line_info_number(fh) + 1
    new_mode.matches[pattern] = lexer_mode.Match(pattern, code,  pattern_state_machine, PatternIdx,
                                                 fh.name, line_n)
    
def check_for_event_specification(word, fh, new_mode, Setup, PatternIdx):

    if word == "on_entry":
        # Event: enter into mode
        parse_unique_code_fragment(fh, "%s::on_entry event handler" % new_mode.name, new_mode.on_entry)
        return True
    
    elif word == "on_exit":
        # Event: exit from mode
        parse_unique_code_fragment(fh, "%s::on_exit event handler" % new_mode.name, new_mode.on_exit)
        return True

    elif word == "on_match":
        # Event: exit from mode
        parse_unique_code_fragment(fh, "%s::on_match event handler" % new_mode.name, new_mode.on_match)
        return True

    elif  word == "on_indentation":
        # Event: start of indentation, 
        #        first non-whitespace after whitespace
        parse_unique_code_fragment(fh, "%s::on_indentation event handler" % new_mode.name, 
                                   new_mode.on_indentation)
        return True

    elif word == "on_failure" or word == "<<FAIL>>":
        # Event: No pattern matched for current position.
        # NOTE: See 'on_end_of_stream' comments.
        parse_unique_code_fragment(fh, "%s::on_failure event handler" % new_mode.name, 
                                   new_mode.on_failure)
        return True

    elif word == "on_end_of_stream" or word == "<<EOF>>": 
        # Event: End of data stream / end of file
        # NOTE: The regular expression parser relies on <<EOF>> and <<FAIL>>. So those
        #       patterns are entered here, even if later versions of quex might dismiss
        #       those rule deefinitions in favor of consistent event handlers.
        return "<<EOF>>"

    elif len(word) >= 3 and word[:3] == "on_":    
        error_msg("Unknown event handler '%s'. Known event handlers are:\n\n" % word + \
                  "on_entry, on_exit, on_indentation, on_end_of_stream, on_failure. on_match\n\n" + \
                  "Note, that any pattern starting with 'on_' is considered an event handler.\n" + \
                  "use double quotes to bracket patterns that start with 'on_'.", fh)

    # word was not an event specification 
    return False

def parse_regular_expression_specification(fh, Setup):

    start_position = fh.tell()
    try:
        # -- adapt pattern dictionary: 
        #    (this may be superfluous if the it was organized differently)
        pattern_dictionary = {}
        for item in lexer_mode.shorthand_db.values():
            pattern_dictionary[item.name] = item.regular_expression         

        # -- parse regular expression, build state machine
        pattern_state_machine = regex.do(fh, pattern_dictionary, 
                                         Setup.begin_of_stream_code, Setup.end_of_stream_code,
                                         DOS_CarriageReturnNewlineF=Setup.dos_carriage_return_newline_f)
    except RegularExpressionException, x:
        error_msg("Regular expression parsing:\n" + x.message, fh)

    end_position = fh.tell()

    fh.seek(start_position)
    pattern = fh.read(end_position - start_position)

    return pattern, pattern_state_machine

