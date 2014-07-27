# PURPOSE:
#
# This is a helper file to keep the current list of command line options 
# up-to-date with the reported list of options in the documentation and 
# man-page.
#
# (1) Collect all command line options recognized in current version
#     of quex.
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])
import re

from quex.input.setup import SETUP_INFO


def get_option_db():
    result = {}
    for name, value in SETUP_INFO.iteritems():
        if name.find("XX_") == 0: continue # DEPRECATED
        elif type(value) != list: continue # derived setup option
        option_list, default = value
        result.update((option, default) for option in option_list)

    print "#odb:", sorted(result.keys())
    return result

option_db = get_option_db()

# Verify that every option is documented.
file_name        = os.environ["QUEX_PATH"] + "/doc/source/invocation/command-line/intro.txt"
command_line_doc = open(file_name).read()
for option in option_db:
    if command_line_doc.find(option) == -1:
        print "error: %s is not documented" % option

# Find things which are documented but do not exist
option_re = re.compile(" \-[_a-zA-Z\-0-9]+", re.UNICODE)
for line_i, line in enumerate(command_line_doc.split("\n")):
    if line.find("cmdoption::") == -1: continue
    for match in option_re.finditer(line):
        lexeme = match.group().strip()
        if lexeme in option_db: continue
        print "%s:%i:error: %s reported but does not exist" % \
              (file_name, line_i + 1, lexeme)
        print lexeme in option_db
