#! /usr/bin/env python
import sys
import generator_test
from generator_test import action

choice = generator_test.hwut_input("Pre- and Post- Conditions: Priorities", "SAME;")

def test(Info, PatternActionPairList, TestStr, Choice):
    print "=========================================================================="
    print info
    generator_test.do(PatternActionPairList, TestStr, {}, Choice)    

#=====================================================================================
pattern_action_pair_list = [
    ('"x"',        "[A-Z]"),
    ('[A-Z]',      "OTHER"),
    ('"x"/"Z"',    "X / Z"),
    ('"A"/"x"/',   "A / X /"),
    ('[ ]',        "WHITESPACE"),
    ('"x"/[YZ]',   "X / [YZ]"),
]

info = \
"""
(1) Same Length of Core Pattern
    -- 'x' preceedes 'A/x/' thus 'A/x/' shall never trigger
    -- 'x' preceedes 'x/Z', but 'x/Z' is a post conditioned pattern
       => 'x/Z' succeeds.
    -- 'x/Z' preceeds 'x/[YZ]', thus for 'xZ' the second shall never match.
"""

test_str = "AxZ Ax xY"

test(info, pattern_action_pair_list, test_str, choice)


#=====================================================================================
pattern_action_pair_list = [
    ('[A-Z]',      "[A-Z]"),
    ('"xZ"',       "XZ"),
    ('"x"/[ZY]"',  "X / [ZY]"),
    ('"x"/"Y"',    "X / Y"),
]

info = \
"""
(2) Precedence of Post Condition
    -- 'xZ' preceeds 'x/[YZ]'.
    -- 'x/[YZ]' preceeds 'x/Y', the second shall never match.
"""

test_str = "xZxY"

test(info, pattern_action_pair_list, test_str, choice)


#=====================================================================================
pattern_action_pair_list = [
    ('[a-zA-Z]', "OTHER"),
    ('A/xy/',    "A / XY /"),
    ('"xyz"',    "XYZ"),
    ('xy/z+',    "XY / Z+"),
]

info = \
"""
(3) Length Decides (Independent of Pre or Post Condition
    -- 'xyz' is outruled by 'xy/z+'.
    -- The core pattern of 'A/xy' is shorter than 'xy/z+' thus
       in case of 'xyz' the second one shall trigger.
    -- ...
"""

# test_str = "AxyAxyzAxyzzxyz"
test_str = "AxyzzAxyAxyz"

test(info, pattern_action_pair_list, test_str, choice)


