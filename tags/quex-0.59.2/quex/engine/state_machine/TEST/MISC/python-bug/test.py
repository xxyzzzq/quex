from core import *

print "---[core.py]---"
a = X()

print "---[test.py]---"
simple()
print "##test:         ", id(global_var)
not_so_simple()
print "##test:         ", id(global_var)
