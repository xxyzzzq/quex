#! /usr/bin/env python
import sys
import os
sys.path.insert(0, os.environ["QUEX_PATH"])
from   quex.frs_py.string_handling import blue_print

DistributionFileDB = sys.argv[1]
Version            = sys.argv[2]


template_str = open(os.environ["QUEX_PATH"] + "/adm/install-builder-template.xml").read()

file_str = \
"""<distributionFile>
      <origin>$$FILE$$</origin>
</distributionFile>
"""

file_list_str = ""
for line in open(sys.argv[1]).readlines():
    for file in line.split():
        file_list_str += file_str.replace("$$FILE$$", file)

file_list_str = file_list_str.replace("\n", "\n                    ")

if file_list_str[-1] == "\n": file_list_str = file_list_str[:-1]

result = blue_print(template_str,
                    [["$$VERSION$$", Version ],
                     ["$$FILE_LIST$$", file_list_str],
                    ])

open("install-builder.xml", "w").write(result)
