from   quex.input.code.core                       import CodeTerminal
from   quex.input.files.parser_data.counter       import ParserDataLineColumn, \
                                                         ParserDataIndentation, \
                                                         CountInfo
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.misc.interval_handling         import NumberSet
from   quex.engine.misc.tools                     import typed

from   quex.blackboard import E_CharacterCountType, \
                              E_R, \
                              setup as Setup, \
                              Lng

from   itertools   import izip, chain
from   collections import defaultdict


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

class LoopCountOpFactory:
    """________________________________________________________________________
    Produces Count Commands

    The factory is setup with basic parameters which are used later to produce
    count commands. 

    ___________________________________________________________________________
    """
    def __init__(self, CounterDb, CMap, InputPName, CharacterSet):
        self.counter_db      = CounterDb
        self.__map           = CMap
        self.input_p_name    = InputPName
        self.__character_set = CharacterSet

        self.__on_begin         = None
        self.__on_end           = None
        self.__on_before_reload = None
        self.__on_after_reload  = None

        # (Only indentation handler will set the following)
        self.door_id_on_bad_indentation = None

    @staticmethod
    @typed(CounterDb=ParserDataLineColumn, CharacterSet=NumberSet)
    def from_ParserDataLineColumn(CounterDb, CharacterSet, InputPName):
        """Use NumberSet_All() if all characters shall be used.
        """
        cmap = [
            CountInfo(dial_db.new_incidence_id(), info.cc_type, info.value, intersection)
            for intersection, info in CounterDb.count_command_map.column_grid_line_iterable_pruned(CharacterSet)
        ]

        return LoopCountOpFactory(CounterDb, cmap, InputPName, CharacterSet) 

    @staticmethod
    @typed(ISetup=ParserDataIndentation, CounterDb=ParserDataLineColumn)
    def from_ParserDataIndentation(ISetup, CounterDb, InputPName, DoorIdBad):
        """Return a factory that produces 'column' and 'grid' counting incidence_id-maps.
        """
        result = LoopCountOpFactory.from_ParserDataLineColumn(CounterDb, 
                                                              ISetup.whitespace_character_set.get(), 
                                                              InputPName)
        # Up to now, the '__map' contains only character sets which intersect with the 
        # defined whitespace. Add the 'bad indentation characters'.
        bad_character_set = ISetup.bad_character_set.get()
        if bad_character_set is not None:
            result.__map.append(
                CountInfo(dial_db.new_incidence_id(), E_CharacterCountType.BAD, None, 
                          bad_character_set)
            )
        result.door_id_on_bad_indentation = DoorIdBad
        return result

    def loop_character_set(self):
        return NumberSet.from_union_of_iterable(x.character_set for x in self.__map)

    def iterable_in_sub_set(self, SubSet):
        """Searches for CountInfo objects where the character set intersects
        with the 'SubSet' given as arguments. 

        YIELDS: [0] SubSet that intersects
                [1] Incidence Id related to the command
        """
        db = defaultdict(NumberSet)
        for ci in self.__map:
            common = SubSet.intersection(ci.character_set)
            if not common.is_empty:
                db[ci.incidence_id].unite_with(common)

        for incidence_id, number_set in db.iteritems():
            yield incidence_id, number_set

    def get_incidence_id_map(self):
        """RETURNS: A list of pairs: (character_set, incidence_id) 
             
           All same counting actions are referred to by the same incidence id.

           If BeyondIncidenceId is given, then the remaining set of characters
           is associated with 'BeyondIncidenceId'.
        """
        return [ (x.character_set, x.incidence_id) for x in self.__map ]

    def get_column_count_per_chunk(self):
        return self.counter_db.count_command_map.get_column_number_per_chunk(self.character_set)

    @property
    def on_begin(self):
        if not self.__on_begin: self.__prepare()
        return self.__on_begin

    @property
    def on_end(self):
        if not self.__on_end: self.__prepare()
        return self.__on_end

    @property
    def on_before_reload(self):
        if not self.__on_before_reload: self.__prepare()
        return self.__on_before_reload

    @property
    def on_after_reload(self):
        if not self.__on_after_reload: self.__prepare()
        return self.__on_after_reload

    @property
    def character_set(self):
        return self.__character_set.intersection(Setup.buffer_codec.source_set)

    def character_set_update(self, MoreCharacterSet):
        self.__character_set.unite_with(MoreCharacterSet)

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
        return self.get_column_count_per_chunk() is not None

    def __prepare(self):
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
        column_n_per_code_unit = self.get_column_count_per_chunk()

        if column_n_per_code_unit is None: 
            self.__on_begin         = [ ]
            self.__on_end           = [ ]
            self.__on_before_reload = [ ]
            self.__on_after_reload  = [ ]
        else:
            # When there is more than one chunk possibly involved, then it is
            # possible that reload happens in between one character. I such cases
            # the 'input_p' cannot be used as reference for delta-add. Here,
            # we must rely on the 'character begin_p'.
            if Setup.buffer_codec.variable_character_sizes_f(): pointer = E_R.CharacterBeginP
            else:                                               pointer = E_R.InputP

            self.__on_begin = [ 
                Op.ColumnCountReferencePSet(pointer) 
            ]
            self.__on_end = [ 
                Op.ColumnCountReferencePDeltaAdd(pointer, column_n_per_code_unit, False) 
            ]
            self.__on_before_reload = [ 
                Op.ColumnCountReferencePDeltaAdd(pointer, column_n_per_code_unit, False) 
            ]
            self.__on_after_reload = [ 
                Op.ColumnCountReferencePSet(pointer) 
            ]


