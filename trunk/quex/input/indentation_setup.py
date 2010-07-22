
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
        self.setup["spaces"]     = LocalizedParameter("indentation setup: 'spaces'", 1)
        self.setup["tabulators"] = LocalizedParameter("indentation setup: 'tabulators'", -4)

        self.defines["spaces"]     = LocalizedParameter("indentation setup: 'tabulators defintion'",    
                                                        ["[\\t]", NumberSet(ord("\t"))])
        self.defines["tabulators"] = LocalizedParameter("indentation setup: 'spaces definition'", 
                                                        ["[ ]", NumberSet(ord(" "))])

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

    # Are there at least some indentation elements?
    if len(filter(lambda x: x.get() != "bad", indentation_setup.setup)) == 0:
        fh.seek(position)
        error_msg("All possible indentation elements are set to 'bad'.\n" \
                  "No indentation detection possible.", fh)

    # Are all defined elements listed as parameters?
    parameter_set = set(indentation_setup.setup.keys())
    for defined in indentation_setup.defines.keys():
        if defined not in parameter_set:
            error_msg("Indentation element '%s' has been defined, but not parameterized.\n" % defined + \
                      "Add an assignment in the indentation section, e.g. '%s = 3;'." % defined, 
                      indentation_setup.defines[defined].file_name,
                      indentation_setup.defines[defined].line_n)

    # Are all setup elements defined as character sets?
    parameter_set = set(indentation_setup.defines.keys())
    for parameterized in indentation_setup.setup.keys():
        if parameterized not in parameter_set:
            error_msg("Indentation element '%s' has been parameterized, but not defined.\n" % parameterized + \
                      "Add a character set definition in a 'define' section inside the\n" + \
                      "indentation section, e.g. '%s = 3;'." % parameterized, 
                      indentation_setup.setup[parameterized].file_name,
                      indentation_setup.setup[parameterized].line_n)

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

    verify_word_in_list(word, ["spaces", "tabulators", "define"],
                        "Unrecognized indentation setting element '%s'." % word)

    parameter = word

    if parameter == "define":
        # parse a definition of tabulators and spaces
        parse_definitions
    else:
        indentation_setup.setting[parameter] = \
            LocalizedParameter("Indentation setup for '%s'" % parameter,
                               parse_parameter_setting(fh, parameter), fh)

    return True

def parse_parameter_setting(fh, ParameterName):
    """Parses information about a type of 'whitespace'. Possible values are

       (1) A possitive integer --> number of indentation spaces that it
           shall represent.

       (2) "grid" + possitive integer --> width of the grid on which the 
           character shall snap.

       (3) "bad" --> disallow the particular character.
    """
    value  = parse_assignment(fh)
    fields = value.split()

    grid_f = False
    if fields[0] == "grid": grid_f = True

    try:
        # Try to convert to integer
        if len(value) > 2 and value[:2] == "0x": net_value = int(value, 16)
        else:                                    net_value = int(value)
    
        if grid_f: return - net_value
        else:      return net_value

    except:
        pass

    if value != "bad":
        error_msg("indentation setup: value for '%s' is specified as '%s'. It must be either\n" % (ParameterName, value) + \
                  " -- a possitive integer, which specifies the width of the tabulator grid, or\n" + \
                  " -- 'bad' which tells that tabulators are not to be considered for indentation\n" + \
                  "    handling.", fh)

    return "bad"
        
def parse_tabulators_and_spaces_definitions(indentation_setup, fh):
    """Parses pattern definitions of the form:
   
          tabulators    [ \t]
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
            error_msg("Missing identifier for tabulators/spaces definition.", fh)

        skip_whitespace(fh)

        if check(fh, "}"): 
            error_msg("Missing character set expression for tabulators/spaces definition '%s'." % \
                      pattern_name, fh)

        # A regular expression state machine
        pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)

        indentation_setup.defines[pattern_name] = \
                     LocalizedParameter("Pattern definition for '%s'" % pattern_name,
                                        [pattern_str, trigger_set], fh)
