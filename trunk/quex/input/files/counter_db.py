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

    def get_counter_dictionary(self, ConcernedCharacterSet, ColumnCountPerChunk, IteratorName):
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
            elif ColumnCountPerChunk is None:
                result.append((x, CommandList(ColumnCountAdd(delta))))
            else:
                result.append((x, CommandList()))

        for grid_step_n, character_set in self.grid.iteritems():
            x = prune(character_set, ConcernedCharacterSet)
            if x.is_empty(): continue
            elif ColumnCountPerChunk is None:
                result.append((x, CommandList(ColumnCountGridAdd(grid_step_n))))
            else:
                result.append((x, CommandList(ColumnCountGridAddWithReferenceP(grid_step_n, IteratorName))))

        for delta, character_set in self.newline.iteritems():
            x = prune(character_set, ConcernedCharacterSet)
            if x.is_empty(): continue
            elif ColumnCountPerChunk is None:
                result.append((x, CommandList(LineCountAdd(delta))))
            else:
                result.append((x, CommandList(LineCountAddWithReferenceP(delta, IteratorName))))

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

    def get_map(self, X, Y, Z):
        assert False, "call get_count_command_map"

    def get_count_command_map(self, IteratorName = None, InsideCharacterSet = None):
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

        RETURN: TransitionMap()


        The transition map may contain intervals with empty 'None' targets. This
        means that there is no action associated with it, due to the fact that
        they are not covered by 'CharacterSet'.
        ___________________________________________________________________________
        """
        assert type(ReloadF) == bool
        assert InsideCharacterSet is None or isinstance(InsideCharacterSet, NumberSet)
        LanguageDB = Setup.language_db

        if InsideCharacterSet is not None:
            inside_set = InsideCharacterSet
            exit_set   = inside_set.inverse()
        else:
            inside_set = None # That is: All!
            exit_set   = None # That is: Empty!

        column_count_per_chunk = self.get_column_number_per_chunk(inside_set)
        counter_dictionary     = self.get_counter_dictionary(inside_set, column_count_per_chunk)

        cm = TransitionMap()
        for number_set, command_list in counter_dictionary:
            assert inside_set is None or inside_set.is_superset(number_set)
            cm.extend((x, command_list) for x in number_set.get_intervals())

        # Gaps are filled with 'None' to indicate that they are outside the CharacterSet
        cm.fill_gaps(None)

        return cm, column_count_per_chunk

    def get_entry_exit_Commands(self, IteratorName, ColumnCountPerChunk):
        """RETURNS:

        [0], [1]    Commands to be executed [0] upon entry, i.e. when the counting
                    starts, and [1] upon counting is terminated.

        None, None  If there is no need to do anthing upon entry or exit.
        """
        if ColumnCountPerChunk is None:
            return None, None
        else:
            on_entry = ColumnCountReferencePSet(IteratorName)
            on_exit  = ColumnCountReferencePDeltaAdd(IteratorName, ColumnCountPerChunk)
            return on_entry, on_exit
        
    def get_reload_Commands(self, IteratorName, ColumnCountPerChunk, ReloadF):
        """RETURNS: 
        
        [0], [1]    Commands to be executed before and after buffer reload. 
                    This basically adapts the reference pointer for column 
                    number counting. 
                 
        None, None  If column number counting cannot profit from the a fixed
                    ColumnCountPerChunk (applying "column += (p-reference_p)*c")

        For convienience, to spare the caller an "if ReloadF: ..." this function
        takes the ReloadF and returns "None, None" if it is false.
        """
        if ReloadF == False or ColumnCountPerChunk is None:
            return None, None
        else:
            on_before_reload = ColumnCountReferencePDeltaAdd(IteratorName, ColumnCountPerChunk)
            on_after_reload  = ColumnCountReferencePSet(IteratorName)
            return on_before_reload, on_after_reload

