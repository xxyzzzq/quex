from quex.engine.analyzer.examine.recipe_base import Recipe
from quex.engine.operations.content_accepter  import AccepterContent
from quex.engine.operations.operation_list    import Op
from quex.engine.operations.se_operations     import SeAccept, \
                                                     SeStoreInputPosition
from quex.engine.misc.tools                   import flatten_it_list_of_lists

from quex.blackboard import E_PreContextIDs, \
                            E_R

class RecipeAcceptance(Recipe):
    """A 'RecipeAcceptance' determines the pattern id of the winning pattern 
    and the place where the input position pointer needs to point upon exit 
    of the state machine in a particular state (Details in 
    '01-ACCEPTANCE.txt'). It also contains enough data so late successor
    states may determine their recipes. Two members describe the recipe:

        .accepter = None, if acceptance MUST be restored.
                  = list, if acceptance can be determine from scheme.

        .ip_offset_db - Dictionary
                .ip_offset_db[i] = const. offset to be added to input position.
                .ip_offset_db[i] is None => input position MUST be restored
                
    (1) .accepter 

    If the acceptance can be determined beforehand for a given state, then the
    .accepter is not None. If it can be determined then the accepter is a list.
    It can be considered as a priorized sequence, where the upper rows are 
    checked before lower rows and the first fulfilled pre-context triggers
    acceptance.

        [  (pre-context-id 6, acceptance-id 12),
           (pre-context-id 4, acceptance-id 11),
           ....
           (No pre-context,   acceptance-id 14),
        ]

    Note, that the first unconditional acceptance makes all later superfluous.
    Such a condition always succeeds and the according acceptance must happen.


    (2) .ip_offset_db

    The input position upon acceptance may have to be reset. This occurs,
    either because the acceptance happened some states before, or because
    it must be restored from a position register (post contexts). The entry

        .ip_offset_db[position_register_id]

    provides the offset that has to be added to the input pointer in
    order to emulate an assignment

        input_p = position_register[position_register_id]                 (2.1)

    That is, the above line is equivalent to
       
        input_p += .ip_offset_db[position_register_id]                    (2.2)

    Note, that the offset must be negative to point to an earlier input
    position This may not always be possible. If there is no entry
    '.ip_offset_db[i]', then the input pointer cannot be set by subtraction and
    it must be restored from registers.

    SUMMARY:

    With a given RecipeAcceptance 'r' for a state, acceptance and input
    position can be determined as follows:

        (1.1) .accepter is None --> read acceptance from 'LAST_ACCEPTANCE' 
                                    register.
        (1.2) .accepter is not None:
                 for row in .accepter:
                     if pre_context_fulfilled(row[0]): accept row[1]
                 else:
                     accept LAST_ACCEPTANCE

        (2.1) .ip_offset_db is None or .ip_offset_db[pattern_id] is None

                 input position = position_register[pattern_id]

        (2.2) .ip_offset_db[i] is present

                 input position -= .ip_offset_db[pattern_id]
    """
    __slots__ = ("accepter", "ip_offset_db")

    SCR = (E_R.InputP, E_R.Acceptance, E_R.PositionRegister)

    def __init__(self, Accepter=None, IpOffsetDb=None):
        self.accepter     = Accepter
        self.ip_offset_db = IpOffsetDb if IpOffsetDb is not None else {}

    @classmethod
    def accumulate(cls, linear, PrevRecipe, CurrSingleEntry):
        """RETURNS: Recipe = concatenation of 'Recipe' + relevant operations of
                             'SingleEntry'.
        """
        accepter     = cls._accumulate_acceptance(PrevRecipe, CurrSingleEntry)
        ip_offset_db = cls._accumulate_input_pointer_storage(PrevRecipe, CurrSingleEntry)

        cls.assign_recipe(linear, RecipeAcceptance(accepter, ip_offset_db))
        
    @classmethod
    def interfere(cls, mouth):
        """Determines 'mouth' by 'interference'. That is, it considers all entry
        recipes and observes their homogeneity. 
        
        RETURNS: 
            
            [0] Entry Db: 

                map: from state index --> operations REQUIRED upon state entry.
            
            
            [1] RecipeAcceptance 

                A recipe that determines acceptance and input position offsets.
        """
        # entry_db: from state index --> list of operations
        mouth.entry_db = dict((si, []) for si in mouth.entry_recipe_db.iterkeys())
        accepter       = cls._interfere_acceptance(mouth)
        ip_offset_db   = cls._interfere_input_position_storage(mouth)
        
        cls.assign_recipe(mouth, RecipeAcceptance(accepter, ip_offset_db))
        
    @classmethod
    def interfere_in_dead_lock_group(cls, MouthList):
        """
        
        RETURNS: An accumulated action that expresses the interference of 
                 recipes of states of a dead_lock group.
        """
        # entry_db: from state index --> list of operations
        for mouth in MouthList:
            mouth.entry_db = dict((si, []) 
                                  for si in mouth.entry_recipe_db.iterkeys())
            
        accepter     = cls._interfere_acceptance_in_dead_lock_group(MouthList)
        ip_offset_db = cls._interfere_store_input_position_in_dead_lock_group(MouthList)
        
        # All recipes in the dead-lock group are the same 
        recipe = RecipeAcceptance(accepter, ip_offset_db)
        cls.assign_recipe(mouth, recipe)

    @staticmethod
    def _accumulate_acceptance(PrevRecipe, CurrSingleEntry):
        """Longest match --> later acceptances have precedence. The acceptance
        scheme of the previous recipe comes AFTER the current acceptance scheme.
        An unconditional acceptance makes any later acceptance check superfluous.
        """ 
        accepter = []
        for cmd in sorted(CurrSingleEntry.get_iterable(SeAccept), 
                          key=lambda x: x.acceptance_id()):
            accepter.append(cmd)
            if not cmd.pre_context_f(): break
        else:
            # No unconditional acceptance occurred, the previous acceptances
            # must be appended.
            accepter.extend(PrevRecipe.accepter)

        return accepter

    @staticmethod
    def _accumulate_input_pointer_storage(PrevRecipe, CurrSingleEntry):
        """Storing the current input position into a register overwrites 
        previous storage operations. Previous storage operations that appear
        'n' steps before can be compensated by 'input_p -= n'. Thus, at
        each step '-1' is added to the compensation offset. 
        
        NOTE: Registers which do not appear in the 'ip_offset_db' are meant
        to be restored from registers. They cannot be computed by offset 
        addition. 
        """
        # Storage into a register overwrites previous storages
        # Previous storages receive '.offset - 1'
        ip_offset_db = dict( 
            (register_id, position_offset - 1)
            for register_id, position_offset in PrevRecipe.storage_offset_db.iteritems()
        )
        for cmd in CurrSingleEntry.get_iterable(SeStoreInputPosition): 
            ip_offset_db[cmd.register_id()] = 0

        return ip_offset_db

    @classmethod
    def _interfere_acceptance(cls, mouth):
        """If the acceptance scheme differs for only two states, then the 
        acceptance must be determined upon entry and stored in the LastAcceptance
        register.
        
        ADAPTS: 'mouth.entry_db' to contain operations that store acceptance, 
                                 if necessary.
        """ 
        prototype = None # Acceptance scheme
        for r in mouth.entry_recipe_db.iteritems():
            if   prototype is None:       prototype = r.accepter
            elif r.accepter == prototype: continue
            cls._let_acceptance_be_stored(mouth)
            return None
        # All acceptance schemes where the same => Overtake the prototype
        return prototype
    
    @classmethod
    def _interfere_input_position_storage(cls, mouth):
        """Each position register is considered separately. If for one register 
        the offset differs, then it can only be determined from storing it in 
        this mouth state and restoring it later.
        """
        # Determine the set of involved input position registers
        register_id_set = set(flatten_it_list_of_lists(
            r.ip_offfset_db.keys() 
            for r in mouth.entry_recipe_db.itervalues()))    

        # If for a given register, there are two different ways to compensate for
        # storing, then storing cannot be implemented consistently. In that case,
        # the resulting database entry is empty. In any other case the entry is
        # the offset to be added.
        ip_offset_db = {}
        for register_id in register_id_set:
            prototype = None
            for recipe in mouth.entry_recipe_db.iteritems():
                offset = recipe.ip_offset_db.get(register_id)
                if   prototype is None:   prototype = offset
                elif offset == prototype: continue
                cls._let_input_position_be_stored(mouth, register_id)
                # ip_offset_db[register_id] remains empty
                # =>> determined from restore, not by offset subtraction.
            else:
                # All input position offsets where the same 
                # => Overtake the prototype
                ip_offset_db[register_id] = prototype

        return ip_offset_db
        
    @classmethod
    def _interfere_acceptance_in_dead_lock_group(cls, mouth_list):
        """If the acceptance scheme differs for only two states, then the 
        acceptance must be determined upon entry and stored in the LastAcceptance
        register.
        
        ADAPTS: 'mouth.entry_db' to contain operations that store acceptance, 
                                 if necessary.
        """ 
        def recipe_iterable(MouthList):
            for mouth in MouthList:
                for r in mouth.entry_recipe_db.itervalues():
                    yield r

        prototype = None # Acceptance scheme
        for r in recipe_iterable(mouth_list):
            if   prototype is None:       prototype = r.accepter
            elif r.accepter == prototype: continue
            for mouth in mouth_list:
                cls._let_acceptance_be_stored(mouth)
            return None

        # All acceptance schemes where the same => Overtake the prototype
        return prototype
    
    @classmethod
    def _interfere_store_input_position_in_dead_lock_group(cls, MouthList):
        """"A dead-lock group contains loops, thus any referred input position
        lies an undefined number of steps backwards. It follows that ALL 
        stored input positions need to be determined by restoring from 
        registers. All incoming recipes must store their input position.
        """
        for mouth in MouthList:
            cls._let_input_position_be_stored(mouth)
        return {}

    @staticmethod
    def _let_acceptance_be_stored(mouth):
        """Sets 'store acceptance' commands at every entry into the state.
        """
        for from_si, r in mouth.entry_recipe_db.iteritems():
            if r.accepter is None: continue
            mouth.entry_db[from_si].append(AccepterContent.from_iterable(r.accepter))

    @staticmethod
    def let_input_position_be_stored(mouth, RegisterId):
        for from_si, r in mouth.entry_recipe_db.iteritems():
            if r.ip_offset_db is None: continue
            # [X] Rationale for unconditional store input position: 
            #     see bottom of file.
            mouth.entry_db[from_si].extend(
                Op.StoreInputPosition(E_PreContextIDs.NONE, register_id, offset)
                for register_id, offset in r.ip_offset_db.iteritems()
                if register_id == RegisterId
            )

    
# [X] Rationale for unconditional input position storage.
#
# The sequence 'if pre-context: store' may be translated into:
#
#      COMPARE            pre_context_flag, true
#      IF_NOT_EQUAL_JUMP  LABEL
#      STORE              input_p -> register
#   LABEL: ...
# 
# Thus even in the case that the position is not stored, the cost is: 1 x
# compare + 1 x conditional jump. The cost for always storing the input position
# is: 1x store. Since both involved entities are either on the stack (-> cache)
# or in registers the store operation can be expected to be very fast.
#
# On the other hand, the stored value is only used if the pre-context holds.
# Thus, no harm is done if the value is stored redundantly.
# 
# For the above two reasons, at the time of this writing it seems  rational to
# assume that the unconditional storage of input positions is faster than the
# conditional. (fschaef 14y12m2d)
