from quex.engine.misc.file_in import get_current_line_info_number, \
                                     error_msg, \
                                     check, \
                                     check_or_die, \
                                     skip_whitespace, \
                                     read_identifier, \
                                     verify_word_in_list, \
                                     read_integer

from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.generator.code.base            import LocalizedParameter
from   quex.engine.interval_handling              import NumberSet
from   quex.engine.state_machine.core             import StateMachine
from   quex.engine.counter                        import CounterSetupIndentation, \
                                                         CounterSetupLineColumn
import quex.input.regular_expression.core         as     regular_expression

class Base:
    def __init__(self, fh, Name, IdentifierList):
        self.fh = fh
        if fh != -1:
            self.file_name = fh.name
            self.line_n    = get_current_line_info_number(fh)
        else:
            self.file_name = "no file handle"
            self.line_n    = -1

        self.space_db               = {}  # Maps: space width --> character_set
        self.grid_db                = {}  # Maps: grid width  --> character_set
        self.identifier_list        = IdentifierList
        self.name                   = Name
        self.__containing_mode_name = ""

    def set_containing_mode_name(self, ModeName):
        assert isinstance(ModeName, (str, unicode))
        self.__containing_mode_name = ModeName

    def containing_mode_name(self):
        return self.__containing_mode_name

    def _check(self, Name, Before, Setting, FH, Key=None):
        self._error_msg_if_defined_earlier(Before, FH, Key=Key, Name=Name)
        if Setting.__class__ == NumberSet: 
            self._error_msg_if_character_set_empty(Setting, FH)
        self._error_if_intersection(Setting, FH, Name)

    def _specify(self, parameter, Value, PatternStr, FH):
        self._check(parameter.name, parameter, Value, FH)
        parameter.set(Value, FH)
        parameter.set_pattern_string(PatternStr)

    def specify_space(self, Pattern, Count, FH=-1):
        CharSet = extract_trigger_set(FH, "space", Pattern)

        self._check("space", self.space_db, CharSet, FH, Key=Count)

        # Note, a space count of '0' is theoretically possible
        entry = self.space_db.get(Count)
        if entry is not None:
            entry.get().unite_with(CharSet)
        else:
            self.space_db[Count] = LocalizedParameter("space", CharSet, FH, PatternStr)

    def specify_grid(self, Pattern, Count, FH=-1):
        CharSet = extract_trigger_set(FH, "grid", Pattern)

        self._check("grid", self.grid_db, CharSet, FH, Key=Count)

        if Count == 0: 
            error_msg("A grid count of 0 is nonsense. May be define a space count of 0.", FH)
        if Count == 1:
            error_msg("Indentation grid counts of '1' are equivalent of to a space\n" + \
                      "count of '1'. The latter is faster to compute.",
                      FH, DontExitF=True)

        entry = self.grid_db.get(Count)
        if entry is not None:
            entry.get().unite_with(CharSet)
        else:
            self.grid_db[Count] = LocalizedParameter("grid", CharSet, FH, PatternStr)

    def homogeneous_spaces(self):
        # Note, from about the grid_db does not accept grid values of '1'
        if   len(self.grid_db) != 0:   return False
        elif len(self.space_db) != 1 : return False
        # Here, the space_db can have only one value. If it is '1' than 
        # the indentation is based soley on single spaces.
        return self.space_db.has_key(1)

    def get_count_command_map(self, CharacterSet, ColumnNPerChunk=None):
        """Returns a list of NumberSet objects where for each X of the list it holds:

             (i)  X is subset of CharacterSet
                   
             (ii) It is related to a different counter action than Y,
                  for each other object Y in the list.

           RETURNS: 

                        map:  CLIID -->  (NumberSet, CommandList)

           NOTE: A 'CLIID' is a UNIQUE incidence id served by 'dial_db'. 
                 => Can be used for terminals implementing the CommandList. 

           where each entry means: "If an input character lies in NumberSet
           then the counting action given by CommandList has to be executed.
           The CommandList is distinctly associated with a CLIID, a command
           list index.
        """
        ColumnNPerChunk = self.get_column_number_per_chunk(CharacterSet)

        def pruned_iteritems(Db, CharacterSet):
            for value, character_set in Db.iteritems():
                if CharacterSet is None: pruned = character_set
                else:                    pruned = character_set.intersection(CharacterSet)
                if pruned.is_empty():    continue
                yield value, pruned

        def on_special(Delta):
            if ColumnNPerChunk is None:  return ColumnCountAdd(Delta)
            else:                        return None

        def on_grid(GridStepN):
            if ColumnNPerChunk is None:  return ColumnCountGridAdd(GridStepN)
            else:                        return ColumnCountGridAddWithReferenceP(GridStepN, 
                                                                                 self.iterator_name,
                                                                                 ColumnNPerChunk)

        def on_newline(Delta):
            if ColumnNPerChunk is None: return LineCountAdd(Delta)
            else:                       return LineCountAddWithReferenceP(Delta, 
                                                                          self.iterator_name, 
                                                                          ColumnNPerChunk)

        result = {}
        for delta, character_set in pruned_iteritems(self.special, CharacterSet):
            cmd = on_special(delta)
            if cmd is None: cl = CommandList()
            else:           cl = CommandList(cmd)
            result[dial_db.new_incidence_id()] = CountCmdInfo(character_set, cl, E_CharacterCountType.CHARACTER)

        result.update(
            (dial_db.new_incidence_id(),
             CountCmdInfo(character_set, CommandList(on_grid(grid_step_n)), E_CharacterCountType.GRID))
            for grid_step_n, character_set in pruned_iteritems(self.grid, CharacterSet)
        )
        result.update(
            (dial_db.new_incidence_id(), 
             CountCmdInfo(character_set, CommandList(on_newline(delta)), E_CharacterCountType.LINE))
            for delta, character_set in pruned_iteritems(self.newline, CharacterSet)
        )

        if column_count_per_chunk is not None:
            on_before_reload = [
                ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                              self.column_count_per_chunk)
            ]
            on_after_reload = [
                ColumnCountReferencePSet(self.iterator_name)
            ]

        return ColumnNPerChunk, result, on_before_reload, on_after_reload

    def consistency_check(self, fh):
        def check_grid_values_integer_multiples(GridDB):
            """If there are no spaces and the grid is on a homogeneous scale,
               => then the grid can be transformed into 'easy-to-compute' spaces.
            """
            # If there is one single variable grid value, then no assumptions can be made
            for value in GridDB.iterkeys():
                if type(value) in [str, unicode]: 
                    return

            grid_value_list = sorted(GridDB.keys())
            min_grid_value  = min(grid_value_list)
            # Are all grid values a multiple of the minimum?
            if len(filter(lambda x: x % min_grid_value == 0, grid_value_list)) != len(grid_value_list):
                return

            grid_def = GridDB[min_grid_value]
            error_msg("%s setup does not contain spaces, only grids (tabulators). All grid\n" \
                      % self.name + \
                      "widths are multiples of %i. The grid setup %s\n" \
                      % (min_grid_value, repr(sorted(grid_value_list))[1:-1]) + \
                      "is equivalent to a setup with space counts %s.\n" \
                      % repr(map(lambda x: x / min_grid_value, sorted(grid_value_list)))[1:-1] + \
                      "Space counts are faster to compute.", 
                      grid_def.file_name, grid_def.line_n, DontExitF=True)

        def check_homogenous_space_counts(SpaceDB):
            # If there is one single space count depending on a variable, then no assumptions can be made
            for value in SpaceDB.keys():
                if type(value) in [str, unicode]: 
                    return

            # If all space values are the same, then they can be replaced by '1' spaces
            if len(SpaceDB) == 1 and SpaceDB.keys()[0] != 1:
                space_count, space_def = SpaceDB.items()[0]
                error_msg("%s does not contain a grid but only homogeneous space counts of %i.\n" \
                          % (self.name, space_count) + \
                          "This setup is equivalent to a setup with space counts of 1. Space counts\n" + \
                          "of 1 are the fastest to compute.", 
                          space_def.file_name, space_def.line_n, DontExitF=True)

        # Are the required elements present for indentation handling?
        assert len(self.space_db) != 0 or len(self.grid_db) != 0

        if len(self.space_db) == 0:
            check_grid_values_integer_multiples(self.grid_db)
                
        elif len(self.grid_db) == 0:
            check_homogenous_space_counts(self.space_db)

    def _error_if_intersection(self, FH, Name):
        assert False, "Must be implemented by derived class."

    def _error_if_intersection_base(self, Candidate, FH, Name):
        # 'space'
        for character_set in self.space_db.values():
            if character_set.get().has_intersection(Candidate): 
                Base._error_character_set_intersection(Name, character_set, FH)

        # 'grid'
        for character_set in self.grid_db.values():
            if character_set.get().has_intersection(Candidate):
                Base._error_character_set_intersection(Name, character_set, FH)

    @staticmethod
    def _error_character_set_intersection(Name, Before, FH):
        error_msg("Character set specification '%s' intersects" % Name, FH, 
                  DontExitF=True, WarningF=False)
        error_msg("with definition for '%s' at this place." % Before.name, 
                  Before.sr)

    @staticmethod
    def _error_state_machine_intersection(Name, Before, FH):
        error_msg("Character set specification '%s' intersects with" % Name, FH, 
                  DontExitF=True, WarningF=False)
        error_msg("the ending of the pattern for '%s' at this place." % Before.name, 
                  Before.sr, DontExitF=True, WarningF=False)
        error_msg("Note, that 'newline' and cannot end with a character which is subject\n"
                  "to indentation counting (i.e. 'space' or 'grid').", FH)

    def _error_msg_if_defined_earlier(self, Before, FH, Key=None, Name=""):
        """If Key is not None, than 'Before' is a database."""
        if Key is None:
            if Before.get().is_empty(): return
            error_msg("'" + Before.name + "' has been defined before;", FH, DontExitF=True, WarningF=False)
            error_msg("at this place.", Before.file_name, Before.line_n)
        #if Key is not None:
        #    if Before.has_key(Key) == False: return
        #    error_msg("'%s' has been defined before for %i;" % (Name, Key), FH, DontExitF=True, WarningF=False)
        #    error_msg("at this place.", Before[Key].file_name, Before[Key].line_n)

    def _error_msg_if_character_set_empty(self, CharSet, FH):
        if not CharSet.is_empty(): return
        error_msg("Empty character set found.", FH)

    @staticmethod
    def _db_to_text(title, db):
        txt = "%s:\n" % title
        for count, character_set in sorted(db.iteritems()):
            if type(count) in [str, unicode]:
                txt += "    %s by %s\n" % (count, character_set.get().get_utf8_string())
            else:
                txt += "    %3i by %s\n" % (count, character_set.get().get_utf8_string())
        return txt

    def __repr__(self):
        txt  = Base._db_to_text("Spaces", self.space_db)
        txt += Base._db_to_text("Grids", self.grid_db)
        return txt

class ParserDataLineColumn(Base):
    def __init__(self, fh=-1):
        Base.__init__(self, fh, "Line/column counter", ("space", "grid", "newline"))
        self.newline_db = {}

    def seal(self, DefaultSpaceSpec, FH):

        if DefaultSpaceSpec is not None:
            # Collect all characters mentioned in 'space_db', 'grid_db', 'newline_db'
            all_char_set = NumberSet(  _extract_interval_lists(self.space_db) 
                                     + _extract_interval_lists(self.grid_db) 
                                     + _extract_interval_lists(self.newline_db))
            remainder = all_char_set.inverse()
            before = self.space_db.get(DefaultSpaceSpec)
            if before is not None:
                remainder.unite_with(before.get())
            self.space_db[DefaultSpaceSpec] = LocalizedParameter("space", remainder, FH, "PatternStr")

    def _error_if_intersection(self, Setting, FH, Name):
        assert Setting.__class__ == NumberSet
        self._error_if_intersection_base(Setting, FH, Name)

        # 'newline'
        for character_set in self.newline_db.values():
            if character_set.get().has_intersection(Setting): 
                Base._error_character_set_intersection(Name, character_set, FH)

    def specify_newline(self, Pattern, CharSet, Count, FH=-1):
        CharSet = extract_trigger_set(FH, "newline", Pattern)

        self._check("newline", self.newline_db, CharSet, FH, Key=Count)

        # Note, a space count of '0' is theoretically possible
        entry = self.newline_db.get(Count)
        if entry is not None:
            entry.get().unite_with(CharSet)
        else:
            self.newline_db[Count] = LocalizedParameter("newline", CharSet, FH, Pattern.pattern_string())

    def __repr__(self):
        txt  = Base.__repr__(self)
        txt += Base._db_to_text("Newlines", self.newline_db)
        return txt

class ParserDataIndentation(Base):
    def __init__(self, fh=-1):
        Base.__init__(self, fh, "Indentation counter", ("space", "grid", "bad", "newline", "suppressor"))

        self.bad_character_set                = LocalizedParameter("bad",        NumberSet())
        self.newline_state_machine            = LocalizedParameter("newline",    None)
        self.newline_suppressor_state_machine = LocalizedParameter("suppressor", None)

    def seal(self):
        all_char_set = NumberSet(  _extract_interval_lists(self.space_db) 
                                 + _extract_interval_lists(self.grid_db))
        Base._seal(self, all_char_set, self.bad_character_set)

    def _error_if_intersection(self, Setting, FH, Name):
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

        self._error_if_intersection_base(candidate, FH, Name)

        # 'bad'
        if Name != "newline":
            # 'bad' indentation characters are not subject to indentation counting so they
            # very well intersect with newline or suppressor.
            if self.bad_character_set.get().has_intersection(candidate):                
                Base._error_character_set_intersection(Name, self.bad_character_set, FH)

        # 'newline'
        if Name != "bad" and self.newline_state_machine.get() is not None:
            # The 'bad' character set can very well appear as the end of newline, since it is
            # not used for indentation counting.
            ending_character_set = self.newline_state_machine.get().get_ending_character_set()
            if ending_character_set.has_intersection(candidate):            
                Base._error_state_machine_intersection(Name, self.newline_state_machine, FH)

        # 'suppressor'
        # Note, the suppressor pattern is free. No indentation is counted after it. Thus if
        # it ends with characters which are subject to indentation counting, then there is
        # no harm or confusion.

    def _error_msg_if_defined_earlier(self, Before, FH, Key=None, Name=""):
        """If Key is not None, than 'Before' is a database."""

        if Name in ["newline", "suppressor"] and Before.get() is None: 
            return
        Base._error_msg_if_defined_earlier(self, Before, FH, Key, Name)

    def specify_bad(self, PatternStr, CharSet, FH=-1):
        if not isinstance(CharSet, NumberSet):
            CharSet = extract_trigger_set(FH, "bad", Pattern=CharSet)

        self._specify(self.bad_character_set, CharSet, PatternStr, FH)

    def specify_newline(self, Pattern, FH=-1):
        self._specify(self.newline_state_machine, Pattern.sm, Pattern.pattern_string(), FH)

    def specify_suppressor(self, PatternStr, SM, FH=-1):
        self._specify(self.newline_suppressor_state_machine, Pattern.sm, Pattern.pattern_string(), FH)

    def indentation_count_character_set(self):
        """Returns the superset of all characters that are involved in
        indentation counting. That is the set of character that can appear
        between newline and the first non whitespace character.  
        """
        result = NumberSet()
        for character_set in self.space_db.values():
            result.unite_with(character_set.get())
        for character_set in self.grid_db.values():
            result.unite_with(character_set.get())
        return result

    def consistency_check(self, fh):
        Base.consistency_check(self, fh)
        assert not self.newline_state_machine.get().is_empty()

    def __repr__(self):
        txt = Base.__repr__(self)

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

def parse_line_column_counter(fh):
    result, default_column_n_per_char = __parse(fh, ParserDataLineColumn(fh))
    return CounterSetupLineColumn(result, default_column_n_per_char)

def parse_indentation(fh):
    result, default_column_n_per_char = __parse(fh, ParserDataIndentation(fh))
    return CounterSetupIndentation(result)

def __parse_definition_head(fh, result):

    if check(fh, "\\default"): pattern = None
    else:                      pattern = regular_expression.parse(fh)

    skip_whitespace(fh)
    check_or_die(fh, "=>", " after character set definition.")

    skip_whitespace(fh)
    identifier = read_identifier(fh, OnMissingStr="Missing identifier for indentation element definition.")

    verify_word_in_list(identifier, result.identifier_list, 
                        "Unrecognized indentation specifier '%s'." % identifier, fh)
    skip_whitespace(fh)

def __parse(fh, result):
    """Parses pattern definitions of the form:
   
          [ \t]                                       => grid 4;
          [:intersection([:alpha:], [\X064-\X066]):]  => space 1;

       In other words the right hand side *must* be a character set.
    """

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)

    default_column_n_per_char = 1 # Define spacing of remaining characters
    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, ">"): 
            break
        
        # A regular expression state machine
        pattern, identifier = __parse_definition_head(fh, result)
        if pattern is None:
            # The '\\default' only has meaning for 'space' in a counter setup
            if identifier != "space":
                error_msg("Keyword '\\default' can only be used for definition of 'space'.", fh)
            elif IndentationSetupF:
                error_msg("Keyword '\\default' cannot be used in indentation setup.", fh)
            default_column_n_per_char = read_value_specifier(fh, "space", 1)

        else:
            # The following treats ALL possible identifiers, including those which may be 
            # inadmissible for a setup. 'verify_word_in_list()' would abort in case that
            # an inadmissible identifier has been found--so there is no harm.
            if identifier == "space":
                value = read_value_specifier(fh, "space", 1)
                result.specify_space(pattern, value, fh)
            elif identifier == "grid":
                value = read_value_specifier(fh, "grid")
                result.specify_grid(pattern, value, fh)
            elif identifier == "bad":
                result.specify_bad(pattern, fh)
            elif identifier == "newline":
                if IndentationSetupF:
                    result.specify_newline(pattern, fh)
                else:
                    value = read_value_specifier(fh, "newline", 1)
                    result.specify_newline(pattern, value, fh)
            elif identifier == "suppressor":
                result.specify_suppressor(pattern, fh)
            else:
                assert False, "Unreachable code reached."

        if not check(fh, ";"):
            error_msg("Missing ';' after '%s' specification." % identifier, fh)

    result.consistency_check(fh)
    return result, default_column_n_per_char

def read_value_specifier(fh, Keyword, Default=None):
    skip_whitespace(fh)
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
    def check_can_be_matched_by_single_character(SM):
        bad_f      = False
        init_state = SM.get_init_state()
        if SM.get_init_state().is_acceptance(): 
            bad_f = True
        elif len(SM.states) != 2:
            bad_f = True
        # Init state MUST transit to second state. Second state MUST not have any transitions
        elif len(init_state.target_map.get_target_state_index_list()) != 1:
            bad_f = True
        else:
            tmp = set(SM.states.keys())
            tmp.remove(SM.init_state_index)
            other_state_index = tmp.__iter__().next()
            if len(SM.states[other_state_index].target_map.get_target_state_index_list()) != 0:
                bad_f = True

        if bad_f:
            error_msg("For '%s' only patterns are addmissible which\n" % Keyword + \
                      "can be matched by a single character, e.g. \" \" or [a-z].", fh)

    check_can_be_matched_by_single_character(Pattern.sm)

    transition_map = Pattern.sm.get_init_state().target_map.get_map()
    assert len(transition_map) == 1
    return transition_map.values()[0]

_ParserDataLineColumn_Default = None
def ParserDataLineColumn_Default():
    global _ParserDataLineColumn_Default

    if _ParserDataLineColumn_Default is None:
        _ParserDataLineColumn_Default = ParserDataLineColumn()
        _ParserDataLineColumn_Default.seal(DefaultSpaceSpec=1, FH=-1)
    return _ParserDataLineColumn_Default

def _extract_interval_lists(db):
    """Extract interval lists of all involved number sets."""
    result = []
    for x in db.itervalues():
        result.extend(x.get().get_intervals(PromiseToTreatWellF=True))
    return result

