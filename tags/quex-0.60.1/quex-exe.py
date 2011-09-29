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

try:    
    if False: print ""
except: 
    print("error: This version of quex was not implemented for Python >= 3.0")
    print("error: Please, use Python versions 2.x.")
    sys.exit(-1)

from quex.engine.misc.file_in  import error_msg

def __exeption_handler(TheException):
    def on_exception(x, Txt):
        if "--debug-exception" in sys.argv: 
            raise x
        error_msg(Txt)

    if isinstance(TheException, AssertionError):
        on_exception(TheException, "Assertion error -- please report a bug under\n" + \
                     " https://sourceforge.net/tracker/?group_id=168259&atid=846112")

    elif isinstance(TheException, KeyboardInterrupt): 
        print
        error_msg("#\n# Keyboard Interrupt -- Processing unfinished.\n#")

    else:
        on_exception(TheException, "Exception occured -- please, report a bug under\n" + \
                  " https://sourceforge.net/tracker/?group_id=168259&atid=846112")
    
try:
    # (*) Check if everything is correctly installed
    import quex.DEFINITIONS
    quex.DEFINITIONS.check()

    import tempfile

    # This script needs to be located one directory above 'quex.'
    # so that it ca get the imports straight.
    from   quex.blackboard               import setup as Setup
    import quex.input.command_line.core  as command_line
    import quex.input.command_line.query as query_parser
    import quex.core                     as core


except BaseException as instance:
    __exeption_handler(instance)
    
try:
    pass
    # import psyco
    # psyco.full()
except:
    pass

if __name__ == "__main__":
    try:
        core._exception_checker()

        # (*) Call only for query? ___________________________________________________________
        if query_parser.do(sys.argv):   # if quex has been called for UCS property
            sys.exit(0)                 # query, then no further processing is performed

        # (*) Get Setup from Command Line and Config File ____________________________________
        #     If the setup parser returns 'False' the requested job was minor
        #     and no further processing has to be done. If 'True' start the process.
        if command_line.do(sys.argv):
            # (*) Run Quex ___________________________________________________________________
            core.do() 

    except BaseException as instance:
        __exeption_handler(instance)


