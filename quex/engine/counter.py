def _adapt(db):
    return dict((count, parameter.get()) 
                for count, parameter in db.iteritems())

class CounterSetupIndentation(object):
    def __init__(self, IndSetup):
        self.special               = _adapt(IndSetup.space_db)
        self.grid                  = _adapt(IndSetup.grid_db)
        self.sm_newline            = IndSetup.newline_state_machine
        self.sm_newline_suppressor = IndSetup.newline_state_machine
        self.bad_character_set     = IndSetup.bad_character_set.get()

    def homogeneous_spaces(self):
        # Note, from about the grid_db does not accept grid values of '1'
        if   len(self.grid_db) != 0:   return False
        elif len(self.space_db) != 1 : return False
        # Here, the space_db can have only one value. If it is '1' than 
        # the indentation is based soley on single spaces.
        return self.space_db.has_key(1)

class CounterSetupLineColumn(object):
    # 'CounterDB' maps from counts to the character set that is involved.
    __slots__ = ("special", "grid", "newline")

    def __init__(self, LccSetup):
        """Generate a counter db from a line column counter setup."""
        assert LCC_Setup is not None
        self.special = _adapt(LccSetup.space_db)
        self.grid    = _adapt(LccSetup.grid_db)
        self.newline = _adapt(LccSetup.newline_db)

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

_CounterDb_Default = None
def CounterDb_Default():
    global _CounterDb_Default

    if _CounterDb_Default is not None:
        default = CounterSetupLineColumn()
        default.seal(DefaultSpaceSpec=1, FH=-1)
        _CounterDb_Default = CounterDB(default)
    return _CounterDb_Default

