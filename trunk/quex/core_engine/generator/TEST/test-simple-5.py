#! /usr/bin/env python
import sys
import generator_test

choice = generator_test.hwut_input("Simple: Keywords 'for', 'forest', 'forester', and 'formidable'", "SAME;")

pattern_action_pair_list = [
    # pre-conditioned expressions need to preceed same (non-preoconditioned) expressions,
    # otherwise, the un-conditional expressions gain precedence and the un-conditional
    # pattern is never matched.
    ('[a-eg-z]+',     "IDENTIFIER"),
    ('" "+',       "WHITESPACE"),
    ('for',        "FOR"),
    ('forest',     "FOREST"),
    ('forester',   "FORESTER"),
    ('formidable', "FORMIDABLE"),
]

test_str = "for forester forest formidable forever foresmic foresti foresteri formidablek formidabl"

generator_test.do(pattern_action_pair_list, test_str, {}, choice)    
