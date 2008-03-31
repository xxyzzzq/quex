import os
import subprocess
import tempfile

from quex.frs_py.file_in             import error_msg
from quex.DEFINITIONS                import QUEX_INSTALLATION_DIR
from quex.core_engine.generator.base import GeneratorBase

class Generator(GeneratorBase):
    def __init__(self, PatternActionPairList, StateMachineName, GraphicFormat):

        GeneratorBase.__init__(self, PatternActionPairList, StateMachineName)

        # -- check if graphics format is supported
        supported_format_list = get_supported_graphic_formats()
        if GraphicFormat not in supported_format_list:
            error_msg("Graphic format '%s' not supported.\n" % GraphicFormat + \
                      get_supported_graphic_format_description())

        self.graphic_format = GraphicFormat

    def do(self):
        """Prepare output in the 'dot' language, that graphviz uses."""
        assert_graphviz_installed()

        self.__do(self.sm, self.state_machine_name + "." + self.graphic_format)

        if self.pre_context_sm != None:
            file_name = "%s-pre-condition.%s" % (self.state_machine_name, self.graphic_format)
            self.pre_context_file_name = file_name
            self.__do(self.pre_context_sm, file_name)

        if self.papc_backward_detector_state_machine_list != []:
            self.backward_detector_file_name = []
            for sm in self.papc_backward_detector_state_machine_list:
                file_name = "%s_%i.%s" % (self.state_machine_name, sm.get_id(), self.graphic_format)
                self.backward_detector_file_name.append(file_name)
                self.__do(sm, file_name)

    def __do(self, state_machine, name):
        dot_code = state_machine.get_graphviz_string(NormalizeF=True)
        _call_dot(dot_code, self.graphic_format, name)
    
def get_supported_graphic_formats():
    reply_str = _call_dot(TestCode, "?", "", GetStdErrF=True)

    list_start_i = reply_str.rfind(":")
    if list_start_i == -1 or list_start_i == len(reply_str)-1:
        error_msg("Graphviz was asked to report supported graphic formats, but\n" + \
                  "reply was incomprehensible.")

    return reply_str[list_start_i+1:].split()

def get_supported_graphic_format_description():
    txt = "SUPPORTED GRAPHIC FORMATS:\n"
    i = -1
    for format in get_supported_graphic_formats():
        i += 1
        txt += format + ", "
        if i > 10: txt += "\n"; i = -1
    
    return txt[:-2] + "."

def _call_dot(Code, OutputFormat, OutputFile, GetStdErrF=False):
    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    # try:
    fd, input_file_name = tempfile.mkstemp(".quex.dot", "TMP")
    fh = os.fdopen(fd, "w")
    fh.write(Code)
    fh.close()

    fd_err, error_file = tempfile.mkstemp(".quex.err", "TMP")
    fd_out, out_file   = tempfile.mkstemp(".quex.out", "TMP")
    fh_err = os.fdopen(fd_err, "w")
    fh_out = os.fdopen(fd_out, "w")

    # except:
    #    error_msg("File access error while preparing graphviz code.")

    try:    
        if OutputFile != "": output_str = "-o%s" % OutputFile 
        else:                output_str = ""
        subprocess.call(["dot", input_file_name, "-T%s" % OutputFormat, output_str],
                        stdout=fh_out, stderr=fh_err)
    except: 
        error_msg("Graphviz seems not to be installed on this system. Please, visit www.graphviz.org\n" + \
                  "and download the package. This package is necessary for for plotting\n" + \
                  "transition graphs.")

    fh_out.close()
    fh_err.close()

    result = None
    if GetStdErrF:
        try:    result = open(error_file).read()
        except: error_msg("Output of graphviz is unaccessible.")

    os.remove(error_file)
    os.remove(out_file)

    return result

TestCode = \
"""
digraph Kraichgau {
	rankdir=LR;
	size="10,5"
	node [shape = doublecircle]; Pforzheim;
	node [shape = circle];
	Ispringen -> Pforzheim [ label = "5 km" ];
	Ispringen -> Ersingen [ label = "1 km" ];
}
"""

def assert_graphviz_installed():
    """This function checks whether the graphviz utility has been installed."""

    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    test_filename = QUEX_INSTALLATION_DIR + "/output/graphviz/files/test.dot"
    _call_dot(TestCode, "fig", test_filename + ".fig")

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

   
