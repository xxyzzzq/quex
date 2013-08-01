from   quex.engine.analyzer.state.entry        import Entry
from   quex.engine.analyzer.state.entry_action import PreConditionOK, TransitionID, TransitionAction
from   quex.engine.analyzer.state.drop_out     import DropOutIndifferent, \
                                                      DropOutBackwardInputPositionDetection
from   quex.blackboard  import E_InputActions

class Base:
    def is_FORWARD(self):                  return False
    def is_BACKWARD_PRE_CONTEXT(self):     return False
    def is_BACKWARD_INPUT_POSITION(self):  return False
    def is_CHARACTER_COUNTER(self):        return False

    def requires_detailed_track_analysis(self):      return False
    def requires_buffer_limit_code_for_reload(self): return True
    def requires_position_register_map(self):        return False

    def direction_str(self):               return None

    def input_action(self, InitStateF):    assert False

    def create_Entry(self, State, FromStateIndexList): assert False
    def create_DropOut(self, SM_State):                assert False

class Class_FORWARD(Base):
    def is_FORWARD(self):                  
        return True
    def requires_detailed_track_analysis(self):
        """DropOut and Entry require construction beyond what is accomplished 
           by constructor of 'AnalyzerState'. Storing of positions need to be
           optimized.
        """
        return True
    def requires_position_register_map(self):
        """For acceptance positions may need to be stored. For this a 
        'position register map' is developped which may minimize the 
        number of registers.
        """
        return True

    def input_action(self, InitStateF):
        if InitStateF: return E_InputActions.DEREF
        else:          return E_InputActions.INCREMENT_THEN_DEREF

    def direction_str(self): 
        return "FORWARD"

    def create_Entry(self, SM_State, StateIndex, FromStateIndexList):
        return Entry(StateIndex, FromStateIndexList)

    def create_DropOut(self, SM_State):                          
        # DropOut and Entry interact and require sophisticated analysis
        # => See "Analyzer.get_drop_out_object(...)"
        return None 

class Class_CHARACTER_COUNTER(Class_FORWARD):
    def is_CHARACTER_COUNTER(self): return True

    def requires_buffer_limit_code_for_reload(self): 
        """Characters to be counted are only inside the lexeme. The lexeme must 
        be entirely in the buffer. Thus, no reload is involved.
        """
        return False

    def create_Entry(self, SM_State, StateIndex, FromStateIndexList):
        return Entry(StateIndex, FromStateIndexList)

    def create_DropOut(self, SM_State):                          
        return None

class Class_BACKWARD_PRE_CONTEXT(Base):
    def is_BACKWARD_PRE_CONTEXT(self):     
        return True

    def direction_str(self): 
        return "BACKWARD"

    def input_action(self, InitStateF):
        return E_InputActions.DECREMENT_THEN_DEREF

    def create_Entry(self, SM_State, StateIndex, FromStateIndexList):
        result = Entry(StateIndex, FromStateIndexList)

        pre_context_ok_command_list = [ 
            PreConditionOK(origin.pattern_id()) for origin in SM_State.origins() \
            if origin.is_acceptance() 
        ]
        for transition_action in result.action_db.itervalues():
            transition_action.command_list.misc.update(pre_context_ok_command_list)
        return result


    def create_DropOut(self, SM_State):                        
        return DropOutIndifferent()

class Class_BACKWARD_INPUT_POSITION(Base):
    def is_BACKWARD_INPUT_POSITION(self):  
        return True

    def requires_buffer_limit_code_for_reload(self): 
        """When going backwards, this happens only along a lexeme which must
        be entirely in the buffer. Thus, no reload is involved.
        """
        return False

    def direction_str(self): 
        return None

    def input_action(self, InitStateF):
        return E_InputActions.DECREMENT_THEN_DEREF

    def create_Entry(self, SM_State, StateIndex, FromStateIndexList):
        return Entry(StateIndex, FromStateIndexList)

    def create_DropOut(self, SM_State):                          
        return DropOutBackwardInputPositionDetection(SM_State.is_acceptance())

FORWARD                 = Class_FORWARD()
CHARACTER_COUNTER       = Class_CHARACTER_COUNTER()
BACKWARD_PRE_CONTEXT    = Class_BACKWARD_PRE_CONTEXT()
BACKWARD_INPUT_POSITION = Class_BACKWARD_INPUT_POSITION()
