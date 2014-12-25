from quex.engine.analyzer.examine.recipe_base import Recipe
from quex.engine.operations.content_accepter  import AccepterContent
from quex.engine.operations.operation_list    import Op
from quex.engine.operations.se_operations     import SeAccept, \
                                                     SeStoreInputPosition
from quex.engine.misc.tools                   import flatten_it_list_of_lists, \
                                                     UniformObject, \
                                                     none_is_None, \
                                                     all_isinstance

from quex.blackboard import E_PreContextIDs, \
                            E_R

class RecipeAcceptance(Recipe):
    """Recipe to describe the acceptance behavior upon exit from a state 
    machine. Details are provided in 01-ACCEPTANCE.txt.
    
    There are two members to implement acceptance and input position 
    placement.

      .accepter:  
          
         A list that looks like 

              [  (pre-context-id 6, acceptance-id 12),
                 (pre-context-id 4, acceptance-id 11),
                 ....
                 (No pre-context,   acceptance-id 14),
              ]

        which tells in a prioritized way what to accept upon under the
        condition that a pre-context is present. The first wins. Thus, 
        any entry after the conditionless acceptance is meaningless.
        
        acceptance-id is None => acceptance is restored from the acceptance
                                 register ('pre-context' must be None, too).


      .ip_offset_db:
          
              position register id   -->   offset

        Input position must be determined by
              
              if offset is not None:
                  input_p += offset
              else:                       
                  input_p  = aux_register[position register id] + offset

    The 'aux_register' values are set during interference in mouth states.
    """
    __slots__            = ("accepter", "ip_offset_db")
    SCR                  = (E_R.AcceptanceRegister, E_R.PositionRegister)
    RestoreAcceptance    = (None, None)
    __restore_all_recipe = None

    def __init__(self, Accepter, IpOffsetDb):
        assert IpOffsetDb is not None
        assert Accepter is not None
        self.accepter     = Accepter
        self.ip_offset_db = IpOffsetDb

    @staticmethod
    def RestoreAll():
        if self.__restore_all_recipe is None:
            ip_offset_db = {} # .get(RegisterId) is None for all => restore all 
            self.__restore_all_recipe = RecipeAcceptance(RecipeAcceptance.RestoreAcceptance, 
                                                         ip_offset_db)
        return self.__restore_all_recipe

    @classmethod
    def accumulate(cls, PrevRecipe, CurrSingleEntry):
        """RETURNS: Recipe = concatenation of 'Recipe' + relevant operations of
                             'SingleEntry'.
        """
        accepter     = cls._accumulate_acceptance(PrevRecipe, CurrSingleEntry)
        ip_offset_db = cls._accumulate_input_pointer_storage(PrevRecipe, CurrSingleEntry)

        return RecipeAcceptance(accepter, ip_offset_db)
        
    @classmethod
    def interfere(cls, EntryRecipeDb):
        """Determines 'mouth' by 'interference'. That is, it considers all entry
        recipes and observes their homogeneity. 
        
        RETURNS: 
            
            [0] Recipe.
            [1] Set of undetermined registers. 

        The undetermined registers are those, that need to be computed upon
        entry, and are restored from inside the recipe.
        """
        undetermined_register_set = set()

        # Acceptance
        accepter     = cls._interfere_acceptance(EntryRecipeDb)
        if cls.RestoreAcceptance in accepter:
            undetermined_register_set.add(E_R.AcceptanceRegister)

        # Input position storage
        ip_offset_db = cls._interfere_input_position_storage(EntryRecipeDb)
        undetermined_register_set.update(
            (E_R.PositionRegister, register_id)
            for register_id, offset in ip_offset_db.iteritems()
            if offset is None
        )
        
        return RecipeAcceptance(accepter, ip_offset_db), \
               undetermined_register_set
        
    @staticmethod
    def _accumulate_acceptance(PrevRecipe, CurrEntry):
        """Longest match --> later acceptances have precedence. The acceptance
        scheme of the previous recipe comes AFTER the current acceptance scheme.
        An unconditional acceptance makes any later acceptance check superfluous.
        """ 
        accepter        = []
        unconditional_f = False
        for cmd in sorted(CurrEntry.get_iterable(SeAccept), 
                          key=lambda x: x.acceptance_id()):
            accepter.append(cmd)
            if cmd.pre_context_id() == E_PreContextIDs.NONE: 
                # Unconditional acceptance overrules all later acceptances.
                break
        else:
            # No unconditional acceptance occurred, the previous acceptances
            # must be appended--if there is something.
            if PrevRecipe is not None and PrevRecipe.accepter is not None:
                accepter.extend(PrevRecipe.accepter)

        if not accepter: return [ RecipeAcceptance.RestoreAcceptance ]
        else:            return accepter

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
        def new_offset(PrevOffset):
            if PrevOffset is None: return None
            else:                  return PrevOffset - 1

        # Storage into a register overwrites previous storages
        # Previous storages receive '.offset - 1'
        if PrevRecipe is not None:
            ip_offset_db = dict( 
                (register_id, new_offset(offset))
                for register_id, offset in PrevRecipe.ip_offset_db.iteritems()
            )
        else:
            ip_offset_db = {}

        for cmd in CurrSingleEntry.get_iterable(SeStoreInputPosition): 
            ip_offset_db[cmd.acceptance_id()] = 0

        # Any acceptance that does not restore from a position register
        # defines the current position as the point where the input pointer
        # needs to be reset upon acceptance.
        for cmd in CurrSingleEntry.get_iterable(SeAccept): 
            if cmd.restore_position_register_f(): continue
            ip_offset_db[cmd.acceptance_id()] = 0

        return ip_offset_db

    @classmethod
    def _interfere_acceptance(cls, EntryRecipeDb):
        """If the acceptance scheme differs for only two recipes, then the 
        acceptance must be determined upon entry and stored in the LastAcceptance
        register.
        """ 
        # Interference requires determined entry recipes.
        assert none_is_None(EntryRecipeDb.itervalues())

        return UniformObject.from_iterable(
                 recipe.accepter
                 for recipe in EntryRecipeDb.itervalues()).content

    
    @classmethod
    def _interfere_input_position_storage(cls, EntryRecipeDb):
        """Each position register is considered separately. If for one register 
        the offset differs, then it can only be determined from storing it in 
        this mouth state and restoring it later.
        """
        def get_uniform_recipe(RegisterId, RecipeList):
            """If there are two recipes with differing offsets for a given
            register, then input position must be reset by register restore.
            Then 'offset = None'.  Else, in the homogeneous case, the offset is
            the one that all entries share."""
            return UniformObject.from_iterable(
                     recipe.ip_offset_db.get(RegisterId)
                     for recipe in RecipeList).content

        # All registers from all recipes --> register_id_set.
        register_id_set = set(flatten_it_list_of_lists(
                              recipe.ip_offset_db.iterkeys() 
                              for recipe in EntryRecipeDb.itervalues()))    
        # List of all recipes.
        recipe_list     = list(EntryRecipeDb.itervalues())

        return dict(
            (register_id, get_uniform_recipe(register_id, recipe_list))
            for register_id in register_id_set
        )
        
    def get_mouth_Entry(self, mouth):
        entry_db = dict(
            (from_si, OpList())
            for from_si in mouth.entry_register_db.iterkeys()
        )

        for register_id in mouth.undetermined_register_set:
            if register_id == E_R.AcceptanceRegister:
                self._let_acceptance_be_stored(entry_db, mouth)
            else:
                sub_register_id = register_id[1]
                self._let_input_position_be_stored(entry_db, 
                                                   mouth.entry_recipe_db, 
                                                   sub_register_id)
        return entry_db

    def get_linear_Entry(self, linear):
        return {}

    def get_DropOut(self, info):
        if self.accepter is None:
            return Op.RouterByLastAcceptance(self.ip_offset_db)
        else:
            return Op.AccepterAndRouter(self.accepter, self.ip_offset_db)

    @staticmethod
    def _let_acceptance_be_stored(entry_db, EntryRecipeDb):
        """Sets 'store acceptance' commands at every entry into the state.
        """
        for from_si, r in EntryRecipeDb.iteritems():
            # If acceptance is already stored in 'aux_acceptance', no second
            # storage is required.
            if r.accepter is None: continue
            assert not entry_db[from_si].has_command_id(E_Op.Accepter) 

            entry_db[from_si].append(Op.Accepter(r.accepter))

    @staticmethod
    def _let_input_position_be_stored(entry_db, EntryRecipeDb, RegisterId):
        for from_si, r in EntryRecipeDb.iteritems():
            # [X] Rationale for unconditional store input position: 
            #     see bottom of file.
            offset = r.ip_offset_db.get(RegisterId)
            # If input position needs to be restored, it cannot be more
            # restored than that.
            if offset is None: continue 

            entry_db[from_si].append(
                Op.StoreInputPosition(E_PreContextIDs.NONE, RegisterId, offset)
            )

    def __str__(self):
        txt = [ "    Accepter:" ]
        if self.accepter is None:
            txt.append("     restore!\n")
        else:
            txt.append("\n")
            for x in self.accepter:
                if x.pre_context_id() != E_PreContextIDs.NONE:
                    txt.append("      pre%s => %s\n" % (x.pre_context_id(), x.acceptance_id())) 
                else:
                    txt.append("      %s\n" % x.acceptance_id())

        txt.append("    InputOffsetDb:\n")
        for register, offset in sorted(self.ip_offset_db.iteritems()):
            if offset is not None:
                txt.append("      [%s] offset: %s\n" % (register, offset))
            else:
                txt.append("      [%s] restore!\n" % register)
        return "".join(txt)

    
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
