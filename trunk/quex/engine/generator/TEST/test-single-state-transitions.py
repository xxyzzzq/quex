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
import quex.engine.analyzer.engine_supply_factory  as     engine
import quex.engine.analyzer.transition_map  as     transition_map_tool

from   quex.engine.generator.base                  import Generator as CppGenerator
import quex.engine.generator.languages.core        as languages
import quex.engine.generator.languages.address     as address
import quex.engine.generator.state.transition.core as transition_block


address.init_address_handling()

if "--hwut-info" in sys.argv:
    print "Single State: Transition Code Generation;"
    print "CHOICES: A, B, C, A-UTF8, B-UTF8, C-UTF8;"
    sys.exit(0)

choice, codec = {
        "A": ("A", ""),
        "B": ("B", ""),
        "C": ("C", ""),
        "A-UTF8": ("A", "UTF8"),
        "B-UTF8": ("B", "UTF8"),
        "C-UTF8": ("C", "UTF8"),
}[sys.argv[1]]

state      = State()
StateIndex = 6666L

if choice == "A":
    tm0 = [
        (Interval(10,20),    1L), 
        (Interval(195,196),  1L),
        (Interval(51,70),    2L), 
        (Interval(261,280),  2L),
        (Interval(90,100),   3L), 
        (Interval(110,130),  3L),
        (Interval(150,151),  4L), 
        (Interval(151,190),  4L),
        (Interval(190,195),  5L), 
        (Interval(21,30),    5L),
        (Interval(197, 198), 6L), 
        (Interval(200,230),  7L), 
        (Interval(231,240),  7L),
        (Interval(250,260),  8L), 
        (Interval(71,80),    8L), 
    ]

    interval_end = 300

elif choice == "B":
    # initialize pseudo random generator: produces always the same numbers.
    random.seed(110270)   # must set the seed for randomness, otherwise system time
    #                     # is used which is no longer deterministic.
    interval_start = 0
    def make(start):
        size               = int(random.random() * 4) + 1
        target_state_index = long(random.random() * 10)
        return (Interval(start, start + size), target_state_index)

    tm0 = []
    for i in range(4000):
        x = make(interval_start)
        tm0.append(x)
        interval_start = x[0].end

    interval_end = interval_start

elif choice == "C":
    interval_start = 0
    interval_end   = -1
    # initialize pseudo random generator: produces always the same numbers.
    random.seed(110270)   # must set the seed for randomness, otherwise system time
    #                     # is used which is no longer deterministic.

    tm0 = []
    for i in range(1000):
        if random.random() > 0.75:
            interval_size      = int(random.random() * 3) + 1
            target_state_index = long(random.random() * 5)

            interval_end = interval_start + interval_size
            tm0.append((Interval(interval_start, interval_end), target_state_index))
            interval_start = interval_end
        else:
            target_state_index = long(random.random() * 5)

            for dummy in xrange(0, int(random.random() * 5) + 2):
                tm0.append((Interval(interval_start, interval_start + 1), target_state_index))
                interval_start += 1 + int(random.random() * 2)

tm = [ (interval, ["return %i;\n" % i]) for interval, i in tm0 ]
tm.sort(key=lambda x: x[0].begin)
target_state_index_list = sorted(list(set(long(i) for interval, i in tm0)))

# One for the 'terminal'
__label_db["$entry"](DoorID(index.get(), None))

function  = [ 
    "#define __quex_debug_state(X) /* empty */\n",
    "int transition(int input) {\n" 
]

# prev_end = -sys.maxint
#for interval, target in tm:
#    print "#it:", interval.begin, interval.end, target
#    prev_end = interval.end

transition_map_tool.fill_gaps(tm, ["return -1;"])

tm_txt = CppGenerator.code_action_map_plain(tm)
assert len(tm_txt) != 0

function.extend(tm_txt)

reload   = "%s: return (int)-1;\n" % address.get_label("$reload", -1)
function.append(reload)
drop_out = "%s: return (int)-1;\n" % address.get_label("$drop-out", -1)
function.append(drop_out)
function.append("\n}\n")

main_txt = """

/* From '.begin' the target map targets to '.target' until the next '.begin' is
 * reached.                                                                  */
typedef struct { int begin; int target; } entry_t;

#include <stdio.h>
int
main(int argc, char** argv) {
    const entry_t db[]      = {
$$ENTRY_LIST$$
    };
    const entry_t* db_last  = &db[sizeof(db)/sizeof(entry_t) - 1];
    const entry_t* iterator = &db[0];
    int            input    = -1;
    int            output   = -1;
    int            target   = -1;
    
    printf("No output is good output!\\n");
    for(iterator=&db[0]; iterator != db_last; ) {
        input  = iterator->begin;
        target = iterator->target;
        ++iterator;
        for(; input != iterator->begin; ++input) {
            output = transition(input);
            if( output != target ) {
                printf("input: 0x%06X; output: %i; expected: %i;   ERROR\\n",
                       (int)input, (int)output, (int)target);
                return 0;
            }
        }
    }
    printf("Intervals:  %i\\n", (int)(iterator - &db[0]));
    printf("Characters: %i\\n", (int)input);
    printf("Oll Korrekt\\n");
}
"""

# Prepare the main function
begin  = 0
target = transition_map_tool.get_target(tm0, begin)
if target is None: target = -1
entry_list = [ (begin, target) ]
for x in range(interval_end):
    new_target = transition_map_tool.get_target(tm0, x)
    if new_target is None: new_target = -1
    if new_target != target:
        target = new_target
        entry_list.append((x, target))
entry_list.append((interval_end, -1))
entry_list.append((0x1FFFF, -1))
 
expected_array = [ "        { 0x%06X, %i },\n" % (begin, target) for begin, target in entry_list ]


main_txt = main_txt.replace("$$ENTRY_LIST$$", "".join(expected_array))

txt = function + [ main_txt ]
Setup.language_db.REPLACE_INDENT(txt)

fh = open("test.c", "wb")
fh.write("".join(txt))
fh.close()
os.system("gcc test.c -o test")
os.system("./test")
os.remove("./test")
#os.remove("./test.c")





