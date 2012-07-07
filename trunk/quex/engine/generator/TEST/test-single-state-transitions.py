#! /usr/bin/env python
# PURPOSE: Test the code generation for number sets. Two outputs are generated:
#
#           (1) stdout: containing value pairs (x,y) where y is 1.8 if x lies
#               inside the number set and 1.0 if x lies outside the number set.
#           (2) 'tmp2': containing the information about the number set under
#               consideration.
#
# The result is best viewed with 'gnuplot'. Call the program redirect the stdout
# to file 'tmp2' and type in gnuplot:
#
#         > plot [][0.8:2] "tmp2" w l, "tmp" w p
################################################################################
import sys
import os
import random
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.blackboard                         import setup as Setup
import quex.engine.generator.languages.core    as languages
from   quex.engine.generator.languages.address import __label_db
Setup.language_db = languages.db["C"]

from   quex.engine.interval_handling           import NumberSet, Interval
from   quex.engine.state_machine.core          import State, StateMachine
import quex.engine.state_machine.index         as index
from   quex.engine.analyzer.state.entry_action import DoorID

import quex.engine.generator.languages.core        as languages
import quex.engine.generator.languages.address     as address
import quex.engine.generator.state.transition.core as transition_block

from   quex.blackboard import E_EngineTypes

address.init_address_handling()

if "--hwut-info" in sys.argv:
    print "Single State: Transition Code Generation;"
    print "CHOICES: A, B, C;"
    sys.exit(0)

state = State()
StateIndex = 6666L

target_state_index_list = []
if "A" in sys.argv:
    state.add_transition(NumberSet([Interval(10,20),    Interval(195,196)]),  1L)
    state.add_transition(NumberSet([Interval(51,70),    Interval(261,280)]),  2L)
    state.add_transition(NumberSet([Interval(90,100),   Interval(110,130)]),  3L)
    state.add_transition(NumberSet([Interval(150,151),  Interval(151,190)]),  4L)
    state.add_transition(NumberSet([Interval(190,195),  Interval(21,30)]),    5L) 
    state.add_transition(NumberSet([Interval(197, 198), Interval(198, 198)]), 6L)
    state.add_transition(NumberSet([Interval(200,230),  Interval(231,240)]),  7L)
    state.add_transition(NumberSet([Interval(250,260),  Interval(71,80), Interval(71,71)]),  8L)
    
    target_state_index_list = map(long, [1, 2, 3, 4, 5, 6, 7, 8])
    interval_end = 300

elif "B" in sys.argv:
    interval_start = 0
    interval_end   = -1
    # initialize pseudo random generator: produces always the same numbers.
    random.seed(110270)   # must set the seed for randomness, otherwise system time
    #                     # is used which is no longer deterministic.
    max_number = 300
    for i in range(4000):
        interval_size      = int(random.random() * 4) + 1
        target_state_index = long(random.random() * 10)
        target_state_index_list.append(target_state_index)

        interval_end = interval_start + interval_size
        state.add_transition(Interval(interval_start, interval_end), target_state_index)
        interval_start = interval_end

elif "C" in sys.argv:
    interval_start = 0
    interval_end   = -1
    # initialize pseudo random generator: produces always the same numbers.
    random.seed(110270)   # must set the seed for randomness, otherwise system time
    #                     # is used which is no longer deterministic.
    target_state_index = long(0)
    for i in range(1000):
        if random.random() > 0.75:
            interval_size      = int(random.random() * 3) + 1
            target_state_index = long(random.random() * 5)
            target_state_index_list.append(target_state_index)

            interval_end = interval_start + interval_size
            state.add_transition(Interval(interval_start, interval_end), target_state_index)
            interval_start = interval_end
        else:
            target_state_index = long(random.random() * 5)
            target_state_index_list.append(target_state_index)

            for dummy in xrange(0, int(random.random() * 5) + 2):
                state.add_transition(Interval(interval_start, interval_start + 1), target_state_index)
                interval_start += 1 + int(random.random() * 2)

states = []
for state_index in sorted(list(set(target_state_index_list))):
    door_id = DoorID(state_index, None)
    states.append("%s: return (int)%i;\n" % (address.get_label("$entry", door_id), state_index))
    # increment the state index counter, so that the drop-out and reload labels 
    # get an appropriate label.
    index.get()
index.get()
index.get()
reload   = "%s: return (int)-1;\n" % address.get_label("$reload", -1)
states.insert(0, reload)
drop_out = "%s: return (int)-1;\n" % address.get_label("$drop-out", -1)
states.insert(0, drop_out)

# One for the 'terminal'
__label_db["$entry"](DoorID(index.get(), None))

function  = [ 
    "#define __quex_debug_state(X) /* empty */\n",
    "int transition(int input) {\n" 
]
transition_block.do(function, 
                    state.transitions().get_trigger_map(), 
                    StateIndex=StateIndex,
                    EngineType=E_EngineTypes.BACKWARD_INPUT_POSITION,
                    GotoReload_Str="return -1;")

function.extend(states)
function.append("\n}\n")

main_txt = """

#include <stdio.h>
int
main(int argc, char** argv) {
#   define      InputSize                $$N$$ 
    const int   input[InputSize]       = { $$CHARS$$ };
    const int   expectation[InputSize] = { $$EXPECT$$ };
    const int*  InputEnd = (const int*)input + InputSize;
    int         result = 0;
    const int*  iterator = 0;
    const int*  eiterator = 0;

    for(iterator = input, eiterator = expectation; 
        iterator != InputEnd; 
        ++iterator, ++eiterator) {
        result = transition(*iterator);
        printf("%i %i %i\\n", *iterator, result, *eiterator);
        if( result != *eiterator ) {
            printf("ERROR");
            break;
        }
    }
}
"""

# Prepare the main function
input_list     = range(interval_end)
input_array    = repr(input_list)[1:-1]
expected_list  = [ state.transitions().get_resulting_target_state_index(number) for number in input_list ]
expected_array = repr([ -1 if x is None else int(x) for x in expected_list])[1:-1]

main_txt = main_txt.replace("$$N$$", repr(len(input_list)))
main_txt = main_txt.replace("$$CHARS$$", input_array)
main_txt = main_txt.replace("$$EXPECT$$", expected_array)

txt = function + [ main_txt ]
Setup.language_db.REPLACE_INDENT(txt)

fh = open("test.c", "wb")
fh.write("".join(txt))
fh.close()
os.system("gcc test.c -o test")
os.system("./test")
os.remove("./test")
os.remove("./test.c")





