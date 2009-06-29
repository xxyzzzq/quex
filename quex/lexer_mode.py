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
import sys
import os

from copy                import copy, deepcopy
from quex.frs_py.file_in import error_msg
from quex.core_engine.generator.action_info import *
import quex.core_engine.state_machine.subset_checker as subset_checker

# ModeDescription/Mode Objects:
#
# During parsing 'ModeDescription' objects are generated. Once parsing is over, 
# the descriptions are translated into 'real' mode objects where code can be generated
# from. All matters of inheritance and pattern resolution are handled in the
# transition from description to real mode.
#-----------------------------------------------------------------------------------------
# mode_description_db: storing the mode information into a dictionary:
#                      key  = mode name
#                      item = ModeDescription object
#-----------------------------------------------------------------------------------------
mode_description_db = {}

#-----------------------------------------------------------------------------------------
# mode_db: storing the mode information into a dictionary:
#            key  = mode name
#            item = Mode object
#-----------------------------------------------------------------------------------------
mode_description_db = {}

class OptionInfo:
    """This type is used only in context of a dictionary, the key
       to the dictionary is the option's name."""
    def __init__(self, Type, Domain=-1):
        # self.name = Option see comment above
        self.type   = Type
        if Type == "list" and Domain == -1: self.domain = []
        else:                               self.domain = Domain

class ModeDescription:
    def __init__(self, Name, Filename, LineN):
        global mode_description_db

        self.filename = Filename
        self.line_n   = LineN

        self.name       = Name
        self.base_modes = []
        # Read pattern information into dictionary object. This allows for the following:
        # (i)   inheritance of pattern behavior in different modes.
        # (ii)  'virtual' patterns in the sense that their behavior can be
        #       overwritten.
        self.__matches = {}  # genuine patterns as specified in the mode declaration

        self.__repriorization_db = {}  # patterns of the base class to be reprioritized
        #                              # map: pattern --> new pattern index
        self.__deletion_db       = {}  # patterns of the base class to be deleted

        # The list of actual pattern action pairs is constructed inside the function
        # '__post_process(...)'. Function 'get_pattern_action_pairs(...) calls it
        # in case that this variable is still [].
        self.__pattern_action_pair_list = []  

        # (*) set the information about possible options
        self.options = {}       # option settings
        self.options["inheritable"]        = "yes"
        self.options["exit"]               = []
        self.options["entry"]              = []
        self.options["restrict"]           = []
        self.options["skip"]               = []
        self.options["skip-range"]         = []
        self.options["skip-nesting-range"] = []

        self.events = {}
        self.events["on_entry"]         = CodeFragment()
        self.events["on_exit"]          = CodeFragment()
        self.events["on_match"]         = CodeFragment()
        self.events["on_failure"]       = CodeFragment()
        self.events["on_end_of_stream"] = CodeFragment()
        self.events["on_indentation"]   = CodeFragment()

        # A flag indicating wether the mode has gone trough
        # consistency check.
        self.consistency_check_done_f             = False
        self.inheritance_circularity_check_done_f = False

        # Register ModeDescription at the mode database
        mode_description_db[Name] = self

    def has_event_handler(self):
        for fragment in self.events.values():
            if fragment.get_code() != "": return True
        return False

    def has_pattern(self, PatternStr):
        return self.__matches.has_key(PatternStr)

    def get_match_object(self, PatternStr):
        return self.__matches[PatternStr]

    def has_matches(self):
        assert self.inheritance_circularity_check_done_f == True, \
               "called before consistency check!"

        if self.__matches != {}: return True

        for name in self.base_modes:
           if mode_description_db[name].has_matches(): return True

        return False

    def own_matches(self):
        return self.__matches

    def add_match(self, Pattern, Action, PatternStateMachine):
        if self.__matches.has_key(Pattern):
            error_msg("Pattern '%s' appeared twice in mode definition.\n" % Pattern + \
                      "Only the last definition is considered.", 
                      Action.filename, Action.line_n, DontExitF=True)

        self.__matches[Pattern] = PatternActionInfo(PatternStateMachine, Action, Pattern)

    def add_match_priority(self, Pattern, PatternStateMachine, PatternIdx, FileName, LineN):
        if self.__matches.has_key(Pattern):
            error_msg("Pattern '%s' appeared twice in mode definition.\n" % Pattern + \
                      "Only this priority mark is considered.", FileName, LineN)

        self.__repriorization_db[Pattern] = [PatternStateMachine, FileName, LineN, PatternIdx]

    def add_match_deletion(self, Pattern, PatternStateMachine, FileName, LineN):
        if self.__matches.has_key(Pattern):
            error_msg("Deletion of '%s' which appeared before in same mode.\n" % Pattern + \
                      "Deletion of pattern.", FileName, LineN)

        self.__deletion_db[Pattern] = [PatternStateMachine, FileName, LineN]

    def on_entry_code_fragments(self, Depth=0):
        """Collect all 'on_entry' event handlers from all base classes.
           Returns list of 'CodeFragment'.
        """
        return self.__collect_fragments("on_entry", Depth)

    def on_exit_code_fragments(self, Depth=0):
        """Collect all 'on_exit' event handlers from all base classes.
           Returns list of 'CodeFragment'.
        """
        return self.__collect_fragments("on_exit", Depth)

    def on_indentation_code_fragments(self, Depth=0):
        """Collect all 'on_indentation' event handlers from all base classes.
           Returns list of 'CodeFragment'.
        """
        return self.__collect_fragments("on_indentation", Depth)

    def on_match_code_fragments(self, Depth=0):
        """Collect all 'on_match' event handlers from all base classes.
           Returns list of 'CodeFragment'.
        """
        return self.__collect_fragments("on_match", Depth)

    def on_end_of_stream_code_fragments(self, Depth=0):
        """Collect all 'on_end_of_stream' event handlers from all base classes.
           Returns list of 'CodeFragment'.
        """
        return self.__collect_fragments("on_end_of_stream", Depth)

    def on_failure_code_fragments(self, Depth=0):
        """Collect all 'on_failure' event handlers from all base classes.
           Returns list of 'CodeFragment'.
        """
        return self.__collect_fragments("on_failure", Depth)

    def __collect_fragments(self, FragmentName, Depth=0):
        """Collect all event handlers with the given FragmentName from all base classes.
           Returns list of 'CodeFragment'.
        """
        fragment = self.events[FragmentName]
        if fragment == None or fragment.get_code() == "":
            code_fragment_list = []
        else:      
            assert isinstance(fragment, CodeFragment)
            code_fragment_list = [ fragment ]

        for base_mode_name in self.base_modes:
            # -- get 'on_match' handler from the base mode
            base_mode     = mode_description_db[base_mode_name]
            base_fragment_list = { 
                    "on_entry":          base_mode.on_entry_code_fragments,
                    "on_exit":           base_mode.on_exit_code_fragments,
                    "on_indentation":    base_mode.on_indentation_code_fragments,
                    "on_match":          base_mode.on_match_code_fragments,
                    "on_end_of_stream":  base_mode.on_end_of_stream_code_fragments,
                    "on_failure":        base_mode.on_failure_code_fragments,
                    }[FragmentName](Depth+1)
            code_fragment_list.extend(base_fragment_list)

        # reverse the order, so that the lowest base class appears first
        if Depth==0: code_fragment_list.reverse()

        return code_fragment_list

    def get_pattern_action_pairs(self, Depth=0):
        if self.__pattern_action_pair_list == []:
            self.__pattern_action_pair_list = self.__post_process(Depth)
        return self.__pattern_action_pair_list

    def __post_process(self, Depth=0):
        """Collect patterns of all inherited modes. Patterns are like virtual functions
           in C++ or other object oriented programming languages. Also, the patterns of the
           uppest mode has the highest priority, i.e. comes first.
        """
        def __collect_patterns_from_base_modes():
            result         = []
            max_pattern_id = -1
            for base_mode_name in self.base_modes:

                base_pattern_action_pairs = mode_description_db[base_mode_name].get_pattern_action_pairs(Depth + 1)
                result.extend(base_pattern_action_pairs)

                for match in base_pattern_action_pairs:
                    pattern_id = match.pattern_state_machine().get_id()
                    if pattern_id > max_pattern_id: max_pattern_id = pattern_id

            return result, max_pattern_id
                
        def __current_min_pattern_index():
            return  min(map(lambda match: match.pattern_state_machine().get_id(),
                            self.__matches.values()))

        def __reset_pattern_indices(MinRequiredIndex, CurrentMinIndex):
            """When a derived mode is defined before its base mode, then its pattern ids
               (according to the time they were created) are lower than thos of the base
               mode. This would imply that they have higher precedence, which is against
               our matching rules. Here, pattern ids are adapted to be higher than a certain
               minimum, and follow the same precedence sequence.
            """
            # Determine the offset for each pattern
            offset = MinRequiredIndex - CurrentMinIndex

            # Assign new pattern ids starting from MinPatternID
            for match in self.__matches.values():
                current_pattern_id = match.pattern_state_machine().get_id()
                match.pattern_state_machine().core().set_id(current_pattern_id + offset)

            # The reprioritizations must also be adapted
            for info in self.__repriorization_db.values():
                info[1] += offset
                                             
        def __validate_marks(DB, DoneDB, CommentStr):
            ok_f = True
            for pattern, info in DB.items():
                if DoneDB.has_key(pattern): continue
                ok_f = False
                error_msg("Pattern '%s' was marked %s but does not\n" % (pattern, CommentStr) + \
                          "exist in any base mode of mode '%s'." % self.name,
                          info[1], info[2], DontExitF=True, WarningF=False)
            return ok_f

        def __is_sub_pattern(AllegedSubSM, MyDB):
            for pattern, info in MyDB.items():
                sm = info[0]
                if subset_checker.do(sm, AllegedSubSM) == True: return pattern
            return ""

        inherited_list, inherited_max_pattern_index = __collect_patterns_from_base_modes()

        # (*) Patterns of base modes have precedence over inherited modes, thus, if
        #     one of our patterns has a lower id than one of the base mode patterns,
        #     all of our pattern ids need to be adapted.
        if len(self.__matches) != 0:
            min_index = __current_min_pattern_index()
            if min_index < inherited_max_pattern_index:
                __reset_pattern_indices(inherited_max_pattern_index + 1, min_index)
                
        # (*) Add own patterns to the list of pattern action pairs (result)
        result = []
        own_state_machine_list = []
        for match in self.__matches.values():
            tmp = copy(match)
            tmp.inheritance_level     = Depth
            tmp.inheritance_mode_name = self.name
            result.append(tmp)
            own_state_machine_list.append(match.pattern_state_machine())

        # (*) Loop over inherited patterns 
        #     -- add
        #     -- delete according to DELETION marks
        #     -- reprioritize according to PRIORITY-MARK
        #
        repriorization_done_db = {}
        deletion_done_db       = {}
        for match in inherited_list:
            pattern_state_machine = match.pattern_state_machine()

            found_pattern = __is_sub_pattern(pattern_state_machine, self.__deletion_db)
            if found_pattern != "":
                # Deletion = not mentioning it in the list of resolved patterns
                deletion_done_db[found_pattern] = True
                continue

            found_pattern = __is_sub_pattern(pattern_state_machine, self.__repriorization_db)
            if found_pattern != "":
                # Adapt the pattern index, this automatically adapts the match precedence
                new_state_machine_id = self.__repriorization_db[found_pattern][-1]
                tmp = deepcopy(match)
                tmp.pattern_state_machine().core().set_id(new_state_machine_id)
                tmp.inheritance_level     = Depth
                tmp.inheritance_mode_name = self.name
                result.append(tmp)
                repriorization_done_db[found_pattern] = True
                continue

            result.append(match)

        # (*) Ensure that all mentioned marks really had some effect.
        if    not __validate_marks(self.__deletion_db, deletion_done_db, "for DELETION")  \
           or not __validate_marks(self.__repriorization_db, repriorization_done_db, "with PRIORITY-MARK"):
            error_msg("Process of lexical analyzer generation aborted due to inacceptable user input.")

        return result

    def inheritance_structure_string(self, Depth=0):
        """NOTE: The consistency check ensures that all base modes are
                 defined and inheritable and there is no circular inheritance !
                 Therefore there is no need to check if the base mode
                 has an entry in the mode database."""
        assert self.consistency_check_done_f == True, \
               "called before consistency check!"

        if Depth != 0: str = "** " + ("   " * Depth) + self.name + "\n"
        else:          str = "** <" + self.name + ">\n"
        for base_mode_name in self.base_modes:
            mode = mode_description_db[base_mode_name]
            str += mode.inheritance_structure_string(Depth + 1)
        return str

    def get_base_modes(self):
        """Get all base classes recursively.
           NOTE: Circularity check needs to happen somewhere else
           This function is part of the consistency check!
        """
        assert self.inheritance_circularity_check_done_f == True, \
               "called before consistency check!"

        base_mode_collection = copy(self.base_modes)
        for base_mode in self.base_modes:
            # -- append base_mode to the base modes of current mode
            base_mode_collection_candidates = mode_description_db[base_mode].get_base_modes()
            for candidate in base_mode_collection_candidates:
                if candidate not in base_mode_collection:
                    base_mode_collection.append(candidate)

        return base_mode_collection

    def add_option(self, Option, Value):
        """ SANITY CHECK:
                -- which options are concatinated to a list
                -- which ones are replaced
                -- what are the values of the options
        """
        assert mode_option_info_db.has_key(Option)

        oi = mode_option_info_db[Option]
        if oi.type == "list":
            # append the value, assume in lists everything is allowed
            if self.options.has_key(Option): self.options[Option].append(Value)
            else:                            self.options[Option] = [ Value ]
        else:
            assert Value in oi.domain
            self.options[Option] = Value

    def consistency_check(self):
        """Checks for the following:

        -- existence of mentioned base modes
        -- circularity of inheritance
        -- outruled patterns in mode (TODO)
        -- existence of enter and exit modes
        -- checks that if X has an exit to Y,
           then Y must have an entry to X

        Any failure causes an immediate break up.
        """

        # (*) Base Modes
        #
        #   -- ability to inherit
        #
        #   NOTE: existence of modes is checked in ciruclarity test.
        #
        for base_mode_name in self.base_modes:
            # -- is base mode inheritable?
            if mode_description_db[base_mode_name].options["inheritable"] == "no":
                error_msg("mode '%s' inherits mode '%s' which is **not inheritable**." % \
                          (self.name, base_mode_name), self.filename, self.line_n)

        # -- require all bases modes
        all_base_modes = self.get_base_modes()

        # (*) A mode that does not force to be inherited needs finally contain matches.
        #     A mode that contains only event handlers is not <inheritable: only>, but
        #     somehow, it needs some matches in the base classes, otherwise it cannot
        #     act as a pattern state machine.
        if self.options["inheritable"] != "only" and self.has_matches() == False:
            error_msg("Mode '%s' was defined without the option <inheritable: only>.\n" % self.name + \
                      "However, it contains no matches--only event handlers. Without pattern\n"     + \
                      "matches it cannot act as a pattern detecting state machine, and thus\n"      + \
                      "cannot be an independent lexical analyzer mode. Define the option\n"         + \
                      "<inheritable: only>.", \
                      self.filename, self.line_n)

        # (*) Enter/Exit Transitions
        for mode_name in self.options["exit"]:
            # -- does other mode exist?
            if mode_description_db.has_key(mode_name) == False:
                error_msg("Mode '%s'\nhas  an exit to mode '%s'\nbut no such mode exists." % \
                          (self.name, mode_name), self.filename, self.line_n)

            # -- does other mode have an entry for this mode?
            #    (does this or any of the base modes have an entry to the other mode?)
            other_mode = mode_description_db[mode_name]
            #    -- no restrictions => OK
            if other_mode.options["entry"] == []: continue
            #    -- restricted entry => check if this mode ore one of the base modes can enter
            for base_mode in [self.name] + all_base_modes:
                if base_mode in other_mode.options["entry"]: break
            else:
                error_msg("Mode '%s'\nhas an exit to mode '%s'," % (self.name, mode_name),
                          self.filename, self.line_n, DontExitF=True, WarningF=False)
                error_msg("but mode '%s'\nhas no entry for mode '%s'.\n" % (mode_name, self.name) + \
                          "or any of its base modes.",
                          other_mode.filename, other_mode.line_n)

        for mode_name in self.options["entry"]:
            # -- does other mode exist?
            if mode_description_db.has_key(mode_name) == False:
                error_msg("Mode '%s'\nhas an entry from mode '%s'\nbut no such mode exists." % \
                          (self.name, mode_name),
                          self.filename, self.line_n)

            # -- does other mode have an exit for this mode?
            #    (does this or any of the base modes have an exit to the other mode?)
            other_mode = mode_description_db[mode_name]
            #    -- no restrictions => OK
            if other_mode.options["exit"] == []: continue
            #    -- restricted exit => check if this mode ore one of the base modes can enter
            for base_mode in [self.name] + all_base_modes:
                if base_mode in other_mode.options["exit"]: break
            else:
                error_msg("Mode '%s'\nhas an entry for mode '%s'" % (self.name, mode_name),
                          self.filename, self.line_n, DontExitF=True, WarningF=False)
                error_msg("but mode '%s'\nhas no exit to mode '%s'\n" % (mode_name, self.name) + \
                          "or any of its base modes.",
                          other_mode.filename, other_mode.line_n)
                
        # (*) Check for outruled patterns inside the mode, i.e. patterns that can never match
        match_list = self.get_pattern_action_pairs()
        match_list.sort(lambda x, y: cmp(x.pattern_state_machine().get_id(),
                                         y.pattern_state_machine().get_id()))
        # A pattern with a lower precedence (i.e. higher pattern index) shall never 
        # match only a subset of a pattern with a higher precedence.
        L = len(match_list)
        for i in range(L-1):
            higher_precedence_pattern    = match_list[i].pattern
            higher_precedence_pattern_sm = match_list[i].pattern_state_machine()
            for k in range(i+1, L):
                lower_precedence_pattern    = match_list[k].pattern
                lower_precedence_pattern_sm = match_list[k].pattern_state_machine()
                if subset_checker.do(higher_precedence_pattern_sm, lower_precedence_pattern_sm):
                    print "##i",  match_list[i].pattern_state_machine().get_id()
                    print "##k",  match_list[k].pattern_state_machine().get_id()
                    error_msg("Pattern '%s' matches a superset of what is matched by" % 
                              higher_precedence_pattern, 
                              match_list[i].action().filename, 
                              match_list[i].action().line_n,  
                              DontExitF=True, WarningF=False) 
                    error_msg("pattern '%s' while the former has precedence.\n" % \
                              lower_precedence_pattern + "The latter can never match.\n" + \
                              "You may switch the sequence of definition to avoid this error.",
                              match_list[k].action().filename, 
                              match_list[k].action().line_n)

        self.consistency_check_done_f = True


class Mode(ModeDescription):
    def __init__(self, Other):
        """Translate a ModeDescription into a real Mode. Here is the place were 
           all rules of inheritance mechanisms and pattern precedence are applied.
        """
        assert isinstance(Other, ModeDescription)
        #for name, member in Other.__dict__.items():
        #    self.__dict__[name] = member
        self.base_mode_sequence = Other.get_base_modes()

        # (1) Collect Event Handlers
        for name in ["on_entry", "on_exit", "on_indentation", "on_match", "on_end_of_stream",  "on_failure"]:
            self.__collect_event_handlers(name)

    def has_indentation_based_event(self):
        return self.events["on_indentation"].get_code() != ""

    def __collect_event_handlers(self, Event):

#-----------------------------------------------------------------------------------------
# mode option information/format: 
#-----------------------------------------------------------------------------------------
mode_option_info_db = {
   # -- a mode can be inheritable or not or only inheritable. if a mode
   #    is only inheritable it is not printed on its on, only as a base
   #    mode for another mode. default is 'yes'
   "inheritable":       OptionInfo("single", ["no", "yes", "only"]),
   # -- a mode can restrict the possible modes to exit to. this for the
   #    sake of clarity. if no exit is explicitly mentioned all modes are
   #    possible. if it is tried to transit to a mode which is not in
   #    the list of explicitly stated exits, an error occurs.
   #    entrys work respectively.
   "exit":              OptionInfo("list"),
   "entry":             OptionInfo("list"),
   # -- a mode can restrict the exits and entrys explicitly mentioned
   #    then, a derived mode cannot add now exits or entrys
   "restrict":          OptionInfo("list", ["exit", "entry"]),
   # -- a mode can have 'skippers' that effectivels skip ranges that are out of interest.
   "skip":              OptionInfo("list"), # "multiple: RE-character-set
   "skip_range":        OptionInfo("list"), # "multiple: RE-character-string RE-character-string
   "skip_nested_range": OptionInfo("list"), # "multiple: RE-character-string RE-character-string
}

#-----------------------------------------------------------------------------------------
# initial_mode: mode in which the lexcial analyser shall start
#-----------------------------------------------------------------------------------------
initial_mode = CodeFragment()

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

class PatternShorthand:
    def __init__(self, Name="", StateMachine="", Filename="", LineN=-1, RE=""):
        assert StateMachine.has_origins() == False
        assert StateMachine.__class__.__name__ == "StateMachine"

        self.name               = Name
        self.state_machine      = StateMachine
        self.filename           = Filename
        self.line_n             = LineN
        self.regular_expression = RE

#-----------------------------------------------------------------------------------------
# shorthand_db: user defined names for regular expressions.
#               (this is what contained in the pattern file for flex-based engines.
#                it is only used with quex generated engines)   
#-----------------------------------------------------------------------------------------
shorthand_db = {}

#-----------------------------------------------------------------------------------------
# token_id_db: list of all defined token-ids together with the file position
#              where they are defined. See token_ide_maker, class TokenInfo.
#-----------------------------------------------------------------------------------------
token_id_db = {}

#-----------------------------------------------------------------------------------------
# token_type_definition: Object that defines a (user defined) token class.
#-----------------------------------------------------------------------------------------
token_type_definition = None

def get_token_class_file_name(Setup):
    file_name = Setup.token_class_file
    if token_type_definition != None:
        file_name = token_type_definition.get_file_name()
        if file_name == "":
            file_name = Setup.output_engine_name + "-token-class"

    return file_name

