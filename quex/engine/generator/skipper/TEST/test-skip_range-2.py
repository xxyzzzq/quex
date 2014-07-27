#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.getcwd())
from helper import *

if "--hwut-info" in sys.argv:
    print "Skip-Range: Varrying DelimiterLength, Large Buffer"
    print "CHOICES: DL=1, DL=2, DL=3, DL=4;"
    #print "SAME;"
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

BS = len(SEP) + 2

def make(Language, CloserStr, BufferSize):
    code = create_range_skipper_code(Language, "", CloserStr, BufferSize, CommentTestStrF=True)
    exe_name, tmp_file_name = compile(Language, code)
    return exe_name, tmp_file_name

def core(Executable, BufferSize, TestStr):
    fh = open("test.txt", "wb")
    fh.write(TestStr)
    fh.close()
    run_this("./%s test.txt %i" % (Executable, BufferSize))
    os.remove("test.txt")

exe_name, tmp_file = make("ANSI-C-from-file", map(ord, SEP), BS)

core(exe_name, BS, 
     "abcdefg" + SEP + "hijklmnop" + SEP + "qrstuvw" + SEP + "xyz" + SEP + "ok")
core(exe_name, BS, 
     SEP + "hijklmnop" + SEP + "qrstuvw" + SEP + "xyz" + SEP)

core(exe_name, BS, 
     "a" + SEP + "h" + SEP + SEP + SEP)

if DL != "DL=1":
    Q = ""
    for i in xrange(1, len(SEP)+1):
        Q += "o" + SEP[:i]
    BS = len(Q) + 2

    core(exe_name, BS, 
         "abcdefg" + Q + "hijklmnop" + Q + "qrstuvw" + Q + "xyz" + Q + "ab")
    core(exe_name, BS, 
         Q + "hijklmnop" + Q + "qrstuvw" + Q + "xyz" + Q)
    core(exe_name, BS, 
         "a" + Q + "h")



