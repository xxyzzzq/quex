
class ActionInfo:
    def __init__(self, PatternStateMachine, ActionCodeStr):
        assert PatternStateMachine != None
        assert type(ActionCodeStr) == str

        self.__action_code_str       = ActionCodeStr
        self.__pattern_state_machine = PatternStateMachine

    def pattern_state_machine(self):
        return self.__pattern_state_machine

    def action_code(self):
        return self.__action_code_str

    def contains_Lexeme_object(self, CommentDelimiters):
        """Returns information wether the code fragment contains the keyword
           'Lexeme'. This is important, because some time can be spared if it
           does not. The preparation of the Lexeme object is some overhead.
        """
        return self.__contains("Lexeme", CommentDelimiters)

    def contains_LexemeLength_object(self, CommentDelimiters):
        """Same as 'contains_Lexeme_object()' for the LexemeLength.
        """
        return self.__contains("LexemeL", CommentDelimiters)

    def __contains(self, ObjectName, CommentDelimiters, IgnoreRegions=["\"", "\""]):
        assert type(CommentDelimiters) == list

        for delimiter_info in CommentDelimiters:
            assert type(delimiter_info) == list, "Argument 'CommentDelimiters' must be of type [[]]"
            assert len(delimiter_info) == 3, \
                   "Elements of argument CommentDelimiters must be arrays with three elements:\n" + \
                   "start of comment, end of comment, replacement string for comment."
        # TODO: Implement the skip_whitespace() function for more general treatment of Comment
        #       delimiters. Quotes for strings '"" shall then also be treate like comments.
        return self.__action_code_str.find(ObjectName) != -1

    def __repr__(self):
        txt0 = "state machine of pattern = \n" + repr(self.__pattern_state_machine)
        txt1 = "action = \n" + self.__action_code_str
        
        txt  = "ActionInfo:\n"
        txt += "   " + txt0.replace("\n", "\n      ") + "\n"
        txt += "   " + txt1.replace("\n", "\n      ")
        return txt
        

