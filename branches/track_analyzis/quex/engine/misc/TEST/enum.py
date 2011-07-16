#! /usr/bin/env python
import sys
import os
from   itertools import product

sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.engine.misc.enum import Enum

if "--hwut-info" in sys.argv:
    print "Enums -- Functionality Test"
    sys.exit(0)

# This test has been derived directly from the recipe.
# Extension were made to check important things such as 'safe usage in dictionaries'.
print "(*) Creating an Enum from tuples of names and values:"
print "   ", ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

Days = Enum('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
Months = Enum('Ramadan', "Shawwal", "Dhu_alHidja", "Muharram")

print
print "(*) String Representations and hash values"
print "All:", Days
print "Mo: ", Days.Mo, hash(Days.Mo), Days.Mo.Value
print "Tu: ", Days.Tu, hash(Days.Tu), Days.Tu.Value
print "We: ", Days.We, hash(Days.We), Days.We.Value
print "Th: ", Days.Th, hash(Days.Th), Days.Th.Value
print "Fr: ", Days.Fr, hash(Days.Fr), Days.Fr.Value
print "Sa: ", Days.Sa, hash(Days.Sa), Days.Sa.Value
print "Su: ", Days.Su, hash(Days.Su), Days.Su.Value

print
print "(*) Length = %i" % len(Days)
print 
print "(*) Compare Matrix (demonstrate iteration and comparison at once)"
print "   Mo Tu We Th Fr Sa Su"
for x in Days:
    print "%s" % x, 
    for y in Days:
        print { 1: " >", -1: " <", 0: " =" }[cmp(x, y)],
    print 

try:    
    print "Try: Days.Mo = 12"
    Days.Mo = 12
except: 
    print "Good, assignment failed!"

print
print "(*) As element in dictionaries"
# Internally, an integer index i = 0 to N is used to scale the values.
# Here, we make sure, that neither index nor name slipped through as
# comparison for dictionary operations
db = {
        Days.Mo: "Monday",
        Days.Tu: "Tuesday",
        Days.We: "Wednesday",
        Days.Th: "Thursday",
        Days.Fr: "Friday",
        Days.Sa: "Saturday",
        Days.Su: "Sunday",
}
print "  Original:"
for key, value in sorted(db.iteritems()):
    print "    ", key, ":", value

print "  Applying integers:"
for i in xrange(7):
    db[i] = "Nonsense"
for key, value in sorted(db.iteritems()):
    print "    ", key, ":", value

print "  Applying names:"
print "  The string representation of enum values are actually the same as"
print "  the new strings used as keys. But the keys are not identical and"
print "  therefore they names appear twice."
for name in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
    db[name] = "Nonsense"
for key, value in sorted(db.iteritems()):
    print "    ", key, ":", value

print 
print "(*) Check 'in'"
x = Days.Mo
print "Mo in Days:", x in Days
x = Months.Ramadan
print "Ramadan in Days:", x in Days
print
print "(*) Class Names and Identities"

print "Days:",   Days.__class__.__name__
print "     ", Days
print "Months:", Months.__class__.__name__
print "     ", Months
print "Classes of two enums are:", 
if id(Days) == id(Months) or id(Days.__class__) == id(Months.__class__): 
    print "identical (ERROR!)"
else:
    print "not identical (GOOD)"

