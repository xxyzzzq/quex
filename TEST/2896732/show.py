import sys

fh = open("tmp.txt")
print_f = False
all_lines = fh.readlines()
for line in all_lines:
    if line.find("All heap blocks were freed") != -1: 
        print line[8:].replace("=", "").replace(".", ""); 
        sys.exit()

for line in all_lines:
    if line.lower().find("error") != -1: 
        print line
