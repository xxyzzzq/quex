from quex.engine.analyzer.examine.recipe_base import Recipe
from quex.engine.operations.content_accepter  import AccepterContent
from quex.engine.operations.operation_list    import Op
from quex.engine.operations.se_operations     import SeAccept, \
                                                     SeStoreInputPosition
from quex.engine.misc.tools                   import flatten_it_list_of_lists

from quex.blackboard import E_PreContextIDs, \
                            E_R

InfoAccept   = namedtuple("InfoAccept",   ("pre_context_id", "acceptance_id"))
InfoIpOffset = namedtuple("InfoIpOffset", ("offset", "aux_register_id"))

class RecipeAcceptance(Recipe):
    """Recipe to describe the acceptance behavior upon exit from a state 
    machine. Details are provided in 01-ACCEPTANCE.txt.
    
    There are two members to implement acceptance and input position 
    placement.

      .accepter:  
          
            None => if acceptance is be restored from 'last_accept'.
            else => list describing the acceptance scheme.

         A list looks like 

              [  (pre-context-id 6, acceptance-id 12),
                 (pre-context-id 4, acceptance-id 11),
                 ....
                 (No pre-context,   acceptance-id 14),
              ]

        which tells in a prioritized way what to accept upon under the
        condition that a pre-context is present. The first wins. Thus, 
        any entry after the conditionless acceptance is meaningless.


      .ip_offset_db:
          
              position register id   -->   (offset, aux_register_id)

        Input position must be determined by
              
              if aux_register_id == -1:
                  input_p += offset
              else:                       
                  input_p  = aux_register[aux_register_id] + offset

    The 'aux_register' values are set during interference in mouth states.
    """
    __slots__ = ("accepter", "ip_offset_db")

    SCR = (E_R.AcceptanceRegister, E_R.PositionRegister)

    def __init__(self, Accepter, IpOffsetDb):
        assert all_isinstance(Accepter,                  InfoAccept)
        assert all_isinstance(InfoIpOffset.itervalues(), InfoIpOffset)
        self.accepter     = Accepter
        self.ip_offset_db = IpOffsetDb

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
        accepter       = cls._interfere_acceptance(EntryRecipeDb)
        ip_offset_db   = cls._interfere_input_position_storage(EntryRecipeDb)
        
        undetermined_register_set = ()
        if accepter is None: undetermined_register_set.add(E_R.AcceptanceRegister)
        for register_id, offset in ip_offset_db.iteritems():
            if offset is not None: continue
            undetermined_register_set.add((E_R.PositionRegister, register_id))
        
        return RecipeAcceptance(accepter, ip_offset_db), undetermined_register_set
        
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
            if cmd.pre_context_id() == E_PreContextIDs.NONE: break

        if PrevRecipe is not None:
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
        def new_offset(PrevOffset):
            if PrevOffset is None: return None
            else:                  return PrevOffset - 1

        # Storage into a register overwrites previous storages
        # Previous storages receive '.offset - 1'
        if PrevRecipe is not None:
            ip_offset_db = dict( 
                (register_id, new_offset(offset))
                for register_id, offset in PrevRecipe.storage_offset_db.iteritems()
            )
        else:
            ip_offset_db = {}

        for cmd in CurrSingleEntry.get_iterable(SeStoreInputPosition): 
            ip_offset_db[cmd.register_id()] = 0

        # Any acceptance that does not restore from a position register
        # defines the current position as the point where the input pointer
        # needs to be reset upon acceptance.
        for cmd in CurrSingleEntry.get_iterable(SeAccept): 
            if not cmd.restore_position_register_f(): continue
            ip_offset_db[cmd.acceptance_id()] = 0

        return ip_offset_db

    @classmethod
    def _interfere_acceptance(cls, EntryRecipeDb):
        """If the acceptance scheme differs for only two states, then the 
        acceptance must be determined upon entry and stored in the LastAcceptance
        register.
        """ 
        prototype = None # Acceptance scheme
        for r in EntryRecipeDb.iteritems():
            if   prototype is None:       prototype = r.accepter
            elif r.accepter == prototype: continue
            # None => acceptance must be taken from 'aux_acceptance'
            return None

        # All acceptance schemes where the same => Overtake the prototype
        return prototype
    
    @classmethod
    def _interfere_input_position_storage(cls, EntryRecipeDb):
        """Each position register is considered separately. If for one register 
        the offset differs, then it can only be determined from storing it in 
        this mouth state and restoring it later.
        """
        # Determine the set of involved input position registers
        iterable = flatten_it_list_of_lists(
                      recipe.ip_offfset_db.iterkeys() 
                      for recipe in EntryRecipeDb.itervalues())    

        ip_offset_db = {}
        for register_id in register_id_set:
            # If there are two entries with differing offsets, then input
            # position must be reset by register restore. Then 'offset = None'.
            # In the homogeneous case, the offset is the one that all entries
            # share..
            prototype = None
            for recipe in EntryRecipeDb.itervalues():
                offset = recipe.ip_offset_db.get(register_id)
                if   prototype is None:   prototype = offset
                elif offset == prototype: continue
                # Inhomogeneity detected -> let input position be stored.
                prototype = None
                break
            ip_offset_db[register_id] = prototype

        return ip_offset_db
        
    def get_Entry(self, mouth):
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

    @staticmethod 
    def get_linear_Entry(self, linear):
        return {}

    @staticmethod 
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
            accepter         = Op.Accepter()
            accepter.content = AccepterContent.from_iterable(r.accepter))
            assert not entry_db[from_si].has_command_id(E_Op.Accepter) 
            entry_db[from_si].append(accepter)

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
        txt = [ "Accepter:\n" ]
        # For acceptance the sequence matters
        for x in self.accepter:
            txt.append("   AccId: %s; RestoreReg: %s;\n" % (x.acceptance_id, x.position_register))
        txt.append("InputOffsetDb:\n")
        for register, offset in sorted(self.ip_offset_db.iteritems()):
            txt.append("    [%s]: %s\n" % (register, offset))
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
