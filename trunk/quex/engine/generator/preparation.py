from quex.engine.tools          import typed
from quex.engine.generator.code import CodeFragment
from quex.blackboard            import setup as Setup

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

    def dedicated_indentation_handler_required(self):
        return    self.has_key(E_IncidenceIDs.INDENTATION_ERROR) \
               or self.has_key(E_IncidenceIDs.INDENTATION_BAD)   \
               or self.has_key(E_IncidenceIDs.INDENTATION_INDENT)   \
               or self.has_key(E_IncidenceIDs.INDENTATION_DEDENT)   \
               or self.has_key(E_IncidenceIDs.INDENTATION_N_DEDENT) \
               or self.has_key(E_IncidenceIDs.INDENTATION_NODENT) 


def do(PPC_List, IncidenceDb, CounterDb, IndentationSetup):
    # (1) pattern_list:
    #    
    # containing a sorted list of patterns where pattern-ids are associated 
    # according to a pattern's priority (high priority=low pattern-id). The
    # matching events of patterns are registered in the incidence_db.
    #
    # (2) terminal_db:
    #
    #       E_TerminalID/pattern_id ---> CodeFragment
    #
    # where the CodeFragment is a plain code fragment without any source
    # reference, or information about lexemes or match behavior.
    # 
    assert all_isinstance(ppc_list, PPC)
    pattern_list = __pattern_list_construct(ppc_list, CounterDb)
    terminal_db  = TerminalDb(IncidenceDb, ppc_list)

def __pattern_list_construct(ppc_list):
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

