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
                                                   
from   quex.engine.interval_handling               import Interval
from   quex.engine.generator.base                  import LoopGenerator
import quex.engine.generator.languages.core        as     languages
import quex.engine.generator.languages.address     as     address
import quex.engine.generator.state.transition.core as     transition_block
from   quex.engine.analyzer.transition_map         import TransitionMap   
from   quex.blackboard                             import setup as Setup, E_MapImplementationType

Setup.language_db = languages.db["C"]              
LanguageDB        = Setup.language_db

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

# initialize pseudo random generator: produces always the same numbers.
random.seed(110270)   # must set the seed for randomness, otherwise system time
#                     # is used which is no longer deterministic.

if choice == "A":
    tm0 = TransitionMap.from_iterable([
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
    ])

    interval_end = 300

elif choice == "B":
    def make(start):
        size               = int(random.random() * 4) + 1
        target_state_index = long(random.random() * 10)
        return (Interval(start, start + size), target_state_index)

    tm0            = TransitionMap()
    interval_begin = 0
    for i in range(4000):
        tm0.append(make(interval_begin))
        interval_begin = tm0[-1][0].end

    interval_end = interval_begin

elif choice == "C":
    def make(start, size=None):
        if size is None:
            size = int(random.random() * 3) + 1
        target_state_index = long(random.random() * 5)
        return (Interval(start, start + size), target_state_index)

    tm0            = TransitionMap()
    interval_begin = 0
    for i in range(3000):
        if random.random() > 0.75:
            tm0.append(make(interval_begin))
            interval_begin = tm0[-1][0].end
        else:
            for dummy in xrange(0, int(random.random() * 5) + 2):
                tm0.append(make(interval_begin, size=1))
                interval_begin = tm0[-1][0].end + int(random.random() * 2)

    interval_end = interval_begin

def prepare(tm):
    tm.sort()
    target_state_index_list = sorted(list(set(long(i) for interval, i in tm)))

    tm.fill_gaps(-1)
    return TransitionMap.from_iterable(tm, lambda i: ["return %i;\n" % i])

def get_transition_function(tm, Codec):
    if codec != "UTF8":
        tm_txt = LoopGenerator.code_action_map_plain(tm)
        assert len(tm_txt) != 0

        header = \
            "#define __quex_debug_state(X) /* empty */\n" \
            "int transition(int input) {\n" 

        transition_txt = \
            "output = transition(input);"

        variable_txt = \
            "int32_t        input    = -1;\n" \
            "int32_t        output   = -1;\n"

    else:
        Setup.buffer_codec_transformation_info = "utf8-state-split"
        tm_txt = LoopGenerator.code_action_state_machine(tm, None, None)
        tm_txt.append("%s return (int)-1;\n" % Label.acceptance(E_AcceptanceIDs.FAILURE)
        tm_txt = LanguageDB.GET_PLAIN_STRINGS(tm_txt)
        LoopGenerator.replace_iterator_name(tm_txt, "input_p", E_MapImplementationType.STATE_MACHINE)

        header = \
            "#define __QUEX_OPTION_PLAIN_C\n"                                    \
            "#define QUEX_NAMESPACE_MAIN_OPEN\n"                                \
            "#define QUEX_NAMESPACE_MAIN_CLOSE\n"                                \
            "#define QUEX_CONVERTER_CHAR_DEFi(X, Y) convert_ ## X ## _to_ ## Y\n" \
            "#define QUEX_CONVERTER_CHAR_DEF(X, Y)  QUEX_CONVERTER_CHAR_DEFi(X, Y)\n" \
            "#define QUEX_CONVERTER_CHAR(X, Y)      QUEX_CONVERTER_CHAR_DEFi(X, Y)\n" \
            "#define QUEX_CONVERTER_STRING_DEFi(X, Y) convertstring_ ## X ## _to_ ## Y\n" \
            "#define QUEX_CONVERTER_STRING_DEF(X, Y)  QUEX_CONVERTER_STRING_DEFi(X, Y)\n" \
            "#define QUEX_CONVERTER_STRING(X, Y)      QUEX_CONVERTER_STRING_DEFi(X, Y)\n" \
            "#include <quex/code_base/converter_helper/from-utf32.i>\n"          \
            "int transition(uint8_t* input_p) {\n"                               \
            "    uint8_t input = (uint8_t)-1;\n"
        
        transition_txt = \
            "utf32_p = &input;\n"                          \
            "utf8_p  = &utf8_array[0];\n"                 \
            "convert_utf32_to_utf8(&utf32_p, &utf8_p);\n" \
            "output  = transition(&utf8_array[0]);"

        variable_txt = \
            "uint32_t        input         = 0;\n" \
            "const uint32_t* utf32_p       = (void*)0;\n" \
            "uint8_t         utf8_array[8] = {};\n" \
            "uint8_t*        utf8_p        = (void*)0;\n" \
            "int32_t         output        = -1;\n"


    reload   = "%s: return (int)-1;\n" % address.get_label("$reload", -1)
    drop_out = "%s: return (int)-1;\n" % address.get_label("$drop-out", -1)

    txt = []
    txt.extend(header)
    txt.extend(tm_txt)
    txt.append(reload)
    txt.append(drop_out)
    txt.append("\n}\n")

    return txt, transition_txt, variable_txt

main_template = """
/* From '.begin' the target map targets to '.target' until the next '.begin' is
 * reached.                                                                  */
typedef struct { int begin; int target; } entry_t;

#include <inttypes.h> 
#include <stdio.h>
int
main(int argc, char** argv) {
    const entry_t db[]      = {
$$ENTRY_LIST$$
    };
    const entry_t* db_last  = &db[sizeof(db)/sizeof(entry_t) - 1];
    const entry_t* iterator = &db[0];
$$VARIABLES$$
    int            target   = -1;
    
    printf("No output is good output!\\n");
    for(iterator=&db[0]; iterator != db_last; ) {
        input  = iterator->begin;
        target = iterator->target;
        ++iterator;
        for(; input != iterator->begin; ++input) {
$$TRANSITION$$
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
def get_main_function(tm0, VariableTxt, TranstionTxt):
    def indent(Txt, N):
        return (" " * N) + (Txt.replace("\n", "\n" + (" " * N)))

    entry_list = [ (0 if interval.begin < 0 else interval.begin, target) for interval, target in tm0 ]
    entry_list.append((tm0[-1][0].begin, -1))
    entry_list.append((0x1FFFF, -1))
    expected_array = [ "        { 0x%06X, %i },\n" % (begin, target) for begin, target in entry_list ]

    txt = main_template.replace("$$ENTRY_LIST$$", "".join(expected_array))
    txt = txt.replace("$$VARIABLES$$", indent(VariableTxt, 4))
    txt = txt.replace("$$TRANSITION$$", indent(TranstionTxt, 12))
    return txt

tm           = prepare(tm0)
function_txt, \
transition_txt, \
variable_txt = get_transition_function(tm, codec)
main_txt     = get_main_function(tm0, variable_txt, transition_txt)

txt = function_txt + [ main_txt ]
Setup.language_db.REPLACE_INDENT(txt)

fh = open("test.c", "wb")
fh.write("".join(txt))
fh.close()
os.system("gcc -I$QUEX_PATH test.c -o test")
os.system("./test")
os.remove("./test")
#os.remove("./test.c")





