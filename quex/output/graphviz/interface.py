import os
import subprocess
from frs_py.file_in import error_msg

transition_template = '$1$ -> $2$ [ label = "$3$"]'

def do(StateMachine, OutputFormat):
    """Prepare output in the 'dot' language, that graphviz uses."""
    supported_format_list = __get_supported_graphic_formats()
    if OutputFormat not in supported_format_list:
        error_msg("Graphic format '%s' not supported. Please, use one of: " + \
                  repr(supported_formats)[1:-1])

    dot_code
    

def __get_supported_graphic_formats():
    return ["fig"]


def __call_dot(Code, OutputFormat, OutputFile=""):
    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    test_filename = QUEX_PATH + "/output/graphviz/test.dot"
    fh_out        = open(test_filename + ".fig", "w")
    fh_err        = open(test_filename + ".err", "w")

    try:    subprocess.call(["dot", test_filename, "-T%s" % OutputFile], 
                            stdout=fh_out, stderr=fh_err)
    except: 
        print "Warning: 'dot' was not callable on this system."
        return False

    fh_out.close()
    fh_err.close()

    try:    fh = open(test_filename + ".fig")
    except: return False


def __is_installed():
    """This function checks whether the graphviz utility has been installed."""

    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    test_filename = QUEX_PATH + "/output/graphviz/test.dot"
    fh_out        = open(test_filename + ".fig", "w")
    fh_err        = open(test_filename + ".err", "w")

    try:    subprocess.call(["dot", test_filename, "-Tfig"], stdout=fh_out, stderr=fh_err)
    except: 
        print "Warning: 'dot' was not callable on this system."
        return False

    fh_out.close()
    fh_err.close()

    try:    fh = open(test_filename + ".fig")
    except: return False

    # (*) read in the result check for consistency, i.e. some
    #     things that need to appead whatsoever version we use.
    content = fh.read()
    if content.find("Pforzheim") == -1: return False
    if content.find("Ispringen") == -1: return False
    if content.find("5 km")      == -1: return False
    if content.find("Ersingen")  == -1: return False
    if content.find("1 km")      == -1: return False

    return True

   
if __name__ == "__main__":
    __is_installed()
