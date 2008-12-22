#! /usr/bin/env python
import sys
import os
sys.path.append("../../../../")
import generator_test

if "--hwut-info" in sys.argv:
    print "Buffer Reload: No Backward Reload -- Precondition at Border"
    print "CHOICES: Cpp_ASSERTS, Cpp, ANSI-C-ASSERTS, ANSI-C, Cpp_StrangeStream;"
    print "SAME;"
    sys.exit(0)

if sys.argv[1].find("ASSERTS") != -1: ASSERT_str = "-DQUEX_OPTION_ASSERTS"
else:                                 ASSERT_str = ""
if sys.argv[1].find("ANSI-C") != -1: BufferType = "ANSI-C"
else:                                BufferType = "Cpp"

pattern_action_pair_list = [
    # keyword (needs to come before identifier, because otherwise they would be overruled by it.)
    ('"0xxxxx"/"a"/', "0xxxxx / a"), 
    # identifier
    ('[0a-z]{2}',     "IDENTIFIER"),
    # 
    ('[ \\t\\n]+',    "WHITESPACE")
]


print "## NOTE: The following setup guides the lexer into a buffer reload right after"
print "##       the pre-conditions. No buffer reload backwards is to appear!"
test_str = "   0xxxxxa lola"
generator_test.do(pattern_action_pair_list, test_str, {}, BufferType, 
                  QuexBufferSize=11, QuexBufferFallbackN=2, ShowBufferLoadsF=True,
                  AssertsActionvation_str=ASSERT_str)
    
