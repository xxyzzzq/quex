import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import quex.engine.generator.skipper.character_set as character_set_skipper
import quex.engine.generator.skipper.range         as range_skipper
import quex.engine.generator.skipper.nested_range  as nested_range_skipper
from   quex.engine.state_machine.core              import StateMachine
from   quex.input.regular_expression.construct     import Pattern
from   quex.engine.generator.TEST.generator_test   import *
from   quex.engine.generator.TEST.generator_test   import __Setup_init_language_database
from   quex.engine.generator.code_fragment_base import CodeFragment

def create_character_set_skipper_code(Language, TestStr, TriggerSet, QuexBufferSize=1024):

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    address.init_address_handling()
    variable_db.variable_db.init()
    data = { 
        "character_set": TriggerSet, 
        "require_label_SKIP_f": True, 
    }
    skipper_code = character_set_skipper.do(data, get_mode_object("CharacterSetSkipper"))

    marker_char_list = []
    for interval in TriggerSet.get_intervals():
        for char_code in range(interval.begin, interval.end):
            marker_char_list.append(char_code)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF=False, 
                                               ShowPositionF=False, EndStr=end_str,
                                               MarkerCharList=marker_char_list, 
                                               LocalVariableDB=deepcopy(variable_db.variable_db.get()), 
                                               ReloadF=True)

def create_range_skipper_code(Language, TestStr, CloserSequence, QuexBufferSize=1024, 
                              CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloserSequence) + 2

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    address.init_address_handling()
    variable_db.variable_db.init()

    data = { 
        "closer_sequence":                 CloserSequence, 
        "closer_pattern":                  Pattern(StateMachine.from_sequence(CloserSequence)),
        "indentation_counter_terminal_id": None,
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

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    address.init_address_handling()
    variable_db.variable_db.init()

    data = { 
        "opener_sequence":                 OpenerSequence, 
        "closer_sequence":                 CloserSequence, 
        "closer_pattern":                  Pattern(StateMachine.from_sequence(CloserSequence)),
        "indentation_counter_terminal_id": None,
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
                                        TokenQueueF=False, ReloadF=False):

    txt  = create_common_declarations(Language, QuexBufferSize, TestStr, 
                                      IndentationSupportF=IndentationSupportF, 
                                      TokenQueueF=TokenQueueF)
    txt += my_own_mr_unit_test_function(ShowPositionF, MarkerCharList, EngineSourceCode, EndStr, LocalVariableDB, ReloadF)
    txt += create_main_function(Language, TestStr, QuexBufferSize, CommentTestStrF)

    return txt

def my_own_mr_unit_test_function(ShowPositionF, MarkerCharList, SourceCode, EndStr, LocalVariableDB={},ReloadF=False):
    LanguageDB = Setup.language_db
    if ShowPositionF: show_position_str = "1"
    else:             show_position_str = "0"

    ml_txt = ""
    if len(MarkerCharList) != 0:
        for character in MarkerCharList:
            ml_txt += "        if( input == %i ) break;\n" % character
    else:
        ml_txt += "    break;\n"

    if type(SourceCode) == list:
        SourceCode = "".join(address.get_plain_strings(SourceCode))

    reload_str = ""
    if ReloadF: 
        txt = []
        for x in LanguageDB.RELOAD():
            txt.extend(x.code)
        # Ensure that '__RELOAD_FORWARD' and '__RELOAD_BACKWARD' is referenced
        routed_address_set = address.get_address_set_subject_to_routing()
        routed_address_set.add(address.get_address("$terminal-EOF", U=True))
        routed_state_info_list = state_router_generator.get_info(routed_address_set)
        txt.extend(address.get_plain_strings([state_router_generator.do(routed_state_info_list)]))
        txt.append("    goto __RELOAD_FORWARD;\n")
        txt.append("    goto __RELOAD_BACKWARD;\n")
        reload_str = "".join(txt)
        variable_db.enter(LocalVariableDB, "target_state_else_index")
        variable_db.enter(LocalVariableDB, "target_state_index")

    return blue_print(customized_unit_test_function_txt,
                      [("$$MARKER_LIST$$",            ml_txt),
                       ("$$SHOW_POSITION$$",          show_position_str),
                       ("$$LOCAL_VARIABLES$$",        "".join(LanguageDB.VARIABLE_DEFINITIONS(VariableDB(LocalVariableDB)))),
                       ("$$MARK_LEXEME_START$$",      LanguageDB.LEXEME_START_SET()),
                       ("$$SOURCE_CODE$$",            SourceCode),
                       ("$$INPUT_P_DEREFERENCE$$",    LanguageDB.ASSIGN("input", LanguageDB.INPUT_P_DEREFERENCE())),
                       ("$$TERMINAL_END_OF_STREAM$$", address.get_label("$terminal-EOF")),
                       ("$$RELOAD$$",                 reload_str),
                       ("$$END_STR$$",                EndStr)])

customized_unit_test_function_txt = """
bool
show_next_character(QUEX_NAME(Buffer)* buffer) {

    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) == 0 ) {
        buffer->_lexeme_start_p = buffer->_input_p;
        if( QUEX_NAME(Buffer_is_end_of_file)(buffer) ) {
            return false;
        }
        QUEX_NAME(buffer_reload_forward)(buffer, (QUEX_TYPE_CHARACTER_POSITION*)0x0, 0);
        ++(buffer->_input_p);
    }
    if( QUEX_NAME(Buffer_distance_input_to_text_end)(buffer) != 0 ) {
#       if $$SHOW_POSITION$$
        printf("next letter: <%c> position: %04X\\n", (char)(*(buffer->_input_p)),
               (int)(buffer->_input_p - buffer->_memory._front));
#       else
        printf("next letter: <%c>\\n", (char)(*(buffer->_input_p)));
#       endif
    }
    return true;
}

__QUEX_TYPE_ANALYZER_RETURN_VALUE 
QUEX_NAME(Mr_UnitTest_analyzer_function)(QUEX_TYPE_ANALYZER* me)
{
#   define  engine (me)
#   define  self   (*me)
    QUEX_TYPE_CHARACTER  input = 0x0;
#   define  position          ((void*)0x0)
#   define  PositionRegisterN 0
$$LOCAL_VARIABLES$$

ENTRY:
    /* Skip irrelevant characters */
    while(1 + 1 == 2) { 
        $$INPUT_P_DEREFERENCE$$
$$MARKER_LIST$$
        if( QUEX_NAME(Buffer_distance_input_to_text_end)(&me->buffer) == 0 ) {
            $$MARK_LEXEME_START$$
            if( QUEX_NAME(Buffer_is_end_of_file)(&me->buffer) ) {
                goto $$TERMINAL_END_OF_STREAM$$;
            }
            QUEX_NAME(buffer_reload_forward)(&me->buffer, (QUEX_TYPE_CHARACTER_POSITION*)0x0, 0);
        }
        ++(me->buffer._input_p);
    }
    QUEX_NAME(Counter_reset)(&me->counter);
/*________________________________________________________________________________________*/
$$SOURCE_CODE$$
/*________________________________________________________________________________________*/
$$RELOAD$$

__REENTRY:
    /* Originally, the reentry preparation does not increment or do anything to _input_p
     * Here, we use the chance to print the position where the skipper ended.
     * If we are at the border and there is still stuff to load, then load it so we can
     * see what the next character is coming in.                                          */
    QUEX_NAME(Counter_print_this)(&self.counter);
    if( ! show_next_character(&me->buffer) ) goto $$TERMINAL_END_OF_STREAM$$; 
    goto ENTRY;

$$TERMINAL_END_OF_STREAM$$:
$$END_STR$$
#undef engine
}
"""

