from   quex.frs_py.file_in import *
import quex.lexer_mode     as     lexer_mode
from   quex.token_id_maker import TokenInfo
from   quex.input.setup    import setup as Setup
from   quex.core_engine.utf8 import __read_one_utf8_code_from_stream


def parse(fh, CodeFragmentName, Setup, code_fragment_carrier=None, 
          ErrorOnFailureF=True, AllowBriefTokenSenderF=True):
    """RETURNS: An object of class ReferencedCodeFragment containing
                line number, filename, and the code fragment.

                None in case of failure.
    """
    assert Setup.__class__.__name__ == "something"
    assert code_fragment_carrier.__class__ == lexer_mode.ReferencedCodeFragment \
           or code_fragment_carrier == None

    skip_whitespace(fh)
    position = fh.tell()

    word = fh.read(2)
    if len(word) >= 1 and word[0] == "{":
        fh.seek(-1,1) # unput the second character
        return __parse_normal(fh, CodeFragmentName, code_fragment_carrier)

    elif AllowBriefTokenSenderF and word == "=>":
        return __parse_brief_token_sender(fh, Setup, code_fragment_carrier)

    elif not ErrorOnFailureF:
        fh.seek(-2,1)
        return None
    else:
        error_msg("missing code fragment after %s definition." % CodeFragmentName, fh)

def __prepare_code_fragment_carrier(fh, carrier):
    if carrier == None:
        result = lexer_mode.ReferencedCodeFragment()
    else:
        assert carrier.__class__ == lexer_mode.ReferencedCodeFragment \

        if carrier.line_n != -1:
            error_msg("%s defined twice" % code_fragment_name, fh, DontExitF=True)
            error_msg("previously defined here", carrier.filename, carrier.line_n)
        result = carrier

    # step over all whitespace, such that the first line of the code fragment
    # refers to the first non-whitespace line.
    skip_whitespace(fh)

    # set starting line number and filename
    result.line_n   = get_current_line_info_number(fh) + 1
    result.filename = fh.name

    return result

def __parse_normal(fh, code_fragment_name, code_fragment_carrier):
    result = __prepare_code_fragment_carrier(fh, code_fragment_carrier)

    result.code = read_until_closing_bracket(fh, "{", "}")

    return result

def __parse_brief_token_sender(fh, Setup, code_fragment_carrier):
    # shorthand for { self.send(TKN_SOMETHING); RETURN; }
    
    result = __prepare_code_fragment_carrier(fh, code_fragment_carrier)

    position = fh.tell()
    try: 
        skip_whitespace(fh)
        position = fh.tell()

        character_code = read_character_code(fh)
        if character_code != -1:
            result.code  = "#ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE\n"
            result.code += "self.send(0x%X); return;\n" % character_code
            result.code += "#else\n"
            result.code += "self.send(0x%X); return 0x%X;\n" % (character_code, character_code)
            result.code += "#endif\n"
            return result

        token_name = read_identifier(fh)
        position = fh.tell()

        if token_name == "":
            error_msg("missing token identifier or character code after '=>' shortcut.", fh)

        dummy, bracket_i = read_until_letter(fh, ["(", ";"], Verbose=True)
        if bracket_i == -1 or (dummy != "" and dummy.isspace() == False): 
            error_msg("missing '(' or ';' at end of '=>' token sending statement.", fh)

        token_constructor_args = ""
        plain_token_constructor_args = ""
        if bracket_i == 0:
            plain_token_constructor_args = read_until_closing_bracket(fh, "(", ")")
            # NOTE: empty brackets do not need a comma ...
            plain_token_constructor_args = plain_token_constructor_args.strip()
            if plain_token_constructor_args != "":
                token_constructor_args = ", " + plain_token_constructor_args
            verify_next_word(fh, ";")
            
        # after 'send' the token queue is filled and one can safely return
        token_name = token_name.strip()
        if token_name.find(Setup.input_token_id_prefix) != 0:
            error_msg("token identifier does not begin with token prefix '%s'\n" % Setup.input_token_id_prefix + \
                      "found: '%s'" % token_name, fh)

        # occasionally add token id automatically to database
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

        result.code  = "#ifdef QUEX_OPTION_TOKEN_SENDING_VIA_QUEUE\n"
        result.code += "self.send(%s%s); return;\n" % (token_name, token_constructor_args)
        result.code += "#else\n"
        result.code += "self.send(%s); return %s;\n" % (plain_token_constructor_args, token_name)
        result.code += "#endif\n"

        return result

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

    if start == "0":
        base = fh.read(1)
        if base not in ["x", "o", "b"] and base.isdigit() == False: 
            error_msg("Number base '%s' is unknown, please use '0x' for hexidecimal,\n" + \ 
                      "'0o' for octal, or '0b' for binary.", fh)
        number_txt = read_integer(fh)
        if number_txt = "":
            error_msg("Missing integer number after '0%s'" % base, fh)
        try: 
            if   base == "x": character_code = int("0x" + number_txt, 16) 
            elif base == "o": character_code = int("0o" + number_txt, 8) 
            elif base == "b": 
                for letter in number_txt:
                    character_code = character_code << 1
                    if   letter == 1:   character_code += 1
                    elif letter != "0":
                        error_msg("Letter '%s' not permitted in binary number (something start with '0b')", fh)
            else:
                # A normal integer number (starting with '0' though)
                character_code = int(base + number_text)
        except:
            error_msg("The string '%s' is not appropriate for number base '%s'." % (number_txt, base), fh)

        return character_code

    else:
        # All that remains is that it is a 'normal' integer
        number_txt = read_integer(sh)

        if number_txt = "":
            error_msg("Missing integer number after '0%s'" % base, fh)
        
        try:    return int(number_txt)
        except: error_msg("The string '%s' is not appropriate for number base '10'." % number_txt, fh)

