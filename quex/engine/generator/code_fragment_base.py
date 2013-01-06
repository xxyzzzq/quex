class CodeFragment:
    def __init__(self, Code=None, RequireTerminatingZeroF=False):
        if   Code == None:                     self.__code = []
        elif isinstance(Code, (str, unicode)): self.__code = [ Code ]
        else:                                  self.__code = Code

    def set_code(self, Code):
        self.__code = Code

    def get_code(self, Mode=None):
        """Returns a list of strings and/or integers that are the 'core code'. 
        Integers represent indentation levels.
        """
        return self.__code

    def get_code_string(self):
        """Returns the 'code' as a string. The derived class may provide other
        content to the code. That is why '.get_code()' is refered.
        """
        return "".join(self.get_code())

    def get_pure_code(self):
        """Return string with 'pure' code, that is without any adornments
        that indicate its original place in user source files etc.
        """
        # NOTE: '.get_code()' because it may be overwritten by derived classes.
        #       Those derived classes may add other information to the code.
        return "".join(self.__code)

    def contains_string(self, TheString):
        for string in self.__code:
            if string.find(TheString) != -1: return True
        return False

    def is_empty(self):
        return len(self.__code) == 0

    def is_whitespace(self):
        for elm in self.__code:
            if len(elm.strip()) != 0: return False
        return True

_Empty = None
def CodeFragment_Empty():
    global _Empty
    if _Empty is None: 
        _Empty = CodeFragment("")
    return _Empty
    
