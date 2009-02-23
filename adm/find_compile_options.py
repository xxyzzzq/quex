#! /usr/bin/env python
import os
from quex.frs_py.file_in import extract_identifiers_with_specific_prefix

unique_option_db = {}
dubious = {}
forbidden = [".exe", ".out", ".pdf", ".xml", ".html", ".bin", ".pyc", ".o", ".swp"]

file = ""

def add_finding(OptionName, FileName, LineN):
    global unique_option_db

    if unique_option_db.has_key(OptionName):
        unique_option_db[OptionName].append([FileName, LineN])
    else:
        unique_option_db[OptionName] = [([FileName, LineN])]

def extract_options(Txt):
    global unique_option_db
    global file_name

    for name, line_n in extract_identifiers_with_specific_prefix(Txt, "QUEX"):
        add_finding(name, file_name, line_n)

    for name, line_n in extract_identifiers_with_specific_prefix(Txt, "__QUEX"):
        add_finding(name, file_name, line_n)

def extension(Filename):
    i = Filename.rfind(".")
    if i == -1: return ""
    else:       return Filename[i:]

for root, dir_list, file_list in os.walk(os.environ["QUEX_PATH"]):
    if root.find(".svn") != -1: continue
    # print root
    for file in file_list:
        if extension(file) in forbidden: continue
        # print "--", file
        file_name = root + "/" + file
        fh        = open(file_name)
        extract_options(fh.read())
        fh.close()

the_list = unique_option_db.items()
the_list.sort()
for key, finding_list in the_list:
    print "[%s]" % key
    for file_name, line_n in finding_list:
        print "    %s:%i: here" % (file_name, line_n)
