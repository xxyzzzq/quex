from   quex.input.code.core                       import CodeTerminal
from   quex.engine.counter                        import LineColumnCount, \
                                                         IndentationCount, \
                                                         CountAction, \
                                                         count_operation_db_without_reference, \
                                                         count_operation_db_with_reference
from   quex.engine.analyzer.door_id_address_label import dial_db
from   quex.engine.misc.interval_handling         import NumberSet
from   quex.engine.misc.tools                     import typed

from   quex.blackboard import E_CharacterCountType, \
                              E_R, \
                              setup as Setup, \
                              Lng

from   itertools   import izip, chain
from   collections import defaultdict

from   copy import copy

class CountInfo(object):
    __slots__ = ("incidence_id", "character_set", "count_action")

    @typed(CountOpInfo=CountAction, CharacterSet=NumberSet)
    def __init__(self, IncidenceId, CharacterSet, TheCountAction):
        self.incidence_id  = IncidenceId
        self.character_set = CharacterSet 
        self.count_action  = TheCountAction

    @property
    def cc_type(self):
        return self.count_action.cc_type

    @property
    def parameter(self):
        return self.count_action.value

    def get_OpList(self, ColumnCountPerChunk):
        if ColumnCountPerChunk is None:
            return count_operation_db_without_reference[self.cc_type](self.parameter)
        else:
            return count_operation_db_with_reference[self.cc_type](self.parameter, 
                                                                   ColumnCountPerChunk)

    def __str__(self):
        return "(incidence_id: %s; character_set: %s; count_action: %s)" \
               % (self.incidence_id, self.character_set, self.count_action)

class CountInfoMap:
    """________________________________________________________________________
    Produces Count Commands

    The factory is setup with basic parameters which are used later to produce
    count commands. 
    ___________________________________________________________________________
    """
    def __init__(self, CMap, CharacterSet):
        ## self.counter_db   = CounterDb # is LineColumnCount/IndentationCount
        self.__map           = CMap
        ## self.input_p_name = InputPName
        self.__character_set = CharacterSet

        self.__on_begin         = None
        self.__on_end           = None
        self.__on_before_reload = None
        self.__on_after_reload  = None

        # (Only indentation handler will set the following)
        self.door_id_on_bad_indentation = None

    @staticmethod
    @typed(CounterDb=LineColumnCount, CharacterSet=NumberSet)
    def from_LineColumnCount(CounterDb, CharacterSet, InputPName):
        """Use NumberSet_All() if all characters shall be used.
        """
        cmap = [
            CountInfo(dial_db.new_incidence_id(), intersection, info)
            for intersection, info in CounterDb.count_command_map.column_grid_line_iterable_pruned(CharacterSet)
        ]

        return CountInfoMap(cmap, CharacterSet) 

    @staticmethod
    @typed(ISetup=IndentationCount, CounterDb=LineColumnCount)
    def from_IndentationCount(ISetup, CounterDb, InputPName, DoorIdBad):
        """Return a factory that produces 'column' and 'grid' counting incidence_id-maps.
        """
        result = CountInfoMap.from_LineColumnCount(ISetup.whitespace_character_set.get())
        # Up to now, the '__map' contains only character sets which intersect with the 
        # defined whitespace. Add the 'bad indentation characters'.
        bad_character_set = ISetup.bad_character_set.get()
        if bad_character_set is not None:
            result.__map.append(
                CountInfo(dial_db.new_incidence_id(), bad_character_set,
                          CountAction(E_CharacterCountType.BAD, None))
            )
        result.door_id_on_bad_indentation = DoorIdBad
        return result

    def loop_character_set(self):
        return NumberSet.from_union_of_iterable(x.character_set for x in self.__map)

    def iterable_in_sub_set(self, SubSet):
        """Searches for CountInfo objects where the character set intersects
        with the 'SubSet' given as arguments. 

        YIELDS: [0] Character Set
                [1] Count Action for character set
                    = None, if no count action has been specified.
        """
        remainder = SubSet.clone()
        for ci in self.__map:
            if not SubSet.has_intersection(ci.character_set): continue
            yield SubSet.intersection(ci.character_set), ci.count_action
            remainder.subtract(ci.character_set)

        if not remainder.is_empty():
            yield remainder, None

    def op_list_for_sub_set(self, SubSet):
        """Searches for 'SubSet' in the counting map and returns the operation
        list that relates to it.

        RETURNS: list of Op-s.
                 None, if SubSet is not a subset of any.
        """
        for ci in self.__map:
            if ci.character_set.is_superset(SubSet): 
                return copy(ci.get_OpList())
        return None

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

