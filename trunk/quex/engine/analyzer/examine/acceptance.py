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
                            E_IncidenceIDs, \
                            E_R


class RecipeAcceptance(Recipe):
    """Recipe tells what pattern wins (i.e. what its pattern id is), under what
    condition, and where the input pointer needs to be set. This information is
    stored in two data structures.

      .accepter:  

         A list of pre-context pattern-id pairs. That is something like

              [  (pre-context-id 6, acceptance-id 12),
                 (pre-context-id 4, acceptance-id 11),
                 ....
                 (No pre-context,   acceptance-id 14),
              ]

        which tells in a prioritized way what to accept under what condition.
        The first pre-context that is fulfilled determines the pattern id of
        the winning pattern. Consequently, any entry after the conditionless
        acceptance is meaningless.
        
        acceptance-id is None => acceptance is restored from the auxiliary register
                                 for acceptance. In that case, the pre-context must 
                                 be 'None', too.
                                 
      .ip_offset_db:
          
              position register id   -->   offset

        Input position must be determined by
              
              if offset is not None: input_p += offset
              else:                  input_p  = aux_register[position register id] 

    The 'aux_register' values are set during interference in mouth states.
    """
    __slots__         = ("accepter", "ip_offset_db", "snapshot_map")
    RestoreAcceptance = SeAccept(E_IncidenceIDs.RESTORE_ACCEPTANCE, E_PreContextIDs.NONE)

    def __init__(self, Accepter, IpOffsetDb, SnapshotMap):
        assert type(IpOffsetDb) == dict
        assert type(Accepter)   == list

        # Parameters of the recipe.
        self.accepter     = Accepter
        self.ip_offset_db = IpOffsetDb

        # snapshot map: register id --> snapshot state
        #               
        # The snapshot map tells to what state the snapshot of the variable given
        # by 'variable_id' has been made.
        self.snapshot_map = SnapshotMap

    @classmethod
    def undetermined(cls, RequiredVariableSet):
        """The 'undetermined' recipe for dead-lock resolution (see [DOC]).
        """
        accepter = [ cls.RestoreAcceptance ]

        for variable_id in RequiredVariableSet:
            if type(variable_id) != tuple: continue
            ip_offset_db[variable_id] = None     # position[i] = Aux(position[i])

        for variable_id in RequiredVariableSet:
            snapshot_map[variable_id] = None     # That is: 'sigma' in [DOC]

        return RecipeAcceptance(accepter, ip_offset_db, snapshot_map)

    @staticmethod
    def get_required_variable_superset_db(sm, StateIndex, PredecessorDb, SuccessorDb):
        """RETURNS: A superset of the required registers for a given state. 
        
        According to [DOC], it is admissible to return a SUPERSET of what is
        required, which is what happens! 

        The acceptance register is required in any state, since one needs to know
        what pattern wins. A position register can only be important after it has
        received an assignment. Thus, the set of successor states of a state where
        the input position is stored in a register 'X' is a superset of the states
        that require 'X'.

        OVERHEAD ANALYSIS: 

        Overhead appears only with respect to position registers.  It is
        conceivable, that after a position for pattern 'X' has been stored, a
        branch is taken that does not have an acceptance of pattern 'X'. If it
        hits a mouth state, an unused entry action may occur. Otherwise, it 
        has not impact. 
        
        The fact that the branch exists, however, tells that there is another
        pattern must exist that starts with the pattern 'X' (before its
        post-context starts). To hit a mouth state, a third pattern must be involved
        with the same requirement. For example something like

                    1:  [a-z]+/":"
                    2:  [a-z]+":"[a-z]
                    3:  [a-z]+":otto"

        would be such a case. So, ":" would be a delimiter for words, and then
        in second pattern and third pattern, it would not. This seems strange,
        to the author of this code. In any case, the impact would be most
        likely unmeasurable. While the identification of the patterns take lots
        of comparisons, the additional entry operation only appears when
        pattern 3 terminates (after 'otto') and the transition branches into
        the pattern 2 (to match an identifier consisting of letters).
        """
        # Acceptance is always necessary. It must be clear what pattern matched.
        always_necessary = set([
            E_R.AcceptanceRegister,
            (E_R.PositionRegister, E_IncidenceIDs.MATCH_FAILURE)
        ])

        # Enter for each the absolute necessities
        result_db = dict(
            (si, copy(always_necessary)) for si in SM.states.iterkeys()
        )

        # Superset upon 'store-input position':
        #
        # If a state stores the input position in a register, then any state
        # which it may reach is subject to its requirement. 
        #
        for si, state in SM.states.iteritems():
            for cmd in single_entry.get_iterable(SeStoreInputPosition):
                variable_id = (E_R.PositionRegister, cmd.acceptance_id())
                result[si].add(variable_id)
                for successor_si in SuccessorDb[si]:
                    result[successor_si].add(variable_id)

        return result_db

    @classmethod
    def accumulation(cls, PrevRecipe, CurrSingleEntry):
        """RETURNS: Recipe =     concatenation of 'Recipe' 
                             and relevant operations of 'SingleEntry'.
        """
        accepter     = cls._accumulate_acceptance(PrevRecipe, CurrSingleEntry)
        ip_offset_db = cls._accumulate_input_pointer_storage(PrevRecipe, CurrSingleEntry)

        return RecipeAcceptance(accepter, ip_offset_db, PrevRecipe.snapshot_map)
        
    @classmethod
    def interference(cls, Mouth):
        """Determines 'mouth' by 'interference'. That is, it considers all entry
        recipes and observes their homogeneity. 

        ADAPTS:  StateInfo.implement_entry_operation_db
        
        RETURNS: Recipe.

        The undetermined registers are those, that need to be computed upon
        entry, and are restored from inside the recipe.
        """
        snapshot_map, \
        homogeneity_db = cls._snap_shot_map_interference(Mouth)

        # Acceptance
        accepter = cls._interfere_acceptance(snapshot_map, 
                                             homogeneity_db, 
                                             Mouth.entry_recipe_db)

        # Input position storage
        ip_offset_db = cls._interfere_input_position_storage(snapshot_map, 
                                                             homogeneity_db,
                                                             Mouth.entry_recipe_db, 
                                                             Mouth.required_variable_set)

        return RecipeAcceptance(accepter, ip_offset_db, snapshot_map), homogeneity_db

    @staticmethod
    def _accumulate_acceptance(PrevRecipe, CurrEntry):
        """Longest match --> later acceptances have precedence. The acceptance
        scheme of the previous recipe comes AFTER the current acceptance scheme.
        An unconditional acceptance makes any later acceptance check superfluous.
        """ 
        assert PrevRecipe.accepter

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
            if PrevRecipe.accepter:
                accepter.extend(PrevRecipe.accepter)

        assert accepter
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
    def _interfere_acceptance(cls, snapshot_map, homogeneity_db, EntryRecipeDb):
        """If the acceptance scheme differs for only two recipes, then the 
        acceptance must be determined upon entry and stored in the LastAcceptance
        register.

        ADAPTS: homogeneity_db

        RETURN: [0] Accumulated 'accepter'
        """ 
        # Interference requires determined entry recipes.
        assert none_is_None(EntryRecipeDb.itervalues())

        if not homogeneity_db[E_R.AcceptanceRegister]:
            return [ cls.RestoreAcceptance ]

        accepter = UniformObject.from_iterable(
                               recipe.accepter
                               for recipe in EntryRecipeDb.itervalues()).plain_content()

        if accepter != E_Value.VOID:
            # Homogeneity
            pass
        else:
            # Inhomogeneity
            accepter = [ cls.RestoreAcceptance ]
            cls.apply_inhomogeneity(snapshot_map, homogeneity_db, 
                                    E_R.AcceptanceRegister)

        return accepter

    @classmethod
    def _interfere_input_position_storage(cls, homogeneity_db, EntryRecipeDb, RequiredVariableSet):
        """Each position register is considered separately. If for one register 
        the offset differs, then it can only be determined from storing it in 
        this mouth state and restoring it later.
        """
        ip_offset_db = {}
        for variable_id in RequiredVariableSet:
            if type(variable_id) != tuple: continue

            offset = UniformObject.from_iterable(
                         recipe.ip_offset_db.get(RegisterId)
                         for recipe in RecipeList).plain_content()

            if offset != E_Value.VOID: 
                # Homogeneity
                pass
            else:
                # Inhomogeneity
                offset = None
                cls.apply_inhomogeneity(snapshot_map, homogeneity_db, variable_id)

            ip_offset_db[variable_id] = offset

        return ip_offset_db
        
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
        txt = [ "    Accepter:\n" ]
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
