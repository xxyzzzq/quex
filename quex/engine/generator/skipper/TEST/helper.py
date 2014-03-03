import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.engine.generator.skipper.character_set as character_set_skipper
import quex.engine.generator.skipper.range         as range_skipper
import quex.engine.generator.skipper.nested_range  as nested_range_skipper
from   quex.engine.generator.TEST.generator_test   import *
from   quex.engine.generator.TEST.generator_test   import __Setup_init_language_database
from   quex.engine.generator.code.base             import CodeFragment
from   quex.engine.generator.base                  import do_state_router
from   quex.engine.state_machine.core              import StateMachine
from   quex.engine.analyzer.door_id_address_label  import get_plain_strings
from   quex.input.files.parser_data.counter        import CounterSetupLineColumn_Default
from   quex.input.regular_expression.construct     import Pattern

def __prepare(Language):
    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    dial_db.clear()
    variable_db.variable_db.init()

    return end_str

def create_character_set_skipper_code(Language, TestStr, TriggerSet, QuexBufferSize=1024, InitialSkipF=True, OnePassOnlyF=False):

    end_str = __prepare(Language)

    data = { 
        "character_set":        TriggerSet, 
        "counter_db":           CounterSetupLineColumn_Default(),
        "require_label_SKIP_f": False, 
    }
    class something:
        pass
    Analyzer = something()
    Analyzer.reload_state = None
    skipper_code = character_set_skipper.do(data, Analyzer)

    if InitialSkipF: marker_char_list = TriggerSet.get_number_list()
    else:            marker_char_list = []

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, 
                                               CommentTestStrF = False, 
                                               ShowPositionF   = False, 
                                               EndStr          = end_str,
                                               MarkerCharList  = marker_char_list, 
                                               LocalVariableDB = deepcopy(variable_db.variable_db.get()), 
                                               ReloadF         = True, 
                                               OnePassOnlyF    = OnePassOnlyF)

def create_range_skipper_code(Language, TestStr, CloserSequence, QuexBufferSize=1024, 
                              CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloserSequence) + 2

    end_str = __prepare(Language)

    data = { 
        "closer_sequence":                 CloserSequence, 
        "closer_pattern":                  Pattern(StateMachine.from_sequence(CloserSequence)),
    }
    event_db = {
        "on_skip_range_open": [ CodeFragment(end_str) ],
    }
    mode = get_mode_object("RangeSkipper", EventDB=event_db)

    skipper_code = range_skipper.do(data, mode)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=deepcopy(variable_db.variable_db.get())) 

def create_nested_range_skipper_code(Language, TestStr, OpenerSequence, CloserSequence, 
                                     QuexBufferSize=1024, CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloserSequence) + 2

    end_str = __prepare(Language)

    data = { 
        "opener_sequence":                 OpenerSequence, 
        "closer_sequence":                 CloserSequence, 
        "closer_pattern":                  Pattern(StateMachine.from_sequence(CloserSequence)),
    }
    event_db = {
        "on_skip_range_open": [ CodeFragment(end_str) ],
    }
    mode = get_mode_object("RangeSkipper", EventDB=event_db)

    skipper_code = nested_range_skipper.do(data, mode)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=deepcopy(variable_db.variable_db.get())) 

def create_customized_analyzer_function(Language, TestStr, EngineSourceCode, 
                                        QuexBufferSize, CommentTestStrF, ShowPositionF, 
                                        EndStr, MarkerCharList,
                                        LocalVariableDB, IndentationSupportF=False, 
                                        TokenQueueF=False, ReloadF=False, OnePassOnlyF=False):

    txt  = create_common_declarations(Language, QuexBufferSize, TestStr, 
                                      IndentationSupportF = IndentationSupportF, 
                                      TokenQueueF         = TokenQueueF,  
                                      QuexBufferFallbackN = 0)

    state_router_txt = do_state_router()
    EngineSourceCode.extend(state_router_txt)
    txt += my_own_mr_unit_test_function(EngineSourceCode, EndStr, LocalVariableDB, 
                                        ReloadF, OnePassOnlyF)

    txt += skip_irrelevant_character_function(MarkerCharList)

    txt += show_next_character_function(ShowPositionF)

    txt += create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF)

    return txt

def my_own_mr_unit_test_function(SourceCode, EndStr, 
                                 LocalVariableDB={}, ReloadF=False, OnePassOnlyF=True):
    
    if type(SourceCode) == list:
        plain_code = "".join(Lng.GET_PLAIN_STRINGS(SourceCode))

    label_failure  = dial_db.get_label_by_door_id(DoorID.incidence(E_IncidenceIDs.MATCH_FAILURE))
    label_eos      = dial_db.get_label_by_door_id(DoorID.incidence(E_IncidenceIDs.END_OF_STREAM))
    label_reentry  = dial_db.get_label_by_door_id(DoorID.global_reentry())
    label_reentry2 = dial_db.get_label_by_door_id(DoorID.continue_without_on_after_match())

    return blue_print(customized_unit_test_function_txt,
                      [
                       
                       ("$$LOCAL_VARIABLES$$",        Lng.VARIABLE_DEFINITIONS(VariableDB(LocalVariableDB))),
                       ("$$SOURCE_CODE$$",            plain_code),
                       ("$$TERMINAL_END_OF_STREAM$$", label_eos),
                       ("$$TERMINAL_FAILURE$$",       label_failure),
                       ("$$REENTRY$$",                label_reentry),
                       ("$$REENTRY2$$",               label_reentry2),
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

ENTRY:
    if( skip_irrelevant_characters(me) == false ) {
        goto $$TERMINAL_END_OF_STREAM$$;
    }
    QUEX_NAME(Counter_reset)(&me->counter);

/*__BEGIN_________________________________________________________________________________*/
$$SOURCE_CODE$$
/*__END___________________________________________________________________________________*/

$$REENTRY$$:
$$REENTRY2$$:
    /* Originally, the reentry preparation does not increment or do anything to _input_p
     * Here, we use the chance to print the position where the skipper ended.
     * If we are at the border and there is still stuff to load, then load it so we can
     * see what the next character is coming in.                                          */
    QUEX_NAME(Counter_print_this)(&self.counter);
    if( ! show_next_character(&me->buffer) || $$ONE_PASS_ONLY$$ ) goto $$TERMINAL_END_OF_STREAM$$; 
    goto ENTRY;

$$TERMINAL_FAILURE$$:
$$TERMINAL_END_OF_STREAM$$:
$$END_STR$$
#undef engine
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
    QUEX_TYPE_CHARACTER   input = 0x0;

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

