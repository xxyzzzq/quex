from quex.engine.analyzer.examine.recipe_base import Recipe

class RecipeAcceptance(Recipe):
    """Base class for SCR recipes. The general recipe depends on:

        -- The current state.
        -- Constants which can be pre-determined.
        -- Register contents which are developed at run-time.

    See 00-README.txt the according DEFINITION.
    """
    SCR = (E_R.InputP, E_R.Acceptance, E_R.PositionRegister)
    def __init__(self):
        self.accept_sequence   = []
        self.storage_offset_db = {}

    @staticmethod
    def from_accumulation(Recipe, SingleEntry):
        """RETURNS: Recipe = concatination of 'Recipe' + relevant operations of
                             'SingleEntry'.
        """
        accept_sequence = []
        # Longest match --> later acceptances have precedence. The current 
        # acceptances are the once which came last, at this point.
        for cmd in sorted(SingleEntry.get_iterable(SeAccept), 
                          key=lambda x: x.acceptance_id()):
            accept_sequence.append
            if not cmd.pre_context_f(): break
        else:
            # No unconditional acceptance occurred, the previous acceptances
            # remain important.
            accept_sequence.extend(Recipe.accept_sequence)

        # Storage into a register overwrites previous storages
        # Previous storages receive '.offset - 1'
        storage_offset_db = dict( 
            (register_id, position_offset - 1)
            for register_id, position_offset in Recipe.storage_offset_db.iteritems()
        )
        for cmd in SingleEntry.get_iterable(SeStoreInputPosition): 
            storage_offset_db[cmd.register_id()] = 0

        return RecipeAcceptance(accept_sequence, storage_offset_db)

    @staticmethod
    def from_interference(RecipeIterable):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes actions at different entries into a MouthState.
        """
        # If a single acceptance differs, then the acceptance need to be stored
        # upon entry.
        prototype = None
        for recipe in RecipeIterable:
            if   prototype is None:                   prototype = recipe.accept_sequence
            elif recipe.accept_sequence == prototype: continue
            restore_acceptance_f = True
            break

        # If a single offset differs, then it needs to be stored away.
        register_iterable = flatten_list_of_lists(
            recipe.storage_offset_db.keys()
            for recipe in RecipeIterable
        )
        for register_id in register_id_iterable:
            prototype = None
            for recipe in RecipeIterable:
                offset = recipe.storage_offset_db.get(register_id)
                if   prototype is None:   prototype = offset
                elif offset == prototype: continue
                restore_from_register_set.add(register_id)

        entry_db = self.determine_interfered_entry_db(RecipeIterable, 
                                                      restore_from_register_set,
                                                      restore_acceptance_f)

        return AcceptanceRecipe(restore_acceptance_f, restore_from_register_set)




    @staticmethod
    def from_interference_in_dead_lock_group(DeadLockGroup):
        """RETURNS: An accumulated action that expresses the interference of 
                    recipes of states of a dead_lock group.
        """
        assert False

    def get_drop_out_OpList(self):
        """With a given Recipe(i) for a state 'i', the action upon state machine
        exit can be determined.

        RETURNS: A OpList that corresponds self.
        """
        assert False
    
    def get_entry_OpList(self, NextRecipe):
        """Consider the NextRecipe with respect to self. Some contents may 
        have to be stored in registers upon entry into this state. 

        RETURNS: A OpList that allows 'InterferedRecipe' to operate after 
                 the state.

        This is particularily important at mouth states, where 'self' is an 
        entry into the mouth state and 'NextRecipe' is the accumulated action
        after the state has been entered.
        """
        assert False
    

