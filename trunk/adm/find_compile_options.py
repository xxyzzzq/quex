#! /usr/bin/env python
import os

unique_option_db = {}
forbidden = [".exe", ".out", ".pdf", ".xml", ".html", ".bin", ".pyc", ".o"]

def find_end_of_macro(Txt, StartIdx, L):
    for i in range(StartIdx, L):
        if not Txt[i].isalnum() and Txt[i] != "_": break
    return i

def extract_options(Txt):
    global unique_option_db
    L = len(Txt)
    i = 0
    while 1 + 1 == 2:
        i = Txt.find("QUEX_OPTION_", i)
        if i == -1: break
        end_i = find_end_of_macro(Txt, i, L)
        # Add compile option to database
        unique_option_db[Txt[i:end_i]] = True
        i += 1

    i = 0
    while 1 + 1 == 2:
        i = Txt.find("QUEX_SETTING", i)
        if i == -1: break
        end_i = find_end_of_macro(Txt, i, L)
        # Add compile option to database
        unique_option_db[Txt[i:end_i]] = True
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
        fh = open(root + "/" + file)
        extract_options(fh.read())
        fh.close()

for key in unique_option_db.keys():
    print "[%s]" % key
