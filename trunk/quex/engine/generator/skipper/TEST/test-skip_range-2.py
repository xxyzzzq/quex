#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())
from helper import *

if "--hwut-info" in sys.argv:
    print "Skip-Range: Varrying DelimiterLength, Large Buffer"
    print "CHOICES: DL=1, DL=2, DL=3, DL=4;"
    print "SAME;"
    sys.exit(0)

if len(sys.argv) < 2 or not (sys.argv[1] in ["DL=1", "DL=2", "DL=3", "DL=4"]): 
    print "Delimiter length argument not acceptable, use --hwut-info"
    sys.exit(0)

Language = "Cpp"
DL = sys.argv[1]
if   DL == "DL=1": SEP = "*"
elif DL == "DL=2": SEP = "*/"
elif DL == "DL=3": SEP = "*/*"
elif DL == "DL=4": SEP = "*/*/"
else:
    print "Delimiter length argument '%s' not acceptable, use --hwut-info" % DL
    sys.exit(0)

end_sequence = map(ord, SEP)

TestStr  = "abcdefg" + SEP + "hijklmnop" + SEP + "qrstuvw" + SEP + "xyz" + SEP + "ok"

compile_and_run(Language, create_range_skipper_code(Language, TestStr, end_sequence, CommentTestStrF=True))

TestStr  = SEP + "hijklmnop" + SEP + "qrstuvw" + SEP + "xyz" + SEP

compile_and_run(Language, create_range_skipper_code(Language, TestStr, end_sequence, CommentTestStrF=True))

TestStr  = "a" + SEP + "h" + SEP + SEP + SEP

compile_and_run(Language, create_range_skipper_code(Language, TestStr, end_sequence, CommentTestStrF=True))


