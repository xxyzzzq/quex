#! /usr/bin/env python
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
            

def get_time_value():
    fh = open("tmp.txt")
    lines = fh.readlines()
    fh.close()
    for line in lines:
        if line.find("TimePerRun:") == 0:
            time_str = line.split()[1]
            return float(time_str)
    print "ERROR"
    print lines
    return None
    
db = DB(find_data_files("input"))

for file_name, size in db.items():
    fh = open("tmp.txt", "w")
    subprocess.call(["../lexer", "input/" + file_name], stdout = fh)
    fh.close()
    print "%08i %f" % (size, get_time_value())

