#! /usr/bin/env python
#
# The file 'command_line_options.py' in $QUEX_PATH/doc generates documentation
# for the command line options. This file double-checks whether the content
# of the generated files is consistent with the current setup.
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
    print "CHOICES: man, sphinx;"
    print "SAME;"
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
    "sphinx": "/doc/source/appendix/command-line/intro.rst",
    "man":    "/doc/manpage/quex.1",
}[sys.argv[1]]
marker = {
    "sphinx": "cmdoption::",
    "man":    ".B"
}[sys.argv[1]]

print "## Consider File:"
print "##    %s" % file_name

# Verify that every option is documented.
print "(*) Options which are not documented (no output is good output)"
command_line_doc = open(file_name).read()
count_n = 0
for option in option_db:
    if command_line_doc.find(option) == -1:
        print "error: %s is not documented" % option
    else:
        count_n += 1
print "Documented options %i out of %i existing options." % (count_n, len(option_db))

# Find things which are documented but do not exist
print "(*) Options which are reported, but are not available in application  (no output is good output)"
option_re = re.compile(" \-[_a-zA-Z\-0-9]+", re.UNICODE)
for line_i, line in enumerate(command_line_doc.splitlines()):
    if line.find(marker) == -1: continue
    for match in option_re.finditer(line):
        lexeme = match.group().strip()
        if lexeme in option_db: continue
        # Tolerate the '-bullet' marker in man pages
        if lexeme == "-bullet" and "man" in sys.argv: continue
        print "%s:%i:error: %s reported but does not exist" % \
              (file_name, line_i + 1, lexeme)
        print lexeme in option_db

