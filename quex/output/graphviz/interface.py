import os
import subprocess
from frs_py.file_in import error_msg


def do(StateMachine, OutputFormat):
    """Prepare output in the 'dot' language, that graphviz uses."""
    __assert_graphviz_installed()

    supported_format_list = __get_supported_graphic_formats()
    if OutputFormat not in supported_format_list:
        error_msg("Graphic format '%s' not supported. Please, use one of: " + \
                  repr(supported_formats)[1:-1])

    dot_code
    
def report_supported_graphic_formats():
    __assert_graphviz_installed()


def __get_supported_graphic_formats():
    return ["fig"]


transition_template = '$1$ -> $2$ [ label = "$3$"]'
def __call_dot(Code, OutputFormat, OutputFile):
    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    try:
        fd, input_file_name = tempfile.mkstemp(".quex.dot", "TMP")
        fh = os.fdopen(fd, "w")
        fh.write(Code)
        fh.close()

        fd, error_report = tempfile.mkstemp(".quex.err", "TMP")
        fh_err = os.fopen(fd, "e")
        fh_out = open(os.devnull, "w")

    except:
        error_msg("File access error while preparing graphviz code.")

    try:    subprocess.call(["dot", input_file_name, "-T%s" % OutputFormat, "-o%s" % OutputFile], 
                            stdout=fh_out, stderr=fh_err)
    except: 
        print "Warning: 'dot' was not callable on this system."
        return False

    fh_out.close()
    fh_err.close()



def __assert_graphviz_installed():
    """This function checks whether the graphviz utility has been installed."""

    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    test_filename = QUEX_PATH + "/output/graphviz/test.dot"
    fh_out        = open(test_filename + ".fig", "w")
    fh_err        = open(test_filename + ".err", "w")

    try:    subprocess.call(["dot", test_filename, "-Tfig"], stdout=fh_out, stderr=fh_err)
    except: 
        error_msg("Graphviz is not installed on this system."
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
    __assert_graphviz_installed()
