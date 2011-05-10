#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])

from   StringIO            import StringIO
from   quex.engine.misc.file_in import read_integer



if "--hwut-info" in sys.argv:
    print "Integer conversion: read_integer(...)"
    print "CHOICES: hex, octal, decimal, binary, roman, misc;"
    sys.exit(0)

def test(Input, Cmp=None):
    print "%s%s --> " % (Input, " " * (10 - len(Input))),
    try:
        output = read_integer(StringIO(Input))
        print output,
        if Cmp is None: print
        else:           print Cmp == output
    except:
        pass

if "misc" in sys.argv:
    test("  Frank")
    test("  0x")
    test("0x")
    test("0b")
    test("0o")
    test("0r")
    test("0x.")
    test("0b.")
    test("0o.")
    test("0r.")
    test("0.1")
    test("0x4.")
    test("0b10.")
    test("0o77.")
    test("0rXII")
    test("0")

elif "hex" in sys.argv:
    # Check that all digits are recognized
    test("0x12340",  int("12340", 16))
    test("0x56789",  int("56789", 16))
    test("0xABCDEF", int("ABCDEF", 16))
    # Disallowed .. 
    test("0xG")
    # Check that redundant dots dont mess
    test("0x.C0FFEE.BABA",  int("C0FFEEBABA", 16))
    test("0x0", 0)

elif "octal" in sys.argv:
    # Check that all digits are recognized
    test("0o12340", int("12340", 8))
    test("0o567",   int("567",   8))
    # Disallowed .. 
    test("0o8")
    # Check that redundant dots dont mess
    test("0o0", 0)

elif "binary" in sys.argv:
    # Check that all digits are recognized
    test("0b0110100010101001",    int("0110100010101001",    2))
    test("0b1010101010101010101", int("1010101010101010101", 2))
    # Disallowed .. 
    test("0b2")
    test("0b0000.0000", 0)
    test("0b1.", 1)

elif "roman" in sys.argv:
    # Check that all digits are recognized
    test("0rMDCLXVI",   1666)
    test("0rMMMMDCCXI", 4711)
    test("0rMXXIV",     1024)
    test("0rMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMDXXXVI", 65536)
    # Disallowed .. 
    test("0rG")
    test("0rI", 1)
    test("0rX", 10)

elif "decimal" in sys.argv:
    # Check that all digits are recognized
    test("0x12340",  int("12340", 10))
    test("0x56789",  int("56789", 10))
    # Disallowed
    test("A")
    # Check that dots are not allowed
    test("10.20")
