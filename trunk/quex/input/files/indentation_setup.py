from quex.engine.misc.file_in import get_current_line_info_number, \
                                     error_msg, \
                                     check, \
                                     skip_whitespace, \
                                     read_identifier, \
                                     verify_word_in_list, \
                                     read_integer

from   quex.engine.generator.action_info  import LocalizedParameter
from   quex.engine.interval_handling      import NumberSet
from   quex.engine.state_machine.core     import StateMachine
import quex.input.regular_expression.core as     regular_expression

class IndentationSetup:
    def __init__(self, fh=-1):
        self.fh = fh
        if fh != -1:
            self.file_name = fh.name
            self.line_n    = get_current_line_info_number(fh)
        else:
            self.file_name = "no file handle"
            self.line_n    = -1

        self.space_db = {}  # Maps: space width --> character_set
        self.grid_db  = {}  # Maps: grid width  --> character_set
        self.bad_character_set                = LocalizedParameter("bad",        NumberSet())
        self.newline_state_machine            = LocalizedParameter("newline",    None)
        self.newline_suppressor_state_machine = LocalizedParameter("suppressor", None)
        self.comment_range_state_machine         = LocalizedParameter("comment_range",         None)
        self.comment_nested_range_state_machine  = LocalizedParameter("comment_nested_range",  None)
        self.comment_until_newline_state_machine = LocalizedParameter("comment_until_newline", None)

        self.__containing_mode_name = ""

    def seal(self):
        if len(self.space_db) == 0 and len(self.grid_db) == 0:
            default_space = ord(' ')
            default_tab   = ord('\t')
            bad = self.bad_character_set
            if bad.get().contains(default_space) == False:
                self.specify_space("[ ]", NumberSet(default_space), 1, self.fh)
            if bad.get().contains(default_tab) == False:
                self.specify_grid("[\\t]", NumberSet(default_tab), 4, self.fh)

            if len(self.space_db) == 0 and len(self.grid_db) == 0:
                error_msg("No space or grid defined for indentation counting. Default\n"
                          "values ' ' and '\\t' could not be used since they are specified as 'bad'.",
                          bad.file_name, bad.line_n)

        if self.newline_state_machine.get() is None:
            sm   = StateMachine()
            end_idx = sm.add_transition(sm.init_state_index, NumberSet(ord('\n')), AcceptanceF=True)
            mid_idx = sm.add_transition(sm.init_state_index, NumberSet(ord('\r')), AcceptanceF=False)
            sm.add_transition(mid_idx, NumberSet(ord('\n')), end_idx, AcceptanceF=False)
            self.specify_newline("(\\r\\n)|(\\n)", sm, self.fh)

    def set_containing_mode_name(self, ModeName):
        assert isinstance(ModeName, (str, unicode))
        self.__containing_mode_name = ModeName

    def containing_mode_name(self):
        return self.__containing_mode_name

    def __error_msg_if_defined_earlier(self, Before, FH, Key=None, Name=""):
        """If Key is not None, than 'Before' is a database."""

        if Name in ["newline", "suppressor"] and Before.get() is None: return

        if Key is None:
            if Before.get().is_empty(): return
            error_msg("'" + Before.name + "' has been defined before;", FH, DontExitF=True, WarningF=False)
            error_msg("at this place.", Before.file_name, Before.line_n)
        if Key is not None:
            if Before.has_key(Key) == False: return
            error_msg("'%s' has been defined before for %i;" % (Name, Key), FH, DontExitF=True, WarningF=False)
            error_msg("at this place.", Before[Key].file_name, Before[Key].line_n)

    def __error_msg_if_character_set_empty(self, CharSet, FH):
        if not CharSet.is_empty(): return
        error_msg("Empty character set found.", FH)

    def __error_if_intersection(self, Setting, FH, Name):
        def __error_character_set_intersection(Before):
            error_msg("Character set specification '%s' intersects" % Name, FH, 
                      DontExitF=True, WarningF=False)
            error_msg("with definition for '%s' at this place." % Before.name, 
                      Before.file_name, Before.line_n)

        def __error_state_machine_intersection(Before):
            error_msg("Character set specification '%s' intersects" % Name, FH, 
                      DontExitF=True, WarningF=False)
            error_msg("the ending of the pattern for '%s' at this place." % Before.name, 
                      Before.file_name, Before.line_n,
                      DontExitF=True, WarningF=False)
            error_msg("Note, that 'newline' and cannot end with a character which is subject\n"
                      "to indentation counting (i.e. 'space' or 'grid').", FH)

        if Name == "suppressor":
            # Newline suppressors are totally free. They can contain newlines, indentation count
            # characters and whatsoever. They are not subject to intersection check.
            return
        
        elif Name == "newline":
            assert Setting.__class__ == StateMachine
            assert Setting is not None
            candidate = Setting.get_ending_character_set()
        else:
            assert Setting.__class__ == NumberSet
            candidate = Setting

        # 'space'
        for character_set in self.space_db.values():
            if character_set.get().has_intersection(candidate): 
                __error_character_set_intersection(character_set)

        # 'grid'
        for character_set in self.grid_db.values():
            if character_set.get().has_intersection(candidate):
                __error_character_set_intersection(character_set)

        # 'bad'
        if Name != "newline":
            # 'bad' indentation characters are not subject to indentation counting so they
            # very well intersect with newline or suppressor.
            if self.bad_character_set.get().has_intersection(candidate):                
                __error_character_set_intersection(self.bad_character_set)

        # 'newline'
        if Name != "bad" and self.newline_state_machine.get() is not None:
            # The 'bad' character set can very well appear as the end of newline, since it is
            # not used for indentation counting.
            ending_character_set = self.newline_state_machine.get().get_ending_character_set()
            if ending_character_set.has_intersection(candidate):            
                __error_state_machine_intersection(self.newline_state_machine)

        # 'suppressor'
        # Note, the suppressor pattern is free. No indentation is counted after it. Thus if
        # it ends with characters which are subject to indentation counting, then there is
        # no harm or confusion.

    def __check(self, Name, Before, Setting, FH, Key=None):
        self.__error_msg_if_defined_earlier(Before, FH, Key=Key, Name=Name)
        if Setting.__class__ == NumberSet: 
            self.__error_msg_if_character_set_empty(Setting, FH)
        self.__error_if_intersection(Setting, FH, Name)

    def __specify(self, parameter, Value, PatternStr, FH):
        self.__check(parameter.name, parameter, Value, FH)
        parameter.set(Value, FH)
        parameter.set_pattern_string(PatternStr)

    def specify_space(self, PatternStr, CharSet, Count, FH=-1):
        self.__check("space", self.space_db, CharSet, FH, Key=Count)

        # Note, a space count of '0' is theoretically possible
        self.space_db[Count] = LocalizedParameter("space", CharSet, FH)
        self.space_db[Count].set_pattern_string(PatternStr)

    def specify_grid(self, PatternStr, CharSet, Count, FH=-1):
        self.__check("grid", self.grid_db, CharSet, FH, Key=Count)

        if Count == 0: 
            error_msg("A grid count of 0 is nonsense. May be define a space count of 0.", FH)
        if Count == 1:
            error_msg("Indentation grid counts of '1' are equivalent of to a space\n" + \
                      "count of '1'. The latter is faster to compute.",
                      FH, DontExitF=True)

        self.grid_db[Count] = LocalizedParameter("grid", CharSet, FH)
        self.grid_db[Count].set_pattern_string(PatternStr)

    def specify_bad(self, PatternStr, CharSet, FH=-1):
        self.__specify(self.bad_character_set, CharSet, PatternStr, FH)

    def specify_newline(self, PatternStr, SM, FH=-1):
        self.__specify(self.newline_state_machine, SM, PatternStr, FH)

    def specify_suppressor(self, PatternStr, SM, FH=-1):
        self.__specify(self.newline_suppressor_state_machine, SM, PatternStr, FH)

    def specify_comment_range(self, PatternStr, SM, FH=-1):
        self.__specify(self.comment_range, SM, PatternStr, FH)

    def specify_comment_until_newline(self, PatternStr, SM, FH=-1):
        self.__specify(self.comment_until_newline_state_machine, SM, PatternStr, FH)

    def specify_comment_nested_range(self, PatternStr, SM, FH=-1):
        self.__specify(self.comment_nested_range_state_machine, SM, PatternStr, FH)

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
            # If there is one single variable grid value, then no assumptions can be made
            for value in self.grid_db.keys():
                if type(value) in [str, unicode]: break
            else:
                grid_value_list = sorted(self.grid_db.keys())
                min_grid_value  = min(grid_value_list)
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
            # If there is one single space count depending on a variable, then no assumptions can be made
            for value in self.space_db.keys():
                if type(value) in [str, unicode]: break
            else:
                # If all space values are the same, then they can be replaced by '1' spaces
                if len(self.space_db) == 1 and self.space_db.keys()[0] != 1:
                    space_count, space_def = self.space_db.items()[0]
                    error_msg("Indentation does not contain a grid but only homogenous space counts of %i.\n" \
                              % space_count + \
                              "This setup is equivalent to a setup with space counts of 1. Space counts\n" + \
                              "of 1 are the fastest to compute.", 
                              space_def.file_name, space_def.line_n, DontExitF=True)

    def indentation_count_character_set(self):
        """Returns the superset of all characters that are involved in
           indentation counting. That is the set of character that can
           appear between newline and the first non whitespace character.
        """
        result = NumberSet()
        for character_set in self.space_db.values():
            result.unite_with(character_set.get())
        for character_set in self.grid_db.values():
            result.unite_with(character_set.get())
        return result

    def __repr__(self):

        txt = ""
        txt += "Spaces:\n"
        for count, character_set in sorted(self.space_db.items()):
            if type(count) in [str, unicode]:
                txt += "    %s by %s\n" % (count, character_set.get().get_utf8_string())
            else:
                txt += "    %3i by %s\n" % (count, character_set.get().get_utf8_string())

        txt += "Grids:\n"
        for count, character_set in sorted(self.grid_db.items()):
            if type(count) in [str, unicode]:
                txt += "    %s by %s\n" % (count, character_set.get().get_utf8_string())
            else:
                txt += "    %3i by %s\n" % (count, character_set.get().get_utf8_string())

        txt += "Bad:\n"
        txt += "    %s\n" % self.bad_character_set.get().get_utf8_string()

        txt += "Newline:\n"
        sm = self.newline_state_machine.get()
        if sm is None: txt += "    <none>\n"
        else:          txt += "    %s\n" % sm.get_string(NormalizeF=True, Option="utf8").replace("\n", "\n    ")

        txt += "Suppressor:\n"
        sm = self.newline_suppressor_state_machine.get()
        if sm is None: txt += "    <none>\n"
        else:          txt += "    %s\n" % sm.get_string(NormalizeF=True, Option="utf8").replace("\n", "\n    ")

        return txt

def parse(fh):
    """Parses pattern definitions of the form:
   
          [ \t]                                       => grid 4;
          [:intersection([:alpha:], [\X064-\X066]):]  => space 1;

       In other words the right hand side *must* be a character set.
          
    """
    indent_setup = IndentationSetup(fh)

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)

    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, ">"): 
            indent_setup.seal()
            indent_setup.consistency_check(fh)
            return indent_setup
        
        # A regular expression state machine
        pattern_str, pattern = regular_expression.parse(fh)

        skip_whitespace(fh)
        if not check(fh, "=>"):
            error_msg("Missing '=>' after character set definition.", fh)

        skip_whitespace(fh)
        identifier = read_identifier(fh)
        if identifier == "":
            error_msg("Missing identifier for indentation element definition.", fh)

        verify_word_in_list(identifier, 
                            ["space", "grid", "bad", "newline", "suppressor", 
                             "comment_range", "comment_until_newline", "comment_nested_range"],
                            "Unrecognized indentation specifier '%s'." % identifier, fh)

        skip_whitespace(fh)
        if identifier == "space":
            value = read_value_specifier(fh, "space", 1)
            indent_setup.specify_space(pattern_str, extract_trigger_set(fh, "space", pattern), value, fh)

        elif identifier == "grid":
            value = read_value_specifier(fh, "grid")
            indent_setup.specify_grid(pattern_str, extract_trigger_set(fh, "grid", pattern), value, fh)

        elif identifier == "bad":
            indent_setup.specify_bad(pattern_str, extract_trigger_set(fh, "bad", pattern), fh)

        elif identifier == "newline":
            indent_setup.specify_newline(pattern_str, pattern.sm, fh)

        elif identifier == "suppressor":
            indent_setup.specify_suppressor(pattern_str, pattern.sm, fh)

        elif identifier == "comment_range":
            indent_setup.specify_comment_range(pattern_str, pattern.sm, fh)

        elif identifier == "comment_until_newline":
            indent_setup.specify_comment_until_newline(pattern_str, pattern.sm, fh)

        elif identifier == "comment_nested_range":
            indent_setup.specify_comment_nested_range(pattern_str, pattern.sm, fh)

        else:
            assert False, "Unreachable code reached."

        if not check(fh, ";"):
            error_msg("Missing ';' after indentation '%s' specification." % identifier, fh)


def read_value_specifier(fh, Keyword, Default=None):
    value = read_integer(fh)
    if value is not None: 
        return value
    # not a number received, is it an identifier?
    variable = read_identifier(fh)
    if variable != "":
        return variable
    elif Default is not None:
        return Default
    else:
        error_msg("Missing integer or variable name after keyword '%s'." % Keyword, fh) 


def extract_trigger_set(fh, Keyword, Pattern):
    if len(Pattern.sm.states) != 2:
        error_msg("For indentation '%s' only patterns are addmissible which\n" % Keyword + \
                  "can be matched by a single character, e.g. \" \" or [a-z].", fh)
    transition_map = Pattern.sm.get_init_state().transitions().get_map()
    assert len(transition_map) == 1
    return transition_map.values()[0]

