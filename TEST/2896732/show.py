fh = open("tmp.txt")
print_f = False
for line in fh.readlines():
    if line.find("HEAP SUMMARY") != -1:    print_f = True
    if print_f and len(line) > 8: print line[8:],
