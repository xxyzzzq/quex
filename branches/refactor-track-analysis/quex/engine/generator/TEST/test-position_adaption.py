#! /usr/bin/env python
import sys
import os
sys.path.append("../../../../")
import generator_test

choice = generator_test.hwut_input("Buffer Reload: Forward Position Adaption", 
                                   "SAME;",
                                   ["Cpp-ASSERTS", "ANSI-C-ASSERTS"])

if choice.find("-ASSERTS") != -1: 
    choice     = choice.replace("-ASSERTS", "")
    ASSERT_str = "-DQUEX_OPTION_ASSERTS"
else: 
    ASSERT_str = ""


pattern_action_pair_list = [
    # keyword (needs to come before identifier, because otherwise they would be overruled by it.)
    ('"X"/"XXXXXXXXX"', "1 X / ... X"), 
    ('"XX"/"XXXXXXXY"', "2 X / ... Y"), 
    ('"XXX"/"XXXXXXZ"', "3 X / ... Z"), 
    ('"XXXX"/"XXXXXA"', "4 X / ... A"), 
    # identifier
    ('[_a-zA-Z][_a-zA-Z0-9]*',   "IDENTIFIER"),
    # 
    ('[ \\t\\n]+',               "WHITESPACE")
]

# NOTE: Buffer Length in generator_test.py = 15 
#       => number of X = 10, so that at lease one buffer load has to occur
test_str = """
XXXXXXXXXX
AAAAAAAAAAA
XXXXXXXXXY
AAAAAAAAAA
XXXXXXXXXZ
AAAAAAAAA
XXXXXXXXXA
AAAAAAAA
XXXXXXXXXX
AAAAAAA
XXXXXXXXXY
AAAAAA
XXXXXXXXXZ
AAAAA
XXXXXXXXXA
AAAA
XXXXXXXXXX
AAA
XXXXXXXXXY
AA
XXXXXXXXXZ
A
XXXXXXXXXA
"""

generator_test.do(pattern_action_pair_list, test_str, {}, choice,
                  AssertsActionvation_str=ASSERT_str)
    
