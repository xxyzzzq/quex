
class CodeFragment:
    def __init__(self, Code=None, RequireTerminatingZeroF=False):
        if   Code == None:                     self.__code = []
        elif isinstance(Code, (str, unicode)): self.__code = [ Code ]
        else:                                  self.__code = Code

    def set_code(self, Code):
        self.__code = Code

    def get_code(self, Mode=None):
        return self.__code

    def contains_string(self, TheString):
        for string in self.__code:
            if string.find(TheString) != -1: return True
        return False

    def is_whitespace(self):
        for elm in self.__code:
            if elm.strip() != 0: return False
        return True

    def get_pure_code(self):
        return "".join(self.__code)


