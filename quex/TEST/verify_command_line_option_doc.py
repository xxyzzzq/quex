#! /usr/bin/env python
#
# Check whether the documentation of the command line options in sphinx
# and man page are up-to-date and consistent.
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])
import re

from quex.input.setup import SETUP_INFO

if "--hwut-info" in sys.argv:
    print "Command Line Option Documentation;"
    print "CHOICES: man, shinx;"
    sys.exit()

def get_option_db():
    result = {}
    for name, value in SETUP_INFO.iteritems():
        if name.find("XX_") == 0: continue # DEPRECATED
        elif type(value) != list: continue # derived setup option
        option_list, default = value
        result.update((option, default) for option in option_list)

    return result

option_db = get_option_db()

file_name = os.environ["QUEX_PATH"] + {
    "sphinx": "/doc/source/invocation/command-line/intro.txt",
    "man":    "/doc/man_page/quex.1",
}[sys.argv[1]]
marker = {
    "sphinx": "cmdoption::",
    "man":    ".SP"
}[sys.argv[1]]

# Verify that every option is documented.
command_line_doc = open(file_name).read()
for option in option_db:
    if command_line_doc.find(option) == -1:
        print "error: %s is not documented" % option

# Find things which are documented but do not exist
option_re = re.compile(" \-[_a-zA-Z\-0-9]+", re.UNICODE)
for line_i, line in enumerate(command_line_doc.split("\n")):
    if line.find(marker) == -1: continue
    for match in option_re.finditer(line):
        lexeme = match.group().strip()
        if lexeme in option_db: continue
        print "%s:%i:error: %s reported but does not exist" % \
              (file_name, line_i + 1, lexeme)
        print lexeme in option_db
