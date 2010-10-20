#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

from quex.output.cpp.token_id_maker import parse_token_id_file
from quex.lexer_mode                import token_id_db


if "--hwut-info" in sys.argv:
    print "User defined token id file: __parse_token_id_file"
    sys.exit(0)

CommentDelimiterList = [["//", "\n"], ["/*", "*/"]]
# Regular expression to find '#include <something>' and extract the 'something'
# in a 'group'. Note that '(' ')' cause the storage of parts of the match.
IncludeRE            = "#[ \t]*include[ \t]*[\"<]([^\">]+)[\">]"

def test(TokenIDFile, TokenPrefix):
    print "##-----------------------------------------------------------------"
    token_id_db.clear()
    parse_token_id_file(TokenIDFile, TokenPrefix, CommentDelimiterList, IncludeRE)
    for key, token_info in token_id_db.items():
        print "%s:%i: %s" % (token_info.file_name, token_info.line_n, key)

test("example.h",     "TKN_")
test("example-x.h",   "TKN_")
test("example-x-x.h", "TKN_")
