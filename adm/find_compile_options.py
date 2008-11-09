#! /usr/bin/env python
import os

unique_option_db = {}
dubious = {}
forbidden = [".exe", ".out", ".pdf", ".xml", ".html", ".bin", ".pyc", ".o", ".swp"]

file = ""

def get_line_n(Txt, Pos):
    line_n = 0
    for i in range(0, Pos):
        if Txt[i] == "\n": line_n += 1
    return line_n

def find_end_of_macro(Txt, StartIdx, L):
    for i in range(StartIdx, L):
        if not Txt[i].isalnum() and Txt[i] != "_": break
    return i

def add_finding(OptionName, FileName, LineN):
    global unique_option_db

    if unique_option_db.has_key(OptionName):
        unique_option_db[OptionName].append([FileName, LineN])
    else:
        unique_option_db[OptionName] = [([FileName, LineN])]

def extract_options(Txt):
    global unique_option_db
    global file_name

    L = len(Txt)
    i = 0
    while 1 + 1 == 2:
        i = Txt.find("QUEX_OPTION_", i)
        if i == -1: break
        end_i = find_end_of_macro(Txt, i, L)
        add_finding(Txt[i:end_i], file_name, get_line_n(Txt, i))
        i += 1

    i = 0
    while 1 + 1 == 2:
        i = Txt.find("QUEX_SETTING", i)
        if i == -1: break
        end_i = find_end_of_macro(Txt, i, L)
        add_finding(Txt[i:end_i], file_name, get_line_n(Txt, i))
        i += 1

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
        print "    %s:%i:" % (file_name, line_n)
