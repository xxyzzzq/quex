# (C) 2010 Frank-Rene Schaefer
"""
   Barren Tree Compression _____________________________________________________
   
   The goal of barren tree compression is to be able to express parts of the
   state machine directly as nested if-then clauses--without the need of 
   explicit state transitions (i.e. gotos). For example, a state machine that
   identifies the keywords 'move' and 'mode' as well as the identifiers matching
   the regular expression [a-z]+ should be written as


      /* Something that identifies 'm' */
      ...

      /* Barren tree to check for 'ove', 'ode' and identifier. */
BARREN_TREE_ROOT_0:
      ++input_p;
      if( *input_p == 'o' ) { 
          ++input_p;
          if( *input_p == 'd' ) { 
              ++input_p;
              if( *input_p == 'e' ) { 
                  ++input_p;
                  goto TERMINAL_MODE;
              }
          }
          else if( *input_p == 'v' ) { 
              ++input_p;
              if( *input_p == 'e' ) { 
                  ++input_p;
                  goto TERMINAL_MOVE;
              }
          }
      }
      if( *input_p in [a-z] ) { 
          goto CHECK_IDENTIFIER;
      }
      if( *input_p == BufferLimitCode ) { 
          reload(...);
          goto __InitialState;
      }
      else { 
          goto TERMINAL_IDENTIFIER;
      }

CHECK_IDENTIFIER:
      ++input_p;
      if( *input_p >= 'a' && *input_p <= 'z' ) { 
          goto TERMINAL_IDENTIFIER;
      }
      goto TERMINAL_IDENTIFIER;
      
   Note, that the detection of 'm' cannot be part of the barren tree, since for
   if the lexeme does not start with 'm' and is not in [a-z] and not the buffer
   limit code, then it is a failure. For the barren tree above the state
   machine transits to success for IDENTIFIER.


   Requirements for a state to be part of a barren tree ________________________

       Transition to state requires less then N comparisons
       (N=2 is may be the best for checking just one range.)

   Result of Analyzis __________________________________________________________

       A barren tree is a set of states organized as a tree. A tree_node
       contains:

            barren_transition_map[target_index] --> trigger_set 

                This is the list of all transition to subsequent states
                that can be reached by a 'barren' transition, i.e. a very
                tiny trigger set.

            fat_transition_map[target_index] --> trigger_set

                Remaining transitions that are not considered to be 
                'barren'.

            drop_out_info

                Information about 'drop-out' behavior.

      All nodes of the barren tree are accessible via a dictionary, i.e.

            tree_db[state_index] --> tree_node

   _____________________________________________________________________________
"""
from quex.core_engine.interval_handling import NumberSet

class MatchInfo:
    """An object of this class describes the 'relationship' between
       a state A (the 'parent') and a state B (the 'child') where 
       there are transitions from A to B. That means, that B can
       potentially be nested into A.

       The decision about nesting B into A is based on how much of 
       the transition map of B can be caught by A's transition map.
       For example:

        STATE_A:                   STATE_B:
                                                     
           if *p == 'm':              if *p == 'z':
               goto STATE_B;              goto 4712;
           if *p in [a-ln-z]:         if *p in [a-y]:
               goto 4711;                 goto 4711;

        Can be transformed into:

           if *p == 'm':         # From STATE_A
              ++p;
              if *p == 'z':      # From STATE_B
                  goto 4712;
           if *p in [a-z]:       # Common remainder for both, provided
              goto 4711;         # that 'm' and 'z' are checked before.

        Potentially, there might be open wildcards from trigger ranges
        that appear in A and B. This object contains:

            -- common catch map.

            -- wildcard trigger map.
    """
    def __init__(self, ParentTM, ParentWC, ChildTM):
        """ParentTM -- Parent State Trigger Map
           ParentWC -- Parent's Wild Cards, that is the trigger set
                       where the parent state transits to nested child
                       states. The Catch Clause can be modified so that
                       it adapts to the requirements of child states.
           ChildTM  -- Child State Trigger Map
        """
        assert type(ParentTM) == dict
        assert type(ParentWC) == NumberSet
        assert type(ChildTM) == dict

        # Compute difference in transition maps
        #     --> table: [trigger_set, target state in skeleton, target state in candidate]
        only_in_A    = NumberSet()
        only_in_B    = NumberSet()
        diff_in_both = NumberSet()

        for A_target_index, A_trigger_set in A.items():
            # If B does not trigger to the A_target_index at all, then the
            # transition 'A_trigger_set --> A_target_index' is **only** in A.
            if B.has_key(target_index) == False:
                only_in_A.unite_with(A_trigger_set)
                continue

            # Collect triggers where A and B trigger to the same target index
            # on different triggers. Symmetric difference = what is either in A
            # or in B but not in both.
            delta_set = B[A_target_index].symmetric_difference(A_trigger_set)
            if not delta_set.is_empty(): 
                diff_in_both.unite_with(delta_set)
                continue

        for B_target_index, B_trigger_set in B.items():
            # If A does not trigger to B_target_index at all, then the
            # transition 'B_trigger_set --> B_target_index' is **only** in B.
            if A.has_key(target_index) == False:
                only_in_B.unite_with(B_trigger_set)
                continue

        return only_in_A, only_in_B, diff_in_both

class Info:
    """Note: The path.CharacterPath class a lot in common with the Info.

       The transitions of a state are categorized into 'barren' and 'fat'.

       -- A barren transition is a transition to subsequent state on the 
          bases of very few comparisons with respect to the input.

       -- Also, the state to which the barren transition triggers must
          fit, i.e. its 'fat transitions' and drop-out action must
          correspond.

       A transition that is not barren is fat.
    """
    def __init__(self, State, FatTransitionMap, BarrentTransitionMap):
        assert isinstance(StartStateIndex, long)
        assert isinstance(FatTransitionMap, dict)

        self.__state  = State

        # Transitions: target_index --> trigger set that triggers to target
        #    barren transitions: transitions on small sets to small fitting states.
        #    fat transitions:    remainder of transitions.
        self.__barren = BarrenTransitionMap
        self.__fat    = FatTransitionMap

        # The trigger sets of 'barren' transitions can be occupied by 
        # arbitrary values, let them be called 'wildcards'.
        trigger_set = NumberSet()
        for trigger_set in self.__barren.values():
            self.__wildcard_set.unite_with(trigger_set)

    def barren(self):
        return self.__barren

    def fat(self):
        return self.__fat

    def move_to_fat(self, TargetIndex):
        """Moves a transition to TargetIndex from the set of barren
           transitions to the set of 'fat' transitions.
        """
        assert self.__barren.has_key(TargetIndex)

        trigger_set = self.__fat.get(TargetIndex)
        if trigger_set == None: self.__fat[TargetIndex] = self.__barren[TargetIndex]
        else:                   trigger_set.unite_with(self.__barren[TargetIndex])

        del self.__barren[TargetIndex]

    def plug_wildcards(self, WildcardMap):
        """The given wildcards become part of the fat transitions."""
        for target_index, trigger_set in WildcardMap.items():
            fat_trigger_set = self.__fat.get(target_index)
            if fat_trigger_set == None: self.__fat[target_index] = trigger_set
            else:                       fat_trigger_set.unite_with(trigger_set)

            self.__wildcard_set.subtract(trigger_set)

    def match(self, CandidateFatTransitionMap, CandidateBarrenTriggerSet):
        """-- The candidate **needs** all transitions in the fat transition map
              in case that no one of its sub-trees is concerned. 

           -- The Tree **can** provide the 'skeleton' transition map and can
              extend the map characters in the wildcard set.

           RETURNS: NumberSet --> Characters from the wild card that need to be used to 
                                  achieve the match. Match is good.
                    empty set --> No wildcard necessary, but match is good.
                    None      --> No match possible.
        """
        # All transitions in the FatTransitionMap must appear in the Skeleton
        #
        #     [     5     ][2]     [    3    ][ 1 ]              skeleton
        #                   *                 *****              wildcard set
        #
        #     [     5     ][6]     [    3    ]     [    6     ]  candidate FAIL
        #     [     5     ][6]     [    3         ]              candidate OK
        #     [     5     ][1]     [    3         ]              candidate OK
        #
        #     -- except for those covered by the wildcards.
        only_in_A, \
        only_in_B, \
        diff_in_both      = \
                get_metric(self.__fat, CandidateFatTransitionMap)

        # (1) what is in self's 'fat' but not in candidate's 'fat transition' 
        #     can **only** be covered by barren transitions of candidate.
        if not only_in_A.is_empty():
            if not CandidateBarrenTriggerSet.is_superset(only_in_A): return None

        # (2) If self and candidate transit to different states on the same trigger set, then
        #     They can only be covered by barren trigger sets of the candidate.
        if not diff_in_both.is_empty():
            if not CandidateFatTransitionMap.is_superset(diff_in_both): return None

        # (3) what is in candidate's 'fat' but not in self's 'fat transition' 
        #     can **only** be covered by wildcards.
        used_wildcard_set = NumberSet()
        if not only_in_B.is_empty():
            if not self.__wildcard_set.is_superset(diff_in_both): return None
            # Take the reference to 'only_in_B' to avoid object creation
            used_wildcard_set = only_in_B
            used_wildcard_set.intersect_with(self.__wildcard_set)

        return used_wildcard_set

def categorize(SM, MaxComparisonN):
    # A state can only be absorbed by one other state.
    # => book keeping about each state that has been absorbed already.
    done_set = set([])

    tree_db  = {}
    # Here, the loop determines the sequence of processing, therefore 
    # determines the **priorization** of where states are absorbed. States that
    # come first, can absorb a subsequent state, later states **must** transit
    # to the subsequent state.
    for state_index, state in SM.items():
        barren, fat = categorize_transitions(State, MaxComparisonN)
        for target_index, trigger_set in barren.items():
            if target_index in done_set: 
                # Move transition to 'fat transitions'
                fat[target_index] = trigger_set
                del barren[target_index]
            else:
                done_set.add(target_index)

        if barren.is_empty(): barren = None
        tree_db[state_index] = TreeBase(state, fat, barren)

    # Barren transitions to states which misfit become part of the fat transitions.
    info_changed_f = False
    while 1 + 1 == 2:

        for state_index, info in sorted(tree_db.items(), my_sort):

            transition_change_f = False
            while 1 + 1 == 2:

                backup = info.wildcard_set()

                for target_index, trigger_set in info.barren_transition_map():
                    target_info        = tree_db[target_index]
                    required_wildcards = info.match(target_info)
                    #
                    if required_wildcards == None:
                        # Misfit --> 'fat transition'
                        info.move_to_fat(target_index)
                        transition_change_f = True
                        info_changed_f      = True
                        break

                    elif required_wildcards.is_empty() == False:
                        info.plug_wildcards(required_wildcards)

                # While there was a change in the 'fat transitions' we need to check
                # again if the fat transitions match.
                if not transition_change_f: break
                
                info.set_wildcard_set(backup)

        if not info_changed_f: break

    return tree_db

def categorize_transitions(State, MaxComparisonN):
    """This function categorizes the transitions of a state into 'barren' and
       'fat' transitions. That is, barren transitions happen on small character
       sets that can be compared with less or equal MaxComparisonN. Any
       transition taking more comparisons than that are 'fat' transitions.
    """
    transition_map = State.transitions().get_map()

    barren_transition_map = {}
    for target_index, trigger_set in transition_map.items():
        interval_list = trigger_set.get_intervals(PromiseToTreatWellF=True)
        cmp_required  = 0
        for interval in interval_list:
            if interval.end - interval.begin < 2: cmp_required += 1 # Check '==' begin
            else:                                 cmp_required += 2 # Check '>=' begin and '<' end
            if cmp_required > MaxComparisonN: break
        if cmp_required > MaxComparisonN: 
            fat_transition_map[target_index] = trigger_set
        else:
            barren_transition_map[target_index] = trigger_set

    return barren_transition_map, fat_transition_map


