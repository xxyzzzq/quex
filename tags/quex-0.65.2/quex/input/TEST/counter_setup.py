#! /usr/bin/env python
import sys
import os
sys.path.append(os.environ["QUEX_PATH"])

from StringIO import StringIO

import quex.input.files.counter as counter
from   quex.engine.misc.file_in import EndOfStreamException, error_msg, error_eof
from   quex.blackboard import setup as Setup

Setup.buffer_codec_prepare("unicode")

if "--hwut-info" in sys.argv:
    print "Parse Counter Setup;"
    print "CHOICES: basic, twice, intersection, intersection-2, non-numeric;"
    sys.exit()

# choice = sys.argv[1]
count_n = 0
def test(Text):
    global count_n
    count_n += 1

    if Text.find("\n") == -1:
        print "(%i) |%s|\n" % (count_n, Text)
    else:
        print "(%i)\n::\n%s\n::\n" % (count_n, Text)

    sh      = StringIO(Text)
    sh.name = "test_string"

    descr = None
    # descr = counter.parse_line_column_counter(sh)
    try:    
        descr = counter.parse_line_column_counter(sh)
        pass

    except EndOfStreamException:
        error_msg("End of file reached while parsing 'counter' section.", sh, DontExitF=True, WarningF=False)

    except:
        print "Exception!"

    if descr is not None: print descr.count_command_map
    print

if "basic" in sys.argv:

    test(">")
    test("[\\v\\a]")
    test("[\\v\\a] >")
    test("[\\v\\a] => grid")
    test("[\\v\\a] => trid")
    test("[\\v\\a] => grid>")
    test("[\\v\\a] => grid 4;>")
    test("[\\v\\a] => space;>")
    test("[\\v\\a] => space 0rXVI;>")
    test("[\\v\\a] => newline;>")
    test("[\\v\\a] => space;\n[\\t] => grid 10;")
    test("[\\v\\a] => space;\n[\\t] => grid 10;>")
    test("[\\n]    => space;>")
    test("x        => newline; [\\n]    => space 2;>")

elif "twice" in sys.argv:
    test("[\\v\\a] => space 10;\n[\\t] => space 10; \\else => space 66;>")
    test("[\\v\\a] => grid 10;\n[\\t] => grid 10; \\else => space 66;>")
    test("[\\v\\a] => newline;\n[\\t] => newline; \\else => space 66;>")

elif "intersection" in sys.argv:
    test("[abc] => space 1;\n[cde] => space 2;>")
    test("[abc] => space 1;\n[cde]  => grid  4;>")
    test("[abc] => space 10;\n[cde] => newline;>")

    test("[abc] => grid 10;\n[cde] => grid 1;>")
    test("[abc] => grid 10;\n[cde] => space 1;>")
    test("[abc] => grid 10;\n[cde] => newline;>")

    test("[abc] => newline 1;\n[cde] => newline 5;>")
    test("[abc] => newline;\n[cde] => grid  10;>")
    test("[abc] => newline;\n[cde] => space;>")


elif "intersection-2" in sys.argv:

    test("c+ => newline;\n[ce] => space;>")
    test("e+ => newline;\n[be] => space;>")
    test("a? => newline;\n[ce] => space;>")
    test("ae* => newline;\n[ce] => space;>")
    test("a => newline;\nc => space;>")

elif "non-numeric" in sys.argv:
    test("[\\v\\a] => grid variable;>")
    test("[\\v\\a] => grid variable kongo;>")
    test("[\\v\\a] => space variable2;>")
    test("[\\v\\a] => space variable 2;>")
    test(">")
    test("/* empty will do */>")

elif "bad-keyword" in sys.argv:
    test("[abc] => suppressor;>")
    test("[abc] => bad;>")
