#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   quex.engine.misc.interval_handling              import NumberSet, Interval
import quex.engine.state_machine.transformation.utf8_state_split as trafo

if "--hwut-info" in sys.argv:
    print "UTF8 State Split: Contigous Byte Sequence Ranges"
    print "CHOICES: 1, 2, 3, 4, 4b, misc;"
    sys.exit(0)

def pretty_sequence(Value):
    txt = ""
    for byte in trafo.unicode_to_utf8(Value):
        txt += "%02X." % byte
    return txt
    
def test(Begin, End):
    X = Interval(Begin, End)
    print "-------------------------"
    print "Interval:     " + X.get_string(Option="hex")
    print "   .front --> " + pretty_sequence(X.begin)
    print "   .back  --> " + pretty_sequence(X.end - 1)
    print

    L = len(trafo.unicode_to_utf8(X.begin))
    assert L == len(trafo.unicode_to_utf8(X.end - 1))
    result, p = trafo.split_interval_into_contigous_byte_sequence_range(X, L)
    print "Result:"
    previous_end = X.begin
    for interval in result:
        print "      %s " % interval.get_string(Option="hex")

        # All sub intervals must be adjacent
        assert interval.begin == previous_end

        print "         .front --> " + pretty_sequence(interval.begin)
        print "         .back  --> " + pretty_sequence(interval.end - 1)
        previous_end = interval.end

    # The whole interval has been spanned
    assert result[0].begin == X.begin
    assert result[-1].end  == X.end

# 0x00000000 - 0x0000007F: 1 byte  - 0xxxxxxx
# 0x00000080 - 0x000007FF: 2 bytes - 110xxxxx 10xxxxxx
# 0x00000800 - 0x0000FFFF: 3 bytes - 1110xxxx 10xxxxxx 10xxxxxx
# 0x00010000 - 0x001FFFFF: 4 bytes - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
# 0x00200000 - 0x03FFFFFF: 5 bytes ... 
# 0x04000000 - 0x7FFFFFFF: 
if "1" in sys.argv:
    begin = 0x00
    end   = 0x80

elif "2" in sys.argv:
    begin = 0x80
    end   = 0x800

elif "3" in sys.argv:
    begin = 0x800
    end   = 0x10000

elif "4" in sys.argv:
    begin = 0x10000
    end   = 0x110000

elif "4b" in sys.argv:
    test(0x40200, 0x40600)
    test(0x4019E, 0x40591)
    test(0x40121, 0x40171)
    test(0x40121, 0x41300)
    test(0x40121, 0xA1300)
    sys.exit()

elif "misc" in sys.argv:
    test(0x800, 0x810)
    sys.exit()
    
test(begin,      begin + 1)
test(begin,      begin + 2)
test(begin + 1,  begin + 2)
test(end - 1,    end)
test(end - 2,    end)
test(end - 2,    end-1)
test(begin,      end)
test(begin + 1,  end - 1)

