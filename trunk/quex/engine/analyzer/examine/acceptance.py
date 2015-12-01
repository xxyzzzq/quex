from quex.engine.analyzer.examine.recipe_base import Recipe
from quex.engine.operations.se_operations     import SeAccept, \
                                                     SeStoreInputPosition
from quex.engine.misc.tools                   import flatten_it_list_of_lists, \
                                                     UniformObject, \
                                                     E_Values, \
                                                     none_is_None

from quex.blackboard import E_PreContextIDs, \
                            E_IncidenceIDs, \
                            E_R

from copy import copy
from collections import defaultdict

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

        But, there must be an acceptance associated to no pre-context. So, it 
        follows, that the last acceptance in the list MUST be 'un-pre-contexted'.

        Input position must be determined by
              
              if offset is not None: input_p += offset
              else:                  input_p  = aux_register[position register id] 

    The 'aux_register' values are set during interference in mouth states.
    """
    __slots__         = ("accepter", "ip_offset_db", "snapshot_set_db")
    RestoreAcceptance = SeAccept(E_IncidenceIDs.RESTORE_ACCEPTANCE, E_PreContextIDs.NONE)

    def __init__(self, Accepter, IpOffsetDb, SnapshotSetDb):
        assert type(IpOffsetDb) == dict
        assert type(Accepter)   == list

        # Parameters of the recipe.
        self.accepter     = Accepter
        self.ip_offset_db = IpOffsetDb

        # snapshot set db: register id --> states that MUST store register id
        #                                  in auxiliary variable
        #               
        self.snapshot_set_db = SnapshotSetDb

    @classmethod
    def NULL(cls, RequiredVariableSet):
        """A recipe that does absolutely nothing. It is used for the sole 
        purpose to generate a recipe from a history-independent operation op(i)
        by accumulation, i.e. R = op(i) o NULL.
        """
        ip_offset_db = dict(
            #__________________________________________________________________
            # 'offset = 1', so that accumulation develops 'offset = 0' as entry
            # recipe.
            #__________________________________________________________________
            (variable_id[1], 1)
            for variable_id in RequiredVariableSet if type(variable_id) == tuple
        )
        return RecipeAcceptance([], ip_offset_db, defaultdict(set))

    @classmethod
    def INITIAL(cls, RequiredVariableSet):
        """The initial recipe matches 'failure'. As long as no other pattern 
        matches, the result is that.
        """
        accepter = [
            SeAccept(E_IncidenceIDs.MATCH_FAILURE)
        ]
        ip_offset_db = {
            #__________________________________________________________________
            #
            # SPECIAL CASE: Entry from 'before entry': 
            #   
            #             The input pointer is not incremented! 
            #            
            # Thus, the standard accumulation of this class would illegally
            # decrement 'ip_offset_db[CONTEXT_FREE_MATCH]' when the composition
            #
            #                        op(i) o R(init)
            #
            # is computed. Thus, 'ip_offset_db[CONTEXT_FREE_MATCH]' is set to 1
            # so that decrementing produces the correct position '0' upon entry
            # into the initial state.
            #__________________________________________________________________
            E_IncidenceIDs.CONTEXT_FREE_MATCH: 1,
        }

        # The initial recipe cannot rely on stored values!
        snapshot_set_db = defaultdict(set)

        return RecipeAcceptance(accepter, ip_offset_db, snapshot_set_db)

    @classmethod
    def UNDETERMINED(cls, RequiredVariableSet):
        """The 'undetermined' recipe for dead-lock resolution (see [DOC]).
        """
        snapshot_set_db = dict(        
            (variable_id, E_Values.SIGMA)        # SIGMA = something that is never
            #                                    #         equal to anything else
            #                                    #         -- not even another SIGMA.
            for variable_id in RequiredVariableSet
        )

        accepter = [ 
            cls.RestoreAcceptance 
        ]

        ip_offset_db = dict(
            (variable_id[1], E_Values.RESTORE)   # position[i] = Aux(position[i])
            for variable_id in RequiredVariableSet
            if type(variable_id) == tuple
        )

        return RecipeAcceptance(accepter, ip_offset_db, snapshot_set_db)

    @classmethod
    def get_required_variable_superset_db(cls, SM, PredecessorDb, SuccessorDb):
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
        result = defaultdict(set)

        # Acceptance is always necessary. It must be clear what pattern matched.
        # Add states are 
        cls.tag_iterable(result, SM.states.iterkeys(), E_R.AcceptanceRegister)
        cls.tag_iterable(result, SM.states.iterkeys(),
                           (E_R.PositionRegister, E_IncidenceIDs.CONTEXT_FREE_MATCH))

        # Superset upon 'store-input position':
        #
        # If a state stores the input position in a register, then any state
        # which it may reach is subject to its requirement. 
        #
        # Acceptance:
        for si, cmd in cls.cmd_iterable(SM, SeAccept):
            # All states are already tagged with 'position register' CONTEXT_FREE_MATCH'
            if cmd.position_register_id() == E_IncidenceIDs.CONTEXT_FREE_MATCH:
                continue
            variable_id = (E_R.PositionRegister, cmd.position_register_id()) 
            result[si].add(variable_id)
            cls.tag_iterable(result, SuccessorDb[si], variable_id)

        # Position Register:
        for si, cmd in cls.cmd_iterable(SM, SeStoreInputPosition):
            variable_id = (E_R.PositionRegister, cmd.position_register_id()) 
            result[si].add(variable_id)
            cls.tag_iterable(result, SuccessorDb[si], variable_id)

        return result

    @classmethod
    def accumulation(cls, PrevRecipe, CurrSingleEntry):
        """RETURNS: Recipe =     concatenation of 'Recipe' 
                             and relevant operations of 'SingleEntry'.
        """
        assert False, "Currently unused"
        #accepter     = cls._accumulate_acceptance(PrevRecipe, CurrSingleEntry)
        #ip_offset_db = cls._accumulate_read_pointer_storage(PrevRecipe, CurrSingleEntry)

        ## Filter out those entries in the snapshot map, where the recipe does 
        ## no longer rely on stored entries.
        #snapshot_set_db = cls.snapshot_set_db_filtered_clone(snapshot_set_db, accepter, ip_offset_db)

        #return RecipeAcceptance(accepter, ip_offset_db, snapshot_set_db)
        
    @classmethod
    def interference(cls, Mouth, StateIndex):
        """Determines 'mouth' by 'interference'. That is, it considers all entry
        recipes and observes their homogeneity. 

        ADAPTS:  StateInfo.implement_entry_operation_db
        
        RETURNS: Recipe.

        The undetermined registers are those, that need to be computed upon
        entry, and are restored from inside the recipe.
        """
        assert False, "currently unused"
        # snapshot_set_db = SnapshotSetDb.from_mouth(Mouth)

        ## Acceptance
        #accepter = cls._interfere_acceptance(snapshot_set_db, 
        #                                     Mouth.entry_recipe_db, 
        #                                     StateIndex)

        ## Input position storage
        #ip_offset_db = cls._interfere_read_position_storage(snapshot_set_db, 
        #                                                     Mouth.entry_recipe_db, 
        #                                                     Mouth.required_variable_set, 
        #                                                     StateIndex)

        #return RecipeAcceptance(accepter, ip_offset_db, snapshot_set_db)

    @staticmethod
    def _accumulate_acceptance(PrevRecipe, SingleEntry):
        """Longest match --> later acceptances have precedence. The acceptance
        scheme of the previous recipe comes AFTER the current acceptance scheme.
        An unconditional acceptance makes any later acceptance check superfluous.
        """ 
        def sort_key(Cmd):
            """MATCH_FAILURE *must* always have the lowest precedence!"""
            acceptance_id = Cmd.acceptance_id()
            if acceptance_id == E_IncidenceIDs.MATCH_FAILURE: return -1
            assert isinstance(acceptance_id, long)
            return acceptance_id

        accepter = []
        for cmd in sorted(SingleEntry.get_iterable(SeAccept), key=sort_key, 
                          reverse=True):
            accepter.append(cmd)
            if cmd.pre_context_id() == E_PreContextIDs.NONE: 
                # Unconditional acceptance overrules all later acceptances.
                break
        else:
            # No unconditional acceptance occurred, the previous acceptances
            # must be appended. 
            # The NULL recipe cannot appear here, because it is only to be applied
            # in composition with history-independent operations which MUST have
            # an '.accepter' that accepts condition-less.
            assert PrevRecipe.accepter
            accepter.extend(PrevRecipe.accepter)

        # There MUST be an accepter as a result; at least 'MATCH_FAILURE'.
        assert accepter 
        # No element before the last can be condition-less.
        assert not any(x.pre_context_id() == E_PreContextIDs.NONE for x in accepter[:-1])
        # The last element of the accepter MUST be condition-less.
        assert accepter[-1].pre_context_id() == E_PreContextIDs.NONE

        return accepter

    @staticmethod
    def _accumulate_read_pointer_storage(PrevRecipe, CurrSingleEntry):
        """Storing the current input position into a register overwrites 
        previous storage operations. Previous storage operations that appear
        'n' steps before can be compensated by 'input_p -= n'. Thus, at
        each step '-1' is added to the compensation offset. 
        
        NOTE: Registers which do not appear in the 'ip_offset_db' are meant
        to be restored from registers. They cannot be computed by offset 
        addition. 
        """
        assert none_is_None(PrevRecipe.ip_offset_db.itervalues())

        def new_offset(PrevOffset):
            if PrevOffset is E_Values.RESTORE: return E_Values.RESTORE
            assert isinstance(PrevOffset, (int, long)), \
                   "Expected previous offset as number; found %s" % str(PrevOffset)
            return PrevOffset - 1

        # Storage into a register overwrites previous storages
        # Previous storages receive '.offset - 1'
        ip_offset_db = dict( 
            (register_id, new_offset(offset))
            for register_id, offset in PrevRecipe.ip_offset_db.iteritems()
        )

        # Storing the input position means, that the stored value differs
        # from the current value by '0'.
        ip_offset_db.update(
            (cmd.position_register_id(), 0)
            for cmd in CurrSingleEntry.get_iterable(SeStoreInputPosition)
        )

        # Any acceptance that does not restore from a position register
        # defines the current position as the point where the input pointer
        # needs to be reset upon acceptance.
        ip_offset_db.update(
            (cmd.position_register_id(), 0)
            for cmd in CurrSingleEntry.get_iterable(SeAccept)
            if not cmd.restore_position_register_f()
        )

        assert none_is_None(ip_offset_db.itervalues())
        return ip_offset_db

    @classmethod
    def _interfere_acceptance(cls, snapshot_set_db, EntryRecipeDb, StateIndex):
        """If the acceptance scheme differs for only two recipes, then the 
        acceptance must be determined upon entry and stored in the LastAcceptance
        register.


        RETURN: [0] Accumulated 'accepter'
        """ 
        # Interference requires determined entry recipes.
        assert none_is_None(EntryRecipeDb.itervalues())

        # Irrelevant E_R.AcceptanceRegister? Impossible! Acceptance is relevant
        # for all states! '.accepter is None' is not treated.
        accepter = UniformObject.from_iterable(
                               recipe.accepter
                               for recipe in EntryRecipeDb.itervalues()).plain_content()

        if accepter != E_Values.VOID:
            # Homogeneity
            pass
        else:
            # Inhomogeneity
            accepter = [ cls.RestoreAcceptance ]
            snapshot_set_db[E_R.AcceptanceRegister] = set([StateIndex])

        assert accepter and accepter[-1].pre_context_id() == E_PreContextIDs.NONE
        return accepter

    @classmethod
    def _interfere_read_position_storage(cls, snapshot_set_db, EntryRecipeDb, 
                                          RequiredVariableSet, StateIndex):
        """Each position register is considered separately. If for one register 
        the offset differs, then it can only be determined from storing it in 
        this mouth state and restoring it later.
        """
        assert none_is_None(
                  flatten_it_list_of_lists(recipe.ip_offset_db.itervalues()
                                           for recipe in EntryRecipeDb.itervalues()))

        ip_offset_db = {}
        for variable_id in RequiredVariableSet:
            if type(variable_id) != tuple: continue
            register_id = variable_id[1]

            # Irrelevant position register? Possible! A recipe that considers 
            # a position register irrelevant is 'equal' to any other. Thus, it
            # can be filtered out. Irrelevant position register is not mentioned
            # in 'ip_offset_db' => 'offset = None'.
            offset_list = [
                  recipe.ip_offset_db.get(register_id)
                  for recipe in EntryRecipeDb.itervalues()
            ]
            offset = UniformObject.from_iterable(
                      x for x in offset_list if x is not None).plain_content()

            if offset != E_Values.VOID: 
                # Homogeneity
                pass
            else:
                # Inhomogeneity
                offset = E_Values.RESTORE
                snapshot_set_db[variable_id] = set([StateIndex])

            ip_offset_db[register_id] = offset

        assert none_is_None(ip_offset_db.itervalues())
        return ip_offset_db
        
    @staticmethod
    def snapshot_set_db_filtered_clone(snapshot_set_db, Accepter, IpOffsetDb):
        """Take those entries out of the snapshot map, where the recipe does
        not rely on stored values.
        """
        assert False, "currently unused"
        # db = defaultdict(set)
        #
        # # (*) Input position storage / offset
        # db.update(
        #     (variable_id, copy(snapshot_set))
        #     for variable_id, state_index in snapshot_set_db.items()
        #     # 'variable_id[1]' = position register
        #     if     type(variable_id) == tuple \
        #        and IpOffsetDb.get(variable_id[1]) != E_Values.RESTORE
        # )
        #
        # # (*) The 'RESTORE_ACCEPTANCE' must always be the last in the accepter,
        # #     because it does not depend on a pre-context.
        # assert Accepter
        # if Accepter[-1].acceptance_id() == E_IncidenceIDs.RESTORE_ACCEPTANCE:
        #     db[E_R.AcceptanceRegister] = copy(snapshot_set_db[E_R.AcceptanceRegister])
        # 
        # return db

    @staticmethod
    def get_string_accepter(Accepter):
        txt = []
        for x in Accepter:
            if x.pre_context_id() != E_PreContextIDs.NONE:
                txt.append("      pre%s => %s\n" % (x.pre_context_id(), x.acceptance_id())) 
            else:
                txt.append("      %s\n" % x.acceptance_id())
        return "".join(txt)

    @staticmethod
    def get_string_input_offset_db(IpOffsetDb):
        txt = []
        for register_id, offset in sorted(IpOffsetDb.iteritems()):
            if offset is not None:
                txt.append("      [%s] offset: %s\n" % (register_id, offset))
            else:
                txt.append("      [%s] restore!\n" % repr(register_id))
        return "".join(txt)

    @staticmethod
    def get_string_snapshot_set_db(SnapshotSetDb):
        if not SnapshotSetDb:
            return ""

        txt = []
        L = max(len("%s" % repr(register)) for register in SnapshotSetDb)
        for register, state_index_set in sorted(SnapshotSetDb.iteritems()):
            if not state_index_set: continue
            txt.append("      %s%s@" % (repr(register), " " * (L-len("%s" % repr(register)))))
            state_index_list = sorted(list(state_index_set))
            txt.append("".join("%s, " % si for si in state_index_list[:-1]))
            txt.append("%s\n" % state_index_list[-1])
        
        return "".join(txt)

    def __str__(self):
        snapshot_set_db_empty_f = True
        for state_index in self.snapshot_set_db.itervalues():
            if state_index is not None: snapshot_set_db_empty_f = False

        return "".join([
            "    Accepter:\n",
            self.get_string_accepter(self.accepter),
            "    InputOffsetDb:\n",
            self.get_string_input_offset_db(self.ip_offset_db),
            "    Snapshot Map:\n" if not snapshot_set_db_empty_f else "",
            self.get_string_snapshot_set_db(self.snapshot_set_db)
        ])

    
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
