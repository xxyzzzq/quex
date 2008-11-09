from   quex.frs_py.file_in import *
import quex.lexer_mode     as lexer_mode
from   quex.token_id_maker import TokenInfo


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

        token_name = read_identifier(fh)
        position = fh.tell()

        if token_name == "":
            error_msg("missing token identifier after '=>' shortcut.", fh)

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
