# (C) Frank-Rene Schaefer
from collections import defaultdict
import subprocess
import os
import sys
# Help to handle pyflakes 'unable to find unresolved'.

# (1) Call PyFlakes on all arguments
def get_flaws(FilenameList):
    fh = open("pyflakes.log", "wb")
    subprocess.call(["pyflakes"] + FilenameList, stdout=fh)
    fh.close()

    # Find the lines with 'unable ....'
    fh = open("pyflakes.log", "rb")
    result = defaultdict(list)
    for line in fh.readlines():
        if line.find("unable") == -1: continue
        i0 = line.find(":")
        i1 = line.find(":", i0+1)
        file_name   = line[:i0]
        line_n      = line[i0+1:i1]
        result[file_name].append(int(line_n))
    fh.close()
    return result

def get_import_disabled(Filename, LineN):
    # Go through each file
    file_name_0 = Filename
    file_name_1 = "tmp-" + Filename.replace("/", "--")
    fh0 = open(file_name_0, "rb")
    fh1 = open(file_name_1, "wb")
    prev_name_set = set()
    indentation = None
    for i, line in enumerate(fh0.readlines(), 1):
        if i == LineN: 
            indentation = line.find("import") + 7
            continue
        fh1.write(line)

        i = line.find("undefined name")
        if i == -1: continue
        name = line[i+15:].replace("'", "").strip()
        prev_name_set.add(name)
    fh0.close()
    fh1.close()
    assert indentation is not None
    return file_name_1, prev_name_set, indentation

def get_new_undefined_names(Filename, PrevNameSet):
    # Run pyflakes on that file
    fh = open("pyflakes.log", "wb")
    subprocess.call(["pyflakes", Filename], stdout=fh)
    fh.close()

    # Extract the missing names
    fh = open("pyflakes.log", "rb")
    name_set = set()
    for line in fh.readlines():
        i    = line.find("undefined name")
        if i == -1: continue
        name = line[i+15:].replace("'", "").strip()
        if name not in PrevNameSet: name_set.add(name)

    return name_set

def replace_new_import_statement(FilenameOrig, FilenameNew, NameSet, Indentation):
    new_content = " "
    last_i      = len(NameSet) - 1
    for i, name in enumerate(sorted(list(NameSet))):
        new_content += name 
        if i != last_i: new_content += ", \\"
        new_content += "\n"
        if i != last_i: new_content += " " * Indentation

    # Now, write the new file
    fh0 = open(FilenameOrig, "rb")
    fh1 = open(FilenameNew, "wb")
    for i, line in enumerate(fh0.readlines(), 1):
        if i == line_n: 
            line = line.replace("*", "").strip()
            line += new_content
        fh1.write(line)
    fh0.close()
    fh1.close()

def call_merge(FilenameOrig, FilenameNew):
    return subprocess.call(["vimdiff", FilenameNew, FilenameOrig])

todo = get_flaws(sys.argv[1:])

for file_name, line_n_list in todo.iteritems():
    for line_n in line_n_list:
        tmp_file_name, prev_name_set, indentation = get_import_disabled(file_name, line_n)
        name_set =  get_new_undefined_names(tmp_file_name, prev_name_set)
        print "##", name_set
        replace_new_import_statement(file_name, tmp_file_name, name_set, indentation)
        call_merge(file_name, tmp_file_name)
        os.remove(tmp_file_name)
    # break
os.remove("pyflakes.log")
