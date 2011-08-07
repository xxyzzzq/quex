#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.output.graphviz.core     as plotter


if "--hwut-info" in sys.argv:
    print "Check supported formats."
    sys.exit(0)


print "Plain Reply:"
for format in sorted(plotter.get_supported_graphic_formats()):
    print format

print "Pretty Reply:"
for format in sorted(plotter.get_supported_graphic_format_description().split(",")):
    print format
