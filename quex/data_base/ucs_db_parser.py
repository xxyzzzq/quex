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

def __enter_number_set(db, Key, Value):
    ValueType = Value.__class__.__name__
    assert ValueType in ["Interval", "int"]

    if ValueType == "int": Value = Interval(Value)

    if db.has_key(Key): db[Key].quick_append_interval(Value, SortF=False)
    else:               db[Key] = NumberSet(Value)

def __enter_string(db, Key, Value):
    db[Key] = Value

def __enter_number(db, Key, Value):
    db[Key] = Value

def convert_table_to_associative_map(table, ValueColumnIdx, ValueType, KeyColumnIdx, OptionalKeyColumnIdx=-1):
    """Produces a dictionary that maps from 'keys' to NumberSets. The 
       number sets represent the code points for which the key (property)
       is valid.

       ValueColumnIdx: Column that contains the character code interval or
                       string to which one wishes to map.

       KeyColmnIdx:   Column that contains the 'key' to be used for the map

       self.db = database to contain the associative map.
    """
    try:
        enter = { "NumberSet": __enter_number_set,
                  "number":    __enter_number,
                  "string":    __enter_string
                }[ValueType]
    except:
        raise BaseException("ValueType = '%s' unknown.\n" % ValueType)

    db = {}
    i = 0
    for record in table:
        i += 1
        key   = record[KeyColumnIdx]
        value = record[ValueColumnIdx]

        enter(db, key, value)
        if  OptionalKeyColumnIdx != -1:
            key2 = record[OptionalKeyColumnIdx]
            enter(db, key2, value)

    return db

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


    def init_db(self):
        table = parse_table(self.db_filename)
        if self.value_type == "NumberSet": convert_column_to_interval(table, self.value_column_index)
        elif self.value_type == "number":  convert_column_to_number(table, self.value_column_index)

        self.db = convert_table_to_associative_map(table, 
                                                   self.value_column_index, 
                                                   self.value_type,
                                                   self.key_column_index, 
                                                   self.optional_second_key_column_index)

class PropertyInfo:
    def __init__(self, Name, Alias, Type, RelatedPropertyInfoDB):
        """Alias = short form of Name or Value.
        """
        self.name  = Name
        self.alias = Alias
        self.type  = Type
        self.name_to_alias_map = {}   # map value to alias
        self.code_point_db     = None # only for binary properties
        self.related_property_info_db = RelatedPropertyInfoDB

    def __repr__(self):
        assert self.type in ["Binary", "Catalogue", "Enumerated", "String", "Miscellaneous", "Numeric"]

        txt  = "NAME          = '%s'\n" % self.name
        txt += "ALIAS         = '%s'\n" % self.alias
        txt += "TYPE          = '%s'\n" % self.type
        if self.type == "Binary":
            txt += "VALUE_ALIASES = (Binary has no values)\n"
        else:
            txt += "VALUE_ALIASES = {\n    %s\n}\n" % repr(self.name_to_alias_map).replace(",", ",\n    ")
        return txt

    def get_character_set(self, Value=None):
        """Returns the character set that corresponds to 'Property==Value'.
           'Value' can be a property value or a property value alias.
           For binary properties 'Value' must be None.
        """
        assert self.type != "Binary" or Value == None

        if self.code_point_db == None:
            self.init_code_point_db()

        if self.type == "Binary": 
            return self.code_point_db

        if self.name_to_alias_map.has_key(Value): value_alias = Value
        else:                                     value_alias = self.name_to_alias_map[Value]

        return self.code_point_db[value_alias]

    def init_code_point_db(self):

        if self.alias in ["na", "na1", "nv", "gc", "bc"]:
            # Name
            # Unicode 1 Name 
            # Numeric Value
            # General Category
            # Bidi Class
            self.related_property_info_db.load_UnicodeData()
            return
        
        if self.type == "Catalog":
            if self.alias == "blk":
                self.code_point_db = FileBasedDB("Blocks.txt",     "NumberSet", 0, 1)
            elif self.alias == "age":
                self.code_point_db = FileBasedDB("DerivedAge.txt", "NumberSet", 0, 1)
            elif self.alias == "sc":
                self.code_point_db = FileBasedDB("Scripts.txt",    "NumberSet", 0, 1)

        elif self.type == "Binary":

            if self.alias in ["AHex", "Bidi_C", "CE", "Dash", "Dep", "Dia",
                    "Ext", "Hex", "Hyphen", "IDSB", "IDST", "Ideo", "Join_C",
                    "LOE", "NChar", "OAlpha", "ODI", "OGr_Ext", "OIDC", "OIDS",
                    "OLower", "OMath", "OUpper", "Pat_Syn", "Pat_WS", "QMark",
                    "Radical", "SD", "STerm", "Term", "UIdeo", "VS", "WSpace"]:

                filename = "PropList.txt"

            elif self.alias == "Bidi_M":

                filename = "extracted/DerivedBinaryProperties.txt"

            elif self.alias in ["Alpha", "DI", "Gr_Base", "Gr_Ext",
                    "Gr_Link", "IDC", "IDS", "Math", "Lower", "Upper", "XIDC", "XIDS" ]:

                filename = "DerivedCoreProperties.txt"

            elif self.alias == "Comp_Ex":

                filename = "DerivedNormalizationProps.txt"

            elif self.alias == "CE":

                self.related_property_info_db.load_Composition_Exclusion()
                return

            else:

                print "## no db file:"
                print self
                return
                   
            self.related_property_info_db.load_binary_properties(filename)

        elif self.type == "Enumerated":
            try:
                filename = {
                        "Numeric_Type":              "extracted/DerivedNumericType.txt",
                        "Joining_Type":              "extracted/DerivedJoiningType.txt",
                        "Joining_Group":             "extracted/DerivedJoiningGroup.txt",
                        "Word_Break":                "auxiliary/WordBreakProperty.txt",
                        "Sentence_Break":            "auxiliary/SentenceBreakProperty.txt",
                        "Grapheme_Cluster_Break":    "auxiliary/GraphemeClusterBreak.txt",
                        "Hangul_Syllable_Type":      "HangulSyllableType.txt",
                        "Line_Break":                "extracted/DerivedLineBreak.txt",
                        "Decomposition_Type":        "extracted/DerivedDecompositionType.txt",
                        "East_Asian_Width":          "extracted/DerivedEastAsionWidth.txt",
                        "Canonical_Combining_Class": "extracted/DerivedCanonicalCombiningClass.txt",
                    }[self.name]
            except:
                print "## no db file for:"
                print self
                return

            self.code_point_db = FileBasedDB(filename, "NumberSet", 0, 1)

        elif self.type == "Miscellaneous":
            pass # see first check




class PropertyInfoDB:
    def __init__(self):
        self.property_name_to_alias_map = {}  # map: property alias to property name
        self.db = {}                          # map: property alias to property information

    def __getitem__(self, PropertyName):
        if self.db == {}: self.__init_db()

        try:              return self.db[self.property_name_to_alias_map[PropertyName]]
        except: return ""

    def get_character_set(self, Property, Value=None):
        """Returns the character set that corresponds to 'Property==Value'.

           'Property' can be a property name or a property alias.
           'Value'    can be a property value or a property value alias.
                      For binary properties 'Value' must be None.
        """
        if self.db == {}: self.__init_db()

        if self.property_name_to_alias_map.has_key(Property):
            property_alias = self.property_name_to_alias_map[Property]
        else:
            property_alias = Property

        if not self.db.has_key(property_alias):
            return None

        property = self.db[property_alias]

        return property.get_character_set(Value)

    def __init_db(self):
        self.__parse_property_name_alias_and_type()
        self.__parse_property_value_and_value_aliases()

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

            self.db[property_alias] = PropertyInfo(property_name, property_alias, property_type, self)
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

    def load_binary_properties(self, DB_Filename):
        # property descriptions working with 'property names'
        db = FileBasedDB(DB_Filename, "NumberSet", 0, 1)
        db.init_db()

        for key, number_set in db.db.items():

            if self.property_name_to_alias_map.has_key(key): 
                property_name_alias = self.property_name_to_alias_map[key]
            else:
                property_name_alias = key

            property = self.db[property_name_alias]

            if property_name_alias == "Comp_Ex": print number_set # DEBUG

            if property.type != "Binary": continue


            property.code_point_db = number_set

    def load_Composition_Exclusion(self):
        table = parse_table("CompositionExclusions.txt")

        number_set = NumberSet()
        for row in table:
           begin = int("0x" + row[0], 16)
           number_set.quick_append_interval(Interval(begin, begin + 1))
        number_set.clean()    

        self.db["CE"].code_point_db = number_set

    def load_UnicodeData(self):
        table = parse_table("UnicodeData.txt")
        CodePointIdx       = 0
        NumericValueIdx    = 6
        NameIdx            = 1
        NameUC1Idx         = 10
        GeneralCategoryIdx = 2
        BidiClassIdx       = 4
        convert_column_to_number(table, CodePointIdx)

        names_db            = convert_table_to_associative_map(table, CodePointIdx, "number", NameIdx)
        names_uc1_db        = convert_table_to_associative_map(table, CodePointIdx, "number", NameUC1Idx)
        numeric_value_db    = convert_table_to_associative_map(table, CodePointIdx, "NumberSet", NumericValueIdx)
        general_category_db = convert_table_to_associative_map(table, CodePointIdx, "NumberSet", GeneralCategoryIdx)
        bidi_class_db       = convert_table_to_associative_map(table, CodePointIdx, "NumberSet", BidiClassIdx) 

        self.db["na"].code_point_db  = names_db          # Name
        self.db["na1"].code_point_db = names_uc1_db      # Name Unicode 1
        self.db["nv"].code_point_db  = numeric_value_db  # Numeric Value
        self.db["gc"].code_point_db  = numeric_value_db  # General Category
        self.db["bc"].code_point_db  = numeric_value_db  # BidiClass

    def get_property_descriptions(self):
        item_list = self.db.items()
        item_list.sort(lambda a, b: cmp(a[0], b[0]))
        txt = ""
        item_list.sort(lambda a, b: cmp(a[1].type, b[1].type))
        for key, property in item_list:
            name = property.name
            txt += "%s(%s): %s%s" % (name, key, " " * (34 - len(name+key)), property.type)
            property.init_code_point_db()
            if property.code_point_db != None: txt += "%s(loaded)\n" % (" " * (15-len(property.type)))
            else:                              txt += "\n"

        return txt


pi_db = PropertyInfoDB()



print pi_db.get_character_set("Block",  "Arabic")
print pi_db.get_character_set("Age",    "5.0")
print pi_db.get_character_set("Script", "Greek")
#print "%X" % names_db["LATIN SMALL LETTER CLOSED REVERSED EPSILON"]
print pi_db.get_character_set("White_Space")

print pi_db.get_property_descriptions()

print "###"
print repr(pi_db["Comp_Ex"]), type(pi_db["CE"])
