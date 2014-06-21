import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.engine.generator.skipper.character_set as character_set_skipper
import quex.engine.generator.skipper.range         as range_skipper
import quex.engine.generator.skipper.nested_range  as nested_range_skipper
import quex.engine.generator.skipper.indentation_counter as     indentation_counter
from   quex.engine.generator.TEST.generator_test   import *
from   quex.engine.generator.languages.variable_db import variable_db
from   quex.engine.generator.TEST.generator_test   import __Setup_init_language_database
from   quex.engine.generator.code.base             import CodeFragment
from   quex.engine.generator.base                  import do_state_router
from   quex.engine.state_machine.core              import StateMachine
from   quex.engine.analyzer.door_id_address_label  import get_plain_strings
from   quex.input.files.parser_data.counter        import CounterSetupLineColumn_Default
from   quex.input.regular_expression.construct     import Pattern
import quex.engine.analyzer.engine_supply_factory  as     engine

class MiniAnalyzer:
    def __init__(self):
        self.reload_state = None
        self.engine_type  = engine.FORWARD

Analyzer = MiniAnalyzer()

def __prepare(Language, TokenQueueF=False):
    end_str  = '    printf("end\\n");\n'
    if not TokenQueueF:
        end_str += '    return false;\n'
    else:
        end_str += "#   define self (*me)\n"
        end_str += "    self_send(QUEX_TKN_TERMINATION);\n"
        end_str += "    return;\n"
        end_str += "#   undef self\n"

    __Setup_init_language_database(Language)
    dial_db.clear()
    variable_db.init()

    return end_str

def __require_variables():
    variable_db.require("input")  
    variable_db.require("target_state_else_index")  # upon reload failure
    variable_db.require("target_state_index")       # upon reload success
    variable_db.require_array("position", ElementN = 0, Initial = "(void*)0")
    variable_db.require("PositionRegisterN", Initial = "(size_t)0")

def create_character_set_skipper_code(Language, TestStr, TriggerSet, QuexBufferSize=1024, InitialSkipF=True, OnePassOnlyF=False):

    end_str = __prepare(Language)

    data = { 
        "character_set":        TriggerSet, 
        "counter_db":           CounterSetupLineColumn_Default(),
        "require_label_SKIP_f": False, 
    }
    skipper_code = character_set_skipper.do(data, Analyzer)

    if InitialSkipF: marker_char_list = TriggerSet.get_number_list()
    else:            marker_char_list = []

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, 
                                               CommentTestStrF = False, 
                                               ShowPositionF   = False, 
                                               EndStr          = end_str,
                                               MarkerCharList  = marker_char_list, 
                                               LocalVariableDB = deepcopy(variable_db.get()), 
                                               ReloadF         = True, 
                                               OnePassOnlyF    = OnePassOnlyF)

def create_range_skipper_code(Language, TestStr, CloserSequence, QuexBufferSize=1024, 
                              CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloserSequence) + 2

    end_str = __prepare(Language)

    door_id_on_skip_range_open = dial_db.new_door_id()

    data = { 
        "closer_sequence":    CloserSequence, 
        "closer_pattern":     Pattern(StateMachine.from_sequence(CloserSequence)),
        "mode_name":          "MrUnitTest",
        "on_skip_range_open": CodeFragment([end_str]),
        "door_id_after":      DoorID.continue_without_on_after_match(),
    }

    skipper_code = range_skipper.do(data, Analyzer)
    __require_variables()

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList  = [], 
                                               LocalVariableDB = deepcopy(variable_db.get()),
                                               DoorIdOnSkipRangeOpen=door_id_on_skip_range_open) 

def create_nested_range_skipper_code(Language, TestStr, OpenerSequence, CloserSequence, 
                                     QuexBufferSize=1024, CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloserSequence) + 2

    end_str = __prepare(Language)

    door_id_on_skip_range_open = dial_db.new_door_id()
    data = { 
        "opener_sequence":    OpenerSequence, 
        "closer_sequence":    CloserSequence, 
        "closer_pattern":     Pattern(StateMachine.from_sequence(CloserSequence)),
        "mode_name":          "MrUnitTest",
        "on_skip_range_open": CodeFragment([end_str]),
        "door_id_after":      DoorID.continue_without_on_after_match(),
    }

    skipper_code = nested_range_skipper.do(data, Analyzer)
    __require_variables()

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=deepcopy(variable_db.get()), 
                                               DoorIdOnSkipRangeOpen=door_id_on_skip_range_open) 

def create_indentation_handler_code(Language, TestStr, ISetup, BufferSize, TokenQueueF):

    end_str = __prepare(Language, TokenQueueF)

    data = {
        "indentation_setup":             ISetup,
        "counter_db":                    CounterSetupLineColumn_Default(),
        "incidence_db":                  {E_IncidenceIDs.INDENTATION_BAD: ""},
        "incidence_id":                  dial_db.new_incidence_id(),
        "default_indentation_handler_f": True,
        "mode_name":                     "Test",
        "suppressed_newline":            None,
    }

    code_str = indentation_counter.do(data, Analyzer)

    return create_customized_analyzer_function(Language, TestStr, code_str, 
                                               QuexBufferSize=BufferSize, 
                                               CommentTestStrF="", ShowPositionF=False, 
                                               EndStr=end_str, MarkerCharList=map(ord, " :\t"),
                                               LocalVariableDB=deepcopy(variable_db.get()), 
                                               IndentationSupportF=True,
                                               TokenQueueF=TokenQueueF, 
                                               ReloadF=True, 
                                               CounterPrintF=False)

def create_customized_analyzer_function(Language, TestStr, EngineSourceCode, 
                                        QuexBufferSize, CommentTestStrF, ShowPositionF, 
                                        EndStr, MarkerCharList,
                                        LocalVariableDB, IndentationSupportF=False, 
                                        TokenQueueF=False, ReloadF=False, OnePassOnlyF=False, 
                                        DoorIdOnSkipRangeOpen=None, 
                                        CounterPrintF=True):

    txt  = create_common_declarations(Language, QuexBufferSize, TestStr, 
                                      IndentationSupportF = IndentationSupportF, 
                                      TokenQueueF         = TokenQueueF,  
                                      QuexBufferFallbackN = 0)

    state_router_txt = do_state_router()
    EngineSourceCode.extend(state_router_txt)
    txt += my_own_mr_unit_test_function(EngineSourceCode, EndStr, LocalVariableDB, 
                                        ReloadF, OnePassOnlyF, DoorIdOnSkipRangeOpen, 
                                        CounterPrintF)

    txt += skip_irrelevant_character_function(MarkerCharList)

    txt += show_next_character_function(ShowPositionF)

    txt += create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF)

    txt = txt.replace(Lng.SOURCE_REFERENCE_END(), "")

    return txt

def my_own_mr_unit_test_function(SourceCode, EndStr, 
                                 LocalVariableDB={}, ReloadF=False, OnePassOnlyF=True, DoorIdOnSkipRangeOpen=None, CounterPrintF=True):
    
    if type(SourceCode) == list:
        plain_code = "".join(Lng.GET_PLAIN_STRINGS(SourceCode))

    label_failure  = dial_db.get_label_by_door_id(DoorID.incidence(E_IncidenceIDs.MATCH_FAILURE))
    label_eos      = dial_db.get_label_by_door_id(DoorID.incidence(E_IncidenceIDs.END_OF_STREAM))
    label_reentry  = dial_db.get_label_by_door_id(DoorID.global_reentry())
    label_reentry2 = dial_db.get_label_by_door_id(DoorID.continue_without_on_after_match())
    if DoorIdOnSkipRangeOpen is not None:
        label_sro = dial_db.get_label_by_door_id(DoorIdOnSkipRangeOpen)
    else:
        label_sro = dial_db.get_label_by_door_id(dial_db.new_door_id())

    if CounterPrintF:
        counter_print_str = "QUEX_NAME(Counter_print_this)(&self.counter);"
    else:
        counter_print_str = ""


    return blue_print(customized_unit_test_function_txt,
                      [
                       ("$$LOCAL_VARIABLES$$",        Lng.VARIABLE_DEFINITIONS(VariableDB(LocalVariableDB))),
                       ("$$SOURCE_CODE$$",            plain_code),
                       ("$$COUNTER_PRINT$$",          counter_print_str),
                       ("$$TERMINAL_END_OF_STREAM$$", label_eos),
                       ("$$TERMINAL_FAILURE$$",       label_failure),
                       ("$$REENTRY$$",                label_reentry),
                       ("$$LEXEME_MACRO_SETUP$$",     Lng.LEXEME_MACRO_SETUP()),
                       ("$$LEXEME_MACRO_CLEAN_UP$$",  Lng.LEXEME_MACRO_CLEAN_UP()),
                       ("$$REENTRY2$$",               label_reentry2),
                       ("$$SKIP_RANGE_OPEN$$",        label_sro),
                       ("$$ONE_PASS_ONLY$$",          "true" if OnePassOnlyF else "false"),
                       ("$$QUEX_LABEL_STATE_ROUTER$$", dial_db.get_label_by_door_id(DoorID.global_state_router())),
                       ("$$END_STR$$",                EndStr)])

def skip_irrelevant_character_function(MarkerCharList):
    ml_txt = ""
    if len(MarkerCharList) != 0:
        for character in MarkerCharList:
            ml_txt += "        if( input == %i ) break;\n" % character
    else:
        ml_txt += "    break;\n"

    return skip_irrelevant_characters_function_txt.replace("$$MARKER_LIST$$", ml_txt)

def show_next_character_function(ShowPositionF):
    if ShowPositionF: show_position_str = "1"
    else:             show_position_str = "0"

    return show_next_character_function_txt.replace("$$SHOW_POSITION$$", show_position_str)

customized_unit_test_function_txt = """
static bool show_next_character(QUEX_NAME(Buffer)* buffer);
static bool skip_irrelevant_characters(QUEX_TYPE_ANALYZER* me);

__QUEX_TYPE_ANALYZER_RETURN_VALUE 
QUEX_NAME(Mr_analyzer_function)(QUEX_TYPE_ANALYZER* me)
{
#   define  engine (me)
#   define  self   (*me)
#   define QUEX_LABEL_STATE_ROUTER $$QUEX_LABEL_STATE_ROUTER$$ 
#   ifndef QUEX_TYPE_CHARACTER_POSITION
#      define QUEX_TYPE_CHARACTER_POSITION (QUEX_TYPE_CHARACTER*)
#   endif
$$LOCAL_VARIABLES$$
$$LEXEME_MACRO_SETUP$$
ENTRY:
    if( skip_irrelevant_characters(me) == false ) {
        goto $$TERMINAL_END_OF_STREAM$$;
    }
    /* QUEX_NAME(Counter_reset)(&me->counter); */
    me->counter._column_number_at_end = 1;

/*__BEGIN_________________________________________________________________________________*/
$$SOURCE_CODE$$
/*__END___________________________________________________________________________________*/

$$REENTRY$$:
$$REENTRY2$$:
    /* Originally, the reentry preparation does not increment or do anything to _input_p
     * Here, we use the chance to print the position where the skipper ended.
     * If we are at the border and there is still stuff to load, then load it so we can
     * see what the next character is coming in.                                          */
    $$COUNTER_PRINT$$ 
    if( ! show_next_character(&me->buffer) || $$ONE_PASS_ONLY$$ ) goto $$TERMINAL_END_OF_STREAM$$; 
    goto ENTRY;

$$TERMINAL_FAILURE$$:
$$TERMINAL_END_OF_STREAM$$:
$$SKIP_RANGE_OPEN$$:
$$END_STR$$
#undef engine

    if( 0 ) {
        /* Avoit undefined label warnings: */
        goto $$TERMINAL_FAILURE$$;
        goto $$TERMINAL_END_OF_STREAM$$;
        goto $$SKIP_RANGE_OPEN$$;
        goto $$REENTRY$$;
        goto $$REENTRY2$$;
    }
$$LEXEME_MACRO_CLEAN_UP$$
}
"""

show_next_character_function_txt = """
static bool
show_next_character(QUEX_NAME(Buffer)* buffer) 
{
    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) == 0 ) {
        buffer->_lexeme_start_p = buffer->_input_p;
        if( QUEX_NAME(Buffer_is_end_of_file)(buffer) ) {
            return false;
        }
        QUEX_NAME(buffer_reload_forward)(buffer, (QUEX_TYPE_CHARACTER_POSITION*)0x0, 0);
        ++(buffer->_input_p);
    }
    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) != 0 ) {
        if( ((*buffer->_input_p) & 0x80) == 0 ) 
            printf("next letter: <%c>\\n", (int)(buffer->_input_p[0]));
        else
            printf("next letter: <0x%02X>\\n", (int)(buffer->_input_p[0]));
#       if $$SHOW_POSITION$$
        printf(" position: %04X\\n", buffer->_input_p),
               (int)(buffer->_input_p - buffer->_memory._front));
#       else
        printf("\\n");
#       endif
    }
    return true;
}
"""

skip_irrelevant_characters_function_txt = """

static bool
skip_irrelevant_characters(QUEX_TYPE_ANALYZER* me)
{
    QUEX_TYPE_CHARACTER   input;
    (void)input;

    while(1 + 1 == 2) { 
        input = *(me->buffer._input_p);
$$MARKER_LIST$$
        if( QUEX_NAME(Buffer_distance_input_to_text_end)(&me->buffer) == 0 ) {
            me->buffer._lexeme_start_p = me->buffer._input_p;
            if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {
                return false;
            }
            QUEX_NAME(buffer_reload_forward)(&me->buffer, (QUEX_TYPE_CHARACTER_POSITION*)0x0, 0);
        }
        ++(me->buffer._input_p);
    }
    return true;
}
"""

