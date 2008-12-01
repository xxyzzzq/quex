from quex.frs_py.file_in import is_identifier_start, \
                                is_identifier_continue

import quex.core_engine.generator.skip_code as skip_code

class ActionI:
    def __init__(self, Code, RequireTerminatingZeroF=False):
        self.__code = Code
        self.__require_terminating_zero_f = RequireTerminatingZeroF

    def set_code(self, Code):
        self.__code = Code

    def get_code(self):
        return self.__code

    def set_require_terminating_zero_f(self):
        self.__require_terminating_zero_f = True

    def require_terminating_zero_f(self):
        return self.__require_terminating_zero_f


class GeneratedCodeFragment(ActionI):
    def __init__(self, Code, RequireTerminatingZeroF=False):
        ActionI.__init__(self, Code, RequireTerminatingZeroF)


ReferencedCodeFragment_OpenLinePragma = {
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
        "C": [
              '/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA */',
              '#line NUMBER "FILENAME"'
             ],
   }

class ReferencedCodeFragment(ActionI):
    def __init__(self, Code="", Filename="", LineN=-1, RequireTerminatingZeroF=False):
        self.filename = Filename
        self.line_n   = LineN

        # No clue yet, how to deal with languages other than C/C++ here.
        if Code != "":
            txt  = '\n#line %i "%s"\n' % (self.line_n, self.filename)
            txt += Code
            if txt[-1] != "\n": txt = txt + "\n"
            txt += ReferencedCodeFragment_OpenLinePragma["C"][0] + "\n"
            code = txt
        else:
            code = Code

        ActionI.__init__(self, code, RequireTerminatingZeroF)


def ReferencedCodeFragment_straighten_open_line_pragmas(filename, Language):
    if Language not in ReferencedCodeFragment_OpenLinePragma.keys():
        return

    try:    fh = open(filename)
    except: raise "error: file to straighten line pragmas not found: '%s'" % \
            filename

    new_content = ""
    line_n      = 0
    LinePragmaInfo = ReferencedCodeFragment_OpenLinePragma[Language]
    for line in fh.readlines():
        line_n += 1
        if line.find(LinePragmaInfo[0]) != -1:
            if Language == "C":
                line = LinePragmaInfo[1]
                line = line.replace("NUMBER", repr(int(line_n)))
                line = line.replace("FILENAME", filename)
                line = line + "\n"
        new_content += line

    fh.close()

    fh = open(filename, "w")
    fh.write(new_content)
    fh.close()


class ActionInfo:
    def __init__(self, PatternStateMachine, ActionCode_or_Str):
        assert PatternStateMachine != None
        assert ActionCode_or_Str == None                        or \
               type(ActionCode_or_Str) == str                   or \
               issubclass(ActionCode_or_Str.__class__, ActionI)

        self.__pattern_state_machine = PatternStateMachine
        if type(ActionCode_or_Str) == str:
            self.__action = ReferencedCodeFragment(ActionCode_or_Str, LineN=1, RequireTerminatingZeroF=True)
        else:
            self.__action = ActionCode_or_Str

    def pattern_state_machine(self):
        return self.__pattern_state_machine

    def action(self):
        return self.__action

    def __repr__(self):
        txt0 = "state machine of pattern = \n" + repr(self.__pattern_state_machine)
        txt1 = "action = \n" + self.__action_.get_code()
        
        txt  = "ActionInfo:\n"
        txt += "   " + txt0.replace("\n", "\n      ") + "\n"
        txt += "   " + txt1.replace("\n", "\n      ")
        return txt
        
class PatternActionInfo(ActionInfo):
    def __init__(self, Pattern, Action, PatternStateMachine, PatternIdx=None,
                 PriorityMarkF=False, DeletionF=False, IL = None, ModeName=""):

        assert Action == None or issubclass(Action.__class__, ActionI)
        assert PatternStateMachine.__class__.__name__ == "StateMachine" \
               or PatternStateMachine == None

        ActionInfo.__init__(self, PatternStateMachine, Action)

        self.pattern               = Pattern
        # depth of inheritance where the pattern occurs
        self.inheritance_level     = IL
        self.inheritance_mode_name = ModeName

    def __repr__(self):         
        txt = ""
        txt += "self.pattern           = " + repr(self.pattern) + "\n"
        txt += "self.action            = " + repr(self.action.get_code()) + "\n"
        txt += "self.filename          = " + repr(self.action.filename) + "\n"
        txt += "self.line_n            = " + repr(self.action.line_n) + "\n"
        txt += "self.inheritance_level = " + repr(self.inheritance_level) + "\n"
        txt += "self.pattern_index     = " + repr(self.pattern_state_machine.core().id()) + "\n"
        return txt

    def pattern_index(self):
        return self.pattern_state_machine().get_id()

