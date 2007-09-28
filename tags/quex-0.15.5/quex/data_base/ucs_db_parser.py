import re
import os
import sys
sys.path.insert(0, os.environ["QUEX_PATH"])

from quex.frs_py.file_in         import *
from quex.frs_py.string_handling import *

from quex.core_engine.interval_handling import Interval, NumberSet

unicode_db_directory = os.environ["QUEX_PATH"] + "/quex/data_base/unicode"
comment_deleter_re   = re.compile("#[^\n]*")

def open_data_base_file(Filename):
    try: 
        fh = open(unicode_db_directory + "/" + Filename)
    except:
        error_msg("Fatal---Unicode Database File '%s' not found!\n" % Filename + \
                  "QUEX_PATH='%s'\n" % os.environ["QUEX_PATH"] + \
                  "Unicode Database Directory: '%s'" % unicode_db_directory)
    return fh

def parse_table(Filename):
    fh = open_data_base_file(Filename)

    record_set = []
    for line in fh.readlines():
        line = trim(line)
        line = comment_deleter_re.sub("", line)
        if line.isspace() or line == "": continue
        # append content to record set
        record_set.append(map(trim, line.split(";")))

    return record_set

def convert_column_to_number(table, CodeColumnIdx):
    """ CodeColumnIdx: Column that contains the UCS character code or
                       code range.
        table:         table in which the content is changed.
    """
    for row in table:
        cell = row[CodeColumnIdx]
        row[CodeColumnIdx] = int("0x" + cell, 16)

def convert_column_to_interval(table, CodeColumnIdx):
    """ CodeColumnIdx: Column that contains the UCS character code or
                       code range.
        table:         table in which the content is changed.
    """
    for row in table:
        cell = row[CodeColumnIdx]
        fields = cell.split("..")         # range: value0..value1
        assert len(fields) in [1, 2]

        if len(fields) == 2: 
           begin = int("0x" + fields[0], 16)
           end   = int("0x" + fields[1], 16) + 1
        else:
           begin = int("0x" + fields[0], 16)
           end   = int("0x" + fields[0], 16) + 1

        row[CodeColumnIdx] = Interval(begin, end)

class FileBasedDB:

    def __init__(self, DB_Filename, ValueType, ValueColumnIdx, KeyColumnIdx, Key2ColumnIdx=-1):
        self.db          = {}
        self.db_filename = DB_Filename
        self.key_column_index                 = KeyColumnIdx
        self.optional_second_key_column_index = Key2ColumnIdx
        self.value_column_index               = ValueColumnIdx
        self.value_type                       = ValueType

    def __getitem__(self, Value):
        if self.db == {}: self.init_db()
        try:    return self.db[Value]
        except: pass

    def __enter_number_set(self, Key, Value):
        if self.db.has_key(Key):
            self.db[Key].quick_append_interval(Value)
        else:
            self.db[Key] = NumberSet(Value)

    def __enter_string(self, Key, Value):
        self.db[Key] = Value

    def __enter_number(self, Key, Value):
        self.db[Key] = Value

    def __convert_table_to_associative_map(self, table):
        """Produces a dictionary that maps from 'keys' to NumberSets. The 
           number sets represent the code points for which the key (property)
           is valid.

           ValueColumnIdx: Column that contains the character code interval or
                           string to which one wishes to map.

           KeyColmnIdx:   Column that contains the 'key' to be used for the map

           self.db = database to contain the associative map.
        """
        ValueColumnIdx = self.value_column_index
        KeyColumnIdx   = self.key_column_index

        enter = { "NumberSet": self.__enter_number_set,
                  "number":    self.__enter_number,
                  "string":    self.__enter_string
                }[self.value_type]

        i = 0
        for record in table:
            i += 1
            key   = record[KeyColumnIdx]
            value = record[ValueColumnIdx]

            enter(key, value)
            if self.optional_second_key_column_index != -1:
                key2 = record[self.optional_second_key_column_index]
                enter(key2, value)

    def init_db(self):
        table = parse_table(self.db_filename)
        if self.value_type == "NumberSet": convert_column_to_interval(table, self.value_column_index)
        elif self.value_type == "number":  convert_column_to_number(table, self.value_column_index)
        self.__convert_table_to_associative_map(table)

class PropertyInfo:
    def __init__(self, Name, Alias, Type):
        """Alias = short form of Name or Value.
        """
        self.name  = Name
        self.alias = Alias
        self.type  = Type
        self.name_to_alias_map = {}   # map value to alias
        self.code_point_db     = None # only for binary properties

    def __repr__(self):
        txt  = "NAME          = '%s'\n" % self.name
        txt += "ALIAS         = '%s'\n" % self.alias
        txt += "TYPE          = '%s'\n" % self.type
        if self.type == "Binary":
            txt += "VALUE_ALIASES = (Binary has no values)\n"
        else:
            txt += "VALUE_ALIASES = {\n    %s\n}\n" % repr(self.name_to_alias_map).replace(",", ",\n    ")
        return txt

    def get_code_points(self, Value):
        """Returns UCS code points of the characters for which 'property=Value'.
        """
        pass



class PropertyInfoDB:
    def __init__(self):
        self.property_name_to_alias_map = {}  # map: property alias to property name
        self.db = {}                          # map: property alias to property information

    def __getitem__(self, PropertyName):
        if self.db == {}: self.__init_db()
        try:    return self.db[self.property_name_to_alias_map[PropertyName]]
        except: return ""

    def __init_db(self):
        self.__parse_property_name_alias_and_type()
        self.__parse_property_value_and_value_aliases()
        # -- most of the properties are binary, so let's load the file PropList and
        #    fill them in one single beat.
        self.__load_binary_property_code_points()
        self.__load_binary_property_code_points_Composition_Exclusion()

    def __parse_property_name_alias_and_type(self):
        fh = open_data_base_file("PropertyAliases.txt")

        # -- skip anything until the first line that contains '======'
        line = fh.readline()
        while line != "":
            if line.find("# ==================") != -1: break
            line = fh.readline()

        property_type = "none"
        for line in fh.readlines():
            line = trim(line)
            if line != "" and line[0] == "#" and line.find("Properties") != -1:
                property_type = line.split()[1]
                continue
            

            line = comment_deleter_re.sub("", line)
            if line.isspace() or line == "": continue
            # append content to record set
            fields = map(trim, line.split(";"))
            property_alias = fields[0]
            property_name  = fields[1]

            self.db[property_alias] = PropertyInfo(property_name, property_alias, property_type)
            self.property_name_to_alias_map[property_name] = property_alias

    def __parse_property_value_and_value_aliases(self):
        """NOTE: Function __parse_property_name_alias_and_type() **must be called**
                 before this function.
        """
        assert self.db != {}
        table = parse_table("PropertyValueAliases.txt")

        for row in table:
            property_alias       = row[0]
            property_value_alias = row[1]
            property_value       = row[2]
            # -- if property db has been parsed before, this shall not fail
            property_info = self.db[property_alias]
            property_info.name_to_alias_map[property_value] = property_value_alias

    def __load_binary_property_code_points(self):
        # property descriptions working with 'property names'
        db_list_1 = [ 
                FileBasedDB("PropList.txt", "NumberSet", 0, 1),
                FileBasedDB("extracted/DerivedBinaryProperties.txt", "NumberSet", 0, 1),
                FileBasedDB("DerivedCoreProperties.txt", "NumberSet", 0, 1),
                FileBasedDB("DerivedNormalizationProps.txt", "NumberSet", 0, 1),
                ]

        def get_item_list(db_list):
            item_list = []
            for db in db_list:
                db.init_db()
                item_list.extend(db.db.items())
            return item_list

        item_list_1 = get_item_list(db_list_1)

        for key, number_set in item_list_1:
            if self.property_name_to_alias_map.has_key(key): 
                property_name_alias = self.property_name_to_alias_map[key]
            else:
                property_name_alias = key
            if self.db[property_name_alias].type != "Binary": continue
            self.db[property_name_alias].code_point_db = number_set

    def __load_binary_property_code_points_Composition_Exclusion(self):
        table = parse_table("CompositionExclusions.txt")

        number_set = NumberSet()
        for row in table:
           begin = int("0x" + row[0], 16)
           number_set.quick_append_interval(Interval(begin, begin + 1))
        number_set.clean()    

        self.db["CE"].code_point_db = number_set

    def get_property_descriptions(self):
        item_list = self.db.items()
        item_list.sort(lambda a, b: cmp(a[0], b[0]))
        txt = ""
        item_list.sort(lambda a, b: cmp(a[1].type, b[1].type))
        for key, property in item_list:
            name = property.name
            txt += "%s(%s): %s%s" % (name, key, " " * (34 - len(name+key)), property.type)
            if property.code_point_db != None: txt += "%s(loaded)\n" % (" " * (15-len(property.type)))
            else:                              txt += "\n"

        return txt



blocks_db  = FileBasedDB("Blocks.txt", "NumberSet", 0, 1)
blocks_db  = FileBasedDB("Blocks.txt", "NumberSet", 0, 1)
scripts_db = FileBasedDB("Scripts.txt", "NumberSet", 0, 1)
names_db   = FileBasedDB("UnicodeData.txt", "number", 0, 1, Key2ColumnIdx=10)
property_info_db = PropertyInfoDB()




print blocks_db["Arabic"]
print scripts_db["Greek"]
print "%X" % names_db["LATIN SMALL LETTER CLOSED REVERSED EPSILON"]
print property_info_db["White_Space"]
print property_info_db.get_property_descriptions()
