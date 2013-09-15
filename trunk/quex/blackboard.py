################################################################################
#! /usr/bin/env python
# Quex is  free software;  you can  redistribute it and/or  modify it  under the
# terms  of the  GNU Lesser  General  Public License  as published  by the  Free
# Software Foundation;  either version 2.1 of  the License, or  (at your option)
# any later version.
# 
# This software is  distributed in the hope that it will  be useful, but WITHOUT
# ANY WARRANTY; without even the  implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the  GNU Lesser General Public License for more
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along
# with this  library; if not,  write to the  Free Software Foundation,  Inc., 59
# Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# (C) 2006, 2007 Frank-Rene Schaefer
#
################################################################################

################################################################################
# IMPORTANT: This file shall be import-able by any 'normal' module of Quex.    #
#            For this, it was a designated design goal to make sure that the   #
#            imports are 'flat' and only cause environment or outer modules.   #
################################################################################
from quex.engine.generator.code_fragment_base import CodeFragment
from quex.engine.misc.enum                    import Enum
from quex.input.setup                         import QuexSetup, SETUP_INFO
from copy                                     import deepcopy

#-----------------------------------------------------------------------------------------
# setup: All information of the user's desired setup.
#-----------------------------------------------------------------------------------------
setup = QuexSetup(SETUP_INFO)

#-----------------------------------------------------------------------------------------
# StateIndices: Values to be used as target states for transitions
#-----------------------------------------------------------------------------------------
E_StateIndices = Enum("DROP_OUT", 
                      "RELOAD_FORWARD",
                      "RELOAD_BACKWARD",
                      "END_OF_PRE_CONTEXT_CHECK",
                      "RECURSIVE",
                      "ALL", 
                      "ANALYZER_REENTRY", 
                      "NONE", 
                      "VOID") 

E_PreContextIDs  = Enum("NONE",    
                        "BEGIN_OF_LINE", 
                        "_DEBUG_NAME_PreContextIDs")

E_AcceptanceIDs  = Enum("FAILURE", 
                        "PRE_CONTEXT_FULFILLED", 
                        "TERMINAL_PRE_CONTEXT_CHECK", 
                        "TERMINAL_BACKWARD_INPUT_POSITION", 
                        "VOID", 
                        "_DEBUG_NAME_E_AcceptanceIDs")

E_PostContextIDs = Enum("NONE", 
                        "IRRELEVANT",
                        "_DEBUG_NAME_E_PostContextIDs")

E_TransitionN = Enum("VOID", 
                     "LEXEME_START_PLUS_ONE",
                     "IRRELEVANT",
                     "_DEBUG_NAME_TransitionNs")

E_TriggerIDs = Enum("NONE", 
                    "_DEBUG_NAME_TriggerIDs")

E_InputActions = Enum("DEREF", 
                      "INCREMENT", 
                      "INCREMENT_THEN_DEREF", 
                      "DECREMENT",
                      "DECREMENT_THEN_DEREF",
                      "_DEBUG_InputActions")

E_Compression = Enum("PATH", 
                     "PATH_UNIFORM",
                     "TEMPLATE",
                     "TEMPLATE_UNIFORM",
                     "_DEBUG_Compression")

E_Count = Enum("VIRGIN", 
               "VOID",
               "NONE",
               "_DEBUG_Count")

E_Commonality = Enum("NONE", "BOTH", "A_IN_B", "B_IN_A")

E_SpecialPatterns = Enum("INDENTATION_NEWLINE", 
                         "SUPPRESSED_INDENTATION_NEWLINE",
                         "SKIP", 
                         "SKIP_RANGE", 
                         "SKIP_NESTED_RANGE", 
                         "_DEBUG_PatternNames")

E_ActionIDs = Enum( # Keep them sorted alphabetically!
               "ON_AFTER_MATCH",        
               "ON_END_OF_STREAM", 
               "ON_EXIT",
               "ON_FAILURE", 
               "ON_GOOD_TRANSITION",
               "ON_MATCH", 
               "_DEBUG_ActionIDs")

E_MapImplementationType = Enum("STATE_MACHINE_TRIVIAL", 
                               "STATE_MACHINE",
                               "PLAIN_MAP", 
                               "_DEBUG_MapImplementationType")

E_Border = Enum("BEGIN", "END", "UNDEFINED", "_DEBUG_Border")

E_Values = Enum("UNASSIGNED", "VOID", "_DEBUG_E_Values")

E_DoorIdIndex = Enum("DROP_OUT", 
                     "TRANSITION_BLOCK", 
                     "ACCEPTANCE", 
                     "STATE_MACHINE_ENTRY", 
                     "EMPTY", 
                     "BIPD_RETURN", 
                     "GLOBAL_STATE_ROUTER", 
                     "GLOBAL_END_OF_PRE_CONTEXT_CHECK", 
                     "GLOBAL_TERMINAL_ROUTER", 
                     "GLOBAL_TERMINAL_END_OF_FILE", 
                     "GLOBAL_TERMINAL_FAILURE",
                     "GLOBAL_REENTRY",
                     "GLOBAL_REENTRY_PREPARATION",
                     "GLOBAL_REENTRY_PREPARATION_2",
                     "_DEBUG_DoorIdIndex") 

E_Commands = Enum("Accepter",
                  "StoreInputPosition",
                  "PreConditionOK",
                  "TemplateStateKeySet",
                  "PathIteratorSet",
                  "PrepareAfterReload",
                  "PrepareAfterReload_InitState",
                  "InputPIncrement",
                  "InputPDecrement",
                  "InputPDereference",
                  "_DEBUG_Commands")

#-----------------------------------------------------------------------------------------
# mode_db: storing the mode information into a dictionary:
#            key  = mode name
#            item = Mode object
#-----------------------------------------------------------------------------------------
mode_db = {}


#-----------------------------------------------------------------------------------------
# initial_mode: mode in which the lexcial analyser shall start
#-----------------------------------------------------------------------------------------
initial_mode = None

#-----------------------------------------------------------------------------------------
# mode_option_info_db: Information about properties of mode options.
#-----------------------------------------------------------------------------------------
class ModeOptionInfo:
    """This type is used only in context of a dictionary, the key
       to the dictionary is the option's name."""
    def __init__(self, Type, Domain=None, Default=-1):
        # self.name = Option see comment above
        self.type          = Type
        self.domain        = Domain
        self.default_value = Default

mode_option_info_db = {
   # -- a mode can be inheritable or not or only inheritable. if a mode
   #    is only inheritable it is not printed on its on, only as a base
   #    mode for another mode. default is 'yes'
   "inheritable":       ModeOptionInfo("single", ["no", "yes", "only"], Default="yes"),
   # -- a mode can restrict the possible modes to exit to. this for the
   #    sake of clarity. if no exit is explicitly mentioned all modes are
   #    possible. if it is tried to transit to a mode which is not in
   #    the list of explicitly stated exits, an error occurs.
   #    entrys work respectively.
   "exit":              ModeOptionInfo("list", Default=[]),
   "entry":             ModeOptionInfo("list", Default=[]),
   # -- a mode can restrict the exits and entrys explicitly mentioned
   #    then, a derived mode cannot add now exits or entrys
   "restrict":          ModeOptionInfo("list", ["exit", "entry"], Default=[]),
   # -- a mode can have 'skippers' that effectivels skip ranges that are out of interest.
   "skip":              ModeOptionInfo("list", Default=[]), # "multiple: RE-character-set
   "skip_range":        ModeOptionInfo("list", Default=[]), # "multiple: RE-character-string RE-character-string
   "skip_nested_range": ModeOptionInfo("list", Default=[]), # "multiple: RE-character-string RE-character-string
   # -- indentation setup information
   "indentation":       ModeOptionInfo("single", Default=None),
   # --line/column counter information
   "counter":           ModeOptionInfo("single", Default=None),
}

#-----------------------------------------------------------------------------------------
# event_handler_db: Stores names of event handler functions as keys and their meaning
#                   as their associated values.
#-----------------------------------------------------------------------------------------
event_handler_db = {
    "on_entry":                  "On entry of a mode.",
    "on_exit":                   "On exit of a mode.", 
    "on_indent":                 "On opening indentation.",
    "on_nodent":                 "On same indentation.",
    "on_dedent":                 "On closing indentation'.",
    "on_n_dedent":               "On closing indentation'.",
    "on_indentation_error":      "Closing indentation on non-border.",
    "on_indentation_bad":        "On bad character in indentation.",
    "on_indentation":            "General Indentation Handler.",
    "on_match":                  "On each match (before pattern action).",
#   TODO        "on_token_stamp":            "On event of token stamping.",
#   instead of: QUEX_ACTION_TOKEN_STAMP 
    "on_after_match":            "On each match (after pattern action).",
    "on_failure":                "In case that no pattern matches.",
    "on_skip_range_open":        "On missing skip range delimiter.",
    "on_end_of_stream":          "On end of file/stream.",
}

#-----------------------------------------------------------------------------------------
# header: code fragment that is to be pasted before mode transitions
#         and pattern action pairs (e.g. '#include<something>'
#-----------------------------------------------------------------------------------------
header = CodeFragment()

#-----------------------------------------------------------------------------------------
# class_body_extension: code fragment that is to be pasted inside the class definition
#                       of the lexical analyser class.
#-----------------------------------------------------------------------------------------
class_body_extension = CodeFragment()

#-----------------------------------------------------------------------------------------
# class_constructor_extension: code fragment that is to be pasted inside the lexer class constructor
#-----------------------------------------------------------------------------------------
class_constructor_extension = CodeFragment()

#-----------------------------------------------------------------------------------------
# memento_extension: fragment to be pasted into the memento  class's body.
#-----------------------------------------------------------------------------------------
memento_class_extension = CodeFragment()
#-----------------------------------------------------------------------------------------
# memento_pack_extension: fragment to be pasted into the function that packs the
#                         lexical analyzer state in a memento.
#-----------------------------------------------------------------------------------------
memento_pack_extension = CodeFragment()
#-----------------------------------------------------------------------------------------
# memento_unpack_extension: fragment to be pasted into the function that unpacks the
#                           lexical analyzer state in a memento.
#-----------------------------------------------------------------------------------------
memento_unpack_extension = CodeFragment()

fragment_db = {
        "header":         "header",
        "body":           "class_body_extension",
        "init":           "class_constructor_extension",
        "memento":        "memento_class_extension",
        "memento_pack":   "memento_pack_extension",
        "memento_unpack": "memento_unpack_extension",
}

all_section_title_list = ["start", "define", "token", "mode", "repeated_token", "token_type" ] + fragment_db.keys()

class PatternShorthand:
    def __init__(self, Name="", StateMachine="", Filename="", LineN=-1, RE=""):
        assert StateMachine.__class__.__name__ == "StateMachine"

        self.name               = Name
        self.__state_machine    = StateMachine
        self.filename           = Filename
        self.line_n             = LineN
        self.regular_expression = RE

    def get_state_machine(self):
        return self.__state_machine.clone()

    def get_character_set(self):
        if len(self.__state_machine.states) != 2: return None
        t  = self.__state_machine.states[self.__state_machine.init_state_index].target_map
        db = t.get_map()
        if len(db) != 1: return None
        return deepcopy(db[db.keys()[0]])

#-----------------------------------------------------------------------------------------
# shorthand_db: user defined names for regular expressions.
#-----------------------------------------------------------------------------------------
shorthand_db = {}

#-----------------------------------------------------------------------------------------
# token_id_db: list of all defined token-ids together with the file position
#              where they are defined. See token_ide_maker, class TokenInfo.
#-----------------------------------------------------------------------------------------
token_id_db = {}
def get_used_token_id_set():
    return [ token.number for token in token_id_db.itervalues() if token.number is not None ]

#-----------------------------------------------------------------------------------------
# token_id_foreign_set: Set of token ids which came from an external token id file.
#                       All tokens which are not defined in an external token id file
#                       are defined by quex.
#-----------------------------------------------------------------------------------------
token_id_foreign_set = set()

#-----------------------------------------------------------------------------------------
# token_id_implicit_list: Keep track of all token identifiers that ware defined 
#                         implicitly, i.e. not in a token section or in a token id file. 
#                         Each list element has three cells:
#                         [ Prefix-less Token ID, Line number in File, File Name]
#-----------------------------------------------------------------------------------------
token_id_implicit_list = []

#-----------------------------------------------------------------------------------------
# token_repetition_support: Quex can be told to return multiple times the same
#                           token before further analyzsis happens. For this,
#                           the engine needs to know how to read and write the
#                           repetition number in the token itself.
# If the 'token_repetition_token_id_list' is None, then the token repetition feature
# is disabled. Otherwise, token repetition in 'token-receiving.i' is enabled
# and the token id that can be repeated is 'token_repetition_token_id'.
#-----------------------------------------------------------------------------------------
token_repetition_token_id_list = ""

#-----------------------------------------------------------------------------------------
# token_type_definition: Object that defines a (user defined) token class.
#
#                        The first token_type section defines the variable as 
#                        a real 'TokenTypeDescriptor'.
#
#                        Default = None is detected by the 'input/file/core.py' and
#                        triggers the parsing of the default token type description. 
#          
#                        The setup_parser.py checks for the specification of a manually
#                        written token class file. If so then an object of type 
#                        'ManualTokenClassSetup' is assigned.
#-----------------------------------------------------------------------------------------
token_type_definition = None

#-----------------------------------------------------------------------------------------
# Helper functions about required features.
#-----------------------------------------------------------------------------------------
def requires_indentation_count(ModeDB):
    """Determine whether the lexical analyser needs indentation counting
       support. if one mode has an indentation handler, than indentation
       support must be provided.                                         
    """
    for mode in ModeDB.itervalues():
        if    mode.has_code_fragment_list("on_indent")      \
           or mode.has_code_fragment_list("on_nodent")      \
           or mode.has_code_fragment_list("on_indentation") \
           or mode.has_code_fragment_list("on_dedent"):
            return True

        if mode.options["indentation"] is not None:
            assert mode.options["indentation"].__class__.__name__ == "IndentationSetup"
            return True

    return False

def requires_begin_of_line_condition_support(ModeDB):
    """If one single pattern in one mode depends on begin of line, then
       the begin of line condition must be supported. Otherwise not.
    """
    for mode in ModeDB.values():
        pattern_action_pair_list = mode.get_pattern_action_pair_list()
        for info in pattern_action_pair_list:
            if info.pattern().pre_context_trivial_begin_of_line_f:
                return True
    return False

def deprecated(*Args):
    """This function is solely to be used as setter/getter property, 
       of member variables that are deprecated. This way misuse
       can be detected. Example usage:

       class X(object):  # Class must be derived from 'object'
           ...
           my_old = property(deprecated, deprecated, "Alarm on 'my_old'")
    """
    assert False

class DefaultCounterFunctionDB:
    """Default counters may be used in several modes. This database
    keeps track of implementations. If an implementation is done for
    one mode, another mode may refer it it.
    """
    __db = []
    @staticmethod
    def get_function_name(CounterDB):
        """Returns name of function which already implemented the 'CounterDB'.
        Otherwise, it returns 'None' if no such function exists.
        """
        for counter_db, function_name in DefaultCounterFunctionDB.__db:
            if   counter_db.special != CounterDB.special: continue
            elif counter_db.newline != CounterDB.newline: continue
            elif counter_db.grid    != CounterDB.grid:    continue
            return function_name
        return None

    @staticmethod
    def function_name_iterable():
        for counter_db, function_name in DefaultCounterFunctionDB.__db:
            yield function_name


    @staticmethod
    def enter(CounterDB, FunctionName):
        for function_name in DefaultCounterFunctionDB.function_name_iterable():
            assert function_name != FunctionName
        DefaultCounterFunctionDB.__db.append((CounterDB, FunctionName))

    @staticmethod
    def clear():
        del DefaultCounterFunctionDB.__db[:]
 

