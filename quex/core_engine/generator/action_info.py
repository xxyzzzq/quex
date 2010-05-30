import os
from quex.frs_py.file_in import is_identifier_start, \
                                is_identifier_continue, \
                                open_file_or_die, \
                                write_safely_and_close

class CodeFragment:
    def __init__(self, Code="", RequireTerminatingZeroF=False):
        self.__code = Code
        self.__require_terminating_zero_f = RequireTerminatingZeroF

    def set_code(self, Code):
        self.__code = Code

    def get_code(self):
        return self.__code

    def get_pure_code(self):
        return self.__code

    def set_require_terminating_zero_f(self):
        self.__require_terminating_zero_f = True

    def require_terminating_zero_f(self):
        return self.__require_terminating_zero_f

UserCodeFragment_OpenLinePragma = {
#___________________________________________________________________________________
# Line pragmas allow to direct the 'virtual position' of a program in a file
# that was generated to its origin. That is, if an error occurs in line in a 
# C-program which is actually is the pasted code from a certain line in a .qx 
# file, then the compiler would print out the line number from the .qx file.
# 
# This mechanism relies on line pragmas of the form '#line xx "filename"' telling
# the compiler to count the lines from xx and consider them as being from filename.
#
# During code generation, the pasted code segments need to be followed by line
# pragmas resetting the original C-file as the origin, so that errors that occur
# in the 'real' code are not considered as coming from the .qx files.
# Therefore, the code generator introduces placeholders that are to be replaced
# once the whole code is generated.
#
#  ...[Language][0]   = the placeholder until the whole code is generated
#  ...[Language][1]   = template containing 'NUMBER' and 'FILENAME' that
#                       are to replaced in order to get the resetting line pragma.
#___________________________________________________________________________________
        "C": 
        [
            [ '/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA */',
              '#line NUMBER "FILENAME"' ],
            ['/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA CppTemplate.txt */',
             '#line NUMBER "CppTemplate.txt"' ]
        ],
   }

class UserCodeFragment(CodeFragment):
    def __init__(self, Code, Filename, LineN, LanguageDB=None):
        assert type(Code)       in [str, unicode]
        assert type(LanguageDB) == dict or LanguageDB == None
        assert type(Filename)   in [str, unicode]
        assert type(LineN)      in [int, long, float]

        self.filename = Filename
        self.line_n   = LineN

        require_terminating_zero_f = False
        if LanguageDB != None and LanguageDB["$require-terminating-zero-preparation"](LanguageDB, Code):
            require_terminating_zero_f = True

        CodeFragment.__init__(self, Code, require_terminating_zero_f)

    def get_code(self):
        return self.adorn_with_source_reference(self.get_pure_code())

    def adorn_with_source_reference(self, Code, ReturnToSourceF=True):
        if Code.strip() == "": return Code

        txt  = '\n#line %i "%s"\n' % (self.line_n, os.path.normpath(self.filename))
        txt += Code
        if ReturnToSourceF:
            if txt[-1] != "\n": txt = txt + "\n"
            txt += get_return_to_source_reference()
        return txt
    
def get_return_to_source_reference():
    return "\n" + UserCodeFragment_OpenLinePragma["C"][0][0] + "\n"


def UserCodeFragment_straighten_open_line_pragmas(filename, Language):
    if Language not in UserCodeFragment_OpenLinePragma.keys():
        return

    fh = open_file_or_die(filename)

    new_content = ""
    line_n      = 0
    LinePragmaInfoList = UserCodeFragment_OpenLinePragma[Language]
    for line in fh.readlines():
        line_n += 1
        if Language == "C":
            for info in LinePragmaInfoList:
                if line.find(info[0]) == -1: continue
                line = info[1]
                line = line.replace("NUMBER", repr(int(line_n + 1)))
                norm_filename = os.normpath(filename).replace("\\", "\\\\")
                line = line.replace("FILENAME", norm_filename)
                line = line + "\n"
        new_content += line

    fh.close()

    write_safely_and_close(filename, new_content)

class PatternActionInfo:
    def __init__(self, PatternStateMachine, Action, Pattern="", IL = None, ModeName=""):

        assert Action == None or \
               issubclass(Action.__class__, CodeFragment) or \
               type(Action) in [str, unicode]
        assert PatternStateMachine.__class__.__name__ == "StateMachine" \
               or PatternStateMachine == None

        self.__pattern_state_machine = PatternStateMachine
        if type(Action) in [str, unicode]: self.__action = CodeFragment(Action)
        else:                              self.__action = Action

        self.pattern   = Pattern
        self.mode_name = ModeName

    def pattern_state_machine(self):
        return self.__pattern_state_machine

    def action(self):
        return self.__action

    def set_action(self, Action):
        self.__action = Action

    def pattern_index(self):
        return self.pattern_state_machine().get_id()

    def __repr__(self):         
        txt  = ""
        txt += "self.mode_name         = " + repr(self.mode_name) + "\n"
        txt += "self.pattern           = " + repr(self.pattern) + "\n"
        txt += "self.pattern_state_machine = \n" + repr(self.pattern_state_machine()).replace("\n", "\n      ")
        txt += "self.action            = " + repr(self.action().get_code()) + "\n"
        if self.action().__class__ == UserCodeFragment:
            txt += "self.filename          = " + repr(self.action().filename) + "\n"
            txt += "self.line_n            = " + repr(self.action().line_n) + "\n"
        txt += "self.pattern_index     = " + repr(self.pattern_state_machine().core().id()) + "\n"
        return txt

