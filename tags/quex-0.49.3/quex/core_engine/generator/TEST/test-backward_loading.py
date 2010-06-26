#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import generator_test

choice = generator_test.hwut_input("Buffer Reload: Backwards",
                                   "SAME;",
                                   ["Cpp-ASSERTS", "ANSI-C-ASSERTS"], 
                                   ["Cpp_StrangeStream"])

if choice.find("-ASSERTS") != -1: 
    choice     = choice.replace("-ASSERTS", "")
    ASSERT_str = "-DQUEX_OPTION_ASSERTS"
else: 
    ASSERT_str = ""

pattern_action_pair_list = [
    # keyword (needs to come before identifier, because otherwise they would be overruled by it.)
    ('"0xxxxxxx"/"a"/', "0xxxxxxx / a"), 
    # identifier
    ('[0a-z]{2}',       "IDENTIFIER"),
    # 
    ('[ \\t\\n]+',      "WHITESPACE")
]

#          |12456789|
test_str = "   0xxxxxxalola 0xxxxxxxa"


generator_test.do(pattern_action_pair_list, test_str, {}, Language=choice, 
                  QuexBufferSize=11, QuexBufferFallbackN=2, ShowBufferLoadsF=True,
                  AssertsActionvation_str=ASSERT_str)
    
