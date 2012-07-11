from   quex.engine.state_machine.core      import State
from   quex.engine.analyzer.state.entry    import Entry
from   quex.engine.analyzer.state.drop_out import DropOutBackward, \
                                                  DropOutBackwardInputPositionDetection
from   quex.blackboard  import E_StateIndices, \
                               E_InputActions

class Base:
    def is_FORWARD(self):                  return False
    def is_BACKWARD_PRE_CONTEXT(self):     return False
    def is_BACKWARD_INPUT_POSITION(self):  return False

    def direction_str(self):               return None

    def input_action(self, InitStateF):    assert False

    def create_Entry(self, State, FromStateIndexList): assert False
    def create_DropOut(self, SM_State):                assert False


class Class_FORWARD(Base):
    def is_FORWARD(self):                  
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

class Class_BACKWARD_PRE_CONTEXT(Base):
    def is_BACKWARD_PRE_CONTEXT(self):     
        return True

    def direction_str(self): 
        return "BACKWARD"

    def input_action(self, InitStateF):
        return E_InputActions.DECREMENT_THEN_DEREF

    def create_Entry(self, SM_State, StateIndex, FromStateIndexList):
        pre_context_id_fulfilled_list = [ origin.pattern_id() for origin in SM_State.origins() \
                                                              if origin.is_acceptance() ]
        return Entry(StateIndex, FromStateIndexList, pre_context_id_fulfilled_list)

    def create_DropOut(self, SM_State):                        
        return DropOutBackward()

class Class_BACKWARD_INPUT_POSITION(Base):
    def is_BACKWARD_INPUT_POSITION(self):  
        return True

    def direction_str(self): 
        return None

    def input_action(self, InitStateF):
        return E_InputActions.DECREMENT_THEN_DEREF

    def create_Entry(self, SM_State, StateIndex, FromStateIndexList):
        return Entry(StateIndex, FromStateIndexList)

    def create_DropOut(self, SM_State):                          
        return DropOutBackwardInputPositionDetection(SM_State.is_acceptance())

FORWARD                 = Class_FORWARD()
BACKWARD_PRE_CONTEXT    = Class_BACKWARD_PRE_CONTEXT()
BACKWARD_INPUT_POSITION = Class_BACKWARD_INPUT_POSITION()
