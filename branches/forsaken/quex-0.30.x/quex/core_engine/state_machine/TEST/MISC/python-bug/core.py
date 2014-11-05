global global_var 
global_var = long(-1)

def simple():
        global global_var
        print "##simple:       ", id(global_var) 

def not_so_simple():
        global global_var
        global_var += 1
        print "##not_so_simple:", id(global_var) 
        return global_var

class X:
        def __init__(self):
                global global_var
                simple()
                not_so_simple()
                print "##class X:      ", id(global_var)
