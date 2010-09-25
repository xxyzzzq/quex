fh = open("Simple.cpp")
print_f = False
for line in fh.readlines():
    if line.find("/* state machine */") != -1:    print_f = True
    elif print_f and line.find("*/") != -1:       print_f = False
    if print_f: print line,
