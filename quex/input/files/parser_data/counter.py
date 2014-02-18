from quex.engine.generator.code.base import SourceRef, SourceRef_VOID
from quex.engine.interval_handling   import NumberSet
from quex.engine.tools               import typed
from quex.blackboard                 import E_CharacterCountType

from collections import namedtuple

CountCmdDef = namedtuple("CountCmdInfo", ("identifier", "cc_type", "value", "sr"))

class CountCmdMap:
    """Maintain a list of occupied characters in the range of all characters.

                   list: (character set, parameter)

       where the 'character set' specifies a subset of characters for which there
       is a definition by the given 'parameter'.
    """
    def __init__(self):
        self.__map  = []
        self.__else = None

    def get_map(self):
        return self.__map

    def add(self, CharSet, Identifier, Value, sr):
        cc_type = {
            "space":   E_CharacterCountType.COLUMN,
            "grid":    E_CharacterCountType.GRID,
            "newline": E_CharacterCountType.LINE,
            "bad":     E_CharacterCountType.BAD,
        }[Identifier]

        if CharSet is None:
            if self.__else is not None:
                error_msg("'\\else has been defined more than once.", sr, DontExitF=True, WarningF=False)
                error_msg("Previously, defined here.", self.__else.sr)
            self.__else = CountCmdDef(Identifier, cc_type, Value, sr)
        else:
            if CharSet.is_empty(): 
                error_msg("Empty character set found.", sr)
            self.check_intersection(Identifier, "character set", CharSet, sr)
            self.__map.append((CharSet, CountCmdDef(Identifier, cc_type, Value, sr)))

    def get_count_commands(self, CharacterSet):
        """Finds the count command for column, grid, and newline.
        
        RETURNS: [0] column increment (None, if none, -1 if undetermined)
                 [1] grid step size   (None, if none, -1 if undetermined)
                 [2] line increment   (None, if none, -1 if undetermined)

            None --> no influence from CharacterSet on setting.
            '-1' --> no distinct influence from CharacterSet on setting.
                     (more than one possible).

        NOTE: If one value not in (None, -1), then all others must be None.
        """

        db = {
            E_CharacterCountType.COLUMN: None,
            E_CharacterCountType.GRID:   None,
            E_CharacterCountType.LINE:   None,
        }

        for character_set, entry in self.__map:
            if entry.cc_type not in db: 
                continue
            elif character_set.is_superset(CharacterSet):
                db[entry.cc_type] = entry.value
                break
            elif character_set.has_intersection(CharacterSet): 
                db[entry.cc_type] = -1     

        return db[E_CharacterCountType.COLUMN], \
               db[E_CharacterCountType.GRID], \
               db[E_CharacterCountType.LINE]


    def check_intersection(self, Name, TypeName, CharSet, sr, ConsiderBadF=True):
        for character_set, before in self.__map:
            if not character_set.has_intersection(CharSet):                         continue
            elif (not ConsiderBadF) and before.cc_type == E_CharacterCountType.BAD: continue
            _error_set_intersection(Name, TypeName, Before, sr)

    def assign_else_count_command(self, GlobalMin, GlobalMax):
        remaining_set = self.__get_remaining_set()
        remaining_set.cut_lesser(GlobalMin)
        remaining_set.cut_greater_or_equal(GlobalMax)

        if self.__else is None: else_cmd = ("space", 1, SourceRef_VOID)
        else:                   else_cmd = self.__else
        
        if not remaining_set.is_empty():
            self.__map.append((remaining_set, else_cmd))

    def remove_bad(self):
        i = len(self.__map)
        while i >= 0:
            entry = self.__map[i]
            if entry.cc_type == E_CharacterCountType.BAD:
                del self.__map[i]
            i -= 1

    def __get_remaining_set(self):
        result = NumberSet()
        for character_set, dummy in self.__map:
            result.unite_with(character_set)
        return result.inverse()

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

class Base:
    def __init__(self, sr, Name, IdentifierList):
        self.sr   = sr
        self.name = Name
        self.count_command_map      = CountCmdMap()
        self.identifier_list        = IdentifierList
        self.__containing_mode_name = ""

    @typed(sr=SourceRef, Identifier=(str,unicode))
    def specify(self, Identifier, Pattern, Count, sr):
        self.count_command_map.add(extract_trigger_set(sr, Identifier, Pattern), 
                                   Identifier, Count, sr)

    def check_grid_specification(self, Value, sr):
        if   Value == 0: 
            error_msg("A grid count of 0 is nonsense. May be define a space count of 0.", sr)
        elif Value == 1:
            error_msg("Indentation grid counts of '1' are equivalent of to a space\n" + \
                      "count of '1'. The latter is faster to compute.",
                          sr, DontExitF=True)
    def set_containing_mode_name(self, ModeName):
        assert isinstance(ModeName, (str, unicode))
        self.__containing_mode_name = ModeName

    def containing_mode_name(self):
        return self.__containing_mode_name

    def consistency_check(self, fh):
        # Are the required elements present for indentation handling?
        assert len(self.space_db) != 0 or len(self.grid_db) != 0

        if len(self.space_db) == 0:
            self.count_command_map.check_grid_values_integer_multiples(self.grid_db)
                
        elif len(self.grid_db) == 0:
            self.count_command_map.check_homogenous_space_counts(self.space_db)

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

    def __repr__(self):
        txt  = Base.__repr__(self)
        txt += Base._db_to_text("Newlines", self.newline_db)
        return txt

class ParserDataIndentation(Base):
    def __init__(self, fh=-1):
        self.bad_character_set     = LocalizedParameter("bad",        NumberSet())
        self.sm_newline            = LocalizedParameter("newline",    None)
        self.sm_newline_suppressor = LocalizedParameter("suppressor", None)

        Base.__init__(self, fh, "Indentation counter", ("space", "grid", "newline", "suppressor", "bad"))

    @typed(sr=SourceRef)
    def specify_newline(self, Pattern, sr):
        if self.newline.get() is None: 
            _error_defined_before(self.newline)
        ending_char_set = Setting.get_ending_character_set()
        self.count_command_map.check_intersection("newline", "ending characters", ending_char_set, sr, 
                                                  ConsiderBadF=False)
        self.sm_newline.set(Pattern.sm, sr, Pattern.pattern_string())
        self.count_command_map.add(ending_char_set, self.bad_character_set)

    def specify_suppressor(self, Pattern, SM, sr):
        if self.sm_newline_suppressor.get() is None: 
            _error_defined_before(self.sm_newline_suppressor)

        # Newline suppressors are totally free. 
        # -- They can contain newlines indentation count characters etc.
        # -- They are not subject to intersection check.
        #
        # NOT: "occupied_map.check("bad", CharSet, sr)"                      !!
        self.sm_newline_suppressor.set(Pattern.sm, sr, Pattern.pattern_string())
        # NOT: "occupied_map.add(CharSet, self.bad_character_set)"           !!

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

def _error_set_intersection(Name, TypeName, Before, sr):
    def type_name(Parameter):
        if Parameter.get().__class__ == NumberSet: return "character set"
        else:                                      return "ending characters"

    note_f = False
    if TypeName != "character set" or type_name(Before) != "character set":
        note_f = True

    error_msg("The %s defined in '%s' intersects" % (TypeName, Name),
              sr, DontExitF=True, WarningF=False)
    error_msg("with %s defined '%s' at this place." % (type_name(Before), Before.name), 
              Before.sr, DontExitF=note_f, WarningF=False)

    if note_f:
        error_msg("Note, for example, 'newline' cannot end with a character which is subject\n"
                  "to indentation counting (i.e. 'space' or 'grid').", sr)

def _error_defined_before(Before, sr):
    error_msg("'%s' has been defined before;" % Before.name, sr, 
              DontExitF=True, WarningF=False)
    error_msg("at this place.", Before.file_name, Before.line_n)

def extract_trigger_set(sr, Keyword, Pattern):
    if Pattern is None:
        return None
    elif isinstance(Pattern, NumberSet):
        return Pattern

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
                      "can be matched by a single character, e.g. \" \" or [a-z].", sr)

    check_can_be_matched_by_single_character(Pattern.sm)

    transition_map = Pattern.sm.get_init_state().target_map.get_map()
    assert len(transition_map) == 1
    return transition_map.values()[0]

