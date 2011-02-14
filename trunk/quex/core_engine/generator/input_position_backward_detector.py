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
import quex.core_engine.generator.state_machine_coder     as state_machine_coder
from   quex.core_engine.generator.state_machine_decorator import StateMachineDecorator
from   quex.frs_py.string_handling                        import blue_print
import quex.core_engine.generator.state_router            as state_router
from   quex.input.setup                                   import setup as Setup

function_str = """
#include <quex/code_base/temporary_macros_on>
QUEX_INLINE void 
PAPC_input_postion_backward_detector_$$ID$$(QUEX_TYPE_ANALYZER* me) 
{
$$LOCAL_VARIABLES$$
$$STATE_MACHINE$$
$$FUNCTION_BODY$$ 
}
#include <quex/code_base/temporary_macros_off>
"""

def do(sm, LanguageDB):

    decorated_state_machine = StateMachineDecorator(sm, 
                                                    "BACKWARD_DETECTOR_" + repr(sm.get_id()),
                                                    PostContextSM_ID_List = [], 
                                                    BackwardLexingF=True, 
                                                    BackwardInputPositionDetectionF=True)

    function_body, variable_db, routed_state_info_list = state_machine_coder.do(decorated_state_machine)

    sm_str = "    " + LanguageDB["$comment"]("state machine") + "\n"
    if Setup.comment_state_machine_transitions_f: 
        analyzer_code += Setup.language_db["$ml-comment"]("BEGIN: BACKWARD DETECTOR STATE MACHINE\n" + \
                                                          sm.get_string(NormalizeF=False)            + \
                                                          "\nEND: BACKWARD DETECTOR STATE MACHINE")
        analyzer_code += "\n"

    if len(routed_state_info_list) != 0:
        function_body += state_router.do(routed_state_info_list)

    # -- input position detectors simply the next 'catch' and return
    function_body += LanguageDB["$label-def"]("$terminal-general-bw") + "\n"
    function_body += LanguageDB["$input/seek_position"]("end_of_core_pattern_position") + "\n"
    function_body += LanguageDB["$input/increment"] + "\n"

    variable_db.update({
         "input":                        ["QUEX_TYPE_CHARACTER",          "(QUEX_TYPE_CHARACTER)(0x0)"],
         "end_of_core_pattern_position": ["QUEX_TYPE_CHARACTER_POSITION", "(QUEX_TYPE_CHARACTER*)(0x0)"],
    })
    variables_txt = LanguageDB["$local-variable-defs"](variable_db)

    return blue_print(function_str, 
                      [["$$ID$$",              repr(sm.get_id()).replace("L", "")],
                       ["$$FUNCTION_BODY$$",   function_body],
                       ["$$LOCAL_VARIABLES$$", variables_txt],
                       ["$$STATE_MACHINE$$",   sm_str],
                      ])




