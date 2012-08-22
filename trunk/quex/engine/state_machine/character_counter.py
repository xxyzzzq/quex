# (C) 2012 Frank-Rene Schaefer
from quex.engine.misc.tree_walker  import TreeWalker
from quex.blackboard               import E_Count

def do(SM, CounterDB, BeginOfLineF=False):
    """LINE AND COLUMN NUMBER ANALYSIS ________________________________________
    
    Given a pattern as a state machine 'SM' this function analyses the 
    increments of line and column numbers. Depending on whether those 
    values can be determined from the state machine or only during run-
    time, a CountInfo object is provided that provides basic information:

      .line_n_increment   
        
         The number of lines that appear in the pattern.
         
         E_Count.VOID => cannot be determined from the pattern off-line.

      .line_n_increment_by_lexeme_length 

         If the line number increment is proportional to the length of the
         lexeme which is matched, then this variable contains the factor. 
         
         E_Count.VOID => lexeme length not proportional to line_n_increment.

      .column_index
      
         If the column index after match has a specific value, then this 
         member variable contains its value. If it has not, it contains
         E_Count.VOID.

         (This makes sense for pattern that have a 'begin-of-line' pre-
         context. Or, when it contains a newline such as "\\notto".)

      .column_n_increment 
      
         The number of columns that appear in the pattern It is E_Count.VOID if
         it cannot be determined from the pattern off-line.

      .column_n_increment_by_lexeme_length 

         If the column number increment is proportional to the length of the
         lexeme which is matched, then this variable contains the factor. It
         is E_Count.VOID if there is no relation between lexeme length and
         column number increment.

    NOTES _____________________________________________________________________

    State machine shall not contain pre- or post-contexts.
    
    DEPENDS ON: CounterDB providing three databases:

                .newline
                .grid
                .special 

    RESTRICTION _______________________________________________________________

    * The current approach does consider the column count to be void as soon  *
    * as a state is reached with two different column counts.                 *

    Disadvantage:

    Sub-optimal results for a very restricted amount of patterns.  In these
    cases, a 'count' is implemented where a plain addition or setting would be
    sufficient.

    Sub-Optimal Scenario:
    
    If there is more than one path to one node in the state machine with
    different column counts AND after that node there comes a newline from
    whereon the pattern behaves 'deterministic'.

    Reason for restriction left in place:

    To fix this, another approach would have to be implemented where the state
    machine is inverted and then the column counts starts from rear to front
    until the first newline. This tremendous computation time overhead is shied
    away from, because of the aforementioned low expected value add.

    ___________________________________________________________________________
    """
    counter = CharacterCountTracer(SM)
    state   = SM.get_init_state()
    count   = Count(0, 0, ColumnIndex = 0 if BeginOfLineF else E_Count.VOID)
    # Next Node: [0] state index of target state
    #            [1] character set that triggers to it
    #            [2] count information
    initial = [ (state_index, character_set, count.clone()) \
                for state_index, character_set in state.transitions().get_map().iteritems() ]

    Count.init(CounterDB)
    counter.do(initial)

    # (*) Determine detailed count information
    grid = Count.grid
    if counter.abort_f and grid == E_Count.NONE:
        # If the count procedure was aborted, possibly NOT all character
        # transitions have been investigated. So the value for 'grid' must
        # determined now, independently of the 'counter.do()'.
        grid = _determine_grid_parameter(SM, CounterDB)

    return CountInfo(counter.result.line_n_increment, 
                     counter.result.column_n_increment, 
                     grid, 
                     Count.column_n_increment_by_lexeme_length,
                     Count.line_n_increment_by_lexeme_length)

def _determine_grid_parameter(SM, CounterDB):
    """The CharacterCountTracer has been aborted (which is a good thing). Now,
    the grid information has to be determined extra. As mentioned in the calling
    function 'grid' can have the following three values:

      N > 0,        if ONLY grid characters of size 'N' are involved.
            
      E_Count.NONE, if no grid character is involved.

      E_Count.VOID, if some grid characters are involved, but increase of 
                    column_n_increment must be determined at run-time.
    """
    prototype = E_Count.VIRGIN
    for state in SM.states.itervalues():
        for character_set in state.transitions().get_map().itervalues():
            for grid_size, grid_character_set in CounterDB.grid.iteritems():
                x = grid_character_set.get_relation(character_set)
                if   x == NumberSet.DISJOINT:     
                    continue
                elif x == NumberSet.SUPERSET:
                    # All characters of the transition are in 'grid_character_set'
                    if   prototype == E_Count.VIRGIN: prototype = grid_size
                    elif prototype != grid_size:      return E_Count.VOID
                else:
                    # Some characters are form 'grid_character_set' others not.
                    return E_Count.VOID

    return prototype

class CharacterCountTracer(TreeWalker):
    """________________________________________________________________________
    
    Recursive Algorithm to count the number of newlines, characters, or spaces
    for each state in the state machine. It is done for each state, so that 
    path walking can be aborted as soon as a known state is hit.

     -- A loop makes a count either (i) void if the counted character appears, 
        or (ii) is unimportant. If (i) happens, then the counter is globally
        void. In case of (ii) no change happened so any analysis starting from
        the loop's knot point is still valid and does not have to be made 
        again.

     -- A node is met through another path. Exactly the same consideration as
        for loops holds again. The break-up here is also essential to avoid
        exponential time (The total number of paths multiplies with the number
        of branches through each knot on the path).

    ONLY PATTERNS WITHOUT PRE- AND POST-CONTEXT ARE HANDLED HERE!
    ___________________________________________________________________________
    """   
    def __init__(self, SM):  
        self.sm       = SM
        self.depth    = 0
        self.result   = Count(E_Count.VIRGIN, E_Count.VIRGIN)
        self.known_db = {}  # state_index --> count
        TreeWalker.__init__(self)

    def on_enter(self, Info):  
        """Info = (state_index of what is entered, character set that triggers to it)"""
        StateIndex, CharacterSet, count = Info

        if not count.compute(CharacterSet):
            self.result.line_n_increment   = E_Count.VOID
            self.result.column_n_increment = E_Count.VOID
            self.abort_f = True
            return None

        state = self.sm.states[StateIndex]
        known = self.known_db.get(StateIndex)
        if known is not None:
            if known.column_n_increment != count.column_n_increment: self.result.column_n_increment = E_Count.VOID
            if known.line_n_increment   != count.line_n_increment:   self.result.line_n_increment   = E_Count.VOID

            if self.result.line_n_increment == E_Count.VOID and self.result.column_n_increment == E_Count.VOID: 
                self.abort_f = True

            # Rest of paths starting from this state has been walked along before
            subsequent = None
        else:
            known                     = Count(count.column_n_increment, count.line_n_increment)
            self.known_db[StateIndex] = known

            subsequent = [ (state_index, character_set, count.clone()) \
                           for state_index, character_set in state.transitions().get_map().iteritems() ]

        if state.is_acceptance():
            if   self.result.column_n_increment == E_Count.VIRGIN:           self.result.column_n_increment = known.column_n_increment
            elif self.result.column_n_increment != known.column_n_increment: self.result.column_n_increment = E_Count.VOID
            if   self.result.line_n_increment == E_Count.VIRGIN:             self.result.line_n_increment = known.line_n_increment
            elif self.result.line_n_increment != known.line_n_increment:     self.result.line_n_increment = E_Count.VOID

            if self.result.line_n_increment == E_Count.VOID and self.result.column_n_increment == E_Count.VOID: 
                self.abort_f = True

        return subsequent

    def on_finished(self, node):   
        pass

class Count(object):
    """________________________________________________________________________

    Contains increment of line and column number of a pattern as soon as one
    particular state has been reached.
    ___________________________________________________________________________
    """
    __slots__ = ('column_n_increment', 'line_n_increment', 'column_index')

    # (*) Increment per step:
    #
    #     If the increment per step is the same 'C' for any character that appears 
    #     in the pattern, then the length of the pattern can be computed at run-
    #     time by a simple subtraction:
    # 
    #               length = (LexemeEnd - LexemeBegin) * C
    #
    #     provided that there is no newline in the pattern this is at the same 
    #     time the column increment. Same holds for line number increments.
    column_n_increment_by_lexeme_length = E_Count.VIRGIN
    # Just for info, in Unicode there are the following candidates which may possibly
    # have assigned a separate line number increment: Line Feed, 0x0A; Vertical Tab, 0x0B; 
    # Form Feed, 0x0C; Carriage Return, 0x0D; Next Line, 0x85; Line Separator, 0x28; 
    # Paragraph Separator, 0x2029; 
    line_n_increment_by_lexeme_length   = E_Count.VIRGIN
    grid                                = E_Count.NONE

    # Line/Column count information
    counter_db                          = None

    @staticmethod
    def init(CounterDB):
        """Initialize global objects in namespace 'Count'."""
        Count.column_n_increment_by_lexeme_length = E_Count.VIRGIN
        Count.line_n_increment_by_lexeme_length   = E_Count.VIRGIN
        Count.grid                                = E_Count.NONE
        Count.counter_db                          = CounterDB

    def __init__(self, ColumnN, LineN, ColumnIndex=E_Count.VOID):
        self.line_n_increment   = LineN
        self.column_n_increment = ColumnN
        self.column_index       = ColumnIndex

    def clone(self):
        return Count(self.column_n_increment, self.line_n_increment, self.column_index)

    def compute(self, CharacterSet):
        """Compute the increase of line and column numbers due to the given
        character set. If both, increase of line and column number, are  
        not distinctly determinable by the character set then the 'abort_f' is 
        raised.
        """
        for delta_line_n, character_set in Count.counter_db.newline.iteritems():

            if character_set.is_superset(CharacterSet):
                Count.announce_line_n_per_step(delta_line_n)
                if isinstance(delta_line_n, (str, unicode)):
                    self.line_n_increment   += delta_line_n
                    self.column_n_increment  = E_Count.VIRGIN
                    self.column_index        = 0
                else:
                    self.line_n_increment   = E_Count.VOID
                    self.column_n_increment = E_Count.VIRGIN
                    self.column_index       = 0
                return True  # 'CharacterSet' does not contain anything beyond 'character_set'

            elif not character_set.has_intersection(CharacterSet):
                continue

            else:
                # Some characters are from 'character_set', others not => VOID.
                self.line_n_increment   = E_Count.VOID   
                self.column_n_increment = E_Count.VOID  
                self.column_index       = E_Count.VOID  
                return False # Abort


        if self.column_n_increment != E_Count.VOID:
            for grid_size, character_set in Count.counter_db.grid.iteritems():
                if character_set.is_superset(CharacterSet):
                    Count.announce_grid_size(grid_size)
                    if self.column_index != E_Count.VOID and isinstance(grid_size, (int, long)): 
                        self.column_index += grid_size - (self.column_i % grid_size)
                        self.column_n_increment = self.column_index
                        return True
                    else:
                        self.column_n_increment = E_Count.VOID
                        return self.line_n_increment is not E_Count.VOID # Abort, if line_n_increment is also void.

                elif not character_set.has_intersection(CharacterSet):
                    continue

                else:
                    self.column_n_increment = E_Count.VOID

        # Still, 'self.column_n_increment != E_Count.VOID'. Otherwise, 'return' was triggered.
        for delta_column_n, character_set in Count.counter_db.special.iteritems():
            if character_set.is_superset(CharacterSet):
                Count.announce_column_n_per_step(delta_column_n)

                if x == True and Count.grid == E_Count.VIRGIN:
                    self.column_n_increment += delta_column_n
                    return True
                else:
                    # Same transition with characters of different horizonzal size.
                    # => delta column_n_increment = VOID
                    self.column_n_increment = E_Count.VOID
                    return self.line_n_increment is not E_Count.VOID # Abort, if line_n_increment is also void.

            elif not character_set.has_intersection(CharacterSet):
                continue

            else:
                self.column_n_increment = E_Count.VOID

        return True # Do not abort, yet

    @staticmethod
    def announce_column_n_per_step(DeltaLineN):
        if  Count.grid != E_Count.VIRGIN: 
            # A column_n_increment step makes the grid steps automaticall inhomogeneous, 
            # and vice versa.
            Count.grid                        = E_Count.VOID
            Count.column_n_increment_by_lexeme_length = E_Count.VOID

        elif Count.column_n_increment_by_lexeme_length == E_Count.VOID:   
            return # Has been 'voided' before. 

        elif Count.column_n_increment_by_lexeme_length == E_Count.VIRGIN: 
            Count.column_n_increment_by_lexeme_length = DeltaLineN

        elif Count.column_n_increment_by_lexeme_length != DeltaLineN:     
            # If a different column_n_increment step appeared before, then things are void.
            Count.column_n_increment_by_lexeme_length = E_Count.VOID

        else:                                                   
            return # .column_n_increment_by_lexeme_length remains '== 'DeltaLineN'

    @staticmethod
    def announce_grid_size(GridSize):
        if Count.column_n_increment_by_lexeme_length != E_Count.VIRGIN: 
            # A column_n_increment step makes the grid steps automatically inhomogeneous, 
            # and vice versa.
            Count.grid                        = E_Count.VOID
            Count.column_n_increment_by_lexeme_length = E_Count.VOID

        elif Count.grid == E_Count.VOID:   
            return # Has been 'voided' before. 

        elif Count.grid == E_Count.VIRGIN: 
            Count.grid = GridSize

        elif Count.grid != GridSize:     
            # If a different column_n_increment step appeared before, then things are void.
            Count.grid = E_Count.VOID

        else:                                                   
            return # .grid remains '== GridSize'

    @staticmethod
    def announce_line_n_per_step(DeltaLineN):
        if   Count.line_n_increment_by_lexeme_length == E_Count.VOID:
            return # Has been 'voided' before.
        
        elif Count.line_n_increment_by_lexeme_length == E_Count.VIRGIN: 
            Count.line_n_increment_by_lexeme_length = DeltaLineN

        elif Count.line_n_increment_by_lexeme_length != DeltaLineN:   
            Count.line_n_increment_by_lexeme_length = E_Count.VOID
        else:
            return # .line_n_increment_by_lexeme_length remains '== DeltaLineN'


class CountInfo(object):
    __slots__ = ("line_n_increment", "column_n_increment", "grid", 
                 "increment_line_n_per_char", "increment_column_n_per_char")

    def __init__(self, LineN, ColumnN, Grid, \
                 IncrementColumnN_PerChar, IncrementLineN_PerChar):
        self.line_n_increment   = LineN
        self.column_n_increment = ColumnN
        self.grid               = Grid
        self.increment_column_n_per_char = IncrementColumnN_PerChar
        self.increment_line_n_per_char   = IncrementLineN_PerChar

        if self.increment_line_n_per_char == E_Count.VIRGIN:
            if isinstance(self.grid, (int, long)):
                self.increment_column_n_per_char = Count.grid
                self.grid                        = E_Count.NONE
            else:
                self.increment_column_n_per_char = 0

    def is_determined(self):
        # Note, that 'grid' only tells about grid sizes being homogeneous.
        return self.line_n_increment != E_Count.VOID and self.column_n_increment != E_Count.VOID

    def has_grid(self):
        return self.grid != E_Count.VIRGIN

    def column_n_proportional_to_lexeme_length(self):
        return     self.column_n_increment_by_lexeme_length != E_Count.VOID \
               and self.column_n_increment                  == E_Count.VOID

    def line_n_proportional_to_lexeme_length(self):
        return     self.line_n_increment_by_lexeme_length != E_Count.VOID \
               and self.line_n_increment                  == E_Count.VOID

