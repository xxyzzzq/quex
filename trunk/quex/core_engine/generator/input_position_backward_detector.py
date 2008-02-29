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
import quex.core_engine.generator.languages.label     as languages_label
from quex.frs_py.string_handling import blue_print

function_str = """
static void 
PAPC_input_postion_backward_detector_$$ID$$(QUEX_CORE_ANALYSER_STRUCT* me) 
{
    QUEX_CHARACTER_TYPE      input = (QUEX_CHARACTER_TYPE)(0x00);\n
    QUEX_CHARACTER_POSITION  end_of_core_pattern_position = (QUEX_CHARACTER_TYPE*)(0x00);
$$STATE_MACHINE$$
$$FUNCTION_BODY$$ 
}
"""

def do(sm, LanguageDB, PrintStateMachineF, ForbiddenCharacterCodeList):

    function_body = state_machine_coder.do(sm, LanguageDB, 
                                           BackwardLexingF                 = True,
                                           BackwardInputPositionDetectionF = True,
                                           ForbiddenCharacterCodeList      = ForbiddenCharacterCodeList)

    sm_str = "    $/* state machine $*/\n"
    if PrintStateMachineF: 
        sm_str += "    $/* " + repr(sm).replace("\n", "$*/\n    $/* ") + "\n"

    # -- input position detectors simply the next 'catch' and return
    LabelName = languages_label.get_terminal("")
    function_body += "%s\n" % LanguageDB["$label-definition"](LabelName) 
    ## function_body += "    $/* ... rely on the compiler to delete the unnecessary assignment ... $*/\n"
    ## function_body += "    QUEX_STREAM_GET_BACKWARDS($input);\n"
    ## function_body += "#   ifdef __QUEX_CORE_OPTION_TRANSITION_DROP_OUT_HANDLING\n"
    ## function_body += "    backward_lexing_drop_out(me, input);\n" 
    ## function_body += "#   endif\n"
    ## function_body += "    $return\n"
    function_body += "    QUEX_STREAM_SEEK(end_of_core_pattern_position);\n"

    return blue_print(function_str, 
                      [["$$ID$$",            repr(sm.get_id()).replace("L", "")],
                       ["$$FUNCTION_BODY$$", function_body],
                       ["$$STATE_MACHINE$$", sm_str],
                      ])




