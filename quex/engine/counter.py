from  quex.engine.interval_handling import NumberSet

class CounterSetupLineColumn(object):
    __slots__ = ("column", "grid", "newline")

    def __init__(self, LccSetup=None, DefaultColumNPerCharacter=None, SourceReference=None):
        """Generate a counter db from a line column counter setup."""
        assert SourceReference is not None

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

    def defaultize(self, DefaultColumNPerCharacter):
        all_set = _get_all_character_set(self.column, self.grid, self.newline)

        self.column, \
        self.grid    = _defaultize_column_and_grid(self.column, self.grid, all_set)
        self.newline = _defaultize_if_admissible(self.newline, 1, ord('\n'), all_set)


class CounterSetupIndentation(object):
    __slots__ = ("special", "grid", "sm_newline", "sm_newline_suppressor", "bad_character_set")
    def __init__(self, IndSetup, SourceReference):
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


