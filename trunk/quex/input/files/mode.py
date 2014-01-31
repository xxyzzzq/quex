
from   quex.input.setup                                import NotificationDB
import quex.input.regular_expression.core              as     regular_expression
from   quex.input.regular_expression.construct         import Pattern           
import quex.input.files.mode_option                    as     mode_option
from   quex.input.files.mode_option                    import OptionDB, \
                                                              SkipRangeData
import quex.input.files.code_fragment                  as     code_fragment
from   quex.input.files.consistency_check              import __error_message as c_error_message
from   quex.engine.counter                             import CounterSetupLineColumn
from   quex.engine.analyzer.door_id_address_label      import DoorID, dial_db
from   quex.engine.analyzer.terminal.core              import Terminal
from   quex.engine.analyzer.terminal.factory           import TerminalFactory
from   quex.engine.analyzer.commands                   import ColumnCountAdd, \
                                                              GotoDoorId
from   quex.engine.generator.code.core                 import CodeTerminal, \
                                                              CodeTerminalOnMatch, \
                                                              CodeUser
from   quex.engine.generator.code.base                 import CodeFragment

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
import quex.output.cpp.counter_for_pattern         as     counter_for_pattern
from   quex.engine.tools import typed, all_isinstance
import quex.blackboard as blackboard
from   quex.engine.generator.code.base import SourceRef
from   quex.blackboard import setup as Setup, \
                              Lng, \
                              standard_incidence_db, \
                              E_IncidenceIDs, \
                              E_IncidenceIDs_Subset_Terminals, \
                              E_IncidenceIDs_Subset_Special, \
                              E_TerminalType

from   copy        import deepcopy, copy
from   collections import namedtuple
from   operator    import itemgetter, attrgetter
from   itertools   import islice
import types

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

#-----------------------------------------------------------------------------------------
# ModeDescription/Mode Objects:
#
# During parsing 'ModeDescription' objects are generated. Once parsing is over, 
# the descriptions are translated into 'real' mode objects where code can be generated
# from. All matters of inheritance and pattern resolution are handled in the
# transition from description to real mode.
#-----------------------------------------------------------------------------------------

PatternRepriorization = namedtuple("PatternRepriorization", ("pattern", "new_pattern_index", "sr"))
PatternDeletion       = namedtuple("PatternDeletion",       ("pattern", "pattern_index",     "sr"))

class PatternActionInfo(object):
    __slots__ = ("__pattern", "__action")
    def __init__(self, ThePattern, TheAction):
        self.__pattern = ThePattern
        self.__action  = TheAction

    @property
    def line_n(self):    return self.action().sr.line_n
    @property
    def file_name(self): return self.action().sr.file_name

    def pattern(self):   return self.__pattern

    def action(self):    return self.__action

    def __repr__(self):         
        txt  = ""
        txt += "self.mode_name      = %s\n" % repr(self.mode_name)
        if self.pattern() not in E_IncidenceIDs:
            txt += "self.pattern_string = %s\n" % repr(self.pattern().pattern_string())
        txt += "self.pattern        = %s\n" % repr(self.pattern()).replace("\n", "\n      ")
        txt += "self.action         = %s\n" % self.action().get_code_string()
        if self.action().__class__ == UserCodeFragment:
            txt += "self.file_name  = %s\n" % repr(self.action().sr.file_name) 
            txt += "self.line_n     = %s\n" % repr(self.action().sr.line_n) 
        txt += "self.incidence_id = %s\n" % repr(self.pattern().incidence_id()) 
        return txt

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
        self.option_db                  = OptionDB()    # map: option_name    --> OptionSetting
        self.incidence_db               = IncidenceDB() # map: incidence_name --> CodeFragment

        self.reprioritization_info_list = []  
        self.deletion_info_list         = [] 

    @typed(ThePattern=Pattern, Action=CodeUser)
    def add_pattern_action_pair(self, ThePattern, TheAction, fh):
        assert ThePattern.check_consistency()

        if ThePattern.pre_context_trivial_begin_of_line_f:
            blackboard.required_support_begin_of_line_set()

        TheAction.set_source_reference(SourceRef.from_FileHandle(fh, self.name))

        self.pattern_action_pair_list.append(PatternActionInfo(ThePattern, TheAction))

    def add_match_priority(self, ThePattern, fh):
        """Whenever a pattern in the mode occurs, which is identical to that given
           by 'ThePattern', then the priority is adapted to the pattern index given
           by the current pattern index.
        """
        PatternIdx = ThePattern.incidence_id() 
        self.reprioritization_info_list.append(
            PatternRepriorization(ThePattern, PatternIdx, SourceRef.from_FileHandle(fh, self.name))
        )

    def add_match_deletion(self, ThePattern, fh):
        """If one of the base modes contains a pattern which is identical to this
           pattern, it has to be deleted.
        """
        PatternIdx = ThePattern.incidence_id() 
        self.deletion_info_list.append(
            PatternDeletion(ThePattern, PatternIdx, SourceRef(FileName, LineN, self.name))
        )

class IncidenceDB(dict):
    """Database of CodeFragments related to 'incidences'.
    ---------------------------------------------------------------------------

                      incidence_id --> [ CodeFragment ]

    If the 'mode_option_info_db[option_name]' mentions that there can be 
    no multiple definitions or if the options can be overwritten than the 
    list of OptionSetting-s must be of length '1' or the list does not exist.

    ---------------------------------------------------------------------------
    """
    @staticmethod
    def from_BaseModeSequence(BaseModeSequence):
        """Collects the content of the 'incidence_db' member of this mode and
        its base modes. 

        RETURNS:      map:    incidence_id --> [ CodeFragment ]
        """
        # Special incidences from 'standard_incidence_db'
        result = IncidenceDB()
        for incidence_name, info in standard_incidence_db.iteritems():
            incidence_id, comment = info
            code = None
            for mode_descr in BaseModeSequence:
                code_fragment = mode_descr.incidence_db.get(incidence_name)
                if   code_fragment is None:         continue
                elif code_fragment.is_whitespace(): continue

                if code is None: code = code_fragment.get_code()
                else:            code.extend(code_fragment.get_code())

            if code is not None:
                result[incidence_id] = CodeFragment(code)

        if E_IncidenceIDs.MATCH_FAILURE not in result:
            # BaseModeSequence[-1] is the mode itself
            mode_name = BaseModeSequence[-1].name
            result[E_IncidenceIDs.MATCH_FAILURE] = CodeFragment([
                  "QUEX_ERROR_EXIT(\"\\n    Match failure in mode '%s'.\\n\"\n" % mode_name
                + "                \"    No 'on_failure' section provided for this mode.\\n\"\n"
                + "                \"    Proposal: Define 'on_failure' and analyze 'Lexeme'.\\n\");\n"
            ])
        if E_IncidenceIDs.END_OF_STREAM not in result:
            result[E_IncidenceIDs.END_OF_STREAM] = CodeFragment([
                "self_send(__QUEX_SETTING_TOKEN_ID_TERMINATION);\n"
                "RETURN;\n"
            ])

        return result

    def __setitem__(self, Key, Value):
        if Key == E_IncidenceIDs.INDENTATION_HANDLER:
            blackboard.required_support_indentation_count_set()
        dict.__setitem__(self, Key, Value)

    @typed(factory=TerminalFactory)
    def extract_terminal_db(self, factory):
        """SpecialTerminals: END_OF_STREAM
                             FAILURE
                             CODEC_ERROR
                             ...
        """
        terminal_type_db = {
            E_IncidenceIDs.MATCH_FAILURE: E_TerminalType.MATCH_FAILURE,
            E_IncidenceIDs.END_OF_STREAM: E_TerminalType.END_OF_STREAM,
        }
        mandatory_list = [
            E_IncidenceIDs.MATCH_FAILURE, 
            E_IncidenceIDs.END_OF_STREAM
        ]

        result = {}
        for incidence_id in mandatory_list:
            if incidence_id in self: continue
            terminal_type = terminal_type_db[incidence_id]
            result[incidence_id] = Lng.DEFAULT_CODE_FRAGMENT(terminal_type)

        for incidence_id, code_fragment in self.iteritems():
            if incidence_id not in terminal_type_db: continue
            terminal_type = terminal_type_db[incidence_id]
            code_terminal = CodeTerminal(code_fragment.get_code())
            assert terminal_type not in result
            terminal = factory.do(terminal_type, code_terminal)
            terminal.set_incidence_id(incidence_id)
            result[incidence_id] = terminal

        return result


    def get_CodeTerminal(self, IncidenceId):
        if IncidenceId not in self:
            return CodeTerminal([""])
        else:
            return CodeTerminal(self[IncidenceId].get_code(), LexemeRelevanceF=True)

    def get_text(self, IncidenceId):
        code_fragment = self.get(IncidenceId)
        if code_fragment is None: return ""
        else:                     return "".join(code_fragment.get_code())

    def default_indentation_handler(self):
        return not (   self.has_key(E_IncidenceIDs.INDENTATION_ERROR) \
                    or self.has_key(E_IncidenceIDs.INDENTATION_BAD)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_INDENT)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_DEDENT)   \
                    or self.has_key(E_IncidenceIDs.INDENTATION_N_DEDENT) \
                    or self.has_key(E_IncidenceIDs.INDENTATION_NODENT))

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
    def __init__(self, Origin):
        """Translate a ModeDescription into a real Mode. Here is the place were 
        all rules of inheritance mechanisms and pattern precedence are applied.
        """
        assert isinstance(Origin, ModeDescription)
        self.name = Origin.name
        self.sr   = Origin.sr   # 'SourceRef' -- is immutable

        base_mode_sequence  = self.__determine_base_mode_sequence(Origin, [], [])
        # At least the mode itself must be there
        # The mode itself is base_mode_sequence[-1]
        assert len(base_mode_sequence) >= 1 \
               and base_mode_sequence[-1].name == self.name

        # Collect Options
        # (A finalized Mode does not contain an option_db anymore).
        options_db   = OptionDB.from_BaseModeSequence(base_mode_sequence)
        incidence_db = IncidenceDB.from_BaseModeSequence(base_mode_sequence)

        # Determine Line/Column Counter Database
        counter_db = options_db.value("counter")
        self.__indentation_setup = None

        # Intermediate Step: Priority-Pattern-Terminal List (PPT list)
        #
        # The list is developed so that patterns can be sorted and code 
        # fragments are prepared.
        self.__pattern_list, \
        self.__terminal_db,  \
        self.__default_character_counter_required_f = \
                      self.__prepare_ppt_list(base_mode_sequence, 
                                              options_db, 
                                              counter_db, 
                                              incidence_db)
        
        # (*) Misc
        self.__abstract_f           = self.__is_abstract(incidence_db, Origin.option_db)
        self.__base_mode_sequence   = base_mode_sequence
        self.__entry_mode_name_list = options_db.value_list("entry") # Those can enter this mode.
        self.__exit_mode_name_list  = options_db.value_list("exit")  # This mode can exit to those.
        self.__incidence_db         = incidence_db
        self.__counter_db           = counter_db
        self.__on_after_match_code  = incidence_db.get(E_IncidenceIDs.AFTER_MATCH)

    def abstract_f(self):           return self.__abstract_f

    @property
    def counter_db(self):           return self.__counter_db

    @property
    def exit_mode_name_list(self):  return self.__exit_mode_name_list

    @property
    def entry_mode_name_list(self): return self.__entry_mode_name_list

    @property
    def incidence_db(self): return self.__incidence_db

    @property
    def pattern_list(self):        return self.__pattern_list
    @property
    def on_after_match_code(self): return self.__on_after_match_code
    @property
    def terminal_db(self):         return self.__terminal_db

    @property
    def default_character_counter_required_f(self): return self.__default_character_counter_required_f

    def has_base_mode(self):
        return len(self.__base_mode_sequence) != 1

    def get_base_mode_sequence(self):
        assert len(self.__base_mode_sequence) >= 1 # At least the mode itself is in there
        return self.__base_mode_sequence

    def get_base_mode_name_list(self):
        assert len(self.__base_mode_sequence) >= 1 # At least the mode itself is in there
        return [ mode.name for mode in self.__base_mode_sequence ]

    def match_indentation_counter_newline_pattern(self, Sequence):
        if self.__indentation_setup is None: return False

        return self.__indentation_setup.sm_newline.does_sequence_match(Sequence)

    def __is_abstract(self, IncidenceDb, OriginalOptionDb):
        """If the mode has incidences and/or patterns defined it is free to be 
        abstract or not. If neither one is defined, it cannot be implemented and 
        therefore MUST be abstract.
        """
        abstract_f = (OriginalOptionDb.value("inheritable") == "only")

        if len(IncidenceDb) != 0 or len(self.pattern_list) != 0:
            return abstract_f

        elif abstract_f == False:
            error_msg("Mode without pattern and event handlers needs to be 'inheritable only'.\n" + \
                      "<inheritable: only> has been set automatically.", self.sr.file_name, self.sr.line_n,  
                      DontExitF=True)
            abstract_f = True # Change to 'inheritable: only', i.e. abstract_f == True.

        return abstract_f

    def __pattern_list_construct(self, ppt_list, CounterDb):
        pattern_list = [ 
            pattern 
            for priority, pattern, terminal in sorted(ppt_list, key=attrgetter("priority")) 
        ]

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

           => That is the mode itself is base_mode_sequence[-1]

           => Patterns and event handlers of 'E' have precedence over
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

    def __prepare_ppt_list(self, BaseModeSequence, OptionsDb, CounterDb, IncidenceDb):
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
        terminal_factory = TerminalFactory(self.name, IncidenceDb) 

        ppt_list = self.__pattern_action_pairs_collect(BaseModeSequence, 
                                                       terminal_factory, CounterDb)

        # (*) Collect pattern recognizers and several 'incidence detectors' in 
        #     state machine lists. When the state machines accept this triggers
        #     an incidence which is associated with an entry in the incidence_db.
        skip_terminal = self.__prepare_skip(ppt_list, 
                                            OptionsDb.value_sequence("skip"), 
                                            CounterDb,
                                            MHI=-4, 
                                            terminal_factory=terminal_factory)

        self.__prepare_skip_range(ppt_list, 
                                  OptionsDb.value_sequence("skip_range"), 
                                  MHI=-3, terminal_factory=terminal_factory, CounterDb=CounterDb)
        self.__prepare_skip_nested_range(ppt_list, 
                                         OptionsDb.value_sequence("skip_nested_range"), 
                                         MHI=-3, terminal_factory=terminal_factory, CounterDb=CounterDb)

        self.__prepare_indentation_counter(ppt_list, 
                                           OptionsDb.value("indentation"), 
                                           MHI=-1, terminal_factory=terminal_factory, CounterDb=CounterDb)

        # (*) Delete and reprioritize
        self.__perform_deletion(ppt_list, BaseModeSequence) 
        self.__perform_reprioritization(ppt_list, BaseModeSequence) 

        # (*) terminal_db
        #     ALSO: Assigns incidence ids according to position on list!
        terminal_db  = self.__prepare_terminals(ppt_list, 
                                                IncidenceDb, 
                                                skip_terminal, 
                                                terminal_factory)

        # (*) pattern list  <-- ppc list 
        pattern_list = self.__pattern_list_construct(ppt_list, 
                                                     CounterDb)

        return pattern_list, terminal_db, terminal_factory.required_default_counter_f

    def __prepare_terminals(self, PPT_List, IncidenceDb, SkipTerminal, terminal_factory):
        """Prepare terminal states for all pattern matches and other terminals,
        such as 'end of stream' or 'failure'. If code is to be generated in a
        delayed fashion, then this may happen as a consequence to the call
        to '.get_code()' to related code fragments.

        RETURNS: 
                          map: incidence_id --> Terminal

        A terminal consists plainly of an 'incidence_id' and a list of text which
        represents the code to be executed when it is reached.
        """
        # (*) re-assign incidence_ids
        #     The incidence ids must be re-assigned according to the 
        #     position in the list.
        for priority, pattern, terminal in PPT_List:
            incidence_id = dial_db.new_incidence_id()
            assert terminal.incidence_id() is None
            pattern.set_incidence_id(incidence_id)
            terminal.set_incidence_id(incidence_id)

        result = {}

        # Every pattern has a terminal for the case that it matches.
        result.update(
            (terminal.incidence_id(), terminal)
            for dummy, dummy, terminal in PPT_List
        )

        # Some incidences have their own terminal
        # THEIR INCIDENCE ID REMAINS FIXED!
        result.update(
            IncidenceDb.extract_terminal_db(terminal_factory)
        )

        if SkipTerminal is not None:
            result[SkipTerminal.incidence_id()] = SkipTerminal

        return result

    def __prepare_skip(self, ppt_list, SkipSetupList, CounterDb, MHI, terminal_factory):
        """MHI = Mode hierarchie index."""
        if SkipSetupList is None or len(SkipSetupList) == 0:
            return None

        iterable               = SkipSetupList.__iter__()
        pattern, character_set = iterable.next()
        pattern_str            = pattern.pattern_string()
        source_reference       = pattern.sr
        # Multiple skippers from different modes are combined into one pattern.
        # This means, that we cannot say exactly where a 'skip' was defined 
        # if it intersects with another pattern.
        for ipattern, icharacter_set in iterable:
            character_set.unite_with(icharacter_set)
            pattern_str += "|" + ipattern.pattern_string()

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

        data = { 
            "counter_db":    CounterDb, 
            "character_set": character_set,
        }
        # The terminal is not related to a pattern, because it is entered
        # from the sub_terminals. Each sub_terminal relates to a sub character
        # set.
        terminal          = terminal_factory.do_generator(None, skip_character_set.do, 
                                                          data, "Character Set Skipper")
        terminal.set_incidence_id(E_IncidenceIDs.SKIP)
        terminal_door_id  = DoorID.incidence(terminal.incidence_id())
        goto_terminal_str = Lng.GOTO(terminal_door_id)
        # Counting actions are added to the terminal automatically by the
        # terminal_factory. The only thing that remains for each sub-terminal:
        # 'goto skipper'.
        dummy, \
        count_command_map = CounterDb.get_count_command_map(character_set)

        for cliid, cmd_info in ccd.count_command_map.iteritems():
            priority         = PatternPriority(MHI, cliid)
            pattern          = Pattern.from_character_set(cmd_info.trigger_set)
            pattern.prepare_count_info(CounterDb, 
                                       Setup.buffer_codec_transformation_info)
            # NOTE: 'terminal_factory.do_plain()' does prepare the counting action.
            code             = CodeTerminal([ goto_terminal_str ])
            sub_terminal     = terminal_factory.do(E_TerminalType.MATCH_PATTERN, 
                                                   code, pattern)
            sub_terminal.set_name("Entry to 'skip': %s" % cmd_info.trigger_set.get_string("hex"))
            ppt_list.append(PPT(priority, pattern, sub_terminal))

        return terminal

    def __prepare_skip_range(self, ppt_list, SkipRangeSetupList, MHI, terminal_factory, CounterDb):
        """MHI = Mode hierarchie index."""
        self.__prepare_skip_range_core(ppt_list, MHI, SkipRangeSetupList,  
                                       skip_range.do, "skip range", terminal_factory, CounterDb)

    def __prepare_skip_nested_range(self, ppt_list, SkipNestedRangeSetupList, MHI, terminal_factory, CounterDb):
        """MHI = Mode hierarchie index."""
        self.__prepare_skip_range_core(ppt_list, MHI, SkipNestedRangeSetupList, 
                                       skip_nested_range.do, "skip nested range", terminal_factory, CounterDb)

    @typed(CodeGeneratorFunction=types.FunctionType)
    def __prepare_skip_range_core(self, ppt_list, MHI, SrSetup, CodeGeneratorFunction, SkipperName,
                                  terminal_factory, CounterDb):
        """MHI = Mode hierarchie index."""

        if SrSetup is None or len(SrSetup) == 0:
            return

        for i, data in enumerate(SrSetup):
            assert isinstance(data, SkipRangeData)
            my_data         = deepcopy(data)
            my_data["mode"] = self

            priority     = PatternPriority(MHI, i)
            pattern      = deepcopy(my_data["opener_pattern"])
            pattern.prepare_count_info(CounterDb, 
                                       Setup.buffer_codec_transformation_info)
            terminal     = terminal_factory.do_generator(pattern, CodeGeneratorFunction, 
                                                         my_data, SkipperName)
            ppt_list.append(PPT(priority, pattern, terminal))

    def __prepare_indentation_counter(self, ppt_list, ISetup, MHI, terminal_factory, CounterDb):
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
        self.__check_indentation_setup = ISetup

        # The indentation counter is entered upon the appearance of the unsuppressed
        # newline pattern. 
        #
        #  TODO: newline = newline/\C{newline suppressor}, i.e. a newline is only a
        #        newline if it is followed by something else than a newline suppressor.
        ppt_suppressed_newline = None
        if ISetup.newline_suppressor_state_machine.get() is not None:
            pattern_str =   "(" + ISetup.newline_suppressor_state_machine.pattern_string() + ")" \
                          + "(" + ISetup.newline_state_machine.pattern_string() +            ")"
            sm = sequentialize.do([ISetup.newline_suppressor_state_machine.get(),
                                   ISetup.newline_state_machine.get()])

            priority = PatternPriority(MHI, 0)
            pattern  = Pattern(sm, IncidenceId=E_IncidenceIDs.SUPPRESSED_INDENTATION_NEWLINE, 
                               PatternStr=pattern_str)
            pattern.prepare_count_info(CounterDb, 
                                       Setup.buffer_codec_transformation_info)
            code     = CodeTerminal([Lng.GOTO(DoorID.global_reentry())])
            terminal = terminal_factory.do(E_TerminalType.PLAIN, code)
            ppt_suppressed_newline = PPT(priority, pattern, terminal)


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

        if ppt_suppressed_newline is not None:
            ppt_list.append(ppt_suppressed_newline)

        priority = PatternPriority(MHI, 1)
        pattern  = Pattern(sm)
        pattern.prepare_count_info(CounterDb, 
                                   Setup.buffer_codec_transformation_info)
        # pattern.set_incidence_id(IncidenceId=E_IncidenceIDs.INDENTATION_NEWLINE)
        terminal = terminal_factory.do_generator(pattern, indentation_counter.do, 
                                                 data, "Indentation Counter")
        ppt_list.append(PPT(priority, pattern, terminal))
        return

    def __pattern_action_pairs_collect(self, BaseModeSequence, terminal_factory, CounterDb):
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

    def __perform_reprioritization(self, ppt_list, BaseModeSequence):
        def repriorize(MHI, Info, ppt_list, ModeName, history):
            done_f = False
            for ppt in ppt_list:
                priority, pattern, terminal = ppt
                if   priority.mode_hierarchy_index > MHI:                      continue
                elif priority.pattern_index        >= Info.new_pattern_index:  continue
                elif not identity_checker.do(pattern, Info.pattern):           continue

                done_f            = True
                history.append([ModeName, 
                                pattern.pattern_string(), pattern.sr.mode_name,
                                pattern.incidence_id(), Info.new_pattern_index])
                priority.mode_hierarchy_index = MHI
                priority.pattern_index        = Info.new_pattern_index

            if not done_f and Info.sr.mode_name == ModeName:
                error_msg("PRIORITY mark does not have any effect.", 
                          Info.sr.file_name, Info.sr.line_n, DontExitF=True)

        history = []
        for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
            for info in mode_descr.reprioritization_info_list:
                repriorize(mode_hierarchy_index, info, ppt_list, self.name, history)

        self.__doc_history_reprioritization = history

    def __perform_deletion(self, ppt_list, BaseModeSequence):
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
        for mode_hierarchy_index, mode_descr in enumerate(BaseModeSequence):
            for info in mode_descr.deletion_info_list:
                delete(mode_hierarchy_index, info, ppt_list, self.name, history)

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

        self.assert_indentation_setup()

    def unique_pattern_pair_iterable(self):
        """Iterates over pairs of patterns:

            (high precedence pattern, low precedence pattern)

           where 'pattern_i' as precedence over 'pattern_k'
        """
        for i, high in enumerate(self.__pattern_list):
            for low in islice(self.__pattern_list, i+1, None):
                yield high, low

    def check_special_incidence_outrun(self, ErrorCode):
        for high, low in self.unique_pattern_pair_iterable():
            if   high.incidence_id() not in E_IncidenceIDs_Subset_Special: continue
            elif not outrun_checker.do(this.sm, that.sm):                  continue
            c_error_message(that, this, ExitF=True, 
                            ThisComment  = "has lower priority but",
                            ThatComment  = "may outrun",
                            SuppressCode = ErrorCode)
                                 
    def check_higher_priority_matches_subset(self, ErrorCode):
        """Checks whether a higher prioritized pattern matches a common subset
           of the ReferenceSM. For special patterns of skipper, etc. this would
           be highly confusing.
        """
        global special_pattern_list
        for high, low in self.unique_pattern_pair_iterable():
            if   high.incidence_id() not in E_IncidenceIDs_Subset_Special: continue
            elif low.incidence_id() not in E_IncidenceIDs_Subset_Special: continue
            elif not superset_check.do(high.sm, low.sm):             continue

            c_error_message(other_pattern, pattern, ExitF=True, 
                            ThisComment  = "has higher priority and",
                            ThatComment  = "matches a subset of",
                            SuppressCode = ErrorCode)

    def check_dominated_pattern(self, ErrorCode):
        for high, low in self.unique_pattern_pair_iterable():
            # 'low' comes after 'high' => 'i' has precedence
            # Check for domination.
            if superset_check.do(high, low):
                print "#sm0:", high.incidence_id(), high.sm.get_string(NormalizeF=False, Option="hex")
                print "#sm1:", high.incidence_id(), low.sm.get_string(NormalizeF=False, Option="hex")
                c_error_message(high, low, 
                                ThisComment  = "matches a superset of what is matched by",
                                EndComment   = "The former has precedence and the latter can never match.",
                                ExitF        = True, 
                                SuppressCode = ErrorCode)

    def check_match_same(self, ErrorCode):
        """Special patterns shall never match on some common lexemes."""
        for high, low in self.unique_pattern_pair_iterable():
            if   high.incidence_id() not in E_IncidenceIDs_Subset_Special: continue
            elif low.incidence_id() not in E_IncidenceIDs_Subset_Special:  continue

            # A superset of B, or B superset of A => there are common matches.
            if not same_check.do(high.sm, low.sm): continue

            c_error_message(high, low, 
                            ThisComment  = "matches on some common lexemes as",
                            ThatComment  = "",
                            ExitF        = True,
                            SuppressCode = ErrorCode)

    def check_low_priority_outruns_high_priority_pattern(self):
        """Warn when low priority patterns may outrun high priority patterns.
        Assume that the pattern list is sorted by priority!
        """
        for high, low in self.unique_pattern_pair_iterable():
            if outrun_checker.do(high.sm, low.sm):
                c_error_message(low, high, ExitF=False, ThisComment="may outrun")

    def assert_indentation_setup(self):
        # (*) Indentation: Newline Pattern and Newline Suppressor Pattern
        #     shall never trigger on common lexemes.
        indentation_setup = self.__indentation_setup
        if indentation_setup is None: return

        # The newline pattern shall not have intersections with other patterns!
        newline_info            = indentation_setup.newline_state_machine
        newline_suppressor_info = indentation_setup.newline_suppressor_state_machine
        assert newline_info is not None
        if newline_suppressor_info.get() is None: return

        # Newline and newline suppressor should never have a superset/subset relation
        if    superset_check.do(newline_info.get(), newline_suppressor_info.get()) \
           or superset_check.do(newline_suppressor_info.get(), newline_info.get()):

            c_error_message(newline_info, newline_suppressor_info,
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

        assert all_isinstance(self.__pattern_list, Pattern)
        if len(self.__pattern_list) != 0:
            txt += "    PATTERN LIST:\n"
            for x in self.__pattern_list:
                space  = " " * (L - len(x.sr.mode_name)) 
                txt   += "      (%3i) %s: %s%s\n" % \
                         (x.incidence_id(), x.sr.mode_name, space, x.pattern_string())
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

def determine_start_mode(mode_db):
    if not blackboard.initial_mode.sr.is_void():
        return

    # Choose an applicable mode as start mode
    first_candidate = None
    for name, mode in mode_db.iteritems():
        if mode.abstract_f(): 
            continue
        elif first_candidate is not None:
            error_msg("No initial mode defined via 'start' while more than one applicable mode exists.\n" + \
                      "Use for example 'start = %s;' in the quex source file to define an initial mode." \
                      % first_candidate.name)
        else:
            first_candidate = mode

    if first_candidate is None:
        error_msg("No non-abstract mode found in source files.")
    else:
        blackboard.initial_mode = CodeUser(first_candidate.name, SourceReference=first_candidate.sr)

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
        pattern     = regular_expression.parse(fh)
        pattern.set_source_reference(fh, position, new_mode.name)

        position    = fh.tell()
        description = "start of mode element: code fragment for '%s'" % pattern.pattern_string()

        __parse_action(new_mode, fh, pattern.pattern_string(), pattern)

    except EndOfStreamException:
        fh.seek(position)
        error_eof(description, fh)

    return True

def __parse_action(new_mode, fh, pattern_str, pattern):

    position = fh.tell()
    try:
        skip_whitespace(fh)
        position = fh.tell()
            
        code = code_fragment.parse(fh, "regular expression", ErrorOnFailureF=False) 
        if code is not None:
            assert isinstance(code, CodeUser), "Found: %s" % code.__class__
            new_mode.add_pattern_action_pair(pattern, code, fh)
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
            new_mode.add_match_priority(pattern, fh)

        elif word == "DELETION":
            # This mark deletes any pattern that was inherited with the same 'name'
            fh.seek(-1, 1)
            check_or_die(fh, ";", ". Since quex version 0.33.5 this is required.")
            new_mode.add_match_deletion(pattern, fh)
            
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

