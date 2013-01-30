import quex.engine.state_machine.algorithm.beautifier as beautifier
import quex.engine.state_machine.algebra.reverse      as reverse
import quex.engine.state_machine.algebra.cut_begin    as cut_begin

def do(SM_A, SM_B):
    all_star      = repeat.do(special.get_any(), min_repetition_n=0)
    sm_b_repeated = repeat.do(SM_B, min_repetition_n=1)

    tmp = sequentialize.do([all_star, sm_b_repeated], 
                           MountToFirstStateMachineF=True, 
                           CloneRemainingStateMachinesF=True)

    tmp = beautifier.do(tmp)

    # There might be many paths which have no hope to reach acceptance
    tmp.clean_up()

    return cut_begin.do(SM_A, tmp)
