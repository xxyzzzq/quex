import quex.input.ucs_db_parser as ucs_db_parser

db_C = None
db_S = None
db_F = None
db_T = None

class DB:
    def __init__(self):
        self.lower_to_upper = {}
        self.upper_to_lower = {}


def __init():
    global db
    if db == None:
        db = ucs_db_parser.load_db("CaseFolding.txt", 
                                   NumberColumnList=[0], NumberListColumnList=[2])

def get_fold(CharacterCode, Flags="CSFT"):
    """Returns all characters to which the specified CharacterCode
       folds. The flag list corresponds to the flags defined in the
       Unicode Database status field, i.e.

       [Extract from Unicode Document]
         C: common case folding, common mappings shared by both simple 
            and full mappings.
         F: full case folding, mappings that cause strings to grow in length. 
            Multiple characters are separated by spaces.
         S: simple case folding, mappings to single characters where different 
            from F.
         T: special case for uppercase I and dotted uppercase I
           - For non-Turkic languages, this mapping is normally not used.
           - For Turkic languages (tr, az), this mapping can be used instead of
             the normal mapping for these characters.  Note that the Turkic
             mappings do not maintain canonical equivalence without additional
             processing. See the discussions of case mapping in the Unicode
             Standard for more information.
    """


