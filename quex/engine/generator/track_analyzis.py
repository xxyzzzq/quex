"""
Track Analysis

(C) 2011 Frank-Rene Schaefer
===============================================================================

The goal of track analysis is to profit from the static relations of 
states inside the state machine, so that the run-time effort can be 
reduced. At the end of the process, each state is decorated with a
set of attributes. They indicate how the state is to be implemented 
as source code.

The implementation of the state has the following basic elements:

*-----------------------------------------------------------------------------*

   Input:           Access the input character.

   SuccessorInfo:   [OPTIONAL] Store information to be used by successor states.

   TriggerMap:      All triggers that transit on a character to specific 
                    successor state.

   DropOut:         Handle the case that input character does not trigger in
                    trigger map.

*-----------------------------------------------------------------------------*

Accordingly, each state will be represented by a new 'state' consisting
of four objects:

    .input          <-- class Input
    .successor_info <-- class SuccessorInfo
    .trigger_map    <-- list of pairs (interval, target_state_index)
    .drop_out       <-- class DropOut

The following sections elaborate on the these objects and how they have
to perform. The classes 'Input', 'SuccessorInfo' and 'DropOut' allow
to access the information that resulted from the track analyzis. After
reading the following, review their class interfaces.
_____________________
                     |
Acceptance Detection |__________________________________________________________
---------------------'

The following discussion shows how these elements are configured. Consider
the simple state machine:

      ( 1 )-- 'a' -->( 2 )-- 'b' -->(( 3 ))
                                          "ab"

Is says that state 1 transits on 'a' to state 2. State 2 transits on 'b'
to state 3. State 3 is an acceptance state that indicates that pattern "ab" 
has been matched. This state machine can be implemented as follows:

        State1:
            /* Input */            input = *input_p;   
            /* TransitionBlock */  if( input == 'a' ) goto State2;
            /* DropOut */          goto Failure;

        State2:
            /* Input */            ++input_p;
                                   input = *input_p;   
            /* TransitionBlock */  if( input == 'b' ) goto State3;
            /* DropOut */          goto Failure;

        State2:
            /* Input */            ++input_p;
            /* DropOut */          goto Terminal('ab');

The following rules can already be derived:

*-----------------------------------------------------------------------------*

  Input:   (1) The init state does not increment the input_p,

           (2) If the state is the terminal of a post-context pattern
               without further transitions, then the input position
               is set to the end of the core pattern. Thus, it does
               not need to be incremented.

           (3) All other states increment/decrement the input position.

  DropOut: 
           (3) if no pattern ever matched the drop-out must be 'goto Failure'.

           (4) if the state is an acceptance state, then the drop-out must
               be 'goto Terminal;' where 'Terminal' is the address of the 
               action code that relates to the matching pattern.

  General: (5) When a terminal is reached, the input **must** point to the
               next character to be analyzed, i.e. one after the last
               character that matched!
*-----------------------------------------------------------------------------*

A somewhat more complicated state machine may be the following:

    ( 1 )-- 'a' -->(( 2 ))-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                         "a"                             "abc"

Here, state 2 looks different since it is an acceptance state and contains a
transition on 'b' to state 3. However, with the above rules it still behaves as
expected. If something different from 'b' arrives, then the input pointer
stands on the position right after the matched character 'a' and we transit to
the terminal of pattern "a". 

State 3 is interesting. If no 'c' is detected then, still, pattern "a" has
matched already. So, state 3 can actually goto Terminal("a"), but the input
position must be decreased by 1 so that it points directly behind the matched
character "a". A new rule can be stated about the DropOut:

*-----------------------------------------------------------------------------*

   DropOut: (6) If a state itself is not an acceptance state, but some
                state before it is an acceptance state, then 
               
                  (6.1) set the input pointer back to the position 
                        where the last acceptance state matched.
                  (6.2) goto the terminal of the last acceptance
                        state.

*-----------------------------------------------------------------------------*

In the case above, the resetting of the input pointer is trivial. Now, 
consider the state machine
                                     'd'
                                    ,---.
                                    \   /
    ( 1 )-- 'a' -->(( 2 ))-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                         "a"                             "abc"

Now, an arbitrary number of 'd's may occur before state 3 drops out.  This
requires, that state 2 must store the acceptance position and state 3 must
reset the acceptance position from a variable. Two new rules:

*-----------------------------------------------------------------------------*

  SuccessorInfo: (7) If there is a non-acceptance successor state 
                     that is reached via a path of arbitrary length 
                     (i.e. there is a loop somewhere), then the 
                     acceptance position must be stored in a variable
                     'last_acceptance_position'.

  DropOut: (8.1) For a non-acceptance state; If the path from the last 
                 acceptance state to this state is of arbitrary length, 
                 then the input position must be set to what 
                 'last_acceptance_position' indicated.

           (8.2) The same is true, if the state can be reached by multiple
                 acceptance states that have a different distance to this 
                 state.

*-----------------------------------------------------------------------------*

An even more complicated case may be mentioned here:

    ( 1 )-- 'a' -->(( 5 ))-- 'b' ---.
       \                 "a|abc"     \
        \                             \
         `-- 'b' -->(( 2 ))-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                          "b"                             "a|abc"

The pattern "a|abc" wins in state 5 and state 4. Pattern "b" wins in state 2.
Now, it cannot be said upfront what pattern has matched if state 3 is reached.
Thus, the acceptance state must store information about the acceptance:

*-----------------------------------------------------------------------------*

    SuccessorInfo: (9) If there is a non-acceptance successor that
                       can be reached from different acceptance states,
                       then the state must store the information about
                       the acceptance in a variable 'last_acceptance'.

    DropOut: (10) For non-acceptance state; If the state can be reached
                  by different acceptance states, or if there are preceding 
                  acceptance states and a path without acceptance, then the 
                  terminal store in 'last_acceptance' must be entered.

*-----------------------------------------------------------------------------*

_____________________
                     |
Pre-Contexts         |__________________________________________________________
---------------------'

Note, that 'Acceptance' may be dependent on pre-contexts, that is the
acceptance of a state generally is determined by a sequence of checks:

    if     ( pre_context[...] ) acceptance X
    else if( pre_context[...] ) acceptance Y
    else                        acceptance Z

where X has higher priority than Y and Y has higher priority than Z. Z is the
highest priority pattern without pre-context. All pre-context dependent
acceptance states are neglected because they are dominated by Z. 

Pre-context flags, however, are constant as soon as the forward lexical
analysis starts. Thus, the comparison of two acceptance chains is enough to
judge whether the acceptance of two states is equivalent. Now, consider the
state machine:

      ( 1 )-- 'a' -->( 2 )-- 'b' -->( 3 )-- 'c' -->(( 4 ))
                                                         "xyz/abc/"

which means that pattern "abc" must be preceded by pattern "xyz" in order to
match. All successor acceptance states of state 1, though, depend on the
pre-context "xyz". Thus, state 1 could actually drop-out immediately if the
pre-context is not met. It is not necessary to transit through states 2, 3, and
4 to find out finally, that pattern "xyz/abc/" fails because of the
pre-context. A new rule can be defined

*-----------------------------------------------------------------------------*

   SuccessorInfo: (11) If all successor acceptance states depend on 
                       a certain pre-context flag being raised, then
                       the first state on that path can drop-out 
                       on the condition that the pre-context is not met.

   Terminal:      (12) When a terminal is reached where the pathes took 
                       care of the pre-context checks, then there is no
                       need to check it again in the terminal.

*-----------------------------------------------------------------------------*

_____________________
                     |
Post-Contexts        |__________________________________________________________
---------------------'

Post contexts are patterns that must be present after the core pattern.  When
the end of the post-context matches, then end of the lexeme must be set to the
end of the core pattern. Example:


      ( 1 )-- 'a' -->( 2 )-- 'b' -->( 3 )-- ':' -->(( 4 ))
                                      S("abc")           "abc/:"

That is pattern "abc" must be followed by ":". After the match, though, the
analysis starts with ':' not with what comes after it. If a post-contexted
patten is matched the position of the end of the core pattern must be 
restored. Similar to the acceptance discussion about new rules can 
be introduced:

*-----------------------------------------------------------------------------*

   SuccessorInfo: (13) If the length of the path from the end-of-core-pattern
                       to the final end-of-post context is arbitrary (due to
                       loops), then the input position of the end-of-core
                       pattern must be stored in a variable 'post_context_position[i]'.

   DropOut: (14) If the match is the end of a post context, then the position
                 of the core pattern needs to be restored.

               (14.1) If the distance to the end of the core pattern can be 
                      determined statically, then the input position is decremented
                      accordingly.

               (14.2) Else, the input position must be set to what is indicated
                      by variable 'post_context_position[i]'.
               
*-----------------------------------------------------------------------------*

Note, that it is not necessary to store what core pattern has matched, since
the fact that the end of the core pattern has been reached testifies what
core pattern is passed. Further, if there are multiple post-context
with the same core-patterns, then the 'post_context_position' can be shared,
if is stored in exactly the same states.

*-----------------------------------------------------------------------------*

    General: (15) post-constext that store their input positions in exactly
                  the same states can share their post_context_position 
                  variable.

*-----------------------------------------------------------------------------*

_____________________
                     |
Lexeme Start Pointer |__________________________________________________________
---------------------'

[[ This needs some clarification: What happens, if no acceptance state is
   reached then? OnFailure would expect that the input position is 
   lexeme_start_p + 1. This is impossible if it is reset at reload.
]]

On reload, in general, the current lexeme must be maintained so that is 
can be accessed in the pattern-action. However, if for a state it 
can be determined that no successor acceptance state cares about the lexeme,
then the lexeme start pointer can be set to the current input position. 
This allows to quickly skip large 'comment' section that span regions that
are even bigger than the current input buffer size. 

A new rule concerning the reload behavior can be defined:

    OnReload:

    (16) If no successor acceptance state 'cares' about the lexeme and
         a 'dont-care' acceptance state has been passed, then then reload
         can set the lexeme_start_p to the current input position and 
         reload the buffer from start.

    (17) All non-acceptance states that immediately follow a 'skipper
         state' must cause 'skip-failure' on drop-out.
"""
from quex.input.setup import setup as Setup
from copy import copy

class AnalyzerState:
    def __init__(self, StateIndex, StorePostContextPositions, TheInput, TheStoreAcceptance, TheDropOut):
        assert type(StateIndex) in [int, long]
        assert type(TheDropOut) == list

        self.index                        = StateIndex
        self.input                        = TheInput
        self.store_post_context_positions = StorePostContextPositions
        self.store_acceptance             = TheStoreAcceptance
        self.drop_out                     = TheDropOut

    def __repr__(self):
        txt  = ".state_index = %i" % StateIndex
        txt += ".input.move_input_position                        = " + repr(self.input.move_input_position())
        txt += "      .immediate_drop_out_if_not_pre_context_list = " + repr(self.input.immediate_drop_out_if_not_pre_context_list())
        txt += ".store_acceptance = [\n"
        for element in store_acceptance:
            if element.pre_context_id() != None: 
                txt += "(pre_context_id = %i, " % element.pre_context_id()
            else:
                txt += "("
            txt += "store_acceptance = %s, "             + repr(element.store_acceptance())
            txt += "store_acceptance_position_f = %s)\n" + repr(element.store_acceptance_position_f())
        txt += "]\n"
        txt += ".drop_out = [" 
        for element in drop_out:
            if element.pre_context_id() != None: 
                txt += "(pre_context_id = %i, " % element.pre_context_id()
            else:
                txt += "("
            txt += "move_input_p = %s, " + repr(element.move_input_position())
            txt += "terminal = %s)\n"    + repr(element.terminal())
        txt += "]\n"

def do(sm, ForwardF):
    track_info = TrackInfo(sm, ForwardF)

    for state_index, state in sm.states.iteritems():

        state._i_ = AnalyzerState(state_index,
                                  track_info.get_post_context_position_to_be_stored(state_index),
                                  get_StoreAcceptance(state_index, state, track_info),
                                  Input(state_index, state, track_info),
                                  get_DropOut(state_index, state, track_info))

    return sm.values()

class Input:
    def __init__(self, StateIndex, track_info):
        """RULES: (1) Init state forward does not increment input_p ...
                  (2) Also, if the state is the terminal of a post-context pattern ...
                  (3) All other states do increment/decrement.
        """
        if track_info.forward_lexing_f():
            # Rules (1), (2), and (3)
            if   track_info.is_init_state_index(StateIndex):        
                self.__move_input_position = 0
            elif     track_info.is_dead_end_state(StateIndex) \
                 and track_info.is_post_context_acceptance(StateIndex): 
                self.__move_input_position = 0
            else:                                                 
                self.__move_input_position = +1
        else:
            # Backward lexing --> rule (3)
            self.__move_input_position = -1

        # TODO: Required analysis
        self.__immediate_drop_out_if_not_pre_context_list = False

    def move_input_position(self):
        """ 1   --> increment by one before dereferencing
           -1   --> decrement by one before dereferencing
            0 --> neither increment nor decrement.
        """
        return self.__move_input_position

    def immediate_drop_out_if_not_pre_context_list(self):
        """If all successor states require the list of given
           pre-contexts, then the state can check whether 
           at least one of them is hit. Otherwise, it 
           could immediately drop out.
        """
        return self.__immediate_drop_out_if_not_pre_context_list

class StoreAcceptance:
    def __init__(self, PreContextID, track_info):
        self.__pre_context_id              = PreContextID
        self.__store_acceptance            = track_info.must_store_last_acceptance(StateIndex)
        self.__store_acceptance_position_f = track_info.must_store_last_acceptance_position(StateIndex)
        
    def pre_context_id(self):
        """Returns the pre-context id (i.e. the id of the pre-context's state machine)
           For which the drop-out instruction is defined. 

           None --> No pre-context (the very usual case).
        """
        return self.__pre_context_id

    def store_acceptance_position_f(self):
        """True  --> position needs to be stored in last_acceptance.
           False --> position does not need to be stored in last_acceptance.

           This may influence, the way that the acceptance object is
           interpreted. For example, if the acceptance requires a pre-context
           to be fulfilled, the last_acceptance is stored inside the 
           pre-context if-block.
        """
        return self.__store_acceptance_position_f

    def store_acceptance(self):
        """Acceptance to be stored upon entry in this function.
           N (integer) --> store acceptance information, Winner = N
           None        --> no acceptance is to be stored.
        """
        return self.__store_acceptance


class DropOut:
    def __init__(self, StateIndex, track_info):
        self.__move_input_position = track_info.acceptance_location(StateIndex)
        self.__pre_context_id      = PreContextID
        self.__terminal            = TerminalID

    def pre_context_id(self):
        """Returns the pre-context id (i.e. the id of the pre-context's state machine)
           For which the drop-out instruction is defined. 

           None --> No pre-context (the very usual case).
        """
        return self.__pre_context_id

    def move_input_position(self):
        """N <= 0   --> move input position backward according to integer.
           None     --> move input position to 'last_acceptance_position', or
                        move input position to 'post_context_position[i]'
                        where 'i' is determined by the acceptance object.
           N == 1   --> move input position to 'lexeme begin + 1'
        """
        return self.__move_input_position

    def terminal(self):
        return self.__terminal

class AcceptanceCondition:

    """This object simply tells that a specific pattern wins if the pre-context
       or a begin of line is fulfilled. An acceptance independent of pre-contexts
       is indicated by 
                            pre_context_id            == -1
                            begin_of_line_condition_f == False

       In this case, the pattern id is simply the acceptance pattern.
    """
    def __init__(self, PatternID, PreContextID, PreContextBeginOfLineF):
        # PatternID                   => ID of the pattern that accepts.
        #
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
        self.pre_context_id              = PreContextID
        self.pre_context_begin_of_line_f = PreContextBeginOfLineF
        self.pattern_id                  = PatternID

    def is_conditional(self):
        return self.pre_context_id != -1 or self.pre_context_begin_of_line_f

class AcceptanceInfo:
    def __init__(self, OriginList=None):
        LanguageDB = Setup.language_db

        if OriginList == None:  # Acceptance = Failure
            self.__acceptance_condition_list = []
            return

        origin_list = OriginList.get_list()
        origin_list.sort()
        # Store information about the 'acceptance behavior' of a state.
        self.__acceptance_condition_list = []
        for origin in origin_list:
            if not origin.is_acceptance(): continue

            info = AcceptanceCondition(origin.state_machine_id,
                                       origin.pre_context_id(),
                                       origin.pre_context_begin_of_line_f())
            
            self.__acceptance_condition_list.append(info)

            # If an unconditioned acceptance occurred, 
            # then no further consideration is necessary.
            if not info.is_conditional(): break

        # Here: no acceptance => len(self.__acceptance_condition_list) == 0 

    def is_failure(self):
        return len(self.__acceptance_condition_list) == 0

    def is_conditional(self):
        if len(self.__acceptance_condition_list) == 0: return False
        # Only the last condition in the acceptance condition list is unconditional.
        # Thus, if there are more than one condition --> conditional
        elif len(self.__acceptance_condition_list) > 1: return False
        # The only one acceptance may still be condition, so check ...
        return self.__acceptance_condition_list[0].is_conditional()

    def __eq__(self, Other):
        if not isinstance(Other, AcceptanceInfo): return False
        return self.__acceptance_condition_list == Other.__acceptance_condition_list

    def __repr__(self):
        if len(self.__info) == 0: return "Failure"
        txt = []
        for acceptance in self.__info:
            txt.append("(A = %i; pre-context = %i, begin_of_line=%s), " % 
                       (acceptance.pattern_id, acceptance.pre_context_id, 
                        repr(acceptance.pre_context_begin_of_line_f)))
        return "".join(txt)

class TrackInfo:
    def __init__(self, SM, ForwardF):
        """SM -- state machine to be investigated."""
        assert type(ForwardF) == bool
        self.__sm        = SM
        self.__forward_f = ForwardF

        # (1) Analyze recursively in the state machine:
        #
        # -- 'Loop States'.
        #    Collect states that are part of a loop in the state machine.  If a
        #    path from state A to state B contains one of those states, then the
        #    number of transitions that appear between A and B can only be
        #    determined at run-time.
        #
        #    set of state indices that are part of a loop.
        #
        self.__loop_states = set([])

        # -- Database of Passed Acceptance States
        #    Store for each state the information about what acceptance states
        #    lie on the way to it. Further store the path, so that later on it
        #    can be determined whether the number of transitions can be
        #    determined beforehand.
        # 
        #    map:  state_index  --> list of (AcceptanceStateIndex, 
        #                                    Path from AcceptanceStateIndex to state_index)
        #
        self.__passed_acceptance_db = {}

        # -- Database of Reachable Acceptance States
        #    Store for each state what acceptance states are reachable.
        #   
        #    map:  state_index  ---> list of acceptance state indices
        #
        self.__reachable_acceptance_db = {}

        #     Dive to get the information above.
        self.__dive(self.__sm.init_state_index, []) 

        # (*) Post Context Configurations
        # 
        #    If multiple post-contexts share the same core pattern, then they
        #    can share the 'post_context_position[i]' variable. The following
        #    data structure stores pairs of 
        #
        #    [(list of ids of post contexts that share the same register) ... ]
        self.__post_context_configurations = self.__post_context_position_store_conifigurations()

        # (2) Acceptance Determination
        #
        #    The database that maps:  state_index --> MovesToAcceptancePosition
        #
        #    MovesToAcceptancePosition :
        #    Number of 'moves' (passed characters) to set the input to the last
        #    acceptance position.
        #
        #      == None --> undetermined (restore last_acceptance_position required)
        #      == 1    --> new input position = 1 after lexeme begin
        #                  (if acceptance = failure)
        #      <= 0    --> number of characters to move backward
        #                  to last acceptance position.
        self.__acceptance_location_db = {}

        #    What acceptance states need to store info about the acceptance?
        #    What acceptance states need to store info about the acceptance position?
        self.__acceptance_states_with_necessity_to_store_last_acceptance          = set([])
        self.__acceptance_states_with_necessity_to_store_last_acceptance_position = set([])

        #     Analyze to build the databases mentioned above.
        self.__determine_acceptance_dbs()

    def forward_f(self):
        return self.__forward_f

    def acceptance_location(self, StateIndex):
        return self.__acceptance_location_db[StateIndex]

    def must_store_last_acceptance(self, StateIndex):
        return StateIndex in self.__acceptance_states_with_necessity_to_store_last_acceptance

    def must_store_last_acceptance_position(self, StateIndex):
        return StateIndex in self.__acceptance_states_with_necessity_to_store_last_acceptance_position

    def __dive(self, StateIndex, path, last_acceptance_state_index=-1, path_since_last_acceptance=[]):
        assert type(path) == list

        state = self.__sm.states[StateIndex]

        if state.is_acceptance(): 
            last_acceptance_state_index = StateIndex
            path_since_last_acceptance  = []
            for state_index in path:
                self.__reachable_acceptance_db[state_index] = StateIndex

        #for origin in state.origins().get_list():
        #    if origin.is_end_of_post_contexted_core_pattern():
        #        post_context_id = origin.post_context_id()
        #        last_post_context_id[post_context_id]   = True
        #        last_post_context_path[post_context_id] = []

        if StateIndex in path:
            # Mark all states that are part of a loop. The length of a path that 
            # contains such a state can only be determined at run-time.
            idx = path.index(StateIndex)
            self.__loop_states.update(path[idx:])
            return

        # Add the information that the current state has a path where the last acceptance
        # lies n transitions backward.
        self.__passed_acceptance_db.setdefault(StateIndex, []).append(
                (last_acceptance_state_index, copy(path_since_last_acceptance)))

        path.append(StateIndex)
        path_since_last_acceptance.append(StateIndex)

        for state_index in state.transitions().get_target_state_index_list():
            self.__dive(state_index, path, last_acceptance_state_index, path_since_last_acceptance)

    def __determine_acceptance_dbs(self):

        def _get_transition_n_since_last_acceptace(InfoList):
            # If any state on the path is element of a recursive cycle, then
            # the distance to the last acceptance is not definite
            n = None
            for info in InfoList:
                path_from_last_acceptance_state = info[1]
                for state_index in path_from_last_acceptance_state:
                    if state_index in self.__loop_states:
                        return None

                if   n == None:                                 n = len(path_from_last_acceptance_state) 
                elif n != len(path_from_last_acceptance_state): return None

            return n

        def _get_common_acceptance(InfoList):
            acceptance = None
            for info in InfoList:
                acceptance_state_index = info[0]

                if acceptance_state_index == -1: # Failure
                    acceptance_obj = AcceptanceInfo()
                else:
                    state = self.__sm.states[acceptance_state_index]
                    acceptance_obj = AcceptanceInfo(state.origins())

                if   acceptance == None:           acceptance = acceptance_obj
                elif acceptance != acceptance_obj: return None

            return acceptance
                   
        # Determine for each state whether the acceptance is definite
        for state_index, state in self.__sm.states.iteritems():
            if state.is_acceptance(): 
                # The last acceptance state is the state itself and the last 
                # acceptance position lies zero characters backward.
                self.__acceptance_location_db[state_index] = 0
                continue

            info = self.__passed_acceptance_db[state_index]
            #    = list of pairs (AcceptanceStateIndex, Path from AcceptanceStateIndex to state_index)

            acceptance = _get_common_acceptance(info)
            if acceptance == None:

                # Note, for any acceptance state involved, that there is a
                # successor that has undetermined acceptance. Thus, this
                # acceptance state needs to be stored.
                self.__acceptance_states_with_necessity_to_store_last_acceptance.update(map(lambda x: x[0], info))

                # Acceptance can only be determined at run-time. It cannot be
                # determined by the transition structure.
                move_n_to_last_acceptance = None

            elif acceptance.is_failure():
                # If acceptance == Failure, then the new input position is one
                # behind the current lexeme start.
                move_n_to_last_acceptance = 1

            else:
                # All information about acceptance points to the same pattern.
                # Thus, try to determine if distance to those states backward
                # is all the same.
                n = _get_transition_n_since_last_acceptace(info)
                if n != None: move_n_to_last_acceptance = - n
                else:         move_n_to_last_acceptance = None

            if move_n_to_last_acceptance == None:
                # If the last acceptance cannot be determined by structure,
                # then all related last acceptance states need to store
                # information about their acceptance.
                last_passed_acceptance_state_list = []
                for dummy, path in info: 
                    last_passed_acceptance_state_list.append(path[0])
                self.__acceptance_states_with_necessity_to_store_last_acceptance_position.update(
                        last_passed_acceptance_state_list)

            self.__acceptance_location_db[state_index] = move_n_to_last_acceptance

    def __post_context_position_store_conifigurations(self):
        """Determine the groups of post contexts that store their input
           positions at the same set of states.

           RETURNS: List of Lists of post context ids.

                    Each the list elements contain post context ids that 
                    can share the same post_context_position[...] register.
        """

        # post context id --> list of states where the input position is to be stored.
        db = {}
        for index, state in self.__sm.states.iteritems():
            for origin in state.origins().get_list():
                if origin.store_input_position_f():
                    db.setdefault(origin.post_context_id(), []).append(index)

        # Combine those post contexts that share the same set of states where 
        # positions are to be stored.
        group_list = []
        for post_context_id, state_index_list in db.iteritems():
            # See whether there is already a group with the same state index list
            for group in group_list:
                if db[group[0]] == state_index_list: 
                    group.append(post_constex_id)
                    break
            else:
                # Build your own group
                group_list.append([post_context_id])

        return group_list

    def get_post_context_position_to_be_stored(self, StateIndex):
        OriginList = self.__sm.states[StateIndex].origins().get_list()

        result = []
        for origin in OriginList:
            if not origin.is_end_of_post_contexted_core_pattern(): continue
            # Assumption about origin based on assumption about single pattern state machine:
            #
            #    According to 'setup_post_context.py' (currently line 121) no acceptance
            #    state of a post context can store the input position. This has been made 
            #    impossible! Otherwise, the post context would have zero length.
            #
            #    Post-conditions via backward search, i.e. pseudo ambiguous post conditions,
            #    are a different ball-game.
            assert origin.is_acceptance() == False

            # Store current input position, to be restored when post condition really matches
            post_context_index = self.get_post_context_index(origin.state_machine_id)
            result.append(post_context_index)


