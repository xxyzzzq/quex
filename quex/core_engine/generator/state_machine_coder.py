import quex.core_engine.generator.languages.core  as languages
import quex.core_engine.generator.languages.label as languages_label

import quex.core_engine.generator.state_transition_coder as state_transition_coder

def do(state_machine, Language = "C", UserDefinedStateMachineName="", BackwardLexingF=False): 
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
    LanguageDB = languages.db[Language]

    txt = ""
    # -- treat initial state separately	
    LabelName = languages_label.get(UserDefinedStateMachineName, state_machine.init_state_index)
	    
    txt += "%s\n"  % LanguageDB["$label-definition"](LabelName)
    init_state = state_machine.states[state_machine.init_state_index]
    #
    txt += state_transition_coder.do(Language, UserDefinedStateMachineName, init_state, state_machine.init_state_index,
	  	                     BackwardLexingF=BackwardLexingF)

    # -- all other states
    for state_index, state in state_machine.states.items():
	if state_index == state_machine.init_state_index: continue
	LabelName = languages_label.get(UserDefinedStateMachineName, state_index)
	txt += "%s\n" % LanguageDB["$label-definition"](LabelName) 
	txt += state_transition_coder.do(Language, UserDefinedStateMachineName, state, state_index,
			                 BackwardLexingF=BackwardLexingF)
	txt += "\n"
    
    # -- for backward lexing a terminal state has to be provided    
    if BackwardLexingF:
	LabelName = "QUEX_LABEL_%s_TERMINAL" % UserDefinedStateMachineName	
	txt += "%s\n" % LanguageDB["$label-definition"](LabelName) 
	# -- set the input stream back to the real current position.
	#    during backward lexing the analyser went backwards, so it needs to be reset.
	txt += "    QUEX_CORE_SEEK_ANALYSER_START_POSITION;\n"

    return txt

