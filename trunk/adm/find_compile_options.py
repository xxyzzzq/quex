#! /usr/bin/env python
import os
import sys
from quex.frs_py.file_in import extract_identifiers_with_specific_prefix

unique_option_db = {}
dubious = {}
forbidden = [".exe", ".out", ".pdf", ".xml", ".html", ".bin", ".pyc", ".o", ".swp"]

forsaken_list = [
        "/home/fschaef/prj/quex/trunk/quex/core_engine/generator/languages/perl.py",
        "/home/fschaef/prj/quex/trunk/quex/core_engine/generator/languages/c.py",
        "/home/fschaef/prj/quex/trunk/quex/core_engine/generator/languages/visual_basic.py",
        ]

file = ""

prefix_list = ["QUEX", "__QUEX" ]

def add_finding(OptionName, FileName, LineN):
    global unique_option_db

    if unique_option_db.has_key(OptionName):
        unique_option_db[OptionName].append([FileName, LineN])
    else:
        unique_option_db[OptionName] = [([FileName, LineN])]

def extract_options(Txt):
    global unique_option_db
    global file_name
    global prefix_list

    for prefix in prefix_list:
        for name, line_n in extract_identifiers_with_specific_prefix(Txt, prefix):
            add_finding(name, file_name, line_n)

def extension(Filename):
    i = Filename.rfind(".")
    if i == -1: return ""
    else:       return Filename[i:]

if "user" in sys.argv:
    prefix_list = ["QUEX_SETTING", "QUEX_OPTION", "QUEX_TYPE"]

for root, dir_list, file_list in os.walk(os.environ["QUEX_PATH"] + "/quex"):
    if root.find(".svn")        != -1: continue
    if root.find("/TEST/OUT/")  != -1: continue
    if root.find("/TEST/GOOD/") != -1: continue
    if root.find("/TEST/ADM/")  != -1: continue

    # print root
    for file in file_list:
        if root.find("/code_base/") != -1:
            if extension(file) in forbidden: continue
        else:
            if extension(file) != ".py": continue

        # print "--", file
        file_name = root + "/" + file
        if file_name in forsaken_list: continue

        fh        = open(file_name)
        extract_options(fh.read())
        fh.close()

the_list = unique_option_db.items()
the_list.sort()
for key, finding_list in the_list:
    print ".. cmacro:: %s" % key
    if "user" not in sys.argv:
        for file_name, line_n in finding_list:
            print "    %s:%i: here" % (file_name, line_n)

