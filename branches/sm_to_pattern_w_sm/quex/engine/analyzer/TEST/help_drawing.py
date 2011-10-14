import sys
import os

def if_DRAW_in_sys_argv(sm):
    if "DRAW" not in sys.argv: return
    fh = open("tmp.dot", "wb")
    fh.write( sm.get_graphviz_string() )
    fh.close()
    os.system("cat tmp.dot | awk ' ! /circle/ { print; }' > tmp1.dot")
    os.system("graph-easy --input=tmp1.dot --as boxart > tmp2.txt")
    os.system("awk '{ print \"   #   \", $0; }' tmp2.txt > tmp3.txt")
    os.system('echo "   #____________________________________________________________________" >> tmp3.txt')
    print "##", sys.argv[1]
    os.system('cat tmp3.txt')
    os.remove("tmp.dot")
    os.remove("tmp1.dot")
    sys.exit()
