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

class OccupiedMap:
    def __init__(self):
        self.__map = []

    def add(self, CharSet, Parameter):
        self.__map.append((CharSet, Parameter))

    def check(self, Name, TypeName, CharSet, fh):
        for character_set, before in occupied_map:
            if not character_set.has_intersection(CharSet): continue
            _error_set_intersection(Name, TypeName, Before, fh)

class CountInfoDb(dict):
    """A database that maintains information about a 'count' dependent on
    a character set. For example, a 'count' may be the number of columns
    which are increment when a character from a chracter set appears.
    """
    def __init__(self, Name):
        self.name

    def enter(self, CharSet, Count, occupied_map, fh):
        if CharSet.is_empty(): error_msg("Empty character set found.", fh)
        occupied_map.check(self.name, "characterSet", CharSet, fh)

        self._check(CharSet, DbList)

        parameter = self.get(Count)
        if parameter is not None:
            parameter.get().unite_with(CharSet)
        else:
            parameter = LocalizedParameter(self.name, CharSet, fh, Pattern.pattern_string()) 
            self[Count] = parameter

        occupied_map.add(CharSet, parameter)
        return entry

class Base:
    def __init__(self, fh, Name, IdentifierList):
        self.fh = fh
        if fh != -1:
            self.file_name = fh.name
            self.line_n    = get_current_line_info_number(fh)
        else:
            self.file_name = "no file handle"
            self.line_n    = -1

        self.space_db = CountInfoDb("space") # Maps: space width --> character_set
        self.grid_db  = CountInfoDb("grid")  # Maps: grid width  --> character_set
        self._db_list = [ self.space_db, self.grid_db ]

        self.identifier_list        = IdentifierList
        self.name                   = Name
        self.__containing_mode_name = ""
        self.__occupied_map         = OccupiedMap()

    def specify_space(self, Pattern, Count, fh=-1):
        self.space_db.enter(Pattern, Count, self.__occupied_map, fh)

    def specify_grid(self, Pattern, Count, fh=-1):
        if Count == 0: 
            error_msg("A grid count of 0 is nonsense. May be define a space count of 0.", fh)
        if Count == 1:
            error_msg("Indentation grid counts of '1' are equivalent of to a space\n" + \
                      "count of '1'. The latter is faster to compute.",
                      fh, DontExitF=True)
        self.grid_db.enter(Pattern, Count, self.__occupied_map, fh)

    def set_containing_mode_name(self, ModeName):
        assert isinstance(ModeName, (str, unicode))
        self.__containing_mode_name = ModeName

    def containing_mode_name(self):
        return self.__containing_mode_name

    def _check(self, Name, Before, Setting, fh, Key=None):
        self._error_msg_if_defined_earlier(Before, fh, Key=Key, Name=Name)
        if Setting.__class__ == NumberSet: 
            self._error_msg_if_character_set_empty(Setting, fh)
        self._error_if_intersection(Setting, fh, Name)


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

    def _error_if_intersection(self, fh, Name):
        assert False, "Must be implemented by derived class."

    def _error_if_intersection_base(self, Candidate, fh, Name):
        # 'space'
        for character_set in self.space_db.values():
            if character_set.get().has_intersection(Candidate): 
                Base._error_character_set_intersection(Name, character_set, fh)

        # 'grid'
        for character_set in self.grid_db.values():
            if character_set.get().has_intersection(Candidate):
                Base._error_character_set_intersection(Name, character_set, fh)

    def _error_msg_if_character_set_empty(self, CharSet, fh):
        if not CharSet.is_empty(): return
        error_msg("Empty character set found.", fh)

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
        self._db_list.append(self.newline_db)

    def seal(self, DefaultSpaceSpec, fh):

        if DefaultSpaceSpec is not None:
            # Collect all characters mentioned in 'space_db', 'grid_db', 'newline_db'
            all_char_set = NumberSet(  _extract_interval_lists(self.space_db) 
                                     + _extract_interval_lists(self.grid_db) 
                                     + _extract_interval_lists(self.newline_db))
            remainder = all_char_set.inverse()
            before = self.space_db.get(DefaultSpaceSpec)
            if before is not None:
                remainder.unite_with(before.get())
            self.space_db[DefaultSpaceSpec] = LocalizedParameter("space", remainder, fh, "PatternStr")

    def specify_newline(self, CharSet, Count, fh=-1):
        self.newline_db.enter(CharSet, Count, self.__occupied_map, fh)

    def __repr__(self):
        txt  = Base.__repr__(self)
        txt += Base._db_to_text("Newlines", self.newline_db)
        return txt

class ParserDataIndentation(Base):
    def __init__(self, fh=-1):
        Base.__init__(self, fh, "Indentation counter", ("space", "grid", "bad", "newline", "suppressor"))

        self.bad_character_set     = LocalizedParameter("bad",        NumberSet())
        self.sm_newline            = LocalizedParameter("newline",    None)
        self.sm_newline_suppressor = LocalizedParameter("suppressor", None)

    def specify_bad(self, CharSet, PatternStr, fh=-1):
        if self.bad_character_set.get().is_empty(): 
            _error_defined_before(self.bad_character_set)

        occupied_map.check("bad", "character set", CharSet, fh):
        self.bad_character_set.set(CharSet, fh, PatternStr)
        # 'bad' indentation characters are not subject to indentation counting so they
        # very well intersect with newline or suppressor.
        # NOT: "occupied_map.add(CharSet, self.bad_character_set)"           !!

    def specify_newline(self, Pattern, fh=-1):
        if self.newline.get() is None: 
            _error_defined_before(self.newline)
        ending_char_set = Setting.get_ending_character_set()
        self.__occupied_map.check("newline", "ending characters", ending_char_set, fh)
        self.sm_newline.set(Pattern.sm, fh, Pattern.pattern_string())
        self.__occupied_map.add(ending_char_set, self.bad_character_set)

    def specify_suppressor(self, Pattern, SM, fh=-1):
        if self.sm_newline_suppressor.get() is None: 
            _error_defined_before(self.sm_newline_suppressor)

        # Newline suppressors are totally free. 
        # -- They can contain newlines indentation count characters etc.
        # -- They are not subject to intersection check.
        #
        # NOT: "occupied_map.check("bad", CharSet, fh)"                      !!
        self.sm_newline_suppressor.set(Pattern.sm, fh, Pattern.pattern_string())
        # NOT: "occupied_map.add(CharSet, self.bad_character_set)"           !!

    def seal(self):
        all_char_set = NumberSet(  _extract_interval_lists(self.space_db) 
                                 + _extract_interval_lists(self.grid_db))
        Base._seal(self, all_char_set, self.bad_character_set)

    def __repr__(self):
        txt = Base.__repr__(self)

        txt += "Bad:\n"
        txt += "    %s\n" % self.bad_character_set.get().get_utf8_string()

        txt += "Newline:\n"
        sm = self.sm_newline.get()
        if sm is None: txt += "    <none>\n"
        else:          txt += "    %s\n" % sm.get_string(NormalizeF=True, Option="utf8").replace("\n", "\n    ")

        txt += "Suppressor:\n"
        sm = self.sm_newline_suppressor.get()
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
                        "Unrecognized specifier '%s'." % identifier, fh)
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
                char_set = extract_trigger_set(fh, pattern, "space")
                result.specify_space(char_set, value, fh)

            elif identifier == "grid":
                value = read_value_specifier(fh, "grid")
                char_set = extract_trigger_set(fh, pattern, "grid")
                result.specify_grid(char_set, value, fh)

            elif identifier == "bad":
                char_set = extract_trigger_set(fh, pattern, "bad")
                result.specify_bad(char_set, fh)

            elif identifier == "newline":
                if IndentationSetupF:
                    result.specify_newline(pattern, fh)
                else:
                    value    = read_value_specifier(fh, "newline", 1)
                    char_set = extract_trigger_set(fh, pattern, "newline")
                    result.specify_newline(char_set, value, fh)

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
    if value is not None:     return value

    # not a number received, is it an identifier?
    variable = read_identifier(fh)
    if   variable != "":      return variable
    elif Default is not None: return Default

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

def _extract_interval_lists(db):
    """Extract interval lists of all involved number sets."""
    result = []
    for x in db.itervalues():
        result.extend(x.get().get_intervals(PromiseToTreatWellF=True))
    return result

def _error_set_intersection(Name, TypeName, Before, fh):
    def type_name(Parameter):
        if Parameter.get().__class__ == NumberSet: return "character set"
        else:                                      return "ending characters"

    note_f = False
    if TypeName != "character set" or type_name(Before) != "character set":
        note_f = True

    error_msg("The %s defined in '%s' intersects" % (TypeName, Name),
              fh, DontExitF=True, WarningF=False)
    error_msg("with %s defined '%s' at this place." % (type_name(Before), Before.name), 
              Before.sr, DontExitF=note_f, WarningF=False)

    if note_f:
        error_msg("Note, for example, 'newline' cannot end with a character which is subject\n"
                  "to indentation counting (i.e. 'space' or 'grid').", fh)

def _error_defined_before(Before, fh):
    error_msg("'%s' has been defined before;" % Before.name, fh, 
              DontExitF=True, WarningF=False)
    error_msg("at this place.", Before.file_name, Before.line_n)
