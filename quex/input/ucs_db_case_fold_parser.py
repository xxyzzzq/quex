"""This implements the basic algorithm for caseless matching
   as described in Unicode Standard Annex #21 "CASE MAPPINGS", Section 1.3.

"""
import quex.input.ucs_db_parser as ucs_db_parser

class DB:
    def __init__(self):
        self.lower_to_upper = {}
        self.upper_to_lower = {}

    def get_upper_and_lower_partners(self, CharacterCode):
        result = []

        for letter in self.upper_to_lower.get(CharacterCode, []):
            if letter not in result: result.append(letter)

        for letter in self.lower_to_upper.get(CharacterCode, []):
            if letter not in result: result.append(letter)

        return result

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

        if len(lower) == 1:
            db_set[status].upper_to_lower.setdefault(upper, []).append(lower[0])
        else:
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
    worklist = [ CharacterCode ]
    result   = []
    while len(worklist) != 0:
        character_code = worklist.pop()

        if type(character_code) == list: continue

        for status, db in db_set.items():
            if status not in Flags: continue

            # Collect the 'pairing' characters
            partner_list = db.get_upper_and_lower_partners(character_code)

            # All 'partners' that are not yet treated need to be added
            # to the 'todo list'. All partners that are not yet in result
            # need to be added.
            for x in partner_list:
                if x not in result: 
                    worklist.append(x)
                    result.append(x)

        if character_code not in result:
            result.append(character_code)
       
    return result
