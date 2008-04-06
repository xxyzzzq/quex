#! /usr/bin/env python
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
# (C) 2007 Frank-Rene Schaefer
#
################################################################################
import sys
import tempfile

# This script needs to be located one directory above 'quex.'
# so that it ca get the imports straight.
import quex.DEFINITIONS
import quex.input.setup as setup_parser
import quex.input.query as query_parser
import quex.core        as core

from quex.frs_py.file_in  import error_msg

if __name__ == "__main__":
    try:
        # (*) Check if everything is correctly installed
        quex.DEFINITIONS.check()

        # (*) Call only for query? ___________________________________________________________
        if query_parser.do(sys.argv):   # if quex has been called for UCS property
            sys.exit(0)                 # query, then no further processing is performed

        # (*) Get Setup from Command Line and Config File ____________________________________
        setup = setup_parser.do(sys.argv)

        if setup.plot_graphic_format_list_f:
            print quex.output.graphviz.interface.get_supported_graphic_format_description()
            sys.exit(0)

        # (*) Run the Quex ___________________________________________________________________
        if setup.plot_graphic_format == "": core.do(setup)       # 'normal' code generation
        else:                               core.do_plot(setup)  # plot transition graphs

    except "": # AssertionError:
        error_msg("Assertion error -- please report a bug at http://quex.sourceforge.net.")


