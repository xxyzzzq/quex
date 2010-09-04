
from quex.frs_py.file_in import get_current_line_info_number, \
                                error_msg, \
                                check, \
                                skip_whitespace, \
                                read_identifier, \
                                verify_word_in_list, \
                                parse_assignment, \
                                read_until_whitespace, \
                                read_integer

from   quex.lexer_mode                    import LocalizedParameter
from   quex.core_engine.interval_handling import NumberSet
import quex.input.regular_expression      as regular_expression

class IndentationSetup:
    def __init__(self, fh=-1):
        if fh != -1:
            self.file_name = fh.name
            self.line_n    = get_current_line_info_number(fh)
        else:
            self.file_name = "no file handle"
            self.line_n    = -1

        self.space_db = {}  # Maps: space width --> character_set
        self.grid_db  = {}  # Maps: grid width  --> character_set
        self.bad_character_set                = LocalizedParameter("bad",        NumberSet())
        self.newline_state_machine            = LocalizedParameter("newline",    NumberSet())
        self.newline_suppressor_state_machine = LocalizedParameter("suppressor", NumberSet())

    def seal(self):
        if len(self.space_db) == 0 and len(self.grid_db) == 0:
            self.specify_space("[ ]", NumberSet(ord(' ')), 1)
            self.specify_grid("[\\t]", NumberSet(ord('\t')), 4)

        if self.newline_state_machine.get().is_empty():
            self.specify_newline("\\n", NumberSet(ord('\n')))

    def __error_msg_if_defined_earlier(self, Before, FH, Key=None, Name=""):
        """If Key != None, than 'Before' is a database."""
        if Key == None:
            if Before.get().is_empty():      return
            error_msg("'" + Before.name + "' has been defined before;", FH, DontExitF=True, WarningF=False)
            error_msg("at this place.", Before.file_name, Before.line_n)
        if Key != None:
            if Before.has_key(Key) == False: return
            error_msg("'%s' has been defined before for %i;" % (Name, Key), FH, DontExitF=True, WarningF=False)
            error_msg("at this place.", Before[Key].file_name, Before[Key].line_n)

    def __error_msg_if_character_set_empty(self, CharSet, FH):
        if not CharSet.is_empty(): return
        error_msg("Empty character set found.", FH)

    def __error_if_intersection(self, Setting, FH, Name):
        def __error_msg(Before):
            error_msg("Character set specification '%s' intersects" % Name, FH, 
                      DontExitF=True, WarningF=False)
            error_msg("with definition for '%s' at this place." % Before.name, 
                      Before.file_name, Before.line_n)

        if Setting.__class__.__name__ == StateMachine:
            Setting = Setting.get_init_state().transitions()±²

        for character_set in self.space_db.values():
            if character_set.get().has_intersection(Setting): 
                __error_msg(character_set)

        for character_set in self.grid_db.values():
            if character_set.get().has_intersection(Setting):
                __error_msg(character_set)

        if self.bad_character_set.get().has_intersection(Setting):                
            __error_msg(self.bad_character_set)

        if self.newline_state_machine.get().has_intersection(Setting):            
            __error_msg(self.newline_state_machine)

        if self.newline_suppressor_state_machine.get().has_intersection(Setting): 
            __error_msg(self.newline_suppressor_state_machine)

    def __check(self, Name, Before, Setting, FH, Key=None):
        self.__error_msg_if_defined_earlier(Before, FH, Key=Key, Name=Name)
        if Setting.__class__ == NumberSet: 
            self.__error_msg_if_character_set_empty(Setting, FH)
        self.__error_if_intersection(Setting, FH, Name)

    def specify_space(self, PatternStr, CharSet, Count, FH=-1):
        self.__check("space", self.space_db, CharSet, FH, Key=Count)

        # Note, a space count of '0' is theoretically possible
        self.space_db[Count] = LocalizedParameter("space", CharSet, FH)
        self.space_db[Count].pattern_str = PatternStr

    def specify_grid(self, PatternStr, CharSet, Count, FH=-1):
        self.__check("grid", self.grid_db, CharSet, FH, Key=Count)

        if Count == 0: 
            error_msg("A grid count of 0 is nonsense. May be define a space count of 0.", FH)
        if Count == 1:
            error_msg("Indentation grid counts of '1' are equivalent of to a space\n" + \
                      "count of '1'. The latter is faster to compute.",
                      FH, DontExitF=True)

        self.grid_db[Count] = LocalizedParameter("grid", CharSet, FH)
        self.grid_db[Count].pattern_str = PatternStr

    def specify_bad(self, PatternStr, CharSet, FH=-1):
        self.__check("bad", self.bad_character_set, CharSet, FH)
        self.bad_character_set = LocalizedParameter("bad", CharSet, FH)
        self.bad_character_set.pattern_str = PatternStr

    def specify_newline(self, PatternStr, SM, FH=-1):
        self.__check("newline", self.newline_state_machine, SM, FH)
        self.newline_state_machine = LocalizedParameter("newline", SM, FH)
        self.newline_state_machine.pattern_str = PatternStr

    def specify_suppressor(self, PatternStr, SM, FH=-1):
        self.__check("suppressor", self.newline_suppressor_state_machine, SM, FH)
        self.newline_suppressor_state_machine = LocalizedParameter("suppressor", SM, FH)
        self.newline_suppressor_state_machine.pattern_str = PatternStr

    def has_only_single_spaces(self):
        # Note, from about the grid_db does not accept grid values of '1'
        if   len(self.grid_db) != 0:   return False
        elif len(self.space_db) != 1 : return False
        # Here, the space_db can have only one value. If it is '1' than 
        # the indentation is based soley on single spaces.
        return self.space_db.has_key(1)

    def consistency_check(self, fh):
        # Are the required elements present for indentation handling?
        if len(self.space_db) == 0 and len(self.grid_db) == 0:
            error_msg("No whitespace defined for indentation. Define at least one 'space' or 'grid'." +
                      "No indentation detection possible.", fh)

        if self.newline_state_machine.get().is_empty():
            error_msg("No newline character set has been specified." + \
                      "No indentation detection possible.", fh)

        # If there are no spaces and the grid is on a homogenous scale,
        # => then the grid can be transformed into 'easy-to-compute' spaces.
        if len(self.space_db) == 0:
            grid_value_list = sorted(self.grid_db.keys())
            min_grid_value  = min(self.grid_db.keys())
            # Are all grid values a multiple of the minimum?
            if len(filter(lambda x: x % min_grid_value == 0, grid_value_list)) == len(grid_value_list):
                grid_def = self.grid_db[min_grid_value]
                error_msg("Indentation setup does not contain spaces, only grids (tabulators). All grid\n" + \
                          "widths are multiples of %i. The grid setup %s\n" \
                          % (min_grid_value, repr(sorted(grid_value_list))[1:-1]) + \
                          "is equivalent to a setup with space counts %s.\n" \
                          % repr(map(lambda x: x / min_grid_value, sorted(grid_value_list)))[1:-1] + \
                          "Space counts are faster to compute.", 
                          grid_def.file_name, grid_def.line_n, DontExitF=True)

        elif len(self.grid_db) == 0:
            # If all space values are the same, then they can be replaced by '1' spaces
            if len(self.space_db) == 1 and self.space_db.keys()[0] != 1:
                space_count, space_def = self.space_db.items()[0]
                error_msg("Indentation does not contain a grid but only homogenous space counts of %i.\n" % space_count + \
                          "This setup is equivalent to a setup with space counts of 1. Space counts\n" + \
                          "of 1 are the fastest to compute.", 
                          space_def.file_name, space_def.line_n, DontExitF=True)

    def __repr__(self):

        txt = ""
        txt += "Spaces:\n"
        for count, character_set in sorted(self.space_db.items()):
            txt += "    %3i by %s\n" % (count, character_set.get().get_utf8_string())

        txt += "Grids:\n"
        for count, character_set in sorted(self.grid_db.items()):
            txt += "    %3i by %s\n" % (count, character_set.get().get_utf8_string())

        txt += "Bad:\n"
        txt += "    %s\n" % self.bad_character_set.get().get_utf8_string()

        txt += "Newline:\n"
        txt += "    %s\n" % self.newline_state_machine.get().get_utf8_string()

        txt += "Suppressor:\n"
        txt += "    %s\n" % self.newline_suppressor_state_machine.get().get_utf8_string()

        return txt

def do(fh):
    """Parses pattern definitions of the form:
   
          [ \t]                                       => grid 4;
          [:intersection([:alpha:], [\X064-\X066]):]  => space 1;

       In other words the right hand side *must* be a character set.
          
    """
    indentation_setup = IndentationSetup(fh)

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)

    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, ">"): 
            indentation_setup.seal()
            indentation_setup.consistency_check(fh)
            return indentation_setup
        
        # A regular expression state machine
        pattern_str, state_machine = regular_expression.parse(fh)

        skip_whitespace(fh)
        if not check(fh, "=>"):
            error_msg("Missing '=>' after character set definition.", fh)

        skip_whitespace(fh)
        identifier = read_identifier(fh)
        if identifier == "":
            error_msg("Missing identifier for indentation element definition.", fh)

        verify_word_in_list(identifier, 
                            ["space", "grid", "bad", "newline", "suppressor"],
                            "Unrecognized indentation specifier '%s'." % identifier, fh)

        trigger_set = None
        if identifier in ["space", "bad", "grid"]:
            if len(state_machine.states) != 2:
                error_msg("For indentation '%s' only patterns are addmissible which\n" % identifier + \
                          "can be matched by a single character, e.g. \" \" or [a-z].", fh)
            transition_map = state_machine.get_init_state().transitions().get_map()
            assert len(transition_map) == 1
            trigger_set = transition_map.values()[0]

        skip_whitespace(fh)
        if identifier == "space":
            value = read_integer(fh)
            if value == None: value = 1
            indentation_setup.specify_space(pattern_str, trigger_set, value, fh)

        elif identifier == "grid":
            value = read_integer(fh)
            if value == None: error_msg("Missing integer after keyword 'grid'.", fh) 
            indentation_setup.specify_grid(pattern_str, trigger_set, value, fh)

        elif identifier == "bad":
            indentation_setup.specify_bad(pattern_str, trigger_set, fh)

        elif identifier == "newline":
            indentation_setup.specify_newline(pattern_str, state_machine, fh)

        elif identifier == "suppressor":
            indentation_setup.specify_suppressor(pattern_str, state_machine, fh)

        else:
            assert False, "Unreachable code reached."

        if not check(fh, ";"):
            error_msg("Missing ';' after indentation '%s' specification." % identifier, fh)



