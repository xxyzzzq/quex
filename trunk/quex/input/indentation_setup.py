
from quex.frs_py.file_in import get_current_line_info_number, \
                                error_msg, \
                                check, \
                                skip_whitespace, \
                                read_identifier, \
                                verify_word_in_list, \
                                parse_assignment, \
                                read_until_whitespace

from   quex.lexer_mode                    import LocalizedParameter
from   quex.core_engine.interval_handling import NumberSet
import quex.input.regular_expression      as regular_expression

class IndentationSetup:
    def __init__(self, fh):
        self.file_name = fh.name
        self.line_n    = get_current_line_info_number(fh)

        self.count_db = {}
        self.specify_count("space", 1)
        self.specify_count("tabulator", -4)

        self.character_set_db = {}
        self.specify_character_set("tabulator", NumberSet(ord("\t")))
        self.specify_character_set("space",     NumberSet(ord(" ")))

    def specify_count(self, Name, Setting, FH=-1):
        self.count_db[Name] = LocalizedParameter("indentation count: '%s'", Setting, FH)

    def specify_character_set(self, Name, Setting, FH=-1):
        self.character_set_db[Name] = LocalizedParameter("indentation character set: '%s'", Setting, FH)

    def consistency_check(self, fh, position):
        # Are there at least some indentation elements?
        if len(filter(lambda x: x.get() != "bad", self.count_db.values())) == 0:
            fh.seek(position)
            error_msg("All possible indentation elements are set to 'bad'.\n" \
                      "No indentation detection possible.", fh)

        # Are all defined elements listed as parameters?
        for identifier in self.character_set_db.keys():
            # If the character set was considered 'bad' it should not be defined.
            count = self.count_db.get(identifier)
            # No character set definition is accepted without that its 'count' is pre-defined.
            assert count != None
            if count.get() != "bad": continue
            error_msg("Indentation element '%s' specified as 'bad'." % identifier,
                      count.file_name, count.line_n, DontExitF=True)
            error_msg("However, a character set has been defined for it.",
                      self.character_set_db[identifier].file_name,
                      self.character_set_db[identifier].line_n)

        # Are all setting elements defined as character sets?
        parameter_set = set(self.character_set_db.keys())
        for identifier in self.count_db.keys():
            if self.character_set_db.has_key(identifier): continue
            error_msg("Count of indentation element '%s' has been specified, but its character set\n" % identifier + \
                      "has not been defined. Add a character set definition in a 'define' section\n" + \
                      "inside the indentation section, e.g. 'indentation { ... define { %s [\\t] }}'." % identifier, 
                      self.count_db[identifier].file_name,
                      self.count_db[identifier].line_n)

    def __repr__(self):
        txt = "Counts:\n"
        L = max(map(len, self.count_db.keys()))
        for name, count in sorted(self.count_db.items()):
            txt += "  %s%s = %s\n" % (name, " " * (L -len(name)), repr(count.get()))

        txt += "Character Sets:\n"
        L = max(map(len, self.character_set_db.keys()))
        for name, character_set in sorted(self.character_set_db.items()):
            txt += "  %s%s --> %s\n" % (name, " " * (L -len(name)), character_set.get().get_utf8_string())

        return txt


def do(fh):
    """Note: EndOfStreamException is to be caught be caller."""
    position = fh.tell()
    indentation_setup = IndentationSetup(fh)

    if not check(fh, "{"):
        error_msg("Missing opening '{' at begin of token_type definition", fh)

    while parse_count(fh, indentation_setup):
        pass

    skip_whitespace(fh)
    if not check(fh, "}"):
        found_str = read_until_whitespace(fh)
        fh.seek(position)
        error_msg("Missing closing '}' at end of token_type definition.\nFound '%s'." % found_str, fh);

    indentation_setup.consistency_check(fh, position)

    return indentation_setup

def parse_count(fh, indentation_setup):
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

    parameter = word

    if parameter == "define":
        parse_character_set(fh, indentation_setup)
    else:
        indentation_setup.specify_count(parameter, parse_parameter_setting(fh, parameter), fh)

    return True

def get_integer(Text):
    try:
        if len(Text) > 2 and Text[:2] == "0x": return int(Text, 16)
        else:                                  return int(Text)
    except:
        return None

def parse_parameter_setting(fh, ParameterName):
    """Parses information about a type of 'whitespace'. Possible values are

       (1) A possitive integer --> number of indentation spaces that it
           shall represent.

       (2) "grid" + possitive integer --> width of the grid on which the 
           character shall snap.

       (3) "bad" --> disallow the particular character.
    """
    value  = parse_assignment(fh)
    if value == "": 
        error_msg("Error while parsing assignment for '%s'." % ParameterName, fh)

    grid_f = False
    fields = value.split()
    if fields[0] == "grid": # Since value != "", the fields[0] is safe.
        grid_f = True
        if len(fields) < 2:
            error_msg("Missing integer after keyword 'grid'.", fh)
        net_value = get_integer(fields[1])
        if net_value == None:
            error_msg("Missing integer after keyword 'grid'.", fh)
        # Negative number means: Grid width
        return - net_value

    # Try to convert to integer
    net_value = get_integer(value) 
    if   net_value != None: 
        return net_value
    elif value == "bad":    
        return "bad"
    else:
        error_msg("Indentation setup: Error, value for '%s' is specified as '%s'.\n" % (ParameterName, value) + \
                  "Example Usages:\n" + \
                  "    space     = 1;      // specifies that spaces shall take 1 indentation space.\n" + \
                  "    tabulator = grid 4; // specifies that tabulators shall be on a 4 space grid.\n" + \
                  "    tabulator = bad;    // tells that tabulators shall not occur in indentation.",
                  fh)
        
def parse_character_set(fh, indentation_setup):
    """Parses pattern definitions of the form:
   
          tabulator [ \t]
          space     [:intersection([:alpha:], [\X064-\X066]):]

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
        identifier = read_identifier(fh)
        if identifier == "":
            error_msg("Missing identifier for indentation element definition.", fh)

        verify_word_in_list(identifier, indentation_setup.count_db.keys(),
                            "Unrecognized character set identifier '%s'." % identifier, fh)

        skip_whitespace(fh)
        if check(fh, "}"): 
            error_msg("Missing character set expression for indentation element '%s'." % identifier, 
                      fh)

        # A regular expression state machine
        pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)

        indentation_setup.specify_character_set(identifier, trigger_set, fh)

