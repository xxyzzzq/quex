from   quex.frs_py.file_in import *
import quex.lexer_mode     as     lexer_mode
from   quex.output.cpp.token_id_maker         import TokenInfo
from   quex.input.setup                       import setup as Setup
from   quex.input.ucs_db_parser               import ucs_property_db
from   quex.core_engine.utf8                  import __read_one_utf8_code_from_stream
from   quex.core_engine.generator.action_info import *



def parse(fh, CodeFragmentName, 
          ErrorOnFailureF=True, AllowBriefTokenSenderF=True, ContinueF=True):
    """RETURNS: An object of class UserCodeFragment containing
                line number, filename, and the code fragment.

                None in case of failure.
    """
    assert Setup.__class__.__name__ == "something"
    assert type(ErrorOnFailureF)        == bool
    assert type(AllowBriefTokenSenderF) == bool

    skip_whitespace(fh)
    position = fh.tell()

    word = fh.read(2)
    if len(word) >= 1 and word[0] == "{":
        fh.seek(-1, 1) # unput the second character
        return __parse_normal(fh, CodeFragmentName)

    elif AllowBriefTokenSenderF and word == "=>":
        return __parse_brief_token_sender(fh, ContinueF)

    elif not ErrorOnFailureF:
        fh.seek(-2,1)
        return None
    else:
        error_msg("Missing code fragment after %s definition." % CodeFragmentName, fh)

def __parse_normal(fh, code_fragment_name):
    LanguageDB = Setup.language_db

    line_n = get_current_line_info_number(fh) + 1
    code   = read_until_closing_bracket(fh, "{", "}")
    return UserCodeFragment(code, fh.name, line_n, LanguageDB)

def __parse_brief_token_sender(fh, ContinueF):
    # shorthand for { self.send(TKN_SOMETHING); QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN(); }
    LanguageDB = Setup.language_db
    
    position = fh.tell()
    line_n   = get_current_line_info_number(fh) + 1
    try: 
        skip_whitespace(fh)
        position = fh.tell()

        code = __parse_token_id_specification_by_character_code(fh)
        if code != -1: 
            code = __create_token_sender_by_character_code(fh, code)
        else:
            skip_whitespace(fh)
            identifier = read_identifier(fh)
            skip_whitespace(fh)
            if identifier in ["GOTO", "GOSUB", "GOUP"]:
                code = __create_mode_transition_and_token_sender(fh, identifier)
            else:
                code = __create_token_sender_by_token_name(fh, identifier)

        if code != "": 
            if ContinueF: code += "QUEX_SETTING_AFTER_SEND_CONTINUE_OR_RETURN();\n"
            return UserCodeFragment(code, fh.name, line_n, LanguageDB)
        else:
            return None

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing token shortcut.", fh)

def read_character_code(fh):
    # NOTE: This function is tested with the regeression test for feature request 2251359.
    #       See directory $QUEX_PATH/TEST/2251359.
    pos = fh.tell()
    
    start = fh.read(1)
    if start == "":  
        seek(pos); return -1

    elif start == "'": 
        # read an utf-8 char an get the token-id
        # Example: '+'
        character_code = __read_one_utf8_code_from_stream(fh)
        if character_code == 0xFF:
            error_msg("Missing utf8-character for definition of character code by character.", fh)

        elif fh.read(1) != '\'':
            error_msg("Missing closing ' for definition of character code by character.", fh)

        return character_code

    if start == "U":
        if fh.read(1) != "C": seek(pos); return -1
        # read Unicode Name 
        # Example: UC MATHEMATICAL_MONOSPACE_DIGIT_FIVE
        skip_whitespace(fh)
        ucs_name = read_identifier(fh)
        if ucs_name == "": seek(pos); return -1
        # Get the character set related to the given name. Note, the size of the set
        # is supposed to be one.
        character_code = ucs_property_db.get_character_set("Name", ucs_name)
        if type(character_code) in [str, unicode]:
            verify_word_in_list(ucs_name, ucs_property_db["Name"].code_point_db,
                                "The string %s\ndoes not identify a known unicode character." % ucs_name, 
                                fh)
        elif type(character_code) not in [int, long]:
            error_msg("%s relates to more than one character in unicode database." % ucs_name, fh) 
        return character_code

    second = fh.read(1)
    if start == "0" and second.isdigit() == False:
        base = second
        if base not in ["x", "o", "b"]: 
            error_msg("Number base '0%s' is unknown, please use '0x' for hexidecimal,\n" % base + \
                      "'0o' for octal, or '0b' for binary.", fh)
        number_txt = read_integer(fh)
        if number_txt == "":
            error_msg("Missing integer number after '0%s'" % base, fh)
        try: 
            if   base == "x": character_code = int("0x" + number_txt, 16) 
            elif base == "o": character_code = int(number_txt, 8) 
            elif base == "b": 
                character_code = 0
                for letter in number_txt:
                    character_code = character_code << 1
                    if   letter == "1":   character_code += 1
                    elif letter != "0":
                        error_msg("Letter '%s' not permitted in binary number (something start with '0b')" % letter, fh)
            else:
                # A normal integer number (starting with '0' though)
                character_code = int(base + number_text)
        except:
            error_msg("The string '%s' is not appropriate for number base '0%s'." % (number_txt, base), fh)

        return character_code

    elif start.isdigit():
        fh.seek(-2, 1) # undo 'start' and 'second'
        # All that remains is that it is a 'normal' integer
        number_txt = read_integer(fh)

        if number_txt == "": fh.seek(pos); return -1
        
        try:    return int(number_txt)
        except: error_msg("The string '%s' is not appropriate for number base '10'." % number_txt, fh)

    else:
        # Try to interpret it as something else ...
        fh.seek(pos); return -1               

def __parse_function_argument_list(fh, ReferenceName):
    argument_list = []
    position = fh.tell()
    try:
        # Read argument list
        tmp = fh.read(1)
        if   tmp == ";":
            return []
        elif tmp != "(":
            error_msg("Missing '(' or ';' after '%s'." % ReferenceName, fh)
        
        text = ""
        while 1 + 1 == 2:
            tmp = fh.read(1)
            if   tmp == ")": 
                verify_next_word(fh, ";")
                break
            elif tmp in ["(", "[", "{"]:
                closing_bracket = {"(": ")", "[": "]", "{": "}"}[tmp]
                text += tmp + read_until_closing_bracket(fh, tmp, closing_bracket) + closing_bracket
            elif tmp == "\"":
                text += tmp + read_until_closing_bracket(fh, "", "\"", IgnoreRegions = []) + "\"" 
            elif tmp == "'":
                text += tmp + read_until_closing_bracket(fh, "", "'", IgnoreRegions = []) + "'" 
            elif tmp == ",":
                argument_list.append(text)
                text = ""
            elif tmp == "":
                fh.seek(position)
                error_msg("End of file reached while parsing argument list for %s." % ReferenceName, fh)
            else:
                text += tmp

        if text != "": argument_list.append(text)

        argument_list = map(lambda arg:    arg.strip(), argument_list)
        argument_list = filter(lambda arg: arg != "",   argument_list)
        return argument_list

    except EndOfStreamException:
        fh.seek(position)
        error_msg("End of file reached while parsing token shortcut.", fh)

def __parse_token_id_specification_by_character_code(fh):
    character_code = read_character_code(fh)
    if character_code == -1: return -1
    verify_next_word(fh, ";")
    return character_code

def __create_token_sender_by_character_code(fh, CharacterCode):
    prefix_less_token_name = "UCS_0x%06X" % CharacterCode
    token_id_str = Setup.token_id_prefix + prefix_less_token_name
    lexer_mode.token_id_db[prefix_less_token_name] = \
            TokenInfo(prefix_less_token_name, CharacterCode, None, fh.name, get_current_line_info_number(fh)) 
    return "self_send(%s);\n" % token_id_str

def verify_token_prefix_or_die(fh, TokenName):
    global Setup
    if TokenName.find(Setup.token_id_prefix) != 0:
        error_msg("Token identifier does not begin with token prefix '%s'\n" % Setup.token_id_prefix + \
                  "found: '%s'" % TokenName, fh)

def token_id_db_verify_or_enter_token_id(fh, TokenName):
    global Setup

    verify_token_prefix_or_die(fh, TokenName)

    prefix_less_TokenName = TokenName[len(Setup.token_id_prefix):]
    # Occasionally add token id automatically to database
    if not lexer_mode.token_id_db.has_key(prefix_less_TokenName):
        # DO NOT ENFORCE THE TOKEN ID TO BE DEFINED, BECAUSE WHEN THE TOKEN ID
        # IS DEFINED IN C-CODE, THE IDENTIFICATION IS NOT 100% SAFE.
        msg = "Token id '%s' defined implicitly." % TokenName
        if TokenName in lexer_mode.token_id_db.keys():
            msg += "\nNOTE: '%s' has been defined in a token { ... } section!" % \
                   (Setup.token_id_prefix + TokenName)
            msg += "\nNote, that tokens in the token { ... } section are automatically prefixed."
        error_msg(msg, fh, DontExitF=True)

        # Enter the implicit token id definition in the database
        lexer_mode.token_id_db[prefix_less_TokenName] = \
                TokenInfo(prefix_less_TokenName, None, None, fh.name, get_current_line_info_number(fh)) 

def __create_token_sender_by_token_name(fh, TokenName):
    assert type(TokenName) in [str, unicode]

    # Enter token_id into database, if it is not yet defined.
    token_id_db_verify_or_enter_token_id(fh, TokenName)

    # Parse the token argument list
    argument_list = __parse_function_argument_list(fh, TokenName)

    # Create the token sender
    explicit_member_names_f = False
    for arg in argument_list:
        if arg.find("=") != -1: explicit_member_names_f = True

    assert lexer_mode.token_type_definition != None, \
           "A valid token_type_definition must have been parsed at this point."

    if not explicit_member_names_f:
        # There are only two allowed cases for implicit token member names:
        #  QUEX_TKN_XYZ(Lexeme)     --> call take_text(Lexeme, LexemeEnd)
        #  QUEX_TKN_XYZ(Begin, End) --> call to take_text(Begin, End)
        if   len(argument_list) == 2:
            return "QUEX_NAME_TOKEN(take_text)(self_token_p(), &self, (%s), (%s));\n" % \
                   (argument_list[0], argument_list[1]) + \
                   "self_send(%s);\n" % (TokenName)

        elif len(argument_list) == 1:
            if argument_list[0] == "Lexeme":
                return "QUEX_NAME_TOKEN(take_text)(self_token_p(), &self, LexemeBegin, LexemeEnd);\n" \
                       "self_send(%s);\n" % (TokenName)
            elif argument_list[0] == "LexemeNull":
                return "QUEX_NAME_TOKEN(take_text)(self_token_p(), &self, LexemeNull, LexemeNull);\n" \
                       "self_send(%s);\n" % (TokenName)
            else:
                error_msg("When one unnamed argument is specified it must be 'Lexeme'\n"
                          "or 'LexemeNull'. Found '%s'" % argument_list[0], fh)

        elif len(argument_list) == 0:
            return "self_send(%s);\n" % TokenName

        else:
            error_msg("Since 0.49.1, there are only the following brief token senders that can take\n"
                      "unnamed token arguments:\n"
                      "     one argument:   'Lexeme'   =>  token.take_text(..., LexemeBegin, LexemeEnd);\n"
                      "     two arguments:  Begin, End =>  token.take_text(..., Begin, End);\n"
                      + "Found: " + repr(argument_list)[1:-1] + ".", fh)

        # Returned from Function if implicit member names

    member_value_pairs = map(lambda x: x.split("="), argument_list)
    txt = ""
    for member, value in member_value_pairs:
        if value == "":
            error_msg("One explicit argument name mentioned requires all arguments to\n" + \
                      "be mentioned explicitly. Value '%s' mentioned without argument.\n" \
                      % member, fh)

        else:
            member_name = member.strip()
            verify_word_in_list(member_name, lexer_mode.token_type_definition.get_member_db(), 
                                "No member:   '%s' in token type description." % member_name, 
                                fh)
            access = lexer_mode.token_type_definition.get_member_access(member_name)
            txt += "self_token_p()->%s = %s;\n" % (access, value.strip())


    # Box the token, stamp it with an id and 'send' it
    txt += "self_send(%s);\n" % TokenName
    return txt

def __create_mode_transition_and_token_sender(fh, Command):
    assert Command in ["GOTO", "GOSUB", "GOUP"]

    position     = fh.tell()
    LanguageDB   = Setup.language_db
    target_mode  = ""
    token_sender = ""
    if check(fh, "("):
        skip_whitespace(fh)
        target_mode = read_identifier(fh)
        skip_whitespace(fh)
        if check(fh, ")"):
            token_sender = ""
        elif check(fh, ","):
            skip_whitespace(fh)
            token_name = read_identifier(fh)
            skip_whitespace(fh)
            token_sender = __create_token_sender_by_token_name(fh, token_name)
            if check(fh, ")") == False:
                fh.seek(position)
                error_msg("Missing closing ')' for %s." % Command, fh)
        else:
            fh.seek(position)
            error_msg("Missing closing ')' or ',' after '%s'." % target_mode, fh)
    elif check(fh, ";") == False:
        error_msg("Missing ')' or ';' after '%s'." % Command, fh)

    if Command in ["GOTO", "GOSUB"] and target_mode == "": 
        error_msg("The %s requires at least one argument: The target mode." % Command, fh)

    # Code for mode change
    txt = { 
        "GOTO":  LanguageDB["$goto-mode"],
        "GOSUB": LanguageDB["$gosub-mode"],
        "GOUP":  LanguageDB["$goup-mode"],
    }[Command](target_mode)

    # Code for token sending
    txt += token_sender

    return txt

