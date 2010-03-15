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

        if row[0] == ord('s') or row[2][0] == ord('s'): 
            print "##", ord('s'), row
        db_set[status].upper_to_lower.setdefault(upper, []).append(lower)

        if status == "F": continue

        # Only use scalar values as dictionary keys --> do
        # dot fold multi-value characters to single characters.
        db_set[status].lower_to_upper.setdefault(lower[0], []).append(upper)


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
    result = [ CharacterCode ]

    # Collect the 'pairing' characters
    for status, db in db_set.items():
        if status not in Flags: continue

        elif db.upper_to_lower.has_key(CharacterCode):
            value = db.upper_to_lower[CharacterCode]
            if value not in result: result.append(value)

        elif db.lower_to_upper.has_key(CharacterCode):
            value = db.lower_to_upper[CharacterCode]
            if value not in result: result.append(value)
       
    return result
        
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
            value = db.upper_to_lower[CharacterCode]
            if value not in result: result.append(value)

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
            value = db.lower_to_upper[CharacterCode]
            if value not in result: result.append(value)

    return result
