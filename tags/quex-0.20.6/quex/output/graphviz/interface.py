import os
import subprocess

QUEX_PATH=""

def is_installed():
    """This function checks whether the graphviz utility has been installed."""

    # (*) initiate call to the graphviz utility ('dot') and use a sample file
    #     for reference.
    test_filename = QUEX_PATH + "output/graphviz/test.dot"
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
    is_installed()
