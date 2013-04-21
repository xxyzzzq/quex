import quex.engine.state_machine.transformation     as     transformation
from quex.blackboard import setup as Setup, \
                            E_ActionIDs

class CounterDB:
    # 'CounterDB' maps from counts to the character set that is involved.
    __slots__ = ("special", "grid", "newline")

    def __init__(self, LCC_Setup):
        """Generate a counter db from a line column counter setup."""
        assert LCC_Setup is not None
        def adapt(db):
            return dict((count, parameter.get()) for count, parameter in db.iteritems())
        self.special = adapt(LCC_Setup.space_db)
        self.grid    = adapt(LCC_Setup.grid_db)
        self.newline = adapt(LCC_Setup.newline_db)

    def get_counter_dictionary(self, ConcernedCharacterSet):
        """Returns a list of NumberSet objects where for each X of the list it holds:

             (i)  X is subset of ConcernedCharacterSet
                   
             (ii) It is related to a different counter action than Y,
                  for each other object Y in the list.

           RETURNS: 

                        list:    (character_set, count_action)
        """
        def prune(X, ConcernedCharacterSet):
            if ConcernedCharacterSet is None: return X
            else:                             return X.intersection(ConcernedCharacterSet)

        result = []
        for delta, character_set in self.special.iteritems():
            x = prune(character_set, ConcernedCharacterSet)
            if x.is_empty(): continue
            result.append((x, ColumnAdd(delta)))

        for grid_step_n, character_set in self.grid.iteritems():
            x = prune(character_set, ConcernedCharacterSet)
            if x.is_empty(): continue
            result.append((x, GridAdd(grid_step_n)))

        for delta, character_set in self.newline.iteritems():
            x = prune(character_set, ConcernedCharacterSet)
            if x.is_empty(): continue
            result.append((x, LineAdd(delta)))

        return result

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
            result = transformation.homogeneous_chunk_n_per_character(number_set, 
                                                                      Setup.buffer_codec_transformation_info)
        return result

class CountAction:
    __slots__ = ("value")
    def __init__(self, Value):
        self.value = Value

    @staticmethod
    def get_epilog(ImplementationType):
        LanguageDB = Setup.language_db
        result = []
        result.append(E_ActionIDs.ON_GOOD_TRANSITION)
        return result

class ExitAction(CountAction):
    def __init__(self):
        CountAction.__init__(self, -1)

    @staticmethod
    def get_txt(ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        result = []
        if ColumnCountPerChunk is not None:
            LanguageDB.REFERENCE_P_COLUMN_ADD(result, IteratorName, ColumnCountPerChunk)
        return result

    @staticmethod
    def get_epilog(ImplementationType):
        LanguageDB = Setup.language_db
        return [E_ActionIDs.ON_EXIT]

class ColumnAdd(CountAction):
    def __init__(self, Value):
        CountAction.__init__(self, Value)

    def get_txt(self, ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        if ColumnCountPerChunk is None and self.value != 0: 
            return ["__QUEX_IF_COUNT_COLUMNS_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(self.value)]
        else:
            return []

class GridAdd(CountAction):
    def __init__(self, Value):
        CountAction.__init__(self, Value)

    def get_txt(self, ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        txt = []
        if ColumnCountPerChunk is not None:
            txt.append(0)
            LanguageDB.REFERENCE_P_COLUMN_ADD(txt, IteratorName, ColumnCountPerChunk) 

        txt.append(0)
        txt.extend(LanguageDB.GRID_STEP("self.counter._column_number_at_end", "size_t",
                                        self.value, IfMacro="__QUEX_IF_COUNT_COLUMNS"))

        if ColumnCountPerChunk is not None:
            txt.append(0)
            LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

        return txt

class LineAdd(CountAction):
    def __init__(self, Value):
        CountAction.__init__(self, Value)

    def get_txt(self, ColumnCountPerChunk, IteratorName):
        LanguageDB = Setup.language_db
        txt        = []
        # Maybe, we only want to set the column counter to '0'.
        # Such action is may be connected to unicode point '0x0D' carriage return.
        if self.value != 0:
            txt.append("__QUEX_IF_COUNT_LINES_ADD((size_t)%s);\n" % LanguageDB.VALUE_STRING(self.value))
            txt.append(0)
        txt.append("__QUEX_IF_COUNT_COLUMNS_SET((size_t)1);\n")

        if ColumnCountPerChunk is not None:
            txt.append(0)
            LanguageDB.REFERENCE_P_RESET(txt, IteratorName) 

        return txt

