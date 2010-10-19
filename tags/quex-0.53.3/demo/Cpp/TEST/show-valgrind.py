fh = open("tmp.txt")
print_f = False
for line in fh.readlines():
    if line.find("==") == 0:
        # 'valgrind' line
        if   line.find("All heap blocks were freed") != -1: print "VALGRIND: ", line[8:].replace("=", "").replace(".", ""), 
        elif line.find(" definitely lost:") != -1: print "VALGRIND: ", line[8:],
        elif line.find(" indirectly lost:") != -1: print "VALGRIND: ", line[8:],
        elif line.find(" possibly lost:") != -1:   print "VALGRIND: ", line[8:],
        elif line.find(" still reachable:") != -1: print "VALGRIND: ", line[8:],
        elif line.find(" suppressed:") != -1:      print "VALGRIND: ", line[8:],
        continue
    else:
        print line,
