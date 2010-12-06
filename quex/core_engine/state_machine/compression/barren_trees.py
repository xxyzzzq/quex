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
def get_difference(self, A, B):
    assert type(A) == dict
    assert type(B) == dict

    # Compute difference in transition maps
    #     --> table: [trigger_set, target state in skeleton, target state in candidate]
    diff_in_A_not_in_B = NumberSet()
    diff_not_in_A_in_B = NumberSet()
    diff_in_both       = NumberSet()

    for A_target_index, A_trigger_set in A.items():
        if B.has_key(target_index) == False:
            diff_in_A_not_in_B.unite_with(A_trigger_set)
            continue

        delta_set = B[A_target_index].mutual_exclusive_set(A_trigger_set)
        if not delta_set.is_empty(): 
            diff_in_both.unite_with(delta_set)
            continue

    for B_target_index, B_trigger_set in B.items():
        if A.has_key(target_index) == False:
            diff_not_in_A_in_B.unite_with(B_trigger_set)
            continue

    return diff_in_A_not_in_B, diff_not_in_A_in_B, diff_in_both

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

        self.__barren = BarrenTransitionMap
        self.__fat    = FatTransitionMap

        trigger_set = NumberSet()
        for trigger_set in self.__barren.values():
            self.__wildcard_set.unite_with(trigger_set)

        # The 'skeleton' is the map of transitions that is performed if the
        # above tree does not match. It has the form of a 'transition map', i.e.
        #      target state index --> trigger set that maps to target state

        # Character that may trigger to any state. This character is
        # adapted when the first character of the path is different
        # from the wildcard character. Then it must trigger to whatever
        # the correspondent state triggers.

    def barren(self):
        return self.__barren

    def fat(self):
        return self.__fat

    def move_to_fat(self, TargetIndex):
        self.__fat[TargetIndex] = self.__barren[TargetIndex]
        del self.__barren[TargetIndex]

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
        used_wildcard_set = NumberSet()
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
        diff_in_A_not_in_B, \
        diff_not_in_A_in_B, \
        diff_in_both      = \
                get_difference(self.__fat, CandidateFatTransitionMap)

        # (1) what is in 'fat' but not in candidate's 'fat transition' can be covered
        #     by barren transitions of candidate.
        if diff_in_A_not_in_B.is_empty() == False:
            diff_in_A_not_in_B.subtract(CandidateBarrenTriggerSet)
            if diff_in_A_not_in_B.is_empty() == False: return None

        # (2) what is in 'fat transition' but not in 'skeleton' can be plugged
        #     by wild cards.
        if diff_not_in_A_in_B.is_empty() == False:
            diff_in_A_not_in_B.subtract(self.__wildcard_set)
            if diff_in_A_not_in_B.is_empty() == False: return None
            used_wildcard_set = diff_not_in_A_in_B.intersection(self.__wildcard_set)

        # (3) What appears in both can be plugged either by (1) or by (2), preferable
        #     by (1) because no wildcard is wasted.
        if diff_in_both.is_empty() == False:
            diff_in_both.subtract(CandidateBarrenTriggerSet)
            if diff_in_both.is_empty() == False:
                diff_in_both.subtract(CandidateBarrenTriggerSet)
                if diff_in_both.is_empty() == False: return None
                used_wildcard_set.unite_with(diff_not_in_A_in_B.intersection(self.__wildcard_set))

        return used_wildcard_set

def absorb_subsequent_states(StateIndex, barren_tree):
    """A 'barren branch' is a state where some subsequent states are absorbed 
       into the 'if-then' blocks, rathen than in separated state code fragments.

       A subsequent state might be absorbed if it is small and fits the current
       state.
    """

    current_state_info = info_db[StateIndex]

    for target_index, trigger_set in current_state_info.barren_transition_map():



def categorize_all_states(SM, MaxComparisonN):

    # A state can only by absorbed by one other state.
    # => book keeping about each state that has been absorbed already.
    done_set = set([])

    tree_db  = {}
    # Here, the loop determines the sequence of processing, therefore 
    # determines the **priorization** of where states are absorbed. States that
    # come first, can absorb a subsequent state, later states **must** transit
    # to the subsequent state.
    for state_index, state in SM.items():
        barren, fat = categorize_transitions(State, MaxComparisonN)
        for target_index, trigger_set in barren:
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
                    else:
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


