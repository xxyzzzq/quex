
from quex.frs_py.file_in import get_current_line_info_number, \
                                error_msg, \
                                check, \
                                skip_whitespace, \
                                read_identifier, \
                                verify_word_in_list, \
                                parse_assignment, \
                                read_until_whitespace

from   quex.lexer_mode                    import LocalizedParameter
from   quex.core_engine.interval_handling import NumberSet
import quex.input.regular_expression      as regular_expression

class IndentationSetup:
    def __init__(self, fh):
        self.file_name = fh.name
        self.line_n    = get_current_line_info_number(fh)

        self.count_db         = {}
        self.character_set_db = {}

    def seal(self):
        if not self.count_db.has_key("space"):             self.specify_count("space", 1)
        if not self.count_db.has_key("tabulator"):         self.specify_count("tabulator", -4)
        if not self.character_set_db.has_key("space"):     self.specify_character_set("space",     NumberSet(ord(" ")))
        if not self.character_set_db.has_key("tabulator"): self.specify_character_set("tabulator", NumberSet(ord("\t")))

    def __error_msg_if_defined_twice(self, db, Name, FH):
        before = db.get(Name)
        if before == None: return
        error_msg(before.name + " has been defined before", FH, DontExitF=True, WarningF=False)
        error_msg("at this place.", before.file_name, before.line_n)

    def specify_space(self, CharSet, Count, FH=-1):
        pass

    def specify_grid(self, CharSet, Count, FH=-1):
        pass

    def specify_newline(self, CharSet, Count, FH=-1):
        pass

    def specify_suppressor(self, CharSet, Count, FH=-1):
        pass

    def specify_space(self, Name, Setting, FH=-1):
        self.__error_msg_if_defined_twice(self.count_db, Name, FH)
        self.count_db[Name] = LocalizedParameter("indentation count '%s'" % Name, Setting, FH)

    def specify_character_set(self, Name, Setting, FH=-1):
        self.__error_msg_if_defined_twice(self.character_set_db, Name, FH)

        # A character cannot appear in more than one set
        for name, character_set in self.character_set_db.items():
            if character_set.get().has_intersection(Setting):
                error_msg("Character set for '%s' intersects with" % Name, FH, DontExitF=True, WarningF=False)
                error_msg("character set for '%s'.\n" % name + \
                          "However, character sets must be mutually exclusive.", 
                          character_set.file_name,
                          character_set.line_n)

        if Setting.contains(ord("\n")):
            error_msg("Character set for indentation cannot contain newline.", FH)

        self.character_set_db[Name] = LocalizedParameter("indentation character set '%s'" % Name, Setting, FH)

    def has_grid(self):
        """A 'grid' is defined by a negative integer."""
        for count in self.count_db.values():
            if count.get() != "bad" and count.get() < 0: return True
        return False

    def has_spaces(self):
        for count in self.count_db.values():
            if count.get() != "bad" and count.get() >= 0: return True
        return False


    def has_only_single_spaces(self):
        if len(self.count_db): return False
        for count in self.count_db.values():
            if count.get() not in [1, -1]: return False
        return True

    def __character_info(self, FilterFunc):
        """Returns a list of character sets paired with their count information.
        """
        result = []
        for identifier, count in self.count_db.items():
            # Consider only what user wants
            if count.get() == "bad" or not FilterFunc(count): continue 
            
            # The consistency check must have ensured that every key in
            # 'character_set_db' is als in 'count_db'.
            character_set = self.character_set.get(identifier)
            assert character_set != None

            result.append([character_set.get(), count.get()])

        return result

    def characters_for_grid(self):
        # count < 0 ==> characters span a grid and '- count' is the grid with
        return self.__character_info(lambda count: count.get() < 0)

    def characters_for_space(self):
        # count >= 0 ==> characters are single spaces, count = number of spaces
        return self.__character_info(lambda count: count.get() >= 0)

    def consistency_check(self, fh, position):
        # Are there at least some indentation elements?
        if len(filter(lambda x: x.get() != "bad", self.count_db.values())) == 0:
            fh.seek(position)
            error_msg("All possible indentation elements are set to 'bad'.\n" \
                      "No indentation detection possible.", fh)

        # Are all defined elements listed as parameters?
        for identifier in self.character_set_db.keys():
            # If the character set was considered 'bad' it should not be defined.
            count = self.count_db.get(identifier)
            # No character set definition is accepted without that its 'count' is pre-defined.
            assert count != None
            if count.get() != "bad": continue
            error_msg("Indentation element '%s' specified as 'bad'." % identifier,
                      count.file_name, count.line_n, DontExitF=True, WarningF=False)
            error_msg("However, a character set has been defined for it.",
                      self.character_set_db[identifier].file_name,
                      self.character_set_db[identifier].line_n)

        # Are all setting elements defined as character sets?
        parameter_set = set(self.character_set_db.keys())
        for identifier, count in self.count_db.items():
            if self.character_set_db.has_key(identifier): continue
            error_msg("Count of indentation element '%s' has been specified,\n" % identifier + \
                      "but its character set has not been defined. Add a character\n" + \
                      "set definition in a 'define' section, e.g.\n" + \
                      "'indentation { ... define { %s [\\t] }}'." % identifier, 
                      count.file_name, count.line_n)

        # Grid counts of '1' are better expressed as spaces of 1
        # .items() --> x, with x[0] = identifier, x[1] = count.
        grid_count_one_list = map(lambda x: x[0], filter(lambda x: x[1].get() == -1, self.count_db.items()))

        if len(grid_count_one_list) != 0:
            error_msg("Indentation grid counts of '1' as in %s\n" % repr(grid_count_one_list)[1:-1] + \
                      "are equivalent to spaces of '1' which are faster to compute.",
                      count.file_name, count.line_n, DontExitF=True)

        # If there are no spaces, then the grid is on a scale, then the grid 
        # can be transformed into 'easy-to-compute' spaces.
        if self.has_spaces() == False:
            grid_value_list = map(lambda x: - x.get(), 
                                  filter(lambda x: x.get() != "bad" and x.get() < 0, 
                                         self.count_db.values()))
            grid_value_list = list(set(grid_value_list)) # make sure things are unique
            min_grid_value  = min(grid_value_list)
            # Are all grid values a multiple of the minimum?
            if len(filter(lambda x: x % min_grid_value == 0, grid_value_list)) == len(grid_value_list):
                error_msg("Indentation setup does not contain spaces, only grids (tabulators). All grid\n" + \
                          "widths are a multiple of %i. The grid setup %s\n" \
                          % (min_grid_value, repr(sorted(grid_value_list))[1:-1]) + \
                          "is equivalent to a setup with space counts %s.\n" \
                          % repr(map(lambda x: x / min_grid_value, sorted(grid_value_list)))[1:-1] + \
                          "Space counts are faster to compute.", 
                          count.file_name, count.line_n, DontExitF=True)

        elif self.has_grid() == False:
            space_value_list = map(lambda x: x.get(), 
                                   filter(lambda x: x.get() != "bad" and x.get() >= 0, 
                                          self.count_db.values()))
            # If all space values are the same, then they can be replaced by '1' spaces
            prototype = space_value_list[0]
            if prototype != 1:
                unequal_list = filter(lambda x: x != prototype, space_value_list[1:])
                if len(unequal_list) == 0:
                    error_msg("Indentation does not contain a grid but only homogenous space counts of %i.\n" % prototype + \
                              "This setup is equivalent to a setup with space counts of 1. Space counts\n" + \
                              "of 1 are the fastest to compute.", 
                              count.file_name, count.line_n, DontExitF=True)
                
    def __repr__(self):
        txt = "Counts:\n"
        L = max(map(len, self.count_db.keys()))
        for name, count in sorted(self.count_db.items()):
            txt += "  %s%s = %s\n" % (name, " " * (L -len(name)), repr(count.get()))

        txt += "Character Sets:\n"
        L = max(map(len, self.character_set_db.keys()))
        for name, character_set in sorted(self.character_set_db.items()):
            txt += "  %s%s --> %s\n" % (name, " " * (L -len(name)), character_set.get().get_utf8_string())

        return txt


def do(fh):
    """Parses pattern definitions of the form:
   
          [ \t]                                       => grid 4;
          [:intersection([:alpha:], [\X064-\X066]):]  => spaces 1;

       In other words the right hand side *must* be a character set.
          
    """
    indentation_setup = IndentationSetup(fh)

    # NOTE: Catching of EOF happens in caller: parse_section(...)
    #
    skip_whitespace(fh)

    while 1 + 1 == 2:
        skip_whitespace(fh)

        if check(fh, ">"): 
            return indentation_setup
        
        # A regular expression state machine
        pattern_str, trigger_set = regular_expression.parse_character_set(fh, PatternStringF=True)

        indentation_setup.specify_character_set(identifier, trigger_set, fh)

        # -- get the name of the pattern
        skip_whitespace(fh)

        if not check(fh, "=>"):
            error_msg("Missing '=>' after character set definition.", fh)

        identifier = read_identifier(fh)
        if identifier == "":
            error_msg("Missing identifier for indentation element definition.", fh)

        verify_word_in_list(identifier, 
                            ["space", "grid", "newline", "suppressor"],
                            "Unrecognized specifier '%s'." % identifier, fh)

        skip_whitespace(fh)

        if identifier == "space":
            value = read_integer(fh)
            if value == None: value = 1
            indentation_setup.specify_space(trigger_set, value)

        elif identifier == "grid":
            value = read_integer(fh)
            if value == None: error_msg("Missing integer after keyword 'grid'.", fh) 
            indentation_setup.specify_grid(trigger_set, value)

        elif identifier == "newline":
            indentation_setup.specify_newline(trigger_set)

        elif identifier == "suppressor":
            indentation_setup.specify_suppressor(trigger_set)

        else:
            assert False, "Unreachable code reached."

        if check(fh, ";"):
            error_msg("Missing ';' after indentation specification.", fh)



