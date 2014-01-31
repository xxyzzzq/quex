from  quex.engine.generator.code.base import SourceRef_VOID
from  quex.engine.interval_handling   import NumberSet
from  quex.engine.tools               import return_None

CountCmdInfo = namedtuple("CountCmdInfo_tuple", ("trigger_set", "command_list", "cc_type"))

class CounterSetupLineColumn(object):
    __slots__ = ("sr",      # Source Reference
                 "column",  # Column Number Increment --> CharacterSet
                 "grid",    # Grid Step Size          --> CharacterSet
                 "newline") # Newline Number          --> CharacterSet

    def __init__(self, LccSetup=None, DefaultColumNPerCharacter=None, 
                 SourceReference=SourceRef_VOID):
        """Generate a counter db from a line column counter setup."""

        self.sr = SourceReference
        if LccSetup is None:
            self.column  = {}  
            self.grid    = {}  
            self.newline = {}  
        else:
            self.column  = _adapt(LccSetup.space_db)
            self.grid    = _adapt(LccSetup.grid_db)
            self.newline = _adapt(LccSetup.newline_db)

        self.defaultize(DefaultColumNPerCharacter)

    def get_column_number_per_chunk(self, CharacterSet):
        """Considers the counter database which tells what character causes
        what increment in line and column numbers. However, only those characters
        are considered which appear in the CharacterSet. 

        'CharacterSet' is None: All characters considered.

        If the special character handling column number increment always
        add the same value the return value is not None. Else, it is.

        RETURNS: None -- If there is no distinct column increment 
                 >= 0 -- The increment of column number for every character
                         from CharacterSet.
        """
        result     = None
        number_set = None
        for delta, character_set in self.special.iteritems():
            if CharacterSet is None or character_set.has_intersection(CharacterSet):
                if result is None: result = delta; number_set = character_set
                else:              return None

        if Setup.variable_character_sizes_f():
            result = homogeneous_chunk_n_per_character(number_set, 
                                                       Setup.buffer_codec_transformation_info)
        return result

    def get_count_command_map(self, CharacterSet, InputPName, DoorIdIfNotLexemeEnd=None):
        """Returns a list of NumberSet objects where for each X of the list it holds:


           DoorIdIfNotLexemeEnd = None => Lexeme end is not to be checked.

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
            
        if not CheckLexemeEndF:
            factory = CountCmdInfoFactory(ColumnNPerChunk, 
                                          DoorIdDone, 
                                          InputPName)
        else:
            factory = CountCmdInfoFactory_WithCheckLexemeEnd(ColumnNPerChunk, 
                                                             DoorIdDone, 
                                                             InputPName, 
                                                             DoorIdUndone)

        for delta, character_set in pruned_iteritems(self.column, CharacterSet):
            factory.add(E_CharacterCountType.CHARACTER, delta, character_set)
        
        for grid_step_n, character_set in pruned_iteritems(self.grid, CharacterSet):
            factory.add(E_CharacterCountType.GRID, grid_step_n, character_set)

        for delta, character_set in pruned_iteritems(self.newline, CharacterSet):
            factory.add(E_CharacterCountType.LINE, delta, character_set)

        return ColumnNPerChunk, \
               factory.incidence_id_map, \
               factory.on_before_reload, \
               factory.on_after_reload

    def defaultize(self, DefaultColumNPerCharacter):
        all_set = _get_all_character_set(self.column, self.grid, self.newline)

        self.column, \
        self.grid    = _defaultize_column_and_grid(self.column, self.grid, all_set)
        self.newline = _defaultize_if_admissible(self.newline, 1, ord('\n'), all_set)


class CounterSetupIndentation(object):
    __slots__ = ("sr",                     # Source Reference
                 "column",                 # Column N per Char --> CharacterSet
                 "grid",                   # Grid Step Size    --> CharacterSet
                 "sm_newline",             # State machine detecting 'newline'
                 "sm_newline_suppressor",  # State machine detecting 'newline suppressor'
                 "bad_character_set")      # Set of characters which shall not appear in indentation
    def __init__(self, IndSetup, SourceReference=SourceRef_VOID):
        self.sr                    = SourceReference
        self.column                = _adapt(IndSetup.space_db)
        self.grid                  = _adapt(IndSetup.grid_db)
        self.sm_newline            = IndSetup.newline_state_machine
        self.sm_newline_suppressor = IndSetup.newline_suppressor_state_machine
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

        self.column, \
        self.grid   = _defaultize_column_and_grid(self.column, self.grid, all_set)

        if len(self.column) == 0 and len(self.grid) == 0:
            error_msg("No space or grid defined for indentation counting. Default\n"
                      "values ' ' and '\\t' could not be used since they are specified as 'bad'.",
                      self.sr)

        self.sm_newline = self.defaultize_sm_newline(all_set)

    def defaultize_sm_newline(self, all_set):
        if self.sm_newline is not None:
            return self.sm_newline

        newline     = ord('\n')
        retour      = ord('\r')
        newline_set = NumberSet(newline)
        retour_set  = NumberSet(retour)
        end_idx     = None
        sm          = StateMachine()
        if not all_set.contains(newline):
            end_idx = sm.add_transition(sm.init_state_index, newline_set, AcceptanceF=True)
            all_set.unite_with(newline_set)

        if not all_set.contains(retour):
            all_set.unite_with(retour_set)
            mid_idx = sm.add_transition(sm.init_state_index, retour_set, AcceptanceF=False)
            sm.add_transition(mid_idx, newline_set, end_idx, AcceptanceF=True)
        return sm


_CounterSetupLineColumn_Default = None
def CounterSetupLineColumn_Default():
    global _CounterSetupLineColumn_Default
    if _CounterSetupLineColumn_Default is None:
        _CounterSetupLineColumn_Default = CounterSetupLineColumn()
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
    if _is_admissible(db, DefaultChar, all_set, Bad):
        default_set = NumberSet(DefaultChar)
        all_set.unite_with(default_set)         # ADAPT 'all_set'
        return { Count: NumberSet(DefaultChar) } 
    else:
        return {}

def _defaultize_column_and_grid(column, grid, all_set, Bad=None):
    """Note, that 'all_set' is adapted if default values are inserted.
    """
    if len(column) == 0 and len(grid) == 0:
        # If columns ore grids (or both) are defined, then it can be 
        # assumed that the specification as is, is intended
        column = _defaultize_if_admissible(column, 1, ord(' '), all_set, Bad)
        grid   = _defaultize_if_admissible(grid, 4, ord('\t'), all_set, Bad)
    return column, grid

class CountCmdInfoFactory:
    def __init__(self, ColumnNPerChunk, DoorIdDone, InputPName):
        self.column_count_per_chunk = ColumnNPerChunk
        self.door_id_done           = DoorIdDone
        self.input_p_name           = InputPName

        # Actions before and after reload buffer.
        self.on_before_reload, \
        self.on_after_reload   = self._before_and_after_reload()

        self.incidence_id_map  = dict()

    def add(self, CC_Type, Parameter, TriggerSet):
        self.incidence_id_map[dial_db.new_incidence_id()] = self._do(CC_Type, Parameter, TriggerSet)

    def _do(self, CC_Type, Parameter, TriggerSet)
        """                   .---------------.
                         ---->| Count Command |----> DoorIdDone
                              '---------------'

        NOTE: CountCmdInfoFactory_WithCheckLexemeEnd overwrites this member 
              function.
        """
        cl = self._command(CC_Type, Parameter) 
        cl.append(GotoDoorId(DoorIdDone))
        return CountCmdInfo(TriggerSet, cl, CC_Type)

    def _command(CC_Type, Parameter):
        if self.column_count_per_chunk is None:
            cmd = {
                E_CharacterCountType.COLUMN: ColumnCountAdd
                E_CharacterCountType.GRID:   ColumnCountGridAdd
                E_CharacterCountType.LINE:   LineCountAdd
            }[CC_Type](Parameter)
        else:
            cmd = {
                E_CharacterCountType.COLUMN: return_None
                E_CharacterCountType.GRID:   ColumnCountGridAddWithReferenceP
                E_CharacterCountType.LINE:   LineCountAddWithReferenceP
            }[CC_Type](Parameter, self.input_p_name, self.column_count_per_chunk)

        if cmd is None: return []
        else:           return [ cmd ]

    def _command_on_lexeme_end(CC_Type, Parameter):
        if   self.column_count_per_chunk is None:    return None
        elif CC_Type != E_CharacterCountType.COLUMN: return None

        return ColumnCountReferencePDeltaAdd(self.input_p_name, 
                                             self.column_count_per_chunk)

    def _before_and_after_reload(self):
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
        on_before_reload = []
        on_after_reload  = []
        if self.column_count_per_chunk is not None:
            on_before_reload.append(
                ColumnCountReferencePDeltaAdd(self.input_p_name, 
                                              self.column_count_per_chunk) 
            )
            on_after_reload.append( 
                ColumnCountReferencePSet(self.input_p_name) 
            )
        return on_before_reload, on_after_reload

class CountCmdInfoFactory_WithCheckLexemeEnd(CountCmdInfoFactory):
    def __init__(self, ColumnNPerChunk, DoorIdDone, InputPName, DoorIdUndone):
        CountCmdInfoFactory.__init__(self, ColumnNPerChunk, DoorIdDone, InputPName)
        self.door_id_undone = DoorIdUndone
        
    def _do(self, CC_Type, Parameter, TriggerSet)
        """     .---------------.    ,----------.   no
           ---->| Count Command |---< LexemeEnd? >------> DoorIdUndone
                '---------------'    '----+-----'
                                          | yes
                                   .---------------.
                                   |  Lexeme End   |
                                   | Count Command |---> DoorIdDone
                                   '---------------'
        """
        cl = self._command(CC_Type, Parameter)
        cl.extend([
            GotoDoorIdIfInputPNotEqualPointer("LexemeEnd", self.door_id_undone),
            self._command_on_lexeme_end(CC_Type, Parameter),
            GotoDoorId(self.door_id_done)
        ])
        return CountCmdInfo(TriggerSet, cl, CC_Type)


