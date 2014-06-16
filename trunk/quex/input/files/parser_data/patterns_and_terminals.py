from   quex.input.files.mode_option                    import SkipRangeData
from   quex.input.regular_expression.construct         import Pattern           
from   quex.input.files.consistency_check              import __error_message as c_error_message
from   quex.engine.counter                             import CountCmdFactory
from   quex.engine.analyzer.terminal.core              import Terminal
from   quex.engine.analyzer.terminal.factory           import TerminalFactory
from   quex.engine.analyzer.door_id_address_label        import DoorID, dial_db
import quex.engine.generator.skipper.character_set       as   skip_character_set
import quex.engine.generator.skipper.range               as   skip_range
import quex.engine.generator.skipper.nested_range        as   skip_nested_range
import quex.engine.generator.skipper.indentation_counter as   indentation_counter
from   quex.engine.generator.code.core                 import CodeTerminal, \
                                                              CodeTerminalOnMatch
import quex.engine.state_machine.check.superset        as     superset_check
import quex.engine.state_machine.check.identity        as     identity_checker
import quex.engine.state_machine.repeat                as     repeat
import quex.engine.state_machine.sequentialize         as     sequentialize
import quex.engine.state_machine.algorithm.beautifier  as     beautifier

from   quex.engine.tools import typed
import quex.blackboard as blackboard
from   quex.blackboard import setup as Setup, \
                              Lng, \
                              E_IncidenceIDs, \
                              E_TerminalType
from   quex.engine.misc.file_in import error_msg
import types
from   copy        import deepcopy
from   collections import namedtuple
from   operator    import attrgetter

class PatternPriority(object):
    """Description of a pattern's priority.
    ___________________________________________________________________________
    PatternPriority-s are possibly adapted according the re-priorization 
    or other 'mode-related' mechanics. Thus, they cannot be named tuples.
    ___________________________________________________________________________
    """
    __slots__ = ("mode_hierarchy_index", "pattern_index")
    def __init__(self, MHI, PatternIdx):
        self.mode_hierarchy_index = MHI
        self.pattern_index        = PatternIdx

    def __cmp__(self, Other):
        if   self.mode_hierarchy_index > Other.mode_hierarchy_index: return 1
        elif self.mode_hierarchy_index < Other.mode_hierarchy_index: return -1
        elif self.pattern_index > Other.pattern_index:               return 1
        elif self.pattern_index < Other.pattern_index:               return -1
        else:                                                        return 0

class PPT(namedtuple("PPT_tuple", ("priority", "pattern", "code_fragment"))):
    """PPT -- (Priority, Pattern, Terminal) 
    ______________________________________________________________________________

    Collects information about a pattern, its priority, and the terminal 
    to be executed when it triggers. Objects of this class are intermediate
    they are not visible outside class 'Mode'.
    ______________________________________________________________________________
    """
    @typed(ThePatternPriority=PatternPriority, TheTerminal=Terminal)
    def __new__(self, ThePatternPriority, ThePattern, TheTerminal):
        return super(PPT, self).__new__(self, ThePatternPriority, ThePattern, TheTerminal)

def get(BaseModeSequence, OptionsDb, CounterDb, IncidenceDb):
    """Priority, Pattern, Terminal List: 'ppt_list'
    -----------------------------------------------------------------------
    The 'ppt_list' is the list of eXtended Pattern Action Pairs.
    Each element in the list consist of
    
        .priority 
        .pattern
        .terminal
    
    The pattern priority allows to keep the list sorted according to its
    priority given by the mode's position in the inheritance hierarchy and
    the pattern index itself.
    -----------------------------------------------------------------------
    """ 
    mode_name        = BaseModeSequence[-1].name
    terminal_factory = TerminalFactory(mode_name, IncidenceDb) 

    # -- Pattern/Actions of the the mode
    ppt_list = _pattern_collect(BaseModeSequence, CounterDb, terminal_factory)
    extra_terminal_list = []

    # -- Collect patterns and terminals which are required to implement
    #    skippers and indentation counters.
    for i, func in enumerate((_prepare_skip_character_set, _prepare_skip_range, 
                              _prepare_skip_nested_range, _prepare_indentation_counter)):
        new_extra_terminals, \
        new_ppts             = func(mode_name, OptionsDb, CounterDb, IncidenceDb, 
                                    terminal_factory, MHI=-4+i)
        extra_terminal_list.extend(new_extra_terminals)
        ppt_list.extend(new_ppts)

    # -- Evaluate the DELETE and PRIORITY-MARK commands
    history_deletion,        \
    history_reprioritization = _pattern_delete_and_reprioritize(ppt_list, 
                                                                BaseModeSequence)

    # -- Setup the pattern list and the terminal db
    pattern_list, \
    terminal_db   = finalize(ppt_list, CounterDb, IncidenceDb, 
                             extra_terminal_list, terminal_factory)

    return pattern_list, \
           terminal_db, \
           terminal_factory.required_default_counter_f, \
           history_deletion, \
           history_reprioritization

def finalize(ppt_list, CounterDb, IncidenceDb, extra_terminal_list, terminal_factory):
    """Finalizes the terminal_db and pattern list resulting from the PPT-List.
    """
    terminal_db  = finalize_terminal_db(ppt_list, IncidenceDb, 
                                        extra_terminal_list, terminal_factory)

    pattern_list = finalize_pattern_list(ppt_list, CounterDb)

    return pattern_list, terminal_db

def finalize_terminal_db(SortedPPT_List, IncidenceDb, ExtraTerminalList, terminal_factory):
    """Prepare terminal states for all pattern matches and other terminals,
    such as 'end of stream' or 'failure'. If code is to be generated in a
    delayed fashion, then this may happen as a consequence to the call
    to '.get_code()' to related code fragments.

    RETURNS: 
                      map: incidence_id --> Terminal

    A terminal consists plainly of an 'incidence_id' and a list of text which
    represents the code to be executed when it is reached.
    """
    # Every pattern has a terminal for the case that it matches.
    result = dict(
        (terminal.incidence_id(), terminal)
        for dummy, dummy, terminal in SortedPPT_List
    )

    # Some incidences have their own terminal
    # THEIR INCIDENCE ID REMAINS FIXED!
    result.update(
        IncidenceDb.extract_terminal_db(terminal_factory)
    )

    for terminal in ExtraTerminalList:
        if terminal is None: continue
        result[terminal.incidence_id()] = terminal

    return result

def finalize_pattern_list(SortedPPT_List, CounterDb):
    pattern_list = [ pattern for priority, pattern, terminal in SortedPPT_List ]

    # (*) Transform anything into the buffer's codec
    #     Skippers: What is relevant to enter the skippers is transformed.
    #               Related data (skip character set, ... ) is NOT transformed!
    for pattern in pattern_list:
        if not pattern.transform(Setup.buffer_codec_transformation_info):
            error_msg("Pattern contains elements not found in engine codec '%s'." % Setup.buffer_codec,
                      pattern.sr, DontExitF=True)

    # (*) Cut the signalling characters from any pattern or state machine
    for pattern in pattern_list:
        pattern.cut_character_list(blackboard.signal_character_list(Setup))


    # (*) Pre-contexts and BIPD can only be mounted, after the transformation.
    for pattern in pattern_list:
        pattern.mount_post_context_sm()
        pattern.mount_pre_context_sm()

    return pattern_list

def _pattern_collect(BaseModeSequence, CounterDb, terminal_factory):
    """Collect patterns of all inherited modes. Patterns are like virtual functions
       in C++ or other object oriented programming languages. Also, the patterns of the
       uppest mode has the highest priority, i.e. comes first.
    """
    def pap_iterator(BaseModeSequence):
        for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
            for pap in mode_descr.pattern_action_pair_list:
                yield mode_hierarchy_index, pap

    result   = []
    mhi_self = len(BaseModeSequence) - 1
    for mhi, pap in pap_iterator(BaseModeSequence):
        # ALWAYS 'deepcopy' (even in the mode itself), because:
        # -- derived patterns may relate to the pattern.
        # -- the pattern's count info may differ from mode to mode.
        pattern  = deepcopy(pap.pattern())
        priority = PatternPriority(mhi, pattern.incidence_id()) 
        # Determine line and column counts -- BEFORE Character-Transformation!
        pattern.prepare_count_info(CounterDb, 
                                   Setup.buffer_codec_transformation_info)
        code     = CodeTerminalOnMatch(pap.action()) 
        terminal = terminal_factory.do(E_TerminalType.MATCH_PATTERN, code, pattern)
        result.append(PPT(priority, pattern, terminal))

    return result

def _pattern_delete_and_reprioritize(ppt_list, BaseModeSequence):
    """Performs the deletion and repriorization according the DELETE and PRIORITY-MARK
    commands in the mode. This may change the order and the incidence ids of the 
    mode's patterns. Thus, the ppt_list needs to be resorted and new incidence_id-s
    need to be assigned.
    """
    # -- Delete and reprioritize
    history_deletion         = _pattern_deletion(ppt_list, BaseModeSequence) 
    history_reprioritization = _pattern_reprioritization(ppt_list, BaseModeSequence) 

    # -- Re-sort and re-assign new incidence id which reflect the new order. 
    ppt_list.sort(key=attrgetter("priority"))
    for priority, pattern, terminal in ppt_list: 
        new_pattern_id = dial_db.new_incidence_id() # new id > any older id.
        pattern.set_incidence_id(new_pattern_id)
        terminal.set_incidence_id(new_pattern_id)

    return history_deletion, history_reprioritization

def _pattern_reprioritization(ppt_list, BaseModeSequence):
    """Repriority patterns. The 'reprioritization_info_list' consists of a list of

                 (pattern, new_pattern_index, source_reference)

       If a pattern defined in this mode matches 'pattern' it needs to receive the
       new pattern index and there changes its preceedence.
    """
    def repriorize(MHI, Info, ppt_list, ModeName, history):
        done_f = False
        for ppt in ppt_list:
            priority, pattern, terminal = ppt
            if   priority.mode_hierarchy_index > MHI:                      continue
            elif priority.pattern_index        >= Info.new_pattern_index:  continue
            elif not identity_checker.do(pattern, Info.pattern):           continue

            done_f = True
            history.append([ModeName, 
                            pattern.pattern_string(), pattern.sr.mode_name,
                            pattern.incidence_id(), Info.new_pattern_index])
            priority.mode_hierarchy_index = MHI
            priority.pattern_index        = Info.new_pattern_index

        if not done_f and Info.sr.mode_name == ModeName:
            error_msg("PRIORITY mark does not have any effect.", 
                      Info.sr.file_name, Info.sr.line_n, DontExitF=True)

    history = []
    mode_name = BaseModeSequence[-1].name
    for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
        for info in mode_descr.reprioritization_info_list:
            repriorize(mode_hierarchy_index, info, ppt_list, mode_name, history)

    return history

def _pattern_deletion(ppt_list, BaseModeSequence):
    """Delete all patterns that match entries in 'deletion_info_list'.
    """
    def delete(MHI, Info, ppt_list, ModeName, history):
        done_f = False
        size   = len(ppt_list)
        i      = 0
        while i < size:
            priority, pattern, terminal = ppt_list[i]
            if     priority.mode_hierarchy_index <= MHI \
               and priority.pattern_index < Info.pattern_index \
               and superset_check.do(Info.pattern, pattern):
                done_f  = True
                del ppt_list[i]
                history.append([ModeName, pattern.pattern_string(), pattern.sr.mode_name])
                size   -= 1
            else:
                i += 1

        if not done_f and Info.sr.mode_name == ModeName:
            error_msg("DELETION mark does not have any effect.", 
                      Info.sr.file_name, Info.sr.line_n, DontExitF=True)

    history = []
    mode_name = BaseModeSequence[-1].name
    for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
        for info in mode_descr.deletion_info_list:
            delete(mode_hierarchy_index, info, ppt_list, mode_name, history)

    return history

def match_indentation_counter_newline_pattern(IndentationSetup, Sequence):
    if IndentationSetup is None: return False
    return IndentationSetup.sm_newline.does_sequence_match(Sequence)

def _prepare_indentation_counter(ModeName, OptionsDb, CounterDb, IncidenceDb, terminal_factory, MHI):
    """Prepare indentation counter. An indentation counter is implemented by 
    the following:

    'newline' pattern --> triggers as soon as an UNSUPPRESSED newline occurs. 
                      --> entry to the INDENTATION COUNTER.

    'suppressed newline' --> INDENTATION COUNTER is NOT triggered.
     
    The supressed newline pattern is longer (and has precedence) over the
    newline pattern. With the suppressed newline it is possible to write
    lines which overstep the newline (see backslahs in Python, for example).

    RETURNS: List of:
             [0] newline PPT and
             [1] optionally the PPT of the newline suppressor.

    The primary pattern action pair list is to be the head of all pattern
    action pairs.

    MHI = Mode hierarchie index defining the priority of the current mode.
    """
    ISetup = OptionsDb.value("indentation")
    if ISetup is None: return [], []

    check_indentation_setup(ISetup)

    data = { 
        "counter_db":                    CounterDb,
        "indentation_setup":             ISetup,
        "default_indentation_handler_f": IncidenceDb.default_indentation_handler_f(),
        "mode_name":                     ModeName,
    }

    ppt_list = [
        # 'newline' triggers --> indentation counter
        PPT_indentation_handler_newline(MHI, data, ISetup, CounterDb, terminal_factory)
    ]

    if ISetup.sm_newline_suppressor.get() is not None:
        ppt_list.append(
            # 'newline-suppressor' followed by 'newline' is ignored (skipped)
            PPT_indentation_handler_suppressed_newline(MHI, ISetup, CounterDb, 
                                                       terminal_factory)
        )

    return [], ppt_list

def _prepare_skip_character_set(ModeName, OptionsDb, CounterDb, IncidenceDb, terminal_factory, MHI):
    """MHI = Mode hierarchie index."""
    SkipSetupList = OptionsDb.value_sequence("skip")
    if SkipSetupList is None or len(SkipSetupList) == 0:
        return [], []

    iterable           = SkipSetupList.__iter__()
    pattern, total_set = iterable.next()
    pattern_str        = pattern.pattern_string()
    source_reference   = pattern.sr
    # Multiple skippers from different modes are combined into one pattern.
    # This means, that we cannot say exactly where a 'skip' was defined 
    # if it intersects with another pattern.
    for ipattern, icharacter_set in iterable:
        total_set.unite_with(icharacter_set)
        pattern_str += "|" + ipattern.pattern_string()

    # The column/line number count actions for the characters in the 
    # total_set may differ. Thus, derive a separate set of characters
    # for each same count action, i.e.
    #
    #          map:  count action --> subset of total_set
    # 
    # When the first character is matched, then its terminal 'TERMINAL_x*'
    # is entered, i.e the count action for the first character is performed
    # before the skipping starts. This will look like this:
    #
    #     TERMINAL_x0:
    #                 count action '0';
    #                 goto __SKIP;
    #     TERMINAL_x1:
    #                 count action '1';
    #                 goto __SKIP;
    #        ...

    # An optional codec transformation is done later. The state machines
    # are entered as pure Unicode state machines.
    # It is not necessary to store the count action along with the state
    # machine.  This is done in "action_preparation.do()" for each
    # terminal.

    data = { 
        "counter_db":    CounterDb, 
        "character_set": total_set,
    }
    # The terminal is not related to a pattern, because it is entered
    # from the sub_terminals. Each sub_terminal relates to a sub character
    # set.
    terminal = terminal_factory.do_generator(None, skip_character_set.do, 
                                             data, "character set skipper")
    terminal.set_incidence_id(E_IncidenceIDs.SKIP)
    terminal_door_id  = DoorID.incidence(terminal.incidence_id())
    goto_terminal_str = Lng.GOTO(terminal_door_id)
    # Counting actions are added to the terminal automatically by the
    # terminal_factory. The only thing that remains for each sub-terminal:
    # 'goto skipper'.
    ccfactory = CountCmdFactory.from_ParserDataLineColumn(CounterDb, total_set, Lng.INPUT_P())

    new_ppt_list = [
        PPT_character_set_skipper(MHI, character_set, incidence_id, CounterDb, goto_terminal_str, terminal_factory)
        for character_set, incidence_id in ccfactory.get_incidence_id_map()
    ]

    return [terminal], new_ppt_list

def _prepare_skip_range(ModeName, OptionsDb, CounterDb, IncidenceDb,
                        terminal_factory, MHI):
    """MHI = Mode hierarchie index.
    
    RETURNS: new ppt_list to be added to the existing one.
    """

    SrSetup = OptionsDb.value_sequence("skip_range")
    if SrSetup is None or len(SrSetup) == 0: return [], []

    return [], [
        PPT_range_skipper(False, MHI, i, data, ModeName, OptionsDb, CounterDb, IncidenceDb, terminal_factory)
        for i, data in enumerate(SrSetup)
    ]

def _prepare_skip_nested_range(ModeName, OptionsDb, CounterDb, IncidenceDb,
                               terminal_factory, MHI):

    SrSetup = OptionsDb.value_sequence("skip_nested_range")
    if SrSetup is None or len(SrSetup) == 0: return [], []

    return [], [
        PPT_range_skipper(True, MHI, i, data, ModeName, OptionsDb, CounterDb, IncidenceDb, terminal_factory)
        for i, data in enumerate(SrSetup)
    ]

def PPT_character_set_skipper(MHI, character_set, incidence_id, CounterDb, goto_terminal_str, terminal_factory):
    """Generate a PPT for a character set skipper. That is, 
        -- A PatternPriority based on a given MHI and the specified incidence id.
        -- A Pattern to be webbed into the lexical analyzer state machine.
        -- A Terminal implementing the character set skipper.
    """
    priority         = PatternPriority(MHI, incidence_id)
    pattern          = Pattern.from_character_set(character_set)
    pattern.prepare_count_info(CounterDb, 
                               Setup.buffer_codec_transformation_info)
    # NOTE: 'terminal_factory.do_plain()' does prepare the counting action.
    code             = CodeTerminal([ goto_terminal_str ])
    sub_terminal     = terminal_factory.do(E_TerminalType.MATCH_PATTERN, 
                                           code, pattern)
    sub_terminal.set_name("Entry to 'skip': %s" % character_set.get_string("hex"))
    return PPT(priority, pattern, sub_terminal)

def PPT_range_skipper(NestedF, MHI, i, data, ModeName, OptionsDb, CounterDb, IncidenceDb, terminal_factory):
    """Generate a PPT for a range skipper.
    """
    # -- door_id_after: Where to go after the closing character sequence matched:
    #     + Normally: To the begin of the analyzer. Start again.
    #     + End(Sequence) == newline of indentation counter.
    #       => goto indentation counter.
    if match_indentation_counter_newline_pattern(OptionsDb.value("indentation"), 
                                                 data["closer_sequence"]):
        door_id_after = DoorID.incidence(E_IncidenceIDs.INDENTATION_HANDLER)
    else:
        door_id_after = DoorID.continue_without_on_after_match()

    if NestedF:
        name                = "skip nested range"
        code_generator_func = skip_nested_range.do
    else:
        name                = "skip range"
        code_generator_func = skip_range.do

    # -- data for code generation
    my_data = deepcopy(data)
    my_data["mode_name"]          = ModeName
    my_data["on_skip_range_open"] = IncidenceDb[E_IncidenceIDs.SKIP_RANGE_OPEN]
    my_data["door_id_after"]      = door_id_after
    my_data["counter_db"]         = CounterDb

    # -- terminal and code generator
    priority = PatternPriority(MHI, i)
    pattern  = deepcopy(my_data["opener_pattern"])
    pattern.prepare_count_info(CounterDb, 
                               Setup.buffer_codec_transformation_info)
    terminal = terminal_factory.do_generator(pattern, code_generator_func, 
                                             my_data, name)
    return PPT(priority, pattern, terminal)

def PPT_indentation_handler_newline(MHI, data, ISetup, CounterDb, terminal_factory):
    """Generate a PPT for newline, that is:

        -- its PatternPriority.
        -- the Pattern object.
        -- the Terminal object.

    The terminal object contains a generator which generates the INDENTATION
    COUNTER.
    """
    sm = ISetup.sm_newline.get()

    pattern = Pattern(sm)
    pattern.prepare_count_info(CounterDb, 
                               Setup.buffer_codec_transformation_info)

    terminal = terminal_factory.do_generator(pattern, 
                                             indentation_counter.do, 
                                             data, 
                                             "indentation counter: on_newline")

    return PPT(PatternPriority(MHI, 0), pattern, terminal)

def PPT_indentation_handler_suppressed_newline(MHI, ISetup, CounterDb, terminal_factory):
    """Generate a PPT for suppressed newline, that is:

        -- its PatternPriority.
        -- the Pattern object.
        -- the Terminal object.

    The terminal simply jumpts to the re-entry of the lexical analyzer.
    """
    assert ISetup.sm_newline_suppressor.get() is not None

    sm = sequentialize.do([ISetup.sm_newline_suppressor.get(),
                           ISetup.sm_newline.get()])

    pattern = Pattern(sm)
    pattern.prepare_count_info(CounterDb, 
                               Setup.buffer_codec_transformation_info)
    code     = CodeTerminal([Lng.GOTO(DoorID.global_reentry())])
    terminal = terminal_factory.do(E_TerminalType.PLAIN, code)
    terminal.set_name("indentation counter: on_suppressed_newline")

    return PPT(PatternPriority(MHI, 1), pattern, terminal)

def check_indentation_setup(isetup):
    """None of the elements 'comment', 'newline', 'newline_suppressor' should 
       not match some subsets of each other. Otherwise, the behavior would be 
       too confusing.
    """
    sm_newline            = isetup.sm_newline
    sm_newline_suppressor = isetup.sm_newline_suppressor
    sm_comment            = isetup.sm_comment
    candidates            = (sm_newline, sm_newline_suppressor, sm_comment)

    def mutually_subset(Sm1, Sm2):
        if   Sm1 is None or Sm2 is None:                           return False
        elif superset_check.do(sm_newline, sm_newline_suppressor): return True
        elif superset_check.do(sm_newline_suppressor, sm_newline): return True
        return False

    for i, candidate1 in enumerate(candidates):
        for candidate2 in candidates[i+1:]:
            if not mutually_subset(candidates1.get(), candidate2.get()): continue
            c_error_message(candidate1, candidate2,
                            ThisComment="matches on some common lexemes as",
                            ThatComment="") 

