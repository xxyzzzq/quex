from quex.frs_py.file_in import get_current_line_info_number, error_msg
from quex.lexer_mode     import LocalizedParameter

class IndentationSetup:
    def __init__(self):
        self.spaces_addmissible_f = LocalizedParameter("indentation setup: 'spaces'", True)
        self.tabulator_grid_width = LocalizedParameter("indentation setup: 'tabs'",   4)

def do(fh):
    indentation_setup = IndentationSetup()

    if not check(fh, "{"):
        error_msg("Missing opening '{' at begin of token_type definition", fh)

    while parse_setting(fh, indentation_setup):
        pass

    if not check(fh, "}"):
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type definition.", fh);

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
    if word == "": return False

    verify_word_in_list(word, ["spaces", "tabs"],
                        "Unrecognized indentation setting parameter '%s'." % word)

    parameter = word
    value     = parse_assignment(fh)

    if parameter == "spaces":
        verify_word_in_list(value, ["spaces", "tabs"],
                            "indentation setup: 'spaces' set to '%s'" % value)
        if value == "good": indentation_setup.spaces_addmissible_f.set(True, fh)
        else:               indentation_setup.spaces_addmissible_f.set(False, fh)

    elif parameter == "tabs":
        # Try to convert to integer
        try:
            if len(value) > 2 and value[:2] == "0x": net_value = int(value, 16)
            else:                                    net_value = int(value)
            indentation_setup.tabulator_grid_width.set(net_value, fh)
        except:
            pass

        if value != "bad":
            error_msg("indentation setup: 'tabs' must be either set to\n" + \
                      " -- a possitive integer, which specifies the width of the tabulator grid, or\n" + \
                      " -- 'bad' which tells that tabs are not to be considered for indentation\n" + \
                      "    handling.", fh)
        indentation_setup.tabulator_grid_width.set(-1, fh) # '-1' tells that tabulators are 'bad'

    return True

        
