from quex.frs_py.file_in import is_identifier_start, \
                                is_identifier_continue

class ActionInfo:
    def __init__(self, PatternStateMachine, ActionCodeStr):
        assert PatternStateMachine != None
        assert type(ActionCodeStr) == str

        self.__pattern_state_machine = PatternStateMachine
        self.__action_code_str       = ActionCodeStr

    def pattern_state_machine(self):
        return self.__pattern_state_machine

    def action_code(self):
        return self.__action_code_str

    def contains_variable(self, VariableName, CommentDelimiters):
        return self.__contains("Lexeme", CommentDelimiters)

    def __contains(self, ObjectName, CommentDelimiters, IgnoreRegions=["\"", "\""]):
        assert type(CommentDelimiters) == list

        for delimiter_info in CommentDelimiters:
            assert type(delimiter_info) == list, "Argument 'CommentDelimiters' must be of type [[]]"
            assert len(delimiter_info) == 3, \
                   "Elements of argument CommentDelimiters must be arrays with three elements:\n" + \
                   "start of comment, end of comment, replacement string for comment."

        txt = self.__action_code_str
        L       = len(txt)
        LO      = len(ObjectName)
        found_i = -1
        while 1 + 1 == 2:
            # TODO: Implement the skip_whitespace() function for more general treatment of Comment
            #       delimiters. Quotes for strings '"" shall then also be treate like comments.
            found_i = txt.find(ObjectName, found_i + 1)

            if found_i == -1: return False

            # Note: The variable must be named 'exactly' like the given name. 'xLexeme' or 'Lexemey'
            #       shall not trigger a treatment of 'Lexeme'.
            if     (found_i == 0      or not is_identifier_start(txt[found_i - 1]))     \
               and (found_i == L - LO or not is_identifier_continue(txt[found_i + LO])): 
                   return True

    def __repr__(self):
        txt0 = "state machine of pattern = \n" + repr(self.__pattern_state_machine)
        txt1 = "action = \n" + self.__action_code_str
        
        txt  = "ActionInfo:\n"
        txt += "   " + txt0.replace("\n", "\n      ") + "\n"
        txt += "   " + txt1.replace("\n", "\n      ")
        return txt
        

