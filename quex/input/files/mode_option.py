import quex.input.files.counter_setup     as     counter_setup
from   quex.input.files.counter_setup     import LineColumnCounterSetup_Default
import quex.input.regular_expression.core as     regular_expression
from   quex.engine.misc.file_in           import error_msg, \
                                                 get_current_line_info_number, \
                                                 skip_whitespace, \
                                                 read_identifier, \
                                                 verify_word_in_list
from   quex.engine.misc.file_in           import EndOfStreamException

from   quex.blackboard                    import SourceRef, mode_description_db

from   collections import namedtuple
import types

#-----------------------------------------------------------------------------------------
# mode_option_info_db: Information about properties of mode options.
#-----------------------------------------------------------------------------------------
class ModeOptionInfo:
    """A ModeOptionInfo is an element of mode_option_info_db."""
    def __init__(self, Type, Domain=None, Default=-1, UniqueF=False, Name=""):
        # self.name = Option see comment above
        self.type          = Type
        self.domain        = Domain
        self.default_value = Default
        self.name          = Name

def __get_mode_name_list():
    return mode_description_db.keys()

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
   "exit":              ModeOptionInfo("list", Default=__get_mode_name_list),
   "entry":             ModeOptionInfo("list", Default=__get_mode_name_list),
   # -- a mode can restrict the exits and entrys explicitly mentioned
   #    then, a derived mode cannot add now exits or entrys
   "restrict":          ModeOptionInfo("list", ["exit", "entry"], Default=[]),
   # -- a mode can have 'skippers' that effectivels skip ranges that are out of interest.
   "skip":              ModeOptionInfo("list", Default=[]), # "multiple: RE-character-set
   "skip_range":        ModeOptionInfo("list", Default=[]), # "multiple: RE-character-string RE-character-string
   "skip_nested_range": ModeOptionInfo("list", Default=[]), # "multiple: RE-character-string RE-character-string
   # -- indentation setup information
   "indentation":       ModeOptionInfo("single", Default=None, Name="indentation specification"),
   # --line/column counter information
   "counter":           ModeOptionInfo("single", Default=LineColumnCounterSetup_Default, Name="line and column count specification"),
}

OptionSetting = namedtuple("OptionSetting", ("value", "sr", "mode_name"))

class OptionDB(dict):
    def get(self, Key):         assert False # Not to be used.
    def __getitem__(self, Key): assert False # Not to be used
    def __setitem__(self, Key): assert False # Not to be used

    def enter(self, OptionName, Value, SourceReference, ModeName):
        """SANITY CHECK:
                -- which option_db are concatinated to a list
                -- which ones are replaced
                -- what are the values of the option_db
        """
        global mode_option_info_db

        # The 'verify_word_in_list()' call must have ensured that the following holds
        assert mode_option_info_db.has_key(OptionName)

        # Is the option of the appropriate value?
        option_info = mode_option_info_db[OptionName]

        if option_info.domain is not None and Value not in option_info.domain:
            error_msg("Tried to set value '%s' for option '%s'. " % (Value, OptionName) + \
                      "Though, possible for this option are only: %s." % repr(option_info.domain)[1:-1], fh)

        option_setting = OptionSetting(Value, SourceReference, ModeName)
        option_info    = mode_option_info_db[OptionName]
        if option_info.type == "list":
            dict.setdefault(self, OptionName, []).append(option_setting)
        elif OptionName not in self: 
            dict.__setitem__(self, OptionName, option_setting)
        else:
            self.__error_double_definition(OptionName, self[OptionName], option_setting)

    @classmethod
    def from_BaseModeSequence(cls, BaseModeSequence):
        # BaseModeSequence[-1] = mode itself
        mode_name = BaseModeSequence[-1].name

        result = cls()
        for mode_descr in BaseModeSequence:
            option_db = mode_descr.option_db
            for name, option_info in mode_option_info_db.iteritems():
                option_setting = dict.get(option_db, name)
                if option_setting is None: 
                    continue
                elif option_info.type == "list": 
                    # Need to decouple by means of 'deepcopy'
                    dict.setdefault(result, name, []).extend(deepcopy(x) for x in option_setting)
                elif name not in result: 
                    dict.__setitem__(result, name, option_setting)
                else:
                    result.__error_double_definition(name, result[name], option_setting)

        # Options which have not been set (or inherited) are set to the default value.
        for name, option_info in mode_option_info_db.iteritems():
            if name in result: continue
            if isinstance(option_info.default_value, types.FunctionType):
                value = option_info.default_value()
            else:
                value = option_info.default_value

            option_setting = OptionSetting(value, SourceRef("<default>", 0), mode_name)
            dict.__setitem__(result, name, option_setting)

        return result

    def value(self, Name):
        result = dict.get(self, Name)
        if result is None: return None
        return result.value

    def __error_double_definition(OptionName, OptionBefore, OptionNow):
        assert isinstance(OptionNow, OptionSetting)
        assert isinstance(OptionBefore, OptionSetting)
        txt = "Option '%s' defined twice in "
        if OptionBefore.mode_name == OptionNow.mode_name:
            txt += "mode '%s'." % OptionNow.mode_name
        else:
            txt += "inheritance tree of mode '%s'." % OptionNow.mode_name
        error_msg(txt, OptionNow.sr.file_name, OptionNow.sr.line_n, DontExitF=True, WarningF=False) 

        txt = "Previous definition was here"
        if OptionBefore.mode_name == OptionNow.mode_name:
            txt += " in mode '%s'." % OptionBefore.mode_name
        else:
            txt += "."
        error_msg(txt, OptionBefore.sr.file_name, OptionBefore.sr.line_n)

def parse(fh, new_mode):
    source_reference = SourceRef.from_FileHandle(fh)

    identifier = read_option_start(fh)
    if identifier is None: return False

    verify_word_in_list(identifier, mode_option_info_db.keys(),
                        "mode option", fh.name, get_current_line_info_number(fh))

    if   identifier == "skip":
        value = __parse_skip_option(fh, new_mode, identifier)

    elif identifier in ["skip_range", "skip_nested_range"]:
        value = __parse_range_skipper_option(fh, identifier, new_mode)
        
    elif identifier == "indentation":
        value = counter_setup.parse(fh, IndentationSetupF=True)
        value.set_containing_mode_name(new_mode.name)

    elif identifier == "counter":
        value = counter_setup.parse(fh, IndentationSetupF=False)

    else:
        value = read_option_value(fh)

    # Finally, set the option
    new_mode.option_db.enter(identifier, value, source_reference, new_mode.name)

    return True

def __parse_skip_option(fh, new_mode, identifier):
    """A skipper 'eats' characters at the beginning of a pattern that belong to
    a specified set of characters. A useful application is most probably the
    whitespace skipper '[ \t\n]'. The skipper definition allows quex to
    implement a very effective way to skip these regions."""

    pattern_str, pattern, trigger_set = regular_expression.parse_character_set(fh, ">")

    skip_whitespace(fh)

    if fh.read(1) != ">":
        error_msg("missing closing '>' for mode option '%s'." % identifier, fh)
    elif trigger_set.is_empty():
        error_msg("Empty trigger set for skipper." % identifier, fh)

    return pattern, trigger_set

def __parse_range_skipper_option(fh, identifier, new_mode):
    """A non-nesting skipper can contain a full fledged regular expression as opener,
    since it only effects the trigger. Not so the nested range skipper-see below.
    """

    # Range state machines only accept 'strings' not state machines
    skip_whitespace(fh)
    opener_str, opener_pattern, opener_sequence = regular_expression.parse_character_string(fh, ">")
    skip_whitespace(fh)
    closer_str, closer_pattern, closer_sequence = regular_expression.parse_character_string(fh, ">")

    # -- closer
    skip_whitespace(fh)
    if fh.read(1) != ">":
        error_msg("missing closing '>' for mode option '%s'" % identifier, fh)
    elif len(opener_sequence) == 0:
        error_msg("Empty sequence for opening delimiter.", fh)
    elif len(closer_sequence) == 0:
        error_msg("Empty sequence for closing delimiter.", fh)

    return (opener_str, opener_pattern, opener_sequence, \
            closer_str, closer_pattern, closer_sequence)

def read_option_start(fh):
    skip_whitespace(fh)

    # (*) base modes 
    if fh.read(1) != "<": 
        ##fh.seek(-1, 1) 
        return None

    skip_whitespace(fh)
    identifier = read_identifier(fh, OnMissingStr="Missing identifer after start of mode option '<'").strip()

    skip_whitespace(fh)
    if fh.read(1) != ":": error_msg("missing ':' after option name '%s'" % identifier, fh)
    skip_whitespace(fh)

    return identifier

def read_option_value(fh):

    position = fh.tell()

    value = ""
    depth = 1
    while 1 + 1 == 2:
        try: 
            letter = fh.read(1)
        except EndOfStreamException:
            fh.seek(position)
            error_msg("missing closing '>' for mode option.", fh)

        if letter == "<": 
            depth += 1
        if letter == ">": 
            depth -= 1
            if depth == 0: break
        value += letter

    return value.strip()

