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
            self_character_set  = selfi[0]
            self_info           = selfi[1]
            other_character_set = otheri[0]
            other_info          = otheri[1]
            if not self_character_set.is_equal(other_character_set):
                return False
            elif self_info != other_info:
                return False
        return True

    def covers(self, Min, Max):
        result = NumberSet()
        for character_set, info in self.count_command_map.get_map():
            result.unite_with(character_set)
        return result.covers_range(Min, Max)

    def get_factory(self, CharacterSet, InputPName):
        ColumnNPerChunk = self.count_command_map.get_column_number_per_chunk(CharacterSet)

        cmap = [
            CountInfo(dial_db.new_incidence_id(), info.cc_type, info.value, intersection)
            for intersection, info in self.count_command_map.pruned_iterable(CharacterSet)
        ]

        return CountCmdFactory(cmap, ColumnNPerChunk, InputPName) 

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
        count_command_map.define_else("space",   1, SourceRef_VOID)                       # Define: "\else"
        count_command_map.assign_else_count_command(0, Setup.get_character_value_limit(), # Apply: "\else"
                                                    SourceRef_VOID) 

        _CounterSetupLineColumn_Default = CounterSetupLineColumn(count_command_map)

    return _CounterSetupLineColumn_Default

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

class CountCmdFactory:
    def __init__(self, CMap, ColumnNPerChunk, InputPName):
        self.__map                  = CMap
        self.column_count_per_chunk = ColumnNPerChunk
        self.input_p_name           = InputPName

        self.on_begin,         \
        self.on_before_reload, \
        self.on_after_reload   = self.__prepare()

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

    def __prepare(self):
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
            return [], [], []

        on_begin = [
            ColumnCountReferencePSet(self.input_p_name) 
        ]
        on_before_reload = [
            ColumnCountReferencePDeltaAdd(self.input_p_name, 
                                          self.column_count_per_chunk) 
        ]
        on_after_reload  = [
            ColumnCountReferencePSet(self.input_p_name) 
        ]
        return on_begin, on_before_reload, on_after_reload

