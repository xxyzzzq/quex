
from   quex.input.setup                                import NotificationDB
import quex.input.regular_expression.core              as     regular_expression
from   quex.input.regular_expression.construct         import Pattern           
import quex.input.files.mode_option                    as     mode_option
from   quex.input.files.mode_option                    import OptionDB, \
                                                              SkipRangeData
import quex.input.files.code_fragment                  as     code_fragment
from   quex.input.files.counter_db                     import CounterDB
import quex.input.files.consistency_check              as     consistency_check
from   quex.engine.analyzer.door_id_address_label      import Label
from   quex.engine.generator.code.core                 import CodeFragment, \
                                                              UserCodeFragment, \
                                                              GeneratedCode, \
                                                              PatternActionInfo

import quex.engine.generator.skipper.character_set       as   skip_character_set
import quex.engine.generator.skipper.range               as   skip_range
import quex.engine.generator.skipper.nested_range        as   skip_nested_range
import quex.engine.generator.skipper.indentation_counter as   indentation_counter

from   quex.engine.state_machine.core                  import StateMachine
import quex.engine.state_machine.index                 as     sm_index
import quex.engine.state_machine.check.identity        as     identity_checker
import quex.engine.state_machine.check.superset        as     superset_check
import quex.engine.state_machine.repeat                as     repeat
import quex.engine.state_machine.sequentialize         as     sequentialize
import quex.engine.state_machine.algorithm.beautifier  as     beautifier
from   quex.engine.misc.file_in                        import EndOfStreamException, \
                                                              check, \
                                                              check_or_die, \
                                                              error_msg, \
                                                              error_eof, \
                                                              get_current_line_info_number, \
                                                              read_identifier, \
                                                              read_until_letter, \
                                                              read_until_whitespace, \
                                                              skip_whitespace, \
                                                              verify_word_in_list
import quex.blackboard as blackboard
from   quex.blackboard import setup as Setup, \
                              SourceRef, \
                              E_IncidenceIDs, \
                              E_IncidenceIDs_Subset_Terminals, \
                              E_IncidenceIDs_Subset_Special, \
                              standard_incidence_db

from   copy        import deepcopy
from   collections import namedtuple
from   operator    import itemgetter, attrgetter

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
        return cmp((self.mode_hierarchy_index,  self.pattern_index),
                   (Other.mode_hierarchy_index, Other.pattern_index))

class PPC(namedtuple("PPC_tuple", ("priority", "pattern", "code_fragment"))):
    """PPC -- (Priority, Pattern, CodeFragment) 
    ______________________________________________________________________________

    Collects information about a pattern, its priority, and the code fragment
    to be executed when it triggers. Objects of this class are intermediate
    they are not visible outside class 'Mode'.
    ______________________________________________________________________________
    """
    @typed(ThePatternPriority=PatternPriority, TheCodeFragment=CodeFragment)
    def __new__(self, ThePatternPriority, ThePattern, TheCodeFragment):
        return super(PPC, self).__new__(self, ThePatternPriority, ThePattern, TheCodeFragment)

    @staticmethod
    def from_PatternActionPair(ModeHierarchyIndex, PAP):
        return PPC(PatternPriority(ModeHierarchyIndex, PAP.pattern().incidence_id()), PAP.pattern(), PAP.action())


#-----------------------------------------------------------------------------------------
# ModeDescription/Mode Objects:
#
# During parsing 'ModeDescription' objects are generated. Once parsing is over, 
# the descriptions are translated into 'real' mode objects where code can be generated
# from. All matters of inheritance and pattern resolution are handled in the
# transition from description to real mode.
#-----------------------------------------------------------------------------------------

PatternRepriorization = namedtuple("PatternRepriorization", ("pattern", "new_pattern_index", "sr"))
PatternDeletion       = namedtuple("PatternDeletion",       ("pattern", "pattern_index",     "sr", "mode_name"))

class ModeDescription:
    """Mode description delivered directly from the parser.
    ______________________________________________________________________________
    MAIN MEMBERS:

     (1) .pattern_action_pair_list:   [ (Pattern, CodeUser) ]

     Lists all patterns which are directly defined in this mode (not the ones
     from the base mode) together with the user code (class CodeUser) to be
     executed upon the detected match.

     (2) .incidence_db:               incidence_id --> [ CodeFragment ]

     Lists of possible incidences (e.g. 'on_match', 'on_enter', ...) together
     with the code fragment to be executed upon occurence.

     (3) .option_db:                  option name  --> [ OptionSetting ]

     Maps the name of a mode option to a list of OptionSetting according to 
     what has been defined in the mode. Those options describe

        -- [optional] The character counter behavior.
        -- [optional] The indentation handler behavior.
        -- [optional] The 'skip' character behavior.
           ...

     That is, they parameterize code generators of 'helpers'. The option_db
     also contains information about mode transition restriction, inheritance
     behavior, etc.

     (*) .derived_from_list:   [ string ]
     
     Lists all modes from where this mode is derived, that is only the direct 
     super modes.
    ______________________________________________________________________________
    OTHER NON_TRIVIAL MEMBERS:

     If the mode is derived from another mode, it may make sense to adapt the 
     priority of patterns and/or delete pattern from the matching hierarchy.

     (*) .reprioritization_info_list: [ PatternRepriorization ] 
       
     (*) .deletion_info_list:         [ PatternDeletion ] 
    ______________________________________________________________________________
    """
    __slots__ = ("name",
                 "sr",
                 "derived_from_list",
                 "option_db",
                 "pattern_action_pair_list",
                 "incidence_db",
                 "reprioritization_info_list",
                 "deletion_info_list")

    def __init__(self, Name, Filename, LineN):
        # Register ModeDescription at the mode database
        blackboard.mode_description_db[Name] = self
        self.name  = Name
        self.sr    = SourceRef(Filename, LineN)

        self.derived_from_list          = []

        self.pattern_action_pair_list   = []  
        self.option_db                  = RestrictedDB(standard_mode_option_db) # map: option_name    --> OptionSetting
        self.incidence_db               = RestrictedDB(standard_incidence_db)   # map: incidence_name --> CodeFragment

        self.reprioritization_info_list = []  
        self.deletion_info_list         = [] 

    def add_pattern_action_pair(self, PatternStr, Action, ThePattern, Comment=""):
        assert ThePattern.check_consistency()

        Action.mode_name      = self.name
        Action.comment        = Comment
        Action.pattern_string = PatternStr
        self.pattern_action_pair_list.append(PatternActionInfo(ThePattern, Action, PatternStr, 
                                                               ModeName=self.name, Comment=Comment))

    def add_match_priority(self, ThePattern, FileName, LineN):
        """Whenever a pattern in the mode occurs, which is identical to that given
           by 'ThePattern', then the priority is adapted to the pattern index given
           by the current pattern index.
        """
        PatternIdx = ThePattern.incidence_id() 
        self.reprioritization_info_list.append(PatternRepriorization(ThePattern, PatternIdx, SourceRef(FileName, LineN), self.name))

    def add_match_deletion(self, ThePattern, FileName, LineN):
        """If one of the base modes contains a pattern which is identical to this
           pattern, it has to be deleted.
        """
        PatternIdx = ThePattern.incidence_id() 
        self.deletion_info_list.append(PatternDeletion(ThePattern, PatternIdx, SourceRef(FileName, LineN), self.name))

class IncidenceDB(dict):
    """Database of CodeFragments related to 'incidences'.
    ---------------------------------------------------------------------------

                      incidence_id --> [ CodeFragment ]

    If the 'mode_option_info_db[option_name]' mentions that there can be 
    no multiple definitions or if the options can be overwritten than the 
    list of OptionSetting-s must be of length '1' or the list does not exist.

    ---------------------------------------------------------------------------
    """
    def from_BaseModeSequence(self, BaseModeSequence):
        """Collects the content of the 'incidence_db' member of this mode and
        its base modes. 

        RETURNS:      map:    incidence_id --> [ CodeFragment ]
        """
        # Special incidences from 'standard_incidence_db'
        result = {}
        for incidence_name, info in standard_incidence_db.iteritems():
            incidence_id, comment = info
            entry = None
            for mode_descr in BaseModeSequence:
                code_fragment = mode_descr.incidence_db[incidence_name]
                if code_fragment is not None and not code_fragment.is_whitespace():
                    new_code_fragment = code_fragment.clone()
                    if entry is None: entry = [ new_code_fragment ]
                    else:             entry.append_CodeFragment(new_code_fragment)
            result[incidence_id] = entry

        if E_IncidenceIDs.FAILURE not in result:
            result[E_IncidenceIDs.FAILURE] = CodeFragment(
                  "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % self.mode_name
                + "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
                + "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
            )
        if E_IncidenceIDs.END_OF_STREAM not in result:
            result[E_IncidenceIDs.END_OF_STREAM] = CodeFragment(
                "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
                "RETURN;\n"
            )

        return result

    def get_text(self, IncidenceId):
        code_fragment = self.get(IncidenceId)
        if code_fragment is None: return ""
        else:                     return "".join(on_match.get_code())

    def default_indentation_handler(self):
        return not (   self.has_key(E_IncidenceIDs.INDENTATION_ERROR) \
                    or self.has_key(E_IncidenceIDs.INDENTATION_BAD)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_INDENT)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_DEDENT)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_N_DEDENT) \
                    or self.has_key(E_IncidenceIDs.INDENTATION_NODENT))



class TerminalDB(dict):
    def __init__(self, IncidenceDb, PPC_List):
        # Miscellaneous incidences
        for incidence_id, code_fragment in IncidenceDb:
            assert incidence_id not in self
            self[incidence_id] = Terminal(incidence_id, code_fragment.get_code())

        # Pattern match incidences
        for priority, pattern, code_fragment in PPC_List:
            incidence_id = pattern.incidence_id()
            assert incidence_id not in self
            self[incidence_id] = Terminal(incidence_id, code_fragment.get_code())

        return

    def __get_code(self, IncidenceId, CodeFragment):

class Mode:
    """Finalized 'Mode' as it results from combination of base modes.
    ____________________________________________________________________________

     A pattern detection mode. It is identified by

       .pattern_list -- A list of patterns which can potentially be detected.
                        A pattern match is a special kind of an incidence.
                        Pattern matches are associated with pattern match
                        actions (i.e. CodeFragment-s).

       .incidence_db -- A mapping from incidence ids to CodeFragments to be
                        executed upon the occurrence of the incidence.
     
                        NOTE: The incidences mentioned in 'incidence_db' are
                        all 'terminals' and NOT things which appear 'by the side'.

     A Mode is built upon a ModeDescription object. A mode description contains
     further 'option_db' such as a column-line-count specification and a
     indentation setup.
    ____________________________________________________________________________
    """
    def __init__(self, Other):
        """Translate a ModeDescription into a real Mode. Here is the place were 
        all rules of inheritance mechanisms and pattern precedence are applied.
        """
        assert isinstance(Other, ModeDescription)
        self.name = Other.name
        self.sr   = Other.sr   # 'SourceRef' -- is immutable

        base_mode_sequence  = self.__determine_base_mode_sequence(Other, [], [])
        assert len(base_mode_sequence) >= 1 # At least the mode itself is in there

        # Collect Options
        # (A finalized Mode does not contain an option_db anymore).
        options_db   = OptionDB.from_BaseModeSequence(base_mode_sequence)
        incidence_db = IncidenceDB.from_BaseModeSequence(base_mode_sequence)

        # Determine Line/Column Counter Database
        counter_db        = CounterDB(options_db.value("counter"))
        indentation_setup = options_db.value("indentation")

        # Intermediate Step: Priority-Pattern-CodeFragment List (PPC list)
        #
        # The list is developed so that patterns can be sorted and code 
        # fragments are prepared.
        self.__pattern_list, \
        self.__terminal_db   = self.__ppc_list_construct(base_mode_sequence, options_db)

        
        # (*) Misc
        self.__abstract_f           = self.__is_abstract(Other.option_db)
        self.__base_mode_sequence   = base_mode_sequence
        self.__entry_mode_name_list = options_db.value_list("entry") # Those can enter this mode.
        self.__exit_mode_name_list  = options_db.value_list("exit")  # This mode can exit to those.

    def __is_abstract(self, OriginalOptionDb):
        """If the mode has incidences and/or patterns defined it is free to be 
        abstract or not. If neither one is defined, it cannot be implemented and 
        therefore MUST be abstract.
        """
        abstract_f = (OriginalOptionDb.value("inheritable") == "only")

        if len(self.incidence_db) != 0 or len(self.pattern_list) != 0:
            return abstract_f

        elif abstract_f == False:
            error_msg("Mode without pattern and event handlers needs to be 'inheritable only'.\n" + \
                      "<inheritable: only> has been set automatically.", self.sr.file_name, self.sr.line_n,  
                      DontExitF=True)
            abstract_f = True # Change to 'inheritable: only', i.e. abstract_f == True.

        return abstract_f

    def abstract_f(self):           return self.__abstract_f

    @property
    def counter_db(self):           return self.__counter_db

    @property
    def indentation_setup(self):    return self.__indentation_setup

    @property
    def exit_mode_name_list(self):  return self.__exit_mode_name_list

    @property
    def entry_mode_name_list(self): return self.__entry_mode_name_list

    @property
    def incidence_db(self): return self.__incidence_db

    @property
    def pattern_list(self): return self.__pattern_list

    def has_base_mode(self):
        return len(self.__base_mode_sequence) != 1

    def get_base_mode_sequence(self):
        assert len(self.__base_mode_sequence) >= 1 # At least the mode itself is in there
        return self.__base_mode_sequence

    def get_base_mode_name_list(self):
        assert len(self.__base_mode_sequence) >= 1 # At least the mode itself is in there
        return [ mode.name for mode in self.__base_mode_sequence ]

    def __pattern_list_construct(self, ppc_list):
        pattern_list = [ 
            pattern 
            for priority, pattern, code_fragment in sorted(ppc_list, key=attrgetter("priority")) 
        ]

        # (*) Try to determine line and column counts -- BEFORE Transformation!
        for pattern in pattern_list:
            pattern.prepare_count_info(CounterDb, 
                                       Setup.buffer_codec_transformation_info)

        # (*) Transform anything into the buffer's codec
        #     Skippers: What is relevant to enter the skippers is transformed.
        #               Related data (skip character set, ... ) is NOT transformed!
        for pattern in pattern_list:
            if not pattern.transform(Setup.buffer_codec_transformation_info):
                error_msg("Pattern contains elements not found in engine codec '%s'." % Setup.buffer_codec,
                          pattern.file_name, pattern.sr.line_n, DontExitF=True)

        # (*) Cut the signalling characters from any pattern or state machine
        for pattern in pattern_list:
            pattern.cut_character_list(blackboard.signal_character_list(Setup))

        # (*) Pre-contexts and BIPD can only be mounted, after the transformation.
        for pattern in pattern_list:
            pattern.mount_post_context_sm()
            pattern.mount_pre_context_sm()

        return pattern_list

    def __determine_base_mode_sequence(self, ModeDescr, InheritancePath, base_mode_sequence):
        """Determine the sequence of base modes. The type of sequencing determines
           also the pattern precedence. The 'deep first' scheme is chosen here. For
           example a mode hierarchie of

                                       A
                                     /   \ 
                                    B     C
                                   / \   / \
                                  D  E  F   G

           results in a sequence: (A, B, D, E, C, F, G).reverse()

           This means, that patterns and event handlers of 'E' have precedence over
           'C' because they are the childs of a preceding base mode.

           This function detects circular inheritance.

        __dive -- inserted this keyword for the sole purpose to signal 
                  that here is a case of recursion, which may be solved
                  later on by a TreeWalker.
        """
        if ModeDescr.name in InheritancePath:
            msg = "mode '%s'\n" % InheritancePath[0]
            for mode_name in InheritancePath[InheritancePath.index(ModeDescr.name) + 1:]:
                msg += "   inherits mode '%s'\n" % mode_name
            msg += "   inherits mode '%s'" % ModeDescr.name

            error_msg("circular inheritance detected:\n" + msg, ModeDescr.sr.file_name, ModeDescr.sr.line_n)

        base_mode_name_list_reversed = deepcopy(ModeDescr.derived_from_list)
        #base_mode_name_list_reversed.reverse()
        for name in base_mode_name_list_reversed:
            # -- does mode exist?
            verify_word_in_list(name, blackboard.mode_description_db.keys(),
                                "Mode '%s' inherits mode '%s' which does not exist." % (ModeDescr.name, name),
                                ModeDescr.sr.file_name, ModeDescr.sr.line_n)

            if name in map(lambda m: m.name, base_mode_sequence): continue

            # -- grab the mode description
            mode_descr = blackboard.mode_description_db[name]
            self.__determine_base_mode_sequence(mode_descr, InheritancePath + [ModeDescr.name], base_mode_sequence)

        base_mode_sequence.append(ModeDescr)

        return base_mode_sequence

    def __ppc_list_construct(self, BaseModeSequence, OptionsDb):
        """Priority, Pattern, CodeFragment List: 'ppc_list'
        -----------------------------------------------------------------------
        The 'ppc_list' is the list of eXtended Pattern Action Pairs.
        Each element in the list consist of
        
            .priority 
            .pattern
            .code_fragment
        
        The pattern priority allows to keep the list sorted according to its
        priority given by the mode's position in the inheritance hierarchy and
        the pattern index itself.
        -----------------------------------------------------------------------
        """ 
        ppc_list    = self.__pattern_action_pairs_collect(BaseModeSequence)
        terminal_db = TerminalDB() # In this function 'terminal_db' collects only
        #                          # non-pattern terminals.

        # (*) Collect pattern recognizers and several 'incidence detectors' in 
        #     state machine lists. When the state machines accept this triggers
        #     an incidence which is associated with an entry in the incidence_db.
        self.__prepare_skip(ppc_list, OptionsDb.value_sequence("skip"), MHI=-4)
        self.__prepare_skip_range(ppc_list, OptionsDb.value_sequence("skip_range"), MHI=-3)
        self.__prepare_skip_nested_range(ppc_list, OptionsDb.value_sequence("skip_nested_range"), MHI=-3)

        self.__prepare_indentation_counter(ppc_list, OptionsDb.value_sequence("indentation"), MHI=-1)

        # (*) Delete and reprioritize
        self.__perform_deletion(ppc_list, BaseModeSequence) 
        self.__perform_reprioritization(ppc_list, BaseModeSequence) 

        # (*) Process PPC list and extract the required terminals into TerminalDB.
        pattern_list = self.__pattern_list_construct(ppc_list, terminal_db)

        # (*) Line-/Column Count DB
        terminal_db  = self.__terminal_db_construct(pattern_list)

        return pattern_list, terminal_db

    def __terminal_db_construct(self, PatternList, PPC_List):
        line_column_count_db = self.__prepare_line_column_count_db(PatternList)

        factory = TerminalFactory(self.name, self.incidence_db, 
                                  line_column_count_db, 
                                  IndentationSupportF, BeginOfLineSupportF)

        terminal_db = {}
        for priority, pattern, code_fragment in PPC_List:
            terminal = factory.do(terminal_type, code_fragment, 
                                  Prefix=line_column_count_db[pattern.incidence_id()])
            terminal_db[pattern.incidence_id()] = terminal

        return terminal_db

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


    def __prepare_skip(self, ppc_list, SkipSetupList, MHI):
        """MHI = Mode hierarchie index."""
        if SkipSetupList is None or len(SkipSetupList) == 0:
            return

        iterable                            = SkipSetupList.__iter__()
        pattern_str, pattern, character_set = iterable.next()
        source_reference                    = pattern.sr
        # Multiple skippers from different modes are combined into one pattern.
        # This means, that we cannot say exactly where a 'skip' was defined 
        # if it intersects with another pattern.
        for ipattern_str, ipattern, icharacter_set in iterable:
            character_set.unite_with(icharacter_set)
            pattern_str += "|" + ipattern_str

        # The column/line number count actions for the characters in the 
        # character_set may differ. Thus, derive a separate set of characters
        # for each same count action, i.e.
        #
        #          map:  count action --> subset of character_set
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
        def get_PPC(MHI, Cli, CmdInfo, TheCodeFragment):
            priority      = PatternPriority(MHI, Cli)
            pattern       = Pattern(StateMachine.from_character_set(CmdInfo.trigger_set))
            ppc_list.append(PPC(priority, pattern, TheCodeFragment))

        ccd          = CounterCoderData(self.counter_db, character_set, AfterExitDoorId)
        incidence_id = index.get_state_machine_id()
        code         = [ LanguageDB.GOTO_BY_DOOR_ID(DoorID.incidence(incidence_id)) ]
        for cli, cmd_info in ccd.count_command_map.iteritems():
            # Counting actions are added to the terminal automatically.
            # What remains to do here is only to go to the skipper.
            sub_incidence_id = index.get_state_machine_id()
            ppc_list.append(get_PPC(MHI, cli, cmd_info, Terminal(sub_incidence_id, code)))

        data = { 
            "counter_db":    self.counter_db, 
            "character_set": character_set,
        }
        code = skip_character_set.do(data)
        ppc_list.append(get_PPC(MHI, main_cli, cmd_info, Terminal(incidence_id, code)))

    def __prepare_skip_range(self, ppc_list, SkipRangeSetupList, MHI):
        """MHI = Mode hierarchie index."""
        self.__prepare_skip_range_core(ppc_list, MHI, SkipRangeSetupList,  
                                       skip_range.do)

    def __prepare_skip_nested_range(self, ppc_list, SkipNestedRangeSetupList, MHI):
        """MHI = Mode hierarchie index."""
        self.__prepare_skip_range_core(ppc_list, MHI, SkipNestedRangeSetupList, 
                                       skip_nested_range.do)

    def __prepare_skip_range_core(self, ppc_list, MHI, SrSetup, CodeGeneratorFunction):
        """MHI = Mode hierarchie index."""

        if SrSetup is None or len(SrSetup) == 0:
            return

        assert    Code_constructor == CodeSkipRange \
               or Code_constructor == CodeSkipNestedRange

        for i, data in enumerate(SrSetup):
            assert isinstance(data, SkipRangeData)
            data.mode = self
            code      = CodeGeneratorFunction(data, opener_pattern.sr)

            priority  = PatternPriority(MHI, i)
            pattern   = opener_pattern.clone()
            incidence_id = index.get_state_machine_id()
            pattern.set_incidence_id(incidence_id)
            ppc_list.append(PPC(priority, pattern, Terminal(incidence_id, code))

    def __prepare_indentation_counter(self, ppc_list, ISetup, MHI):
        """Prepare indentation counter. An indentation counter is implemented by the 
        following:

             -- A 'newline' pattern triggers as soon as an unsuppressed newline 
                occurs. The related action to this 'newline pattern' is the 
                indentation counter.
             -- A suppressed newline prevents that the next line is considered
                as the beginning of a line. The pattern matches longer and eats
                the 'newline' before it can match.

        As said, the indentation counter engine is entered upon the triggering
        of the 'newline' pattern. It is the action which is related to it.

        The two aforementioned patterns better have preceedence over any other
        pattern. So, if there is indentation counting, then they have to be 
        considered 'primary' patterns'.

        RETURNS: [0] Terminal ID of the 'newline' pattern.
                 [1] Primaray pattern action pair list

        The primary pattern action pair list is to be the head of all pattern
        action pairs.

        MHI = Mode hierarchie index.
        """
        if ISetup is None:
            return 

        # The indentation counter is entered upon the appearance of the unsuppressed
        # newline pattern. 
        #
        #  TODO: newline = newline/\C{newline suppressor}, i.e. a newline is only a
        #        newline if it is followed by something else than a newline suppressor.
        ppc_suppressed_newline = None
        if ISetup.newline_suppressor_state_machine.get() is not None:
            pattern_str =   "(" + ISetup.newline_suppressor_state_machine.pattern_string() + ")" \
                          + "(" + ISetup.newline_state_machine.pattern_string() +            ")"
            sm = sequentialize.do([ISetup.newline_suppressor_state_machine.get(),
                                   ISetup.newline_state_machine.get()])

            priority      = PatternPriority(MHI, 0)
            pattern       = Pattern(sm, IncidenceId=E_IncidenceIDs.SUPPRESSED_INDENTATION_NEWLINE, 
                                    PatternStr=pattern_str)
            code_fragment = UserCodeFragment(LanguageDB.GOTO_BY_DOOR_ID(DoorID.global_reentry(GotoedF=True)), 
                                             SourceReference=ISetup.newline_suppressor_state_machine.sr) 

            ppc_list.append(PPC(priority, pattern, code_fragment))


        # When there is an empty line, then there shall be no indentation count on it.
        # Here comes the trick: 
        #
        #      Let               newline         
        #      be defined as:    newline ([space]* newline])*
        # 
        # This way empty lines are eaten away before the indentation count is activated.
        x0 = StateMachine()                                             # 'space'
        x0.add_transition(x0.init_state_index, ISetup.indentation_count_character_set(), 
                          AcceptanceF=True)
        x1 = repeat.do(x0)                                              # '[space]*'
        x2 = sequentialize.do([x1, ISetup.newline_state_machine.get()]) # '[space]* newline'
        x3 = repeat.do(x2)                                              # '([space]* newline)*'
        x4 = sequentialize.do([ISetup.newline_state_machine.get(), x3]) # 'newline ([space]* newline)*'
        sm = beautifier.do(x4)                                          # nfa to dfa; hopcroft optimization

        data = { 
            "indentation_setup": ISetup 
        }

        if ppc_suppressed_newline is not None:
            ppc_list.append(ppc_suppressed_newline)

        priority      = PatternPriority(MHI, 1)
        pattern       = Pattern(sm, IncidenceId=E_IncidenceIDs.INDENTATION_NEWLINE)
        code_fragment = CodeIndentationCounter(data, ISetup.newline_state_machine.sr)

        ppc_list.append(PPC(priority, pattern, code_fragment))

        return

    def __pattern_action_pairs_collect(self, BaseModeSequence):
        """Collect patterns of all inherited modes. Patterns are like virtual functions
           in C++ or other object oriented programming languages. Also, the patterns of the
           uppest mode has the highest priority, i.e. comes first.
        """
        result = []
        for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
            result.extend(
                PPC.from_PatternActionPair(mode_hierarchy_index, pap)
                for pap in mode_descr.pattern_action_pair_list
            )
        return result

    def __perform_reprioritization(self, ppc_list, BaseModeSequence):
        def repriorize(MHI, Info, ppc_list, ModeName, history):
            done_f = False
            for xpap in ppc_list:
                if     xpap[0].mode_hierarchy_index <= MHI \
                   and xpap[0].pattern_index        < Info.new_pattern_index \
                   and identity_checker.do(xpap[1].pattern(), Info.pattern):
                    done_f = True
                    history.append([ModeName, 
                                    xpap[1].pattern_string(), 
                                    xpap[1].mode_name,
                                    xpap[1].pattern().incidence_id(), 
                                    Info.new_pattern_index])
                    xpap[0].mode_hierarchy_index = MHI
                    xpap[0].pattern_index        = Info.new_pattern_index

            if not done_f and Info.mode_name == ModeName:
                error_msg("PRIORITY mark does not have any effect.", 
                          Info.file_name, Info.sr.line_n, DontExitF=True)

        history = []
        for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
            for info in mode_descr.get_reprioritization_info_list():
                repriorize(mode_hierarchy_index, info, ppc_list, self.name, history)

        self.__doc_history_reprioritization = history

    def __perform_deletion(self, ppc_list, BaseModeSequence):
        def delete(MHI, Info, ppc_list, ModeName, history):
            done_f = False
            size   = len(ppc_list)
            i      = 0
            while i < size:
                xpap = ppc_list[i]
                if     xpap[0].mode_hierarchy_index <= MHI \
                   and xpap[0].pattern_index < Info.pattern_index \
                   and superset_check.do(Info.pattern, xpap[1].pattern()):
                    done_f  = True
                    del ppc_list[i]
                    history.append([ModeName, xpap[1].pattern_string(), xpap[1].mode_name])
                    size   -= 1
                else:
                    i += 1

            if not done_f and Info.mode_name == ModeName:
                error_msg("DELETION mark does not have any effect.", 
                          Info.file_name, Info.sr.line_n, DontExitF=True)

        history = []
        for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
            for info in mode_descr.get_deletion_info_list():
                delete(mode_hierarchy_index, info, ppc_list, self.name, history)

        self.__doc_history_deletion = history

    def check_consistency(self):
        # (*) Modes that are inherited must allow to be inherited
        for base_mode in self.__base_mode_sequence:
            if base_mode.option_db.value("inheritable") == "no":
                error_msg("mode '%s' inherits mode '%s' which is not inheritable." % \
                          (self.name, base_mode.name), self.sr.file_name, self.sr.line_n)

        # (*) Empty modes which are not inheritable only?
        # (*) A mode that is instantiable (to be implemented) needs finally contain matches!
        if (not self.__abstract_f)  and len(self.__pattern_list) == 0:
            error_msg("Mode '%s' was defined without the option <inheritable: only>.\n" % self.name + \
                      "However, it contains no matches--only event handlers. Without pattern\n"     + \
                      "matches it cannot act as a pattern detecting state machine, and thus\n"      + \
                      "cannot be an independent lexical analyzer mode. Define the option\n"         + \
                      "<inheritable: only>.", \
                      self.sr.file_name, self.sr.line_n)

        # (*) Indentation: Newline Pattern and Newline Suppressor Pattern
        #     shall never trigger on common lexemes.
        self.check_indentation_setup()

    def check_special_incidence_outrun(self, ErrorCode):
        for pattern in self.__pattern_list:
            if pattern.incidence_id() not in E_IncidenceIDs_Subset_Special: continue

            for other_pattern in self.get_pattern_action_pair_list():
                # No 'commonalities' between self and self shall be checked
                if pattern.incidence_id() >= other_pattern.incidence_id(): continue

                if outrun_checker.do(pattern.sm, other_pattern.sm):
                    __error_message(other_pattern, pattern, ExitF=True, 
                                    ThisComment  = "has lower priority but",
                                    ThatComment  = "may outrun",
                                    SuppressCode = ErrorCode)
                                 
    def check_higher_priority_matches_subset(self, ErrorCode):
        """Checks whether a higher prioritized pattern matches a common subset
           of the ReferenceSM. For special patterns of skipper, etc. this would
           be highly confusing.
        """
        global special_pattern_list
        for pattern in self.__pattern_list:
            if pattern.incidence_id() not in E_IncidenceIDs_Subset_Special: continue

            for other_pattern in self.__pattern_list:
                if   pattern.incidence_id() <= other_pattern.incidence_id(): continue
                elif not superset_check.do(pattern.sm, other_pattern.sm):    continue

                __error_message(other_pattern, pattern, ExitF=True, 
                                ThisComment  = "has higher priority and",
                                ThatComment  = "matches a subset of",
                                SuppressCode = ErrorCode)

    def check_dominated_pattern(self, ErrorCode):
        for pattern in self.__pattern_list:
            incidence_id  = pattern.incidence_id()

            for other_pattern in self.__pattern_list:
                if other_pattern.incidence_id() >= incidence_id: 
                    continue
                if superset_check.do(other_pattern, pattern):
                    file_name, line_n = other_pattern.action().sr
                    __error_message(other_pattern, pattern, 
                                    ThisComment  = "matches a superset of what is matched by",
                                    EndComment   = "The former has precedence and the latter can never match.",
                                    ExitF        = True, 
                                    SuppressCode = ErrorCode)

    def check_match_same(self, ErrorCode):
        """Special patterns shall never match on some common lexemes."""
        for pattern in self.__pattern_list:
            if pattern.incidence_id() not in E_IncidenceIDs_Subset_Terminals: continue

            A = pattern.sm
            for other_pattern in self.get_pattern_action_pair_list():

                B = other_pattern.sm
                if   other_pap.incidence_id() not in E_IncidenceIDs_Subset_Special: continue
                elif A.incidence_id() == B.incidence_id(): continue

                # A superset of B, or B superset of A => there are common matches.
                if same_check.do(A, B):
                    __error_message(other_pattern, pattern, 
                                    ThisComment  = "matches on some common lexemes as",
                                    ThatComment  = "",
                                    ExitF        = True,
                                    SuppressCode = ErrorCode)

    def check_low_priority_outruns_high_priority_pattern(self):
        """Warn when low priority patterns may outrun high priority patterns.
        """
        pattern_list = copy(self.__pattern_list) # No 'deepcopy' its just about sorting
        # Sort by acceptance_id
        pattern_list.sort(key=lambda pattern: pattern.incidence_id())

        for i, pattern_i in enumerate(pattern):
            sm_high = pattern_i.sm
            for pattern_k in islice(pattern_list, i+1, None):
                # 'pattern_k' has a higher id than 'pattern_i'. Thus, it has a lower
                # priority. Check for outrun.
                sm_low = pattern_k.pattern().sm
                if outrun_checker.do(sm_high, sm_low):
                    file_name, line_n = pattern_i.action().sr
                    __error_message(pattern_k, pattern_i, ExitF=False, ThisComment="may outrun")

    def match_indentation_counter_newline_pattern(self, Sequence):
        if self.indentation_setup is None: return False

        return self.indentation_setup.newline_state_machine.get().does_sequence_match(Sequence)

    def check_indentation_setup(self):
        # (*) Indentation: Newline Pattern and Newline Suppressor Pattern
        #     shall never trigger on common lexemes.
        if self.__indentation_setup is None: return

        # The newline pattern shall not have intersections with other patterns!
        newline_info            = self.__indentation_setup.newline_state_machine
        newline_suppressor_info = self.__indentation_setup.newline_suppressor_state_machine
        assert newline_info is not None
        if newline_suppressor_info.get() is None: return

        # Newline and newline suppressor should never have a superset/subset relation
        if    superset_check.do(newline_info.get(), newline_suppressor_info.get()) \
           or superset_check.do(newline_suppressor_info.get(), newline_info.get()):

            __error_message(newline_info, newline_suppressor_info,
                            ThisComment="matches on some common lexemes as",
                            ThatComment="") 

    def get_documentation(self):
        L = max(map(lambda mode: len(mode.name), self.__base_mode_sequence))
        txt  = "\nMODE: %s\n" % self.name

        txt += "\n"
        if len(self.__base_mode_sequence) != 1:
            txt += "    BASE MODE SEQUENCE:\n"
            base_mode_name_list = map(lambda mode: mode.name, self.__base_mode_sequence[:-1])
            base_mode_name_list.reverse()
            for name in base_mode_name_list:
                txt += "      %s\n" % name
            txt += "\n"

        if len(self.__doc_history_deletion) != 0:
            txt += "    DELETION ACTIONS:\n"
            for entry in self.__doc_history_deletion:
                txt += "      %s:  %s%s  (from mode %s)\n" % \
                       (entry[0], " " * (L - len(self.name)), entry[1], entry[2])
            txt += "\n"

        if len(self.__doc_history_reprioritization) != 0:
            txt += "    PRIORITY-MARK ACTIONS:\n"
            self.__doc_history_reprioritization.sort(lambda x, y: cmp(x[4], y[4]))
            for entry in self.__doc_history_reprioritization:
                txt += "      %s: %s%s  (from mode %s)  (%i) --> (%i)\n" % \
                       (entry[0], " " * (L - len(self.name)), entry[1], entry[2], entry[3], entry[4])
            txt += "\n"

        if len(self.__pattern_list) != 0:
            txt += "    PATTERN LIST:\n"
            def my_key(x):
                if   x.pattern() in E_IncidenceIDs: return (0, str(x.pattern()))
                elif hasattr(x.pattern(), "sm"):    return (1, x.pattern().incidence_id())
                else:                               return (2, x)

            self.__pattern_list.sort(key=my_key)

            for pap in self.__pattern_list:
                if hasattr(pap.pattern(), "sm"): 
                    txt += "      (%3i) %s: %s%s\n" % \
                           (pap.pattern().incidence_id(),
                            pap.mode_name, " " * (L - len(self.name)), 
                            pap.pattern_string())
                else:
                    txt += "      %s\n" % pap.pattern()
            txt += "\n"

        return txt

def parse(fh):
    """This function parses a mode description and enters it into the 
       'blackboard.mode_description_db'. Once all modes are parsed
       they can be translated into 'real' modes and are located in
       'blackboard.mode_db'. 
    """

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    skip_whitespace(fh)
    mode_name = read_identifier(fh, OnMissingStr="Missing identifier at beginning of mode definition.")

    # NOTE: constructor does register this mode in the mode_db
    new_mode  = ModeDescription(mode_name, fh.name, get_current_line_info_number(fh))

    # (*) inherited modes / option_db
    skip_whitespace(fh)
    dummy = fh.read(1)
    if dummy not in [":", "{"]:
        error_msg("missing ':' or '{' after mode '%s'" % mode_name, fh)

    if dummy == ":":
        __parse_option_list(new_mode, fh)

    # (*) read in pattern-action pairs and events
    while __parse_element(new_mode, fh): 
        pass

def finalize():
    """After all modes have been defined, the mode descriptions can now
       be translated into 'real' modes.
    """
    # (*) Translate each mode description int a 'real' mode
    for name, mode_descr in blackboard.mode_description_db.iteritems():
        blackboard.mode_db[name] = Mode(mode_descr)

    if blackboard.initial_mode is None:
        # Choose an applicable mode as start mode
        single = None
        for name, mode in blackboard.mode_db.iteritems():
            if mode.abstract_f(): 
                continue
            elif single is not None:
                error_msg("No initial mode defined via 'start' while more than one applicable mode exists.\n" + \
                          "Use for example 'start = %s;' in the quex source file to define an initial mode." \
                          % single.name)
            else:
                single = mode

        if single is None:
            blackboard.initial_mode = None
        else:
            blackboard.initial_mode = UserCodeFragment(single.name, SourceReference=single.sr)

    # (*) perform consistency check 
    consistency_check.do(blackboard.mode_db)

def __parse_option_list(new_mode, fh):
    position = fh.tell()
    try:  
        # ':' => inherited modes/option_db follow
        skip_whitespace(fh)

        __parse_base_mode_list(fh, new_mode)
        
        while mode_option.parse(fh, new_mode):
            pass

    except EndOfStreamException:
        fh.seek(position)
        error_eof("mode '%s'." % new_mode.name, fh)

def __parse_base_mode_list(fh, new_mode):
    new_mode.derived_from_list = []
    trailing_comma_f    = False
    while 1 + 1 == 2:
        if   check(fh, "{"): fh.seek(-1, 1); break
        elif check(fh, "<"): fh.seek(-1, 1); break

        skip_whitespace(fh)
        identifier = read_identifier(fh)
        if identifier == "": break

        new_mode.derived_from_list.append(identifier)
        trailing_comma_f = False
        if not check(fh, ","): break
        trailing_comma_f = True


    if trailing_comma_f:
        error_msg("Trailing ',' after base mode '%s'." % new_mode.derived_from_list[-1], fh, 
                  DontExitF=True, WarningF=True)
        
    elif len(new_mode.derived_from_list) != 0:
        # This check is a 'service' -- for those who follow the old convention
        pos = fh.tell()
        skip_whitespace(fh)
        dummy_identifier = read_identifier(fh)
        if dummy_identifier != "":
            error_msg("Missing separating ',' between base modes '%s' and '%s'.\n" \
                      % (new_mode.derived_from_list[-1], dummy_identifier) + \
                      "(The comma separator is mandatory since quex 0.53.1)", fh)
        fh.seek(pos)

def __parse_element(new_mode, fh):
    """Returns: False, if a closing '}' has been found.
                True, else.
    """
    position = fh.tell()
    try:
        description = "pattern or event handler" 

        skip_whitespace(fh)
        # NOTE: Do not use 'read_word' since we need to continue directly after
        #       whitespace, if a regular expression is to be parsed.
        position = fh.tell()

        word = read_until_whitespace(fh)
        if word == "}": return False

        # -- check for 'on_entry', 'on_exit', ...
        if __parse_event(new_mode, fh, word): return True

        fh.seek(position)
        description = "start of mode element: regular expression"
        pattern_str, pattern = regular_expression.parse(fh)

        position    = fh.tell()
        description = "start of mode element: code fragment for '%s'" % pattern_str

        __parse_action(new_mode, fh, pattern_str, pattern)

    except EndOfStreamException:
        fh.seek(position)
        error_eof(description, fh)

    return True

def __parse_action(new_mode, fh, pattern_str, pattern):

    position = fh.tell()
    try:
        skip_whitespace(fh)
        position = fh.tell()
            
        code_obj = code_fragment.parse(fh, "regular expression", ErrorOnFailureF=False) 
        if code_obj is not None:
            new_mode.add_pattern_action_pair(pattern_str, code_obj, pattern)
            return

        fh.seek(position)
        word = read_until_letter(fh, [";"])
        if word == "PRIORITY-MARK":
            # This mark 'lowers' the priority of a pattern to the priority of the current
            # pattern index (important for inherited patterns, that have higher precedence).
            # The parser already constructed a state machine for the pattern that is to
            # be assigned a new priority. Since, this machine is not used, let us just
            # use its id.
            fh.seek(-1, 1)
            check_or_die(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_priority(pattern, fh.name, get_current_line_info_number(fh))

        elif word == "DELETION":
            # This mark deletes any pattern that was inherited with the same 'name'
            fh.seek(-1, 1)
            check_or_die(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_deletion(pattern, fh.name, get_current_line_info_number(fh))
            
        else:
            error_msg("Missing token '{', 'PRIORITY-MARK', 'DELETION', or '=>' after '%s'.\n" % pattern_str + \
                      "found: '%s'. Note, that since quex version 0.33.5 it is required to add a ';'\n" % word + \
                      "to the commands PRIORITY-MARK and DELETION.", fh)


    except EndOfStreamException:
        fh.seek(position)
        error_eof("pattern action", fh)

def __parse_event(new_mode, fh, word):
    pos = fh.tell()

    # Allow '<<EOF>>' and '<<FAIL>>' out of respect for classical tools like 'lex'
    if   word == "<<EOF>>":                  word = "on_end_of_stream"
    elif word == "<<FAIL>>":                 word = "on_failure"
    elif word in blackboard.all_section_title_list:
        error_msg("Pattern '%s' is a quex section title. Has the closing '}' of mode %s \n" % (word, new_mode.name) \
                  + "been forgotten? Else use quotes, i.e. \"%s\"." % word, fh)
    elif len(word) < 3 or word[:3] != "on_": return False

    comment = "Unknown event handler '%s'. \n" % word + \
              "Note, that any pattern starting with 'on_' is considered an event handler.\n" + \
              "use double quotes to bracket patterns that start with 'on_'."

    __general_validate(fh, new_mode, word, pos)
    verify_word_in_list(word, standard_incidence_db.keys(), comment, fh)
    __validate_required_token_policy_queue(word, fh, pos)

    continue_f = True
    if word == "on_end_of_stream" or word == "on_failure":
        # -- When a termination token is sent, no other token shall follow. 
        #    => Enforce return from the analyzer! Do not allow CONTINUE!
        # -- When an 'on_failure' is received allow immediate action of the
        #    receiver => Do not allow CONTINUE!
        continue_f = False

    new_mode.incidence_db[word] = \
            code_fragment.parse(fh, "%s::%s event handler" % (new_mode.name, word),
                                ContinueF=continue_f)

    return True

def __general_validate(fh, Mode, Name, pos):
    if Name == "on_indentation":
        fh.seek(pos)
        error_msg("Definition of 'on_indentation' is no longer supported since version 0.51.1.\n"
                  "Please, use 'on_indent' for the event of an opening indentation, 'on_dedent'\n"
                  "for closing indentation, and 'on_nodent' for no change in indentation.", fh) 


    def error_dedent_and_ndedent(code, A, B):
        filename = "(unknown)"
        line_n   = "0"
        if hasattr(code, "filename"): filename = code.sr.file_name
        if hasattr(code, "line_n"):   line_n   = code.sr.line_n
        error_msg("Indentation event handler '%s' cannot be defined, because\n" % A,
                  fh, DontExitF=True, WarningF=False)
        error_msg("the alternative '%s' has already been defined." % B,
                  filename, line_n)

    if Name == "on_dedent" and Mode.incidence_db.has_key("on_n_dedent"):
        fh.seek(pos)
        code = Mode.incidence_db["on_n_dedent"]
        if not code.is_whitespace():
            error_dedent_and_ndedent(code, "on_dedent", "on_n_dedent")
                      
    if Name == "on_n_dedent" and Mode.incidence_db.has_key("on_dedent"):
        fh.seek(pos)
        code = Mode.incidence_db["on_dedent"]
        if not code.is_whitespace():
            error_dedent_and_ndedent(code, "on_n_dedent", "on_dedent")
                      
def __validate_required_token_policy_queue(Name, fh, pos):
    """Some handlers are better only used with token policy 'queue'."""

    if Name not in ["on_entry", "on_exit", 
                    "on_indent", "on_n_dedent", "on_dedent", "on_nodent", 
                    "on_indentation_bad", "on_indentation_error", 
                    "on_indentation"]: 
        return
    if Setup.token_policy == "queue":
        return

    pos_before = fh.tell()
    fh.seek(pos)
    error_msg("Using '%s' event handler, while the token queue is disabled.\n" % Name + \
              "Use '--token-policy queue', so then tokens can be sent safer\n" + \
              "from inside this event handler.", fh,
              DontExitF=True, SuppressCode=NotificationDB.warning_on_no_token_queue) 
    fh.seek(pos_before)

