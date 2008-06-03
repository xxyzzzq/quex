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
static void 
PAPC_input_postion_backward_detector_$$ID$$(QUEX_CORE_ANALYSER_STRUCT* me) 
{
$$LOCAL_VARIABLES$$
$$STATE_MACHINE$$
$$FUNCTION_BODY$$ 
}
"""

def do(sm, LanguageDB, PrintStateMachineF):

    function_body = state_machine_coder.do(sm, LanguageDB, 
                                           BackwardLexingF                 = True,
                                           BackwardInputPositionDetectionF = True)

    sm_str = "    " + LanguageDB["$comment"]("state machine") + "\n"
    if PrintStateMachineF: 
        sm_str += LanguageDB["$ml-comment"](sm.get_string(NormalizeF=False)) + "\n"

    # -- input position detectors simply the next 'catch' and return
    function_body += LanguageDB["$label-def"]["$terminal-general"](BackwardLexingF=True) + "\n"
    ## function_body += "    $/* ... rely on the compiler to delete the unnecessary assignment ... $*/\n"
    ## function_body += "    QUEX_STREAM_GET_BACKWARDS($input);\n"
    ## function_body += "#   ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING\n"
    ## function_body += "    backward_lexing_drop_out(me, input);\n" 
    ## function_body += "#   endif\n"
    ## function_body += "    $return\n"
    function_body += "    QUEX_BUFFER_SEEK_ADR(end_of_core_pattern_position);\n"
    function_body += "    " + LanguageDB["$decrement"] + "\n"
    function_body += "    " + LanguageDB["$get"] + "\n"

    variables_txt = LanguageDB["$local-variable-defs"](
        [["QUEX_CHARACTER_TYPE",     "input",                        "(QUEX_CHARACTER_TYPE)(0x0)"],
         ["QUEX_CHARACTER_POSITION", "end_of_core_pattern_position", "(QUEX_CHARACTER_TYPE*)(0x0)"]])

    return blue_print(function_str, 
                      [["$$ID$$",              repr(sm.get_id()).replace("L", "")],
                       ["$$FUNCTION_BODY$$",   function_body],
                       ["$$LOCAL_VARIABLES$$", variables_txt],
                       ["$$STATE_MACHINE$$",   sm_str],
                      ])




