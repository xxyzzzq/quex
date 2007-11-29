from copy import copy
from quex.frs_py.string_handling import blue_print

#________________________________________________________________________________
# Python
#    
def __transition(UserDefinedStateMachineName, CurrentStateIdx, CurrentStateIsAcceptanceF, StateIdx, 
                 OriginList=None, BackwardLexingF=False, BufferReloadRequiredOnDropOutF=True):
    # NOTE: This is a very rudimental implementation of the __goto_state, see the cpp implementation
    #       for a complete implementation.
    if StateIdx == None: 
        if CurrentStateIsAcceptanceF:
            return __goto_terminal_state(UserDefinedStateMachineName,  
                                         OriginList[0].state_machine_id)  # specific terminal state
        else:    
            return __goto_terminal_state(UserDefinedStateMachineName)     # general terminal state

    txt = "# QUEX_LABEL_%s_ENTRY_%s;\n" % (UserDefinedStateMachineName,
                                           repr(StateIdx).replace("L",""))
    return txt + "return %s" % repr(StateIdx)
        
         
def __goto_terminal_state(UserDefinedStateMachineName, SuccessfulOriginalStateMachineID=None):
    if SuccessfulOriginalStateMachineID == None:
        txt = "# goto QUEX_LABEL_%s_TERMINAL;\n" % UserDefinedStateMachineName
    else:       
        txt = "# goto QUEX_LABEL_%s_TERMINAL_%s;\n" % (UserDefinedStateMachineName,
                                                       repr(SuccessfulOriginalStateMachineID).replace("L",""))
    return txt + "return -1"    

def __note_acceptance(SuccessfulOriginalStateMachineID, LanguageDB, BackwardLexingF=False):
    if SuccessfulOriginalStateMachineID != None:
        txt =  "# last_acceptance = %s\n" % SuccessfulOriginalStateMachineID
        txt += "# last_acceptance_input_position = stream.tell()\n"
    else:
        txt = ""    
    return txt

def __label_definition(LabelName):
    return "# case " + LabelName + ":"

def __state_drop_out_code(StateMachineName, CurrentStateIdx, BackwardLexingF,
                          BufferReloadRequiredOnDropOutF,
                          CurrentStateIsAcceptanceF = None,
                          OriginList                = None,
                          LanguageDB                = None):
    return ""
