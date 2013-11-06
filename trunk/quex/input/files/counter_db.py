from   quex.engine.state_machine.transformation     import homogeneous_chunk_n_per_character
from   quex.engine.interval_handling                import NumberSet
from   quex.engine.analyzer.transition_map          import TransitionMap
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.blackboard import setup as Setup, \
                              E_IncidenceIDs

from   collections import namedtuple

CountCmdInfo = namedtuple("CountCmdInfo_tuple", ("trigger_set", "command_list"))

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

    def get_map(self, X, Y, Z):
        assert False, "call get_count_command_map"

    def get_count_command_map(self, CharacterSet = None):
        """Provide a map which associates intervals with line/column counting 
        actions as well as appropriate increments of the input pointer.

           map: 
                            interval --> CommandList

        The mapping is provided in the form of a list, where the intervals in
        the list are NOT NECESSARILY ADJACENT!
        sorted pairs of (interval, action).

        ARGUMENTS:
                  CharacterSet -- Considered set of characters.

        The intervals of the result list will constitute of the intervals 
        of the given CharacterSet. If the CharacterSet is None then the
        whole range of characters is considered.

        RETURNS:  [0] list( (interval, CommandList) )
                  [1] ColumnNPerChunk

        Where the ColumnNPerChunk is not None, if and only if the column number
        increment can be computed by "(input_p - reference_p) * C". That is
        all column related characters have the same horizontal size.

        ___________________________________________________________________________
        REFERENCE POINTER COUNTING

        Counting by means of a reference pointer may spare intermediate column
        number increments. Instead, one only needs to do

                column_n += (input_p - reference_p) * C

        as soon as a 'non-column character' occurs. Consider the figure below:

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
        ___________________________________________________________________________
        """
        assert CharacterSet is None or isinstance(CharacterSet, NumberSet)
        LanguageDB = Setup.language_db

        column_count_per_chunk = self.get_column_number_per_chunk(CharacterSet)
        counter_dictionary     = self.get_counter_dictionary(CharacterSet, column_count_per_chunk)

        cm = TransitionMap()
        for number_set, command_list in counter_dictionary:
            assert CharacterSet is None or CharacterSet.is_superset(number_set)
            cm.extend((interval, command_list) for interval in number_set.get_intervals())

        return cm, column_count_per_chunk

class CounterCoderData:
    def __init__(self, CounterDb, CharacterSet, IteratorName=LanguageDB.INPUT_P):
        assert not CharacterSet.is_empty()
        assert isinstance(CharacterSet, NumberSet)
        assert isinstance(CounterDb, CounterDB)

        # If 'column_count_per_chunk' is not None, then reference positions may 
        # be used for counting (i.e. "column_n += (input_p - reference_p) * C").
        # This avoids 'column_n += C' at every single step.
        self.column_count_per_chunk = CounterDb.get_column_number_per_chunk(CharacterSet)
        self.iterator_name          = IteratorName

        # count_command_map:
        #
        #               map:  CLI -->  (NumberSet, CommandList)
        #
        # where the CommandList does the required column/line number counting 
        # for the given NumberSet. The tuple (NumberSet, CommandList) is
        # implemented as CountCmdInfo.
        self.count_command_map = self.__count_command_map_prepare(CounterDb, 
                                                                  CharacterSet) 

    def get_entry_exit_commands(self):
        """Actions to be performed at entry into the counting code fragment and 
        when exiting.

        RETURNS:

            [0], [1]    Commands to be executed [0] upon entry, i.e. when the 
                        counting starts, and [1] upon counting is terminated.

            None, None  If there is no need to do anthing upon entry or exit.
        """
        if ColumnCountPerChunk is None:
            return None, None
        else:
            on_entry = ColumnCountReferencePSet(self.iterator_name)
            on_exit  = ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                                     self.column_count_per_chunk)
            return on_entry, on_exit
        

    def get_before_after_reload_commands(self, ReloadF, LexemeF=True):
        """Actions to be performed before and after reload.

        RETURNS: 
        
            [0], [1]    Commands to be executed before and after buffer reload. 
                        This basically adapts the reference pointer for column 
                        number counting. 
                     
            None, None  If column number counting cannot profit from the a fixed
                        ColumnCountPerChunk (applying "column += (p-reference_p)*c")

        For convienience, to spare the caller an "if ReloadF: ..." this function
        takes the ReloadF and returns "None, None" if it is false.

        The LexemeF tells whether the current lexeme is important, i.e. treated
        by some handler. If not, the how buffer may be reloaded by setting the 
        lexeme start pointer to the input pointer.
        """
        if ReloadF == False or ColumnCountPerChunk is None:
            return None, None
        else:
            on_before_reload = ColumnCountReferencePDeltaAdd(self.iterator_name, 
                                                             self.column_count_per_chunk)
            on_after_reload  = ColumnCountReferencePSet(self.iterator_name)

        if not LexemeF:
            # The lexeme start pointer defines the lower border of memory to be 
            # kept when reloading. Setting it to the input pointer allows for 
            # the whole buffer to be reloaded. THIS CAN ONLY BE DONE IF THE 
            # LEXEME IS NOT IMPORTANT!
            on_before_reload.append(LexemeStartToReferenceP(self.iterator_name))

        return on_before_reload, on_after_reload

    def __count_command_map_prepare(self, CounterDb, CharacterSet):
        """Returns a list of NumberSet objects where for each X of the list it holds:

             (i)  X is subset of CharacterSet
                   
             (ii) It is related to a different counter action than Y,
                  for each other object Y in the list.

           RETURNS: 

                        map:  CLI -->  (NumberSet, CommandList)

           NOTE: A 'CLI' is UNIQUE also as a state index. That is, it can be 
                 used a a 'pseudo state' which represents the CommandList
                 without extra effort.

           where each entry means: "If an input character lies in NumberSet
           then the counting action given by CommandList has to be executed.
           The CommandList is distinctly associated with a CLI, a command
           list index.
        """
        def pruned_iteritems(Db, CharacterSet):
            for value, character_set in Db.iteritems():
                if CharacterSet is None: pruned = X
                else:                    pruned = X.intersection(CharacterSet)
                if pruned.is_empty():    continue
                yield value, pruned

        def on_special(Delta):
            if self.column_count_per_chunk is None:  return ColumnCountAdd(Delta)
            else:                                    return None

        def on_grid(GridStepN):
            if self.column_count_per_chunk is None:  return ColumnCountGridAdd(grid_step_n)
            else:                                    return ColumnCountGridAddWithReferenceP(grid_step_n, 
                                                                                             self.iterator_name)

        def on_newline(Delta):
            if self.column_count_per_chunk is None: return LineCountAdd(delta)
            else:                                   return LineCountAddWithReferenceP(delta, 
                                                                                      self.iterator_name)

        result = {}
        result.update(
            (index.get(), CountCmdInfo(character_set, CommandList(on_special(delta))))
            for delta, character_set in pruned_iteritems(CounterDb.special, CharacterSet)
        )
        result.update(
            (index.get(), CountCmdInfo(character_set, CommandList(on_grid(grid_step_n))))
            for grid_step_n, character_set in pruned_iteritems(CounterDb.grid, CharacterSet)
        )
        result.update(
            (index.get(), CountCmdInfo(character_set, CommandList(on_newline(delta))))
            for delta, character_set in pruned_iteritems(CounterDb.newline, CharacterSet)
        )

        return result

