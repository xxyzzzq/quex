class Handler:
    def __init__(self, TheState):
        self.force_input_dereferencing_f = False
        if isinstance(TheState, PathWalkerState):
            self.force_input_dereferencing_f = True
            self.require_data = self.__path_walker_require_data
        else:
            self.require_data = self.__template_require_data



def do(txt, TheState, TheAnalyzer):
    global LanguageDB
    LanguageDB = Setup.language_db

    handler = Handler(TheState)

    # (*) Entry _______________________________________________________________
    entry_coder.do(txt, TheState, TheAnalyzer) 

    # (*) Access input character ______________________________________________
    input_do(txt, TheState, handler.force_input_dereferencing_f) 

    # (*) MegaState specific frameworks
    handler.framework(txt, TheState, TheAnalyzer)

    # (*) Transition Map ______________________________________________________
    prepare_transition_map(TheState)
    transition_block.do(txt, 
                        TheState.transition_map, 
                        TheState.index, 
                        TheState.engine_type, 
                        TheState.init_state_f, 
                        TheAnalyzer = TheAnalyzer)

    # (*) Drop Out ____________________________________________________________
    __drop_out(txt, TheState, TheAnalyzer)

    # (*) Request necessary variable definition _______________________________
    handler.require_data(TheState)

    return

def prepare_transition_map(TheState):
    """Prepare the transition map of the MegaState for code generation.

       NOTE: A word about the reload procedure.
       
       Reload can end either with success (new data has been loaded), or failure
       (no more data available). In case of success the **only** the transition
       step has to be repeated. Nothing else is effected.  Stored positions are
       adapted automatically.
       
       By convention we redo the transition map, in case of reload success and 
       jump to the state's drop-out in case of failure. There is no difference
       here in the template state example.
    """
    # Transition map of the 'skeleton'        
    if TheState.transition_map_empty_f:
        # Transition Map Empty:
        # This happens, for example, if there are only keywords and no 
        # 'overlaying' identifier pattern. But, in this case also, there
        # must be something that catches the 'buffer limit code'. 
        # => Define an 'all drop out' trigger_map, and then later
        # => Adapt the trigger map, so that the 'buffer limit' is an 
        #    isolated single interval.
        TheState.transition_map = [ (Interval(-sys.maxint, sys.maxint), MegaState_Target(E_StateIndices.DROP_OUT)) ]

    transition_map = TheState.transition_map

    for i, info in enumerate(transition_map):
        interval, target = info
        
        if   target.drop_out_f:
            # Later functions detect the 'DROP_OUT' in the transition map, so
            # we do not want to put it in text here. Namely function:
            # __separate_buffer_limit_code_transition(...) which implements the
            # buffer limit code insertion.
            transition_map[i] = (interval, E_StateIndices.DROP_OUT)
            continue

        if target.door_id is not None:
            text = LanguageDB.GOTO_BY_DOOR_ID(target.door_id)

        else:
            get_label("$state-router", U=True) # Ensure reference of state router
            # Transition target depends on state key
            label = "template_%i_target_%i[state_key]" % (TheState.index, target.index)
            text  = LanguageDB.GOTO_BY_VARIABLE(label)

        # Replace target 'i' by written text
        target            = TextTransitionCode([text])
        transition_map[i] = (interval, target)

    return

