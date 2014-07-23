#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

from   quex.output.cpp.token_id_maker import parse_token_id_file
from   quex.blackboard                import token_id_db
import quex.input.command_line.core   as     command_line


if "--hwut-info" in sys.argv:
    print "User defined token id file: __parse_token_id_file"
    print "HAPPY: data/example-x-x.h:[0-9]+:;"
    sys.exit(0)

CommentDelimiterList = [["//", "\n"], ["/*", "*/"]]
def test(TokenIDFile, TokenPrefix):
    print "##-----------------------------------------------------------------"
    token_id_db.clear()
    command_line.do(["--foreign-token-id-file", "data/%s" % TokenIDFile, 
                     "--token-id-prefix", TokenPrefix,
                     "--foreign-token-id-file-show"])
    # parse_token_id_file(TokenIDFile, TokenPrefix, CommentDelimiterList)

    #for key, token_info in token_id_db.items():
    #    print "%s:%i: %s" % (token_info.file_name, token_info.line_n, key)

test("example.h",     "TKN_")
test("example-x.h",   "TKN_")
test("example-x-x.h", "TKN_")
test("example-2.h",   "token::")
test("example-2.h",   "token::TK_")
test("example-2.h",   "::")
