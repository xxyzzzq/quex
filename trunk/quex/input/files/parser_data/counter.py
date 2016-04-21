# (C) Frank-Rene Schaefer
#
#        .--( LineColumnCount )--------------------------------.
#        |                                                     |
#        | + count_command_map (map: count command --> value)  |
#        '-----------------------------------------------------'
#
#
#        .--( IndentationCount ---> LineColumnCount )----------.
#        |                                                     |
#        | + whitespace_character_set                          |
#        | + bad_character_set                                 |
#        | + sm_newline                                        |
#        | + sm_newline_suppressor                             |
#        | + sm_comment                                        |
#        '-----------------------------------------------------'
#
# (C) Frank-Rene Schaefer
#______________________________________________________________________________                      

from   quex.input.setup                           import NotificationDB
from   quex.input.code.base                       import SourceRefObject, \
                                                         SourceRef, \
                                                         SourceRef_DEFAULT
from   quex.engine.misc.tools                     import typed
import quex.engine.misc.error                     as     error
from   quex.engine.misc.interval_handling         import NumberSet
from   quex.blackboard                            import E_CharacterCountType

from   quex.blackboard import setup as Setup
from   collections     import namedtuple, defaultdict
from   operator        import itemgetter

cc_type_db = {
    "space":                     E_CharacterCountType.COLUMN,
    "grid":                      E_CharacterCountType.GRID,
    "newline":                   E_CharacterCountType.LINE,
    "begin(newline suppressor)": E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR,
    "begin(newline)":            E_CharacterCountType.BEGIN_NEWLINE,
    "begin(comment to newline)": E_CharacterCountType.BEGIN_COMMENT_TO_NEWLINE,
    "end(newline)":              E_CharacterCountType.END_NEWLINE,
    "bad":                       E_CharacterCountType.BAD,
    "whitespace":                E_CharacterCountType.WHITESPACE,
}

cc_type_name_db = dict((value, key) for key, value in cc_type_db.iteritems())

count_operation_db_without_reference = {
    E_CharacterCountType.BAD:    lambda Parameter: [ 
            Op.GotoDoorId(self.door_id_on_bad_indentation) 
        ]
    E_CharacterCountType.COLUMN: lambda Parameter: [
            Op.ColumnCountAdd(Parameter),
        ]
    E_CharacterCountType.GRID:   lambda Parameter: [
            Op.ColumnCountGridAdd(Parameter),
        ]
    E_CharacterCountType.LINE:   lambda Parameter: [
            Op.LineCountAdd(Parameter),
            Op.AssignConstant(E_R.Column, 1),
        ]
}

count_operation_db_with_reference = {
    E_CharacterCountType.BAD:    lambda Parameter, ColumnNPerCodeUnit: [
        Op.ColumnCountReferencePDeltaAdd(E_R.InputP, ColumnNPerCodeUnit, False),
        Op.ColumnCountReferencePSet(E_R.InputP),
        Op.GotoDoorId(self.door_id_on_bad_indentation) 
    ],
    E_CharacterCountType.COLUMN: lambda Parameter, ColumnNPerCodeUnit: [
    ],
    E_CharacterCountType.GRID:   lambda Parameter, ColumnNPerCodeUnit: [
        Op.ColumnCountReferencePDeltaAdd(E_R.InputP, ColumnNPerCodeUnit, True),
        Op.ColumnCountGridAdd(Parameter),
        Op.ColumnCountReferencePSet(E_R.InputP)
    ],
    E_CharacterCountType.LINE:   lambda Parameter, ColumnNPerCodeUnit: [
        Op.LineCountAdd(Parameter),
        Op.AssignConstant(E_R.Column, 1),
        Op.ColumnCountReferencePSet(E_R.InputP)
    ]
}

class CountAction(namedtuple("CountAction", ("cc_type", "value", "sr"))):
    def __new__(self, CCType, Value, sr=None):
        return super(CountAction, self).__new__(self, CCType, Value, sr)

class LineColumnCount:
    def __init__(self, SourceReference):
        self.sr = SourceReference
        # The 'count_command_map' is specified later.
        self.count_command_map = None

    @staticmethod
    def from_FileHandle(fh):
        container = LineColumnCount(SourceRef.from_FileHandle(fh))
        return ReceiverLineColumnCount(container).parse(fh)

    def consistency_check(self):
        self.count_command_map.check_grid_values_integer_multiples()
        # The following is nonsense: We detect that we did not choose an alternative 
        # which is worse?!
        # self.count_command_map.check_homogenous_space_counts()
        self.count_command_map.check_defined(self.sr, E_CharacterCountType.LINE)

class IndentationCount(LineColumnCount):
    @typed(sr=SourceRef)
    def __init__(self, SourceReference):
        LineColumnCount.__init__(SourceReference, None)
        self.whitespace_character_set = SourceRefObject("whitespace", None)
        self.bad_character_set        = SourceRefObject("bad", None)
        self.sm_newline               = SourceRefObject("newline", None)
        self.sm_newline_suppressor    = SourceRefObject("suppressor", None)
        self.sm_comment               = SourceRefObject("comment", None)

    @staticmethod
    def from_FileHandle(fh):
        container = IndentationCount(SourceRef.from_FileHandle(fh))
        return ReceiverIndentationCount(container).parse(fh)

    def consistency_check(self):
        LineColumnCount.consistency_check()
        self.count_command_map.check_defined(self.sr, E_CharacterCountType.WHITESPACE)
        self.count_command_map.check_defined(self.sr, E_CharacterCountType.BEGIN_NEWLINE)
        if self.sm_newline_suppressor.get() is not None:
            if self.sm_newline.get() is None:
                error.log("A newline 'suppressor' has been defined.\n"
                          "But there is no 'newline' in indentation defintion.", 
                          self.sm_newline_suppressor.sr)

    def __str__(self):
        def cs_str(Name, Cs):
            msg  = "%s:\n" % Name
            if Cs is None: msg += "    <none>\n" 
            else:          msg += "    %s\n" % Cs.get_utf8_string()
            return msg

        def sm_str(Name, Sm):
            msg = "%s:\n" % Name
            if Sm is None: 
                msg += "    <none>\n"
            else:          
                msg += "    %s\n" % Sm.get_string(NormalizeF=True, Option="utf8").replace("\n", "\n    ").strip()
            return msg

        return "".join([
            cs_str("Whitespace", self.whitespace_character_set.get()),
            cs_str("Bad",        self.bad_character_set.get()),
            sm_str("Newline",    self.sm_newline.get()),
            sm_str("Suppressor", self.sm_newline_suppressor.get()),
            sm_str("Comment",    self.sm_comment.get()),
        ])

def _error_set_intersection(CcType, Before, sr):
    global cc_type_name_db

    note_f = False
    if    CcType         == E_CharacterCountType.END_NEWLINE \
       or Before.cc_type == E_CharacterCountType.END_NEWLINE:
        note_f = True

    prefix = {
        E_CharacterCountType.COLUMN:                   "",
        E_CharacterCountType.GRID:                     "",
        E_CharacterCountType.LINE:                     "",
        E_CharacterCountType.BEGIN_NEWLINE_SUPPRESSOR: "beginning ",
        E_CharacterCountType.BEGIN_NEWLINE:            "beginning ",
        E_CharacterCountType.END_NEWLINE:              "ending ",
        E_CharacterCountType.BAD:                      "",
        E_CharacterCountType.WHITESPACE:               "",
        E_CharacterCountType.BEGIN_COMMENT_TO_NEWLINE: "beginning ",
    }[CcType]

    error.log("The %scharacter set defined in '%s' intersects" % (prefix, cc_type_name_db[CcType]),
              sr, DontExitF=True)
    error.log("with '%s' at this place." % cc_type_name_db[Before.cc_type], 
              Before.sr, DontExitF=note_f)

    if note_f:
        error.log("Note, for example, 'newline' cannot end with a character which is subject\n"
                  "to indentation counting (i.e. 'space' or 'grid').", sr)

def _error_if_defined_before(Before, sr):
    if not Before.set_f(): return

    error.log("'%s' has been defined before;" % Before.name, sr, 
              DontExitF=True)
    error.log("at this place.", Before.sr)

def extract_trigger_set(sr, Keyword, Pattern):
    if Pattern is None:
        return None
    elif isinstance(Pattern, NumberSet):
        return Pattern

    def check_can_be_matched_by_single_character(SM):
        bad_f      = False
        init_state = SM.get_init_state()
        if SM.get_init_state().is_acceptance(): 
            bad_f = True
        elif len(SM.states) != 2:
            bad_f = True
        # Init state MUST transit to second state. Second state MUST not have any transitions
        elif len(init_state.target_map.get_target_state_index_list()) != 1:
            bad_f = True
        else:
            tmp = set(SM.states.keys())
            tmp.remove(SM.init_state_index)
            other_state_index = tmp.__iter__().next()
            if len(SM.states[other_state_index].target_map.get_target_state_index_list()) != 0:
                bad_f = True

        if bad_f:
            error.log("For '%s' only patterns are addmissible which\n" % Keyword + \
                      "can be matched by a single character, e.g. \" \" or [a-z].", sr)

    check_can_be_matched_by_single_character(Pattern.sm)

    transition_map = Pattern.sm.get_init_state().target_map.get_map()
    assert len(transition_map) == 1
    return transition_map.values()[0]

_LineColumnCount_Default = None
def LineColumnCount_Default():
    global _LineColumnCount_Default

    if _LineColumnCount_Default is None:
        specifier = SpecifierCountActionMap()
        specifier.add(NumberSet(ord('\n')), "newline", 1, SourceRef_DEFAULT)
        specifier.add(NumberSet(ord('\t')), "grid",    4, SourceRef_DEFAULT)
        specifier.define_else("space",   1, SourceRef_DEFAULT)    # Define: "\else"
        count_command_map = specifier.finalize(
            Setup.buffer_codec.source_set.minimum(), 
            Setup.buffer_codec.source_set.supremum(),                     # Apply:  "\else"
            SourceRef_DEFAULT) 

        _LineColumnCount_Default = LineColumnCount(SourceRef_DEFAULT, 
                                                   count_command_map)

    return _LineColumnCount_Default

