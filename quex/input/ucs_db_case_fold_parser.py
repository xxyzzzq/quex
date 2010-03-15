"""This implements the basic algorithm for caseless matching
   as described in Unicode Standard Annex #21, Section 1.3.
"""
import quex.input.ucs_db_parser as ucs_db_parser

class DB:
    def __init__(self):
        self.lower_to_upper = {}
        self.upper_to_lower = {}

db_set = None

def __init():
    global db_set

    if db_set != None: return

    db_set = { 
       "C": DB(),
       "S": DB(),
       "F": DB(),
       "T": DB(),
    }

    table = ucs_db_parser.parse_table("CaseFolding.txt", 
                                      NumberColumnList=[0], 
                                      NumberListColumnList=[2])

    for row in table:
        upper  = row[0]
        status = row[1]
        lower  = row[2]

        db_set[status].upper_to_lower.setdefault(upper, []).append(lower)

        if status == "F": continue

        # Only use scalar values as dictionary keys --> do
        # dot fold multi-value characters to single characters.
        db_set[status].lower_to_upper.setdefault(lower[0], []).append(upper)

def __add_result(result, db, CharacterCode):
    letter_list = db[CharacterCode]
    for letter in letter_list:
        if letter not in result: result.append(letter)

def get_fold_set(CharacterCode, Flags="CSFT"):
    """Returns all characters to which the specified CharacterCode
       folds. The flag list corresponds to the flags defined in the
       Unicode Database status field, i.e.

       [Extract from Unicode Document]
         C: common case folding, common mappings shared by both simple 
            and full mappings.
         F: full case folding, mappings that cause strings to grow in length. 
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
    __init()

    # The character itself shall always be part of the fold
    worklist = [ CharacterCode ]

    while 1 + 1 == 2:
        new_worklist = [ ]
        for character_code in worklist:
            if character_code not in new_worklist: 
                new_worklist.append(character_code)

            if type(character_code) == list: continue

            # Collect the 'pairing' characters
            for status, db in db_set.items():
                if status not in Flags: continue

                elif db.upper_to_lower.has_key(character_code):
                    __add_result(new_worklist, db.upper_to_lower, character_code)

                elif db.lower_to_upper.has_key(character_code):
                    __add_result(new_worklist, db.lower_to_upper, character_code)

        if worklist == new_worklist: break
        worklist = new_worklist
       
    print worklist
    return worklist
        
def get_lower_fold_set(CharacterCode, Flags="CSFT"):
    """Collect the lower 'pairing' characters."""
    __init()
    
    result = []
    for status, db in db_set.items():
        if status not in Flags: continue

        elif db.lower_to_upper.has_key(CharacterCode):
            # If the character is a 'lower' character then it is part of the set
            result.append(CharacterCode)

        elif db.upper_to_lower.has_key(CharacterCode):
            __add_result(result, db.upper_to_lower, CharacterCode)

    return result

def get_upper_fold_set(CharacterCode, Flags="CSFT"):
    """Collect the lower 'pairing' characters."""
    __init()

    result = []
    for status, db in db_set.items():
        if status not in Flags: continue

        elif db.upper_to_lower.has_key(CharacterCode):
            # If the character is a 'lower' character then it is part of the set
            result.append(CharacterCode)

        elif db.lower_to_upper.has_key(CharacterCode):
            __add_result(result, db.lower_to_upper, CharacterCode)

    return result
