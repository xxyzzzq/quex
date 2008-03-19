#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.core                                as coder
import quex.core_engine.regular_expression.core as regex
import quex.core_engine.generator.core          as generator
from   quex.lexer_mode                 import Match, LexMode


if "--hwut-info" in sys.argv:
    print "Prepare Pattern Information for Code Generation"
    sys.exit(0)

def create_Match_object(match_info):
    # set inheritance level to something pseudo-random
    inheritance_level = len(match_info[0])

    return Match(match_info[0], 
                 "std::cout << \"%s\" << std::endl;\n" % match_info[1],
                 regex.do(match_info[0]), 0,
                 IL=inheritance_level) 

pattern_action_pair_list = [
    # identifier
    ('[_a-zA-Z]+', "IDENTIFIER"),
    # number
    ('[ \\t\\n]+', "WHITESPACE")
]

match_list = map(lambda x: create_Match_object(x), 
                 pattern_action_pair_list)

class pseudo_setup:
    def __init__(self):
        self.output_debug_f                = False
        self.begin_of_stream_code          = 0x19
        self.end_of_stream_code            = 0x1A
        self.no_dos_carriage_return_newline_f = True

Setup = pseudo_setup()

Mode = LexMode("TEST", "", 0)

inheritance_info, generator_input = coder.get_generator_input(Mode, match_list, Setup)

print "/*\n" + inheritance_info + "*/\n"

for match_obj in match_list:
    print match_obj


for action_info in generator_input:
    print action_info


