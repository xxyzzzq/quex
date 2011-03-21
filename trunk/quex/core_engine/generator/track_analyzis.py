"""
(1) Lexeme Pointer Required ___________________________________________________

    The buffer reload can be more effective, if the lexeme is actually not
    important. In this analyzis, it is determined whether at the end
    of subsequent transitions the lexeme is actually required or not.

    The TrackInfo object provides a member function

        .necessary_to_maintain_lexeme(StateIndex)

    which returns 'True' in case that the lexeme has to be preserved, and 
    'False' in case that the lexeme start pointer can be dropped upon reload.

(2) Acceptance Investigations _________________________________________________

Consider the patterns 

             21    'a'
             37    'abc'

A state machine that is able to detect those two patterns is the following:

        (0)-- 'a' --> ((1))-- 'b' --> (2)-- 'c' --> ((3))
                          21                            37

where ((1)) is the acceptance state for pattern 21 ('a') and state ((3)) is the
acceptance state for pattern 37 ('abc'). 

    Input:        'abd'
    Transitions:  (0)-- 'a' .->((1))-- 'b' -->(2)- 'd' --> drop out

But, pattern 21 ('a') has already matched. The state machine must keep track of
the last acceptance state and the input position where it was achieved. Thus,
it could store in state ((1))

   last_acceptance          = 21;
   last_acceptance_position = input_position;

Then, in the drop-out of state (2) a 'goto last_acceptance' would

   input_position = last_acceptance_position;
   ... route to 'last_acceptance terminal' ...

However, in most cases it is not necessary to store the last acceptance
position and last acceptance information in a variable at run time. In the
above example, it is clear the state (2) is **only** entered by state ((1)) and
thus the last acceptance is always 21. Also the input position is one position
ahead of where '21' matched. Thus, the drop-out of state (2) could look like

    input_position -= 1;
    goto TERMINAL_21;

an nothing would have to be stored at the entry of state ((1)). This could save
a significant amount of time. To support this, the TrackInfo object provides
the member functions

    .all_successors_have_distinct_acceptance_on_drop_out(StateIndex)

        True --> There are subsequent non-acceptance states where 
                 the acceptance cannot be derived from its predecessors.

                 In this case, variables 'last_acceptance' and 
                 'last_acceptance_position' **must** be used to 
                 communicate the back-track requirements.

        False --> Either there are no subsequent non-acceptance states,
                  or each subsequent non-acceptance state is of determined
                  acceptance in the sense of the exaplanation above.

                  Then, the acceptance state does not need to store 
                  information about last acceptance and its position.

        NOTE: This function is **only** to be called for acceptance states.

    .acceptance_info_on_drop_out(StateIndex)

        Returns: PatternID, BackStepN

        PatternID --> identifier of the pattern that is the determined
                      winner in case of drop-out in the given state.

                      -1   --> definitively failure
                      None --> the winner cannot be determined. It
                               needs to be referred to last_acceptance.

        BackStepN --> number of positions to step back in the input
                      to the place where the acceptance occured.
"""
from quex.input.setup import setup as Setup

class AcceptanceCondition:
    def __init__(self, PatternID, PreContextID, PreContextBeginOfLineF):
        # PatternID                   => ID of the pattern that accepts.
        # PreContextID                => pre-context that must be fulfilled so that 
        #                                pattern id is the winner. 
        #                   == -1     => no pre-context
        # PreContextBeginOfLineF      
        #                   == True   => For the acceptance PatternID
        #                                The begin of line must be fulfilled
        #                   == False  => no begin of line condition
        #
        # The normal case of a pattern without pre-context and begin-of-line 
        # condition is the (N, -1, False), where N is some integer.
        self.pattern_id                  = PatternID
        self.pre_context_id              = PreContextID
        self.pre_context_begin_of_line_f = PreContextBeginOfLineF

class AcceptanceObj:
    def __init__(self, OriginList=None):
        LanguageDB = Setup.language_db

        if OriginList == None:  # Acceptance = Failure
            self.__info = []
            return

        origin_list = OriginList.get_list()
        origin_list.sort()
        # Store information about the 'acceptance behavior' of a state.
        # 
        #    len(self.__info) == 0 --> state is not an acceptance state at all
        #    self.__info[i]
        self.__info = []
        for origin in origin_list:
            if not origin.is_acceptance(): continue

            info = AcceptanceCondition(origin.state_machine_id,
                                       origin.pre_context_id(),
                                       origin.pre_context_begin_of_line_f())
            
            self.__info.append(info)

            # If an unconditioned acceptance occurred, then no further consideration
            # is necessary.
            if     origin.pre_context_id()              == -1 \
               and origin.pre_context_begin_of_line_f() == False:
                break

    def is_failure(self):
        return len(self.__info) == 0

    def is_unconditioned_acceptance(self):
        if   len(self.__info) != 1:                 return False
        elif self.__info[0].pre_context_id != -1:   return False
        elif self.__info[0].pre_context_id == True: return False
        return True

    def __eq__(self, Other):
        if not isinstance(Other, AcceptanceObj): return False
        return self.__info == Other.__info

    def __repr__(self):
        if len(self.__info) == 0: return "Failure"
        txt = []
        for acceptance in self.__info:
            txt.append("(A = %i; pre-context = %i, begin_of_line=%s), " % 
                       (acceptance.pattern_id, acceptance.pre_context_id, 
                        repr(acceptance.pre_context_begin_of_line_f)))
        return "".join(txt)


class TrackInfo:
    def __init__(self, SM):
        """SM -- state machine to be investigated.
        """
        self.__sm = SM

        # (1) Analyze recursively in the state machine:
        #     -- Collect states that are part of a loop in the state machine.
        #        If a path from state A to state B contains one of those states,
        #        then the number of transitions that appear between A and B 
        #        can only be determined at run-time.
        self.__loop_states = set([])
        #     -- Acceptance Database.
        #        Store for each state the information about what acceptance 
        #        states lie on the way to them. Further store the path, so
        #        that later on it can be determined whether the number of 
        #        transitions can be determined beforehand.
        self.__acceptance_db = {}
        #     Dive to get the information above.
        self.__dive(SM.init_state_index, []) 

        # (2) Acceptance Determination
        #     -- The database that maps:  state_index --> (Acceptance, TransitionsNSinceAcceptance)
        #
        #        Acceptance --> An object carrying information about the 
        #                       acceptance of the state.
        #
        #        TransitionsNSinceAcceptance --> Number of transitions (passed characters) since 
        #                                        the last acceptance state.
        #                                        == None --> undetermined
        #                                        == -1   --> new input position = 1 after lexeme begin
        #                                        == int  --> number of characters since acceptance
        self.__db = {}

        #     -- Sets that keep track of necessity to store acceptance and/or acceptance position
        self.__acceptance_states_with_necessity_to_store_last_acceptance          = set([])
        self.__acceptance_states_with_necessity_to_store_last_acceptance_position = set([])

        #     Analyze to build the databases mentioned above.
        self.__determine_database()

    def acceptance_info_on_drop_out(self, StateIndex):
        """RETURNS 2 Values: 
        
              AcceptanceObj -- about the acceptance on drop out
              N             -- number of characters to go backwards to the
                               end of the acceptance position.
                               -1   --> go back to lexeme start + 1
                               None --> require storage of acceptance position
                                        goto last_acceptance_position.
        """
        return self.__db[StateIndex]

    def necessary_to_store_last_acceptance(self, StateIndex):
        """StateIndex must be the index of an acceptance state. 

           RETURNS: True,  if all successor states have a distinct acceptance
                           that can be determined from the state machine structure.
                           Then, no storage of the acceptance in an acceptance
                           variable is necessary.
                    False, if there are subsequent states that are of void 
                           acceptance that can only be determined at run-time.
                           Then, the 'last_acceptance' variable is required.

        """
        return StateIndex in self.__acceptance_states_with_necessity_to_store_last_acceptance

    def necessary_to_store_last_acceptance_position(self, StateIndex):
        """StateIndex must be the index of an acceptance state. 

           Same as 'all_successors_have_distinct_acceptance_on_drop_out()'--now
           about the necessity to store the acceptance position. It is conceivable
           that the acceptance of all successor states is determined, but the 
           distance from the last acceptance state is not (due to loops in the
           state machine).
        """
        return StateIndex in self.__acceptance_states_with_necessity_to_store_last_acceptance_position

    def necessary_to_maintain_lexeme(self, StateIndex):
        """If an acceptance has been passed, that does not care about the lexeme
           and if all subsequent possible acceptance states do not care about the
           lexeme, the lexeme start pointer bended. On reload, the lexeme start
           does not have to lie inside the buffer and, therefore are larger
           section can be reloaded.
        """
        return True

    def __dive(self, StateIndex, path, last_acceptance_state_index=-1, path_since_last_acceptance=[]):
        assert type(path) == list

        state = self.__sm.states[StateIndex]
        if state.is_acceptance(): 
            last_acceptance_state_index = StateIndex
            path_since_last_acceptance  = []

        # Add the information that the current state has a path where the last acceptance
        # lies n transitions backward.
        self.__acceptance_db.setdefault(StateIndex, []).append((last_acceptance_state_index, 
                                                                copy(path_since_last_acceptance)))

        if StateIndex in path:
            # All states in the detected loop must be marked as being part of
            # a recursion. Thus, if a path contains any one of those states the
            # distance cannot be determined.
            idx = path.index(StateIndex)
            self.__loop_states.update(path[idx:])
            return

        path.append(StateIndex)

        path_since_last_acceptance.append(StateIndex)
        for state_index in state.transitions().get_target_state_index_list():
            self.__dive(state_index, path, last_acceptance_state_index, path_since_last_acceptance)

    def __determine_database(self):
        def _get_transition_n_since_last_acceptace(InfoList):
            # If any state on the path is element of a recursive cycle, then
            # the distance to the last acceptance is not definite
            n = None
            for info in InfoList:
                path_from_last_acceptance_state = info[1]
                for state_index in path_from_last_acceptance_state:
                    if state_index in self.__loop_states:
                        return None

                if   n == None:                                 n = len(path_from_last_acceptance_state) - 1
                elif n != len(path_from_last_acceptance_state): return None

            return n

        def _get_common_acceptance(InfoList):
            acceptance = None
            for info in InfoList:
                acceptance_state_index = info[0]

                if acceptance_state_index == -1: # Failure
                    acceptance_obj = AcceptanceObj()
                else:
                    state = self.__sm.states[acceptance_state_index]
                    acceptance_obj = AcceptanceObj(state.origins())

                if   acceptance == None:           acceptance = acceptance_obj
                elif acceptance != acceptance_obj: return None

            return acceptance
                   
        # Determine for each state whether the acceptance is definite
        for state_index, state in self.__sm.states.iteritems():
            if state.is_acceptance(): 
                # The last acceptance state is the state itself and the last 
                # acceptance position lies zero characters backward.
                self.__db[state_index] = (AcceptanceObj(state.origins()), 0)

            info = self.__acceptance_db[state_index]
            # info = list of pairs (AcceptanceStateIndex, Path from AcceptanceStateIndex to state_index)

            acceptance = _get_common_acceptance(info)
            if acceptance == None:
                # Note, for any acceptance state involved, that there is a successor that 
                # has undetermined acceptance. Thus, this acceptance state needs to be stored.
                self.__acceptance_states_with_necessity_to_store_last_acceptance.update(map(lambda x: x[0], info))

                # Acceptance can only be determined at run-time. It cannot be determined
                # by the transition structure.
                transition_n_since_last_acceptance = None

            elif acceptance.is_failure():
                # If acceptance == Failure, then the new input position is one behind
                # the current lexeme start.
                transition_n_since_last_acceptance = -1

            else:
                # All information about acceptance points to the same pattern.
                # Thus, try to determine if distance to those states backward is
                # all the same.
                transition_n_since_last_acceptance = _get_transition_n_since_last_acceptace(info)

            if transition_n_since_last_acceptance == None:
                self.__acceptance_states_with_necessity_to_store_last_acceptance_position.update(map(lambda x: x[0], info))

            self.__db[state_index] = (acceptance, transition_n_since_last_acceptance)



