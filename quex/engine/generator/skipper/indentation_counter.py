from   quex.blackboard                              import setup as Setup, \
                                                           E_StateIndices
import quex.blackboard                              as     blackboard
import quex.engine.state_machine.index              as     sm_index
import quex.engine.analyzer.engine_supply_factory   as     engine
from   quex.engine.analyzer.transition_map          import TransitionMap
import quex.engine.generator.state.transition.core  as     relate_to_TransitionCode
from   quex.engine.generator.state.transition.code  import TransitionCode
from   quex.engine.generator.languages.variable_db  import variable_db
from   quex.engine.analyzer.door_id_address_label   import dial_db, \
                                                           Label
from   quex.engine.misc.string_handling             import blue_print

def do(Data, Mode=None):
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
    global variable_db

    

    IndentationSetup = Data["indentation_setup"]
    assert IndentationSetup.__class__.__name__ == "IndentationSetup"

    Mode = None
    if IndentationSetup.containing_mode_name() != "":
        Mode = blackboard.mode_db[IndentationSetup.containing_mode_name()]

    # The 'TransitionCode -> DoorID' has to be circumvented, because this state
    # is not officially part of the state machine.
    counter_adr          = dial_db.new_address()
    counter_label        = dial_db.map_address_to_label(counter_adr)
    counter_adr_str      = "%i" % counter_adr
    transition_block_str = __get_transition_block(IndentationSetup, counter_adr)
    end_procedure        = __get_end_procedure(IndentationSetup, Mode)

    dial_db.mark_address_as_routed(counter_adr) 

    # The finishing touch
    prolog = blue_print(prolog_txt,
                         [
                           ["$$INPUT_GET$$",         Lng.ACCESS_INPUT()],
                           ["$$INPUT_P_INCREMENT$$", Lng.INPUT_P_INCREMENT()],
                           ["$$LABEL$$",             counter_label],
                           ["$$ADDRESS$$",           counter_adr_str], 
                         ])

    # The finishing touch
    teof_address = dial_db.get_address_by_door_id(DoorID.incidence(E_IncidenceIDs.END_OF_STREAM))
    dial_db.mark_address_as_routed(teof_address)

    epilog = blue_print(epilog_txt, [
        ["$$ADDRESS$$",                 counter_adr_str], 
        ["$$END_PROCEDURE$$",           "".join(end_procedure)],
        ["$$GOTO_REENTRY$$",            Lng.GOTO_BY_DOOR_ID(DoorID.global_reentry())],
        ["$$BAD_CHARACTER_HANDLING$$",  __get_bad_character_handler(Mode, IndentationSetup, counter_adr)],
    ])

    txt = [prolog]
    txt.extend(transition_block_str)
    txt.append(epilog)

    variable_db.require("reference_p")

    return txt

prolog_txt = """
    QUEX_BUFFER_ASSERT_CONSISTENCY(&me->buffer);
    __quex_assert(QUEX_NAME(Buffer_content_size)(&me->buffer) >= 1);

    /* Indentation Counter:
     * Skip whitespace at line begin; Count indentation. */

    reference_p              = me->buffer._input_p;
    me->counter._indentation = (QUEX_TYPE_INDENTATION)0;

    goto _ENTRY_$$ADDRESS$$;

$$LABEL$$:
    $$INPUT_P_INCREMENT$$ 
_ENTRY_$$ADDRESS$$:
$$INPUT_GET$$ 
"""

epilog_txt = """
    /* Here's where the first non-whitespace appeared after newline. 
     * 
     * NOTE: The entry into the indentation counter happens by matching the pattern:
     * 
     *                   newline ([space]* newline)*'
     *
     * Thus, it is not possible that here a newline appears. All empty lines have 
     * been eaten by the pattern match.                                            */
$$END_PROCEDURE$$                           
    /* No need for re-entry preparation. Acceptance flags and modes are untouched. */
    $$GOTO_REENTRY$$

$$BAD_CHARACTER_HANDLING$$
"""

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
    def __init__(self, Type, Number, CounterAdr):
        self.type        = Type
        self.number      = Number
        self.counter_adr = CounterAdr

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
    def __init__(self, Number, CounterAdr):
        self.number        = Number
        self.counter_adr   = CounterAdr
        self.variable_name = None        # not yet implemented

    def __eq__(self, Other):
        if Other.__class__ != Count_Space: return False
        return self.number == Other.number and self.variable_name == Other.variable_name

    @property
    def code(self):
        """Indentation counters may count as a consequence of a 'triggering'."""
        

        # Spaces simply increment
        if self.number != -1: add_str = "%i" % self.number
        else:                 add_str = "me->" + self.variable_name
        return "me->counter._indentation += %s;" % add_str + Lng.GOTO_door_id(self.counter_door_id)

class Count_Grid(IndentationCounter):
    """________________________________________________________________________
    
    Implement the 'grid count' action upon the detection of a grid character.
    The '_indentation' is incremented to the next value on a grid.
    ___________________________________________________________________________
    """
    def __init__(self, Number, CounterAdr):
        self.number        = Number
        self.counter_adr   = CounterAdr
        self.variable_name = None        # not yet implemented

    def __eq__(self, Other):
        if Other.__class__ != Count_Grid: return False
        return self.number == Other.number and self.variable_name == Other.variable_name

    @property
    def code(self):
        """Indentation counters may count as a consequence of a 'triggering'."""
        
        
        txt = Lng.GRID_STEP("me->counter._indentation", "QUEX_TYPE_INDENTATION", self.number)
        Lng.REPLACE_INDENT(txt)

        return   "".join(txt) \
               + Lng.GOTO_DOOR_ID(self.counter_door_id)

class Detect_Bad(IndentationCounter):
    """________________________________________________________________________
    
    Implement the 'transit to bad indentation character' region upon the 
    detection of a grid character. 
    ___________________________________________________________________________
    """
    def __init__(self, CounterAdr):
        assert CounterAdr != -1
        self.counter_adr = CounterAdr
        
    def __eq__(self, Other):
        if Other.__class__ != Detect_Bad: return False
        return self.counter_adr == Other.counter_adr

    @property
    def code(self):
        return "goto _BAD_CHARACTER_%i;\n" % self.counter_adr

def __get_bad_character_handler(Mode, IndentationSetup, CounterIdx):
    if Mode is None: 
        return ""

    if IndentationSetup.bad_character_set.get().is_empty(): 
        return ""

    txt  = "_BAD_CHARACTER_%i:\n" % CounterIdx
    if not Mode.incidence_db.has_key(E_IncidenceIDs.INDENTATION_BAD):
        txt += 'QUEX_ERROR_EXIT("Lexical analyzer mode \'%s\': bad indentation character detected!\\n"' \
                                % Mode.name + \
               '                "No \'on_indentation_bad\' handler has been specified.\\n");'
    else:
        code, eol_f = Mode.incidence_db[E_IncidenceIDs.INDENTATION_BAD].get_text()
        txt += "#define BadCharacter ((QUEX_TYPE_CHARACTER)*(me->buffer._input_p))\n"
        txt += code
        txt += "#undef  BadCharacter\n"

    return txt

def __get_transition_block(IndentationSetup, CounterAdr):
    """Generate the transition block.
    
    The transition code MUST circumvent the 'TransitionID --> DoorID' mapping.
    This is so, since the implemented state is not 'officially' part of the
    analyzer state machine. The transition_map relies on 'TransitionCode'
    objects as target.
    """
    

    def extend(transition_map, character_set, Target):
        interval_list = character_set.get().get_intervals(PromiseToTreatWellF=True)
        transition_map.extend((interval, Target) for interval in interval_list)

    transition_map = TransitionMap()
    if IndentationSetup.homogeneous_spaces():
        # If the indentation consists only of spaces, than it is 'uniform' ...
        # Count indentation/column at end of run;
        # simply: current position - reference_p
        character_set  = IndentationSetup.space_db.values()[0]
        extend(transition_map, character_set, TransitionCode(Lng.GOTO_BY_DOOR_ID(CounterDoorId)))

    else:
        # Add the space counters
        for count, character_set in IndentationSetup.space_db.items():
            extend(transition_map, character_set, Count_Space(count, CounterAdr))

        # Add the grid counters
        for count, character_set in IndentationSetup.grid_db.items():
            extend(transition_map, character_set, Count_Grid(count, CounterAdr))

    # Bad character detection
    if IndentationSetup.bad_character_set.get().is_empty() == False:
        extend(transition_map, IndentationSetup.bad_character_set, 
               Detect_Bad(CounterAdr))

    transition_map.sort()
    transition_map.fill_gaps(DoorID.drop_out(CounterAdr))

    reload_cl = CommandList()
    reload_cl.append(LexemeStartToReferenceP("reference_p"))
    reload_cl.append(PrepareAfterReload_InitState(state)) # This causes 'Terminal End-of-File' upon reload failure.
    analyzer.reload_state.add_state(CounterState, reload_cl)

    txt = []
    tm = relate_to_TransitionCode(transition_map)
    transition_block.do(txt, tm) 
    txt.append("\n")

    return txt

def __get_end_procedure(IndentationSetup, Mode):
    # NOTE: Line and column number counting is off
    #       -- No newline can occur
    #       -- column number = indentation at the end of the process
    indent_str = "    "
    txt = []
    if IndentationSetup.homogeneous_spaces():
        # Reference Pointer: Define Variable, Initialize, determine how to subtact.
        txt.append(indent_str + "me->counter._indentation = (size_t)(me->buffer._input_p - reference_p);\n")
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

