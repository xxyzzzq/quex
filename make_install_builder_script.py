#! /usr/bin/env python
import sys

file_str = \
"""<distributionFile>
      <origin>$$FILE$$</origin>
</distributionFile>
"""

file_list_str = ""
for line in open(sys.argv[1]).readlines():
    for file in line.split():
        file_list_str += file_str.replace("$$FILE$$", file)

print file_list_str
