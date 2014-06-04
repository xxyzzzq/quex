from   quex.input.files.parser_data.counter       import ParserDataLineColumn, \
                                                         ParserDataIndentation, \
                                                         CountInfo
from   quex.engine.interval_handling              import NumberSet
from   quex.engine.analyzer.terminal.core         import Terminal
from   quex.engine.generator.code.base            import SourceRef_VOID, \
                                                         SourceRef
from   quex.engine.generator.code.core            import CodeTerminal
from   quex.engine.interval_handling              import NumberSet
from   quex.engine.tools                          import return_None
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.analyzer.commands.core         import E_R, \
                                                         Assign, \
                                                         ColumnCountAdd, \
                                                         ColumnCountGridAdd, \
                                                         ColumnCountReferencePDeltaAdd, \
                                                         ColumnCountReferencePSet, \
                                                         ColumnCountGridAddWithReferenceP, \
                                                         LineCountAdd, \
                                                         LineCountAddWithReferenceP, \
                                                         GotoDoorId, \
                                                         GotoDoorIdIfInputPNotEqualPointer

from   quex.engine.state_machine.engine_state_machine_set import CharacterSetStateMachine

from   quex.engine.tools import typed
from   quex.blackboard   import E_CharacterCountType, \
                                setup as Setup, \
                                Lng

from   collections import namedtuple, defaultdict
from   itertools   import izip
from   operator    import itemgetter

import sys

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
        self.bad_character_set     = IndSetup.bad_character_set

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
    def __init__(self, CMap, ColumnNPerChunk, InputPName, CharacterSet):
        self.__map                  = CMap
        self.column_count_per_chunk = ColumnNPerChunk
        self.input_p_name           = InputPName
        self.character_set          = CharacterSet

        self.on_begin,         \
        self.on_end,           \
        self.on_before_reload, \
        self.on_after_reload   = CountCmdFactory.__prepare(ColumnNPerChunk)

    @staticmethod
    @typed(CounterDb=ParserDataLineColumn, CharacterSet=NumberSet)
    def from_ParserDataLineColumn(CounterDb, CharacterSet, InputPName):
        """Use NumberSet_All() if all characters shall be used.
        """
        cmap = [
            CountInfo(dial_db.new_incidence_id(), info.cc_type, info.value, intersection)
            for intersection, info in CounterDb.count_command_map.pruned_cgl_iterable(CharacterSet)
        ]

        ColumnNPerChunk = CounterDb.count_command_map.get_column_number_per_chunk(CharacterSet)

        return CountCmdFactory(cmap, ColumnNPerChunk, InputPName, CharacterSet) 

    @staticmethod
    @typed(CounterDb=ParserDataIndentation)
    def from_ParserDataIndentation(CounterDb, InputPName):
        """Return a factory that produces 'column' and 'grid' counting incidence_id-maps.
        """
        ColumnNPerChunk = CounterDb.count_command_map.get_column_number_per_chunk(NumberSet_All())

        cmap = [
            CountInfo(dial_db.new_incidence_id(), info.cc_type, info.value, character_set)
            for character_set, info in CounterDb.count_command_map.column_grid_bad_count_iterable()
        ]

        return CountCmdFactory(cmap, ColumnNPerChunk, InputPName, NumberSet_All()) 


    def is_equal(self, Other):
        if len(self.__map) != len(Other.__map):
            return False
        for x, y in izip(self.__map, Other.__map):
            if not x.character_set.is_equal(y.character_set):
                return False
            elif x.parameter != y.parameter:
                return False
        return True

    def covers(self, Min, Max):
        result = NumberSet()

        for info in self.__map:
            result.unite_with(info.character_set)
        return result.covers_range(Min, Max)

    def requires_reference_p(self):
        return self.column_count_per_chunk is not None

    def get_incidence_id_map(self, BeyondIncidenceId=None):
        """RETURNS: A list of pairs: (character_set, incidence_id) 
             
           All same counting actions are referred to by the same incidence id.

           If BeyondIncidenceId is given, then the remaining set of characters
           is associated with 'BeyondIncidenceId'.
        """
        result = [ (x.character_set, x.incidence_id) for x in self.__map ]
        if BeyondIncidenceId is not None:
            beyond_set = self.character_set.inverse().mask(0, Setup.get_character_value_limit())
            result.append((beyond_set, BeyondIncidenceId))
        return result
        
    def get_CharacterSetStateMachine(self, LexemeMaintainedF, ParallelSmList=None):
        """RETURNS: [0] CharacterSetStateMachine which accepts on counting 
                        actions. Each counting action has an incidence id 
                        associated with it. 

           The function 'get_terminal_list' returns a list of termins which 
           fit the incidence ids of the counting actions.
        """
        beyond_iid = dial_db.new_incidence_id()

        # Build a state machine based on (character set, incidence_id) pairs.
        cssm = CharacterSetStateMachine(
                   self.get_incidence_id_map(beyond_iid), 
                   LexemeMaintainedF, 
                   ParallelSmList, 
                   OnBegin        = self.on_begin, 
                   OnEnd          = self.on_end,
                   OnBeforeReload = self.on_before_reload,
                   OnAfterReload  = self.on_after_reload)

        return cssm, beyond_iid

    def get_terminal_list(self, OnEnd, BeyondIncidenceId, DoorIdExit, DoorIdOk, DoorIdOnLexemeEnd=None):
        # _get_terminal() --> _do_with_lexeme_end_check()
        #             '-----> _do()
        #
        # In the '_do' functions the 'door_id_ok' and 'door_id_on_lexeme_end'
        # are required.
        self.door_id_ok            = DoorIdOk
        self.door_id_on_lexeme_end = DoorIdOnLexemeEnd
        result = [ self._get_terminal(x) for x in self.__map ] 
        if BeyondIncidenceId is not None:
            result.append(self.__get_terminal_beyond(OnEnd, DoorIdExit, BeyondIncidenceId))
        return result

    @staticmethod
    def __get_terminal_beyond(OnEnd, DoorIdExit, BeyondIid, AdditionalCommandList=None):
        """Generate Terminal to be executed upon exit from the 'loop'.
        
           DoorIdExit -- DoorId where to go after the terminal has finished.
           BeyondIid  -- 'Beyond Incidence Id', that is the incidencen id if of
                         the terminal to be generated.
        """
        on_beyond = []
        on_beyond.extend(OnEnd)
        if AdditionalCommandList is not None:
            on_beyond.extend(AdditionalCommandList)
        on_beyond.append(GotoDoorId(DoorIdExit))

        code_on_beyond  = CodeTerminal([Lng.COMMAND(cmd) for cmd in on_beyond])

        result = Terminal(code_on_beyond, "<BEYOND>") # Put last considered character back
        result.set_incidence_id(BeyondIid)

        return result


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
            GotoDoorIdIfInputPNotEqualPointer(self.door_id_ok, E_R.LexemeEnd),
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
            }[CC_Type](Parameter, E_R.InputP, self.column_count_per_chunk)

        if cmd is None: return []
        else:           return [ cmd ]

    def _command_on_lexeme_end(self, CC_Type, Parameter):
        if   self.column_count_per_chunk is None:    return None
        elif CC_Type != E_CharacterCountType.COLUMN: return None

        return ColumnCountReferencePDeltaAdd(E_R.InputP, self.column_count_per_chunk)

    @staticmethod
    def __prepare(ColumnNPerChunk):
        """BEFORE RELOAD:
                                                           input_p
                                                           |
                [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]
                                            |
                                            reference_p
             
                     column_n += (input_p - reference_p) * C

              where C = ColumnNPerChunk

           AFTER RELOAD:

                 input_p
                 |
                [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]
                 |
                 reference_p
        """
        if ColumnNPerChunk is None: 
            return [], [], [], []


        # When there is more than one chunk possibly involved, then it is
        # possible that reload happens in between one character. I such cases
        # the 'input_p' cannot be used as reference for delta-add. Here,
        # we must rely on the 'character begin_p'.
        if Setup.variable_character_sizes_f(): pointer = E_R.CharacterBeginP
        else:                                  pointer = E_R.InputP

        on_begin         = [ ColumnCountReferencePSet(pointer) ]
        on_after_reload  = [ ColumnCountReferencePSet(pointer) ]
        on_end           = [ ColumnCountReferencePDeltaAdd(pointer, ColumnNPerChunk) ]
        on_before_reload = [ ColumnCountReferencePDeltaAdd(pointer, ColumnNPerChunk) ]

        return on_begin, on_end, on_before_reload, on_after_reload

