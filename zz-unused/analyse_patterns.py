# NOTE: this file is currently not used, we call the recognize newline function
#       for every token ... cumbersome, but for the moment this works perfectly


#! /usr/bin/env python
import sys
from string import split
from file_in import *


class pattern_info:
    def __init__(self, Pattern):
        # note, that for further processing it is safe
        # to know whenever there is a newline even if the
        # claim 'newline present' includes cases where it
        # isn't. the only reason for doing the newline
        # analysis is, because we want to increase the line
        # numbers and call a function 'record_newlines(yytext).'
        # whenever this is necessary.
        self.pattern = Pattern

        idx = Pattern

def do(PatternFilename):

    txt = get_comment_stripped_text(PatternFilename)

    # (1) parse patterns into dictionary
    pattern_base = {}
    for line_info in split(txt, "\n"):
        fields = split(line_info)
        if len(fields) == 2:
            pattern_base[fields[0]] = pattern_info(fields[2])

    # (2) expand the pattern information about newlines



    return pattern_base


def get_comment_stripped_text(PatternFilename):

    fh = open_file_or_die(PatternFilename)

    # (1) find "/* ... */" comments
    txt = fh.read()
    while 1 + 1 == 2:
        idx1 = txt.find("/*")
        if idx1 == -1: break
        idx2 = txt.find("*/", idx1)
        if idx2 == -1:
            print "missing closing comment in file: ", PatternFilename
            sys.exit(-1)

        txt = txt[:idx1] + txt[idx2+2:]

    # (1) find "// ... \n" comments
    while 1 + 1 == 2:
        idx1 = txt.find("//")
        if idx1 == -1: break
        idx2 = txt.find("\n", idx1)
        if idx2 == -1:
            print "missing closing comment in file: ", PatternFilename
            sys.exit(-1)

        txt = txt[:idx1] + txt[idx2+1:]

    return txt
    

