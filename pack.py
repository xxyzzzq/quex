#! /usr/bin/env python

import sys
import os
import time
from   copy import copy

if len(sys.argv) < 2:    
    print "## specify a version for which to pack quex"
    sys.exit(-1)

license_txt = """#! /usr/bin/env python
# Quex is  free software;  you can  redistribute it and/or  modify it  under the
# terms  of the  GNU Lesser  General  Public License  as published  by the  Free
# Software Foundation;  either version 2.1 of  the License, or  (at your option)
# any later version.
# 
# This software is  distributed in the hope that it will  be useful, but WITHOUT
# ANY WARRANTY; without even the  implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the  GNU Lesser General Public License for more
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along
# with this  library; if not,  write to the  Free Software Foundation,  Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
################################################################################
"""

def ensure_license_statement_in_file(FullFilename):
    fh = open(FullFilename)
    text = fh.read()
    fh.close()
    
    if text.find("Quex is  free software") != -1:
        return
    
    text = license_txt + text
    text += "\n#license-info %s#" % time.asctime()

    fh = open(FullFilename, "w")
    fh.write(text)
    fh.close()

version  = sys.argv[1]

# (*) replace the $$Date$$ and $$Version$$ in the Quex file
fh = open("DEFINITIONS.py.template")
backup_str = fh.read()
fh.close()
tmp_adapted = backup_str.replace("$$VERSION$$", version)
#   write the adapted DEFINITIONS file out
fh = open("DEFINITIONS.py", "w")
fh.write(tmp_adapted)
fh.close()


# -- create list of test files
test_files_pre = ['in/token.dat', 'in/simple.qx', 'in/PATTERNS.lex',
              'Makefile', 'lexer.cpp', 'example.txt' ]
test_files = []
for i in range(3):
    test_files.extend(map(lambda filename: "%03i/%s" % (i, filename),
                          test_files_pre))

files = {
    "/":
       [ "file_in.py",
         "DEFINITIONS.py",
         "modes_out.py",
         "pre_flex.py",
         "quex_token_id_maker.py",
         "GetPot.py",
         "lexer_mode.py",
         "quex",
         "setup_parser.py",
         "LPGL.txt",
         "quex_class_out.py",
         "error_msg.py",
         "install-unix.sh",
         "input/quex_file_parser.py",
         "post_flex.py",
         "quex.py" ],
    #
    "TEST/":
         test_files,
    #
    "DOC/":
         [ "main.pdf" ],
    #
    "templates/":
         [ "circular_queue-v-0.0.1", "circular_queue",
           "quex",
           "token", "token.cpp", "token_queue" ],
}


tar_file = "quex-%s.tar " % version
doc_file = "quex-doc-%s.pdf " % version
pack_str = ""
for dir_name, file_list in files.items():
    d = "quex/" + dir_name
    for filename in file_list:
        if d == "quex//":
            ensure_license_statement_in_file("../%s%s" % (d, filename))
        
        print "%s%s" % (d, filename)
        pack_str += "%s%s \\\n" % (d, filename)

# pack all files together
os.system("cd ..; tar chf %s %s" % (tar_file, pack_str))
os.system("cd ..; gzip -9 %s" % tar_file)
os.system("cp DOC/main.pdf ../%s" % doc_file)


