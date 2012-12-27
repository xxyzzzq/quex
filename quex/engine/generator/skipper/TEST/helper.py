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

def create_range_skipper_code(Language, TestStr, EndSequence, QuexBufferSize=1024, 
                              CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(EndSequence) + 2

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    address.init_address_handling()
    variable_db.variable_db.init()

    data = { 
        "closer_sequence":                 EndSequence, 
        "closer_pattern":                  Pattern(StateMachine.from_sequence(EndSequence)),
        "indentation_counter_terminal_id": None,
    }
    skipper_code = range_skipper.do(data, get_mode_object("RangeSkipper"))

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=deepcopy(variable_db.variable_db.get())) 

def create_nested_range_skipper_code(Language, TestStr, OpenSequence, CloseSequence, 
                                     QuexBufferSize=1024, CommentTestStrF=False, ShowPositionF=False):
    assert QuexBufferSize >= len(CloseSequence) + 2

    end_str  = '    printf("end\\n");'
    end_str += '    return false;\n'

    __Setup_init_language_database(Language)
    address.init_address_handling()
    variable_db.variable_db.init()
    skipper_code = nested_range_skipper.get_skipper(OpenSequence, CloseSequence, 
                                                    OnSkipRangeOpenStr=end_str)

    return create_customized_analyzer_function(Language, TestStr, skipper_code,
                                               QuexBufferSize, CommentTestStrF, ShowPositionF, end_str,
                                               MarkerCharList=[], LocalVariableDB=deepcopy(variable_db.variable_db.get())) 

