from quex.blackboard import E_StateIndices, \
                            E_EngineTypes,  \
                            setup as Setup

def do(Target, StateIndex, InitStateF, EngineType, OnReloadOK_Str, GotoReload_Str, OnReloadFail_Str, TheAnalyzer=None):
    """Generate a 'real' target action object based on a given Target that 
       may be an identifier or actually a real object already.

       The approach of having 'code-ready' objects as targets makes code 
       generation much simpler. No information has to be passed down the 
       recursive call tree.
    """
    assert Target is not None
    assert Target != -1

    if isinstance(Target, TransitionCode): 
        return Target
    else:
        return TransitionCode(Target, StateIndex, InitStateF, EngineType, 
                              OnReloadOK_Str, GotoReload_Str, OnReloadFail_Str, 
                              TheAnalyzer)

class TransitionCode:
    def __init__(self, Target, StateIndex, InitStateF, EngineType, 
                 OnReloadOK_Str, GotoReload_Str, OnReloadFail_Str, TheAnalyzer=None):
        """The generation of transition code is postponed to the moment when
           the code fragment is used. This happens in order to avoid the
           generation of references to 'goto-labels' that are later not used.
           Note, that in some cases, for example 'goto drop-out' can be avoided
           by simply dropping out of an if-else clause or a switch statement.

           if self.__code is None: postponed
           else:                   not postponed
        """
        LanguageDB = Setup.language_db

        assert EngineType        in E_EngineTypes
        assert type(InitStateF)  == bool
        assert StateIndex        is None or isinstance(StateIndex, (int, long))
        assert OnReloadOK_Str    is None or isinstance(OnReloadOK_Str, (str, unicode))
        assert OnReloadFail_Str  is None or isinstance(OnReloadFail_Str, (str, unicode))
        assert GotoReload_Str    is None or isinstance(GotoReload_Str, (str, unicode))

        if GotoReload_Str is not None:
            assert OnReloadOK_Str is None
            assert OnReloadFail_Str is None
        if OnReloadOK_Str is not None or  OnReloadFail_Str is not None:
            assert GotoReload_Str is None
        if OnReloadOK_Str is not None and OnReloadFail_Str is not None:
            assert OnReloadOK_Str != OnReloadFail_Str

        self.__target              = Target
        self.__state_index         = StateIndex
        self.__init_state_f        = InitStateF
        self.__engine_type         = EngineType
        self.__on_reload_ok_str    = OnReloadOK_Str
        self.__on_reload_fail_str  = OnReloadFail_Str

        if   Target == E_StateIndices.RELOAD_PROCEDURE:
            self.__drop_out_f = False
            if GotoReload_Str is not None: self.__code = GotoReload_Str
            else:                          self.__code = None # postponing

        elif Target == E_StateIndices.DROP_OUT:
            self.__code       = None # postponing
            self.__drop_out_f = True

        elif isinstance(Target, (int, long)):
            # The transition to another target state cannot possibly be cut out!
            # => no postponed code generation
            # If the entry of the target state is uniform (the same from every 'SourceState'),
            # then we do not need to goto it through a specific door (FromStateIndex = None).
            # If the 'Analyzer == None' we assume that all related states have independent_of_source_state entries.
            if    TheAnalyzer is None \
               or not TheAnalyzer.state_db[Target].entry.special_door_from_state(StateIndex):
                self.__code = LanguageDB.GOTO(Target, FromStateIndex=None, EngineType=EngineType)
            else:
                self.__code = LanguageDB.GOTO(Target, StateIndex, EngineType)
            self.__drop_out_f = False

        else:
            # This should only be reached by derived class constructors of 
            # TemplateTransitionCode or PathTransitionCode. Then 'target = None'.
            assert Target is None 

    @property
    def code(self):       
        if self.__code is not None: return self.__code
        LanguageDB = Setup.language_db

        if   self.__target == E_StateIndices.RELOAD_PROCEDURE:
            return LanguageDB.GOTO_RELOAD(self.__state_index, 
                                          self.__init_state_f, 
                                          self.__engine_type, 
                                          self.__on_reload_ok_str, 
                                          self.__on_reload_fail_str)
        elif self.__target == E_StateIndices.DROP_OUT:
            return LanguageDB.GOTO_DROP_OUT(self.__state_index)
        else:
            assert False

    @property
    def drop_out_f(self): return self.__drop_out_f

class TextTransitionCode(TransitionCode):
    def __init__(self, Code, DropOutF=False):
        self.__code       = Code
        self.__drop_out_f = DropOutF
    @property
    def code(self):       return self.__code
    @property
    def drop_out_f(self): return self.__drop_out_f

