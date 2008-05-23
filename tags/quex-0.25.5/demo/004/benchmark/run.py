#! /usr/bin/env python
import sys
import subprocess
import os

def find_data_files(Dir):
    def condition(Filename):
        if   Filename.find("data-") != 0: return False
        elif Filename.rfind("-kB.txt") != len(Filename) - 7: return False
        return True

    return filter(condition, os.listdir(Dir))

class DB:
    def __init__(self, FileList):
        self.__db = {}
        for file in FileList:
            size_str = file.split("-")[1]
            size     = int(size_str)
            self.__db[file] = size

    def __getitem__(self, Arg):
        return self.__db[Arg]

    def items(self):
        items = self.__db.items()
        items.sort(lambda a, b: cmp(a[1], b[1]))
        return items
            

def get_value(Str):
    fh = open("tmp.txt")
    content = fh.read()
    fh.close()
    lines = content.split("\n")
    for line in lines:
        if line.find(Str) == 0:
            value_str = line.split()[1]
            return float(value_str)
    print "ERROR", Str
    print lines
    return None

    
db = DB(find_data_files("input"))

for file_name, size in db.items():
    file_name = "input/" + file_name

    # The benchmark call
    fh = open("tmp.txt", "w")
    subprocess.call(["../lexer", file_name, repr(size)], stdout = fh)
    fh.close()
    repetition_n = get_value("Runs:")
    run_time     = get_value("Clocks/Char:")

    # The token counter
    fh = open("tmp.txt", "w")
    subprocess.call(["../lexer", file_name], stdout = fh)
    fh.close()
    token_n = get_value("TokenN:")

    # The reference call
    fh = open("tmp.txt", "w")
    subprocess.call(["../lexer", file_name, repr(size), "%i" % int(token_n), "%i" % int(repetition_n)], stdout = fh)
    fh.close()
    ref_run_time = get_value("Clocks/Char:")

    print "%08i %f %f %f" % (size, run_time - ref_run_time, run_time, ref_run_time)

