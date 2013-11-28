from   quex.engine.misc.file_in                        import error_msg
from   quex.engine.generator.code.core                 import PatternActionInfo
import quex.engine.generator.state_machine_coder       as     state_machine_coder
import quex.engine.generator.state_router              as     state_router_generator
from   quex.engine.generator.languages.variable_db     import variable_db
from   quex.engine.generator.code_fragment_base        import CodeFragment
from   quex.engine.analyzer.door_id_address_label      import DoorID, \
                                                              IfDoorIdReferencedCode, \
                                                              get_plain_strings, \
                                                              dial_db
import quex.engine.state_machine.parallelize           as     parallelize
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
import quex.engine.state_machine.index                 as     index
from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.transformation        as     transformation
from   quex.engine.generator.state.transition.code     import TransitionCodeFactory
import quex.engine.generator.state.transition.core     as     transition_block
import quex.engine.generator.reload_state              as     reload_state_coder
import quex.engine.analyzer.engine_supply_factory      as     engine
from   quex.engine.analyzer.transition_map             import TransitionMap
import quex.engine.analyzer.core                       as     analyzer_generator
from   quex.engine.analyzer.state.core                 import ReloadState
from   quex.engine.analyzer.terminal.factory           import TerminalStateFactory
import quex.engine.analyzer.engine_supply_factory      as     engine_supply_factory
from   quex.engine.interval_handling                   import NumberSet, Interval, NumberSet_All
from   quex.input.files.counter_db                     import CounterDB, \
                                                              CounterCoderData
from   quex.input.files.counter_setup                  import LineColumnCounterSetup_Default
from   quex.input.regular_expression.construct         import Pattern
import quex.output.cpp.counter_for_pattern             as     counter_for_pattern

from   quex.engine.tools                               import all_isinstance, \
                                                              none_is_None
from   quex.blackboard import E_IncidenceIDs, \
                              E_StateIndices, \
                              E_MapImplementationType, \
                              setup as Setup

from   itertools   import ifilter
import re
from   copy        import copy, deepcopy
from   collections import defaultdict

Match_input    = re.compile("\\binput\\b", re.UNICODE)
Match_iterator = re.compile("\\iterator\\b", re.UNICODE)

class GeneratorBase:
    def __init__(self, ModeName, PatternList, IncidenceDb, IndentationSupportF, BeginOfLineSupportF):
        assert isinstance(PatternList, list)
        assert isinstance(IncidenceDb, dict)
        assert type(IndentationSupportF) == bool
        assert type(BeginOfLineSupportF) == bool
        # Function '.prepare_count_info()' must have been called before a 
        # a pattern can be considered here. Note, that '.prepare_count_info()'
        # must be called before any code transformation.
        assert none_is_None(pattern.count_info() for pattern in PatternList)

        # (*) Core SM, Pre-Context SM, ...
        #     ... and sometimes backward input position SMs.
        self.sm,                    \
        self.pre_context_sm,        \
        self.bipd_sm_db,            \
        self.pre_context_sm_id_list = self.__prepare_main_state_machines(PatternList)

        self.counter_db, \
        self.default_character_counter_required_f = self.__prepare_line_column_count_db(PatternList)

        # (*) Terminal States
        self.terminal_db = self.__prepare_terminals(ModeName, 
                                                    IncidenceDb, PatternList,
                                                    IndentationSupportF, BeginOfLineSupportF)

    def __prepare_main_state_machines(self, PatternList):
        # -- setup of state machine lists and id lists
        core_sm_list,                 \
        pre_context_sm_list,          \
        incidence_id_and_bipd_sm_list = self.__prepare_sm_lists(PatternList)

        # (*) Create (combined) state machines
        #     Backward input position detection (bipd) remains separate engines.
        return get_combined_state_machine(core_sm_list),                  \
               get_combined_state_machine(pre_context_sm_list,            \
                                          FilterDominatedOriginsF=False), \
               dict((incidence_id, sm) for incidence_id, sm in incidence_id_and_bipd_sm_list), \
               [ sm.get_id() for sm in pre_context_sm_list ]

    def __prepare_line_column_count_db(self, PatternList):
        LanguageDB = Setup.language_db

        default_counter_f = False
        result = {}
        for pattern in PatternList:
            requires_default_counter_f, \
            count_text                  = counter_for_pattern.get(pattern)
            count_text = "".join(LanguageDB.REPLACE_INDENT(count_text))

            default_counter_f |= requires_default_counter_f

            result[pattern.incidence_id()] = count_text

        return result, default_counter_f

    def __prepare_terminals(self, ModeName, IncidenceDb, PatternList, 
                            IndentationSupportF, BeginOfLineSupportF):

        factory = TerminalStateFactory(ModeName, IncidenceDb, 
                                       self.counter_db, self.default_character_counter_required_f, 
                                       IndentationSupportF, BeginOfLineSupportF)

        result = {}
        for incidence_id, code_fragment in IncidenceDb.iteritems():
            if    incidence_id == E_IncidenceIDs.END_OF_STREAM \
               or incidence_id == E_IncidenceIDs.FAILURE:
                continue

            terminal = factory.do(incidence_id, code_fragment)
            # The factory returns 'None' if the incidence is not related to a
            # dedicated terminal state, e.g. 'ON_MATCH', 'NODENT', etc.
            if terminal is None: continue

            result[incidence_id] = terminal

        result[E_IncidenceIDs.END_OF_STREAM] = factory.do_OnEndOfStream()
        result[E_IncidenceIDs.FAILURE]       = factory.do_OnFailure()

        return result

    def __prepare_sm_lists(self, PatternList):
        # -- Core state machines of patterns
        state_machine_list = [ pattern.sm for pattern in PatternList ]

        # -- Pre-Contexts
        pre_context_sm_list = [    
            pattern.pre_context_sm for pattern in PatternList \
            if pattern.pre_context_sm is not None 
        ]

        # -- Backward input position detection (BIPD)
        bipd_sm_list = [
            (pattern.incidence_id(), pattern.bipd_sm) for pattern in PatternList \
            if pattern.bipd_sm is not None 
        ]
        return state_machine_list, pre_context_sm_list, bipd_sm_list

# MAIN:      sm --> analyzer
#            sm_txt --> code_analyzer
#            terminal_txt --> code_terminals
#
# PRE_SM:    pre_sm --> analyzer
#            pre_sm_txt --> code_analyzer
#            terminal = begin of core
#
# BIPD_SM-s: bipd_sm -> analyzer
#            bipd_sm_txt -> code_analyzer
#            termina = terminal for which BIPD operated
#
# COUNT_SM:  count_db --> count_sm
#            analyzer  = get_analyzer
#            modify analyzer
#            terminal = exit_door_id
#
# SKIPER_SM:
#
# RANGE_SKIPPER_SM:
#
# NESTER_RANGE_SKIPPER_SM:
#
# INDENTATION_DETECTOR_SM:

def do_main(SM, BipdEntryDoorIdDb):
    """Main pattern matching state machine (forward).
    ---------------------------------------------------------------------------
    Micro actions are: line/column number counting, position set/reset,
    last acceptance setting/reset, lexeme start pointer set/reset, setting
    terminating zero for lexeme/reset, setting last character. 

            DropOut     --> FAILURE
            BLC         --> ReloadStateForward
            EndOfStream --> END_OF_STREAM

    Variables (potentially) required:

            position, PositionRegisterN, last_acceptance, input.
    """
    txt, analyzer = do_state_machine(SM, engine.Class_FORWARD(BipdEntryDoorIdDb))

    # Number of different entries in the position register map
    position_register_n = len(set(analyzer.position_register_map.itervalues()))
    # Position registers
    if position_register_n == 0:
        variable_db.require("position",          Initial = "(void*)0x0", Type = "void*")
        variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % position_register_n)
    else:
        variable_db.require_array("position", ElementN = position_register_n,
                                  Initial  = "{ " + ("0, " * (position_register_n - 1) + "0") + "}")
        variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % position_register_n)

    if analyzer.last_acceptance_variable_required():
        variable_db.require("last_acceptance")

    return txt, analyzer.reload_state

def do_pre_context(SM, PreContextSmIdList):
    """Pre-context detecting state machine (backward).
    ---------------------------------------------------------------------------
    Micro actions are: pre-context fullfilled_f

            DropOut     --> Begin of 'main' state machine.
            BLC         --> ReloadStateBackward
            EndOfStream --> 'error'

    Variables (potentially) required:

            pre_context_fulfilled_f[N] --> Array of flags for pre-context
                                           indication.
    RETURNS: [0] generated code text
             [1] reload state BACKWARD, to be generated later.
    """
    LanguageDB = Setup.language_db

    if SM is None: 
        return [], None

    txt, analyzer = do_state_machine(SM, engine.BACKWARD_PRE_CONTEXT) 

    txt.append("\n%s:" % dial_db.get_label_by_door_id(DoorID.global_end_of_pre_context_check()))
    # -- set the input stream back to the real current position.
    #    during backward lexing the analyzer went backwards, so it needs to be reset.
    txt.append("    %s\n" % LanguageDB.INPUT_P_TO_LEXEME_START())

    for sm_id in PreContextSmIdList:
        variable_db.require("pre_context_%i_fulfilled_f", Index = sm_id)

    return txt, analyzer.reload_state

def do_backward_input_position_detectors(BipdDb):
    result = []
    bipd_entry_door_id_db = {}
    for incidence_id, bipd_sm in BipdDb.iteritems():
        txt, analyzer = do_state_machine(bipd_sm, engine.Class_BACKWARD_INPUT_POSITION(incidence_id)) 
        bipd_entry_door_id_db[incidence_id] = analyzer.get_action_at_state_machine_entry().door_id
        result.extend(txt)
    return result, bipd_entry_door_id_db

def do_reload_procedures(ReloadForwardState, ReloadBackwardState):
    """Lazy (delayed) code generation of the forward and backward reloaders. 
    Any state who needs reload may 'register' in a reloader. This registering may 
    happen after the code generation of forward or backward state machine.
    """
    # Variables that tell where to go after reload success and reload failure
    if Setup.buffer_based_analyzis_f:               
        return

    txt = []
    if ReloadForwardState is not None:
        txt.extend(reload_state_coder.do(ReloadForwardState))
    if ReloadBackwardState is not None:
        txt.extend(reload_state_coder.do(ReloadBackwardState))

    variable_db.require("target_state_else_index")  # upon reload failure
    variable_db.require("target_state_index")       # upon reload success

    return txt

def do_state_router():
    routed_address_set = dial_db.routed_address_set()
    # If there is only one address subject to state routing, then the
    # state router needs to be implemented.
    #if len(routed_address_set) == 0:
    #    return []

    # Add the address of 'terminal_end_of_file()' if it is not there, already.
    # (It should: assert address_eof in routed_address_set
    address_eof        = dial_db.get_address_by_door_id(DoorID.incidence(E_IncidenceIDs.END_OF_STREAM)) 
    routed_address_set.add(address_eof)
    dial_db.mark_label_as_gotoed(dial_db.get_label_by_address(address_eof))

    routed_state_info_list = state_router_generator.get_info(routed_address_set)
    return state_router_generator.do(routed_state_info_list) 

def do_variable_definitions():
    LanguageDB = Setup.language_db

    # Target state index
    variable_db.require("target_state_index", Condition_ComputedGoto=False) 

    # Following function refers to the global 'variable_db'
    return LanguageDB.VARIABLE_DEFINITIONS(variable_db)

def do_state_machine(sm, EngineType): 
    assert len(sm.get_orphaned_state_index_list()) == 0
    LanguageDB = Setup.language_db

    txt = []
    # -- [optional] comment state machine transitions 
    if Setup.comment_state_machine_f: 
        LanguageDB.COMMENT_STATE_MACHINE(txt, sm)

    # -- implement the state machine itself
    analyzer = analyzer_generator.do(sm, EngineType)
    return do_analyzer(analyzer), analyzer

def do_analyzer(analyzer): 
    LanguageDB = Setup.language_db

    state_machine_code = state_machine_coder.do(analyzer)
    LanguageDB.REPLACE_INDENT(state_machine_code)
    # Variable to store the current input
    variable_db.require("input") 
    return state_machine_code

def do_terminals(TerminalDb, SimpleF=False):
    LanguageDB = Setup.language_db

    lexeme_macro_definition_str = ""
    if not SimpleF:
        lexeme_macro_definition_str = LanguageDB.TERMINAL_LEXEME_MACRO_DEFINITIONS()

        # Pattern match terminals goto 'Re-entry' by default
        goto_reentry_str = "\n    %s" % LanguageDB.GOTO_BY_DOOR_ID(DoorID.global_reentry_preparation())

        for incidence_id, terminal_state in TerminalDb.iteritems():
            if   incidence_id == E_IncidenceIDs.END_OF_STREAM: continue
            elif incidence_id == E_IncidenceIDs.FAILURE:       continue
            elif incidence_id == E_IncidenceIDs.AFTER_MATCH:   continue

            terminal_state.code_fragment.append_text(goto_reentry_str)

    terminal_states_txt = LanguageDB.TERMINAL_CODE(TerminalDb) 
    assert all_isinstance(terminal_states_txt, (str, unicode, IfDoorIdReferencedCode, int))

    txt = [ lexeme_macro_definition_str ]
    txt.extend(terminal_states_txt)

    return txt

def do_reentry_preparation(PreContextSmIdList, TerminalDb):
    LanguageDB = Setup.language_db
    return LanguageDB.REENTRY_PREPARATION(PreContextSmIdList, 
                                          TerminalDb.get(E_IncidenceIDs.AFTER_MATCH))

def do_loop(CounterDb, AfterExitDoorId, CharacterSet=None, CheckLexemeEndF=False, ReloadF=False, GlobalReloadState=None):
    """Buffer Limit Code --> Reload
       Skip Character    --> Loop to Skipper State
       Else              --> Exit Loop
    """
    assert CharacterSet is None or isinstance(CharacterSet, NumberSet)

    if CharacterSet is None:
        CharacterSet = NumberSet_All()

    ccd                     = CounterCoderData(CounterDb, CharacterSet, AfterExitDoorId)
    analyzer, exit_terminal = ccd.get_analyzer(engine.CHARACTER_COUNTER, GlobalReloadState, CheckLexemeEndF=CheckLexemeEndF)

    code                    = state_machine_coder.do(analyzer)

    terminal_db = { exit_terminal.incidence_id(): exit_terminal, }

    code.extend(do_terminals(terminal_db, SimpleF=True))

    if ReloadF and not GlobalReloadState:
        reload_code = Generator.code_reload_procedures(analyzer.reload_state, None)
        code.extend(reload_code)
        variable_db.require("position",          Initial = "(void*)0x0", Type = "void*")
        variable_db.require("PositionRegisterN", Initial = "(size_t)%i" % 0)

    variable_db.require("input") 
    # Upon reload, the reference pointer may have to be added. When the reload is
    # done the reference pointer needs to be reset. 
    if ccd.column_count_per_chunk is not None:
        variable_db.require("reference_p")

    return code

class LoopGenerator(GeneratorBase):
    @classmethod
    def code_action_map(cls, TM, IteratorName, 
                        BeforeReloadAction, AfterReloadAction, OnContinue):
        """TM is an object in the form of a 'transition map'. That is, it maps
        from an interval to an action--in this case not necessarily a state 
        transition. It consists of a list of pairs:

                               (interval, action)

        where the list is sorted by the interval's begin. Intervals shall not 
        interleave.

        NOTE: In case of a state machine implementation, this task does NOT 
              implement standard terminals such as FAILURE or END_OF_STREAM! 
        """
        global Match_input
        global Match_iterator
        LanguageDB = Setup.language_db
        #TM.assert_adjacency() # EOF needs to be considered!

        reload_f           = (BeforeReloadAction is not None)
        ImplementationType = cls.determine_implementation_type(TM, reload_f)

        # (*) Implement according to implementation type.
        if ImplementationType == E_MapImplementationType.PLAIN_MAP:
            complete_f, transformed_tm = transformation.do_transition_map(TM)
            # This is only a work-around until 'on_codec_error' is implemented
            on_codec_error = copy(OnContinue)
            on_codec_error.insert(0, "%s\n" % LanguageDB.INPUT_P_INCREMENT())
            transformed_tm.fill_gaps(on_codec_error)
            txt = cls.code_action_map_plain(transformed_tm, BeforeReloadAction, AfterReloadAction)

        elif ImplementationType == E_MapImplementationType.STATE_MACHINE_TRIVIAL:
            # In case of variable character sizes, there can be no 'column_n +=
            # (iterator - reference_p) * C'. Thus, there is no 'AfterReloadAction'.
            # NOTE: code_action_state_machine_trivial() --> code_action_map_plain()
            txt = cls.code_action_state_machine_trivial(TM, BeforeReloadAction, AfterReloadAction)

        elif ImplementationType == E_MapImplementationType.STATE_MACHINE:
            txt = cls.code_action_state_machine(TM, BeforeReloadAction, AfterReloadAction)

        else:
            assert False

        return ImplementationType, \
               cls.replace_iterator_name(txt, IteratorName, ImplementationType)

    @classmethod
    def determine_implementation_type(cls, TM, ReloadF):
        if Setup.variable_character_sizes_f():
            if     not ReloadF \
               and cls.state_machine_trivial_possible(TM):
                return E_MapImplementationType.STATE_MACHINE_TRIVIAL
            else:
                return E_MapImplementationType.STATE_MACHINE
        else:
            return E_MapImplementationType.PLAIN_MAP

    @classmethod
    def code_action_map_plain(cls, TM, BeforeReloadAction=None, AfterReloadAction=None):
        TM.assert_adjacency()

        pseudo_state_index = dial_db.new_address()
        LanguageDB         = Setup.language_db

        if BeforeReloadAction is None: 
            engine_type = engine.CHARACTER_COUNTER
        else:                          
            engine_type = engine.FORWARD
            AfterReloadAction.insert(0, "%s\n" % LanguageDB.INPUT_P_INCREMENT())
            AfterReloadAction.insert(0, 1)

            TM.set_target(Setup.buffer_limit_code, DoorID.drop_out(pseudo_state_index))
            BeforeReloadAction.append("%s\n" % LanguageDB.LEXEME_START_SET())

            #TM.replace_action_id(E_IncidenceIDs.EXIT_LOOP,
            #                     [1, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])

        TM.insert_after_action_id(E_IncidenceIDs.GOOD_TRANSITION,
                                  [2, "%s\n" % LanguageDB.INPUT_P_INCREMENT()])

        # The range of possible characters may be restricted. It must be ensured,
        # that the occurring characters only belong to the admissible range.
        TM.prune(0, Setup.get_character_value_limit())

        # Now, we start with code generation. The signalizing ActionIDs must be deleted.
        TM.delete_action_ids()

        txt = []
        if BeforeReloadAction is not None:
            assert engine_type.requires_buffer_limit_code_for_reload()
            cls.code_generation_reload_preparation(txt, pseudo_state_index)

        #TransitionCodeFactory.init(engine_type, StateIndex = pseudo_state_index)

        if BeforeReloadAction is not None:
            TransitionCodeFactory.prepare_reload_tansition(TM, pseudo_state_index)

        tm = TransitionMap.from_iterable(TM, TransitionCodeFactory.do)

        #LanguageDB.code_generation_switch_cases_add_statement("break;")
        transition_block.do(txt, tm)
        #LanguageDB.code_generation_switch_cases_add_statement(None)

        reload_txt = []
        if BeforeReloadAction is not None:
            assert engine_type.requires_buffer_limit_code_for_reload()
            cls.code_generation_reload_clean_up(reload_txt, BeforeReloadAction, AfterReloadAction)

        return txt + reload_txt

    @classmethod
    def code_action_state_machine(cls, TM, BeforeReloadAction, AfterReloadAction):
        """Generates a state machine that represents the transition map 
        according to the codec given in 'Setup.buffer_codec_transformation_info'
        """
        LanguageDB = Setup.language_db
        assert TM is not None

        # Here, characters are made up of more than one 'chunk'. When the last
        # character needs to be reset, its start position must be known. For 
        # this the 'lexeme start pointer' is used.
        if      BeforeReloadAction is not None \
            and TM.has_action_id(E_IncidenceIDs.EXIT_LOOP,):
            variable_db.require("character_begin_p")

            loop_epilog = [1, "%s\n" % LanguageDB.CHARACTER_BEGIN_P_SET()]
            TM.replace_action_id(E_IncidenceIDs.EXIT_LOOP, 
                                 [1, "%s\n" % LanguageDB.INPUT_P_TO_CHARACTER_BEGIN_P()])
            BeforeReloadAction.append("%s\n" % LanguageDB.LEXEME_START_TO_CHARACTER_BEGIN_P())
            AfterReloadAction.append("%s\n" % LanguageDB.CHARACTER_BEGIN_P_TO_LEXEME_START_P())
        else:
            loop_epilog = []

        # Now, we start with code generation. The signalizing ActionIDs must be deleted.
        TM.delete_action_ids()

        pattern_list, incidence_db = get_pattern_list_and_incidence_id_from_map(TM)
        counter_db = CounterDB(LineColumnCounterSetup_Default())
        for pattern in pattern_list:
            pattern.prepare_count_info(counter_db, Setup.buffer_codec_transformation_info)
            pattern.transform(Setup.buffer_codec_transformation_info)

        generator = Generator("Loop%i" % index.get(), pattern_list, incidence_db, IndentationSupportF=False, BeginOfLineSupportF=False) 

        if BeforeReloadAction is None: 
            engine_type = engine.CHARACTER_COUNTER
        else:                          
            engine_type = engine.FORWARD
            generator.sm.delete_transitions_on_interval(Interval(Setup.buffer_limit_code))
            generator.sm.delete_orphaned_states()

        if BeforeReloadAction is not None:
            cls.code_generation_reload_preparation(loop_epilog)

        sm_txt,       \
        terminal_txt, \
        analyzer      = generator.code_state_machine_core(engine_type, SimpleF=True)

        # self.reload_state_forward.absorb(analyzer.reload_state)

        reload_txt = []
        if BeforeReloadAction is not None:
            cls.code_generation_reload_clean_up(reload_txt, BeforeReloadAction, AfterReloadAction)

        return loop_epilog + sm_txt + terminal_txt + reload_txt

    @classmethod
    def code_generation_reload_preparation(cls, txt, UponReloadDoneAdr=None):
        LanguageDB = Setup.language_db
        reload_adr   = dial_db.new_address()
        reload_label = dial_db.get_label_by_address(reload_adr) 
        LanguageDB.code_generation_reload_label_set(reload_label)

        address = dial_db.get_address_by_door_id(DoorID.incidence(E_IncidenceIDs.END_OF_STREAM))
        dial_db.mark_address_as_routed(address)
        LanguageDB.code_generation_on_reload_fail_adr_set(address)

        if UponReloadDoneAdr is not None:
            txt.append("%s:\n" % dial_db.get_label_by_address(UponReloadDoneAdr))

    @staticmethod
    def code_generation_reload_clean_up(txt, BeforeReloadAction, AfterReloadAction):
        LanguageDB = Setup.language_db
        txt.extend(LanguageDB.RELOAD_SPECIAL(BeforeReloadAction, AfterReloadAction))
        LanguageDB.code_generation_reload_label_set(None)
        LanguageDB.code_generation_on_reload_fail_adr_set(None)

    @staticmethod
    def state_machine_trivial_possible(tm):
        """Checks whether the 'trivial' implementation of the state machine 
        for UTF8 or UTF16 is possible. 

        IDEA: If all characters > LowestRangeBorder cause the same action.
              then a trivial map can be implemented:

              if( *iterator > LowestRangeBorder ) {
                  Action
                  Increment iterator according to incoming bytes
              }
              Transition map based on a single chunk '*iterator'.
        """
        if   Setup.buffer_codec_transformation_info == "utf8-state-split":
            LowestRangeBorder = 0x80 
        elif Setup.buffer_codec_transformation_info == "utf16-state-split":
            LowestRangeBorder = 0x10000 
        else:
            return False

        if tm[-1][0].begin >= LowestRangeBorder: 
            return False

        return True

    @classmethod
    def code_action_state_machine_trivial(cls, tm, BeforeReloadAction, AfterReloadAction):
        """This function tries to provide easy solutions for dynamic character
        length encodings, such as UTF8 or UTF16. 
        
        The simplification:

        Check whether all critical checks from inside the 'counter_db' happen in
        the range where there is only one chunk considered (UTF8->1byte at x <
        0x800, UTF16->2byte at x < 0x10000). The range is identified by
        'LowestRangeBorder'. Then implement a simple transition map for this range.
        The remainder of the counter function only implements the input pointer
        increments. They come from a template string given by
        'IncrementActionStr'.

        NOTE: Currently, this is only implemented for 'counter'. Nothing where
        reload is involved may use this function.

        RETURNS: None -- if no easy solution could be provided.
                 text -- the implementation of the counter functionh.
        """
        global _increment_actions_for_utf16
        global _increment_actions_for_utf8
       
        # Currently, we do not handle the case 'Reload': refuse to work.
        assert BeforeReloadAction is None
        assert cls.state_machine_trivial_possible(tm)
        tm.assert_continuity() #, str([x[0] for x in tm])

        # (*) Try to find easy and elegant special solutions 
        if   Setup.buffer_codec_transformation_info == "utf8-state-split":
            IncrementActionStr = _increment_actions_for_utf8
        elif Setup.buffer_codec_transformation_info == "utf16-state-split":
            IncrementActionStr = _increment_actions_for_utf16
        else:
            assert False

        # (*) Add increment actions to the actions
        def add_increment(action, IncrementActionStr, LastF):
            if LastF:
                action = deepcopy(action) # disconnect from same action on other interval
                assert E_IncidenceIDs.GOOD_TRANSITION in action
                idx = action.index(E_IncidenceIDs.GOOD_TRANSITION)
                # Delete 'GOOD_TRANSITION' prevents 
                # 'code_action_map_plain()' from adding '++iterator'.
                del action[idx]
                for x in reversed(IncrementActionStr):
                    action.insert(idx, x)
            return action

        LastI = len(tm) - 1
        tm = TransitionMap.from_iterable(
             (x[0], add_increment(x[1], IncrementActionStr, LastF=(i==LastI))) 
             for i, x in enumerate(tm) 
        )

        # (*) The first interval may start at - sys.maxint
        if tm[0][0].begin < 0: tm[0][0].begin = 0

        # Later interval shall not be less than 0!
        assert tm[0][0].end > 0

        # Code the transition map
        return cls.code_action_map_plain(tm) # No reload possible (see entry assert) 

    @staticmethod
    def replace_iterator_name(txt, IteratorName, ImplementationType):
        assert ImplementationType in E_MapImplementationType
        StateMachineF = (ImplementationType == E_MapImplementationType.STATE_MACHINE)
        def replacer(block, StateMachineF):
            if block.find("me->buffer._input_p") != -1: 
                block = block.replace("me->buffer._input_p", "(%s)" % IteratorName)
            if not StateMachineF:
                block = Match_input.sub("(*%s)" % IteratorName, block)
                block = Match_iterator.sub("(%s)" % IteratorName, block)
            return block

        for i, elm in enumerate(txt):
            if not isinstance(elm, (str, unicode)): continue
            txt[i] = replacer(elm, StateMachineF)

        return txt

def get_combined_state_machine(StateMachine_List, FilterDominatedOriginsF=True):
    """Creates a DFA state machine that incorporates the paralell
       process of all pattern passed as state machines in 
       the StateMachine_List. Each origins of each state machine
       are kept in the final state, if it is not dominated.

       Performs: -- parallelization
                 -- translation from NFA to DFA
                 -- Frank Schaefers Adapted Hopcroft optimization.

       Again: The state machine ids of the original state machines
              are traced through the whole process.
              
       FilterDominatedOriginsF, if set to False, can disable the filtering
              of dominated origins. This is important for pre-contexts, because,
              all successful patterns need to be reported!            
                      
    """   
    if len(StateMachine_List) == 0:
        return None

    def __check(Place, sm):
        __check_on_orphan_states(Place, sm)
        __check_on_init_state_not_acceptance(Place, sm)

    def __check_on_orphan_states(Place, sm):
        orphan_state_list = sm.get_orphaned_state_index_list()
        if len(orphan_state_list) == 0: return
        error_msg("After '%s'" % Place + "\n" + \
                  "Orphaned state(s) detected in regular expression (optimization lack).\n" + \
                  "Please, log a defect at the projects website quex.sourceforge.net.\n"    + \
                  "Orphan state(s) = " + repr(orphan_state_list)) 

    def __check_on_init_state_not_acceptance(Place, sm):
        init_state = sm.get_init_state()
        if init_state.is_acceptance():
            error_msg("After '%s'" % Place + "\n" + \
                      "The initial state is 'acceptance'. This should never appear.\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n")

        for dummy in ifilter(lambda origin: origin.is_acceptance(), init_state.origins()):
            error_msg("After '%s'" % Place + "\n" + \
                      "Initial state contains an origin that is 'acceptance'. This should never appear.\n" + \
                      "Please, log a defect at the projects website quex.sourceforge.net.\n")

    # (1) mark at each state machine the machine and states as 'original'.
    #      
    #     This is necessary to trace in the combined state machine the
    #     pattern that actually matched. Note, that a state machine in
    #     the StateMachine_List represents one possible pattern that can
    #     match the current input.   
    #
    for sm in StateMachine_List:
        sm.mark_state_origins()
        assert sm.is_DFA_compliant(), sm.get_string(Option="hex")

    # (2) setup all patterns in paralell 
    sm = parallelize.do(StateMachine_List, CommonTerminalStateF=False) #, CloneF=False)
    __check("Parallelization", sm)

    # (4) determine for each state in the DFA what is the dominating original state
    if FilterDominatedOriginsF: sm.filter_dominated_origins()
    __check("Filter Dominated Origins", sm)

    # (3) convert the state machine to an DFA (paralellization created an NFA)
    sm = beautifier.do(sm)
    __check("NFA to DFA, Hopcroft Minimization", sm)
    
    return sm

def get_pattern_list_and_incidence_id_from_map(TM):
    """Returns a state machine list which implements the transition map given
    in unicode. It is assumed that the codec is a variable
    character size codec. Each count action is associated with a separate
    state machine in the list. The association is recorded in 'action_db'.

    RETURNS: [0] -- The 'action_db': state_machine_id --> count action
             [1] -- The list of state machines. 
    """
    # Sort by actions.
    action_code_db = defaultdict(NumberSet)
    for character_set, action_list in TM:
        if hasattr(action_list, "drop_out_f") and action_list.drop_out_f(): continue
        assert isinstance(action_list, list)
        # Make 'action_list' a tuple so that it is hash-able
        action_code_db[tuple(action_list)].unite_with(character_set)

    pattern_list = []
    incidence_db = {}
    for action, trigger_set in action_code_db.iteritems():
        # Make 'action' a list again, so that it can be used as CodeFragment
        pattern = Pattern(StateMachine.from_character_set(trigger_set))
        pattern_list.append(pattern)
        incidence_db[pattern.incidence_id()] = CodeFragment(action)

    return pattern_list, incidence_db

_increment_actions_for_utf8 = [
     1, "if     ( ((*iterator) & 0x80) == 0 ) { iterator += 1; } /* 1byte character */\n",
     1, "/* NOT ( ((*iterator) & 0x40) == 0 ) { iterator += 2; }    2byte character */\n",
     1, "else if( ((*iterator) & 0x20) == 0 ) { iterator += 2; } /* 2byte character */\n",
     1, "else if( ((*iterator) & 0x10) == 0 ) { iterator += 3; } /* 3byte character */\n",
     1, "else if( ((*iterator) & 0x08) == 0 ) { iterator += 4; } /* 4byte character */\n",
     1, "else if( ((*iterator) & 0x04) == 0 ) { iterator += 5; } /* 5byte character */\n",
     1, "else if( ((*iterator) & 0x02) == 0 ) { iterator += 6; } /* 6byte character */\n",
     1, "else if( ((*iterator) & 0x01) == 0 ) { iterator += 7; } /* 7byte character */\n",
     1, "else                                 { iterator += 1; } /* default 1       */\n",
]
    
_increment_actions_for_utf16 = [
     1, "if( *iterator >= 0xD800 && *iterator < 0xE000 ) { iterator += 2; }\n",
     1, "else                                            { iterator += 1; }\n", 
]
    
