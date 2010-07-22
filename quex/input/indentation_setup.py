
from quex.frs_py.file_in import get_current_line_info_number, \
                                error_msg, \
                                check, \
                                skip_whitespace, \
                                read_identifier, \
                                verify_word_in_list, \
                                parse_assignment, \
                                read_until_whitespace
from quex.lexer_mode     import LocalizedParameter

import quex.input.regular_expression  as regular_expression

class IndentationSetup:
    def __init__(self):
        self.spaces_addmissible_f = LocalizedParameter("indentation setup: 'spaces'", True)
        self.tabulator_grid_width = LocalizedParameter("indentation setup: 'tabs'",   4)
        self.tabs_definition      = LocalizedParameter("indentation setup: 'tabs defintion'",    ["[\\t]", ])
        self.spaces_definition    = LocalizedParameter("indentation setup: 'spaces definition'", ["[ ]", ])

def do(fh):
    """Note: EndOfStreamException is to be caught be caller."""
    position = fh.tell()
    indentation_setup = IndentationSetup()

    if not check(fh, "{"):
        error_msg("Missing opening '{' at begin of token_type definition", fh)

    while parse_setting(fh, indentation_setup):
        pass

    skip_whitespace(fh)
    if not check(fh, "}"):
        found_str = read_until_whitespace(fh)
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type definition.\nFound '%s'." % found_str, fh);

    if      indentation_setup.spaces_addmissible_f.get() == False \
        and indentation_setup.tabulator_grid_width.get() == -1:
        fh.seek(position)
        error_msg("Tabulators and spaces have both been de-activated.\n" \
                  "No indentation detection possible.", fh)

    return indentation_setup

def parse_setting(fh, indentation_setup):
    """NOTE: The feature of 'indentation inhibitor' has been declined for two 
             reasons:

             -- the inhibitor would require a space to delimit the regular 
                expression and the ';' to delimit the assigment statement.
                this could cause very confusing errors.
             -- inhibitors would have to be webbed into the modes which 
                increases complexity.
             -- inhibitors can be programmed easily by having pattern actions
                such as 

                {BACKSLASHED_NEWLINE} {
                    indentation_stack.sleep();
                }
    """
    position = fh.tell()
    skip_whitespace(fh)
    word = read_identifier(fh)
    if word == "": 
        return False

    verify_word_in_list(word, ["spaces", "tabs", "define"],
                        "Unrecognized indentation setting element '%s'." % word)

    parameter = word
    value     = parse_assignment(fh)

    if parameter == "spaces":
        verify_word_in_list(value, ["good", "bad"],
                            "indentation setup: Value for 'spaces' set to '%s'" % value)
        if value == "good": indentation_setup.spaces_addmissible_f.set(True, fh)
        else:               indentation_setup.spaces_addmissible_f.set(False, fh)

    elif parameter == "tabs":
        try:
            # Try to convert to integer
            if len(value) > 2 and value[:2] == "0x": net_value = int(value, 16)
            else:                                    net_value = int(value)
            indentation_setup.tabulator_grid_width.set(net_value, fh)
            return True
        except:
            pass

        if value != "bad":
            error_msg("indentation setup: value for 'tabs' is specified as '%s'. It must be either\n" % value + \
                      " -- a possitive integer, which specifies the width of the tabulator grid, or\n" + \
                      " -- 'bad' which tells that tabs are not to be considered for indentation\n" + \
                      "    handling.", fh)
        indentation_setup.tabulator_grid_width.set(-1, fh) # '-1' tells that tabulators are 'bad'

    elif parameter == "define":
        # parse a definition of tabs and spaces

    return True

        
def parse_tabs_and_spaces_definitions(indentation_setup, fh):
    """Parses pattern definitions of the form:
   
          tabs    [ \t]
          spaces  [:intersection([:alpha:], [\X064-\X066]):]

       In other words the right hand side *must* be a character set.
          
    """
    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)
    if not check(fh, "{"):
        error_msg("indentation setup: define region must start with opening '{'.", fh)

    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, "}"): 
            return
        
        # -- get the name of the pattern
        skip_whitespace(fh)
        pattern_name = read_identifier(fh)
        if pattern_name == "":
            error_msg("Missing identifier for tabs/spaces definition.", fh)

        verify_word_in_list(pattern_name, ["spaces", "tabs"],
                            "Unrecognized indentation setting element '%s'." % word)

        skip_whitespace(fh)

        if check(fh, "}"): 
            error_msg("Missing character set expression for tabs/spaces definition '%s'." % \
                      pattern_name, fh)

        # A regular expression state machine
        pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)

        { "tabs":   indentation_setup.spaces_definition,
          "spaces": indentation_setup.tabs_definition,
        }[pattern_name].set([pattern_str, trigger_set], fh)
