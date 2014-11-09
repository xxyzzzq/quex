#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.interval_handling              import Interval
import quex.engine.state_machine.transformation.utf16_state_split as trafo
from   quex.engine.state_machine.transformation.utf16_state_split import unicode_to_utf16

if "--hwut-info" in sys.argv:
    print "UTF16 State Split: Contigous Word Sequence Ranges"
    print "CHOICES: 1, 2, 3, 4, 5;"
    sys.exit(0)

def pretty_sequence(Value):
    txt = ""
    for word in unicode_to_utf16(Value):
        txt += "%04X." % word
    return txt
    
def test(Begin, End):
    X = Interval(Begin, End)
    print "-------------------------"
    print "Interval:     " + X.get_string(Option="hex")
    print "   .front --> " + pretty_sequence(X.begin)
    print "   .back  --> " + pretty_sequence(X.end - 1)
    print

    x0, list1 = trafo.get_contigous_intervals(X)
    print "Result:"
    print "   Interval < 0x10000:    ", 
    if x0 is not None: print "%s" % x0.get_string(Option="hex")
    else:          print "None"
    print "   Intervals >= 0x10000:  ",
    
    if list1 is None: print "None"
    else:
        print
        previous_end = list1[0].begin
        for interval in list1:
            print "      %s " % interval.get_string(Option="hex")

            # All sub intervals must be adjacent
            assert interval.begin == previous_end

            print "         .front --> " + pretty_sequence(interval.begin)
            print "         .back  --> " + pretty_sequence(interval.end - 1)
            previous_end = interval.end

        # The whole interval has been spanned
        assert list1[-1].end  == X.end

if "1" in sys.argv:
    begin = 0x0
    end   = 0xD800

elif "2" in sys.argv:
    begin = 0xE000
    end   = 0x10000

elif "3" in sys.argv:
    begin = 0xE000
    end   = 0x110000

elif "4" in sys.argv:
    test(0x04FF00, 0x04FFFE)
    test(0x04FF00, 0x04FFFF)
    test(0x04FF00, 0x050000)
    test(0x04FF00, 0x050001)
    test(0x04FF00, 0x050002)
    test(0x04FF00, 0x05FFFF)
    test(0x04FF00, 0x060000)
    test(0x04FF00, 0x060001)
    sys.exit()

elif "5" in sys.argv:
    test(0x10000, 0x10010)
    sys.exit()
    
test(begin,      begin + 1)
test(begin,      begin + 2)
test(begin + 1,  begin + 2)
test(end - 1,    end)
test(end - 2,    end)
test(end - 2,    end-1)
test(begin,      end)
test(begin + 1,  end - 1)

