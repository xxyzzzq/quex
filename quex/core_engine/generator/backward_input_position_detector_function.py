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


def do(sm, LanguageDB):




