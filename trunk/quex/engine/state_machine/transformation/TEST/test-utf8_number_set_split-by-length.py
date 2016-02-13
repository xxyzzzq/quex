#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.misc.interval_handling              import NumberSet, Interval
import quex.engine.state_machine.transformation.utf8_state_split as trafo

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Intervals"
    print "CHOICES: 1, 2, Overlap1, Overlap2;"
    sys.exit(0)

def pretty_sequence(Value):
    txt = ""
    for byte in trafo.unicode_to_utf8(Value):
        txt += "%02X." % byte
    return txt
    
def test(X):
    assert X.__class__.__name__ == "Interval"
    print "-------------------------"
    print "Interval:     " + X.get_string(Option="hex")
    print "   .front --> " + pretty_sequence(X.begin)
    print "   .back  --> " + pretty_sequence(X.end - 1)
    print

    result = trafo._split_by_transformed_sequence_length(X)
    print "Result:"
    for n, interval in result.items():
        print "      SubInterval (bytes=%i): %s " % (n, interval.get_string(Option="hex"))
        print "         .front --> " + pretty_sequence(interval.begin)
        print "         .back  --> " + pretty_sequence(interval.end - 1)

# 0x00000000 - 0x0000007F: 1 byte  - 0xxxxxxx
# 0x00000080 - 0x000007FF: 2 bytes - 110xxxxx 10xxxxxx
# 0x00000800 - 0x0000FFFF: 3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
# 0x00010000 - 0x001FFFFF: 4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
# 0x00200000 - 0x03FFFFFF: 5 bytes ... 
# 0x04000000 - 0x7FFFFFFF: 
if "1" in sys.argv:
    test(Interval(0x0,     0x1))
    test(Interval(0x7F,    0x80))
    test(Interval(0x80,    0x81))
    test(Interval(0x7FF,   0x800))
    test(Interval(0x800,   0x801))
    test(Interval(0xFFFF,  0x10000))
    test(Interval(0x10000, 0x10001))
    test(Interval(0x10FFFF, 0x110000))

elif "2" in sys.argv:
    test(Interval(0x0,     0x2))
    test(Interval(0x7F,    0x81))
    test(Interval(0x7FF,   0x801))
    test(Interval(0xFFFF,  0x10001))
    test(Interval(0x10FFFE, 0x110000))

elif "Overlap1" in sys.argv:
    test(Interval(0x0,     0x80))     #  [0-7F]
    test(Interval(0x0,     0x81))     #  [0-7F]+

    test(Interval(0x80,    0x800))    #  [80-7FF]
    test(Interval(0x7F,    0x800))    # -[80-7FF]
    test(Interval(0x80,    0x801))    #  [80-7FF]+
    test(Interval(0x7F,    0x801))    # -[80-7FF]+

    test(Interval(0x800,   0x10000))  #  [800-FFFF]
    test(Interval(0x7FF,   0x10000))  # -[800-FFFF]
    test(Interval(0x800,   0x10001))  #  [800-FFFF]+
    test(Interval(0x7FF,   0x10001))  # -[800-FFFF]+

    test(Interval(0x10000,  0x11000)) #  [10000-10FFFF]
    test(Interval(0xFFFF,   0x11000)) # -[10000-10FFFF]
    test(Interval(0x10000,  0x11001)) #  [10000-10FFFF]+
    test(Interval(0xFFFF,   0x11001)) # -[10000-10FFFF]+

elif "Overlap2" in sys.argv:
    test(Interval(0x0, 0x800))
    test(Interval(0x0, 0x10000))
    test(Interval(0x80, 0x10000))
    test(Interval(0x80, 0x110000))
    test(Interval(0x0, 0x110000))
