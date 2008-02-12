from   quex.frs_py.file_in          import *
from   quex.token_id_maker          import TokenInfo
from   quex.exception               import RegularExpressionException
import quex.lexer_mode              as lexer_mode
import quex.lexer_mode                          as lexer_mode
import quex.core_engine.regular_expression.core as regex
import quex.input.regular_expression            as regular_expression
import quex.input.code_fragment                 as code_fragment

def parse(fh, Setup):
    # NOTE: Catching of EOF happens in caller: parse_section(...)

    skip_whitespace(fh)
    mode_name = read_identifier(fh)
    if mode_name == "":
        error_msg("missing identifier at beginning of mode definition.", fh)

    # NOTE: constructor does register this mode in the mode_db
    new_mode  = lexer_mode.LexMode(mode_name, fh.name, get_current_line_info_number(fh))

    # (*) inherited modes / options
    skip_whitespace(fh)
    dummy, k = read_until_letter(fh, [":", "{"], Verbose=1)

    if k != 1 and k != 0:
        error_msg("missing ':' or '{' after mode '%s'" % mode_name, fh)

    if k == 0:
        parse_mode_option_list(new_mode, fh)

    # (*) read in pattern-action pairs and events
    pattern_i = -1
    while 1 + 1 == 2:
        pattern_i += 1
        if not parse_mode_element(Setup, new_mode, fh, pattern_i): break


    # (*) check for modes w/o pattern definitions
    # print "## matches = " , repr(new_mode.matches)
    if new_mode.matches == {}:
        if new_mode.options["inheritable:"] != "only":
            new_mode.options["inheritable:"] = "only"
            error_msg("Mode without pattern needs to be 'inheritable only'.\n" + \
                      "<inheritable: only> has been added automatically.", fh,  DontExitF=True)

def parse_mode_option_list(new_mode, fh):
    position = fh.tell()
    try:  
        # ':' => inherited modes/options follow
        skip_whitespace(fh)

        # (*) base modes 
        base_modes, i = read_until_letter(fh, ["{", "<"], Verbose=1)
        new_mode.base_modes = split(base_modes)

        if i != 1: return

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

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while options of mode '%s'." % mode_name, fh)

def parse_mode_element(Setup, new_mode, fh, pattern_i):
    """Returns: False, if a closing '}' has been found.
                True, else.
    """
    position = fh.tell()
    try:
        description = "Pattern or event handler name.\n" + \
                      "Missing closing '}' for end of mode"

        skip_whitespace(fh)
        # NOTE: Do not use 'read_word' since we need to continue directly after
        #       whitespace, if a regular expression is to be parsed.
        position = fh.tell()

        word     = read_until_whitespace(fh)
        if word == "}":
            return False

        # -- check for 'on_entry', 'on_exit', ...
        result = check_for_event_specification(word, fh, new_mode, Setup, pattern_i)
        if result == True: 
            return True # all work has been done in check_for_event_specification()

        elif result == "<<EOF>>":
            pattern = "<<EOF>>"
            pattern_state_machine = regex.do("<<EOF>>", {}, 
                                             Setup.begin_of_stream_code, Setup.end_of_stream_code,
                                             DOS_CarriageReturnNewlineF=Setup.dos_carriage_return_newline_f)

        else:
            fh.seek(position)
            description = "start of mode element: regular expression"
            pattern, pattern_state_machine = regular_expression.parse(fh, Setup)

        position    = fh.tell()

        description = "start of mode element: code fragment for '%s'" % pattern
        parse_action_code(new_mode, fh, Setup, pattern, pattern_state_machine, pattern_i)

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing %s." % description, fh)

    return True



def parse_action_code(new_mode, fh, Setup, pattern, pattern_state_machine, PatternIdx):

    position = fh.tell()
    try:
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
            error_msg("missing token '{', 'PRIORITY-MARK', 'DELETE', or '=>' after '%s'.\n" % pattern + \
                      "found: '%s'" % word, fh)

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing action code for pattern.", fh)

def parse_brief_token_sender(new_mode, fh, pattern, pattern_state_machine, PatternIdx, Setup):

    position = fh.tell()
    try: 
        skip_whitespace(fh)
        position = fh.tell()

        # shorthand for { self.send(TKN_SOMETHING); RETURN; }
        token_name = read_identifier(fh)
        position = fh.tell()

        if token_name == "":
            error_msg("missing token identifier after '=>' shortcut.", fh)

        dummy, bracket_i = read_until_letter(fh, ["(", ";"], Verbose=True)
        if bracket_i == -1 or (dummy != "" and dummy.isspace() == False): 
            error_msg("missing '(' or ';' at end of '=>' token sending statement.", fh)

        if bracket_i == 0:
            token_constructor_args = read_until_closing_bracket(fh, "(", ")")
            # NOTE: empty brackets do not need a comma ...
            token_constructor_args = token_constructor_args.strip()
            if token_constructor_args != "":
                token_constructor_args = ", " + token_constructor_args
            verify_next_word(fh, ";")
        else:
            token_constructor_args = ""
            
        # after 'send' the token queue is filled and one can safely return
        token_name = token_name.strip()
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
    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing token shortcut.", fh)

def check_for_event_specification(word, fh, new_mode, Setup, PatternIdx):

    if word == "on_entry":
        # Event: enter into mode
        code_fragment.parse_unique(fh, "%s::on_entry event handler" % new_mode.name, new_mode.on_entry)
        return True
    
    elif word == "on_exit":
        # Event: exit from mode
        code_fragment.parse_unique(fh, "%s::on_exit event handler" % new_mode.name, new_mode.on_exit)
        return True

    elif word == "on_match":
        # Event: exit from mode
        code_fragment.parse_unique(fh, "%s::on_match event handler" % new_mode.name, new_mode.on_match)
        return True

    elif  word == "on_indentation":
        # Event: start of indentation, 
        #        first non-whitespace after whitespace
        code_fragment.parse_unique(fh, "%s::on_indentation event handler" % new_mode.name, 
                                   new_mode.on_indentation)
        return True

    elif word == "on_failure" or word == "<<FAIL>>":
        # Event: No pattern matched for current position.
        # NOTE: See 'on_end_of_stream' comments.
        code_fragment.parse_unique(fh, "%s::on_failure event handler" % new_mode.name, 
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

