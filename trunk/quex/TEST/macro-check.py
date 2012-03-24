#! /usr/bin/env python
import os
import sys

if "--hwut-info" in sys.argv:
    print "Propper undefinition of configuration parameters."
    sys.exit()

BaseDir = os.environ["QUEX_PATH"] + "/quex/code_base/analyzer/"

def extract_macro(LineStr):
    txt = LineStr.strip()

    if txt[0] == "#":
        # "#define" or "#undef"
        macro = txt.split()[2]
        if macro.find("(") != -1: macro = macro[:macro.index("(")]
        return macro

    # "$$SWITCH$$" statement
    return txt.split()[1]

def get_defined_macro_list():
    result = []
    for file_name in ["TXT", "derived"]:
        line_n = 0
        for line in open(BaseDir + "configuration/" + file_name, "rb").readlines():
            line_n += 1
            line = line.strip()
            if line == "": continue
            line = line.replace("#", "#   ") # handle case safely where '#undef'
            fields = line.split()
            if   fields[0] == "$$SWITCH$$":                  result.append(extract_macro(line))
            elif line[0] != "#":                             continue
            elif len(fields) > 1 and fields[1] == "define":  result.append(extract_macro(line))
    return result

def get_undef_macro_list():
    result = []
    FileName = BaseDir + "configuration/undefine"
    for line in open(FileName, "rb").readlines():
        line = line.strip()
        if line == "": continue
        line = line.replace("#", "#   ") # handle case safely where '#undef'
        fields = line.split()
        if line[0] != "#":                              continue
        elif len(fields) > 1 and fields[1] == "undef":  result.append(extract_macro(line))
    return result

defined_list   = get_defined_macro_list()
undefined_list = get_undef_macro_list()

# print defined_list
# print undefined_list

if "help" not in sys.argv:
    for macro in defined_list:
        if macro not in undefined_list:
            print "Macro %s defined but not undefined." % macro

    for macro in undefined_list:
        if macro not in defined_list:
            print "Macro %s undefined but not defined." % macro
    print "## Call this script with help get the definitions automatically for copy/paste"

else:
    for macro in defined_list:
        if macro not in undefined_list:
            print "#ifdef    %s" % macro
            print "#   undef %s" % macro
            print "#endif"
