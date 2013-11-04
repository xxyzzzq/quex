from   quex.engine.misc.file_in import \
                                       open_file_or_die, \
                                       write_safely_and_close, \
                                       get_current_line_info_number, \
                                       error_msg
from   quex.engine.generator.code_fragment_base import CodeFragment
from   quex.blackboard import setup as Setup, E_IncidenceIDs, SourceRef

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
            ['/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA */',
             '#   line NUMBER "FILENAME"' ],
            ['/* POST-ADAPTION: FILL IN APPROPRIATE LINE PRAGMA CppTemplate.txt */',
             '#   line NUMBER "CppTemplate.txt"' ]
        ],
   }

class UserCodeFragment(CodeFragment):
    def __init__(self, Code="", SourceReference=None):
        assert isinstance(Code, (str, unicode))
        assert isinstance(SourceReference, SourceRef) or SourceReference is None

        CodeFragment.__init__(self, Code)
        self.sr = SourceReference

    def clone(self):
        result = UserCodeFragment()
        result.set_code(CodeFragment.get_code(self))
        result.sr = self.sr # SourceRef is immutable
        return result

    def get_code(self, Mode=None):
        return  [ self.adorn_with_source_reference(CodeFragment.get_code(self)) ]

    def adorn_with_source_reference(self, Code, ReturnToSourceF=True):
        if type(Code) == list:
            Code = "".join(Code)

        if len(Code.strip()) == 0: return ""

        # Even under Windows (tm), the '/' is accepted. Thus do not rely on 'normpath'
        norm_filename = Setup.get_file_reference(self.sr.file_name) 
        txt  = '\n#   line %i "%s"\n' % (self.sr.line_n, norm_filename)
        txt += Code
        if ReturnToSourceF:
            if txt[-1] != "\n": txt = txt + "\n"
            txt += get_return_to_source_reference()
        return txt

class GeneratedCode(UserCodeFragment):
    def __init__(self, Data, SourceReference):
        assert isinstance(Data, dict)
        self.data = Data
        UserCodeFragment.__init__(self, SourceReference=SourceReference)

    def get_code(self, Mode=None):
        assert False, "Not to be called. TerminalStateFactory shall use '.data' and incidence_id to find TerminalType"

class PatternActionInfo:
    def __init__(self, ThePattern, Action, PatternStr="", IL = None, ModeName="", Comment=""):
        assert    ThePattern in E_IncidenceIDs \
               or (ThePattern.__class__.__name__ == "Pattern") \
               or (ThePattern is None)

        if Action is None or issubclass(Action.__class__, CodeFragment):
            self.__action = Action
        else:
            self.__action = CodeFragment(Action)

        self.__pattern     = ThePattern
        self.__pattern_str = PatternStr
        self.mode_name     = ModeName
        self.comment       = Comment

    @property
    def line_n(self): return self.action().sr.line_n
    @property
    def file_name(self): return self.action().sr.file_name

    def acceptance_id(self):
        if self.__pattern in E_IncidenceIDs: return self.__pattern 
        else:                             return self.__pattern.sm.get_id()
    def pattern(self):
        return self.__pattern

    def pattern_string(self):
        return self.__pattern_str

    def action(self):
        return self.__action

    def set_action(self, Action):
        assert Action is None or \
               issubclass(Action.__class__, CodeFragment) or \
               type(Action) in [str, unicode]
        self.__action = Action

    def pattern_index(self):
        return self.pattern_state_machine().get_id()

    def __repr__(self):         
        txt  = ""
        txt += "self.mode_name      = %s\n" % repr(self.mode_name)
        if self.pattern() not in E_IncidenceIDs:
            txt += "self.pattern_string = %s\n" % repr(self.pattern_string())
        txt += "self.pattern        = %s\n" % repr(self.pattern()).replace("\n", "\n      ")
        txt += "self.action         = %s\n" % self.action().get_code_string()
        if self.action().__class__ == UserCodeFragment:
            txt += "self.file_name  = %s\n" % repr(self.action().sr.file_name) 
            txt += "self.line_n     = %s\n" % repr(self.action().sr.line_n) 
        if self.pattern() not in E_IncidenceIDs:
            txt += "self.pattern_index  = %s\n" % repr(self.pattern().sm.get_id()) 
        return txt

class LocalizedParameter:
    def __init__(self, Name, Default, FH=-1, PatternStr = None):
        self.name      = Name
        self.__default = Default
        if FH == -1:
            self.__value = None
            self.sr      = SourceRef("", -1)
        else:
            self.__value = Default
            self.sr      = SourceRef.from_FileHandle(FH)
        self.__pattern_string = PatternStr

    def set(self, Value, fh):
        if self.__value is not None:
            error_msg("%s has been defined more than once.\n" % self.name, fh, DontExitF=True)
            error_msg("previous definition has been here.\n", self.file_name, self.line_n)
                      
        self.__value   = Value
        if fh == -1:
            self.file_name = "<string>"
            self.line_n    = 0
        else:
            self.file_name = fh.name
            self.line_n    = get_current_line_info_number(fh)

    def get(self):
        if self.__value is not None: return self.__value
        return self.__default

    def set_pattern_string(self, Value):
        self.__pattern_string = Value

    def pattern_string(self):
        return self.__pattern_string

    @property
    def comment(self):
        return self.name

def UserCodeFragment_straighten_open_line_pragmas(filename, Language):
    if Language not in UserCodeFragment_OpenLinePragma.keys():
        return

    fh = open_file_or_die(filename)
    norm_filename = Setup.get_file_reference(filename)

    new_content = []
    line_n      = 0
    LinePragmaInfoList = UserCodeFragment_OpenLinePragma[Language]
    for line in fh.readlines():
        line_n += 1
        if Language == "C":
            for info in LinePragmaInfoList:
                if line.find(info[0]) == -1: continue
                line = info[1]
                # Since by some definition, line number pragmas < 32768; let us avoid
                # compiler warnings by setting line_n = min(line_n, 32768)
                line = line.replace("NUMBER", repr(int(min(line_n + 1, 32767))))
                # Even under Windows (tm), the '/' is accepted. Thus do not rely on 'normpath'
                line = line.replace("FILENAME", norm_filename)
                if len(line) == 0 or line[-1] != "\n":
                    line = line + "\n"
        new_content.append(line)

    fh.close()

    write_safely_and_close(filename, "".join(new_content))

def get_return_to_source_reference():
    return "\n" + UserCodeFragment_OpenLinePragma["C"][0][0] + "\n"

