import quex.core_engine.generator.languages.core  as languages
from   quex.core_engine.generator.languages.core  import __nice
import quex.core_engine.generator.state_coder as state_coder
import quex.core_engine.state_machine.dead_end_analysis as dead_end_analysis
from   quex.input.setup import setup as Setup

LanguageDB = Setup.language_db

class StateMachineDecorator:
    def __init__(self, SM, Name, PostConditionID_List, 
                 BackwardLexingF, BackwardInputPositionDetectionF):
        assert SM.__class__.__name__ == "StateMachine"
        assert Name != ""
        assert type(BackwardInputPositionDetectionF) == bool
        assert type(BackwardLexingF) == bool
        assert not BackwardInputPositionDetectionF or BackwardLexingF == True, \
               "BackwardInputPositionDetectionF can only be set if BackwardLexingF is set."
        assert type(PostConditionID_List) == list

        self.__name                   = Name
        self.__state_machine          = SM
        self.__post_condition_id_list = PostConditionID_List
        self.__mode = "ForwardLexing"
        if BackwardLexingF:
            if BackwardInputPositionDetectionF: self.__mode = "BackwardInputPositionDetection"
            else:                               self.__mode = "BackwardLexing"

        # -- collect the 'dead end states' (states without further transitions)
        #    create a map from the 'dead end state
        self.__dead_end_state_db, self.__directly_reached_terminal_id_list = \
                dead_end_analysis.do(SM)

        if BackwardLexingF:
            # During backward lexing (pre-condition, backward input position detection)
            # there are no dedicated terminal states in the first place.
            self.__directly_reached_terminal_id_list = []

    def name(self):
        return self.__name

    def mode(self):
        return self.__mode

    def backward_lexing_f(self):
        assert self.__mode in ["ForwardLexing", "BackwardLexing", "BackwardInputPositionDetection"]
        return self.__mode in ["BackwardLexing", "BackwardInputPositionDetection"] 

    def forward_lexing_f(self):
        assert self.__mode in ["ForwardLexing", "BackwardLexing", "BackwardInputPositionDetection"]
        return not backward_lexing_f()

    def backward_input_position_detection_f(self):
        assert self.__mode in ["ForwardLexing", "BackwardLexing", "BackwardInputPositionDetection"]
        return self.__mode == "BackwardInputPositionDetection" 

    def post_contexted_sm_id_list(self):
        return self.__post_condition_id_list

    def sm(self):
        return self.__state_machine

    def dead_end_state_db(self):
        return self.__dead_end_state_db

    def directly_reached_terminal_id_list(self):
        self.__directly_reached_terminal_id_list

def do(state_machine, StateMachineName, 
       BackwardLexingF, BackwardInputPositionDetectionF, 
       PostConditionID_List):
    """Returns the program code implementing the StateMachine's behavior.
       NOTE: This function should only be called on a DFA after the call
             to 'filter_dominated_origins'. The latter is important
             to ensure that for an acceptance state there is only one
             related original state.

       The procedure for each state is the following:
            i)  input <-- next character from stream 
            ii) state transition code (include marking of last success state
                and last success stream position).                  
    """
    if BackwardInputPositionDetectionF: assert BackwardLexingF

    decorated_state_machine = StateMachineDecorator(state_machine, StateMachineName, 
                                                    PostConditionID_List, 
                                                    BackwardLexingF, BackwardInputPositionDetectionF)

    txt = ""
    # -- treat initial state separately 
    if state_machine.is_init_state_a_target_state():
        # (only define the init state label, if it is really needed)
        txt += LanguageDB["$label-def"]("$entry", state_machine.init_state_index) + "\n"

    init_state = state_machine.states[state_machine.init_state_index]
    #
    # NOTE: Only the init state provides a transition via 'EndOfFile'! In any other
    #       case, end of file needs to cause a drop out! After the drop out, lexing
    #       starts at furthest right before the EndOfFile and the init state transits
    #       into the TERMINAL_END_OF_FILE.
    txt += LanguageDB["$label-def"]("$entry", state_machine.init_state_index) + "\n"
    txt += state_coder.do(init_state, 
                          state_machine.init_state_index,
                          decorated_state_machine,
                          InitStateF = True)

    # -- all other states
    for state_index, state in state_machine.states.items():
        # the init state has been coded already
        if state_index == state_machine.init_state_index: continue

        state_code = state_coder.do(state, state_index, decorated_state_machine)

        # some states are not coded (some dead end states)
        if state_code == "": continue

        txt += LanguageDB["$label-def"]("$entry", state_index) + "\n"
        txt += state_code
        txt += "\n"
    
    return txt, decorated_state_machine.directly_reached_terminal_id_list()





