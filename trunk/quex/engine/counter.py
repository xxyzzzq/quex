from   quex.input.files.parser_data.counter       import CountCmdMap
from   quex.engine.analyzer.terminal.core         import Terminal
from   quex.engine.generator.code.base            import SourceRef_VOID, \
                                                         SourceRef
from   quex.engine.generator.code.core            import CodeTerminal
from   quex.engine.interval_handling              import NumberSet
from   quex.engine.tools                          import return_None
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.analyzer.commands              import CommandList, \
                                                         ColumnCountAdd, \
                                                         ColumnCountGridAdd, \
                                                         ColumnCountReferencePDeltaAdd, \
                                                         ColumnCountReferencePSet, \
                                                         ColumnCountGridAddWithReferenceP, \
                                                         LineCountAdd, \
                                                         LineCountAddWithReferenceP, \
                                                         GotoDoorId, \
                                                         GotoDoorIdIfInputPNotEqualPointer
import quex.engine.state_machine.transformation   as     transformation

from   quex.engine.tools import typed
from   quex.blackboard import E_CharacterCountType, \
                              setup as Setup, \
                              Lng
from   collections import namedtuple, defaultdict
from   itertools   import izip
from   operator    import itemgetter

CountInfo = namedtuple("CountInfo", ("incidence_id", "cc_type", "parameter", "character_set"))

class CounterSetupLineColumn(object):
    __slots__ = ("sr",                 # Source Reference
                 "count_command_map")  # Column Number Increment --> CharacterSet

    @typed(TheCountCmdMap=CountCmdMap, SourceReference=SourceRef)
    def __init__(self, TheCountCmdMap=None, SourceReference=SourceRef_VOID):
        """Generate a counter db from a line column counter setup."""
        assert CountCmdMap is not None

        self.sr                = SourceReference
        self.count_command_map = TheCountCmdMap

    def is_equal(self, Other):
        self_map  = self.count_command_map.get_map()
        other_map = Other.count_command_map.get_map()
        if len(self_map) != len(other_map):
            return False
        for selfi, otheri in izip(self_map, other_map):
            self_character_set = selfi[0]
            self_info          = selfi[1]
            other_character_set = otheri[0]
            other_info          = otheri[1]
            if not self_character_set.is_equal(other_character_set):
                return False
            elif self_info != other_info:
                return False
        return True

    def covered_character_set(self):
        result = NumberSet()
        for character_set, info in self.count_command_map.get_map():
            result.unite_with(character_set)
        return result

    def __get_column_number_per_chunk(self, CharacterSet):
        """Considers the counter database which tells what character causes
        what increment in line and column numbers. However, only those characters
        are considered which appear in the CharacterSet. 

        'CharacterSet' is None: All characters considered.

        If the column character handling column number increment always
        add the same value the return value is not None. Else, it is.

        RETURNS: None -- If there is no distinct column increment 
                 >= 0 -- The increment of column number for every character
                         from CharacterSet.
        """
        column_incr_per_character = None
        number_set                = None
        for character_set, info in self.count_command_map.get_map():
            if info.cc_type != E_CharacterCountType.COLUMN: 
                continue
            elif column_incr_per_character is None:       
                column_incr_per_character = info.value
                number_set                = character_set
            elif gccolumn_incr_per_character == info.value: 
                number_set.unite_with(character_set)
            else:
                return None

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

    def get_factory(self, CharacterSet, InputPName):
        ColumnNPerChunk = self.__get_column_number_per_chunk(CharacterSet)

        def pruned_iterable(CountCmdMap, CharacterSet):
            for character_set, info in self.count_command_map.get_map():
                if not character_set.has_intersection(CharacterSet):
                    continue
                yield character_set.intersection(CharacterSet), info

        cmap = [
            CountInfo(dial_db.new_incidence_id(), info.cc_type, info.value, intersection)
            for intersection, info in pruned_iterable(self.count_command_map, CharacterSet)
        ]

        return CountCmdFactory(cmap, ColumnNPerChunk, InputPName) 

    @staticmethod
    def _db_to_text(title, CountCmdInfoList):
        txt = "%s:\n" % title
        for character_set, info in sorted(CountCmdInfoList, key=lambda x: x[0].minimum()):
            if type(info.value) in [str, unicode]:
                txt += "    %s by %s\n" % (info.value, character_set.get_utf8_string())
            else:
                txt += "    %3i by %s\n" % (info.value, character_set.get_utf8_string())
        return txt

    def __str__(self):
        db_by_name = defaultdict(list)
        for character_set, info in self.count_command_map.get_map():
            db_by_name[info.identifier].append((character_set, info))

        txt = [
            CounterSetupLineColumn._db_to_text(name, count_command_info_list)
            for name, count_command_info_list in sorted(db_by_name.iteritems(), key=itemgetter(0))
        ]
        return "".join(txt)

class CounterSetupIndentation(object):
    __slots__ = ("sr",                     # Source Reference
                 "count_command_map",      # Column N per Char --> CharacterSet
                                           # Grid Step Size    --> CharacterSet
                 "sm_newline",             # State machine detecting 'newline'
                 "sm_newline_suppressor",  # State machine detecting 'newline suppressor'
                 "bad_character_set")      # Set of characters which shall not appear in indentation
    def __init__(self, IndSetup, SourceReference=SourceRef_VOID):
        self.sr                    = SourceReference
        self.count_command_map     = IndSetup.count_command_map
        self.sm_newline            = IndSetup.sm_newline
        self.sm_newline_suppressor = IndSetup.sm_newline_suppressor
        self.bad_character_set     = IndSetup.bad_character_set.get()

        self.defaultize()

    def homogeneous_spaces(self):
        # Note, from about the grid_db does not accept grid values of '1'
        if   len(self.grid) != 0:   return False
        elif len(self.column) != 1 : return False
        # Here, the column can have only one value. If it is '1' than 
        # the indentation is based soley on single spaces.
        return self.column.has_key(1)

    def indentation_count_character_set(self):
        """Returns the superset of all characters that are involved in
        indentation counting. That is the set of character that can appear
        between newline and the first non whitespace character.  
        """
        result = NumberSet()
        for character_set in self.column.values():
            result.unite_with(character_set)
        for character_set in self.grid.values():
            result.unite_with(character_set)
        return result

    def consistency_check(self, fh):
        Base.consistency_check(self, fh)
        assert not self.sm_newline.get().is_empty()

    def defaultize(self):
        all_set = _get_all_character_set(self.column, self.grid)
        all_set.unite_with(self.bad_character_set)

        self.sm_newline = self.defaultize_sm_newline(all_set)

_CounterSetupLineColumn_Default = None
def CounterSetupLineColumn_Default():
    global _CounterSetupLineColumn_Default

    if _CounterSetupLineColumn_Default is None:
        count_command_map = CountCmdMap()
        count_command_map.add(NumberSet(ord('\n')), "newline", 1, SourceRef_VOID)
        count_command_map.add(NumberSet(ord('\t')), "grid",    4, SourceRef_VOID)
        count_command_map.add(None,                 "space",   1, SourceRef_VOID)         # Define: "\else"
        count_command_map.assign_else_count_command(0, Setup.get_character_value_limit()) # Apply: "\else"

        _CounterSetupLineColumn_Default = CounterSetupLineColumn(count_command_map)

    return _CounterSetupLineColumn_Default

def _adapt(db):
    return dict((count, parameter.get()) for count, parameter in db.iteritems())

def _get_all_character_set(*DbList):
    result = NumberSet()
    for db in DbList:
        for character_set in db.itervalues():
            result.unite_with(character_set)
    return result

def _is_admissible(db, DefaultChar, AllCharSet, Bad):
    if   len(db) != 0:                                  return False
    elif Bad is not None and Bad.contains(DefaultChar): return False
    elif AllCharSet.contains(DefaultChar):              return False
    else:                                               return True

def _defaultize_if_admissible(db, Count, DefaultChar, all_set, Bad=None):
    """'all_set' is adpated, for further investigations.
    """
    if len(db) != 0:
        return
    elif _is_admissible(db, DefaultChar, all_set, Bad):
        default_set = NumberSet(DefaultChar)
        all_set.unite_with(default_set)         # ADAPT 'all_set'
        return { Count: default_set } 
    else:
        return {}

def _defaultize_column_and_grid(column, grid, all_set, Bad=None):
    """Note, that 'all_set' is adapted if default values are inserted.
    """
    if len(grid) == 0:
        # Define the 'grid' step on tabulator, if it is not covered by some
        # other parameter.
        grid = _defaultize_if_admissible(grid, 4, ord('\t'), all_set, Bad)
    
    remaining_set = all_set.inverse()
    if Bad is not None: 
        remaining_set.subtract(Bad)

    if not remaining_set.is_empty():
        column = { 1: remaining_set.inverse() }

    return column, grid

class CountCmdFactory:
    def __init__(self, CMap, ColumnNPerChunk, InputPName):
        self.__map                  = CMap
        self.column_count_per_chunk = ColumnNPerChunk
        self.input_p_name           = InputPName

        self.__prepare_before_and_after_reload()

    def requires_reference_p(self):
        return self.column_count_per_chunk is not None

    def get_incidence_id_map(self):
        return [ (x.character_set, x.incidence_id) for x in self.__map ]

    def get_terminal_list(self, IncidenceMap, DoorIdOk, DoorIdOnLexemeEnd=None):
        self.door_id_ok            = DoorIdOk
        self.door_id_on_lexeme_end = DoorIdOnLexemeEnd
        return [ self._get_terminal(x) for x in self.__map ] 

    def _get_terminal(self, X):
        assert self.door_id_ok is not None

        if self.door_id_on_lexeme_end is not None:
            cl = self._do_with_lexeme_end_check(X.cc_type, X.parameter)
        else:
            cl = self._do(X.cc_type, X.parameter)

        terminal = Terminal(CodeTerminal([Lng.COMMAND(cmd) for cmd in cl]))
        terminal.set_incidence_id(X.incidence_id)
        return terminal

    def _do(self, CC_Type, Parameter):
        """                   .---------------.
                         ---->| Count Command |----> DoorIdOk
                              '---------------'
        """
        cl = self._command(CC_Type, Parameter) 
        cl.append(GotoDoorId(self.door_id_ok))
        return cl

    def _do_with_lexeme_end_check(self, CC_Type, Parameter):
        """     .---------------.    ,----------.   no
           ---->| Count Command |---< LexemeEnd? >------> DoorIdOk
                '---------------'    '----+-----'
                                          | yes
                                   .---------------.
                                   |  Lexeme End   |
                                   | Count Command |----> DoorIdOnLexemeEnd
                                   '---------------'
        """
        assert self.door_id_ok is not None
        assert self.door_id_on_lexeme_end is not None

        cl = self._command(CC_Type, Parameter)
        cl.append(
            GotoDoorIdIfInputPNotEqualPointer(self.door_id_ok, "LexemeEnd"),
        )

        check_cmd = self._command_on_lexeme_end(CC_Type, Parameter)
        if check_cmd is not None:
            cl.append(check_cmd)

        cl.append(
            GotoDoorId(self.door_id_on_lexeme_end)
        )
        return cl

    def _command(self, CC_Type, Parameter):
        if self.column_count_per_chunk is None:
            cmd = {
                E_CharacterCountType.COLUMN: ColumnCountAdd,
                E_CharacterCountType.GRID:   ColumnCountGridAdd,
                E_CharacterCountType.LINE:   LineCountAdd,
            }[CC_Type](Parameter)
        else:
            cmd = {
                E_CharacterCountType.COLUMN: return_None,
                E_CharacterCountType.GRID:   ColumnCountGridAddWithReferenceP,
                E_CharacterCountType.LINE:   LineCountAddWithReferenceP,
            }[CC_Type](Parameter, self.input_p_name, self.column_count_per_chunk)

        if cmd is None: return []
        else:           return [ cmd ]

    def _command_on_lexeme_end(self, CC_Type, Parameter):
        if   self.column_count_per_chunk is None:    return None
        elif CC_Type != E_CharacterCountType.COLUMN: return None

        return ColumnCountReferencePDeltaAdd(self.input_p_name, 
                                             self.column_count_per_chunk)

    def __prepare_before_and_after_reload(self):
        """BEFORE RELOAD:
                                                           input_p
                                                           |
                [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]
                                            |
                                            reference_p
             
                     column_n += (input_p - reference_p) * C

              where C = self.column_count_per_chunk.

           AFTER RELOAD:

                 input_p
                 |
                [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]
                 |
                 reference_p
        """
        if self.column_count_per_chunk is None: 
            self.on_before_reload = []
            self.on_after_reload  = []
        else:
            self.on_before_reload = [
                ColumnCountReferencePDeltaAdd(self.input_p_name, 
                                              self.column_count_per_chunk) 
            ]
            self.on_after_reload  = [
                ColumnCountReferencePSet(self.input_p_name) 
            ]

