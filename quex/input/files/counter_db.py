from   quex.engine.state_machine.transformation     import homogeneous_chunk_n_per_character
from   quex.engine.interval_handling                import NumberSet
from   quex.engine.generator.base                   import LoopGenerator
from   quex.engine.analyzer.transition_map          import TransitionMap
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.blackboard import setup as Setup, \
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
            result = homogeneous_chunk_n_per_character(number_set, 
                                                       Setup.buffer_codec_transformation_info)
        return result

    def get_map(self, 
                IteratorName       = None,
                InsideCharacterSet = None,
                ReloadF            = False):
        """Provide a map which associates intervals with line/column counting 
        actions as well as appropriate increments of the input pointer.

           map: 
                interval --> (count line/column, increment input_p)

        The mapping is provided in the form of a transition map, i.e.  a list of
        sorted pairs of (interval, action).

        ARGUMENTS: 

          IteratorName       -- name of the input pointer variable.

          InsideCharacterSet -- Set of characters which are subject to counting.
                                That is, all other characters are not considered
                                to 'stop the show'.

          ReloadF            -- If 'True' reload may occur during counting. 
                                Else not.

        RETURNS:

           [0] Counter Map in UNICODE 
               (not in Setup.buffer_codec_transformation_info)

           [1] Implementation Type to be used 
               (STATE_MACHINE, STATE_MACHINE_TRIVIAL, PLAIN_MAP).

           [2], [3] Entry and exit action before counting and after counting ends.
           
           [4], [5] Before and after reload actions.

        The counter map contains special actions:
           
           -- 'E_ActionIDs.ON_EXIT' indicating that as a consequence of this
              action the counting loop needs to be exited.
           -- 'E_ActionIDs.ON_GOOD_TRANSITION' indicating that this action
              must result in staying inside the counting loop.

        ___________________________________________________________________________
        REFERENCE POINTER COUNTING

        Using a reference pointer counting can be optimized. It is applied in
        case that there is only one single value for column counts.  Consider
        the figure below:

              ---- memory address --->
                                             later
                                             iterator
                                                 |
              | | | | | | |*| | | | | | | | | | | | | | | | | | | | | |
                           |
                      reference_p 
                      = iterator

        The '*' stands for a 'grid' or a 'newline' character.  If such a character
        appears, the 'reference_p' is set to the current 'iterator'.  As long as no
        such character appears, the term to be added is proportional to 'iterator -
        reference_p'.  The counter implementation profits from this.  It does not
        increment the 'column_n' as long as only 'normal' characters appear.  It
        only adds the delta multiplied with a constant.

        The implementation of this mechanism is implemented by the functions
        '__special()', '__grid()', and '__newline()'.  It is controlled there by
        argument 'ColumnCountPerChunk'.  If it is not None, it happens to be the
        factor 'C' for the addition of 'C * (iterator - reference_p)'.
        ___________________________________________________________________________
        """
        assert type(ReloadF) == bool
        assert InsideCharacterSet is None or isinstance(InsideCharacterSet, NumberSet)
        LanguageDB = Setup.language_db

        if InsideCharacterSet is not None:
            if ReloadF:
                blc_set    = NumberSet(Setup.buffer_limit_code)
                inside_set = InsideCharacterSet.clone()
                inside_set.subtract(blc_set)
            else:
                inside_set = InsideCharacterSet
            exit_set = inside_set.inverse()
            exit_set.subtract(blc_set)
        else:
            inside_set = None # That is: All!
            exit_set   = None # That is: Empty!

        counter_dictionary     = self.get_counter_dictionary(inside_set)
        column_count_per_chunk = self.get_column_number_per_chunk(inside_set)

        cm = TransitionMap()
        for number_set, action in counter_dictionary:
            assert inside_set is None or inside_set.is_superset(number_set)
            action_txt = action.get_txt(column_count_per_chunk, IteratorName)
            cm.extend((x, action_txt) for x in number_set.get_intervals())

        implementation_type = LoopGenerator.determine_implementation_type(cm, ReloadF)

        cm.add_action_to_all(CountAction.get_epilog(implementation_type))

        exit_action_txt = ExitAction.get_txt(column_count_per_chunk, IteratorName)
        exit_action_txt.extend(ExitAction.get_epilog(implementation_type))
        if exit_set is not None:
            cm.extend((x, exit_action_txt) for x in exit_set.get_intervals())

        cm.clean_up()

        # Upon reload, the reference pointer may have to be added. When the reload is
        # done the reference pointer needs to be reset. 
        entry_action = []
        exit_action  = []
        if not ReloadF:
            before_reload_action = None
            after_reload_action  = None
            if column_count_per_chunk is not None:
                LanguageDB.REFERENCE_P_RESET(entry_action, IteratorName, AddOneF=False)
                LanguageDB.REFERENCE_P_COLUMN_ADD(exit_action, IteratorName, column_count_per_chunk)
        else:
            before_reload_action = []
            after_reload_action  = []
            if column_count_per_chunk is not None:
                LanguageDB.REFERENCE_P_RESET(entry_action, IteratorName, AddOneF=False)
                LanguageDB.REFERENCE_P_COLUMN_ADD(exit_action, IteratorName, column_count_per_chunk)
                LanguageDB.REFERENCE_P_COLUMN_ADD(before_reload_action, IteratorName, column_count_per_chunk)
                LanguageDB.REFERENCE_P_RESET(after_reload_action, IteratorName, AddOneF=False)

        if column_count_per_chunk is not None:
            variable_db.require("reference_p")

        return cm, implementation_type, entry_action, exit_action, before_reload_action, after_reload_action

class CountAction:
    __slots__ = ("value")
    def __init__(self, Value):
        self.value = Value

    @staticmethod
    def get_epilog(ImplementationType):
        return [ E_ActionIDs.ON_GOOD_TRANSITION ]

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
        return [ E_ActionIDs.ON_EXIT ]

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

