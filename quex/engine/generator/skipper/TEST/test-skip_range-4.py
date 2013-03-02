#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())
from helper import *

if "--hwut-info" in sys.argv:
    print "Skip-Range: Semi-Complete Delimiters, BufferSize = DelimiterLength + 2"
    print "CHOICES: 2, 3, 4, 5;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["1", "2", "3", "4", "5"]): 
    print "Delimiter length argument not acceptable, use --hwut-info"
    sys.exit(0)

Language = "Cpp"
DL = int(sys.argv[1])

if   DL == 2: SEP = ["*", "*/"]
elif DL == 3: SEP = ["*", "**", "**/"]
elif DL == 4: SEP = ["*", "**", "***", "***/"]
elif DL == 5: SEP = ["*", "**", "***", "****", "****/"]
else:
    print "Delimiter length argument '%s' not acceptable, use --hwut-info" % DL
    sys.exit(0)

QuexBufferSize = DL + 2

# SEP[-1] is the 'real' delimiter, SEP[:-1] are all but the complete one
end_sequence = map(ord, SEP[-1])

fragment = ""
for x in SEP:
    fragment += "o" + x

TestStr  = "abcdefg" + fragment + "hijklmnop" + fragment + "qrstuvw" + fragment + "xyz" + fragment + "ab"

compile_and_run(Language, create_range_skipper_code(Language, TestStr, end_sequence, QuexBufferSize, CommentTestStrF=True))

TestStr  = "abcdefg" + fragment + "hijklmnop" + fragment + "qrstuvw" + fragment + "xyz" + fragment + "ab"
TestStr  = fragment + "hijklmnop" + fragment + "qrstuvw" + fragment + "xyz" + fragment

compile_and_run(Language, create_range_skipper_code(Language, TestStr, end_sequence, QuexBufferSize, CommentTestStrF=True))

TestStr  = "abcdefg" + fragment + "hijklmnop" + fragment + "qrstuvw" + fragment + "xyz" + fragment + "ab"
TestStr  = fragment + "hijklmnop" + fragment + "qrstuvw" + fragment + "xyz" + fragment
TestStr  = "a" + fragment + "h" 

compile_and_run(Language, create_range_skipper_code(Language, TestStr, end_sequence, QuexBufferSize, CommentTestStrF=True))


