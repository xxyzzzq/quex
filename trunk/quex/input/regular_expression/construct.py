from   quex.engine.misc.file_in                     import get_current_line_info_number
from   quex.engine.interval_handling                import UnicodeInterval, Interval
from   quex.engine.state_machine.core               import StateMachine
from   quex.engine.state_machine.utf16_state_split  import ForbiddenRange
import quex.engine.state_machine.character_counter  as character_counter
import quex.engine.state_machine.setup_post_context as setup_post_context
import quex.engine.state_machine.setup_pre_context  as setup_pre_context
import quex.engine.state_machine.setup_backward_input_position_detector  as setup_backward_input_position_detector
import quex.engine.state_machine.transformation        as     transformation
import quex.engine.state_machine.algorithm.beautifier  as beautifier
#                                                         
from   quex.blackboard           import setup     as Setup, deprecated
from   quex.engine.misc.file_in  import error_msg
import sys

class Pattern(object):
    __slots__ = ("file_name", "line_n", 
                 "__core_sm", 
                 "__sm", 
                 "__post_context_f", 
                 "__bipd_sm_to_be_inverted",        "__bipd_sm", 
                 "__pre_context_sm_to_be_inverted", "__pre_context_sm", 
                 "__pre_context_begin_of_line_f", 
                 "__count_info", 
                 "__alarm_transformed_f")
    def __init__(self, CoreSM, PreContextSM=None, PostContextSM=None, 
                 BeginOfLineF=False, EndOfLineF=False, 
                 fh=-1):
        assert type(BeginOfLineF) == bool
        assert type(EndOfLineF) == bool
        assert isinstance(CoreSM, StateMachine)
        assert PreContextSM is None or isinstance(CoreSM, StateMachine)

        if fh != -1:
            try:    self.file_name = fh.name
            except: self.file_name = "<string>"
            self.line_n = get_current_line_info_number(fh)
        else:
            self.file_name = "<string>"
            self.line_n    = -1

        # (*) Setup the whole pattern
        if PostContextSM is None:
            self.__core_sm = CoreSM # Nothing will be mounted to it. prepare_count_info() OK.
        else:
            self.__core_sm = CoreSM.clone()
        self.__sm      = CoreSM

        # -- [optional] post contexts
        self.__post_context_f = (PostContextSM is not None)

        #    Backward input position detection requires an inversion of the 
        #    state machine. This can only be done after the (optional) codec
        #    transformation. Thus, a non-inverted version of the state machine
        #    is maintained until the transformation is done.
        self.__sm,     \
        self.__bipd_sm_to_be_inverted = setup_post_context.do(self.__sm, PostContextSM, EndOfLineF, fh=fh) 
        self.__bipd_sm                = None

        # -- [optional] pre contexts
        #
        #    Same as for backward input position detection holds for pre-contexts.
        self.__pre_context_sm_to_be_inverted = PreContextSM
        self.__pre_context_sm                = None

        # All state machines must be DFAs
        assert self.__sm is not None
        if not self.__sm.is_DFA_compliant(): 
            self.__sm                        = beautifier.do(self.__sm)

        if         self.__pre_context_sm_to_be_inverted is not None \
           and not self.__pre_context_sm_to_be_inverted.is_DFA_compliant(): 
            self.__pre_context_sm_to_be_inverted = beautifier.do(self.__pre_context_sm_to_be_inverted)

        if         self.__bipd_sm_to_be_inverted is not None \
           and not self.__bipd_sm_to_be_inverted.is_DFA_compliant(): 
            self.__bipd_sm_to_be_inverted        = beautifier.do(self.__bipd_sm_to_be_inverted)

        # Detect the trivial pre-context
        self.__pre_context_begin_of_line_f = BeginOfLineF
        
        self.__count_info = None

        # Ensure, that the pattern is never transformed twice
        self.__alarm_transformed_f = False

        self.__validate(fh)
    
    def prepare_count_info(self, LineColumn_CounterDB, CodecTrafoInfo):                
        """Perform line/column counting on the core pattern, i.e. the pattern
        which is not concerned with the post context. The counting happens 
        on a UNICODE state machine--not on a possibly transformed codec state
        machine.
        """
        if self.__count_info is not None:
            return self.__count_info

        # If the pre-context is 'trivial begin of line', then the column number
        # starts counting at '1' and the column number may actually be set
        # instead of being added.
        self.__count_info = character_counter.do(self.__core_sm, 
                                                 LineColumn_CounterDB, 
                                                 self.pre_context_trivial_begin_of_line_f, 
                                                 CodecTrafoInfo)
        return self.__count_info

    def count_info(self):                          return self.__count_info
    @property
    def sm(self):                                  return self.__sm
    @property
    def pre_context_sm_to_be_inverted(self):       return self.__pre_context_sm
    @property
    def pre_context_sm(self):                      return self.__pre_context_sm
    @property
    def bipd_sm(self):                             return self.__bipd_sm
    @property
    def pre_context_trivial_begin_of_line_f(self): 
        if self.__pre_context_sm_to_be_inverted is not None:
            return False
        return self.__pre_context_begin_of_line_f

    def has_pre_context(self): 
        return    self.__pre_context_begin_of_line_f \
               or self.__pre_context_sm_to_be_inverted is not None \
               or self.__pre_context_sm                is not None
    def has_post_context(self):   
        return self.__post_context_f
    def has_pre_or_post_context(self):
        return self.has_pre_context() or self.has_post_context()

    def mount_pre_context_sm(self):
        if    self.__pre_context_sm_to_be_inverted is None \
          and self.__pre_context_begin_of_line_f == False:
            return

        self.__pre_context_sm = setup_pre_context.do(self.__sm, 
                                                     self.__pre_context_sm_to_be_inverted, 
                                                     self.__pre_context_begin_of_line_f)

    def mount_bipd_sm(self):
        if self.__bipd_sm_to_be_inverted is None: 
            return

        self.__bipd_sm = setup_backward_input_position_detector.do(self.__sm, 
                                                                   self.__bipd_sm_to_be_inverted) 

    def cut_character_list(self, CharacterList):
        """Characters can only be cut, if transformation is done and 
        pre- and bipd are mounted.
        """
        def my_error(Name, Pattern):
            error_msg("Pattern becomes empty after deleting signal character '%s'." % Name,
                      Pattern.file_name, Pattern.line_n)

        for character, name in CharacterList:
            for sm in [self.__sm, self.__pre_context_sm, self.__bipd_sm]:
                if sm is None: continue
                sm.delete_transtions_on_interval(Interval(character))
                sm.clean_up()
                if sm.is_empty(): 
                    my_error(name, self)

    def transform(self, TrafoInfo):
        """Transform state machine if necessary."""
        # Make sure that a pattern is never transformed twice
        assert self.__alarm_transformed_f == False
        self.__alarm_transformed_f = True

        # Transformation MUST be called before any pre-context or bipd
        # is mounted.
        assert self.__pre_context_sm is None
        assert self.__bipd_sm        is None

        c0, self.__sm                            = transformation.try_this(self.__sm)
        c1, self.__pre_context_sm_to_be_inverted = transformation.try_this(self.__pre_context_sm_to_be_inverted)
        c2, self.__bipd_sm_to_be_inverted        = transformation.try_this(self.__bipd_sm_to_be_inverted)

        # Only if all transformation have been complete, then the transformation
        # can be considered complete.
        return c0 and c1 and c2

    def __validate(self, fh):
        # (*) It is essential that state machines defined as patterns do not 
        #     have origins.
        if self.__sm.has_origins():
            error_msg("Regular expression parsing resulted in state machine with origins.\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n", fh)

        # (*) Acceptance states shall not store the input position when they are 'normally'
        #     post-conditioned. Post-conditioning via the backward search is a different 
        #     ball-game.
        acceptance_f = False
        for state in self.__sm.states.values():
            if state.is_acceptance(): 
                acceptance_f = True
            if     state.input_position_store_f() \
               and state.is_acceptance():
                error_msg("Pattern with post-context: An irregularity occurred.\n" + \
                          "(end of normal post-contexted core pattern is an acceptance state)\n" 
                          "Please, log a defect at the projects website quex.sourceforge.net.", fh)

        if acceptance_f == False:
            error_msg("Pattern has no acceptance state and can never match.\n" + \
                      "Aborting generation process.", fh)

    def __repr__(self):
        return self.get_string(self)

    def get_string(self, NormalizeF=False, Option="utf8"):
        assert Option in ["utf8", "hex"]

        msg = self.__sm.get_string(NormalizeF, Option)
            
        if   self.__pre_context_sm is not None:
            msg += "pre-context = "
            msg += self.__pre_context_sm.get_string(NormalizeF, Option)           

        elif self.__pre_context_sm_to_be_inverted is not None:
            msg += "pre-context to be inverted = "
            msg += self.__pre_context_sm_to_be_inverted.get_string(NormalizeF, Option)           

        if self.__bipd_sm is not None:
            msg += "post-context backward input position detector = "
            msg += self.__bipd_sm.get_string(NormalizeF, Option)           

        elif self.__bipd_sm_to_be_inverted is not None:
            msg += "post-context backward input position detector to be inverted = "
            msg += self.__bipd_sm_to_be_inverted.get_string(NormalizeF, Option)           

        return msg

    side_info = property(deprecated, deprecated, deprecated, "Member 'side_info' deprecated!")

def do(core_sm, 
       begin_of_line_f=False, pre_context=None, 
       end_of_line_f=False,   post_context=None, 
       fh=-1, 
       AllowNothingIsNecessaryF = False,
       AllowStateMachineTrafoF  = True):

    assert type(begin_of_line_f) == bool
    assert type(end_of_line_f) == bool
    assert type(AllowNothingIsNecessaryF) == bool

    # Detect orphan states in the 'raw' state machines --> error in sm-building
    for sm in [pre_context, core_sm, post_context]:
        if sm is not None and sm.has_orphaned_states(): 
            error_msg("Orphaned state(s) detected in regular expression (optimization lack).\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
                      "Orphan state(s) = " + repr(sm.get_orphaned_state_index_list()), 
                      fh, DontExitF=True)

    if pre_context is not None and pre_context.is_empty():   error_msg("Empty pre-context pattern.", fh)
    if core_sm.is_empty():                                   error_msg("Empty pattern.", fh)
    if post_context is not None and post_context.is_empty(): error_msg("Empty post-context pattern.", fh)

    # Detect the 'Nothing is Necessary' error in a pattern.
    # (*) 'Nothing is necessary' cannot be accepted. See the discussion in the 
    #     module "quex.output.cpp.core"          
    if not AllowNothingIsNecessaryF:
        post_context_f = (post_context is not None)
        __detect_path_of_nothing_is_necessary(pre_context,  "pre context",  post_context_f, fh)
        __detect_path_of_nothing_is_necessary(core_sm,      "core pattern", post_context_f, fh)
        __detect_path_of_nothing_is_necessary(post_context, "post context", post_context_f, fh)

    return Pattern(core_sm, pre_context, post_context, 
                   begin_of_line_f, end_of_line_f, fh)

def __detect_path_of_nothing_is_necessary(sm, Name, PostContextPresentF, fh):
    assert Name in ["core pattern", "pre context", "post context"]

    if sm is None: return

    msg = "The %s contains in a 'nothing is necessary' path in the state machine.\n"   \
          % Name                                                                     + \
          "This means, that without reading a character the analyzer drops into\n"   + \
          "an acceptance state. "

    init_state = sm.get_init_state()

    if not init_state.is_acceptance(): return

    msg += { 
        "core pattern":
            "The analyzer would then stall.",

        "pre context":
            "E.g., pattern 'x*/y/' means that zero or more 'x' are a pre-\n"             + \
            "condition for 'y'. If zero appearances of 'x' are enough, then obviously\n" + \
            "there is no pre-context for 'y'! Most likely the author intended 'x+/y/'.",

        "post context":
            "A post context where nothing is necessary is superfluous.",
    }[Name]

    if Name != "post context" and PostContextPresentF:
        msg += "\n"                                                          \
               "Note: A post context does not change anything to that fact." 

    error_msg(msg, fh)

def __delete_forbidden_ranges(sm, fh):
    """Unicode does define all code points >= 0. Thus there can be no code points
       below zero as it might result from some number set operations.

       NOTE: This operation might result in orphaned states that have to 
             be deleted.
    """
    global Setup

    def range_error_msg(Character):
        error_msg(  "Pattern contains character 0x%0X which is beyond the scope of\n" \
                    % Character \
                  + "the buffer element size (%s)\n" \
                    % Setup.get_character_value_limit_str() + \
                  + "Please, cut the character range of the regular expression,\n"
                  + "adapt \"--buffer-element-size\" or \"--buffer-element-type\",\n"       + \
                  + "or specify '--buffer-element-size-irrelevant' to ignore the issue.", fh)

    character_value_limit = Setup.get_character_value_limit()

    for state in sm.states.values():

        for target_state_index, trigger_set in state.transitions().get_map().items():

            # Make sure, all transitions lie inside the unicode code range 
            interval_list = trigger_set.get_intervals(PromiseToTreatWellF=True)
            assert len(interval_list) != 0
            first = interval_list[0]
            if first.begin == - sys.maxint:
                if first.end < UnicodeInterval.begin:   range_error_msg(first.end - 1)
                first.begin = UnicodeInterval.begin
                if first.begin == first.end:            del interval_list[0]
            if len(interval_list) != 0:
                last  = interval_list[-1]
                if last.end == sys.maxint:
                    if last.begin >= character_value_limit: range_error_msg(last.begin)
                    last.end = character_value_limit
                    if last.begin == last.end:              del interval_list[-1]

            if Setup.buffer_codec in ["utf16-le", "utf16-be"]:
                # Delete the forbidden interval: D800-DFFF
                if trigger_set.has_intersection(ForbiddenRange):
                    error_msg("Pattern contains characters in unicode range 0xD800-0xDFFF.\n"
                              "This range is not covered by UTF16. Cutting Interval.", fh, DontExitF=True)
                    trigger_set.cut_interval(ForbiddenRange)
            
            # If the operation resulted in cutting the path to the target state, then delete it.
            if trigger_set.is_empty():
                state.transitions().delete_transitions_to_target(target_state_index)

