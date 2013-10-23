
from   quex.input.setup                                import NotificationDB
import quex.input.regular_expression.core              as     regular_expression
from   quex.input.regular_expression.construct         import Pattern           
import quex.input.files.mode_option                    as     mode_option
import quex.input.files.code_fragment                  as     code_fragment
from   quex.input.files.counter_db                     import CounterDB
from   quex.input.files.counter_setup                  import LineColumnCounterSetup_Default
import quex.input.files.consistency_check              as     consistency_check
import quex.engine.generator.skipper.indentation_counter as   indentation_counter
from   quex.engine.analyzer.door_id_address_label      import Label
import quex.engine.generator.skipper.character_set     as     skip_character_set
from   quex.engine.generator.action_info               import CodeFragment, \
                                                              UserCodeFragment, \
                                                              GeneratedCode, \
                                                              PatternActionInfo
import quex.engine.generator.skipper.range             as     skip_range
import quex.engine.generator.skipper.nested_range      as     skip_nested_range
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
                              E_SpecialPatterns, \
                              E_ActionIDs, \
                              event_handler_db, \
                              mode_option_info_db 

from   copy        import deepcopy
from   collections import namedtuple
from   operator    import itemgetter

#-----------------------------------------------------------------------------------------
# ModeDescription/Mode Objects:
#
# During parsing 'ModeDescription' objects are generated. Once parsing is over, 
# the descriptions are translated into 'real' mode objects where code can be generated
# from. All matters of inheritance and pattern resolution are handled in the
# transition from description to real mode.
#-----------------------------------------------------------------------------------------

PatternRepriorization = namedtuple("PatternRepriorization", ("pattern", "new_pattern_index", "file_name", "line_n", "mode_name"))
PatternDeletion       = namedtuple("PatternDeletion",       ("pattern", "pattern_index", "file_name", "line_n", "mode_name"))

class PatternPriority(object):
    """PatternPriority objects may need re-assignment so they cannot
    be implemented as tuple or named tuple.
    """
    __slots__ = ("mode_hierarchy_index", "pattern_index")
    def __init__(self, MHI, PatternIdx):
        self.mode_hierarchy_index = MHI
        self.pattern_index        = PatternIdx

    def __cmp__(self, Other):
        return cmp((self.mode_hierarchy_index,  self.pattern_index),
                   (Other.mode_hierarchy_index, Other.pattern_index))

class ModeDescription:
    registry_db = {}  # map:  mode name --> ModeDescription object

    def __init__(self, Name, Filename, LineN):
        # Register ModeDescription at the mode database
        ModeDescription.registry_db[Name] = self
        self.name     = Name
        self.filename = Filename
        self.line_n   = LineN

        self.base_modes = []

        # (*) Pattern-Action Pairs:
        #
        #     Set of all pairs: 'pattern' and the 'reaction' upon their detection.
        #
        self.__pattern_action_pair_list = []  

        # (*) Repriorization Database
        #   
        #     Lists all patterns which have to be reprioritized.
        #
        self.__repriorization_info_list = []  
        #                              
        #
        # (*) Deletion Database
        # 
        #     Lists all patterns which have to be deleted. 
        #
        self.__deletion_info_list = [] 

        # (*) Default Options
        #
        # Not only copy the reference, copy the default value object!
        self.options = dict((name, deepcopy(descr.default_value))
                            for name, descr in mode_option_info_db.iteritems())

        # (*) Default Event Handler: Empty
        #
        self.events = dict((name, CodeFragment()) 
                            for name in event_handler_db.iterkeys())

    def add_pattern_action_pair(self, PatternStr, Action, ThePattern, Comment=""):
        assert     ThePattern.sm.is_DFA_compliant()
        assert     ThePattern.pre_context_sm is None \
               or  ThePattern.pre_context_sm.is_DFA_compliant()
        assert     ThePattern.pre_context_sm is None \
               or  ThePattern.pre_context_sm.has_orphaned_states() == False
        assert     ThePattern.sm.has_orphaned_states() == False

        self.__pattern_action_pair_list.append(PatternActionInfo(ThePattern, Action, PatternStr, 
                                               ModeName=self.name, Comment=Comment))

    def add_match_priority(self, ThePattern, FileName, LineN):
        """Whenever a pattern in the mode occurs, which is identical to that given
           by 'ThePattern', then the priority is adapted to the pattern index given
           by the current pattern index.
        """
        PatternIdx = ThePattern.sm.get_id() 
        self.__repriorization_info_list.append(PatternRepriorization(ThePattern, PatternIdx, FileName, LineN, self.name))

    def add_match_deletion(self, ThePattern, FileName, LineN):
        """If one of the base modes contains a pattern which is identical to this
           pattern, it has to be deleted.
        """
        PatternIdx = ThePattern.sm.get_id() 
        self.__deletion_info_list.append(PatternDeletion(ThePattern, PatternIdx, FileName, LineN, self.name))

    def add_option(self, Option, Value):
        """SANITY CHECK:
                -- which options are concatinated to a list
                -- which ones are replaced
                -- what are the values of the options
        """
        assert mode_option_info_db.has_key(Option)

        option_info = mode_option_info_db[Option]
        if option_info.type == "list":
            self.options.setdefault(Option, []).append(Value)
        else:
            if option_info.domain is not None: assert Value in option_info.domain
            self.options[Option] = Value

    def get_pattern_action_pair_list(self):
        return self.__pattern_action_pair_list

    def get_repriorization_info_list(self):
        return self.__repriorization_info_list

    def get_deletion_info_list(self):
        return self.__deletion_info_list

class Mode:
    def __init__(self, Other):
        """Translate a ModeDescription into a real Mode. Here is the place were 
           all rules of inheritance mechanisms and pattern precedence are applied.
        """
        assert isinstance(Other, ModeDescription)
        self.name     = Other.name
        self.filename = Other.filename
        self.line_n   = Other.line_n
        self.options  = Other.options

        self.signal_character_list = [
            (Setup.buffer_limit_code, "Buffer Limit Code"),
            (Setup.path_limit_code,   "Path Limit Code")
        ]

        self.__base_mode_sequence = []
        self.__determine_base_mode_sequence(Other, [])

        # (*) Collection Options
        self.__collect_options()

        # (0) Determine Line/Column Counter Database
        self.__counter_db = self.__prepare_counter_db()

        # (*) Collect Event Handlers
        self.__event_handler_db = {}
        self.__collect_event_handler()
        
        # (*) Collect Pattern Action Pairs in 'xpap_list'
        #
        # The 'xpap_list' is the list of eXtended Pattern Action Pairs.
        # Each element in the list consist of
        #
        #      [0] -- a PatternPriority, given by 'mode_hierarchy_index'
        #             and 'pattern_index'.
        #      [1] -- a pattern action pair
        #
        # The pattern priority allows to keep the list sorted according
        # to its priority given by the mode's position in the inheritance
        # hierarchy and the pattern index itself.
        xpap_list = []

        # -- (Optional) Skippers
        self.__prepare_skip(xpap_list, MHI=-4)
        self.__prepare_skip_range(xpap_list, MHI=-3)
        self.__prepare_skip_nested_range(xpap_list, MHI=-3)

        # -- (Optional) Indentation Counter
        self.__prepare_indentation_counter(xpap_list, MHI=-1)

        # -- Collect 'real' Pattern/Action Pairs
        self.__collect_pattern_action_pairs(xpap_list)

        # (*) Delete and reprioritize
        self.__history_deletion       = self.__perform_deletion(xpap_list) 
        self.__history_repriorization = self.__perform_repriorization(xpap_list) 

        xpap_list.sort(key=itemgetter(0))

        # 'deepcopy' needs to be applied, even for patterns of 'self'.
        # Other derived patterns may rely on the pattern id. 
        self.__pattern_action_pair_list = [ deepcopy(x[1]) for x in xpap_list ]

        for pap in self.__pattern_action_pair_list:
            i = sm_index.get()
            pap.pattern().sm.set_id(long(i))

        # (*) Try to determine line and column counts -- BEFORE Transformation!
        for pap in self.__pattern_action_pair_list:
            pap.pattern().prepare_count_info(self.__counter_db, 
                                             Setup.buffer_codec_transformation_info)

        # (*) Transform anything into the buffer's codec
        #     Skippers: What is relevant to enter the skippers is transformed.
        #               Related data (skip character set, ... ) is NOT transformed!
        for pap in self.__pattern_action_pair_list:
            if not pap.pattern().transform(Setup.buffer_codec_transformation_info):
                error_msg("Pattern contains elements not found in engine codec '%s'." % Setup.buffer_codec,
                          pap.pattern().file_name, pap.pattern().line_n, DontExitF=True)

        # (*) Cut the signalling characters from any pattern or state machine
        for pap in self.__pattern_action_pair_list:
            pap.pattern().cut_character_list(self.signal_character_list)

        # (*) Pre-contexts and BIPD can only be mounted, after the transformation.
        for pap in self.__pattern_action_pair_list:
            pap.pattern().mount_post_context_sm()
            pap.pattern().mount_pre_context_sm()

        # (*) Default counter required?
        self.__default_character_counter_required_f = False

    @property
    def counter_db(self): return self.__counter_db

    def insert_code_fragment_at_front(self, EventName, TheCodeFragment):
        assert isinstance(TheCodeFragment, CodeFragment)
        assert EventName == "on_end_of_stream"
        self.__event_handler_db[EventName].insert(0, TheCodeFragment)

    def set_code_fragment_list(self, EventName, TheCodeFragment):
        assert isinstance(TheCodeFragment, CodeFragment)
        assert EventName in ["on_end_of_stream", "on_failure"]
        assert len(self.__event_handler_db[EventName]) == 0
        self.__event_handler_db[EventName] = [TheCodeFragment]

    def has_base_mode(self):
        return len(self.__base_mode_sequence) != 1

    def has_code_fragment_list(self, EventName):
        assert self.__event_handler_db.has_key(EventName)
        return len(self.__event_handler_db[EventName]) != 0

    def has_event_handler(self):
        for entry in self.__event_handler_db.itervalues():
            if len(entry) != 0: return True
        return False

    def default_character_counter_required_f(self):
        """If there is one pattern where the character count cannot be
        determined from its structure or the lexeme length, then the default
        character counter needs to be implemented. This is documented by the
        flag below."""
        return self.__default_character_counter_required_f 

    def default_character_counter_required_f_set(self):
        self.__default_character_counter_required_f = True

    def get_base_mode_sequence(self):
        return self.__base_mode_sequence

    def get_base_mode_name_list(self):
        return map(lambda mode: mode.name, self.__base_mode_sequence)

    def get_code_fragment_list(self, EventName):
        assert self.__event_handler_db.has_key(EventName)
        return self.__event_handler_db[EventName]

    def get_pattern_action_pair_list(self):
        return self.__pattern_action_pair_list

    def get_indentation_counter_terminal_index(self):
        """Under some circumstances a terminal code need to jump to the indentation
           counter directly. Thus, it must be known in what terminal it is actually 
           located.

           To be on the safe side: There might be transformation, repriorization,
           or whatsoever. So, we search for an indentation counter here.

            RETURNS: None, if no indentation counter is involved.
                     > 0,  terminal id of the terminal that contains the indentation
                           counter.
        """
        for pap in self.__pattern_action_pair_list:
            if pap.comment == E_SpecialPatterns.INDENTATION_NEWLINE:
                return pap.pattern().sm.get_id()
        return None

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

        if len(self.__history_deletion) != 0:
            txt += "    DELETION ACTIONS:\n"
            for entry in self.__history_deletion:
                txt += "      %s:  %s%s  (from mode %s)\n" % \
                       (entry[0], " " * (L - len(self.name)), entry[1], entry[2])
            txt += "\n"

        if len(self.__history_repriorization) != 0:
            txt += "    PRIORITY-MARK ACTIONS:\n"
            self.__history_repriorization.sort(lambda x, y: cmp(x[4], y[4]))
            for entry in self.__history_repriorization:
                txt += "      %s: %s%s  (from mode %s)  (%i) --> (%i)\n" % \
                       (entry[0], " " * (L - len(self.name)), entry[1], entry[2], entry[3], entry[4])
            txt += "\n"

        if len(self.__pattern_action_pair_list) != 0:
            txt += "    PATTERN-ACTION PAIRS:\n"
            def my_key(x):
                if   x.pattern() in E_ActionIDs: return (0, str(x.pattern()))
                elif hasattr(x.pattern(), "sm"): return (1, x.pattern().sm.get_id())
                else:                            return (2, x)

            self.__pattern_action_pair_list.sort(key=my_key)

            for pap in self.__pattern_action_pair_list:
                if hasattr(pap.pattern(), "sm"): 
                    txt += "      (%3i) %s: %s%s\n" % \
                           (pap.pattern().sm.get_id(),
                            pap.mode_name, " " * (L - len(self.name)), 
                            pap.pattern_string())
                else:
                    txt += "      %s\n" % pap.pattern()
            txt += "\n"

        return txt

    def default_indentation_handler_sufficient(Mode):
        """If no user defined indentation handler is defined, then the 
           default token handler is sufficient.
        """
        return     not Mode.has_code_fragment_list("on_indentation_error") \
               and not Mode.has_code_fragment_list("on_indentation_bad")   \
               and not Mode.has_code_fragment_list("on_indent")            \
               and not Mode.has_code_fragment_list("on_dedent")            \
               and not Mode.has_code_fragment_list("on_nodent") 
           
    def __determine_base_mode_sequence(self, ModeDescr, InheritancePath):
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

            error_msg("circular inheritance detected:\n" + msg, ModeDescr.filename, ModeDescr.line_n)

        base_mode_name_list_reversed = deepcopy(ModeDescr.base_modes)
        #base_mode_name_list_reversed.reverse()
        for name in base_mode_name_list_reversed:
            # -- does mode exist?
            verify_word_in_list(name, ModeDescription.registry_db.keys(),
                                "Mode '%s' inherits mode '%s' which does not exist." % (ModeDescr.name, name),
                                ModeDescr.filename, ModeDescr.line_n)

            if name in map(lambda m: m.name, self.__base_mode_sequence): continue

            # -- grab the mode description
            mode_descr = ModeDescription.registry_db[name]
            self.__determine_base_mode_sequence(mode_descr, InheritancePath + [ModeDescr.name])

        self.__base_mode_sequence.append(ModeDescr)

        return self.__base_mode_sequence

    def __collect_options(self):
        # self.__base_mode_sequence[-1] = mode itself
        for mode in self.__base_mode_sequence[:-1]:
            for name, option_descr in mode_option_info_db.items():
                if option_descr.type != "list": continue
                # Need to decouple by means of 'deepcopy'
                self.options.setdefault(name, []).extend(mode.options[name])

    def __get_unique_setup_option(self, OptionName):
        """Loop over all related modes in the base mode sequence and search for
        setup data. Make sure, that the whole inheritance tree does not contain
        two setup options. Setups of a kind must happen in one single mode.
        """
        assert OptionName in ["indentation", "counter"] # In case of extension see 'setup_name' below!
        # Iterate from the base to the top
        setup = None
        for mode_descr in self.__base_mode_sequence:
            local = mode_descr.options[OptionName]
            if local is None: 
                continue
            elif setup is not None:
                setup_name = { "indentation": "indentation counter", 
                               "counter":     "line column counter",
                             }[OptionName]
                error_msg("Hierarchie of mode '%s' contains more than one specification of\n" % self.name + \
                          "an %s. First one here and second one\n" % setup_name, \
                          local.fh, DontExitF=True, WarningF=False)
                error_msg("at this place.", setup.fh)
            else:
                setup = local

        return setup

    def __prepare_counter_db(self):
        """Counters can only be specified at one place. This function checks whether 
           the counter setups are unique or doubly specified. The check happens
           inside __get_unique_setup_option().
        """
        lcc_setup = self.__get_unique_setup_option("counter") # Line/Column Counter Setup
        if lcc_setup is None:
            lcc_setup = LineColumnCounterSetup_Default()

        return CounterDB(lcc_setup)

    def __prepare_skip(self, xpap_list, MHI):
        """MHI = Mode hierarchie index."""
        ssetup_list = self.options.get("skip")

        if ssetup_list is None or len(ssetup_list) == 0:
            return

        iterable                            = ssetup_list.__iter__()
        pattern_str, pattern, character_set = iterable.next()
        # Multiple skippers from different modes are combined into one pattern.
        # This means, that we cannot say exactly where a 'skip' was defined 
        # if it intersects with another pattern.
        file_name = pattern.file_name
        line_n    = pattern.line_n
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
        terminal = TerminalSkipCharacterSet(character_set, self.counter_db, file_name, line_n)

        # It is not necessary to store the count action along with the state
        # machine.  This is done in "action_preparation.do()" for each
        # terminal.
        sm_list = [ 
            StateMachine.from_character_set(count_cmd_info.trigger_set) 
            for count_cmd_info in terminal.count_command_map.itervalues() 
        ]
        terminal.require_label_SKIP_f = (len(sm_list) != 1)

        # Skipper code is generated later, all but one skipper go to a terminal
        # that only counts according to the character which appeared.  The last
        # implements the skipper.
        def xpap(MHI, SM, Action, Comment=None):
            return ((PatternPriority(MHI, SM.get_id()),    
                     PatternActionInfo(Pattern(SM), Action, pattern_str, ModeName=self.name, Comment=Comment)))

        interim_terminal = TerminalInterim(terminal.index) # interim terminal goes to terminal
        xpap_list.extend(xpap(MHI, sm,          interim_terminal) for sm in sm_list[:-1])
        xpap_list.append(xpap(MHI, sm_list[-1], terminal, Comment=E_SpecialPatterns.SKIP))
        return

    def __prepare_skip_range(self, xpap_list, MHI):
        """MHI = Mode hierarchie index."""
        self.__prepare_skip_range_core(xpap_list, MHI, "skip_range", 
                                       skip_range.do, E_SpecialPatterns.SKIP_RANGE)

    def __prepare_skip_nested_range(self, xpap_list, MHI):
        """MHI = Mode hierarchie index."""
        self.__prepare_skip_range_core(xpap_list, MHI, "skip_nested_range", 
                                       skip_nested_range.do, E_SpecialPatterns.SKIP_NESTED_RANGE)

    def __prepare_skip_range_core(self, xpap_list, MHI, OptionName, SkipperFunction, Comment):
        """MHI = Mode hierarchie index."""

        ssetup_list = self.options.get(OptionName)

        if ssetup_list is None or len(ssetup_list) == 0:
            return

        for i, range_skip_info in enumerate(ssetup_list):
            opener_str, opener_pattern, opener_sequence, \
            closer_str, closer_pattern, closer_sequence  = range_skip_info

            # Skipper code is to be generated later
            action = GeneratedCode(SkipperFunction,
                                   FileName = opener_pattern.file_name,
                                   LineN    = opener_pattern.line_n) # get_current_line_info_number(fh))

            action.data["opener_sequence"] = opener_sequence
            action.data["opener_pattern"]  = opener_pattern
            action.data["closer_sequence"] = closer_sequence
            action.data["closer_pattern"]  = closer_pattern

            xpap_list.append((PatternPriority(MHI, i), 
                              PatternActionInfo(opener_pattern, action, opener_str, 
                                                ModeName=self.name, Comment=Comment)))

    def __prepare_indentation_counter(self, xpap_list, MHI):
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

        isetup = self.__get_unique_setup_option("indentation")

        if isetup is None:
            return 

        # The indentation counter is entered upon the appearance of the unsuppressed
        # newline pattern. 
        pap_suppressed_newline = None
        if isetup.newline_suppressor_state_machine.get() is not None:
            pattern_str =   "(" + isetup.newline_suppressor_state_machine.pattern_string() + ")" \
                          + "(" + isetup.newline_state_machine.pattern_string() +            ")"
            sm = sequentialize.do([isetup.newline_suppressor_state_machine.get(),
                                   isetup.newline_state_machine.get()])

            # When a suppressed newline is detected, restart the analysis.
            code = UserCodeFragment("goto %s;" % Label.global_reentry(GotoedF=True), 
                                    isetup.newline_suppressor_state_machine.file_name, 
                                    isetup.newline_suppressor_state_machine.line_n)

            pap_suppressed_newline = PatternActionInfo(Pattern(sm), code, 
                                                       pattern_str, 
                                                       ModeName=self.name, 
                                                       Comment=E_SpecialPatterns.SUPPRESSED_INDENTATION_NEWLINE)

            xpap_list.append((PatternPriority(MHI, 0), pap_suppressed_newline))

        # When there is an empty line, then there shall be no indentation count on it.
        # Here comes the trick: 
        #
        #      Let               newline         
        #      be defined as:    newline ([space]* newline])*
        # 
        # This way empty lines are eaten away before the indentation count is activated.
        x0 = StateMachine()                                             # 'space'
        x0.add_transition(x0.init_state_index, isetup.indentation_count_character_set(), 
                          AcceptanceF=True)
        x1 = repeat.do(x0)                                              # '[space]*'
        x2 = sequentialize.do([x1, isetup.newline_state_machine.get()]) # '[space]* newline'
        x3 = repeat.do(x2)                                              # '([space]* newline)*'
        x4 = sequentialize.do([isetup.newline_state_machine.get(), x3]) # 'newline ([space]* newline)*'
        sm = beautifier.do(x4)                                          # nfa to dfa; hopcroft optimization

        action      = GeneratedCode(indentation_counter.do, 
                                    isetup.newline_state_machine.file_name, 
                                    isetup.newline_state_machine.line_n)
        action.data["indentation_setup"] = isetup

        pap_newline = PatternActionInfo(Pattern(sm), action, 
                                        isetup.newline_state_machine.pattern_string(), 
                                        ModeName=self.name, 
                                        Comment=E_SpecialPatterns.INDENTATION_NEWLINE)

        xpap_list.append((PatternPriority(MHI, 1), pap_newline))

        return

    def __collect_event_handler(self):
        """Collect event handlers from base mode and the current mode.
           Event handlers of the most 'base' mode come first, then the 
           derived event handlers. 

           See '__determine_base_mode_sequence(...) for details about the line-up.
        """
        for event_name in event_handler_db.iterkeys():
            entry = []
            for mode_descr in self.__base_mode_sequence:
                fragment = mode_descr.events[event_name]
                if fragment is not None and not fragment.is_whitespace():
                    entry.append(fragment)
            self.__event_handler_db[event_name] = entry

        return 

    def __collect_pattern_action_pairs(self, xpap_list):
        """Collect patterns of all inherited modes. Patterns are like virtual functions
           in C++ or other object oriented programming languages. Also, the patterns of the
           uppest mode has the highest priority, i.e. comes first.
        """
        for mode_hierarchy_index, mode_descr in enumerate(self.__base_mode_sequence):
            xpap_list.extend(
                (PatternPriority(mode_hierarchy_index, pap.pattern().sm.get_id()), pap)
                for pap in mode_descr.get_pattern_action_pair_list())
        return

    def __perform_repriorization(self, xpap_list):
        def repriorize(MHI, Info, xpap_list, ModeName, history):
            done_f = False
            for xpap in xpap_list:
                if     xpap[0].mode_hierarchy_index <= MHI \
                   and xpap[0].pattern_index        < Info.new_pattern_index \
                   and identity_checker.do(xpap[1].pattern(), Info.pattern):
                    done_f = True
                    history.append([ModeName, 
                                    xpap[1].pattern_string(), 
                                    xpap[1].mode_name,
                                    xpap[1].pattern().sm.get_id(), 
                                    Info.new_pattern_index])
                    xpap[0].mode_hierarchy_index = MHI
                    xpap[0].pattern_index        = Info.new_pattern_index

            if not done_f and Info.mode_name == ModeName:
                error_msg("PRIORITY mark does not have any effect.", 
                          Info.file_name, Info.line_n, DontExitF=True)

        history = []
        for mode_hierarchy_index, mode_descr in enumerate(self.__base_mode_sequence):
            for info in mode_descr.get_repriorization_info_list():
                repriorize(mode_hierarchy_index, info, xpap_list, self.name, history)
        return history

    def __perform_deletion(self, xpap_list):
        def delete(MHI, Info, xpap_list, ModeName, history):
            done_f = False
            size   = len(xpap_list)
            i      = 0
            while i < size:
                xpap = xpap_list[i]
                if     xpap[0].mode_hierarchy_index <= MHI \
                   and xpap[0].pattern_index < Info.pattern_index \
                   and superset_check.do(Info.pattern, xpap[1].pattern()):
                    done_f  = True
                    del xpap_list[i]
                    history.append([ModeName, xpap[1].pattern_string(), xpap[1].mode_name])
                    size   -= 1
                else:
                    i += 1

            if not done_f and Info.mode_name == ModeName:
                error_msg("DELETION mark does not have any effect.", 
                          Info.file_name, Info.line_n, DontExitF=True)

        history = []
        for mode_hierarchy_index, mode_descr in enumerate(self.__base_mode_sequence):
            for info in mode_descr.get_deletion_info_list():
                delete(mode_hierarchy_index, info, xpap_list, self.name, history)
        return history

def parse(fh):
    """This function parses a mode description and enters it into the 
       'ModeDescription.registry_db'. Once all modes are parsed
       they can be translated into 'real' modes and are located in
       'blackboard.mode_db'. 
    """

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    skip_whitespace(fh)
    mode_name = read_identifier(fh, OnMissingStr="Missing identifier at beginning of mode definition.")

    # NOTE: constructor does register this mode in the mode_db
    new_mode  = ModeDescription(mode_name, fh.name, get_current_line_info_number(fh))

    # (*) inherited modes / options
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
    for name, mode_descr in ModeDescription.registry_db.iteritems():
        blackboard.mode_db[name] = Mode(mode_descr)

    if blackboard.initial_mode is None:
        # Choose an applicable mode as start mode
        single = None
        for name, mode in blackboard.mode_db.iteritems():
            if mode.options["inheritable"] == "only": 
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
            blackboard.initial_mode = UserCodeFragment(single.name, single.filename, single.line_n)

    # (*) perform consistency check 
    consistency_check.do(blackboard.mode_db)

def __parse_option_list(new_mode, fh):
    position = fh.tell()
    try:  
        # ':' => inherited modes/options follow
        skip_whitespace(fh)

        __parse_base_mode_list(fh, new_mode)
        
        while mode_option.parse(fh, new_mode):
            pass

    except EndOfStreamException:
        fh.seek(position)
        error_eof("mode '%s'." % new_mode.name, fh)

def __parse_base_mode_list(fh, new_mode):
    new_mode.base_modes = []
    trailing_comma_f    = False
    while 1 + 1 == 2:
        if   check(fh, "{"): fh.seek(-1, 1); break
        elif check(fh, "<"): fh.seek(-1, 1); break

        skip_whitespace(fh)
        identifier = read_identifier(fh)
        if identifier == "": break

        new_mode.base_modes.append(identifier)
        trailing_comma_f = False
        if not check(fh, ","): break
        trailing_comma_f = True


    if trailing_comma_f:
        error_msg("Trailing ',' after base mode '%s'." % new_mode.base_modes[-1], fh, 
                  DontExitF=True, WarningF=True)
        
    elif len(new_mode.base_modes) != 0:
        # This check is a 'service' -- for those who follow the old convention
        pos = fh.tell()
        skip_whitespace(fh)
        dummy_identifier = read_identifier(fh)
        if dummy_identifier != "":
            error_msg("Missing separating ',' between base modes '%s' and '%s'.\n" \
                      % (new_mode.base_modes[-1], dummy_identifier) + \
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
    verify_word_in_list(word, event_handler_db.keys(), comment, fh)
    __validate_required_token_policy_queue(word, fh, pos)

    continue_f = True
    if word == "on_end_of_stream" or word == "on_failure":
        # -- When a termination token is sent, no other token shall follow. 
        #    => Enforce return from the analyzer! Do not allow CONTINUE!
        # -- When an 'on_failure' is received allow immediate action of the
        #    receiver => Do not allow CONTINUE!
        continue_f = False

    new_mode.events[word] = code_fragment.parse(fh, "%s::%s event handler" % (new_mode.name, word),
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
        if hasattr(code, "filename"): filename = code.filename
        if hasattr(code, "line_n"):   line_n   = code.line_n
        error_msg("Indentation event handler '%s' cannot be defined, because\n" % A,
                  fh, DontExitF=True, WarningF=False)
        error_msg("the alternative '%s' has already been defined." % B,
                  filename, line_n)

    if Name == "on_dedent" and Mode.events.has_key("on_n_dedent"):
        fh.seek(pos)
        code = Mode.events["on_n_dedent"]
        if not code.is_whitespace():
            error_dedent_and_ndedent(code, "on_dedent", "on_n_dedent")
                      
    if Name == "on_n_dedent" and Mode.events.has_key("on_dedent"):
        fh.seek(pos)
        code = Mode.events["on_dedent"]
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


