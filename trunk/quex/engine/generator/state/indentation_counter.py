from   quex.blackboard                              import setup as Setup, \
                                                           E_StateIndices, \
                                                           E_EngineTypes
import quex.blackboard                              as     blackboard
import quex.engine.state_machine.index              as     sm_index
import quex.engine.analyzer.transition_map          as     transition_map_tools
import quex.engine.generator.state.transition.core  as     transition_block
from   quex.engine.generator.state.transition.code  import TransitionCode
from   quex.engine.generator.languages.variable_db  import Variable
from   quex.engine.generator.languages.address      import get_label, get_address
from   quex.engine.interval_handling                import Interval
from   quex.engine.misc.string_handling             import blue_print
import quex.output.cpp.action_preparation           as     action_preparation

from   math     import log
from   operator import attrgetter
import sys

def do(Data):
    """________________________________________________________________________
    Generate an indentation counter. An indentation counter is entered upon 
    the detection of a newline (which is not followed by a newline suppressor).
    
    Indentation Counter:

    An indentation counter is a single state that iterates to itself as long
    as whitespace occurs. During that iteration the column counter is adapted.
    There are two types of adaption:

       -- 'normal' adaption by a fixed delta. This adaption happens upon
          normal space characters.

       -- 'grid' adaption. When a grid character occurs, the column number
          snaps to a value given by a grid size parameter.

    When a newline occurs the indentation counter exits and restarts the
    lexical analysis. If the newline is not followed by a newline suppressor
    the analyzer will immediately be back to the indentation counter state.
    ___________________________________________________________________________
    """
    LanguageDB = Setup.language_db

    IndentationSetup = Data["indentation_setup"]
    assert IndentationSetup.__class__.__name__ == "IndentationSetup"

    Mode = None
    if IndentationSetup.containing_mode_name() != "":
        Mode = blackboard.mode_db[IndentationSetup.containing_mode_name()]

    counter_index        = sm_index.get()
    
    transition_block_str = __get_transition_block(IndentationSetup, counter_index)

    end_procedure        = __get_end_procedure(IndentationSetup, Mode)

    # The finishing touch
    prolog = blue_print(prolog_txt,
                         [
                           ["$$INPUT_GET$$",     LanguageDB.ACCESS_INPUT()],
                           ["$$INPUT_P_INCREMENT$$",              LanguageDB.INPUT_P_INCREMENT()],
                           ["$$COUNTER_LABEL$$",                  LanguageDB.LABEL(counter_index)], 
                           ["$$COUNTER_ADR$$",                    "%i" % (LanguageDB.ADDRESS(counter_index, None))], 
                         ])

    # The finishing touch
    epilog = blue_print(epilog_txt,
                      [
                       ["$$COUNTER_LABEL$$",                  LanguageDB.LABEL(counter_index)], 
                       ["$$COUNTER_ADR$$",                    "%i" % (LanguageDB.ADDRESS(counter_index, None))], 
                       ["$$IF_INPUT_EQUAL_BUFFER_LIMIT_CODE$$",  LanguageDB.IF_INPUT("==", LanguageDB.BUFFER_LIMIT_CODE)],
                       ["$$RELOAD$$",                         get_label("$reload", counter_index)],
                       ["$$TERMINAL_EOF_ADR$$",               "%i" % (get_address("$terminal-EOF", U=True))],
                       ["$$LEXEME_START_SET_TO_REF$$",        LanguageDB.LEXEME_START_SET("reference_p")],
                       # When things were skipped, no change to acceptance flags or modes has
                       # happend. One can jump immediately to the start without re-entry preparation.
                       ["$$END_PROCEDURE$$",                  "".join(end_procedure)],
                       ["$$REENTRY$$",                        get_label("$start", U=True)],
                       ["$$BAD_CHARACTER_HANDLING$$",         __get_bad_character_handler(Mode, IndentationSetup, counter_index)],
                      ])

    txt = [prolog]
    txt.extend(transition_block_str)
    txt.append(epilog)

    local_variable_db = { "reference_p" : Variable("reference_p", 
                                                   "QUEX_TYPE_CHARACTER_POSITION", None, 
                                                   "(QUEX_TYPE_CHARACTER_POSITION)0x0")
    }

    # Reload requires the state router; mark as 'used'
    get_label("$state-router", U=True)

    return txt, local_variable_db

class IndentationCounter(TransitionCode):
    """________________________________________________________________________
    
    Base class for indentation counter actions which are placed in a transition
    map of a state.

    When counting indentation after newline, a state is implemented that 
    loops to itself until a non-whitespace character occurs. During the
    iteration to itself the indentation is counted. Characters after newline
    may be spaces or tabulators (grid triggers).

                IndentationCounter <---+---- Count_Space
                                       |
                                       +---- Count_Grid
                                       |
                                       '---- Detect_Bad
    
    The two derived classes 'Count_Space' and 'Count_Grid' can implement code
    that increments '_indentation' according to a space or a grid value. The
    derived class 'Detect_Bad' implements code that transits to the 'indentation
    bad' code fragment.
    ___________________________________________________________________________
    """
    def __init__(self, Type, Number, StateIndex):
        self.type        = Type
        self.number      = Number
        self.state_index = StateIndex

    def __ne__(self, Other):
        return not self.__eq__(Other)

    @property
    def drop_out_f(self):
        return False

    def __str__(self):
        return self.code

class Count_Space(IndentationCounter):
    """________________________________________________________________________
    
    Implement the 'space count' action upon the detection of a space character.
    The '_indentation' is incremented by a fixed number.
    ___________________________________________________________________________
    """
    def __init__(self, Number, StateIndex):
        self.number        = Number
        self.state_index   = StateIndex
        self.variable_name = None        # not yet implemented

    def __eq__(self, Other):
        if Other.__class__ != Count_Space: return False
        return self.number == Other.number and self.variable_name == Other.variable_name

    @property
    def code(self):
        """Indentation counters may count as a consequence of a 'triggering'."""
        LanguageDB = Setup.language_db

        # Spaces simply increment
        if self.number != -1: add_str = "%i" % self.number
        else:                 add_str = "me->" + self.variable_name
        return "me->counter._indentation += %s;" % add_str + LanguageDB.GOTO(self.state_index)

class Count_Grid(IndentationCounter):
    """________________________________________________________________________
    
    Implement the 'grid count' action upon the detection of a grid character.
    The '_indentation' is incremented to the next value on a grid.
    ___________________________________________________________________________
    """
    def __init__(self, Number, StateIndex):
        self.number      = Number
        self.state_index = StateIndex
        self.variable_name = None        # not yet implemented

    def __eq__(self, Other):
        if Other.__class__ != Count_Grid: return False
        return self.number == Other.number and self.variable_name == Other.variable_name

    @property
    def code(self):
        """Indentation counters may count as a consequence of a 'triggering'."""
        LanguageDB = Setup.language_db

        if self.number != -1: 
            log2 = log(self.number)/log(2)
            if log2.is_integer():
                # For k = a potentials of 2, the expression 'x - x % k' can be written as: x & ~log2(mask) !
                # Thus: x = x - x % k + k = x & mask + k
                mask = (1 << int(log2)) - 1
                return "me->counter._indentation &= ~ ((QUEX_TYPE_INDENTATION)0x%X);\n" % mask + \
                       "me->counter._indentation += %i;\n" % self.number + \
                       LanguageDB.GOTO(self.state_index)
            else:
                add_str = "%i" % self.number
        else:   
            add_str = "me->" + self.variable_name

        return "me->counter._indentation = (me->counter._indentation - (me->counter._indentation %% %s)) + %s;" \
               % (add_str, add_str) + \
               LanguageDB.GOTO(self.state_index)

class Detect_Bad(IndentationCounter):
    """________________________________________________________________________
    
    Implement the 'transit to bad indentation character' region upon the 
    detection of a grid character. 
    ___________________________________________________________________________
    """
    def __init__(self, StateIndex):
        assert self.state_index != -1
        self.state_index = StateIndex
        
    def __eq__(self, Other):
        if Other.__class__ != Detect_Bad: return False
        return self.state_index == Other.state_index

    @property
    def code(self):
        return "goto INDENTATION_COUNTER_%i_BAD_CHARACTER;\n" % self.state_index


prolog_txt = """
    /* Skip whitespace at line begin; count indentation. */
    reference_p = QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer);
    me->counter._indentation = (QUEX_TYPE_INDENTATION)0;

    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);
    goto _ENTRY_$$COUNTER_ADR$$;

$$COUNTER_LABEL$$
    $$INPUT_P_INCREMENT$$ 
_ENTRY_$$COUNTER_ADR$$:
$$INPUT_GET$$ 
"""

epilog_txt = """
    /* Here's where the first non-whitespace appeared after newline. */
$$END_PROCEDURE$$                           
    /* No need for re-entry preparation. Acceptance flags and modes are untouched. */
    goto $$REENTRY$$;

$$RELOAD$$:
    /* -- In the case of 'indentation counting' we do not worry about the lexeme at all --
     *    HERE, WE DO! We can only set the lexeme start to the current reference_p, i.e.
     *    the point of the last newline!
     *    The appplication might actually do something with indented region.
     *
     * -- The input_p will at this point in time always point to the buffer border.     */
    $$LEXEME_START_SET_TO_REF$$
    QUEX_GOTO_RELOAD_FORWARD($$COUNTER_ADR$$, $$TERMINAL_EOF_ADR$$);

$$BAD_CHARACTER_HANDLING$$
"""

def __get_bad_character_handler(Mode, IndentationSetup, CounterIdx):
    if Mode is None: 
        return ""

    if IndentationSetup.bad_character_set.get().is_empty(): 
        return ""

    txt  = "INDENTATION_COUNTER_%i_BAD_CHARACTER:\n" % CounterIdx
    if not Mode.has_code_fragment_list("on_indentation_bad"):
        txt += 'QUEX_ERROR_EXIT("Lexical analyzer mode \'%s\': bad indentation character detected!\\n"' \
                                % Mode.name + \
               '                "No \'on_indentation_bad\' handler has been specified.\\n");'
    else:
        code, eol_f = action_preparation.get_code(Mode.get_code_fragment_list("on_indentation_bad"))
        txt += "#define BadCharacter ((QUEX_TYPE_CHARACTER)*(me->buffer._input_p))\n"
        txt += code
        txt += "#undef  BadCharacter\n"

    return txt

def __get_transition_block(IndentationSetup, CountersStateIndex):
    # Mini trigger map:  [ trigger set ] --> loop start
    # That means: As long as characters of the trigger set appear, we go to the loop start.

    # If the indentation consists only of spaces, than it is 'uniform' ...
    if IndentationSetup.has_only_single_spaces():
        # Count indentation/column at end of run;
        # simply: current position - reference_p
        character_set = IndentationSetup.space_db.values()[0].get()
        interval_list = character_set.get_intervals(PromiseToTreatWellF=True)
        result        = [ (interval, CountersStateIndex) for interval in interval_list ]

    else:
        result = []
        # Add the space counters
        for count, character_set in IndentationSetup.space_db.items():
            interval_list = character_set.get().get_intervals(PromiseToTreatWellF=True)
            result.extend((interval, Count_Space(count, CountersStateIndex)) \
                          for interval in interval_list)
        # Add the grid counters
        for count, character_set in IndentationSetup.grid_db.items():
            interval_list = character_set.get().get_intervals(PromiseToTreatWellF=True)
            result.extend((interval, Count_Grid(count, CountersStateIndex)) \
                          for interval in interval_list)

    # Bad character detection
    if IndentationSetup.bad_character_set.get().is_empty() == False:
        for interval in IndentationSetup.bad_character_set.get().get_intervals(PromiseToTreatWellF=True):
            result.append((interval, Detect_Bad(CountersStateIndex)))

    transition_map_tools.sort(result)
    transition_map_tools.fill_gaps(result, E_StateIndices.DROP_OUT)

    txt = []
    transition_block.do(txt, result, 
                        StateIndex     = CountersStateIndex, 
                        EngineType     = E_EngineTypes.INDENTATION_COUNTER,
                        GotoReload_Str = "goto %s;" % get_label("$reload", CountersStateIndex))
    txt.append("\n")

    return txt

def __get_end_procedure(IndentationSetup, Mode):
    # NOTE: Line and column number counting is off
    #       -- No newline can occur
    #       -- column number = indentation at the end of the process
    indent_str = "    "
    txt = []
    if IndentationSetup.has_only_single_spaces():
        # Reference Pointer: Define Variable, Initialize, determine how to subtact.
        txt.append(indent_str + "me->counter._indentation = (size_t)(QUEX_NAME(Buffer_tell_memory_adr)(&me->buffer) - reference_p);\n")
    else:
        # Reference Pointer: Not required.
        #                    No subtraction 'current_position - reference_p'.
        #                    (however, we pass 'reference_p' to indentation handler)
        pass

    txt.append(indent_str + "__QUEX_IF_COUNT_COLUMNS_ADD(me->counter._indentation);\n")
    if Mode is None or Mode.default_indentation_handler_sufficient():
        txt.append(indent_str + "QUEX_NAME(on_indentation)(me, me->counter._indentation, reference_p);\n")
    else:
        # Definition of '%s_on_indentation' in mode_classes.py.
        txt.append(indent_str + "QUEX_NAME(%s_on_indentation)(me, me->counter._indentation, reference_p);\n" \
                   % Mode.name)

    return txt
