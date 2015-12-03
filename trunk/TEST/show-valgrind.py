import sys
if len(sys.argv) > 1: file_name = sys.argv[1]
else:                 file_name = "tmp.txt"

fh = open(file_name)

print_f = False
for line in fh.readlines():
    if line.find("--") == 0:
        continue
    if line.find("==") == 0:
        # 'valgrind' line
        if   line.find("All heap blocks were freed") != -1: print "VALGRIND: ", line[8:].replace("=", "").replace(".", ""), 
        elif line.find(" definitely lost:") != -1:          print "VALGRIND: ", line[8:].replace("=", ""),
        elif line.find(" indirectly lost:") != -1:          print "VALGRIND: ", line[8:].replace("=", ""),
        elif line.find(" possibly lost:") != -1:            print "VALGRIND: ", line[8:].replace("=", ""),
        elif line.find(" still reachable:") != -1:          print "VALGRIND: ", line[8:].replace("=", ""),
        elif line.find(" suppressed:") != -1:               print "VALGRIND: ", line[8:].replace("=", ""), 
        continue
    else:
        print line,
