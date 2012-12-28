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

