#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
import generator_test

if "--hwut-info" in sys.argv:
    print "Buffer Reload: Backwards;"
    print "CHOICES: No_NDEBUG, NDEBUG;"
    print "SAME;"
    sys.exit(0)

if "NDEBUG" in sys.argv:
    NDEBUG_compiler_str = "-DNDEBUG"
else:
    NDEBUG_compiler_str = ""


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
generator_test.do(pattern_action_pair_list, test_str, {}, BufferType="QuexBuffer", 
                  QuexBufferSize=11, QuexBufferFallbackN=2, ShowBufferLoadsF=True,
                  NDEBUG_str=NDEBUG_compiler_str)
    
