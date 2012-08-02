# (C) 2012 Frank-Rene Schaefer
from quex.engine.misc.tree_walker  import TreeWalker
from quex.blackboard               import E_Count

def do(SM, CounterDB):
    """LINE AND COLUMN NUMBER PRE-DETERMINATION _______________________________
    
    Count line and column number, if possible, from the structure of the state
    machine 'SM' that represents the pattern.

    RETURN: [0] newline_n -- Number of newlines in any lexeme matching 'SM'.

            [1] column_n  -- Number of columns in any lexeme matching 'SM'.

            [2] grid      -- N > 0,  if ONLY grid characters of size 'N' are
                                     involved.
            
                             E_Count.NONE,   

                             if no grid character is involved.

                             E_Count.VOID,

                             if some grid characters are involved, but increase 
                             of column_n must be determined at run-time.

    If [0] or [1] is 'E_Count.VOID', then the its value depends on the matched
    lexeme. Then, the pattern itself does not directly allow to determine its 
    value.

    NOTES _____________________________________________________________________

    State machine shall not contain pre- or post-contexts.
    
    DEPENDS ON: CounterDB providing three databases:

                .newline
                .grid
                .special 

    SHORTCOMING _______________________________________________________________

    The current approach does consider the column count to be void as soon
    as a state is reached with two different column counts. This is too rigid
    in a sense that a newline may clear the column count later in the pattern.
    If the column counts to the acceptance state are then equal from there on,
    the column count could be a numeric constant.

    Practically, this means that Quex will implement a column counter in some
    special cases where a pattern contains a newline, where a fixed constant
    could be added instead. Multi-line patterns are considered to be rare and
    the overhead of counting from the end of the lexeme to the last newline 
    is considered to be minimal. There is no significant performance decrease
    expected from this shortcoming.

    To fix this, another approach would have to be implemented where the state
    machine is inverted and then the column counts starts from rear to front
    until the first newline. This tremendous computation time overhead is shied
    away from, because of the aforementioned low expected value add.
    ___________________________________________________________________________
    """
    ## if not CounterDB.is_enabled(): 
    ##    return E_Count.VOID, E_Count.VOID

    Count.init(CounterDB)

    counter = CharacterCountTracer(SM)
    state   = SM.get_init_state()
    count   = Count(0, 0)
    # Next Node: [0] state index of target state
    #            [1] character set that triggers to it
    #            [2] count information
    initial = [ (state_index, character_set, count.clone()) \
                for state_index, character_set in state.transitions().get_map().iteritems() ]
    counter.do(initial)

    # (*) Determine detailed count information
    grid = Count.grid
    if counter.abort_f and grid == E_Count.NONE:
        # If the count procedure was aborted, possibly NOT all character
        # transitions have been investigated. So the value for 'grid' must
        # determined now, independently of the 'counter.do()'.
        grid = _determine_grid_parameter(SM, CounterDB)

    return CountInfo(counter.result.line_n, counter.result.column_n, \
                     grid, \
                     Count.column_increment_per_step,
                     Count.line_increment_per_step)

class CountInfo(object):
    __slots__ = ("line_n", "column_n", "grid", 
                 "increment_line_n_per_char", "increment_column_n_per_char")

    def __init__(self, LineN, ColumnN, Grid, \
                 IncrementColumnN_PerChar, IncrementLineN_PerChar):
        self.line_n   = LineN
        self.column_n = ColumnN
        self.grid     = Grid
        self.increment_column_n_per_char = IncrementColumnN_PerChar
        self.increment_line_n_per_char   = IncrementLineN_PerChar

        if self.increment_line_n_per_char == E_Count.VIRGIN:
            if isinstance(self.grid, (int, long)):
                self.increment_column_n_per_char = Count.grid
                self.grid                        = E_Count.NONE
            else:
                self.increment_column_n_per_char = 0

def _determine_grid_parameter(SM, CounterDB):
    """The CharacterCountTracer has been aborted (which is a good thing). Now,
    the grid information has to be determined extra. As mentioned in the calling
    function 'grid' can have the following three values:

      N > 0,        if ONLY grid characters of size 'N' are involved.
            
      E_Count.NONE, if no grid character is involved.

      E_Count.VOID, if some grid characters are involved, but increase of 
                    column_n must be determined at run-time.
    """
    prototype = E_Count.NONE
    for state in SM.states.itervalues():
        for character_set in state.transitions().get_map().itervalues():
            for grid_size, grid_character_set in CounterDB.grid.iteritems():
                x = _check_set(grid_character_set, character_set)
                if x == False:           # Grid does not appear.
                    continue
                if x is None:            # Grid appears, but also others.
                    return E_Count.VOID
                elif x == True:          # Only 'Grid' appears.
                    if   prototype is E_Count.NONE: prototype = grid_size
                    elif prototype != grid_size:    return E_Count.VOID

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
            self.result.line_n   = E_Count.VOID
            self.result.column_n = E_Count.VOID
            self.abort_f = True
            return None

        state = self.sm.states[StateIndex]
        known = self.known_db.get(StateIndex)
        if known is not None:
            if known.column_n != count.column_n: self.result.column_n = E_Count.VOID
            if known.line_n   != count.line_n:   self.result.line_n   = E_Count.VOID

            if self.result.line_n == E_Count.VOID and self.result.column_n == E_Count.VOID: 
                self.abort_f = True

            # Rest of paths starting from this state has been walked along before
            subsequent = None
        else:
            known = Count(count.column_n, count.line_n)
            self.known_db[StateIndex] = known

            subsequent = [ (state_index, character_set, count.clone()) \
                           for state_index, character_set in state.transitions().get_map().iteritems() ]

        if state.is_acceptance():
            if   self.result.column_n == E_Count.VIRGIN: self.result.column_n = known.column_n
            elif self.result.column_n != known.column_n: self.result.column_n = E_Count.VOID
            if   self.result.line_n == E_Count.VIRGIN:   self.result.line_n = known.line_n
            elif self.result.line_n != known.line_n:     self.result.line_n = E_Count.VOID

            if self.result.line_n == E_Count.VOID and self.result.column_n == E_Count.VOID: 
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
    __slots__ = ('column_n', 'line_n')

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
    column_increment_per_step = E_Count.VIRGIN
    # Just for info, in Unicode there are the following candidates which may possibly
    # have assigned a separate line number increment: Line Feed, 0x0A; Vertical Tab, 0x0B; 
    # Form Feed, 0x0C; Carriage Return, 0x0D; Next Line, 0x85; Line Separator, 0x28; 
    # Paragraph Separator, 0x2029; 
    line_increment_per_step   = E_Count.VIRGIN
    grid                      = E_Count.NONE

    # Line/Column count information
    counter_db                = None

    @staticmethod
    def init(CounterDB):
        """Initialize global objects in namespace 'Count'."""
        Count.column_increment_per_step = E_Count.VIRGIN
        Count.line_increment_per_step   = E_Count.VIRGIN
        Count.grid                      = E_Count.NONE
        Count.counter_db                = CounterDB

    def __init__(self, ColumnN, LineN):
        self.column_n = ColumnN
        self.line_n   = LineN

    def clone(self):
        return Count(self.column_n, self.line_n)

    def compute(self, CharacterSet):
        """Compute the increase of line and column numbers due to the given
        character set. If both, increase of line and column number, are void 
        not distinctly determinable to the character set then the 'abort_f' is 
        raised.
        """

        for delta_line_n, character_set in Count.counter_db.newline.iteritems():
            x = _check_set(character_set, CharacterSet)
            if x == False: continue
            Count.announce_line_n_per_step(delta_line_n)

            if x == True:
                self.line_n   += delta_line_n
                self.column_n  = 0
                return True  # 'CharacterSet' does not contain anything beyond 'character_set'
            else:
                self.line_n   = E_Count.VOID  # Newline together with other characters in one
                self.column_n = E_Count.VOID  # transition. => delta line, delta column = void.
                return False # Abort

        for grid_size, character_set in Count.counter_db.grid.iteritems():
            x = _check_set(character_set, CharacterSet)
            if x == False: continue
            Count.announce_grid_size(grid_size)
            Count.contains_grid_f = True

            if x == True:
                self.column_n = (self.column_n // grid_size + 1) * grid_size
                return True
            else:
                # Same transition with characters of different horizonzal size.
                # => delta column_n = VOID
                self.column_n = E_Count.VOID
                return self.line_n is not E_Count.VOID # Abort, if line_n is also void.

        for delta_column_n, character_set in Count.counter_db.special.iteritems():
            x = _check_set(character_set, CharacterSet)
            if x == False: continue
            Count.announce_column_n_per_step(delta_column_n)

            if x == True:
                self.column_n += delta_column_n
                return True
            else:
                # Same transition with characters of different horizonzal size.
                # => delta column_n = VOID
                self.column_n = E_Count.VOID
                return self.line_n is not E_Count.VOID # Abort, if line_n is also void.

        if   self.column_n == E_Count.VIRGIN: 
            self.column_n = 1
        elif self.column_n != E_Count.VOID:                               
            self.column_n += 1
            Count.announce_column_n_per_step(1)
        
        return True # Do not abort, yet

    @staticmethod
    def announce_grid_size(GridSize):
        if   Count.grid == E_Count.NONE: Count.grid = GridSize
        elif Count.grid != GridSize:     Count.grid = E_Count.VOID
        else:                            pass # Count.grid remains 'GridSize'

    @staticmethod
    def announce_line_n_per_step(DeltaLineN):
        if Count.line_increment_per_step == E_Count.VIRGIN: 
            Count.line_increment_per_step = DeltaLineN
        elif Count.line_increment_per_step != DeltaLineN:   
            Count.line_increment_per_step = E_Count.VOID

    @staticmethod
    def announce_column_n_per_step(DeltaLineN):
        if Count.column_increment_per_step == E_Count.VIRGIN: 
            Count.column_increment_per_step = DeltaLineN
        elif Count.column_increment_per_step != DeltaLineN:   
            Count.column_increment_per_step = E_Count.VOID

def _check_set(CmpSet, CharacterSet):
    """Compare 'CmpSet' with 'CharacterSet'
    
    RETURNS: True  -- CmpSet covers CharacterSet. 
    
                      All characters in CharacterSet are in CmpSet and
                      CharacterSet does not contain any character beyond.

             False -- CharacterSet does not intersect with CmpSet.

             None  -- CharacterSet has some characters from CmpSet
                      but also others beyond.
    """
    if   CmpSet.is_superset(CharacterSet):      return True
    elif CmpSet.has_intersection(CharacterSet): return None
    else:                                       return False

