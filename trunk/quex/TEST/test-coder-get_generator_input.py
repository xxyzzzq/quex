#! /usr/bin/env python

import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

import quex.input.setup
import quex.core                                as coder
import quex.input.regular_expression.engine as regex
import quex.engine.generator.core          as generator
from   quex.lexer_mode                          import ModeDescription, Mode
from   quex.engine.generator.action_info   import CodeFragment


if "--hwut-info" in sys.argv:
    print "Prepare Pattern Information for Code Generation"
    sys.exit(0)

pattern_action_pair_list = [
    # identifier
    ('[_a-zA-Z]+', "IDENTIFIER"),
    # number
    ('[ \\t\\n]+', "WHITESPACE")
]

mode_descr = ModeDescription("TEST", "", 0)
i = -1
for pattern, action in pattern_action_pair_list:
    i += 1
    mode_descr.add_match(pattern, 
                   CodeFragment("std::cout << \"%s\" << std::endl;\n" % action), 
                   regex.do(pattern, {}))

# This is brutal!
quex.input.setup.setup.output_debug_f                = False
quex.input.setup.setup.begin_of_stream_code          = 0x19
quex.input.setup.setup.end_of_stream_code            = 0x1A
quex.input.setup.setup.dos_carriage_return_newline_f = False


mode = Mode(mode_descr)
generator_input  = coder.get_generator_input(mode, False)
inheritance_info = mode.get_documentation()

print "/*\n" + inheritance_info + "*/\n"

for match_obj in mode.get_pattern_action_pair_list():
    print match_obj

for action_info in generator_input:
    print action_info


