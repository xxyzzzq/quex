#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.setup
import quex.core                                as coder
import quex.core_engine.regular_expression.core as regex
import quex.core_engine.generator.core          as generator
from   quex.lexer_mode                 import Match, LexMode, ReferencedCodeFragment


if "--hwut-info" in sys.argv:
    print "Prepare Pattern Information for Code Generation"
    sys.exit(0)

pattern_action_pair_list = [
    # identifier
    ('[_a-zA-Z]+', "IDENTIFIER"),
    # number
    ('[ \\t\\n]+', "WHITESPACE")
]

mode = LexMode("TEST", "", 0)
i = -1
for pattern, action in pattern_action_pair_list:
    i += 1
    mode.add_match(pattern, 
                   ReferencedCodeFragment("std::cout << \"%s\" << std::endl;\n" % action, "", -1), 
                   regex.do(pattern, {}, -1))

# This is brutal!
quex.input.setup.setup.output_debug_f                = False
quex.input.setup.setup.begin_of_stream_code          = 0x19
quex.input.setup.setup.end_of_stream_code            = 0x1A
quex.input.setup.setup.no_dos_carriage_return_newline_f = True


inheritance_info, generator_input = coder.get_generator_input(mode)

print "/*\n" + inheritance_info + "*/\n"

for match_obj in mode.pattern_action_pairs().values():
    print match_obj

for action_info in generator_input:
    print action_info


