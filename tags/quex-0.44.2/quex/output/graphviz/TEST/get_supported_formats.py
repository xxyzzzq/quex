#! /usr/bin/env python
import sys
import os

sys.path.append(os.environ["QUEX_PATH"])

import quex.input.query as query
import quex.output.graphviz.interface as plotter


if "--hwut-info" in sys.argv:
    print "Check supported formats."
    sys.exit(0)


print "Plain Reply:"
for format in plotter.get_supported_graphic_formats():
    print format

print "Pretty Reply:"
for format in plotter.get_supported_graphic_format_description().split(","):
    print format
