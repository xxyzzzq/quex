# PURPOSE: Where there is a pseudo ambiguous post-condition, there
#          cannot be made an immediate decision about the input position after
#          an acceptance state is reached. Instead, it is necessary to 
#          go backwards and detect the start of the post-condition 
#          a-posteriori. This function produces code of the backward
#          detector inside a function.
#
# (C) 2007 Frank-Rene Schaefer
#
################################################################################
import quex.core_engine.generator.state_machine_coder as state_machine_coder
from quex.frs_py.string_handling import blue_print

function_str = """
#include <quex/code_base/temporary_macros_on>
TEMPLATE_IN void 
PAPC_input_postion_backward_detector_$$ID$$(MINIMAL_ANALYZER_TYPE* me) 
{
$$LOCAL_VARIABLES$$
$$STATE_MACHINE$$
$$FUNCTION_BODY$$ 
}
#include <quex/code_base/temporary_macros_off>
"""

def do(sm, LanguageDB, PrintStateMachineF):

    function_body, directly_reached_terminal_id_list = \
              state_machine_coder.do(sm, LanguageDB, 
                                     BackwardLexingF                 = True,
                                     BackwardInputPositionDetectionF = True,
                                     PostConditionID_List            = [])

    sm_str = "    " + LanguageDB["$comment"]("state machine") + "\n"
    if PrintStateMachineF: 
        sm_str += LanguageDB["$ml-comment"](sm.get_string(NormalizeF=False)) + "\n"

    # -- input position detectors simply the next 'catch' and return
    function_body += LanguageDB["$label-def"]("$terminal-general", True) + "\n"
    function_body += LanguageDB["$input/seek_position"]("end_of_core_pattern_position") + "\n"
    function_body += LanguageDB["$input/increment"] + "\n"

    variables_txt = LanguageDB["$local-variable-defs"](
            [["CharacterCarrierType",         "input",                        "(CharacterCarrierType)(0x0)"],
             ["QUEX_CHARACTER_POSITION_TYPE", "end_of_core_pattern_position", "(CharacterCarrierType*)(0x0)"]])

    return blue_print(function_str, 
                      [["$$ID$$",              repr(sm.get_id()).replace("L", "")],
                       ["$$FUNCTION_BODY$$",   function_body],
                       ["$$LOCAL_VARIABLES$$", variables_txt],
                       ["$$STATE_MACHINE$$",   sm_str],
                      ])




