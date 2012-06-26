#! /usr/bin/env python
import sys
sys.path.append("../../../../")
import generator_test

choice = generator_test.hwut_input("Buffer Reload: No Backward Reload -- Precondition at Border",
                                   "SAME;",
                                   ["Cpp-ASSERTS", "ANSI-C-ASSERTS"])

if choice.find("-ASSERTS") != -1: 
    choice     = choice.replace("-ASSERTS", "")
    ASSERT_str = "-DQUEX_OPTION_ASSERTS"
else: 
    ASSERT_str = ""

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
generator_test.do(pattern_action_pair_list, test_str, {}, choice, 
                  QuexBufferSize=11, QuexBufferFallbackN=2, ShowBufferLoadsF=True,
                  AssertsActionvation_str=ASSERT_str)
    
