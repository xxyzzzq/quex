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

DEFINITION 'acceptance info': Let such a sequence of checks be defined as 
                              the 'acceptance info' of a state.

Pre-context flags, however, are constant as soon as the forward lexical
analysis starts. Any combination of pre_contexts being fulfilled is
conceivable-including no pre-context. If two states have a different acceptance
info, then this means that there is a combination of pre-contexts were they
have a different acceptance. Thus the condition 'different acceptance' from the
rules above can be generalized to 'different acceptance info'. The comparison
of two acceptance chains is enough to judge whether the acceptance of two
states is equivalent.

Now, consider the state machine:

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
from copy             import copy, deepcopy
from collections      import defaultdict

def do(sm, ForwardF):
    track_info = TrackInfo(sm, ForwardF)

    for state_index, acceptance_info in track.acceptance_db.iteritems():
            
        state._i_ = AnalyzerState(state_index,
                                  acceptance_info,
                                  EntryActions(state_index, acceptance_info, [], []),
                                  Input(state_index, track_info),
                                  DropOut(state_index, acceptance_info, track_info))

    return sm.values()

class AnalyzerState:
    def __init__(self, StateIndex, TheInput, TheEntryActions, TheDropOut):
        assert type(StateIndex) in [int, long]
        assert type(TheDropOut) == list

        self.index         = StateIndex
        self.input         = TheInput
        self.entry_actions = TheEntryActions
        self.drop_out      = TheDropOut

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
            else:                                                 
                self.__move_input_position = +1
        else:
            # Backward lexing --> rule (3)
            self.__move_input_position = -1

        # TODO: Required analysis
        self.__immediate_drop_out_if_not_pre_context_list = False

    def move_input_position(self):
        """+1 --> increment by one before dereferencing
           -1 --> decrement by one before dereferencing
            0 --> neither increment nor decrement.
        """
        return self.__move_input_position

    def immediate_drop_out_if_not_pre_context_list(self):
        """If all successor states require the list of given pre-contexts, then 
           the state can check whether at least one of them is hit. Otherwise, it 
           could immediately drop out.
        """
        return self.__immediate_drop_out_if_not_pre_context_list

class EntryActions:
    def __init__(self, TheAcceptanceInfo, StorePostContextPositionList, StorePreContextFulfilledList):

        self.__store_acceptance_f               = TheAcceptanceInfo.necessary_to_store_last_acceptance_f()
        self.__store_acceptance_position_f      = TheAcceptanceInfo.necessary_to_store_last_acceptance_position_f()
        self.__store_post_context_position_list = StorePostContextPositionList
        self.__pre_context_fulfilled_list       = StorePreContextFulfilledList

    def acceptance_sequence(self):
        return self.__sequence

    def store_acceptance_f(self):
        return self.__store_acceptance_f

    def store_acceptance_position_f(self):
        return self.__store_acceptance_position_f
        
    def store_post_context_position_list(self):
        """What post context positions have to be stored. Return list of
           register indices. That is for each element 'i' in the list the
           position needs to be stored:

                    post_context_position[i] = input_p;
        """
        return self.__store_post_context_position_list

    def mark_pre_context_fulfilled_list(self):
        """This is only relevant during backward lexical analyzis while
           searching for pre-contexts. The list that is returned tells
           that the given pre-contexts are fulfilled in the current state
           and must be set, e.g.

                    pre_context_fulfilled[i] = true; 
        """
        return self.__pre_context_fulfilled_list

class DropOutElement:
    def __init__(self, StateIndex, PreContextID, MoveInputPosition, TerminalID):
        """Pre-context id (i.e. the id of the pre-context's state machine)
           For which the drop-out instruction is defined. 

           None --> No pre-context (the very usual case).
        """
        self.pre_context_id      = PreContextID
        """N <= 0   --> move input position backward according to integer.
           None     --> move input position to 'last_acceptance_position', or
                        move input position to 'post_context_position[i]'
                        where 'i' is determined by the acceptance object.
           N == 1   --> move input position to 'lexeme begin + 1'
        """
        self.move_input_position = MoveInputPosition
        """ N > 0       pattern id of the winning pattern.
            None        terminal = end of file/stream
            -1          terminal = failure
        """
        self.terminal_id         = TerminalID

class DropOut:
    def __init__(self, StateIndex, TheAcceptanceInfo, track_info):
        self.__sequence = []

        for x in TheAcceptanceInfo.get_list():
            element = DropOutElement(x.pre_context_id, 
                                     track_info.acceptance_location_db[StateIndex],
                                     x.pattern_id)
            self.__sequence.append(element)

    def acceptance_sequence(self):
        return self.__sequence

class AcceptanceInfoElement:
    """This object simply tells that a specific pattern wins if the pre-context
       or a begin of line is fulfilled. 
    """
    def __init__(self, PatternID, PreContextID):
        """PatternID     => ID of the pattern that accepts.
                            None --> end of file
                            -1   --> failure
           PreContextID  => pre-context that must be fulfilled so that 
                            pattern id is the winner. 
                            None --> no pre-context whatsoever
                            - 1  --> pre-context = begin of line
          
           The normal case of a pattern without pre-context and begin-of-line 
           condition is the (None, PatternID). Normal case for end of file
           is (None, None). Normal case for 'failure' is (None, -1).
        """
        self.pre_context_id = PreContextID
        self.pattern_id     = PatternID

class AcceptanceInfo:
    def __init__(self, TheState):
        LanguageDB = Setup.language_db

        if TheState.is_acceptance() == False:  # Acceptance = Failure
            self.__acceptance_condition_list = []
            return

        origin_list = TheState.origins().get_list()
        origin_list.sort()
        # Store information about the 'acceptance behavior' of a state.
        self.__acceptance_condition_list = []
        for origin in origin_list:
            if not origin.is_acceptance(): continue

            if   origin.pre_context_begin_of_line_f(): pre_context_id = -1
            elif origin.pre_context_id() == -1:        pre_context_id = None
            else:                                      pre_context_id = origin.pre_context_id()
            info = AcceptanceInfoElement(origin.state_machine_id, pre_context_id)
            
            self.__acceptance_condition_list.append(info)

            # If an unconditioned acceptance occurred, then no further consideration!
            # (Rest of acceptance candidates is dominated).
            if pre_context_id != None: break
        # If: no acceptance => len(self.__acceptance_condition_list) == 0 

        # Each necessity is related to a pre-context
        self.__necessary_to_store_last_acceptance_f          = False
        self.__necessary_to_store_last_acceptance_position_f = False

    def is_failure(self):
        return len(self.__acceptance_condition_list) == 0

    def get_acceptance_id(self, PreContextID):
        """PatternID of the winning pattern, provided that PreContextID 
                     is fulfilled.
           -1        if state 'fails' in case of the given PreContextID.
        """
        for element in self.__acceptance_condition_list:
            if element.pre_context_id == PreContextID: return element.pattern_id
        return -1

    def is_conditional(self):
        if len(self.__acceptance_condition_list) == 0: return False
        # Only the last condition in the acceptance condition list is unconditional.
        # Thus, if there are more than one condition --> conditional
        elif len(self.__acceptance_condition_list) > 1: return True
        # The only one acceptance may still be condition, so check ...
        return self.__acceptance_condition_list[0].pre_context_id != None

    def failure_always(self):
        return len(self.__acceptance_condition_list) == 0
        
    def failure_possible(self):
        """Determines if it is possible that the state 'fails'. This may
           happen, because:
                         -- state is a 'failure' state
                         -- state does not accept if there is no 
                            pre-context fulfilled.
        """
        if len(self.__acceptance_condition_list) == 0: return True
        # Only the last entry is possibly unconditional. If the last entry
        # is conditional, this means there is no acceptance for the case
        # that no pre-context holds.
        last = self.__acceptance_condition_list[-1]
        if last.pre_context_id != None:
            return True
        else:
            return (last.pattern_id == -1) or (last.pattern_id == None)

    def get_pattern_id_list(self):
        return map(lambda x: x[0], self.__acceptance_condition_list)

    def __eq__(self, Other):
        if not isinstance(Other, AcceptanceInfo): return False
        return self.__acceptance_condition_list == Other.__acceptance_condition_list

    def set_necessary_to_store_last_acceptance_f(self):
        self.__necessary_to_store_last_acceptance_f = True

    def necessary_to_store_last_acceptance_f(self):
        return self.__necessary_to_store_last_acceptance_f

    def set_necessary_to_store_last_acceptance_position_f(self):
        self.__necessary_to_store_last_acceptance_position_f = True

    def necessary_to_store_last_acceptance_position_f(self):
        return self.__necessary_to_store_last_acceptance_position_f

    def __repr__(self):
        if len(self.__acceptance_condition_list) == 0: return "(Failure)"
        txt = []
        for acceptance in self.__acceptance_condition_list:
            if   acceptance.pre_context_id == None: pre_context_str = "None"
            elif acceptance.pre_context_id != -1:   pre_context_str = "%i" % self.pre_context_id
            else:                                   pre_context_str = "begin-of-line"
            txt.append("(A = %i; pre = %s), " % 
                       (acceptance.pattern_id, pre_context_str))
        return "".join(txt)

class AcceptanceTraceEntry:
    def __init__(PreContextID, PatternID, MoveBackwardN, AcceptingStateIndex, PositioningStateIndex):
        """PreContextID  --
           PatternID     -- 
           MoveBackwardN --
           AcceptingStateIndex -- Index of the state that accepts the mentioned
                                  pattern. This is used when we need to inform
                                  the state that it needs to store the acceptance
                                  information.
           PositioningStateIndex -- Index of the state that positions the input pointer
                                    in the case of acceptance. This is usually the 
                                    acceptance state. For post-context patterns it is 
                                    the state where the post context begins.

           PositioningStateIndex != AcceptingStateIndex => It is a post context pattern
        """
        self.pre_context_id  = PreContextID
        self.pattern_id      = PatternID
        self.move_backward_n = MoveBackwardN
        # 
        self.accepting_state_index   = AcceptingStateIndex
        self.positioning_state_index = PositioningStateIndex
        #
        self.post_context_f          = (PositioningStateIndex != AcceptingStateIndex)

class AcceptanceTrace:
    def __init__(self):
        self.__info_table = []

    def update(self, StateIndex, TheState, path, LoopStateF):
        # If the current state is a loop state, than all positions become void.
        # This means that number of characters to reach this state can no longer
        # be determined by the state machine structure itself.
        if LoopStateF:
            for entry in self.__info_table:
                entry.move_backward_n = None
        else:
            for entry in self.__info_table:
                entry.move_backward_n += 1

        if not TheState.is_acceptance(): return

        least_priviledged_pattern_id = self.__info_table[-1].pattern_id

        # For each pre-context make an entry
        origin_list = TheState.origins().get_list()
        for origin in sorted(origin_list):
            if not origin.is_acceptance(): continue

            # (0) The pattern's ID
            pattern_id = origin.state_machine_id
            if pattern_id > least_priviledged_pattern_id: break

            # (1) The Pre-Context under which it triggers
            if   origin.pre_context_begin_of_line_f(): pre_context_id = -1
            elif origin.pre_context_id() != -1:        pre_context_id = origin.pre_context_id()
            else:                                      pre_context_id = None

            # (2) The position where the input pointer has to be set if the 
            #     pattern is accepted (how many characters to go backwards).
            if origin.post_context_id() == -1: 
                move_backward_n = 0
            else:
                move_backward_n = self.__find_last_post_context_begin(origin.post_context_id(), 
                                                                      path, track_info.states_db())
            
            # (*) Make the entry in the database
            self.__info_table.append(AcceptanceTraceEntry(pre_context_id, pattern_id, move_backward_n))

            if pre_context_id == None:
                # The lists ends now, since no other pre-context can be considered
                self.__info_table = filter(lambda x: x.pattern_id > pattern_id, self.__info_table)
                break

        # Make sure, that pattern prioritization is maintained.
        self.__info_table.sort(key=attrgetter("pattern_id"))

        # Assume that the last entry is always the 'default' where no pre-context is required.
        assert len(self.__info_table) >= 1
        assert self.__info_table[-1].pre_context_id == None

    def __eq__(self, Other):
        return None

    def __find_last_post_context_begin(self, PostContextID, Path, track_info):
        """Walk the path backwards until the state is found that stores the position
           of the acceptance.
        """
        distance = 0
        successor_is_loop_state_f = track_info.is_loop_state(state_index)
        for state_index in reversed(path[:-1]):
            distance += 1
            if successor_is_loop_state_f:
                # If the state is part of a loop, then the distance backwards cannot be 
                # determined from the structure of the state machine.
                return None

            for origin in track_info.get_origin_list(state_index):
                if     origin.post_context_id() == PostContextID \
                   and origin.store_input_position_f(): 
                    return distance

            successor_is_loop_state_f = track_info.is_loop_state(state_index)
        
        # This function is only to be called to find the beginning of a post context. It
        # **must** be impossible to reach a post-context end without passing the place where
        # the post context begins. Thus, the path **must** contain a state that stores this
        # position. If we reach this position here, then something is seriously wrong. 
        assert False

def AcceptanceTrace_analyzis(AcceptanceTraceList):
    """For a given state of AcceptanceTraces that belong to a state, check:

       (1) On DropOut: -- does the state have to restore the accepting pattern id,
                          or is it clear from the state machine's structure?

                       -- where to put the input position? Does it have to rely on 
                          stored acceptance ids?

       For all pattern id and acceptance position that is restored, the state that
       stores it needs to know about it.
    """

class TrackInfo:
    def __init__(self, SM, ForwardF):
        """SM -- state machine to be investigated."""
        assert type(ForwardF) == bool
        self.__sm        = SM
        self.__forward_f = ForwardF

        # (0) Acceptance DB
        #
        # -- Provide for each acceptance state an 'acceptance info' that tells 
        #    what pattern id wins under what pre_context.  
        self.acceptance_db = dict([ (i, AcceptanceInfo(state)) for i, state in self.__sm.states.iteritems() ])

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
        self.__loop_state_set = set([])
        self.__loop_state_search(self.__sm.init_state_index, path=[])

        # -- Database of Passed Acceptance States
        # 
        #    map:  state_index  --> list of AcceptanceTrace objects.
        #
        self.__acceptance_trace_db = dict([(i, []) for i in self.__sm.states.iterkeys()])
        self.__acceptance_trace_search(self.__sm.init_state_index, 
                                       path             = [], 
                                       acceptance_trace = AcceptanceTrace())

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
        self.acceptance_location_db = dict([ (i, {}) for i in self.__sm.states.iterkeys() ])

        #     Analyze to build the databases mentioned above.
        #     (store in acceptance info objects the necessity to store acceptance 
        #      and acceptance position).
        self.__analyze_acceptance()

    def __loop_state_search(self, StateIndex, path):
        """Determine the indices of states that are part of a loop. Whenever
           such a state appears in a path from one state A to another state B, 
           then the number of transitions from A to B cannot be determined 
           from the state machine itself.

           Recursion Terminal: When a state has no target state that has not
                               yet been handled in the path.
        """
        if StateIndex in path:
            return

        # (1) Add current state index to path
        path.append(StateIndex)

        # (2) Iterate over all target states
        for state_index in state.transitions().get_target_state_index_list()
            if x in path: 
                # Mark all states that are part of a loop. The length of a path that 
                # contains such a state can only be determined at run-time.
                idx = path.index(StateIndex)
                self.__loop_state_set.update(path[idx:])
                continue # Do not dive into done states

            self.__loop_state_search(state_index, p)

        # (3) Remove current state index --> path is as before
        x = path.pop()
        assert x == StateIndex

    def __acceptance_trace_search(self, StateIndex, path, acceptance_trace):
        """StateIndex -- current state
           path       -- path from init state to current state (state index list)

           last_acceptance_i -- index in 'path' of the last acceptance state. 
                                path[last_acceptance_i] == state index of 
                                last acceptance state.

           last_post_context_i_db[k] -- index in 'path' of the last state where post context 
                                        'k' begins. 
                                        path[last_post_context_i_db[k] == state index 
                                        of last state where post context k begins.

           Recursion Terminal: When state has no target state that has not yet been
                               handled in the 'path'.
        """
        # (1) Add current state to path
        path.append(StateIndex)

        # (2) Update the information about the 'trace of acceptances'
        acceptance_trace.update(StateIndex, self.__sm.states[StateIndex], self)

        # (3) Mark the current state with its acceptance trace
        if acceptance_trace.is_empty() == False:
            self.__acceptance_trace_db[StateIndex].append(deepcopy(acceptance_trace))

        # (4) Recurse to all (undone) target states. 
        for target_index in state.transitions().get_target_state_index_list():
            if x in path: continue # Do not dive into done states
            self.__acceptance_trace_search(target_index, path, acceptance_trace)

        # (5) Remove current state index --> path is as before
        x = path.pop()
        assert x == StateIndex

    def __analyze_acceptance(self):

        def analyze_this(PathList):
            """Find out whether:
               -- The acceptance on-drop-out based on passing previous states
                  can be determined from the state machine itself.
               -- The position of the last acceptance can be determined from
                  the state machine.
               
               RETURNS: 
                   acceptance_id > 0 => pattern id of accepted pattern - known
                                        from the state machine constitution.
                                 - 1 => Failure -- no acceptance
                                None => acceptance depends on run-time

                   path_length as integer => path length from last acceptance state
                                             is distinct 
                                  None    => path length from last acceptance state
                                             must be determined at run-time.
            """
            acceptance  = -1   # '-1' means: not yet considered
            path_length = -2   # '-2' means: not yet considered (-1 --> input_p = lexeme_start_p + 1)

            # Iterate over the possible paths from the last acceptance state
            # to the state under investigation.
            for path in PathList:
                acceptance_state_index = path[0]
                # (1) AcceptanceInfo
                acceptance_info = self.acceptance_db[acceptance_state_index]

                if   acceptance == -1:              acceptance = acceptance_info
                elif acceptance != acceptance_info: acceptance = None   # unequal detected
                else:                               pass # No problem -- same acceptance 

                # (2) Length of path from acceptance state
                if   acceptance_info.failure_always():            
                    length = -1  # Means: set input_p --> lexeme_start_p + 1 / on failure anyway
                elif acceptance_info.failure_possible():            
                    # If acceptance is 'failure' in case of missing pre-context, then length = void.
                    length = None                      
                elif self.__loop_state_set.isdisjoint(path) == False: 
                    # If one of the states in the path is a 'loop state' then the state machine 
                    # could loop on the way from the begin to the end. Thus, the length of the 
                    # path cannot be determined from the state machine alone.
                    length = None       
                else:
                    length = len(path) - 1

                if   path_length == -2:     length      = path_length
                elif path_length != length: path_length = None # unequal detected
                else:                       pass # No problem -- same path length

            # If no change happend --> values are undetermined.
            if acceptance  == -1: acceptance  = None
            if path_length == -2: path_length = None
            return acceptance, path_length
                   
        # Determine for each state whether the acceptance is definite
        for state_index, acceptance_trace in self.__acceptance_trace_db.iteritems():

            # Determine how consistent the different paths are.
            acceptance, path_length = analyze_this(path_list)

            if acceptance == None:
                # Mark in all acceptance states involved, that there is a
                # successor that has undetermined acceptance. Thus, those
                # acceptance states need to the acceptance information.
                for acceptance_state_index in map(lambda x: x[0], path_list):
                    x = self.acceptance_db[acceptance_state_index]
                    x.set_necessary_to_store_last_acceptance_f()

            if path_length == None:
                # If the last acceptance cannot be determined by structure,
                # then all related last acceptance states need to store
                # information about their acceptance position.
                for acceptance_state_index in map(lambda x: x[0], path_list):
                    x = self.acceptance_db[acceptance_state_index]
                    x.set_necessary_to_store_last_acceptance_position_f()
                self.acceptance_location_db[state_index] = None
            else:
                self.acceptance_location_db[state_index] = - path_length

    def get_origin_list(self, StateIndex):
        return self.__sm.states[StateIndex].origins().get_list():

    def is_loop_state(self, StateIndex):
        return StateIndex in self.__loop_state_set

    def is_init_state_index(self, StateIndex):
        return self.__sm.init_state_index == StateIndex

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
                    group.append(post_context_id)
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


