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
                                                   
from   quex.engine.state_machine.engine_state_machine_set import CharacterSetStateMachine
import quex.engine.analyzer.engine_supply_factory         as     engine
from   quex.engine.interval_handling                      import Interval, NumberSet
import quex.engine.generator.languages.core               as     languages
from   quex.engine.generator.base                         import do_analyzer
from   quex.engine.analyzer.door_id_address_label         import DoorID
import quex.engine.analyzer.core                          as     analyzer_generator
from   quex.engine.analyzer.door_id_address_label         import dial_db
import quex.engine.generator.state.transition.core        as     transition_block
from   quex.engine.analyzer.transition_map                import TransitionMap   
from   quex.blackboard                                    import setup as Setup, \
                                                                 E_MapImplementationType, \
                                                                 E_IncidenceIDs, \
                                                                 Lng
from   collections import defaultdict

Setup.language_db = languages.db["C++"]

dial_db.clear()

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
    tm.fill_gaps(E_IncidenceIDs.MATCH_FAILURE)

    iid_db = defaultdict(NumberSet)
    for interval, iid in tm:
        iid_db[iid].add_interval(interval)
    iid_map = [ (character_set, iid) for iid, character_set in iid_db.iteritems() ]
    return iid_map

def get_transition_function(iid_map, Codec):
    if Codec == "UTF8":
        Setup.buffer_codec_transformation_info = "utf8-state-split"
    else:
        Setup.buffer_codec_transformation_info = None

    cssm     = CharacterSetStateMachine(iid_map, MaintainLexemeF=False)
    analyzer = analyzer_generator.do(cssm.sm, engine.CHARACTER_COUNTER)
    tm_txt   = do_analyzer(analyzer)
    tm_txt   = Lng.GET_PLAIN_STRINGS(tm_txt)
    tm_txt.append("\n")
    label    = dial_db.get_label_by_door_id(DoorID.incidence(E_IncidenceIDs.MATCH_FAILURE))

    for character_set, iid in iid_map:
        tm_txt.append("%s return (int)%s;\n" % (Lng.LABEL(DoorID.incidence(iid)), iid))
    tm_txt.append("%s return (int)-1;\n" % Lng.LABEL(DoorID.drop_out(-1)))

    return "".join(tm_txt)

main_template = """
/* From '.begin' the target map targets to '.target' until the next '.begin' is
 * reached.                                                                  */
#include <quex/code_base/compatibility/stdint.h> 
#include <stdio.h>
#define QUEX_TYPE_CHARACTER              $$QUEX_TYPE_CHARACTER$$
#define __QUEX_OPTION_PLAIN_C
#define QUEX_NAMESPACE_MAIN_OPEN
#define QUEX_NAMESPACE_MAIN_CLOSE
#define QUEX_CONVERTER_CHAR_DEFi(X, Y)   convert_ ## X ## _to_ ## Y
#define QUEX_CONVERTER_CHAR_DEF(X, Y)    QUEX_CONVERTER_CHAR_DEFi(X, Y)
#define QUEX_CONVERTER_CHAR(X, Y)        QUEX_CONVERTER_CHAR_DEFi(X, Y)
#define QUEX_CONVERTER_STRING_DEFi(X, Y) convertstring_ ## X ## _to_ ## Y
#define QUEX_CONVERTER_STRING_DEF(X, Y)  QUEX_CONVERTER_STRING_DEFi(X, Y)
#define QUEX_CONVERTER_STRING(X, Y)      QUEX_CONVERTER_STRING_DEFi(X, Y)
#include <quex/code_base/converter_helper/from-utf32.i>

typedef struct {
    struct {
        QUEX_TYPE_CHARACTER*  _input_p;
        QUEX_TYPE_CHARACTER*  _lexeme_start_p;
    } buffer;
} MiniAnalyzer;

int transition(QUEX_TYPE_CHARACTER* buffer);

typedef struct { 
    uint32_t begin; 
    int      target; 
} entry_t;

int
main(int argc, char** argv) {
    const entry_t db[]      = {
$$ENTRY_LIST$$
    };
    const entry_t*       db_last  = &db[sizeof(db)/sizeof(entry_t) - 1];
    const entry_t*       iterator = &db[0];
    const entry_t*       next     = (void*)0;

    int                  output          = -1;
    int                  output_expected = -1;
    uint32_t             input;
    QUEX_TYPE_CHARACTER  buffer[8];
    
    printf("No output is good output!\\n");
    for(iterator=&db[0]; iterator != db_last; iterator = next) {
        input           = iterator->begin;
        output_expected = iterator->target;
        next            = iterator + 1;
        for(input  = iterator->begin; input != next->begin; ++input) {
            $$PREPARE_INPUT$$

            output = transition(&buffer[0]);

            if( output != output_expected ) {
                printf("input: 0x%06X; output: %i; expected: %i;   ERROR\\n",
                       (int)input, (int)output, (int)output_expected);
                return 0;
            }
        }
    }
    printf("Intervals:  %i\\n", (int)(iterator - &db[0]));
    printf("Characters: %i\\n", (int)input);
    printf("Oll Korrekt\\n");
}

int 
transition(QUEX_TYPE_CHARACTER* buffer)
{
    MiniAnalyzer         self;
    MiniAnalyzer*        me = &self;
    QUEX_TYPE_CHARACTER  input = 0;

    me->buffer._input_p = buffer;

    $$TRANSITION$$
}

"""
def get_main_function(tm0, TranstionTxt, Codec):
    def indent(Txt, N):
        return (" " * N) + (Txt.replace("\n", "\n" + (" " * N)))

    if Codec == "UTF8": qtc_str = "uint8_t"
    else:               qtc_str = "uint32_t"

    input_preperation = get_input_preparation(codec)

    entry_list = [ (0 if interval.begin < 0 else interval.begin, target) for interval, target in tm0 ]
    entry_list.append((tm0[-1][0].begin, -1))
    entry_list.append((0x1FFFF, -1))
    expected_array = [ "        { 0x%06X, %s },\n" % (begin, target) for begin, target in entry_list ]

    txt = main_template.replace("$$ENTRY_LIST$$", "".join(expected_array))
    txt = txt.replace("$$QUEX_TYPE_CHARACTER$$", qtc_str)
    txt = txt.replace("$$TRANSITION$$", indent(TranstionTxt, 12))
    txt = txt.replace("$$PREPARE_INPUT$$", input_preperation)

    txt = txt.replace("MATCH_FAILURE", "((int)-1)")
    return txt

def get_input_preparation(Codec):
    if Codec == "UTF8":
        txt = [
            "{\n"
            "    QUEX_TYPE_CHARACTER* buffer_p = &buffer[0];\n"
            "    const uint32_t*      input_p = &input;\n"
            "    convert_utf32_to_utf8(&input_p, &buffer_p);\n"
            "}\n"
        ]
    else:
        txt = [
            "buffer[0] = input;\n"
        ]
    return "".join("        %s" % line for line in txt)

iid_map           = prepare(tm0)
transition_txt    = get_transition_function(iid_map, codec)
txt               = get_main_function(tm0, transition_txt, codec)

Lng.REPLACE_INDENT(txt)

fh = open("test.c", "wb")
fh.write("".join(txt))
fh.close()
os.system("gcc -I$QUEX_PATH test.c -o test")
os.system("./test")
os.remove("./test")
#os.remove("./test.c")





