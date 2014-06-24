# (C) Frank-Rene Schaefer
from   quex.input.setup                           import NotificationDB
from   quex.input.regular_expression.construct    import Pattern
from   quex.engine.tools                          import typed
from   quex.engine.misc.file_in                   import error_msg
import quex.engine.state_machine.transformation   as     transformation
from   quex.engine.state_machine.core             import StateMachine  
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.generator.code.base            import SourceRefObject, \
                                                         SourceRef, \
                                                         SourceRef_VOID
from   quex.engine.interval_handling              import NumberSet, \
                                                         NumberSet_All
from   quex.blackboard                            import E_CharacterCountType

from   quex.blackboard import setup as Setup
from   collections     import namedtuple, defaultdict
from   operator        import itemgetter

cc_type_db = {
    "space":                     E_CharacterCountType.COLUMN,
    "grid":                      E_CharacterCountType.GRID,
    "newline":                   E_CharacterCountType.LINE,
    "begin(newline_suppressor)": E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR,
    "begin(newline)":            E_CharacterCountType.BEGIN_NEWLINE,
    "begin(comment to newline)": E_CharacterCountType.BEGIN_COMMENT_TO_NEWLINE,
    "end(newline)":              E_CharacterCountType.END_NEWLINE,
    "bad":                       E_CharacterCountType.BAD,
    "whitespace":                E_CharacterCountType.WHITESPACE,
}

cc_type_name_db = dict((value, key) for key, value in cc_type_db.iteritems())


class CountCmdMapEntry(namedtuple("CountCmdMapEntry", ("cc_type", "value", "sr"))):
    def __new__(self, CCType, Value, sr):
        return super(CountCmdMapEntry, self).__new__(self, CCType, Value, sr)

    def get_command_list(self, ColumnCountPerChunk=None):
        if self.column_count_per_chunk is None:
            cmd = {
                E_CharacterCountType.COLUMN: ColumnCountAdd,
                E_CharacterCountType.GRID:   ColumnCountGridAdd,
                E_CharacterCountType.LINE:   LineCountAdd,
            }[self.cc_type](self.value)
        else:
            cmd = {
                E_CharacterCountType.COLUMN: return_None,
                E_CharacterCountType.GRID:   ColumnCountGridAddWithReferenceP,
                E_CharacterCountType.LINE:   LineCountAddWithReferenceP,
            }[self.cc_type](self.value, E_R.InputP, ColumnCountPerChunk)

        if cmd is None: return []
        else:           return [ cmd ]

    def get_command_list_with_lexeme_end_check(self, ColumnCountPerChunk, DoorIdOk, DoorIdOnLexemeEnd):
        """     .---------------.    ,----------.   no
           ---->| Count Command |---< LexemeEnd? >------> DoorIdOk
                '---------------'    '----+-----'
                                          | yes
                                   .---------------.
                                   |  Lexeme End   |
                                   | Count Command |----> DoorIdOnLexemeEnd
                                   '---------------'
        """
        assert DoorIdOk is not None
        assert DoorIdOnLexemeEnd is not None

        cl = self._command(self.cc_type, self.value)
        cl.append(
            GotoDoorIdIfInputPNotEqualPointer(DoorIdOk, E_R.LexemeEnd),
        )

        if ColumnCountPerChunk is not None and self.cc_type == E_CharacterCountType.COLUMN:
            cl.append(
                ColumnCountReferencePDeltaAdd(E_R.InputP, self.column_count_per_chunk, False)
            )

        cl.append(
            GotoDoorId(DoorIdOnLexemeEnd)
        )
        return cl

CountInfo = namedtuple("CountInfo",        ("incidence_id", "cc_type", "parameter", "character_set"))

class CountCmdMap(object):
    """Association of character sets with triggered count commands.
    ___________________________________________________________________________

                   list: (character set, CountCmdMapEntry)

    where the 'character set' specifies a subset of characters for which there
    is a definition by the given 'parameter'. The character sets are disjoint.

    This map is used to determine whether actions on character sets are defined 
    more than once. The CountCmdMapEntry contains source references. This allows
    for detailed error messages.
    ___________________________________________________________________________
    """
    __slots__ = ("__map", "__else")
    def __init__(self):
        """Primarily, the '__map' member stores the list of associations between
        character sets and the count command entry. The '__else' contains the 
        count command which waits to be applied to the remaining set of characters.
        """
        self.__map  = []
        self.__else = None

    def get_map(self):
        return self.__map

    def define_else(self, Identifier, Value, sr):
        """Define the '\else' character set which is resolved AFTER everything has been 
        defined.
        """
        global cc_type_db

        if self.__else is not None:
            error_msg("'\\else has been defined more than once.", sr, 
                      DontExitF=True, WarningF=False)
            error_msg("Previously, defined here.", self.__else.sr)
        self.__else = CountCmdMapEntry(cc_type_db[Identifier], Value, sr)

    def add(self, CharSet, Identifier, Value, sr):
        global cc_type_db
        if CharSet.is_empty(): 
            error_msg("Empty character set found for '%s'." % Identifier, sr)
        elif Identifier == "grid":
            self.check_grid_specification(Value, sr)
        cc_type = cc_type_db[Identifier]
        self.check_intersection(cc_type, CharSet, sr)
        self.__map.append((CharSet, CountCmdMapEntry(cc_type, Value, sr)))

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

    def check_intersection(self, CcType, CharSet, sr):
        """Check whether the given character set 'CharSet' intersects with 
        a character set already mentioned in the map. Depending on the CcType
        of the new candidate certain count commands may be tolerated, i.e. 
        their intersection is not considered.
        """
        intersection_tolerated = {
            E_CharacterCountType.COLUMN:                   (),
            E_CharacterCountType.GRID:                     (),
            E_CharacterCountType.LINE:                     (),
            E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR: (E_CharacterCountType.BAD,),
            E_CharacterCountType.BEGIN_NEWLINE:            (E_CharacterCountType.BAD,
                                                            E_CharacterCountType.END_NEWLINE),
            E_CharacterCountType.END_NEWLINE:              (E_CharacterCountType.BAD,
                                                            E_CharacterCountType.BEGIN_NEWLINE),
            E_CharacterCountType.BEGIN_COMMENT_TO_NEWLINE: (), 
            E_CharacterCountType.WHITESPACE:               (),
            E_CharacterCountType.BAD:                      (E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR, 
                                                            E_CharacterCountType.BEGIN_NEWLINE, 
                                                            E_CharacterCountType.END_NEWLINE)
        }[CcType]

        interferer = self.find_occupier(CharSet, Tolerated=intersection_tolerated)
        if interferer is None:
            return
        _error_set_intersection(CcType, interferer, sr)

    def get_remaining_set(self, GlobalMin, GlobalMax):
        """Return the set of characters which are not associated with count commands.
        Restrict the operation to characters from GlobalMin to GlobalMax (inclusively).
        """
        result = self.__get_remaining_set()
        result.cut_lesser(GlobalMin)
        result.cut_greater_or_equal(GlobalMax)
        return result

    def assign_else_count_command(self, GlobalMin, GlobalMax, SourceReference):
        """After all count commands have been assigned to characters, the 
        remaining character set can be associated with the 'else-CountCmdMapEntry'.
        """
        if self.__else is None: 
            else_cmd = CountCmdMapEntry(E_CharacterCountType.COLUMN, 1, SourceRef_VOID)
            error_msg("No '\else' defined in counter setup. Assume '\else => space 1;'", SourceReference, 
                      DontExitF=True, WarningF=True, 
                      SuppressCode=NotificationDB.warning_counter_setup_without_else)
        else:                   
            else_cmd = self.__else
        
        remaining_set = self.get_remaining_set(GlobalMin, GlobalMax)
        if not remaining_set.is_empty():
            self.__map.append((remaining_set, else_cmd))

    def column_grid_line_iterable_pruned(self, CharacterSet):
        """Iterate over count command map. It is assumed that anything in the map
        is 'valid'. 
        """
        considered_set = (E_CharacterCountType.COLUMN, 
                          E_CharacterCountType.GRID, 
                          E_CharacterCountType.LINE)
        for character_set, info in self.__map:
            if character_set.has_intersection(CharacterSet):
                if info.cc_type not in considered_set: continue
                yield character_set.intersection(CharacterSet), info

    def column_grid_bad_iterable(self):
        """Iterate over count command map. Only 'COLUMN' and 'GRID' are reported. 
        This is for indentation counting.
        """
        considered_set = (E_CharacterCountType.COLUMN, 
                          E_CharacterCountType.GRID, 
                          E_CharacterCountType.BAD)
        for character_set, info in self.__map:
            if info.cc_type in considered_set:
                yield character_set, info

    @typed(CharacterSet=NumberSet)
    def get_column_number_per_chunk(self, CharacterSet):
        """Considers the counter database which tells what character causes
        what increment in line and column numbers. However, only those characters
        are considered which appear in the CharacterSet. 

        RETURNS: None -- If there is NO distinct column increment.
                 >= 0 -- The increment of column number for every character
                         from CharacterSet.
        """
        column_incr_per_character = None
        number_set                = None
        for character_set, info in self.column_grid_line_iterable_pruned(CharacterSet):
            if info.cc_type != E_CharacterCountType.COLUMN: 
                continue
            elif column_incr_per_character is None:       
                column_incr_per_character = info.value
                number_set                = character_set
            elif column_incr_per_character == info.value: 
                number_set.unite_with(character_set)
            else:
                return None

        if column_incr_per_character is None:
            return None                       # TODO: return 0

        # HERE: There is only ONE 'column_n_increment' command. It appears on
        # the character set 'number_set'. If the character set is represented
        # by the same number of chunks, than the column number per chunk is
        # found.
        if not Setup.variable_character_sizes_f():
            return column_incr_per_character

        chunk_n_per_character = \
            transformation.homogeneous_chunk_n_per_character(number_set, 
                                              Setup.buffer_codec_transformation_info)
        if chunk_n_per_character  is None:
            return None
        else:
            return float(column_incr_per_character) / chunk_n_per_character

    def find_occupier(self, CharSet, Tolerated):
        """Find a command that occupies the given CharSet, at least partly.
           RETURN: None, if no such occupier exists.
        """
        for character_set, before in self.__map:
            if   before.cc_type in Tolerated:                 continue
            elif not character_set.has_intersection(CharSet): continue
            return before
        return None

    def __get_remaining_set(self):
        ignored = (E_CharacterCountType.BAD, 
                   E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR, 
                   E_CharacterCountType.BEGIN_NEWLINE, 
                   E_CharacterCountType.END_NEWLINE) 
        result  = NumberSet()
        for character_set, info in self.__map:
            if info.cc_type in ignored: continue
            result.unite_with(character_set)
        return result.inverse()

    def check_grid_values_integer_multiples(self):
        """If there are no spaces and the grid is on a homogeneous scale,
           => then the grid can be transformed into 'easy-to-compute' spaces.
        """
        grid_value_list = []
        min_info        = None
        column_n_f      = False
        for character_set, info in self.__map:
            if info.cc_type != E_CharacterCountType.GRID: 
                if info.cc_type == E_CharacterCountType.COLUMN: 
                    return
                continue
            elif type(info.value) in (str, unicode): 
                # If there is one single 'variable' grid value, 
                # then no assumptions can be made.
                return
            grid_value_list.append(info.value)
            if min_info is None or info.value < min_info.value:
                min_info = info

        if min_info is None:
            return

        # Are all grid values a multiple of the minimum?
        if len(filter(lambda x: x % min_info.value == 0, grid_value_list)) != len(grid_value_list):
            return

        error_msg("Setup does not contain spaces, only grids (tabulators). All grid\n" \
                  "widths are multiples of %i. The grid setup %s\n" \
                  % (min_info.value, repr(sorted(grid_value_list))[1:-1]) + \
                  "is equivalent to a setup with space counts %s.\n" \
                  % repr(map(lambda x: x / min_info.value, sorted(grid_value_list)))[1:-1] + \
                  "Space counts are faster to compute.", 
                  min_info.sr, DontExitF=True)

    def check_homogenous_space_counts(self):
        common = None
        grid_f = False
        for character_set, info in self.__map:
            if info.cc_type != E_CharacterCountType.COLUMN: 
                if info.cc_type == E_CharacterCountType.GRID: 
                    return
                continue
            elif type(info.value) in (str, unicode): 
                # If there is one single 'variable' grid value, 
                # then no assumptions can be made.
                return
            elif common is None:
                common = info
            elif common.value != info.value:
                # space counts are not homogeneous
                return

        if common is None:
            return
            
        error_msg("Setup does not contain a grid but only homogeneous space counts of %i.\n" \
                  % common.value + \
                  "This setup is equivalent to a setup with space counts of 1. Space counts\n" + \
                  "of 1 are the fastest to compute.", 
                  common.sr, DontExitF=True)

    def check_defined(self, SourceReference, CCT):
        """Checks whether the character counter type has been defined in the 
        map.
        
        THROWS: Error in case that is has not been defined.
        """
        for character_set, info in self.__map:
            if info.cc_type == CCT: 
                return

        error_msg("Setup does not define '%s'." % cc_type_name_db[CCT], SourceReference, 
                  DontExitF=True, WarningF=True, 
                  SuppressCode=NotificationDB.warning_counter_setup_without_newline)

    def check_grid_specification(self, Value, sr):
        if   Value == 0: 
            error_msg("A grid count of 0 is nonsense. May be define a space count of 0.", sr)
        elif Value == 1:
            error_msg("Indentation grid counts of '1' are equivalent of to a space\n" + \
                      "count of '1'. The latter is faster to compute.",
                          sr, DontExitF=True)

    def __str__(self):
        def _db_to_text(title, CountCmdInfoList):
            txt = "%s:\n" % title
            for character_set, info in sorted(CountCmdInfoList, key=lambda x: x[0].minimum()):
                if type(info.value) in [str, unicode]:
                    txt += "    %s by %s\n" % (info.value, character_set.get_utf8_string())
                else:
                    txt += "    %3i by %s\n" % (info.value, character_set.get_utf8_string())
            return txt

        db_by_name = defaultdict(list)
        for character_set, info in self.__map:
            name = cc_type_name_db[info.cc_type]
            db_by_name[name].append((character_set, info))

        txt = [
            _db_to_text(name, count_command_info_list)
            for name, count_command_info_list in sorted(db_by_name.iteritems(), key=itemgetter(0))
        ]
        return "".join(txt)

class Base:
    @typed(sr=SourceRef)
    def __init__(self, sr, Name, IdentifierList, TheCountCmdMap=None):
        self.sr   = sr
        self.name = Name
        if TheCountCmdMap is None: self.count_command_map = CountCmdMap()
        else:                      self.count_command_map = TheCountCmdMap
        self.identifier_list        = IdentifierList
        self.__containing_mode_name = ""

    @typed(sr=SourceRef, Identifier=(str,unicode))
    def specify(self, Identifier, Pattern, Count, sr):
        if Pattern is None:
            self.count_command_map.define_else(Identifier, Count, sr)
        else:
            self.count_command_map.add(extract_trigger_set(sr, Identifier, Pattern), 
                                       Identifier, Count, sr)

    def consistency_check(self):
        assert False, "Derived class must implement this."

    def set_containing_mode_name(self, ModeName):
        assert isinstance(ModeName, (str, unicode))
        self.__containing_mode_name = ModeName

    def containing_mode_name(self):
        return self.__containing_mode_name

class ParserDataLineColumn(Base):
    """Line/column number count specification.
    ___________________________________________________________________________
    The main result of the parsing the the Base's .count_command_map which is 
    an instance of CountCmdMap.
    ____________________________________________________________________________
    """
    @typed(sr=SourceRef)
    def __init__(self, sr, TheCountCmdMap=None):
        Base.__init__(self, sr, "Line/column counter", ("space", "grid", "newline"), TheCountCmdMap)

    def finalize(self):
        # Assign the 'else' command to all the remaining places in the character map.
        self.count_command_map.assign_else_count_command(0, Setup.get_character_value_limit(), 
                                                         self.sr)
        self.consistency_check()

    def consistency_check(self):
        self.count_command_map.check_grid_values_integer_multiples()
        self.count_command_map.check_homogenous_space_counts()
        self.count_command_map.check_defined(self.sr, E_CharacterCountType.LINE)

class ParserDataIndentation(Base):
    """Indentation counter specification.
    ____________________________________________________________________________
    The base's .count_command_map contains information about how to count the 
    space at the beginning of the line. The count until the first non-whitespace
    is the 'indentation'. 
    
    +bad:

    The spec contains information about what characters are not supposed to
    appear in indentation (bad characters). Depending on the philosophical
    basis, some might consider 'space' as evil, others consider 'tab' as evil.

    +newline:

    A detailed state machine can be defined for 'newline'. This might be 
    '\n|(\r\n)' or more complex things.

    +suppressor:

    A newline might be suppressed by '\' for example. For that, it might be
    specified as 'newline suppressor'.
    ____________________________________________________________________________
    """
    @typed(sr=SourceRef)
    def __init__(self, sr):
        self.whitespace_character_set = SourceRefObject("whitespace", None)
        self.bad_character_set        = SourceRefObject("bad", None)
        self.sm_newline               = SourceRefObject("newline", None)
        self.sm_newline_suppressor    = SourceRefObject("suppressor", None)
        self.sm_comment               = SourceRefObject("comment", None)

        Base.__init__(self, sr, "Indentation counter", ("whitespace", "comment", "newline", "suppressor", "bad"))

    def specify(self, identifier, pattern, sr):
        if   identifier == "whitespace": 
            self.__specify_character_set(self.whitespace_character_set, 
                                         "whitespace", pattern, sr)
        elif identifier == "bad":        
            self.__specify_character_set(self.bad_character_set, 
                                         "bad", pattern, sr)
        elif identifier == "newline":    
            self.specify_newline(pattern.sm, sr)
        elif identifier == "suppressor": 
            self.specify_suppressor(pattern.sm, sr)
        elif identifier == "comment":    
            self.specify_comment(pattern.sm, sr)
        else:                            
            return False
        return True

    @typed(sr=SourceRef)
    def __specify_character_set(self, ref, Name, Pattern, sr):
        cset = extract_trigger_set(sr, Name, Pattern)
        self.count_command_map.add(cset, Name, None, sr)
        ref.set(cset, sr)

    @typed(sr=SourceRef)
    def specify_newline(self, SmNewline, sr):
        _error_if_defined_before(self.sm_newline, sr)

        beginning_char_set = SmNewline.get_beginning_character_set()
        ending_char_set    = SmNewline.get_ending_character_set()

        self.count_command_map.add(beginning_char_set, "begin(newline)", None, sr)

        # Do not consider a character from newline twice
        ending_char_set.subtract(beginning_char_set)
        if not ending_char_set.is_empty():
            self.count_command_map.add(ending_char_set, "end(newline)", None, sr)

        self.sm_newline.set(SmNewline, sr)

    @typed(sr=SourceRef)
    def specify_suppressor(self, Sm, sr):
        _error_if_defined_before(self.sm_newline_suppressor, sr)

        self.count_command_map.add(Sm.get_beginning_character_set(), 
                                   "begin(newline supressor)", None, sr)
        self.sm_newline_suppressor.set(Sm, sr)

    @typed(sr=SourceRef)
    def specify_comment(self, Sm, sr):
        _error_if_defined_before(self.sm_comment, sr)

        self.count_command_map.add(Sm.get_beginning_character_set(), 
                                   "begin(comment to newline)", None, sr)
        self.sm_newline_suppressor.set(Sm, sr)

    def sm_newline_defaultize(self):
        """Default newline: '(\n)|(\r\n)'
        """
        global cc_type_name_db

        newline_set = NumberSet(ord('\n'))
        retour_set  = NumberSet(ord('\r'))

        before = self.count_command_map.find_occupier(newline_set, set())
        if before is not None:
            error_msg("Trying to implement default newline: '\\n' or '\\r\\n'.\n" 
                      "The '\\n' option is not possible, since it has been occupied by '%s'.\n" \
                      "No newline can be defined by default."
                      % cc_type_name_db[before.cc_type], before.sr, DontExitF=True, 
                      SuppressCode=NotificationDB.warning_default_newline_0A_impossible)
            # In this case, no newline can be defined!
            return

        sm = StateMachine.from_character_set(newline_set)

        before = self.count_command_map.find_occupier(retour_set, set())
        if before is not None:
            error_msg("Trying to implement default newline: '\\n' or '\\r\\n'.\n" 
                      "The '\\r\\n' option is not possible, since '\\r' has been occupied by '%s'." \
                      % cc_type_name_db[before.cc_type],
                      before.sr, DontExitF=True, 
                      SuppressCode=NotificationDB.warning_default_newline_0D_impossible)
        else:
            sm.add_transition_sequence(sm.init_state_index, [retour_set, newline_set])

        self.specify_newline(sm, SourceRef_VOID)

    def finalize(self, fh):
        if self.whitespace_character_set.get() is None:
            self.specify("whitespace", Pattern[" \n"], sr=SourceFileRef())
        if self.sm_newline.get() is None:
            self.sm_newline_defaultize()
        self.consistency_check()

    def consistency_check(self):
        self.count_command_map.check_defined(self.sr, E_CharacterCountType.WHITESPACE)
        self.count_command_map.check_defined(self.sr, E_CharacterCountType.BEGIN_NEWLINE)

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

def _error_set_intersection(CcType, Before, sr):
    global cc_type_name_db

    note_f = False
    if    CcType         == E_CharacterCountType.END_NEWLINE \
       or Before.cc_type == E_CharacterCountType.END_NEWLINE:
        note_f = True

    prefix = {
        E_CharacterCountType.COLUMN:                   "",
        E_CharacterCountType.GRID:                     "",
        E_CharacterCountType.LINE:                     "",
        E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR: "beginning ",
        E_CharacterCountType.BEGIN_NEWLINE:            "beginning ",
        E_CharacterCountType.END_NEWLINE:              "ending ",
        E_CharacterCountType.BAD:                      "",
    }[CcType]

    error_msg("The %scharacter set defined in '%s' intersects" % (prefix, cc_type_name_db[CcType]),
              sr, DontExitF=True, WarningF=False)
    error_msg("with '%s' at this place." % cc_type_name_db[Before.cc_type], 
              Before.sr, DontExitF=note_f, WarningF=False)

    if note_f:
        error_msg("Note, for example, 'newline' cannot end with a character which is subject\n"
                  "to indentation counting (i.e. 'space' or 'grid').", sr)

def _error_if_defined_before(Before, sr):
    if not Before.set_f(): return

    error_msg("'%s' has been defined before;" % Before.name, sr, 
              DontExitF=True, WarningF=False)
    error_msg("at this place.", Before.sr.file_name, Before.sr.line_n)

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

_CounterSetupLineColumn_Default = None
def CounterSetupLineColumn_Default():
    global _CounterSetupLineColumn_Default

    if _CounterSetupLineColumn_Default is None:
        count_command_map = CountCmdMap()
        count_command_map.add(NumberSet(ord('\n')), "newline", 1, SourceRef_VOID)
        count_command_map.add(NumberSet(ord('\t')), "grid",    4, SourceRef_VOID)
        count_command_map.define_else("space",   1, SourceRef_VOID)                       # Define: "\else"
        count_command_map.assign_else_count_command(0, Setup.get_character_value_limit(), # Apply: "\else"
                                                    SourceRef_VOID) 

        _CounterSetupLineColumn_Default = ParserDataLineColumn(SourceRef_VOID, 
                                                               count_command_map)

    return _CounterSetupLineColumn_Default

