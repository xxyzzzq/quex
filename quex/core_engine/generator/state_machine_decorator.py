from copy import deepcopy
import quex.core_engine.state_machine.dead_end_analyzis as dead_end_analyzis

class StateMachineDecorator:
    def __init__(self, SM, Name, PostContextSM_ID_List, 
                 BackwardLexingF, BackwardInputPositionDetectionF):
        assert SM.__class__.__name__ == "StateMachine"
        assert Name != ""
        assert type(BackwardInputPositionDetectionF) == bool
        assert type(BackwardLexingF) == bool
        assert not BackwardInputPositionDetectionF or BackwardLexingF == True, \
               "BackwardInputPositionDetectionF can only be set if BackwardLexingF is set."
        assert type(PostContextSM_ID_List) == list
        if BackwardInputPositionDetectionF: assert BackwardLexingF

        self.__name                   = Name
        self.__state_machine          = SM
        self.__post_condition_id_list = deepcopy(PostContextSM_ID_List)
        self.__post_condition_id_list.sort()

        self.__mode = "ForwardLexing"
        if BackwardLexingF:
            if BackwardInputPositionDetectionF: self.__mode = "BackwardInputPositionDetection"
            else:                               self.__mode = "BackwardLexing"

        # -- collect the 'dead end states' (states without further transitions)
        #    create a map from the 'dead end state
        print "##A", SM.states.keys()
        self.__dead_end_state_db, self.__directly_reached_terminal_id_list = \
                dead_end_analyzis.do(SM)
        print "##B", SM.states.keys()

        if BackwardLexingF:
            # During backward lexing (pre-condition, backward input position detection)
            # there are no dedicated terminal states in the first place.
            self.__directly_reached_terminal_id_list = []

        # -- information about the states which are compressed into a 'path' or a 'template'
        self.__template_compression_db = {}
        self.__path_compression_db     = {}

    def template_compression_db(self):
        return self.__template_compression_db

    def set_template_compression_db(self, Value):
        assert type(Value) == dict
        self.__template_compression_db = Value

    def path_compression_db(self):
        return self.__path_compression_db

    def set_path_compression_db(self, Value):
        assert type(Value) == dict
        self.__path_compression_db = Value

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

    def post_contexted_sm_n(self):
        return len(self.post_contexted_sm_id_list())

    def get_post_context_index(self, PostContextSM_ID):
        assert PostContextSM_ID in self.__post_condition_id_list, \
               "Error: request of post context state machine id which does not exist."
        return self.__post_condition_id_list.index(PostContextSM_ID)

    def sm(self):
        return self.__state_machine

    def dead_end_state_db(self):
        return self.__dead_end_state_db

    def directly_reached_terminal_id_list(self):
        self.__directly_reached_terminal_id_list


