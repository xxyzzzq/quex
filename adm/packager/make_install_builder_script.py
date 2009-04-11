#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.frs_py.string_handling import blue_print

DistributionDir = sys.argv[1]
Version         = sys.argv[2]


template_str = open(os.environ["QUEX_PATH"] + "/adm/packager/install-builder-template.xml").read()

result = blue_print(template_str,
                    [["$$VERSION$$",               Version ],
                     ["$$QUEX_PATH$$",             os.environ["QUEX_PATH"]],
                     ["$$DISTRIBUTION_ROOT_DIR$$", DistributionDir],
                    ])

open("install-builder.xml", "w").write(result)
print "DIR: %s CONTAINS: %s" % (os.getcwd(), "install-builder.xml")

